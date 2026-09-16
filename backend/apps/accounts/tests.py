from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.accounts.models import RoleAssignment, UserAccount
from apps.schools.models import School


class UserAccountAndRoleTests(TestCase):
    def setUp(self):
        self.school_a = School.objects.create(code="school-a", name="测试学校 A")
        self.school_b = School.objects.create(code="school-b", name="测试学校 B")
        self.user = UserAccount.objects.create_user(
            username="teacher.one",
            password="test-password-only",
            display_name="测试教师",
        )

    def test_display_name_is_not_required_for_identity(self):
        user = UserAccount.objects.create_user(username="plain-user", password="test-password-only")
        self.assertEqual(str(user), "plain-user")

    def test_same_account_can_hold_roles_in_multiple_schools(self):
        RoleAssignment.objects.create(
            school=self.school_a,
            user=self.user,
            role=RoleAssignment.Role.TEACHER,
        )
        RoleAssignment.objects.create(
            school=self.school_b,
            user=self.user,
            role=RoleAssignment.Role.ACADEMIC_ADMIN,
        )

        self.assertEqual(RoleAssignment.objects.filter(user=self.user).count(), 2)

    def test_duplicate_role_assignment_is_rejected(self):
        RoleAssignment.objects.create(
            school=self.school_a,
            user=self.user,
            role=RoleAssignment.Role.TEACHER,
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            RoleAssignment.objects.create(
                school=self.school_a,
                user=self.user,
                role=RoleAssignment.Role.TEACHER,
            )

    def test_role_assignment_is_school_scoped(self):
        role_a = RoleAssignment.objects.create(
            school=self.school_a,
            user=self.user,
            role=RoleAssignment.Role.TEACHER,
        )
        RoleAssignment.objects.create(
            school=self.school_b,
            user=self.user,
            role=RoleAssignment.Role.TEACHER,
        )

        self.assertEqual(list(RoleAssignment.objects.for_school(self.school_a)), [role_a])
