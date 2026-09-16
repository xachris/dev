from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from apps.accounts.models import RoleAssignment, UserAccount
from apps.schools.models import School
from apps.students.models import GuardianRelationship, Student, StudentSchoolMembership


class StudentIdentityRelationshipTests(TestCase):
    def setUp(self):
        self.school_a = School.objects.create(code="school-a", name="测试学校 A")
        self.school_b = School.objects.create(code="school-b", name="测试学校 B")
        self.student = Student.objects.create(full_name="测试学生")

    def membership(self, school, number):
        return StudentSchoolMembership.objects.create(
            school=school,
            student=self.student,
            student_number=number,
        )

    def test_student_can_exist_without_login_account(self):
        self.assertIsNone(self.student.user_account)

    def test_student_can_be_linked_to_one_login_account(self):
        account = UserAccount.objects.create_user(username="student.login", password="test-password-only")
        self.student.user_account = account
        self.student.save(update_fields=["user_account"])

        self.assertEqual(account.student_identity, self.student)

    def test_same_student_can_have_memberships_in_multiple_schools(self):
        membership_a = self.membership(self.school_a, "S001")
        membership_b = self.membership(self.school_b, "B900")

        self.assertNotEqual(membership_a.school_id, membership_b.school_id)
        self.assertEqual(membership_a.student_id, membership_b.student_id)
        self.assertEqual(list(Student.objects.for_school(self.school_a)), [self.student])
        self.assertEqual(list(Student.objects.for_school(self.school_b)), [self.student])

    def test_same_student_number_is_allowed_in_different_schools(self):
        self.membership(self.school_a, "S001")
        self.membership(self.school_b, "S001")
        self.assertEqual(StudentSchoolMembership.objects.count(), 2)

    def test_duplicate_student_number_is_rejected_inside_one_school(self):
        self.membership(self.school_a, "S001")
        another_student = Student.objects.create(full_name="另一名学生")

        with self.assertRaises(IntegrityError), transaction.atomic():
            StudentSchoolMembership.objects.create(
                school=self.school_a,
                student=another_student,
                student_number="S001",
            )

    def test_duplicate_membership_for_same_student_and_school_is_rejected(self):
        self.membership(self.school_a, "S001")

        with self.assertRaises(IntegrityError), transaction.atomic():
            self.membership(self.school_a, "S002")

    def test_guardian_authorisation_is_scoped_through_school_membership(self):
        membership_a = self.membership(self.school_a, "S001")
        membership_b = self.membership(self.school_b, "B900")
        guardian = UserAccount.objects.create_user(username="guardian.one", password="test-password-only")
        relationship = GuardianRelationship.objects.create(
            student_membership=membership_a,
            guardian=guardian,
        )

        self.assertEqual(list(GuardianRelationship.objects.for_school(self.school_a)), [relationship])
        self.assertEqual(list(GuardianRelationship.objects.for_school(self.school_b)), [])
        self.assertNotEqual(membership_a.school_id, membership_b.school_id)

    def test_one_account_can_be_guardian_and_school_staff(self):
        membership_a = self.membership(self.school_a, "S001")
        adult = UserAccount.objects.create_user(
            username="adult.one",
            password="test-password-only",
            display_name="家长兼教师",
        )
        GuardianRelationship.objects.create(student_membership=membership_a, guardian=adult)
        RoleAssignment.objects.create(
            school=self.school_a,
            user=adult,
            role=RoleAssignment.Role.TEACHER,
        )

        self.assertTrue(GuardianRelationship.objects.active().filter(guardian=adult).exists())
        self.assertTrue(RoleAssignment.objects.filter(user=adult, school=self.school_a).exists())

    def test_student_with_school_membership_cannot_be_deleted(self):
        self.membership(self.school_a, "S001")
        with self.assertRaises(ProtectedError):
            self.student.delete()
