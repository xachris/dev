from django.db import models


class SchoolScopedQuerySet(models.QuerySet):
    """需要学校作用域的业务模型共用查询入口。"""

    def for_school(self, school):
        return self.filter(school=school)


class SchoolScopedModel(models.Model):
    """多学校业务数据的抽象基类。

    它只解决最基础的问题：每条业务记录必须明确属于一所学校。
    更严格的“当前请求只能访问哪所学校”将在身份和权限阶段实现。
    """

    school = models.ForeignKey(
        "schools.School",
        on_delete=models.PROTECT,
        related_name="%(app_label)s_%(class)s_records",
    )

    objects = SchoolScopedQuerySet.as_manager()

    class Meta:
        abstract = True
