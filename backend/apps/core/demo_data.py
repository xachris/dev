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
from apps.reports.models import ReportCycle, StudentReport
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
    if user.display_name != display_name:
        user.display_name = display_name
    user.set_password(_password())
    user.is_active = True
    user.save()
    return user


@transaction.atomic
def ensure_demo_data():
    """创建或修复一套可重复使用的纯虚拟 Pilot 数据。

    该函数故意幂等：部署重启可以安全重复执行，不会制造第二个演示学生、
    第二套角色或第二份报告。
    """
    school, _ = School.objects.get_or_create(
        code=DEMO_SCHOOL_CODE,
        defaults={"name": "演示国际学校"},
    )
    changed = False
    if school.name != "演示国际学校":
        school.name = "演示国际学校"
        changed = True
    if school.status != School.Status.ACTIVE:
        school.status = School.Status.ACTIVE
        changed = True
    if changed:
        school.save()

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
    academic_role, _ = RoleAssignment.objects.get_or_create(
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
    for role in (cs_role, math_role, homeroom_role, academic_role):
        if not role.is_active:
            role.is_active = True
            role.save(update_fields=["is_active", "updated_at"])

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
        user_account=student_user,
        defaults={"full_name": "学生 A"},
    )
    if student.full_name != "学生 A":
        student.full_name = "学生 A"
        student.save(update_fields=["full_name", "updated_at"])

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
        relation, _ = StudentClassMembership.objects.get_or_create(
            student_membership=membership,
            class_group=group,
            defaults={"is_active": True},
        )
        if not relation.is_active:
            relation.is_active = True
            relation.save(update_fields=["is_active", "updated_at"])

    guardian_relation, _ = GuardianRelationship.objects.get_or_create(
        student_membership=membership,
        guardian=guardian,
        defaults={"is_active": True},
    )
    if not guardian_relation.is_active:
        guardian_relation.is_active = True
        guardian_relation.save(update_fields=["is_active", "updated_at"])

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
    """兼容旧 Pilot 入口，但 Phase 7 起重置整个演示花名册，而不是只重置 A001。"""
    from .demo_roster import reset_demo_roster

    return reset_demo_roster(actor=actor)
