import csv
import io

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from openpyxl import Workbook

from apps.accounts.models import RoleAssignment
from apps.academics.models import HomeroomAssignment, TeachingAssignment
from apps.reports.bulk_import import ImportRow, parse_import_upload
from apps.reports.models import ReportCycle, StudentReport, SubjectComment
from apps.reports.policies import (
    can_edit_report_subject,
    can_manage_report_cycles,
    can_publish_report,
    can_review_report,
    has_report_subject_scope,
    report_content_for,
    subject_comment_content_for,
)
from apps.reports.services import (
    approve_report,
    publish_report,
    return_subject_comment,
    save_subject_comment,
    submit_subject_comment,
)
from apps.schools.models import School
from apps.students.models import GuardianRelationship, StudentSchoolMembership

from .teacher_throughput import assignment_comments, teacher_batch_entries


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


def _teacher_assignment_for(user, assignment_id):
    return get_object_or_404(
        TeachingAssignment.objects.active().select_related(
            "teacher_role__user",
            "subject",
            "class_group",
            "class_group__academic_year",
            "class_group__academic_year__school",
        ),
        pk=assignment_id,
        teacher_role__user=user,
        class_group__academic_year__is_active=True,
    )


def _teacher_cycle_for(assignment, cycle_id):
    return get_object_or_404(
        ReportCycle.objects.select_related("academic_year", "academic_year__school"),
        pk=cycle_id,
        academic_year=assignment.class_group.academic_year,
    )


def _batch_counts(comments):
    total = comments.count()
    submitted = comments.filter(status=SubjectComment.Status.SUBMITTED).count()
    returned = comments.filter(status=SubjectComment.Status.RETURNED).count()
    return {
        "total": total,
        "submitted": submitted,
        "remaining": total - submitted,
        "returned": returned,
    }


def _import_session_key(assignment, cycle):
    return f"teacher_batch_import:{assignment.pk}:{cycle.pk}"


def _validate_import_rows(*, actor, comments, rows):
    comment_by_number = {
        comment.report.student_membership.student_number: comment for comment in comments
    }
    preview = []
    has_errors = False

    for row in rows:
        item = row.as_dict() if isinstance(row, ImportRow) else dict(row)
        errors = []
        comment = comment_by_number.get(item["student_number"])
        if comment is None:
            errors.append("该学号不在当前任课分组 / 报告周期内。")
        else:
            actual_name = comment.report.student_membership.student.full_name.strip()
            supplied_name = item.get("student_name", "").strip()
            if supplied_name and supplied_name.casefold() != actual_name.casefold():
                errors.append(f"姓名不匹配，系统中为“{actual_name}”。")
            if comment.status == SubjectComment.Status.SUBMITTED:
                errors.append("该评价已经提交，不能通过批量导入覆盖。")
            elif not can_edit_report_subject(actor, comment.report, comment.subject):
                errors.append("当前账号没有该学生 / 学科的编辑权限。")
            if item.get("action") == "SUBMIT" and not item.get("student_feedback", "").strip():
                errors.append("选择 SUBMIT 时学生反馈不能为空。")

        item["student_name_actual"] = (
            comment.report.student_membership.student.full_name if comment else ""
        )
        item["comment_id"] = str(comment.pk) if comment else ""
        item["errors"] = errors
        item["valid"] = not errors
        preview.append(item)
        has_errors = has_errors or bool(errors)

    return preview, has_errors


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
            "teacher_batches": teacher_batch_entries(request.user),
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
def teacher_batch(request, assignment_id, cycle_id):
    assignment = _teacher_assignment_for(request.user, assignment_id)
    cycle = _teacher_cycle_for(assignment, cycle_id)
    comments = assignment_comments(assignment, cycle)
    if not comments.exists():
        raise PermissionDenied

    if request.method == "POST":
        comment = get_object_or_404(comments, pk=request.POST.get("comment_id"))
        editable = (
            can_edit_report_subject(request.user, comment.report, comment.subject)
            and comment.status != SubjectComment.Status.SUBMITTED
        )
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
            action = request.POST.get("action", "save")
            if action == "submit":
                submit_subject_comment(actor=request.user, comment=comment)
            comment.refresh_from_db()
            counts = _batch_counts(comments)
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "ok": True,
                        "comment_id": str(comment.pk),
                        "status": comment.status,
                        "status_label": comment.get_status_display(),
                        "action": action,
                        "counts": counts,
                    }
                )
            messages.success(
                request,
                "评价已提交。" if action == "submit" else "草稿已保存。",
            )
            return redirect("core:teacher_batch", assignment_id=assignment.pk, cycle_id=cycle.pk)
        except ValidationError as exc:
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"ok": False, "errors": exc.messages}, status=400)
            messages.error(request, "；".join(exc.messages))

    items = []
    requested_focus = request.GET.get("focus", "")
    for comment in comments:
        editable = (
            can_edit_report_subject(request.user, comment.report, comment.subject)
            and comment.status != SubjectComment.Status.SUBMITTED
        )
        items.append({"comment": comment, "editable": editable})

    first_focus = requested_focus
    if not first_focus:
        editable_item = next((item for item in items if item["editable"]), None)
        first_focus = str((editable_item or items[0])["comment"].pk) if items else ""

    return render(
        request,
        "reports/teacher_batch.html",
        {
            "assignment": assignment,
            "cycle": cycle,
            "items": items,
            "focus_id": first_focus,
            "counts": _batch_counts(comments),
        },
    )


@login_required
def teacher_batch_import(request, assignment_id, cycle_id):
    assignment = _teacher_assignment_for(request.user, assignment_id)
    cycle = _teacher_cycle_for(assignment, cycle_id)
    comments = assignment_comments(assignment, cycle)
    if not comments.exists():
        raise PermissionDenied

    session_key = _import_session_key(assignment, cycle)
    preview = None
    has_errors = False

    if request.method == "POST" and request.POST.get("action") == "preview":
        upload = request.FILES.get("file")
        if upload is None:
            messages.error(request, "请选择 CSV 或 Excel 文件。")
        else:
            try:
                rows = parse_import_upload(upload)
                preview, has_errors = _validate_import_rows(
                    actor=request.user,
                    comments=comments,
                    rows=rows,
                )
                request.session[session_key] = [row.as_dict() for row in rows]
                request.session.modified = True
            except ValidationError as exc:
                messages.error(request, "；".join(exc.messages))

    elif request.method == "POST" and request.POST.get("action") == "confirm":
        stored_rows = request.session.get(session_key)
        if not stored_rows:
            messages.error(request, "导入预检已失效，请重新上传文件。")
        else:
            preview, has_errors = _validate_import_rows(
                actor=request.user,
                comments=comments,
                rows=stored_rows,
            )
            if has_errors:
                messages.error(request, "数据状态已变化，请检查错误后重新预检。")
            else:
                comment_by_id = {str(comment.pk): comment for comment in comments}
                try:
                    with transaction.atomic():
                        for row in preview:
                            comment = comment_by_id[row["comment_id"]]
                            saved = save_subject_comment(
                                actor=request.user,
                                report=comment.report,
                                subject=comment.subject,
                                student_feedback=row["student_feedback"],
                                guardian_message=row["guardian_message"],
                                staff_note=row["staff_note"],
                            )
                            if row["action"] == "SUBMIT":
                                submit_subject_comment(actor=request.user, comment=saved)
                    request.session.pop(session_key, None)
                    messages.success(request, f"已导入 {len(preview)} 名学生的评价。")
                    return redirect(
                        "core:teacher_batch",
                        assignment_id=assignment.pk,
                        cycle_id=cycle.pk,
                    )
                except ValidationError as exc:
                    messages.error(request, "；".join(exc.messages))

    return render(
        request,
        "reports/teacher_batch_import.html",
        {
            "assignment": assignment,
            "cycle": cycle,
            "preview": preview,
            "has_errors": has_errors,
        },
    )


@login_required
def teacher_batch_template(request, assignment_id, cycle_id, file_format):
    assignment = _teacher_assignment_for(request.user, assignment_id)
    cycle = _teacher_cycle_for(assignment, cycle_id)
    comments = list(assignment_comments(assignment, cycle))
    if not comments:
        raise PermissionDenied

    headers = ["学号", "姓名", "学生反馈", "家长信息", "内部备注", "动作"]
    rows = [
        [
            comment.report.student_membership.student_number,
            comment.report.student_membership.student.full_name,
            "",
            "",
            "",
            "DRAFT",
        ]
        for comment in comments
    ]
    base_name = f"{assignment.class_group.name}-{assignment.subject.code}-{cycle.name}"

    if file_format == "csv":
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="{base_name}.csv"'
        response.write("\ufeff")
        writer = csv.writer(response)
        writer.writerow(headers)
        writer.writerows(rows)
        return response

    if file_format == "xlsx":
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "批量评价"
        sheet.append(headers)
        for row in rows:
            sheet.append(row)
        output = io.BytesIO()
        workbook.save(output)
        response = HttpResponse(
            output.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="{base_name}.xlsx"'
        return response

    raise PermissionDenied


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

    review_items = []
    for comment in report.subject_comments.select_related("subject").order_by("subject__code"):
        review_items.append(
            {
                "comment": comment,
                "content": subject_comment_content_for(request.user, comment),
            }
        )

    return render(
        request,
        "reports/homeroom_report.html",
        {"report": report, "review_items": review_items},
    )


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

    from .demo_data import DEMO_SCHOOL_CODE, reset_demo_workflow

    school = School.objects.filter(code=DEMO_SCHOOL_CODE, status=School.Status.ACTIVE).first()
    if school is None or not can_manage_report_cycles(request.user, school):
        raise PermissionDenied

    try:
        reset_demo_workflow(actor=request.user)
        messages.success(request, "演示报告已重置为未填写状态。")
    except ValidationError as exc:
        messages.error(request, "；".join(exc.messages))
    return redirect("core:dashboard")
