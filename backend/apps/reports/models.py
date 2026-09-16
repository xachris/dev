import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.academics.models import Subject
from apps.schools.models import AcademicYear
from apps.students.models import StudentSchoolMembership


class ReportCycleQuerySet(models.QuerySet):
    def for_school(self, school):
        return self.filter(academic_year__school=school)


class ReportCycle(models.Model):
    """一个学年中的报告批次。

    第一版只保存“这个报告属于哪个学年、叫什么名字”两个真正被工作流消费的事实。
    截止日期、展示主题、颜色等字段在出现真实消费者之前不预留。
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name="report_cycles",
        verbose_name="学年",
    )
    name = models.CharField("报告周期名称", max_length=100)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    objects = ReportCycleQuerySet.as_manager()

    class Meta:
        verbose_name = "报告周期"
        verbose_name_plural = "报告周期"
        ordering = ["academic_year__starts_on", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["academic_year", "name"],
                name="uniq_report_cycle_name_per_year",
            )
        ]

    @property
    def school(self):
        return self.academic_year.school

    def save(self, *args, **kwargs):
        self.name = self.name.strip()
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.academic_year.school.code} / {self.academic_year.name} / {self.name}"


class StudentReportQuerySet(models.QuerySet):
    def for_school(self, school):
        return self.filter(report_cycle__academic_year__school=school)


class StudentReport(models.Model):
    """一名学生在一个报告周期中的工作流容器。

    不复制各学科评价，也不在第一版强迫班主任额外撰写“总体总结”。
    """

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "填写中"
        IN_REVIEW = "IN_REVIEW", "待班主任审核"
        RETURNED = "RETURNED", "已退回修改"
        APPROVED = "APPROVED", "已批准"
        PUBLISHED = "PUBLISHED", "已发布"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_cycle = models.ForeignKey(
        ReportCycle,
        on_delete=models.PROTECT,
        related_name="student_reports",
        verbose_name="报告周期",
    )
    student_membership = models.ForeignKey(
        StudentSchoolMembership,
        on_delete=models.PROTECT,
        related_name="reports",
        verbose_name="学生学校关系",
    )
    status = models.CharField(
        "状态",
        max_length=16,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="published_student_reports",
        null=True,
        blank=True,
        verbose_name="发布人",
    )
    published_at = models.DateTimeField("发布时间", null=True, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    objects = StudentReportQuerySet.as_manager()

    class Meta:
        verbose_name = "学生报告"
        verbose_name_plural = "学生报告"
        constraints = [
            models.UniqueConstraint(
                fields=["report_cycle", "student_membership"],
                name="uniq_student_report_per_cycle",
            )
        ]

    @property
    def school(self):
        return self.report_cycle.school

    def clean(self):
        errors = {}
        if self.student_membership_id and self.report_cycle_id:
            if self.student_membership.school_id != self.report_cycle.academic_year.school_id:
                errors["student_membership"] = "学生学校关系与报告周期必须属于同一所学校。"

        if self.status == self.Status.PUBLISHED:
            if not self.published_at:
                errors["published_at"] = "已发布报告必须记录发布时间。"
            if not self.published_by_id:
                errors["published_by"] = "已发布报告必须记录发布人。"
        elif self.published_at or self.published_by_id:
            errors["status"] = "只有已发布报告可以保存发布人和发布时间。"

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.report_cycle} / {self.student_membership.student_number}"


class SubjectCommentQuerySet(models.QuerySet):
    def for_school(self, school):
        return self.filter(report__report_cycle__academic_year__school=school)


class SubjectComment(models.Model):
    """一个报告中某一学科的唯一工作槽与评价事实。

    StudentReport 创建时由系统根据当时的真实教学结构自动生成学科槽，冻结本次正式报告的
    学科构成。`created_by` 在第一位教师真正开始填写时才写入，因此系统生成空槽不冒充人工作者。
    """

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "草稿"
        SUBMITTED = "SUBMITTED", "已提交"
        RETURNED = "RETURNED", "已退回"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(
        StudentReport,
        on_delete=models.PROTECT,
        related_name="subject_comments",
        verbose_name="学生报告",
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.PROTECT,
        related_name="report_comments",
        verbose_name="学科",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_subject_comments",
        null=True,
        blank=True,
        verbose_name="首位填写人",
    )
    student_feedback = models.TextField("学生可见反馈", blank=True)
    guardian_message = models.TextField("家长专属信息", blank=True)
    staff_note = models.TextField("教职工内部备注", blank=True)
    status = models.CharField(
        "状态",
        max_length=16,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="submitted_subject_comments",
        null=True,
        blank=True,
        verbose_name="最近提交人",
    )
    submitted_at = models.DateTimeField("最近提交时间", null=True, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    objects = SubjectCommentQuerySet.as_manager()

    class Meta:
        verbose_name = "学科评价"
        verbose_name_plural = "学科评价"
        ordering = ["subject__code"]
        constraints = [
            models.UniqueConstraint(
                fields=["report", "subject"],
                name="uniq_subject_comment_per_report",
            )
        ]

    def clean(self):
        errors = {}
        if self.report_id and self.subject_id:
            if self.subject.school_id != self.report.report_cycle.academic_year.school_id:
                errors["subject"] = "学科与学生报告必须属于同一所学校。"

        if self.status in {self.Status.SUBMITTED, self.Status.RETURNED}:
            if not self.created_by_id:
                errors["created_by"] = "已进入人工填写流程的评价必须记录首位填写人。"
            if not self.submitted_by_id or not self.submitted_at:
                errors["status"] = "已提交或已退回的评价必须保留最近提交人和提交时间。"
        elif self.submitted_by_id or self.submitted_at:
            errors["status"] = "草稿不能提前保存提交人或提交时间。"

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.report} / {self.subject.code}"


class ReportActionQuerySet(models.QuerySet):
    def for_school(self, school):
        return self.filter(report__report_cycle__academic_year__school=school)


class ReportAction(models.Model):
    """需要人工判断的报告工作流动作。

    自动从“所有必需学科均已提交”推导出的 IN_REVIEW 不重复记录为人工动作。
    """

    class Action(models.TextChoices):
        RETURN_SUBJECT = "RETURN_SUBJECT", "退回学科评价"
        APPROVE = "APPROVE", "批准报告"
        PUBLISH = "PUBLISH", "发布报告"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(
        StudentReport,
        on_delete=models.PROTECT,
        related_name="actions",
        verbose_name="学生报告",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="report_actions",
        verbose_name="操作人",
    )
    action = models.CharField("动作", max_length=24, choices=Action.choices)
    subject_comment = models.ForeignKey(
        SubjectComment,
        on_delete=models.PROTECT,
        related_name="review_actions",
        null=True,
        blank=True,
        verbose_name="目标学科评价",
    )
    note = models.TextField("说明", blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    objects = ReportActionQuerySet.as_manager()

    class Meta:
        verbose_name = "报告工作流动作"
        verbose_name_plural = "报告工作流动作"
        ordering = ["created_at"]

    def clean(self):
        errors = {}
        if self.subject_comment_id and self.report_id:
            if self.subject_comment.report_id != self.report_id:
                errors["subject_comment"] = "目标学科评价必须属于同一份报告。"

        if self.action == self.Action.RETURN_SUBJECT:
            if not self.subject_comment_id:
                errors["subject_comment"] = "退回操作必须指定学科评价。"
            if not self.note.strip():
                errors["note"] = "退回操作必须说明修改原因。"
        elif self.subject_comment_id:
            errors["subject_comment"] = "批准或发布报告时不应绑定单个学科评价。"

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.report} / {self.get_action_display()} / {self.actor}"
