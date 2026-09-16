import uuid

from django.conf import settings
from django.db import models

from apps.core.models import SchoolScopedModel


class StudentQuerySet(models.QuerySet):
    def for_school(self, school):
        """只返回在指定学校存在成员关系的学生。"""
        return self.filter(school_memberships__school=school).distinct()


class Student(models.Model):
    """平台层面的学生身份。

    UUID 是平台稳定身份，不因学校、班级或登录方式变化而改变。
    学校内部可见的学号保存在 StudentSchoolMembership.student_number 中。
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_account = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="student_identity",
        null=True,
        blank=True,
        verbose_name="学生登录账号",
        help_text="学生可以暂时没有登录账号；账号与学生业务身份保持分离。",
    )
    full_name = models.CharField("学生姓名", max_length=150)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    objects = StudentQuerySet.as_manager()

    class Meta:
        verbose_name = "学生"
        verbose_name_plural = "学生"
        ordering = ["full_name"]

    def __str__(self) -> str:
        return self.full_name


class StudentSchoolMembership(SchoolScopedModel):
    """学生与学校的稳定成员关系。

    一名学生在同一学校只保留一条成员记录，通过状态变化表达转学、暂停或校友，
    避免退学后重新入学就产生第二个“同一个学生”。
    """

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "在读"
        SUSPENDED = "SUSPENDED", "暂停"
        WITHDRAWN = "WITHDRAWN", "已离校"
        ALUMNI = "ALUMNI", "校友"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        Student,
        on_delete=models.PROTECT,
        related_name="school_memberships",
        verbose_name="学生",
    )
    student_number = models.CharField(
        "学校学号",
        max_length=64,
        help_text="该学生在本校内稳定使用的学号；同一学校内唯一。",
    )
    status = models.CharField(
        "状态",
        max_length=16,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "学生学校关系"
        verbose_name_plural = "学生学校关系"
        constraints = [
            models.UniqueConstraint(
                fields=["school", "student"],
                name="uniq_student_membership_per_school",
            ),
            models.UniqueConstraint(
                fields=["school", "student_number"],
                name="uniq_student_number_per_school",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.school.code} / {self.student_number} / {self.student.full_name}"


class GuardianRelationshipQuerySet(models.QuerySet):
    def for_school(self, school):
        return self.filter(student_membership__school=school)

    def active(self):
        return self.filter(is_active=True)


class GuardianRelationship(models.Model):
    """某一学校明确授权的家长 / 监护人与学生关系。

    关系直接绑定 StudentSchoolMembership，而不是只绑定全局 Student，确保“家长能否看
    某所学校里的学生资料”是学校范围内的授权事实。
    """

    class RelationshipType(models.TextChoices):
        PARENT = "PARENT", "家长"
        LEGAL_GUARDIAN = "LEGAL_GUARDIAN", "法定监护人"
        OTHER_AUTHORISED = "OTHER_AUTHORISED", "其他授权监护人"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student_membership = models.ForeignKey(
        StudentSchoolMembership,
        on_delete=models.PROTECT,
        related_name="guardian_relationships",
        verbose_name="学生学校关系",
    )
    guardian = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="guardian_relationships",
        verbose_name="家长 / 监护人账号",
    )
    relationship_type = models.CharField(
        "关系类型",
        max_length=24,
        choices=RelationshipType.choices,
        default=RelationshipType.PARENT,
    )
    is_active = models.BooleanField("有效", default=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    objects = GuardianRelationshipQuerySet.as_manager()

    class Meta:
        verbose_name = "家长学生关系"
        verbose_name_plural = "家长学生关系"
        constraints = [
            models.UniqueConstraint(
                fields=["student_membership", "guardian"],
                name="uniq_guardian_per_student_membership",
            )
        ]

    def __str__(self) -> str:
        return f"{self.student_membership} / {self.guardian}"
