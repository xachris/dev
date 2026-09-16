"""学习报告对象级权限。

Phase 5 只回答“用户与哪个学生存在什么业务关系”。本模块继续回答：
“面对这一份具体报告 / 这一条具体学科评价，哪些字段能读，哪些动作能做”。
"""

from django.db.models import QuerySet

from apps.accounts.models import RoleAssignment, UserAccount
from apps.academics.models import HomeroomAssignment, StudentClassMembership, TeachingAssignment
from apps.core.policies import can_access_student_space
from apps.schools.models import School
from apps.students.models import GuardianRelationship, StudentSchoolMembership

from .models import ReportCycle, StudentReport, SubjectComment


def _active_authenticated_user(user) -> bool:
    return bool(
        user
        and getattr(user, "is_authenticated", False)
        and getattr(user, "is_active", False)
    )


def _operational_school(school: School) -> bool:
    return bool(school and school.status == School.Status.ACTIVE)


def can_manage_report_cycles(user: UserAccount, school: School) -> bool:
    """报告周期和报告实例属于学术业务，不赋予内容读取权。"""
    if not _active_authenticated_user(user) or not _operational_school(school):
        return False
    return RoleAssignment.objects.filter(
        school=school,
        user=user,
        role=RoleAssignment.Role.ACADEMIC_ADMIN,
        is_active=True,
    ).exists()


def _student_group_ids_for_report(report: StudentReport) -> QuerySet:
    return StudentClassMembership.objects.filter(
        student_membership=report.student_membership,
        is_active=True,
        class_group__academic_year=report.report_cycle.academic_year,
    ).values("class_group_id")


def can_edit_report_subject(
    user: UserAccount,
    report: StudentReport,
    subject,
) -> bool:
    """当前教师是否仍有权维护这份报告中的指定学科评价。"""
    if (
        not _active_authenticated_user(user)
        or not report
        or not subject
        or not _operational_school(report.school)
        or report.student_membership.status != StudentSchoolMembership.Status.ACTIVE
        or not report.report_cycle.academic_year.is_active
        or subject.school_id != report.school.id
        or report.status in {StudentReport.Status.APPROVED, StudentReport.Status.PUBLISHED}
    ):
        return False

    return TeachingAssignment.objects.active().filter(
        teacher_role__user=user,
        teacher_role__school=report.school,
        subject=subject,
        class_group__academic_year=report.report_cycle.academic_year,
        class_group_id__in=_student_group_ids_for_report(report),
    ).exists()


def can_review_report(user: UserAccount, report: StudentReport) -> bool:
    """当前班主任是否负责这份报告所属学年中的该学生。"""
    if (
        not _active_authenticated_user(user)
        or not report
        or not _operational_school(report.school)
        or report.student_membership.status != StudentSchoolMembership.Status.ACTIVE
        or not report.report_cycle.academic_year.is_active
    ):
        return False

    homeroom_group_ids = StudentClassMembership.objects.filter(
        student_membership=report.student_membership,
        is_active=True,
        class_group__academic_year=report.report_cycle.academic_year,
        class_group__group_type="HOMEROOM",
    ).values("class_group_id")

    return HomeroomAssignment.objects.active().filter(
        teacher_role__user=user,
        teacher_role__school=report.school,
        class_group__academic_year=report.report_cycle.academic_year,
        class_group_id__in=homeroom_group_ids,
    ).exists()


def can_publish_report(user: UserAccount, report: StudentReport) -> bool:
    """学术管理员可执行发布动作，但该能力不自动授予报告内容读取权。"""
    return bool(
        report
        and report.report_cycle.academic_year.is_active
        and can_manage_report_cycles(user, report.school)
    )


def _is_student_self(user: UserAccount, report: StudentReport) -> bool:
    return bool(
        _active_authenticated_user(user)
        and report.student_membership.student.user_account_id == getattr(user, "id", None)
        and can_access_student_space(user, report.student_membership)
    )


def _is_active_guardian(user: UserAccount, report: StudentReport) -> bool:
    if not _active_authenticated_user(user):
        return False
    if not can_access_student_space(user, report.student_membership):
        return False
    return GuardianRelationship.objects.filter(
        student_membership=report.student_membership,
        guardian=user,
        is_active=True,
    ).exists()


def subject_comment_content_for(user: UserAccount, comment: SubjectComment) -> dict:
    """按具体对象返回允许看到的内容字段。

    返回空字典表示没有内容读取权。调用方不应先取全字段再自行删除。
    """
    if not comment or not _active_authenticated_user(user):
        return {}

    report = comment.report

    # 实际负责该学科的教师可查看并维护自己业务范围内的三类内容。
    if can_edit_report_subject(user, report, comment.subject):
        return {
            "student_feedback": comment.student_feedback,
            "guardian_message": comment.guardian_message,
            "staff_note": comment.staff_note,
        }

    # 班主任只有在学科教师提交后才进入完整审核视图；草稿仍属于教师工作区。
    if can_review_report(user, report) and comment.status != SubjectComment.Status.DRAFT:
        return {
            "student_feedback": comment.student_feedback,
            "guardian_message": comment.guardian_message,
            "staff_note": comment.staff_note,
        }

    # 对外内容必须等整份报告正式发布。
    if report.status != StudentReport.Status.PUBLISHED:
        return {}

    if _is_active_guardian(user, report):
        return {
            "student_feedback": comment.student_feedback,
            "guardian_message": comment.guardian_message,
        }

    if _is_student_self(user, report):
        return {"student_feedback": comment.student_feedback}

    return {}


def report_content_for(user: UserAccount, report: StudentReport) -> list[dict]:
    """返回一份报告中当前用户真正可见的学科内容。

    这是后续 Portal / API 的安全默认读取入口；不会把 Staff-only 字段先加载给客户端再隐藏。
    """
    if not report or not _active_authenticated_user(user):
        return []

    result = []
    for comment in report.subject_comments.select_related("subject").order_by("subject__code"):
        content = subject_comment_content_for(user, comment)
        if content:
            result.append(
                {
                    "subject_code": comment.subject.code,
                    "subject_name": comment.subject.name,
                    **content,
                }
            )
    return result
