from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.models import RoleAssignment
from apps.academics.models import HomeroomAssignment, TeachingAssignment
from apps.reports.models import StudentReport, SubjectComment
from apps.reports.policies import (
    can_edit_report_subject,
    can_publish_report,
    can_review_report,
    has_report_subject_scope,
    report_content_for,
)
from apps.reports.services import (
    approve_report,
    publish_report,
    return_subject_comment,
    save_subject_comment,
    submit_subject_comment,
)
from apps.students.models import GuardianRelationship, StudentSchoolMembership


DEMO_ACCOUNTS = [
    ("teacher.cs", "CS 教师"),
    ("teacher.math", "数学教师"),
    ("homeroom.g8a", "G8A 班主任"),
    ("academic.admin", "学术管理员"),
    ("student.a001", "学生"),
    ("guardian.a001", "家长"),
    ("system.admin", "系统管理员（用于验证默认看不到教育内容）"),
]


def home(request):
    if request.user.is_authenticated:
        return redirect("core:dashboard")
    return render(
        request,
        "home.html",
        {
            "demo_mode": getattr(settings, "DEMO_MODE", False),
            "demo_accounts": DEMO_ACCOUNTS,
            "demo_password": getattr(settings, "DEMO_PASSWORD", ""),
        },
    )


def _teacher_comments_for(user):
    assignments = list(
        TeachingAssignment.objects.active()
        .filter(
            teacher_role__user=user,
            class_group__academic_year__is_active=True,
        )
        .select_related("subject", "class_group__academic_year")
    )
    query = Q(pk__isnull=True)
    for assignment in assignments:
        student_membership_ids = assignment.class_group.student_memberships.filter(
            is_active=True,
            student_membership__status=StudentSchoolMembership.Status.ACTIVE,
        ).values("student_membership_id")
        query |= Q(
            subject=assignment.subject,
            report__report_cycle__academic_year=assignment.class_group.academic_year,
            report__student_membership_id__in=student_membership_ids,
        )

    return (
        SubjectComment.objects.filter(query)
        .select_related(
            "subject",
            "report",
            "report__student_membership__student",
            "report__report_cycle",
            "report__report_cycle__academic_year__school",
        )
        .distinct()
        .order_by("report__student_membership__student_number", "subject__code")
    )


def _homeroom_reports_for(user):
    assignments = list(
        HomeroomAssignment.objects.active()
        .filter(
            teacher_role__user=user,
            class_group__academic_year__is_active=True,
        )
        .select_related("class_group__academic_year")
    )
    query = Q(pk__isnull=True)
    for assignment in assignments:
        student_membership_ids = assignment.class_group.student_memberships.filter(
            is_active=True,
            student_membership__status=StudentSchoolMembership.Status.ACTIVE,
        ).values("student_membership_id")
        query |= Q(
            report_cycle__academic_year=assignment.class_group.academic_year,
            student_membership_id__in=student_membership_ids,
        )

    return (
        StudentReport.objects.filter(query)
        .select_related(
            "student_membership__student",
            "report_cycle",
            "report_cycle__academic_year__school",
        )
        .distinct()
        .order_by("student_membership__student_number")
    )


def _admin_reports_for(user):
    school_ids = RoleAssignment.objects.filter(
        user=user,
        role=RoleAssignment.Role.ACADEMIC_ADMIN,
        is_active=True,
        school__status="ACTIVE",
    ).values("school_id")
    return (
        StudentReport.objects.filter(report_cycle__academic_year__school_id__in=school_ids)
        .select_related(
            "student_membership__student",
            "report_cycle",
            "report_cycle__academic_year__school",
        )
        .order_by("student_membership__student_number")
    )


def _portal_reports_for(user):
    membership_ids = set(
        StudentSchoolMembership.objects.filter(
            student__user_account=user,
            status=StudentSchoolMembership.Status.ACTIVE,
        ).values_list("id", flat=True)
    )
    membership_ids.update(
        GuardianRelationship.objects.active()
        .filter(guardian=user)
        .values_list("student_membership_id", flat=True)
    )
    if not membership_ids:
        return StudentReport.objects.none()
    return (
        StudentReport.objects.filter(
            student_membership_id__in=membership_ids,
            status=StudentReport.Status.PUBLISHED,
        )
        .select_related(
            "student_membership__student",
            "report_cycle",
            "report_cycle__academic_year__school",
        )
        .order_by("-published_at")
    )


@login_required
def dashboard(request):
    teacher_comments = _teacher_comments_for(request.user)
    homeroom_reports = _homeroom_reports_for(request.user)
    admin_reports = _admin_reports_for(request.user)
    portal_reports = _portal_reports_for(request.user)

    return render(
        request,
        "dashboard.html",
        {
            "teacher_comments": teacher_comments,
            "homeroom_reports": homeroom_reports,
            "admin_reports": admin_reports,
            "portal_reports": portal_reports,
            "demo_mode": getattr(settings, "DEMO_MODE", False),
        },
    )


@login_required
def teacher_comment(request, comment_id):
    comment = get_object_or_404(
        SubjectComment.objects.select_related(
            "subject",
            "report",
            "report__student_membership__student",
            "report__report_cycle",
            "report__report_cycle__academic_year__school",
        ),
        pk=comment_id,
    )
    if not has_report_subject_scope(request.user, comment.report, comment.subject):
        raise PermissionDenied

    editable = (
        can_edit_report_subject(request.user, comment.report, comment.subject)
        and comment.status != SubjectComment.Status.SUBMITTED
    )

    if request.method == "POST":
        if not editable:
            raise PermissionDenied
        try:
            comment = save_subject_comment(
                actor=request.user,
                report=comment.report,
                subject=comment.subject,
                student_feedback=request.POST.get("student_feedback", ""),
                guardian_message=request.POST.get("guardian_message", ""),
                staff_note=request.POST.get("staff_note", ""),
            )
            if request.POST.get("action") == "submit":
                submit_subject_comment(actor=request.user, comment=comment)
                messages.success(request, "学科评价已提交。")
            else:
                messages.success(request, "草稿已保存。")
            return redirect("core:dashboard")
        except ValidationError as exc:
            messages.error(request, "；".join(exc.messages))
            comment.refresh_from_db()

    return render(
        request,
        "reports/teacher_comment.html",
        {"comment": comment, "editable": editable},
    )


@login_required
def homeroom_report(request, report_id):
    report = get_object_or_404(
        StudentReport.objects.select_related(
            "student_membership__student",
            "report_cycle",
            "report_cycle__academic_year__school",
        ).prefetch_related("subject_comments__subject"),
        pk=report_id,
    )
    if not can_review_report(request.user, report):
        raise PermissionDenied

    if request.method == "POST":
        try:
            action = request.POST.get("action")
            if action == "approve":
                approve_report(actor=request.user, report=report)
                messages.success(request, "报告已批准，等待学术管理员发布。")
                return redirect("core:dashboard")
            if action == "return":
                comment = get_object_or_404(
                    report.subject_comments.select_related("subject"),
                    pk=request.POST.get("comment_id"),
                )
                return_subject_comment(
                    actor=request.user,
                    comment=comment,
                    reason=request.POST.get("reason", ""),
                )
                messages.success(request, f"{comment.subject.name} 已退回对应教师修改。")
                return redirect("core:dashboard")
        except ValidationError as exc:
            messages.error(request, "；".join(exc.messages))
            report.refresh_from_db()

    return render(request, "reports/homeroom_report.html", {"report": report})


@login_required
def publish_report_view(request, report_id):
    if request.method != "POST":
        raise PermissionDenied
    report = get_object_or_404(
        StudentReport.objects.select_related(
            "student_membership__student",
            "report_cycle__academic_year__school",
        ),
        pk=report_id,
    )
    if not can_publish_report(request.user, report):
        raise PermissionDenied
    try:
        publish_report(actor=request.user, report=report)
        messages.success(request, "报告已发布。学生与已授权家长现在可以查看。")
    except ValidationError as exc:
        messages.error(request, "；".join(exc.messages))
    return redirect("core:dashboard")


@login_required
def report_view(request, report_id):
    report = get_object_or_404(
        StudentReport.objects.select_related(
            "student_membership__student",
            "report_cycle",
            "report_cycle__academic_year__school",
        ).prefetch_related("subject_comments__subject"),
        pk=report_id,
    )
    content = report_content_for(request.user, report)
    if not content:
        raise PermissionDenied
    return render(
        request,
        "reports/report_view.html",
        {"report": report, "content": content},
    )


@login_required
def demo_reset(request):
    if request.method != "POST" or not getattr(settings, "DEMO_MODE", False):
        raise PermissionDenied

    from .demo_data import reset_demo_workflow

    try:
        reset_demo_workflow(actor=request.user)
        messages.success(request, "演示报告已重置为未填写状态。")
    except ValidationError as exc:
        messages.error(request, "；".join(exc.messages))
    return redirect("core:dashboard")
