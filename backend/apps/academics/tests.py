from datetime import date

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
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


class AcademicStructureTests(TestCase):
    def setUp(self):
        self.school_a = School.objects.create(code="school-a", name="测试学校 A")
        self.school_b = School.objects.create(code="school-b", name="测试学校 B")
        self.year_a = AcademicYear.objects.create(
            school=self.school_a,
            name="2026-2027",
            starts_on=date(2026, 8, 1),
            ends_on=date(2027, 7, 31),
        )
        self.year_b = AcademicYear.objects.create(
            school=self.school_b,
            name="2026-2027",
            starts_on=date(2026, 8, 1),
            ends_on=date(2027, 7, 31),
        )
        self.student = Student.objects.create(full_name="测试学生")
        self.student_a = StudentSchoolMembership.objects.create(
            school=self.school_a,
            student=self.student,
            student_number="A001",
        )
        self.teacher_user = UserAccount.objects.create_user(
            username="teacher.a",
            password="test-password-only",
            display_name="测试教师 A",
        )
        self.teacher_role = RoleAssignment.objects.create(
            school=self.school_a,
            user=self.teacher_user,
            role=RoleAssignment.Role.TEACHER,
        )

    def test_class_group_name_is_unique_inside_academic_year(self):
        ClassGroup.objects.create(academic_year=self.year_a, name="G8A")
        with self.assertRaises(IntegrityError), transaction.atomic():
            ClassGroup.objects.create(academic_year=self.year_a, name="G8A")

    def test_same_class_group_name_is_allowed_across_schools(self):
        ClassGroup.objects.create(academic_year=self.year_a, name="G8A")
        ClassGroup.objects.create(academic_year=self.year_b, name="G8A")
        self.assertEqual(ClassGroup.objects.filter(name="G8A").count(), 2)

    def test_subject_code_is_unique_inside_school(self):
        Subject.objects.create(school=self.school_a, code="CS", name="Computer Science")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Subject.objects.create(school=self.school_a, code="CS", name="重复学科")

    def test_same_subject_code_is_allowed_across_schools(self):
        Subject.objects.create(school=self.school_a, code="CS", name="Computer Science")
        Subject.objects.create(school=self.school_b, code="CS", name="Computer Science")
        self.assertEqual(Subject.objects.filter(code="CS").count(), 2)

    def test_student_can_join_one_homeroom_and_multiple_teaching_groups(self):
        homeroom = ClassGroup.objects.create(
            academic_year=self.year_a,
            name="G8A",
            group_type=ClassGroup.GroupType.HOMEROOM,
        )
        math_set = ClassGroup.objects.create(
            academic_year=self.year_a,
            name="G8 Math Set 1",
            group_type=ClassGroup.GroupType.TEACHING,
        )
        cs_group = ClassGroup.objects.create(
            academic_year=self.year_a,
            name="G8 CS Group",
            group_type=ClassGroup.GroupType.TEACHING,
        )

        StudentClassMembership.objects.create(student_membership=self.student_a, class_group=homeroom)
        StudentClassMembership.objects.create(student_membership=self.student_a, class_group=math_set)
        StudentClassMembership.objects.create(student_membership=self.student_a, class_group=cs_group)

        self.assertEqual(StudentClassMembership.objects.active().count(), 3)

    def test_student_cannot_have_two_active_homerooms_in_same_year(self):
        homeroom_a = ClassGroup.objects.create(academic_year=self.year_a, name="G8A")
        homeroom_b = ClassGroup.objects.create(academic_year=self.year_a, name="G8B")
        StudentClassMembership.objects.create(student_membership=self.student_a, class_group=homeroom_a)

        with self.assertRaises(ValidationError):
            StudentClassMembership.objects.create(student_membership=self.student_a, class_group=homeroom_b)

    def test_student_class_membership_cannot_cross_schools(self):
        class_b = ClassGroup.objects.create(academic_year=self.year_b, name="G8A")
        with self.assertRaises(ValidationError):
            StudentClassMembership.objects.create(student_membership=self.student_a, class_group=class_b)

    def test_inactive_school_membership_cannot_have_active_class_membership(self):
        self.student_a.status = StudentSchoolMembership.Status.WITHDRAWN
        self.student_a.save(update_fields=["status"])
        homeroom = ClassGroup.objects.create(academic_year=self.year_a, name="G8A")

        with self.assertRaises(ValidationError):
            StudentClassMembership.objects.create(student_membership=self.student_a, class_group=homeroom)

    def test_teaching_assignment_requires_teacher_role(self):
        admin_user = UserAccount.objects.create_user(username="admin.a", password="test-password-only")
        admin_role = RoleAssignment.objects.create(
            school=self.school_a,
            user=admin_user,
            role=RoleAssignment.Role.ACADEMIC_ADMIN,
        )
        group = ClassGroup.objects.create(academic_year=self.year_a, name="G8 CS")
        subject = Subject.objects.create(school=self.school_a, code="CS", name="Computer Science")

        with self.assertRaises(ValidationError):
            TeachingAssignment.objects.create(
                teacher_role=admin_role,
                class_group=group,
                subject=subject,
            )

    def test_teaching_assignment_cannot_cross_school_boundaries(self):
        group = ClassGroup.objects.create(academic_year=self.year_a, name="G8 CS")
        subject_b = Subject.objects.create(school=self.school_b, code="CS", name="Computer Science")

        with self.assertRaises(ValidationError):
            TeachingAssignment.objects.create(
                teacher_role=self.teacher_role,
                class_group=group,
                subject=subject_b,
            )

    def test_teaching_group_can_have_multiple_teachers(self):
        group = ClassGroup.objects.create(
            academic_year=self.year_a,
            name="G8 CS",
            group_type=ClassGroup.GroupType.TEACHING,
        )
        subject = Subject.objects.create(school=self.school_a, code="CS", name="Computer Science")
        second_user = UserAccount.objects.create_user(username="teacher.b", password="test-password-only")
        second_role = RoleAssignment.objects.create(
            school=self.school_a,
            user=second_user,
            role=RoleAssignment.Role.TEACHER,
        )

        TeachingAssignment.objects.create(
            teacher_role=self.teacher_role,
            class_group=group,
            subject=subject,
        )
        TeachingAssignment.objects.create(
            teacher_role=second_role,
            class_group=group,
            subject=subject,
        )

        self.assertEqual(TeachingAssignment.objects.filter(class_group=group, subject=subject).count(), 2)

    def test_homeroom_assignment_requires_homeroom_group(self):
        teaching_group = ClassGroup.objects.create(
            academic_year=self.year_a,
            name="G8 Math Set 1",
            group_type=ClassGroup.GroupType.TEACHING,
        )
        with self.assertRaises(ValidationError):
            HomeroomAssignment.objects.create(
                teacher_role=self.teacher_role,
                class_group=teaching_group,
            )

    def test_homeroom_assignment_cannot_cross_school_boundaries(self):
        homeroom_b = ClassGroup.objects.create(academic_year=self.year_b, name="G8A")
        with self.assertRaises(ValidationError):
            HomeroomAssignment.objects.create(
                teacher_role=self.teacher_role,
                class_group=homeroom_b,
            )

    def test_for_school_queries_do_not_leak_other_school_records(self):
        group_a = ClassGroup.objects.create(academic_year=self.year_a, name="G8A")
        ClassGroup.objects.create(academic_year=self.year_b, name="G8A")
        subject_a = Subject.objects.create(school=self.school_a, code="CS", name="Computer Science")
        Subject.objects.create(school=self.school_b, code="CS", name="Computer Science")
        class_membership = StudentClassMembership.objects.create(
            student_membership=self.student_a,
            class_group=group_a,
        )
        teaching = TeachingAssignment.objects.create(
            teacher_role=self.teacher_role,
            class_group=group_a,
            subject=subject_a,
        )
        homeroom = HomeroomAssignment.objects.create(
            teacher_role=self.teacher_role,
            class_group=group_a,
        )

        self.assertEqual(list(ClassGroup.objects.for_school(self.school_a)), [group_a])
        self.assertEqual(list(Subject.objects.for_school(self.school_a)), [subject_a])
        self.assertEqual(list(StudentClassMembership.objects.for_school(self.school_a)), [class_membership])
        self.assertEqual(list(TeachingAssignment.objects.for_school(self.school_a)), [teaching])
        self.assertEqual(list(HomeroomAssignment.objects.for_school(self.school_a)), [homeroom])
