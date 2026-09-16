from apps.academics.models import TeachingAssignment
from apps.reports.models import ReportCycle, SubjectComment
from apps.students.models import StudentSchoolMembership


def assignment_comments(assignment, report_cycle):
    """返回一个真实任课关系在某报告周期内可处理的评价槽。

    这里不按“全校 + 学科”粗筛，必须同时经过任课分组、学年和在读关系，
    让批量入口与单学生权限保持同一事实来源。
    """
    if report_cycle.academic_year_id != assignment.class_group.academic_year_id:
        return SubjectComment.objects.none()

    student_membership_ids = assignment.class_group.student_memberships.filter(
        is_active=True,
        student_membership__status=StudentSchoolMembership.Status.ACTIVE,
    ).values("student_membership_id")

    return (
        SubjectComment.objects.filter(
            subject=assignment.subject,
            report__report_cycle=report_cycle,
            report__student_membership_id__in=student_membership_ids,
        )
        .select_related(
            "subject",
            "report",
            "report__student_membership__student",
            "report__report_cycle",
            "report__report_cycle__academic_year__school",
        )
        .order_by("report__student_membership__student_number")
    )


def teacher_batch_entries(user):
    """教师工作台中的“班级 / 学科 / 报告周期”高吞吐入口。"""
    assignments = (
        TeachingAssignment.objects.active()
        .filter(
            teacher_role__user=user,
            class_group__academic_year__is_active=True,
        )
        .select_related(
            "subject",
            "class_group",
            "class_group__academic_year",
            "class_group__academic_year__school",
        )
        .order_by("class_group__name", "subject__code")
    )

    entries = []
    for assignment in assignments:
        cycles = ReportCycle.objects.filter(
            academic_year=assignment.class_group.academic_year,
        ).order_by("name")
        for cycle in cycles:
            comments = assignment_comments(assignment, cycle)
            total = comments.count()
            if not total:
                continue
            submitted = comments.filter(status=SubjectComment.Status.SUBMITTED).count()
            returned = comments.filter(status=SubjectComment.Status.RETURNED).count()
            entries.append(
                {
                    "assignment": assignment,
                    "cycle": cycle,
                    "total": total,
                    "submitted": submitted,
                    "remaining": total - submitted,
                    "returned": returned,
                }
            )
    return entries
