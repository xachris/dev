import uuid

from django.db import models
from django.db.models import F, Q

from apps.core.models import SchoolScopedModel


class School(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "启用"
        SUSPENDED = "SUSPENDED", "暂停"
        ARCHIVED = "ARCHIVED", "已归档"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.SlugField(
        "学校代码",
        max_length=64,
        unique=True,
        help_text="平台内稳定且唯一的学校代码，不使用学校名称作为关系主键。",
    )
    name = models.CharField("学校名称", max_length=200)
    status = models.CharField(
        "状态",
        max_length=16,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    language_code = models.CharField("默认语言", max_length=20, default="zh-hans")
    timezone = models.CharField("默认时区", max_length=64, default="Asia/Shanghai")
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "学校"
        verbose_name_plural = "学校"
        ordering = ["name", "code"]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class AcademicYear(SchoolScopedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField("学年名称", max_length=64)
    starts_on = models.DateField("开始日期")
    ends_on = models.DateField("结束日期")
    is_active = models.BooleanField("可用", default=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "学年"
        verbose_name_plural = "学年"
        ordering = ["-starts_on", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "name"],
                name="uniq_academic_year_name_per_school",
            ),
            models.CheckConstraint(
                condition=Q(ends_on__gt=F("starts_on")),
                name="academic_year_end_after_start",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.school.code} / {self.name}"
