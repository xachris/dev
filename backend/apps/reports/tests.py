from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.accounts.models import RoleAssignment, UserAccount
from apps.academics.models import (
    ClassGroup,
    HomeroomAssignment,
    StudentClassMembership,
    Subject,
    TeachingAssignment,
)
from apps.schools.models import AcademicYear, School
from apps.students.models import GuardianRelationship, Student, StudentSchoolMembership

from .models import ReportAction, ReportCycle, StudentReport, SubjectComment
from .policies import (
    can_publish_report,
    report_content_for,
    subject_comment_content_for,
)
from .services import (
    approve_report,
    create_report_cycle,
    create_student_report,
    expected_subjects_for_report,
    publish_report,
    report_is_complete,
    return_subject_comment,
    save_subject_comment,
    submit_subject_comment,
)


class ReportWorkflowTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(code="school-a", name="测试学校")
        self.other_school = School.objects.create(code="school-b", name="其他学校")
        self.year = AcademicYear.objects.create(
            school=self.school,
            name="2026-2027",
            starts_on=date(2026, 8, 1),
            ends_on=date(2027, 7, 31),
        )
        self.other_year = AcademicYear.objects.create(
            school=self.other_school,
            name="2026-2027",
            starts_on=date(2026, 8, 1),
            ends_on=date(2027, 7, 31),
        )

        self.homeroom = ClassGroup.objects.create(
            academic_year=self.year,
            name="G8A",
            group_type=ClassGroup.GroupType.HOMEROOM,
        )
        self.cs_group = ClassGroup.objects.create(
            academic_year=self.year,
            name="G8 CS",
            group_type=ClassGroup.GroupType.TEACHING,
        )
        self.math_group = ClassGroup.objects.create(
            academic_year=self.year,
            name="G8 Math",
            group_type=ClassGroup.GroupType.TEACHING,
        )
        self.cs = Subject.objects.create(
            school=self.school,
            code="CS",
            name="Computer Science",
        )
        self.math = Subject.objects.create(
            school=self.school,
            code="MATH",
            name="Mathematics",
        )
        self.other_subject = Subject.objects.create(
            school=self.other_school,
            code="CS",
            name="Computer Science",
        )

        self.student_user = UserAccount.objects.create_user(
            username="student.a",
            password="test-password-only",
            display_name="学生 A",
        )
        self.student = Student.objects.create(
            full_name="学生 A",
            user_account=self.student_user,
        )
        self.student_membership = StudentSchoolMembership.objects.create(
            school=self.school,
            student=self.student,
            student_number="A001",
        )
        for group in (self.homeroom, self.cs_group, self.math_group):
            StudentClassMembership.objects.create(
                student_membership=self.student_membership,
                class_group=group,
            )

        self.guardian = UserAccount.objects.create_user(
            username="guardian.a",
            password="test-password-only",
            display_name="家长 A",
        )
        GuardianRelationship.objects.create(
            student_membership=self.student_membership,
            guardian=self.guardian,
        )
        self.other_guardian = UserAccount.objects.create_user(
            username="guardian.other",
            password="test-password-only",
        )

        self.cs_teacher = UserAccount.objects.create_user(
            username="teacher.cs",
            password="test-password-only",
            display_name="CS 教师",
        )
        self.cs_teacher_role = RoleAssignment.objects.create(
            school=self.school,
            user=self.cs_teacher,
            role=RoleAssignment.Role.TEACHER,
        )
        TeachingAssignment.objects.create(
            teacher_role=self.cs_teacher_role,
            class_group=self.cs_group,
            subject=self.cs,
        )

        self.math_teacher = UserAccount.objects.create_user(
            username="teacher.math",
            password="test-password-only",
            display_name="数学教师",
        )
        self.math_teacher_role = RoleAssignment.objects.create(
            school=self.school,
            user=self.math_teacher,
            role=RoleAssignment.Role.TEACHER,
        )
        TeachingAssignment.objects.create(
            teacher_role=self.math_teacher_role,
            class_group=self.math_group,
            subject=self.math,
        )

        self.homeroom_teacher = UserAccount.objects.create_user(
            username="teacher.homeroom",
            password="test-password-only",
            display_name="班主任",
        )
        self.homeroom_teacher_role = RoleAssignment.objects.create(
            school=self.school,
            user=self.homeroom_teacher,
            role=RoleAssignment.Role.TEACHER,
        )
        HomeroomAssignment.objects.create(
            teacher_role=self.homeroom_teacher_role,
            class_group=self.homeroom,
        )

        self.other_teacher = UserAccount.objects.create_user(
            username="teacher.other",
            password="test-password-only",
        )
        self.other_teacher_role = RoleAssignment.objects.create(
            school=self.school,
            user=self.other_teacher,
            role=RoleAssignment.Role.TEACHER,
        )

        self.academic_admin = UserAccount.objects.create_user(
            username="academic.admin",
            password="test-password-only",
            display_name="学术管理员",
        )
        RoleAssignment.objects.create(
            school=self.school,
            user=self.academic_admin,
            role=RoleAssignment.Role.ACADEMIC_ADMIN,
        )
        self.system_admin = UserAccount.objects.create_user(
            username="system.admin",
            password="test-password-only",
        )
        RoleAssignment.objects.create(
            school=self.school,
            user=self.system_admin,
            role=RoleAssignment.Role.SYSTEM_ADMIN,
        )

        self.cycle = create_report_cycle(
            actor=self.academic_admin,
            academic_year=self.year,
            name="Term 1",
        )
        self.report = create_student_report(
            actor=self.academic_admin,
            report_cycle=self.cycle,
            student_membership=self.student_membership,
        )

    def make_comment(self, teacher, subject, feedback="学习进展良好", guardian="家长信息", staff="内部备注"):
        return save_subject_comment(
            actor=teacher,
            report=self.report,
            subject=subject,
            student_feedback=feedback,
            guardian_message=guardian,
            staff_note=staff,
        )

    def submit_both_subjects(self):
        cs_comment = self.make_comment(self.cs_teacher, self.cs, feedback="CS 学习反馈")
        math_comment = self.make_comment(self.math_teacher, self.math, feedback="数学学习反馈")
        submit_subject_comment(actor=self.cs_teacher, comment=cs_comment)
        submit_subject_comment(actor=self.math_teacher, comment=math_comment)
        self.report.refresh_from_db()
        return (
            SubjectComment.objects.get(pk=cs_comment.pk),
            SubjectComment.objects.get(pk=math_comment.pk),
        )

    def approve_and_publish(self):
        cs_comment, math_comment = self.submit_both_subjects()
        approve_report(actor=self.homeroom_teacher, report=self.report)
        self.report.refresh_from_db()
        publish_report(actor=self.academic_admin, report=self.report)
        self.report.refresh_from_db()
        return cs_comment, math_comment

    def test_report_cycle_is_unique_inside_academic_year(self):
        with self.assertRaises(ValidationError):
            create_report_cycle(
                actor=self.academic_admin,
                academic_year=self.year,
                name="Term 1",
            )

    def test_non_academic_admin_cannot_create_report_cycle(self):
        with self.assertRaises(ValidationError):
            create_report_cycle(
                actor=self.system_admin,
                academic_year=self.year,
                name="Term 2",
            )

    def test_expected_subjects_are_derived_from_real_teaching_structure(self):
        self.assertEqual(
            set(expected_subjects_for_report(self.report)),
            {self.cs, self.math},
        )

    def test_report_starts_in_draft_and_has_no_duplicate_summary_fields(self):
        self.assertEqual(self.report.status, StudentReport.Status.DRAFT)
        field_names = {field.name for field in StudentReport._meta.get_fields()}
        self.assertNotIn("overall_summary_student", field_names)
        self.assertNotIn("overall_summary_guardian", field_names)

    def test_wrong_teacher_cannot_create_subject_comment(self):
        with self.assertRaises(ValidationError):
            self.make_comment(self.other_teacher, self.cs)

    def test_teacher_cannot_write_another_subject(self):
        with self.assertRaises(ValidationError):
            self.make_comment(self.cs_teacher, self.math)

    def test_cross_school_subject_cannot_enter_report(self):
        with self.assertRaises(ValidationError):
            self.make_comment(self.cs_teacher, self.other_subject)

    def test_draft_must_have_student_feedback_before_submission(self):
        comment = self.make_comment(self.cs_teacher, self.cs, feedback="")
        with self.assertRaises(ValidationError):
            submit_subject_comment(actor=self.cs_teacher, comment=comment)

    def test_submitted_comment_is_locked_until_returned(self):
        comment = self.make_comment(self.cs_teacher, self.cs)
        submit_subject_comment(actor=self.cs_teacher, comment=comment)
        with self.assertRaises(ValidationError):
            self.make_comment(self.cs_teacher, self.cs, feedback="偷偷改掉")

    def test_first_subject_submission_does_not_start_review_when_another_subject_is_missing(self):
        comment = self.make_comment(self.cs_teacher, self.cs)
        submit_subject_comment(actor=self.cs_teacher, comment=comment)
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, StudentReport.Status.DRAFT)
        self.assertFalse(report_is_complete(self.report))

    def test_last_required_subject_submission_automatically_starts_review(self):
        self.submit_both_subjects()
        self.assertEqual(self.report.status, StudentReport.Status.IN_REVIEW)
        self.assertTrue(report_is_complete(self.report))

    def test_subject_teacher_cannot_approve_complete_report(self):
        self.submit_both_subjects()
        with self.assertRaises(ValidationError):
            approve_report(actor=self.cs_teacher, report=self.report)

    def test_homeroom_teacher_can_return_only_one_subject_with_reason(self):
        cs_comment, math_comment = self.submit_both_subjects()
        return_subject_comment(
            actor=self.homeroom_teacher,
            comment=cs_comment,
            reason="请补充更具体的学习证据。",
        )
        self.report.refresh_from_db()
        cs_comment.refresh_from_db()
        math_comment.refresh_from_db()

        self.assertEqual(self.report.status, StudentReport.Status.RETURNED)
        self.assertEqual(cs_comment.status, SubjectComment.Status.RETURNED)
        self.assertEqual(math_comment.status, SubjectComment.Status.SUBMITTED)
        action = ReportAction.objects.get(action=ReportAction.Action.RETURN_SUBJECT)
        self.assertEqual(action.subject_comment, cs_comment)
        self.assertIn("学习证据", action.note)

    def test_return_requires_reason(self):
        cs_comment, _ = self.submit_both_subjects()
        with self.assertRaises(ValidationError):
            return_subject_comment(
                actor=self.homeroom_teacher,
                comment=cs_comment,
                reason="   ",
            )

    def test_only_returned_subject_needs_edit_and_resubmit(self):
        cs_comment, math_comment = self.submit_both_subjects()
        return_subject_comment(
            actor=self.homeroom_teacher,
            comment=cs_comment,
            reason="请修改",
        )

        revised = self.make_comment(
            self.cs_teacher,
            self.cs,
            feedback="修改后的 CS 学习反馈",
        )
        with self.assertRaises(ValidationError):
            self.make_comment(self.math_teacher, self.math, feedback="不应允许重复编辑")

        submit_subject_comment(actor=self.cs_teacher, comment=revised)
        self.report.refresh_from_db()
        math_comment.refresh_from_db()
        self.assertEqual(self.report.status, StudentReport.Status.IN_REVIEW)
        self.assertEqual(math_comment.status, SubjectComment.Status.SUBMITTED)

    def test_homeroom_teacher_can_approve_complete_report(self):
        self.submit_both_subjects()
        approved = approve_report(actor=self.homeroom_teacher, report=self.report)
        self.assertEqual(approved.status, StudentReport.Status.APPROVED)
        self.assertTrue(ReportAction.objects.filter(action=ReportAction.Action.APPROVE).exists())

    def test_approved_report_cannot_be_edited(self):
        self.submit_both_subjects()
        approve_report(actor=self.homeroom_teacher, report=self.report)
        self.report.refresh_from_db()
        with self.assertRaises(ValidationError):
            self.make_comment(self.cs_teacher, self.cs, feedback="批准后修改")

    def test_only_academic_admin_can_publish_approved_report(self):
        self.submit_both_subjects()
        approve_report(actor=self.homeroom_teacher, report=self.report)
        self.report.refresh_from_db()

        self.assertTrue(can_publish_report(self.academic_admin, self.report))
        self.assertFalse(can_publish_report(self.system_admin, self.report))
        with self.assertRaises(ValidationError):
            publish_report(actor=self.system_admin, report=self.report)

    def test_publish_records_state_actor_time_and_action(self):
        self.approve_and_publish()
        self.assertEqual(self.report.status, StudentReport.Status.PUBLISHED)
        self.assertEqual(self.report.published_by, self.academic_admin)
        self.assertIsNotNone(self.report.published_at)
        self.assertTrue(ReportAction.objects.filter(action=ReportAction.Action.PUBLISH).exists())

    def test_publish_does_not_create_notification_yet(self):
        self.approve_and_publish()
        # Phase 13 才负责 Notification Outbox。当前发布是独立业务状态变化。
        self.assertEqual(self.report.status, StudentReport.Status.PUBLISHED)

    def test_student_and_guardian_cannot_see_unpublished_content(self):
        self.submit_both_subjects()
        self.assertEqual(report_content_for(self.student_user, self.report), [])
        self.assertEqual(report_content_for(self.guardian, self.report), [])

    def test_subject_teacher_sees_only_own_subject_full_internal_content(self):
        cs_comment = self.make_comment(
            self.cs_teacher,
            self.cs,
            feedback="学生反馈",
            guardian="家长内容",
            staff="内部内容",
        )
        math_comment = self.make_comment(self.math_teacher, self.math, feedback="数学反馈")

        self.assertEqual(
            subject_comment_content_for(self.cs_teacher, cs_comment),
            {
                "student_feedback": "学生反馈",
                "guardian_message": "家长内容",
                "staff_note": "内部内容",
            },
        )
        self.assertEqual(subject_comment_content_for(self.cs_teacher, math_comment), {})

    def test_homeroom_teacher_cannot_read_teacher_draft_but_can_read_submitted_content(self):
        comment = self.make_comment(self.cs_teacher, self.cs)
        self.assertEqual(subject_comment_content_for(self.homeroom_teacher, comment), {})

        submit_subject_comment(actor=self.cs_teacher, comment=comment)
        comment.refresh_from_db()
        visible = subject_comment_content_for(self.homeroom_teacher, comment)
        self.assertEqual(visible["student_feedback"], "学习进展良好")
        self.assertEqual(visible["guardian_message"], "家长信息")
        self.assertEqual(visible["staff_note"], "内部备注")

    def test_academic_admin_can_publish_without_content_read_permission(self):
        self.submit_both_subjects()
        self.assertEqual(report_content_for(self.academic_admin, self.report), [])
        approve_report(actor=self.homeroom_teacher, report=self.report)
        self.report.refresh_from_db()
        self.assertTrue(can_publish_report(self.academic_admin, self.report))
        self.assertEqual(report_content_for(self.academic_admin, self.report), [])

    def test_system_admin_has_no_report_content_read_permission(self):
        self.submit_both_subjects()
        self.assertEqual(report_content_for(self.system_admin, self.report), [])

    def test_teacher_keeps_read_access_to_own_subject_after_approval_but_cannot_edit(self):
        cs_comment, _ = self.submit_both_subjects()
        approve_report(actor=self.homeroom_teacher, report=self.report)
        self.report.refresh_from_db()
        cs_comment.refresh_from_db()

        visible = subject_comment_content_for(self.cs_teacher, cs_comment)
        self.assertEqual(visible["student_feedback"], "CS 学习反馈")
        with self.assertRaises(ValidationError):
            self.make_comment(self.cs_teacher, self.cs, feedback="不能修改")

    def test_published_student_view_contains_only_student_feedback(self):
        self.approve_and_publish()
        content = report_content_for(self.student_user, self.report)
        self.assertEqual(len(content), 2)
        for item in content:
            self.assertIn("student_feedback", item)
            self.assertNotIn("guardian_message", item)
            self.assertNotIn("staff_note", item)

    def test_published_guardian_view_contains_parent_message_but_not_staff_note(self):
        self.approve_and_publish()
        content = report_content_for(self.guardian, self.report)
        self.assertEqual(len(content), 2)
        for item in content:
            self.assertIn("student_feedback", item)
            self.assertIn("guardian_message", item)
            self.assertNotIn("staff_note", item)

    def test_unrelated_guardian_cannot_read_published_report(self):
        self.approve_and_publish()
        self.assertEqual(report_content_for(self.other_guardian, self.report), [])

    def test_workflow_actions_preserve_human_judgment_history(self):
        cs_comment, _ = self.submit_both_subjects()
        return_subject_comment(
            actor=self.homeroom_teacher,
            comment=cs_comment,
            reason="证据不足",
        )
        revised = self.make_comment(self.cs_teacher, self.cs, feedback="增加了证据")
        submit_subject_comment(actor=self.cs_teacher, comment=revised)
        self.report.refresh_from_db()
        approve_report(actor=self.homeroom_teacher, report=self.report)
        self.report.refresh_from_db()
        publish_report(actor=self.academic_admin, report=self.report)

        self.assertEqual(
            list(self.report.actions.values_list("action", flat=True)),
            [
                ReportAction.Action.RETURN_SUBJECT,
                ReportAction.Action.APPROVE,
                ReportAction.Action.PUBLISH,
            ],
        )
