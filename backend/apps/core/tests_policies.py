from datetime import date

from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from apps.accounts.models import RoleAssignment, UserAccount
from apps.academics.models import (
    ClassGroup,
    HomeroomAssignment,
    StudentClassMembership,
    Subject,
    TeachingAssignment,
)
from apps.core.policies import (
    can_access_student,
    can_manage_academic_structure,
    can_manage_school_accounts,
    can_review_student_report,
    can_write_subject_comment,
    reviewable_student_memberships_for,
    visible_student_memberships_for,
    writable_student_memberships_for_subject,
)
from apps.schools.models import AcademicYear, School
from apps.students.models import GuardianRelationship, Student, StudentSchoolMembership


class ContextualPermissionPolicyTests(TestCase):
    def setUp(self):
        self.school_a = School.objects.create(code="school-a", name="学校 A")
        self.school_b = School.objects.create(code="school-b", name="学校 B")
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

        self.homeroom_a = ClassGroup.objects.create(
            academic_year=self.year_a,
            name="G8A",
            group_type=ClassGroup.GroupType.HOMEROOM,
        )
        self.other_homeroom_a = ClassGroup.objects.create(
            academic_year=self.year_a,
            name="G8B",
            group_type=ClassGroup.GroupType.HOMEROOM,
        )
        self.cs_group_a = ClassGroup.objects.create(
            academic_year=self.year_a,
            name="G8 CS",
            group_type=ClassGroup.GroupType.TEACHING,
        )
        self.math_group_a = ClassGroup.objects.create(
            academic_year=self.year_a,
            name="G8 Math",
            group_type=ClassGroup.GroupType.TEACHING,
        )
        self.homeroom_b = ClassGroup.objects.create(
            academic_year=self.year_b,
            name="G8A",
            group_type=ClassGroup.GroupType.HOMEROOM,
        )

        self.cs_a = Subject.objects.create(school=self.school_a, code="CS", name="Computer Science")
        self.math_a = Subject.objects.create(school=self.school_a, code="MATH", name="Mathematics")
        self.cs_b = Subject.objects.create(school=self.school_b, code="CS", name="Computer Science")

        self.student_user = UserAccount.objects.create_user(
            username="student.a1",
            password="test-password-only",
            display_name="学生 A1",
        )
        self.student_a1 = Student.objects.create(
            full_name="学生 A1",
            user_account=self.student_user,
        )
        self.membership_a1 = StudentSchoolMembership.objects.create(
            school=self.school_a,
            student=self.student_a1,
            student_number="A001",
        )
        StudentClassMembership.objects.create(
            student_membership=self.membership_a1,
            class_group=self.homeroom_a,
        )
        StudentClassMembership.objects.create(
            student_membership=self.membership_a1,
            class_group=self.cs_group_a,
        )

        self.student_a2 = Student.objects.create(full_name="学生 A2")
        self.membership_a2 = StudentSchoolMembership.objects.create(
            school=self.school_a,
            student=self.student_a2,
            student_number="A002",
        )
        StudentClassMembership.objects.create(
            student_membership=self.membership_a2,
            class_group=self.other_homeroom_a,
        )
        StudentClassMembership.objects.create(
            student_membership=self.membership_a2,
            class_group=self.math_group_a,
        )

        self.student_b1 = Student.objects.create(full_name="学生 B1")
        self.membership_b1 = StudentSchoolMembership.objects.create(
            school=self.school_b,
            student=self.student_b1,
            student_number="B001",
        )
        StudentClassMembership.objects.create(
            student_membership=self.membership_b1,
            class_group=self.homeroom_b,
        )

        self.guardian = UserAccount.objects.create_user(
            username="guardian.a1",
            password="test-password-only",
            display_name="家长 A1",
        )
        self.guardian_relation = GuardianRelationship.objects.create(
            student_membership=self.membership_a1,
            guardian=self.guardian,
        )

        self.subject_teacher = UserAccount.objects.create_user(
            username="teacher.cs",
            password="test-password-only",
            display_name="CS 教师",
        )
        self.subject_teacher_role = RoleAssignment.objects.create(
            school=self.school_a,
            user=self.subject_teacher,
            role=RoleAssignment.Role.TEACHER,
        )
        self.cs_assignment = TeachingAssignment.objects.create(
            teacher_role=self.subject_teacher_role,
            class_group=self.cs_group_a,
            subject=self.cs_a,
        )

        self.homeroom_teacher = UserAccount.objects.create_user(
            username="teacher.homeroom",
            password="test-password-only",
            display_name="G8A 班主任",
        )
        self.homeroom_teacher_role = RoleAssignment.objects.create(
            school=self.school_a,
            user=self.homeroom_teacher,
            role=RoleAssignment.Role.TEACHER,
        )
        self.homeroom_assignment = HomeroomAssignment.objects.create(
            teacher_role=self.homeroom_teacher_role,
            class_group=self.homeroom_a,
        )

        self.academic_admin = UserAccount.objects.create_user(
            username="academic.admin",
            password="test-password-only",
            display_name="学术管理员",
        )
        RoleAssignment.objects.create(
            school=self.school_a,
            user=self.academic_admin,
            role=RoleAssignment.Role.ACADEMIC_ADMIN,
        )

        self.system_admin = UserAccount.objects.create_user(
            username="system.admin",
            password="test-password-only",
            display_name="学校系统管理员",
        )
        RoleAssignment.objects.create(
            school=self.school_a,
            user=self.system_admin,
            role=RoleAssignment.Role.SYSTEM_ADMIN,
        )

    def test_student_can_access_only_own_student_space(self):
        self.assertTrue(can_access_student(self.student_user, self.membership_a1))
        self.assertFalse(can_access_student(self.student_user, self.membership_a2))

    def test_guardian_can_access_only_explicitly_linked_student(self):
        self.assertTrue(can_access_student(self.guardian, self.membership_a1))
        self.assertFalse(can_access_student(self.guardian, self.membership_a2))

    def test_inactive_guardian_relationship_removes_access(self):
        self.guardian_relation.is_active = False
        self.guardian_relation.save(update_fields=["is_active"])
        self.assertFalse(can_access_student(self.guardian, self.membership_a1))

    def test_subject_teacher_sees_only_students_in_active_teaching_group(self):
        visible = visible_student_memberships_for(self.subject_teacher, self.school_a)
        self.assertEqual(list(visible), [self.membership_a1])

    def test_homeroom_teacher_sees_only_students_in_own_homeroom(self):
        visible = visible_student_memberships_for(self.homeroom_teacher, self.school_a)
        self.assertEqual(list(visible), [self.membership_a1])

    def test_teacher_cannot_access_other_school_student(self):
        self.assertFalse(can_access_student(self.subject_teacher, self.membership_b1))

    def test_teacher_can_write_only_assigned_subject_for_assigned_student(self):
        self.assertTrue(
            can_write_subject_comment(self.subject_teacher, self.membership_a1, self.cs_a)
        )
        self.assertFalse(
            can_write_subject_comment(self.subject_teacher, self.membership_a1, self.math_a)
        )
        self.assertFalse(
            can_write_subject_comment(self.subject_teacher, self.membership_a2, self.cs_a)
        )
        self.assertFalse(
            can_write_subject_comment(self.subject_teacher, self.membership_b1, self.cs_b)
        )

    def test_writable_subject_query_returns_only_real_teaching_scope(self):
        writable = writable_student_memberships_for_subject(
            self.subject_teacher,
            self.school_a,
            self.cs_a,
        )
        self.assertEqual(list(writable), [self.membership_a1])

    def test_homeroom_teacher_can_review_only_own_homeroom_student(self):
        self.assertTrue(can_review_student_report(self.homeroom_teacher, self.membership_a1))
        self.assertFalse(can_review_student_report(self.homeroom_teacher, self.membership_a2))

    def test_subject_teacher_does_not_gain_full_report_review_permission(self):
        self.assertFalse(can_review_student_report(self.subject_teacher, self.membership_a1))

    def test_reviewable_query_returns_only_homeroom_scope(self):
        reviewable = reviewable_student_memberships_for(self.homeroom_teacher, self.school_a)
        self.assertEqual(list(reviewable), [self.membership_a1])

    def test_academic_admin_can_manage_structure_but_cannot_read_student_content_by_role_alone(self):
        self.assertTrue(can_manage_academic_structure(self.academic_admin, self.school_a))
        self.assertFalse(can_manage_school_accounts(self.academic_admin, self.school_a))
        self.assertFalse(can_access_student(self.academic_admin, self.membership_a1))

    def test_system_admin_can_manage_accounts_but_cannot_read_student_content_by_role_alone(self):
        self.assertTrue(can_manage_school_accounts(self.system_admin, self.school_a))
        self.assertFalse(can_manage_academic_structure(self.system_admin, self.school_a))
        self.assertFalse(can_access_student(self.system_admin, self.membership_a1))

    def test_roles_are_school_scoped(self):
        self.assertFalse(can_manage_academic_structure(self.academic_admin, self.school_b))
        self.assertFalse(can_manage_school_accounts(self.system_admin, self.school_b))

    def test_django_superuser_does_not_automatically_gain_business_student_access(self):
        superuser = UserAccount.objects.create_superuser(
            username="technical.superuser",
            password="test-password-only",
        )
        self.assertFalse(can_access_student(superuser, self.membership_a1))
        self.assertFalse(can_manage_academic_structure(superuser, self.school_a))
        self.assertFalse(can_manage_school_accounts(superuser, self.school_a))

    def test_anonymous_user_is_denied(self):
        anonymous = AnonymousUser()
        self.assertFalse(can_access_student(anonymous, self.membership_a1))
        self.assertFalse(can_manage_academic_structure(anonymous, self.school_a))
        self.assertFalse(can_manage_school_accounts(anonymous, self.school_a))

    def test_inactive_user_is_denied_even_when_relationship_exists(self):
        self.guardian.is_active = False
        self.guardian.save(update_fields=["is_active"])
        self.assertFalse(can_access_student(self.guardian, self.membership_a1))

    def test_inactive_teacher_role_removes_teaching_and_review_scope(self):
        self.subject_teacher_role.is_active = False
        self.subject_teacher_role.save(update_fields=["is_active"])
        self.assertFalse(can_access_student(self.subject_teacher, self.membership_a1))
        self.assertFalse(
            can_write_subject_comment(self.subject_teacher, self.membership_a1, self.cs_a)
        )

        self.homeroom_teacher_role.is_active = False
        self.homeroom_teacher_role.save(update_fields=["is_active"])
        self.assertFalse(can_review_student_report(self.homeroom_teacher, self.membership_a1))

    def test_withdrawn_student_is_removed_from_all_active_content_scopes(self):
        self.membership_a1.status = StudentSchoolMembership.Status.WITHDRAWN
        self.membership_a1.save(update_fields=["status"])

        self.assertFalse(can_access_student(self.student_user, self.membership_a1))
        self.assertFalse(can_access_student(self.guardian, self.membership_a1))
        self.assertFalse(can_access_student(self.subject_teacher, self.membership_a1))
        self.assertFalse(can_access_student(self.homeroom_teacher, self.membership_a1))
        self.assertFalse(
            can_write_subject_comment(self.subject_teacher, self.membership_a1, self.cs_a)
        )
        self.assertFalse(can_review_student_report(self.homeroom_teacher, self.membership_a1))

    def test_suspended_school_denies_operational_permissions(self):
        self.school_a.status = School.Status.SUSPENDED
        self.school_a.save(update_fields=["status"])

        self.assertFalse(can_access_student(self.student_user, self.membership_a1))
        self.assertFalse(can_access_student(self.guardian, self.membership_a1))
        self.assertFalse(can_access_student(self.subject_teacher, self.membership_a1))
        self.assertFalse(can_manage_academic_structure(self.academic_admin, self.school_a))
        self.assertFalse(can_manage_school_accounts(self.system_admin, self.school_a))
