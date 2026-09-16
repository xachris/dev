from django.core.exceptions import ValidationError
from django.db import transaction

from apps.academics.models import ClassGroup, StudentClassMembership
from apps.reports.models import ReportAction, StudentReport, SubjectComment
from apps.reports.policies import can_manage_report_cycles
from apps.reports.services import create_student_report
from apps.students.models import Student, StudentSchoolMembership

from .demo_data import ensure_demo_data


DEMO_ROSTER_SIZE = 18


@transaction.atomic
def ensure_demo_roster():
    """扩展 Pilot 为足以测试连续录入的纯虚拟班级。

    A001 保留学生/家长 Portal 演示；A002 起不创建登录账号，避免为了测试教师吞吐量
    额外制造无业务价值的账号。
    """
    data = ensure_demo_data()
    year = data["year"]
    cycle = data["cycle"]

    homeroom = ClassGroup.objects.get(academic_year=year, name="G8A")
    cs_group = ClassGroup.objects.get(academic_year=year, name="G8 CS")
    math_group = ClassGroup.objects.get(academic_year=year, name="G8 Math")

    reports = [data["report"]]
    for index in range(2, DEMO_ROSTER_SIZE + 1):
        student_number = f"A{index:03d}"
        full_name = f"演示学生 {index:02d}"

        membership = StudentSchoolMembership.objects.filter(
            school=data["school"],
            student_number=student_number,
        ).select_related("student").first()

        if membership is None:
            student = Student.objects.create(full_name=full_name)
            membership = StudentSchoolMembership.objects.create(
                school=data["school"],
                student=student,
                student_number=student_number,
                status=StudentSchoolMembership.Status.ACTIVE,
            )
        else:
            student = membership.student
            changed = False
            if student.full_name != full_name:
                student.full_name = full_name
                student.save(update_fields=["full_name", "updated_at"])
            if membership.status != StudentSchoolMembership.Status.ACTIVE:
                membership.status = StudentSchoolMembership.Status.ACTIVE
                changed = True
            if changed:
                membership.save(update_fields=["status", "updated_at"])

        for group in (homeroom, cs_group, math_group):
            relation, _ = StudentClassMembership.objects.get_or_create(
                student_membership=membership,
                class_group=group,
                defaults={"is_active": True},
            )
            if not relation.is_active:
                relation.is_active = True
                relation.save(update_fields=["is_active", "updated_at"])

        report = StudentReport.objects.filter(
            report_cycle=cycle,
            student_membership=membership,
        ).first()
        if report is None:
            report = create_student_report(
                actor=data["academic_admin"],
                report_cycle=cycle,
                student_membership=membership,
            )
        reports.append(report)

    return {**data, "reports": reports}


@transaction.atomic
def reset_demo_roster(*, actor):
    data = ensure_demo_roster()
    if not can_manage_report_cycles(actor, data["school"]):
        raise ValidationError("只有演示学校的学术管理员可以重置演示流程。")

    reports = StudentReport.objects.filter(report_cycle=data["cycle"])
    ReportAction.objects.filter(report__in=reports).delete()
    SubjectComment.objects.filter(report__in=reports).update(
        created_by=None,
        student_feedback="",
        guardian_message="",
        staff_note="",
        status=SubjectComment.Status.DRAFT,
        submitted_by=None,
        submitted_at=None,
    )
    reports.update(
        status=StudentReport.Status.DRAFT,
        published_by=None,
        published_at=None,
    )
    return data["report"]
