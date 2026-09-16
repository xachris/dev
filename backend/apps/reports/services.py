"""学习报告写入与状态机服务。

所有真实业务写入应优先经过这里，而不是由 View / API 直接修改模型状态。
"""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.academics.models import (
    ClassGroup,
    HomeroomAssignment,
    StudentClassMembership,
    Subject,
    TeachingAssignment,
)
from apps.students.models import StudentSchoolMembership

from .models import ReportAction, ReportCycle, StudentReport, SubjectComment
from .policies import (
    can_edit_report_subject,
    can_manage_report_cycles,
    can_publish_report,
    can_review_report,
)


def _subjects_for_student_when_report_created(report_cycle: ReportCycle, student_membership):
    """只在报告创建时读取当前教学结构，形成正式报告的学科快照。"""
    student_group_ids = StudentClassMembership.objects.filter(
        student_membership=student_membership,
        is_active=True,
        class_group__academic_year=report_cycle.academic_year,
    ).values("class_group_id")

    return Subject.objects.filter(
        school=report_cycle.school,
        teaching_assignments__is_active=True,
        teaching_assignments__class_group_id__in=student_group_ids,
        teaching_assignments__class_group__academic_year=report_cycle.academic_year,
    ).distinct()


def expected_subjects_for_report(report: StudentReport):
    """返回创建报告时已经冻结的学科槽，而不是重新读取今天的课表关系。"""
    return Subject.objects.filter(report_comments__report=report).distinct()


def report_is_complete(report: StudentReport) -> bool:
    """报告中的每一个学科槽都已提交时，报告才算完整。"""
    comments = report.subject_comments.all()
    return comments.exists() and not comments.exclude(status=SubjectComment.Status.SUBMITTED).exists()


def create_report_cycle(*, actor, academic_year, name: str) -> ReportCycle:
    """由学术管理员创建最小报告周期。"""
    if not academic_year.is_active:
        raise ValidationError("不能在停用学年中创建新的报告周期。")
    if not can_manage_report_cycles(actor, academic_year.school):
        raise ValidationError("当前用户无权创建该学校的报告周期。")
    if not name or not name.strip():
        raise ValidationError("报告周期名称不能为空。")

    return ReportCycle.objects.create(academic_year=academic_year, name=name.strip())


def create_student_report(*, actor, report_cycle: ReportCycle, student_membership) -> StudentReport:
    """创建学生报告，并自动生成当时真实应填写的学科工作槽。

    学科槽是正式报告构成和教师待办，不是管理员维护的第二份学科名单。
    报告创建后，普通任课调整不会悄悄改变这份正式报告的学科构成。
    """
    if not can_manage_report_cycles(actor, report_cycle.school):
        raise ValidationError("当前用户无权创建该学校的学生报告。")
    if not report_cycle.academic_year.is_active:
        raise ValidationError("不能在停用学年中创建新的学生报告。")
    if student_membership.school_id != report_cycle.school.id:
        raise ValidationError("学生与报告周期必须属于同一所学校。")
    if student_membership.status != StudentSchoolMembership.Status.ACTIVE:
        raise ValidationError("只有当前在读学生可以进入新的报告周期。")

    homeroom_group_ids = StudentClassMembership.objects.filter(
        student_membership=student_membership,
        is_active=True,
        class_group__academic_year=report_cycle.academic_year,
        class_group__group_type=ClassGroup.GroupType.HOMEROOM,
    ).values("class_group_id")

    if not homeroom_group_ids.exists():
        raise ValidationError("学生在该学年没有有效班主任班级，无法进入报告审核流程。")

    has_reviewer = HomeroomAssignment.objects.active().filter(
        class_group_id__in=homeroom_group_ids,
        class_group__academic_year=report_cycle.academic_year,
        teacher_role__school=report_cycle.school,
    ).exists()
    if not has_reviewer:
        raise ValidationError("学生所在班级没有有效班主任，无法进入报告审核流程。")

    subjects = list(_subjects_for_student_when_report_created(report_cycle, student_membership))
    if not subjects:
        raise ValidationError("学生在该学年没有有效任教学科，不能生成空报告。")

    with transaction.atomic():
        report = StudentReport.objects.create(
            report_cycle=report_cycle,
            student_membership=student_membership,
        )
        for subject in subjects:
            SubjectComment.objects.create(
                report=report,
                subject=subject,
                created_by=None,
            )
        return report


def save_subject_comment(
    *,
    actor,
    report: StudentReport,
    subject: Subject,
    student_feedback: str = "",
    guardian_message: str = "",
    staff_note: str = "",
) -> SubjectComment:
    """更新当前报告已经存在的学科工作槽。

    SUBMITTED 状态被锁定；班主任退回后才重新允许编辑。
    报告创建后不能因为后来新增任课关系就偷偷多出一门正式报告学科。
    """
    if not can_edit_report_subject(actor, report, subject):
        raise ValidationError("当前用户无权编辑该学生的这一学科评价。")

    with transaction.atomic():
        locked_report = StudentReport.objects.select_for_update().select_related(
            "report_cycle",
            "report_cycle__academic_year",
            "student_membership",
        ).get(pk=report.pk)
        if not can_edit_report_subject(actor, locked_report, subject):
            raise ValidationError("当前用户的任课权限已经变化，请刷新后重试。")
        if locked_report.status in {StudentReport.Status.APPROVED, StudentReport.Status.PUBLISHED}:
            raise ValidationError("当前报告已经锁定，不能继续修改学科评价。")

        comment = SubjectComment.objects.select_for_update().filter(
            report=locked_report,
            subject=subject,
        ).first()
        if comment is None:
            raise ValidationError("这一学科不属于该报告创建时冻结的学科范围。")
        if comment.status == SubjectComment.Status.SUBMITTED:
            raise ValidationError("已提交评价不能直接修改；需要班主任退回后才能编辑。")

        if comment.created_by_id is None:
            comment.created_by = actor
        comment.student_feedback = (student_feedback or "").strip()
        comment.guardian_message = (guardian_message or "").strip()
        comment.staff_note = (staff_note or "").strip()
        comment.save()
        return comment


def _refresh_report_after_submission(report: StudentReport) -> None:
    """完整性由学科槽状态自动推导，不让班主任多点一次“开始审核”。"""
    if report.status in {StudentReport.Status.APPROVED, StudentReport.Status.PUBLISHED}:
        return

    if report_is_complete(report):
        if report.status != StudentReport.Status.IN_REVIEW:
            report.status = StudentReport.Status.IN_REVIEW
            report.save(update_fields=["status", "updated_at"])
    elif report.status not in {StudentReport.Status.RETURNED, StudentReport.Status.DRAFT}:
        report.status = StudentReport.Status.DRAFT
        report.save(update_fields=["status", "updated_at"])


def submit_subject_comment(*, actor, comment: SubjectComment) -> SubjectComment:
    """提交或重新提交一条评价；最后一个学科槽提交后报告自动进入班主任审核。

    先锁整份 StudentReport，再锁具体 SubjectComment，使同一学生的并发提交按报告串行判断完整性。
    """
    if not can_edit_report_subject(actor, comment.report, comment.subject):
        raise ValidationError("当前用户无权提交这一学科评价。")
    if comment.status not in {SubjectComment.Status.DRAFT, SubjectComment.Status.RETURNED}:
        raise ValidationError("只有草稿或已退回评价可以提交。")
    if not comment.student_feedback.strip():
        raise ValidationError("提交前必须填写学生可见学习反馈。")

    with transaction.atomic():
        locked_report = StudentReport.objects.select_for_update().select_related(
            "report_cycle",
            "report_cycle__academic_year",
            "student_membership",
        ).get(pk=comment.report_id)
        locked = SubjectComment.objects.select_for_update().select_related("subject").get(pk=comment.pk)

        if not can_edit_report_subject(actor, locked_report, locked.subject):
            raise ValidationError("当前用户的任课权限已经变化，请刷新后重试。")
        if locked_report.status in {StudentReport.Status.APPROVED, StudentReport.Status.PUBLISHED}:
            raise ValidationError("报告已经锁定，不能继续提交评价。")
        if locked.status not in {SubjectComment.Status.DRAFT, SubjectComment.Status.RETURNED}:
            raise ValidationError("评价状态已经变化，请刷新后重试。")
        if not locked.student_feedback.strip():
            raise ValidationError("提交前必须填写学生可见学习反馈。")

        locked.status = SubjectComment.Status.SUBMITTED
        locked.submitted_by = actor
        locked.submitted_at = timezone.now()
        locked.save(update_fields=["status", "submitted_by", "submitted_at", "updated_at"])
        _refresh_report_after_submission(locked_report)
        return locked


def return_subject_comment(
    *,
    actor,
    comment: SubjectComment,
    reason: str,
) -> SubjectComment:
    """班主任只退回需要修改的学科，而不是整份报告重新抄一遍。"""
    reason = (reason or "").strip()
    if not reason:
        raise ValidationError("退回学科评价必须说明修改原因。")
    if not can_review_report(actor, comment.report):
        raise ValidationError("当前用户无权审核这份学生报告。")
    if comment.report.status != StudentReport.Status.IN_REVIEW:
        raise ValidationError("只有待审核报告中的学科评价可以退回。")
    if comment.status != SubjectComment.Status.SUBMITTED:
        raise ValidationError("只有已提交的学科评价可以退回。")

    with transaction.atomic():
        report = StudentReport.objects.select_for_update().select_related(
            "report_cycle",
            "report_cycle__academic_year",
            "student_membership",
        ).get(pk=comment.report_id)
        locked = SubjectComment.objects.select_for_update().get(pk=comment.pk)

        if not can_review_report(actor, report):
            raise ValidationError("当前班主任权限已经变化，请刷新后重试。")
        if report.status != StudentReport.Status.IN_REVIEW or locked.status != SubjectComment.Status.SUBMITTED:
            raise ValidationError("报告状态已经变化，请刷新后重试。")

        locked.status = SubjectComment.Status.RETURNED
        locked.save(update_fields=["status", "updated_at"])

        report.status = StudentReport.Status.RETURNED
        report.save(update_fields=["status", "updated_at"])

        ReportAction.objects.create(
            report=report,
            actor=actor,
            action=ReportAction.Action.RETURN_SUBJECT,
            subject_comment=locked,
            note=reason,
        )
        return locked


def approve_report(*, actor, report: StudentReport) -> StudentReport:
    """班主任批准完整且仍处于审核状态的报告。"""
    if not can_review_report(actor, report):
        raise ValidationError("当前用户无权审核这份学生报告。")
    if report.status != StudentReport.Status.IN_REVIEW:
        raise ValidationError("只有待审核报告可以批准。")
    if not report_is_complete(report):
        raise ValidationError("报告仍缺少应提交的学科评价，不能批准。")

    with transaction.atomic():
        locked = StudentReport.objects.select_for_update().select_related(
            "report_cycle",
            "report_cycle__academic_year",
            "student_membership",
        ).get(pk=report.pk)
        if not can_review_report(actor, locked):
            raise ValidationError("当前班主任权限已经变化，请刷新后重试。")
        if locked.status != StudentReport.Status.IN_REVIEW:
            raise ValidationError("报告状态已经变化，请刷新后重试。")
        if not report_is_complete(locked):
            raise ValidationError("报告完整性已经变化，不能批准。")

        locked.status = StudentReport.Status.APPROVED
        locked.save(update_fields=["status", "updated_at"])
        ReportAction.objects.create(
            report=locked,
            actor=actor,
            action=ReportAction.Action.APPROVE,
        )
        return locked


def publish_report(*, actor, report: StudentReport) -> StudentReport:
    """学术管理员发布已批准报告；发布不依赖邮件服务。"""
    if not can_publish_report(actor, report):
        raise ValidationError("当前用户无权发布这份学生报告。")
    if report.status != StudentReport.Status.APPROVED:
        raise ValidationError("只有已批准报告可以发布。")

    with transaction.atomic():
        locked = StudentReport.objects.select_for_update().select_related(
            "report_cycle",
            "report_cycle__academic_year",
            "student_membership",
        ).get(pk=report.pk)
        if not can_publish_report(actor, locked):
            raise ValidationError("当前发布权限已经变化，请刷新后重试。")
        if locked.status != StudentReport.Status.APPROVED:
            raise ValidationError("报告状态已经变化，请刷新后重试。")

        locked.status = StudentReport.Status.PUBLISHED
        locked.published_by = actor
        locked.published_at = timezone.now()
        locked.save(
            update_fields=["status", "published_by", "published_at", "updated_at"]
        )
        ReportAction.objects.create(
            report=locked,
            actor=actor,
            action=ReportAction.Action.PUBLISH,
        )
        return locked
