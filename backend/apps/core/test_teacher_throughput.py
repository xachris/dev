from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.academics.models import TeachingAssignment
from apps.reports.models import SubjectComment

from .demo_roster import DEMO_ROSTER_SIZE, ensure_demo_roster


@override_settings(DEMO_MODE=True, DEMO_PASSWORD="DemoOnly-2026!")
class TeacherThroughputTests(TestCase):
    def setUp(self):
        self.data = ensure_demo_roster()
        self.cycle = self.data["cycle"]
        self.cs_assignment = TeachingAssignment.objects.get(
            teacher_role__user__username="teacher.cs",
            subject__code="CS",
        )
        self.math_assignment = TeachingAssignment.objects.get(
            teacher_role__user__username="teacher.math",
            subject__code="MATH",
        )
        self.assertTrue(self.client.login(username="teacher.cs", password="DemoOnly-2026!"))

    def batch_url(self, assignment=None):
        assignment = assignment or self.cs_assignment
        return reverse(
            "core:teacher_batch",
            kwargs={"assignment_id": assignment.pk, "cycle_id": self.cycle.pk},
        )

    def import_url(self, assignment=None):
        assignment = assignment or self.cs_assignment
        return reverse(
            "core:teacher_batch_import",
            kwargs={"assignment_id": assignment.pk, "cycle_id": self.cycle.pk},
        )

    def test_batch_page_contains_full_demo_roster(self):
        response = self.client.get(self.batch_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "连续处理整个教学组")
        self.assertContains(response, "A001")
        self.assertContains(response, f"A{DEMO_ROSTER_SIZE:03d}")
        self.assertEqual(len(response.context["items"]), DEMO_ROSTER_SIZE)

    def test_teacher_cannot_open_other_teachers_assignment(self):
        response = self.client.get(self.batch_url(self.math_assignment))
        self.assertEqual(response.status_code, 404)

    def test_ajax_submit_updates_only_scoped_comment(self):
        comment = SubjectComment.objects.get(
            report__report_cycle=self.cycle,
            report__student_membership__student_number="A002",
            subject__code="CS",
        )
        response = self.client.post(
            self.batch_url(),
            {
                "comment_id": str(comment.pk),
                "student_feedback": "A002 can explain iteration clearly.",
                "guardian_message": "Good progress.",
                "staff_note": "Check debugging next week.",
                "action": "submit",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["status"], SubjectComment.Status.SUBMITTED)
        comment.refresh_from_db()
        self.assertEqual(comment.student_feedback, "A002 can explain iteration clearly.")
        self.assertEqual(comment.status, SubjectComment.Status.SUBMITTED)

    def test_submitted_comment_cannot_be_overwritten_from_batch_endpoint(self):
        comment = SubjectComment.objects.get(
            report__report_cycle=self.cycle,
            report__student_membership__student_number="A003",
            subject__code="CS",
        )
        first = self.client.post(
            self.batch_url(),
            {
                "comment_id": str(comment.pk),
                "student_feedback": "Original",
                "action": "submit",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(first.status_code, 200)
        second = self.client.post(
            self.batch_url(),
            {
                "comment_id": str(comment.pk),
                "student_feedback": "Overwritten",
                "action": "save",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(second.status_code, 403)
        comment.refresh_from_db()
        self.assertEqual(comment.student_feedback, "Original")

    def test_csv_preview_then_confirm_imports_atomically(self):
        content = (
            "学号,姓名,学生反馈,家长信息,内部备注,动作\n"
            "A004,演示学生 04,Feedback 4,Guardian 4,Staff 4,DRAFT\n"
            "A005,演示学生 05,Feedback 5,Guardian 5,Staff 5,SUBMIT\n"
        ).encode("utf-8-sig")
        upload = SimpleUploadedFile("comments.csv", content, content_type="text/csv")
        preview = self.client.post(
            self.import_url(),
            {"action": "preview", "file": upload},
        )
        self.assertEqual(preview.status_code, 200)
        self.assertFalse(preview.context["has_errors"])
        self.assertEqual(len(preview.context["preview"]), 2)

        confirm = self.client.post(self.import_url(), {"action": "confirm"})
        self.assertEqual(confirm.status_code, 302)

        draft = SubjectComment.objects.get(
            report__report_cycle=self.cycle,
            report__student_membership__student_number="A004",
            subject__code="CS",
        )
        submitted = SubjectComment.objects.get(
            report__report_cycle=self.cycle,
            report__student_membership__student_number="A005",
            subject__code="CS",
        )
        self.assertEqual(draft.student_feedback, "Feedback 4")
        self.assertEqual(draft.status, SubjectComment.Status.DRAFT)
        self.assertEqual(submitted.student_feedback, "Feedback 5")
        self.assertEqual(submitted.status, SubjectComment.Status.SUBMITTED)

    def test_import_name_mismatch_is_preview_error_and_writes_nothing(self):
        content = (
            "学号,姓名,学生反馈,动作\n"
            "A006,另一个学生,Should not save,DRAFT\n"
        ).encode("utf-8-sig")
        upload = SimpleUploadedFile("comments.csv", content, content_type="text/csv")
        preview = self.client.post(
            self.import_url(),
            {"action": "preview", "file": upload},
        )
        self.assertEqual(preview.status_code, 200)
        self.assertTrue(preview.context["has_errors"])
        self.assertIn("姓名不匹配", preview.context["preview"][0]["errors"][0])

        comment = SubjectComment.objects.get(
            report__report_cycle=self.cycle,
            report__student_membership__student_number="A006",
            subject__code="CS",
        )
        self.assertEqual(comment.student_feedback, "")

    def test_excel_template_is_prefilled_with_stable_student_numbers(self):
        url = reverse(
            "core:teacher_batch_template",
            kwargs={
                "assignment_id": self.cs_assignment.pk,
                "cycle_id": self.cycle.pk,
                "file_format": "xlsx",
            },
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertGreater(len(response.content), 1000)

    def test_demo_reset_clears_the_whole_throughput_roster(self):
        comment = SubjectComment.objects.get(
            report__report_cycle=self.cycle,
            report__student_membership__student_number="A018",
            subject__code="CS",
        )
        response = self.client.post(
            self.batch_url(),
            {
                "comment_id": str(comment.pk),
                "student_feedback": "Temporary demo feedback",
                "action": "submit",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        comment.refresh_from_db()
        self.assertEqual(comment.status, SubjectComment.Status.SUBMITTED)

        self.client.logout()
        self.assertTrue(self.client.login(username="academic.admin", password="DemoOnly-2026!"))
        reset = self.client.post(reverse("core:demo_reset"))
        self.assertEqual(reset.status_code, 302)

        comment.refresh_from_db()
        self.assertEqual(comment.status, SubjectComment.Status.DRAFT)
        self.assertEqual(comment.student_feedback, "")
