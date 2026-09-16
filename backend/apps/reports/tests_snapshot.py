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
from apps.students.models import Student, StudentSchoolMembership

from .models import SubjectComment
from .services import (
    create_report_cycle,
    create_student_report,
    expected_subjects_for_report,
    save_subject_comment,
)


class ReportSubjectSnapshotTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(code="school-a", name="测试学校")
        self.year = AcademicYear.objects.create(
            school=self.school,
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
        self.cs = Subject.objects.create(school=self.school, code="CS", name="Computer Science")
        self.math = Subject.objects.create(school=self.school, code="MATH", name="Mathematics")

        self.student = Student.objects.create(full_name="测试学生")
        self.membership = StudentSchoolMembership.objects.create(
            school=self.school,
            student=self.student,
            student_number="A001",
        )
        for group in (self.homeroom, self.cs_group, self.math_group):
            StudentClassMembership.objects.create(
                student_membership=self.membership,
                class_group=group,
            )

        self.cs_teacher = UserAccount.objects.create_user(
            username="teacher.cs",
            password="test-password-only",
        )
        self.cs_role = RoleAssignment.objects.create(
            school=self.school,
            user=self.cs_teacher,
            role=RoleAssignment.Role.TEACHER,
        )
        self.cs_assignment = TeachingAssignment.objects.create(
            teacher_role=self.cs_role,
            class_group=self.cs_group,
            subject=self.cs,
        )

        self.math_teacher = UserAccount.objects.create_user(
            username="teacher.math",
            password="test-password-only",
        )
        self.math_role = RoleAssignment.objects.create(
            school=self.school,
            user=self.math_teacher,
            role=RoleAssignment.Role.TEACHER,
        )
        self.math_assignment = TeachingAssignment.objects.create(
            teacher_role=self.math_role,
            class_group=self.math_group,
            subject=self.math,
        )

        self.homeroom_teacher = UserAccount.objects.create_user(
            username="teacher.homeroom.snapshot",
            password="test-password-only",
        )
        self.homeroom_role = RoleAssignment.objects.create(
            school=self.school,
            user=self.homeroom_teacher,
            role=RoleAssignment.Role.TEACHER,
        )
        HomeroomAssignment.objects.create(
            teacher_role=self.homeroom_role,
            class_group=self.homeroom,
        )

        self.admin = UserAccount.objects.create_user(
            username="academic.admin.snapshot",
            password="test-password-only",
        )
        RoleAssignment.objects.create(
            school=self.school,
            user=self.admin,
            role=RoleAssignment.Role.ACADEMIC_ADMIN,
        )

        self.cycle = create_report_cycle(
            actor=self.admin,
            academic_year=self.year,
            name="Term 1",
        )
        self.report = create_student_report(
            actor=self.admin,
            report_cycle=self.cycle,
            student_membership=self.membership,
        )

    def test_report_creation_generates_empty_subject_work_slots(self):
        slots = list(self.report.subject_comments.select_related("subject").order_by("subject__code"))
        self.assertEqual([slot.subject for slot in slots], [self.cs, self.math])
        self.assertTrue(all(slot.status == SubjectComment.Status.DRAFT for slot in slots))
        self.assertTrue(all(slot.created_by is None for slot in slots))
        self.assertTrue(all(slot.student_feedback == "" for slot in slots))

    def test_first_real_teacher_edit_claims_authorship_without_creating_second_slot(self):
        slot_before = self.report.subject_comments.get(subject=self.cs)
        self.assertIsNone(slot_before.created_by)

        edited = save_subject_comment(
            actor=self.cs_teacher,
            report=self.report,
            subject=self.cs,
            student_feedback="第一次真实填写",
        )

        self.assertEqual(edited.pk, slot_before.pk)
        self.assertEqual(edited.created_by, self.cs_teacher)
        self.assertEqual(self.report.subject_comments.filter(subject=self.cs).count(), 1)

    def test_later_teaching_assignment_deactivation_does_not_rewrite_report_subject_snapshot(self):
        self.math_assignment.is_active = False
        self.math_assignment.save(update_fields=["is_active"])

        self.assertEqual(
            set(expected_subjects_for_report(self.report)),
            {self.cs, self.math},
        )
        self.assertEqual(self.report.subject_comments.count(), 2)

    def test_later_new_subject_does_not_silently_expand_existing_report(self):
        science = Subject.objects.create(school=self.school, code="SCI", name="Science")
        science_group = ClassGroup.objects.create(
            academic_year=self.year,
            name="G8 Science",
            group_type=ClassGroup.GroupType.TEACHING,
        )
        StudentClassMembership.objects.create(
            student_membership=self.membership,
            class_group=science_group,
        )
        science_teacher = UserAccount.objects.create_user(
            username="teacher.science",
            password="test-password-only",
        )
        science_role = RoleAssignment.objects.create(
            school=self.school,
            user=science_teacher,
            role=RoleAssignment.Role.TEACHER,
        )
        TeachingAssignment.objects.create(
            teacher_role=science_role,
            class_group=science_group,
            subject=science,
        )

        self.assertEqual(set(expected_subjects_for_report(self.report)), {self.cs, self.math})
        with self.assertRaises(ValidationError):
            save_subject_comment(
                actor=science_teacher,
                report=self.report,
                subject=science,
                student_feedback="不应自动加入旧报告",
            )
        self.assertFalse(self.report.subject_comments.filter(subject=science).exists())

    def test_new_teacher_can_take_over_existing_frozen_subject_slot(self):
        self.cs_assignment.is_active = False
        self.cs_assignment.save(update_fields=["is_active"])

        replacement = UserAccount.objects.create_user(
            username="teacher.cs.replacement",
            password="test-password-only",
        )
        replacement_role = RoleAssignment.objects.create(
            school=self.school,
            user=replacement,
            role=RoleAssignment.Role.TEACHER,
        )
        TeachingAssignment.objects.create(
            teacher_role=replacement_role,
            class_group=self.cs_group,
            subject=self.cs,
        )

        with self.assertRaises(ValidationError):
            save_subject_comment(
                actor=self.cs_teacher,
                report=self.report,
                subject=self.cs,
                student_feedback="原教师已无权限",
            )

        edited = save_subject_comment(
            actor=replacement,
            report=self.report,
            subject=self.cs,
            student_feedback="接任教师继续填写",
        )
        self.assertEqual(edited.created_by, replacement)
        self.assertEqual(self.report.subject_comments.filter(subject=self.cs).count(), 1)

    def _make_student_membership(self, number):
        student = Student.objects.create(full_name=f"学生 {number}")
        return StudentSchoolMembership.objects.create(
            school=self.school,
            student=student,
            student_number=number,
        )

    def test_report_creation_rejects_student_without_homeroom(self):
        membership = self._make_student_membership("A002")
        StudentClassMembership.objects.create(
            student_membership=membership,
            class_group=self.cs_group,
        )

        with self.assertRaises(ValidationError):
            create_student_report(
                actor=self.admin,
                report_cycle=self.cycle,
                student_membership=membership,
            )

    def test_report_creation_rejects_homeroom_without_active_reviewer(self):
        membership = self._make_student_membership("A003")
        orphan_homeroom = ClassGroup.objects.create(
            academic_year=self.year,
            name="G8C",
            group_type=ClassGroup.GroupType.HOMEROOM,
        )
        StudentClassMembership.objects.create(
            student_membership=membership,
            class_group=orphan_homeroom,
        )
        StudentClassMembership.objects.create(
            student_membership=membership,
            class_group=self.cs_group,
        )

        with self.assertRaises(ValidationError):
            create_student_report(
                actor=self.admin,
                report_cycle=self.cycle,
                student_membership=membership,
            )

    def test_report_creation_rejects_student_with_no_teaching_subjects(self):
        membership = self._make_student_membership("A004")
        StudentClassMembership.objects.create(
            student_membership=membership,
            class_group=self.homeroom,
        )

        with self.assertRaises(ValidationError):
            create_student_report(
                actor=self.admin,
                report_cycle=self.cycle,
                student_membership=membership,
            )
