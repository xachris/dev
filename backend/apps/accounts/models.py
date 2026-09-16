import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.core.models import SchoolScopedModel


class UserAccount(AbstractUser):
    """平台登录身份。

    登录身份与学生、家长、教职工等业务身份分离。同一个账号未来可以同时
    承担多个业务身份，例如“某校教师 + 某学生家长”，避免重复账号和重复资料。
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    display_name = models.CharField(
        "显示名称",
        max_length=150,
        blank=True,
        help_text="用于界面显示，不作为身份关系或权限判断主键。",
    )

    class Meta:
        verbose_name = "用户账号"
        verbose_name_plural = "用户账号"

    def __str__(self) -> str:
        return self.display_name.strip() or self.get_full_name().strip() or self.username


class RoleAssignment(SchoolScopedModel):
    """学校范围内需要显式授予的工作人员角色。

    学生和家长身份不在这里重复记录：
    - 学生身份来自 Student.user_account + StudentSchoolMembership；
    - 家长身份来自 GuardianRelationship；
    - 学科教师、班主任的具体业务范围将在 TeachingAssignment / HomeroomAssignment 中表达。

    这样避免同一事实分别存在于多个表里，降低权限数据漂移风险。
    """

    class Role(models.TextChoices):
        TEACHER = "TEACHER", "教师"
        ACADEMIC_ADMIN = "ACADEMIC_ADMIN", "学术管理员"
        SYSTEM_ADMIN = "SYSTEM_ADMIN", "学校系统管理员"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        "accounts.UserAccount",
        on_delete=models.PROTECT,
        related_name="school_role_assignments",
        verbose_name="用户账号",
    )
    role = models.CharField("角色", max_length=32, choices=Role.choices)
    is_active = models.BooleanField("有效", default=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "学校角色授权"
        verbose_name_plural = "学校角色授权"
        constraints = [
            models.UniqueConstraint(
                fields=["school", "user", "role"],
                name="uniq_role_assignment_per_school_user_role",
            )
        ]

    def __str__(self) -> str:
        return f"{self.school.code} / {self.user} / {self.get_role_display()}"
