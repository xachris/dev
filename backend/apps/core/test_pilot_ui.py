from django.test import TestCase, override_settings
from django.urls import reverse

from apps.accounts.models import UserAccount
from apps.reports.models import StudentReport, SubjectComment

from .demo_data import ensure_demo_data


@override_settings(DEMO_MODE=True, DEMO_PASSWORD="PilotPass-2026!")
class PilotUiTests(TestCase):
    def setUp(self):
        data = ensure_demo_data()
        self.report = data["report"]
        self.password = "PilotPass-2026!"
        self.cs_comment = self.report.subject_comments.get(subject__code="CS")
        self.math_comment = self.report.subject_comments.get(subject__code="MATH")

    def login(self, username):
        self.client.logout()
        ok = self.client.login(username=username, password=self.password)
        self.assertTrue(ok, username)

    def submit_comment(self, username, comment, prefix):
        self.login(username)
        response = self.client.post(
            reverse("core:teacher_comment", args=[comment.id]),
            {
                "student_feedback": f"{prefix} student feedback",
                "guardian_message": f"{prefix} guardian message",
                "staff_note": f"{prefix} staff note",
                "action": "submit",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        comment.refresh_from_db()
        self.assertEqual(comment.status, SubjectComment.Status.SUBMITTED)

    def test_home_lists_demo_accounts(self):
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, "teacher.cs")
        self.assertContains(response, "guardian.a001")
        self.assertContains(response, self.password)

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("core:dashboard"))
        self.assertRedirects(
            response,
            f"{reverse('core:login')}?next={reverse('core:dashboard')}",
        )

    def test_teacher_sees_only_real_subject_scope(self):
        self.login("teacher.cs")
        response = self.client.get(reverse("core:dashboard"))
        self.assertContains(response, "Computer Science")
        self.assertNotContains(response, "Mathematics")

        wrong = self.client.get(reverse("core:teacher_comment", args=[self.math_comment.id]))
        self.assertEqual(wrong.status_code, 403)

    def test_homeroom_cannot_read_teacher_draft_content(self):
        self.login("teacher.cs")
        saved = self.client.post(
            reverse("core:teacher_comment", args=[self.cs_comment.id]),
            {
                "student_feedback": "PRIVATE DRAFT STUDENT TEXT",
                "guardian_message": "PRIVATE DRAFT GUARDIAN TEXT",
                "staff_note": "PRIVATE DRAFT STAFF TEXT",
                "action": "save",
            },
            follow=True,
        )
        self.assertEqual(saved.status_code, 200)
        self.cs_comment.refresh_from_db()
        self.assertEqual(self.cs_comment.status, SubjectComment.Status.DRAFT)

        self.login("homeroom.g8a")
        review = self.client.get(reverse("core:homeroom_report", args=[self.report.id]))
        self.assertEqual(review.status_code, 200)
        self.assertNotContains(review, "PRIVATE DRAFT STUDENT TEXT")
        self.assertNotContains(review, "PRIVATE DRAFT GUARDIAN TEXT")
        self.assertNotContains(review, "PRIVATE DRAFT STAFF TEXT")
        self.assertContains(review, "草稿内容不会提前显示")

    def test_system_admin_does_not_receive_education_content(self):
        self.login("system.admin")
        response = self.client.get(reverse("core:dashboard"))
        self.assertContains(response, "当前没有可显示的教育内容")
        self.assertNotContains(response, "学生 A")

    def test_full_browser_workflow_and_role_filtered_report(self):
        self.submit_comment("teacher.cs", self.cs_comment, "CS")
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, StudentReport.Status.DRAFT)

        self.submit_comment("teacher.math", self.math_comment, "MATH")
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, StudentReport.Status.IN_REVIEW)

        self.login("homeroom.g8a")
        review = self.client.get(reverse("core:homeroom_report", args=[self.report.id]))
        self.assertContains(review, "CS student feedback")
        self.assertContains(review, "MATH staff note")

        approve = self.client.post(
            reverse("core:homeroom_report", args=[self.report.id]),
            {"action": "approve"},
            follow=True,
        )
        self.assertEqual(approve.status_code, 200)
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, StudentReport.Status.APPROVED)

        self.login("academic.admin")
        admin_dashboard = self.client.get(reverse("core:dashboard"))
        self.assertContains(admin_dashboard, "发布")
        published = self.client.post(
            reverse("core:publish_report", args=[self.report.id]),
            follow=True,
        )
        self.assertEqual(published.status_code, 200)
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, StudentReport.Status.PUBLISHED)

        self.login("student.a001")
        student_view = self.client.get(reverse("core:report_view", args=[self.report.id]))
        self.assertEqual(student_view.status_code, 200)
        self.assertContains(student_view, "CS student feedback")
        self.assertNotContains(student_view, "CS guardian message")
        self.assertNotContains(student_view, "CS staff note")
        self.assertNotContains(student_view, "家长专属信息")
        self.assertNotContains(student_view, "教职工内部备注")

        self.login("guardian.a001")
        guardian_view = self.client.get(reverse("core:report_view", args=[self.report.id]))
        self.assertEqual(guardian_view.status_code, 200)
        self.assertContains(guardian_view, "CS student feedback")
        self.assertContains(guardian_view, "CS guardian message")
        self.assertContains(guardian_view, "家长专属信息")
        self.assertNotContains(guardian_view, "CS staff note")
        self.assertNotContains(guardian_view, "教职工内部备注")

    def test_return_one_subject_then_resubmit(self):
        self.submit_comment("teacher.cs", self.cs_comment, "CS")
        self.submit_comment("teacher.math", self.math_comment, "MATH")

        self.login("homeroom.g8a")
        response = self.client.post(
            reverse("core:homeroom_report", args=[self.report.id]),
            {
                "action": "return",
                "comment_id": str(self.cs_comment.id),
                "reason": "请补充更具体的学习证据。",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.report.refresh_from_db()
        self.cs_comment.refresh_from_db()
        self.math_comment.refresh_from_db()
        self.assertEqual(self.report.status, StudentReport.Status.RETURNED)
        self.assertEqual(self.cs_comment.status, SubjectComment.Status.RETURNED)
        self.assertEqual(self.math_comment.status, SubjectComment.Status.SUBMITTED)

        self.submit_comment("teacher.cs", self.cs_comment, "CS revised")
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, StudentReport.Status.IN_REVIEW)

    def test_demo_reset_is_restricted_to_academic_admin(self):
        self.login("teacher.cs")
        forbidden = self.client.post(reverse("core:demo_reset"))
        self.assertEqual(forbidden.status_code, 403)

        self.login("academic.admin")
        ok = self.client.post(reverse("core:demo_reset"), follow=True)
        self.assertEqual(ok.status_code, 200)
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, StudentReport.Status.DRAFT)
        self.assertFalse(self.report.subject_comments.exclude(status=SubjectComment.Status.DRAFT).exists())

    def test_unpublished_report_is_not_openable_by_student_or_guardian(self):
        for username in ("student.a001", "guardian.a001"):
            self.login(username)
            response = self.client.get(reverse("core:report_view", args=[self.report.id]))
            self.assertEqual(response.status_code, 403)

    def test_demo_seed_is_idempotent(self):
        ensure_demo_data()
        ensure_demo_data()
        self.assertEqual(UserAccount.objects.filter(username="student.a001").count(), 1)
        self.assertEqual(StudentReport.objects.count(), 1)
        self.assertEqual(SubjectComment.objects.filter(report=self.report).count(), 2)
