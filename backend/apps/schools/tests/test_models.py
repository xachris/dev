from datetime import date

from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from apps.schools.models import AcademicYear, School


class SchoolTenantFoundationTests(TestCase):
    def setUp(self):
        self.school_a = School.objects.create(code="school-a", name="测试学校 A")
        self.school_b = School.objects.create(code="school-b", name="测试学校 B")

    def create_year(self, school, name="2026-2027"):
        return AcademicYear.objects.create(
            school=school,
            name=name,
            starts_on=date(2026, 8, 1),
            ends_on=date(2027, 7, 31),
        )

    def test_school_code_is_unique(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            School.objects.create(code="school-a", name="重复代码学校")

    def test_same_academic_year_name_is_allowed_across_schools(self):
        year_a = self.create_year(self.school_a)
        year_b = self.create_year(self.school_b)

        self.assertEqual(year_a.name, year_b.name)
        self.assertNotEqual(year_a.school_id, year_b.school_id)

    def test_duplicate_academic_year_name_is_rejected_within_same_school(self):
        self.create_year(self.school_a)

        with self.assertRaises(IntegrityError), transaction.atomic():
            self.create_year(self.school_a)

    def test_for_school_scope_does_not_return_other_school_records(self):
        year_a = self.create_year(self.school_a)
        self.create_year(self.school_b)

        result = list(AcademicYear.objects.for_school(self.school_a))

        self.assertEqual(result, [year_a])

    def test_invalid_academic_year_date_range_is_rejected(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            AcademicYear.objects.create(
                school=self.school_a,
                name="invalid",
                starts_on=date(2027, 8, 1),
                ends_on=date(2027, 7, 31),
            )

    def test_school_with_academic_year_cannot_be_deleted(self):
        self.create_year(self.school_a)

        with self.assertRaises(ProtectedError):
            self.school_a.delete()
