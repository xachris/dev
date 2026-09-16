"""集中式业务权限策略。

这里的函数回答“当前用户基于真实业务关系可以做什么”，不依赖页面是否显示按钮，
也不把 Django superuser 自动等同于学校业务权限。

原则：
- 默认拒绝；
- 学校、账号和上游关系状态共同决定权限；
- 学生空间访问不等于查看所有学生内容；
- 学生内容访问与技术账号管理分离；
- 后续 View / API / Service 应调用这里，而不是各自复制权限判断。
"""

from django.db.models import Q, QuerySet

from apps.accounts.models import RoleAssignment, UserAccount
from apps.academics.models import HomeroomAssignment, Subject, TeachingAssignment
from apps.schools.models import School
from apps.students.models import StudentSchoolMembership


def _active_authenticated_user(user) -> bool:
    return bool(
        user
        and getattr(user, "is_authenticated", False)
        and getattr(user, "is_active", False)
    )


def _operational_school(school: School) -> bool:
    return bool(school and school.status == School.Status.ACTIVE)


def _empty_student_memberships() -> QuerySet:
    return StudentSchoolMembership.objects.none()


def _has_active_role(user: UserAccount, school: School, role: str) -> bool:
    if not _active_authenticated_user(user) or not _operational_school(school):
        return False
    return RoleAssignment.objects.filter(
        school=school,
        user=user,
        role=role,
        is_active=True,
    ).exists()


def visible_student_memberships_for(user: UserAccount, school: School) -> QuerySet:
    """返回当前用户在该校可进入“学生业务空间”的在读学生关系。

    这是 roster / context 级访问范围，不代表有权读取该学生的全部内容。
    Phase 6 起，报告中的学生可见、家长专属、教职工内部内容还必须继续通过
    具体对象与内容级 Policy 判断。

    当前允许来源：
    - 学生本人；
    - 有效家长 / 监护人关系；
    - 当前有效学年的任课关系覆盖的学生；
    - 当前有效学年的班主任关系覆盖的学生。

    学术管理员和学校系统管理员不会因为角色本身自动获得学生教育内容读取权。
    """
    if not _active_authenticated_user(user) or not _operational_school(school):
        return _empty_student_memberships()

    teaching_group_ids = TeachingAssignment.objects.active().filter(
        teacher_role__user=user,
        teacher_role__school=school,
        class_group__academic_year__school=school,
        class_group__academic_year__is_active=True,
    ).values("class_group_id")

    homeroom_group_ids = HomeroomAssignment.objects.active().filter(
        teacher_role__user=user,
        teacher_role__school=school,
        class_group__academic_year__school=school,
        class_group__academic_year__is_active=True,
    ).values("class_group_id")

    return (
        StudentSchoolMembership.objects.filter(
            school=school,
            status=StudentSchoolMembership.Status.ACTIVE,
        )
        .filter(
            Q(student__user_account=user)
            | Q(
                guardian_relationships__guardian=user,
                guardian_relationships__is_active=True,
            )
            | Q(
                class_memberships__is_active=True,
                class_memberships__class_group_id__in=teaching_group_ids,
            )
            | Q(
                class_memberships__is_active=True,
                class_memberships__class_group_id__in=homeroom_group_ids,
            )
        )
        .distinct()
    )


def can_access_student_space(
    user: UserAccount,
    student_membership: StudentSchoolMembership,
) -> bool:
    """是否可以进入该学生在该校的业务空间。

    注意：返回 True 只表示存在基本业务关系，不表示可以读取所有报告字段、
    家长专属内容或教职工内部内容。
    """
    if not student_membership:
        return False
    return visible_student_memberships_for(user, student_membership.school).filter(
        pk=student_membership.pk
    ).exists()


def writable_student_memberships_for_subject(
    user: UserAccount,
    school: School,
    subject: Subject,
) -> QuerySet:
    """返回教师可为指定学科创建评价的当前在读学生范围。"""
    if (
        not _active_authenticated_user(user)
        or not _operational_school(school)
        or not subject
        or subject.school_id != school.id
    ):
        return _empty_student_memberships()

    teaching_group_ids = TeachingAssignment.objects.active().filter(
        teacher_role__user=user,
        teacher_role__school=school,
        subject=subject,
        class_group__academic_year__school=school,
        class_group__academic_year__is_active=True,
    ).values("class_group_id")

    return (
        StudentSchoolMembership.objects.filter(
            school=school,
            status=StudentSchoolMembership.Status.ACTIVE,
            class_memberships__is_active=True,
            class_memberships__class_group_id__in=teaching_group_ids,
        )
        .distinct()
    )


def can_write_subject_comment(
    user: UserAccount,
    student_membership: StudentSchoolMembership,
    subject: Subject,
) -> bool:
    """教师是否能给该学生写这一学科的评价。"""
    if not student_membership or not subject:
        return False
    return writable_student_memberships_for_subject(
        user,
        student_membership.school,
        subject,
    ).filter(pk=student_membership.pk).exists()


def reviewable_student_memberships_for(user: UserAccount, school: School) -> QuerySet:
    """返回当前班主任可以审核完整报告的当前在读学生范围。"""
    if not _active_authenticated_user(user) or not _operational_school(school):
        return _empty_student_memberships()

    homeroom_group_ids = HomeroomAssignment.objects.active().filter(
        teacher_role__user=user,
        teacher_role__school=school,
        class_group__academic_year__school=school,
        class_group__academic_year__is_active=True,
    ).values("class_group_id")

    return (
        StudentSchoolMembership.objects.filter(
            school=school,
            status=StudentSchoolMembership.Status.ACTIVE,
            class_memberships__is_active=True,
            class_memberships__class_group__group_type="HOMEROOM",
            class_memberships__class_group_id__in=homeroom_group_ids,
        )
        .distinct()
    )


def can_review_student_report(
    user: UserAccount,
    student_membership: StudentSchoolMembership,
) -> bool:
    """班主任是否能审核该学生的完整报告。

    学术管理员的升级 / 覆盖审核将在真实报告工作流存在后单独建模，
    此处不因为管理员角色而默认放宽读取或审批权限。
    """
    if not student_membership:
        return False
    return reviewable_student_memberships_for(user, student_membership.school).filter(
        pk=student_membership.pk
    ).exists()


def can_manage_academic_structure(user: UserAccount, school: School) -> bool:
    """是否可以维护班级、学科、任课等学术组织关系。"""
    return _has_active_role(user, school, RoleAssignment.Role.ACADEMIC_ADMIN)


def can_manage_school_accounts(user: UserAccount, school: School) -> bool:
    """是否可以执行学校范围内的业务账号管理。

    该权限不等于读取学生教育内容。
    """
    return _has_active_role(user, school, RoleAssignment.Role.SYSTEM_ADMIN)
