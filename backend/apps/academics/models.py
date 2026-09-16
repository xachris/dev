import uuid

from django.core.exceptions import ValidationError
from django.db import models

from apps.accounts.models import RoleAssignment
from apps.core.models import SchoolScopedModel
from apps.schools.models import AcademicYear
from apps.students.models import StudentSchoolMembership


class ClassGroupQuerySet(models.QuerySet):
    def for_school(self, school):
        return self.filter(academic_year__school=school)


class ClassGroup(models.Model):
    """一个学年中的学生组织单元。

    HOMEROOM 用于班主任管理与完整报告审核；TEACHING 用于分层教学、选课组等实际授课组合。
    同一个学生可以同时属于一个 HOMEROOM 组和多个 TEACHING 组。
    """

    class GroupType(models.TextChoices):
        HOMEROOM = "HOMEROOM", "行政 / 班主任班级"
        TEACHING = "TEACHING", "教学分组"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name="class_groups",
        verbose_name="学年",
    )
    name = models.CharField("班级 / 分组名称", max_length=100)
    group_type = models.CharField(
        "分组类型",
        max_length=16,
        choices=GroupType.choices,
        default=GroupType.HOMEROOM,
    )
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    objects = ClassGroupQuerySet.as_manager()

    class Meta:
        verbose_name = "班级 / 教学分组"
        verbose_name_plural = "班级 / 教学分组"
        ordering = ["academic_year__starts_on", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["academic_year", "name"],
                name="uniq_class_group_name_per_academic_year",
            )
        ]

    @property
    def school(self):
        return self.academic_year.school

    def __str__(self) -> str:
        return f"{self.academic_year.school.code} / {self.academic_year.name} / {self.name}"


class Subject(SchoolScopedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField("学科代码", max_length=32)
    name = models.CharField("学科名称", max_length=120)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "学科"
        verbose_name_plural = "学科"
        ordering = ["code"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "code"],
                name="uniq_subject_code_per_school",
            )
        ]

    def save(self, *args, **kwargs):
        # 学科代码是机器和业务共同使用的稳定标识。统一大小写，避免 CS / cs 成为两门“不同”学科。
        self.code = self.code.strip().upper()
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.school.code} / {self.code} / {self.name}"


class StudentClassMembershipQuerySet(models.QuerySet):
    def for_school(self, school):
        return self.filter(class_group__academic_year__school=school)

    def active(self):
        """有效班级关系由本关系和上游学生在读状态共同决定。"""
        return self.filter(
            is_active=True,
            student_membership__status=StudentSchoolMembership.Status.ACTIVE,
        )


class StudentClassMembership(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student_membership = models.ForeignKey(
        StudentSchoolMembership,
        on_delete=models.PROTECT,
        related_name="class_memberships",
        verbose_name="学生学校关系",
    )
    class_group = models.ForeignKey(
        ClassGroup,
        on_delete=models.PROTECT,
        related_name="student_memberships",
        verbose_name="班级 / 教学分组",
    )
    is_active = models.BooleanField("关系本身有效", default=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    objects = StudentClassMembershipQuerySet.as_manager()

    class Meta:
        verbose_name = "学生班级关系"
        verbose_name_plural = "学生班级关系"
        constraints = [
            models.UniqueConstraint(
                fields=["student_membership", "class_group"],
                name="uniq_student_class_membership",
            )
        ]

    def clean(self):
        errors = {}
        class_school_id = self.class_group.academic_year.school_id
        if self.student_membership.school_id != class_school_id:
            errors["class_group"] = "学生学校关系与班级必须属于同一所学校。"

        if self.is_active and self.student_membership.status != StudentSchoolMembership.Status.ACTIVE:
            errors["is_active"] = "非在读学生不能拥有新的有效班级关系。"

        if (
            self.is_active
            and self.class_group.group_type == ClassGroup.GroupType.HOMEROOM
            and StudentClassMembership.objects.active()
            .filter(
                student_membership=self.student_membership,
                class_group__academic_year=self.class_group.academic_year,
                class_group__group_type=ClassGroup.GroupType.HOMEROOM,
            )
            .exclude(pk=self.pk)
            .exists()
        ):
            errors["class_group"] = "同一学年中，一名在读学生只能有一个有效班主任班级。"

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.student_membership} / {self.class_group.name}"


class TeachingAssignmentQuerySet(models.QuerySet):
    def for_school(self, school):
        return self.filter(class_group__academic_year__school=school)

    def active(self):
        """任课关系只有在关系、教师角色和账号都有效时才实际生效。"""
        return self.filter(
            is_active=True,
            teacher_role__is_active=True,
            teacher_role__user__is_active=True,
        )


class TeachingAssignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    teacher_role = models.ForeignKey(
        RoleAssignment,
        on_delete=models.PROTECT,
        related_name="teaching_assignments",
        verbose_name="教师角色授权",
    )
    class_group = models.ForeignKey(
        ClassGroup,
        on_delete=models.PROTECT,
        related_name="teaching_assignments",
        verbose_name="班级 / 教学分组",
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.PROTECT,
        related_name="teaching_assignments",
        verbose_name="学科",
    )
    is_active = models.BooleanField("关系本身有效", default=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    objects = TeachingAssignmentQuerySet.as_manager()

    class Meta:
        verbose_name = "任课关系"
        verbose_name_plural = "任课关系"
        constraints = [
            models.UniqueConstraint(
                fields=["teacher_role", "class_group", "subject"],
                name="uniq_teaching_assignment",
            )
        ]

    def clean(self):
        errors = {}
        class_school_id = self.class_group.academic_year.school_id

        if self.teacher_role.role != RoleAssignment.Role.TEACHER:
            errors["teacher_role"] = "任课关系必须使用教师角色授权。"
        elif self.is_active and not self.teacher_role.is_active:
            errors["teacher_role"] = "无效的教师角色不能创建新的有效任课关系。"
        elif self.is_active and not self.teacher_role.user.is_active:
            errors["teacher_role"] = "已停用账号不能创建新的有效任课关系。"

        if self.teacher_role.school_id != class_school_id:
            errors["teacher_role"] = "教师角色与班级必须属于同一所学校。"

        if self.subject.school_id != class_school_id:
            errors["subject"] = "学科与班级必须属于同一所学校。"

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    @property
    def teacher(self):
        return self.teacher_role.user

    def __str__(self) -> str:
        return f"{self.teacher_role.user} / {self.subject.code} / {self.class_group.name}"


class HomeroomAssignmentQuerySet(models.QuerySet):
    def for_school(self, school):
        return self.filter(class_group__academic_year__school=school)

    def active(self):
        """班主任关系只有在关系、教师角色和账号都有效时才实际生效。"""
        return self.filter(
            is_active=True,
            teacher_role__is_active=True,
            teacher_role__user__is_active=True,
        )


class HomeroomAssignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    teacher_role = models.ForeignKey(
        RoleAssignment,
        on_delete=models.PROTECT,
        related_name="homeroom_assignments",
        verbose_name="教师角色授权",
    )
    class_group = models.ForeignKey(
        ClassGroup,
        on_delete=models.PROTECT,
        related_name="homeroom_assignments",
        verbose_name="班主任班级",
    )
    is_active = models.BooleanField("关系本身有效", default=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    objects = HomeroomAssignmentQuerySet.as_manager()

    class Meta:
        verbose_name = "班主任关系"
        verbose_name_plural = "班主任关系"
        constraints = [
            models.UniqueConstraint(
                fields=["teacher_role", "class_group"],
                name="uniq_homeroom_assignment",
            )
        ]

    def clean(self):
        errors = {}
        class_school_id = self.class_group.academic_year.school_id

        if self.teacher_role.role != RoleAssignment.Role.TEACHER:
            errors["teacher_role"] = "班主任关系必须使用教师角色授权。"
        elif self.is_active and not self.teacher_role.is_active:
            errors["teacher_role"] = "无效的教师角色不能创建新的有效班主任关系。"
        elif self.is_active and not self.teacher_role.user.is_active:
            errors["teacher_role"] = "已停用账号不能创建新的有效班主任关系。"

        if self.teacher_role.school_id != class_school_id:
            errors["teacher_role"] = "教师角色与班主任班级必须属于同一所学校。"

        if self.class_group.group_type != ClassGroup.GroupType.HOMEROOM:
            errors["class_group"] = "班主任只能绑定 HOMEROOM 类型班级。"

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    @property
    def teacher(self):
        return self.teacher_role.user

    def __str__(self) -> str:
        return f"{self.teacher_role.user} / {self.class_group.name}"
