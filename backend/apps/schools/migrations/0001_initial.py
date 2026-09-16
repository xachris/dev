import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="School",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "code",
                    models.SlugField(
                        help_text="平台内稳定且唯一的学校代码，不使用学校名称作为关系主键。",
                        max_length=64,
                        unique=True,
                        verbose_name="学校代码",
                    ),
                ),
                ("name", models.CharField(max_length=200, verbose_name="学校名称")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("ACTIVE", "启用"),
                            ("SUSPENDED", "暂停"),
                            ("ARCHIVED", "已归档"),
                        ],
                        default="ACTIVE",
                        max_length=16,
                        verbose_name="状态",
                    ),
                ),
                (
                    "language_code",
                    models.CharField(default="zh-hans", max_length=20, verbose_name="默认语言"),
                ),
                (
                    "timezone",
                    models.CharField(default="Asia/Shanghai", max_length=64, verbose_name="默认时区"),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
            ],
            options={
                "verbose_name": "学校",
                "verbose_name_plural": "学校",
                "ordering": ["name", "code"],
            },
        ),
        migrations.CreateModel(
            name="AcademicYear",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("name", models.CharField(max_length=64, verbose_name="学年名称")),
                ("starts_on", models.DateField(verbose_name="开始日期")),
                ("ends_on", models.DateField(verbose_name="结束日期")),
                ("is_active", models.BooleanField(default=True, verbose_name="可用")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
                (
                    "school",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="%(app_label)s_%(class)s_records",
                        to="schools.school",
                    ),
                ),
            ],
            options={
                "verbose_name": "学年",
                "verbose_name_plural": "学年",
                "ordering": ["-starts_on", "name"],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("school", "name"),
                        name="uniq_academic_year_name_per_school",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("ends_on__gt", models.F("starts_on"))),
                        name="academic_year_end_after_start",
                    ),
                ],
            },
        ),
    ]
