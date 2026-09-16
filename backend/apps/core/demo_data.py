from datetime import date

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction

from apps.accounts.models import RoleAssignment, UserAccount
from apps.academics.models import (
    ClassGroup,
    HomeroomAssignment,
    StudentClassMembership,
    Subject,
    TeachingAssignment,
)
from apps.reports.models import ReportAction, ReportCycle, StudentReport, SubjectComment
from apps.reports.policies import can_manage_report_cycles
from apps.reports.services import create_student_report
from apps.schools.models import AcademicYear, School
from apps.students.models import GuardianRelationship, Student, StudentSchoolMembership


DEMO_SCHOOL_CODE = "DEMO"
DEMO_YEAR_NAME = "2026-2027"
DEMO_CYCLE_NAME = "Term 1"


def _password():
    return getattr(settings, "DEMO_PASSWORD", "") or "DemoOnly-2026!"


def _user(username: str, display_name: str):
    user, _ = UserAccount.objects.get_or_create(
        username=username,
        defaults={"display_name": display_name},
    )
    changed = False
    if user.display_name != display_name:
        user.display_name = display_name
        changed = True
    user.set_password(_password())
    user.is_active = True
    user.save()
    return user


@transaction.atomic
def ensure_demo_data():
    school, _ = School.objects.get_or_create(
        code=DEMO_SCHOOL_CODE,
        defaults={"name": "演示国际学校"},
    )
    if school.status != School.Status.ACTIVE:
        school.status = School.Status.ACTIVE
        school.save(update_fields=["status", "updated_at"])

    year, _ = AcademicYear.objects.get_or_create(
        school=school,
        name=DEMO_YEAR_NAME,
        defaults={
            "starts_on": date(2026, 8, 1),
            "ends_on": date(2027, 7, 31),
            "is_active": True,
        },
    )
    if not year.is_active:
        year.is_active = True
        year.save(update_fields=["is_active", "updated_at"])

    homeroom, _ = ClassGroup.objects.get_or_create(
        academic_year=year,
        name="G8A",
        defaults={"group_type": ClassGroup.GroupType.HOMEROOM},
    )
    cs_group, _ = ClassGroup.objects.get_or_create(
        academic_year=year,
        name="G8 CS",
        defaults={"group_type": ClassGroup.GroupType.TEACHING},
    )
    math_group, _ = ClassGroup.objects.get_or_create(
        academic_year=year,
        name="G8 Math",
        defaults={"group_type": ClassGroup.GroupType.TEACHING},
    )

    cs, _ = Subject.objects.get_or_create(
        school=school,
        code="CS",
        defaults={"name": "Computer Science"},
    )
    math, _ = Subject.objects.get_or_create(
        school=school,
        code="MATH",
        defaults={"name": "Mathematics"},
    )

    cs_teacher = _user("teacher.cs", "CS 教师")
    math_teacher = _user("teacher.math", "数学教师")
    homeroom_teacher = _user("homeroom.g8a", "G8A 班主任")
    academic_admin = _user("academic.admin", "学术管理员")
    system_admin = _user("system.admin", "系统管理员")
    student_user = _user("student.a001", "学生 A001")
    guardian = _user("guardian.a001", "家长 A001")

    cs_role, _ = RoleAssignment.objects.get_or_create(
        school=school,
        user=cs_teacher,
        role=RoleAssignment.Role.TEACHER,
        defaults={"is_active": True},
    )
    math_role, _ = RoleAssignment.objects.get_or_create(
        school=school,
        user=math_teacher,
        role=RoleAssignment.Role.TEACHER,
        defaults={"is_active": True},
    )
    homeroom_role, _ = RoleAssignment.objects.get_or_create(
        school=school,
        user=homeroom_teacher,
        role=RoleAssignment.Role.TEACHER,
        defaults={"is_active": True},
    )
    RoleAssignment.objects.get_or_create(
        school=school,
        user=academic_admin,
        role=RoleAssignment.Role.ACADEMIC_ADMIN,
        defaults={"is_active": True},
    )
    RoleAssignment.objects.get_or_create(
        school=school,
        user=system_admin,
        role=RoleAssignment.Role.SYSTEM_ADMIN,
        defaults={"is_active": True},
    )

    TeachingAssignment.objects.get_or_create(
        teacher_role=cs_role,
        class_group=cs_group,
        subject=cs,
        defaults={"is_active": True},
    )
    TeachingAssignment.objects.get_or_create(
        teacher_role=math_role,
        class_group=math_group,
        subject=math,
        defaults={"is_active": True},
    )
    HomeroomAssignment.objects.get_or_create(
        teacher_role=homeroom_role,
        class_group=homeroom,
        defaults={"is_active": True},
    )

    student, _ = Student.objects.get_or_create(
        full_name="学生 A",
        defaults={"user_account": student_user},
    )
    if student.user_account_id != student_user.id:
        student.user_account = student_user
        student.save(update_fields=["user_account", "updated_at"])

    membership, _ = StudentSchoolMembership.objects.get_or_create(
        school=school,
        student=student,
        defaults={"student_number": "A001", "status": StudentSchoolMembership.Status.ACTIVE},
    )
    changed = False
    if membership.student_number != "A001":
        membership.student_number = "A001"
        changed = True
    if membership.status != StudentSchoolMembership.Status.ACTIVE:
        membership.status = StudentSchoolMembership.Status.ACTIVE
        changed = True
    if changed:
        membership.save()

    for group in (homeroom, cs_group, math_group):
        StudentClassMembership.objects.get_or_create(
            student_membership=membership,
            class_group=group,
            defaults={"is_active": True},
        )

    GuardianRelationship.objects.get_or_create(
        student_membership=membership,
        guardian=guardian,
        defaults={"is_active": True},
    )

    cycle, _ = ReportCycle.objects.get_or_create(
        academic_year=year,
        name=DEMO_CYCLE_NAME,
    )
    report = StudentReport.objects.filter(
        report_cycle=cycle,
        student_membership=membership,
    ).first()
    if report is None:
        report = create_student_report(
            actor=academic_admin,
            report_cycle=cycle,
            student_membership=membership,
        )

    return {
        "school": school,
        "year": year,
        "cycle": cycle,
        "report": report,
        "academic_admin": academic_admin,
    }


@transaction.atomic
def reset_demo_workflow(*, actor):
    data = ensure_demo_data()
    school = data["school"]
    if not can_manage_report_cycles(actor, school):
        raise ValidationError("只有演示学校的学术管理员可以重置演示流程。")

    report = data["report"]
    ReportAction.objects.filter(report=report).delete()
    report.subject_comments.update(
        created_by=None,
        student_feedback="",
        guardian_message="",
        staff_note="",
        status=SubjectComment.Status.DRAFT,
        submitted_by=None,
        submitted_at=None,
    )
    report.status = StudentReport.Status.DRAFT
    report.published_by = None
    report.published_at = None
    report.save(update_fields=["status", "published_by", "published_at", "updated_at"])
    return report
