# Data Model

## Design principle

The permanent student ID is the centre of the domain model. Accounts, guardians, reports, classes, and notifications reference structured records rather than free-text names or inferred relationships.

## Core entities

### Student
- `id`
- `student_id` (permanent, unique)
- `full_name`
- `status` (`ACTIVE`, `SUSPENDED`, `WITHDRAWN`, `ALUMNI`)
- `date_of_birth` (future production field; sensitive)
- `created_at`
- `updated_at`

### UserAccount
Represents an authenticated actor.

- `id`
- `username`
- `password_hash`
- `actor_type` (`STUDENT`, `GUARDIAN`, `STAFF`)
- `status`
- `last_login_at`

### GuardianRelationship
Links a guardian actor to one or more students.

- `id`
- `guardian_account_id`
- `student_id`
- `relationship_type`
- `is_active`

### TeacherProfile
- `id`
- `user_account_id`
- `staff_id`
- `display_name`
- `status`

### AcademicYear
- `id`
- `name`
- `starts_on`
- `ends_on`
- `is_active`

### ClassGroup
- `id`
- `academic_year_id`
- `name`
- `grade_level`

### Subject
- `id`
- `code`
- `name`

### TeachingAssignment
Links teachers to subjects/classes.

- `id`
- `teacher_id`
- `subject_id`
- `class_group_id`
- `starts_on`
- `ends_on`
- `is_active`

### HomeroomAssignment
- `id`
- `teacher_id`
- `class_group_id`
- `starts_on`
- `ends_on`
- `is_active`

### StudentClassMembership
- `id`
- `student_id`
- `class_group_id`
- `starts_on`
- `ends_on`
- `is_active`

### ReportCycle
- `id`
- `academic_year_id`
- `name`
- `starts_on`
- `ends_on`
- `submission_deadline`
- `publication_at`
- `status`

### SubjectComment
Subject-level teacher input.

- `id`
- `report_cycle_id`
- `student_id`
- `subject_id`
- `teacher_id`
- `student_feedback`
- `guardian_message`
- `staff_note`
- `status` (`DRAFT`, `SUBMITTED`, `RETURNED`, `ACCEPTED`)
- `submitted_at`
- `updated_at`

### StudentReport
Whole-student report for one cycle.

- `id`
- `report_cycle_id`
- `student_id`
- `overall_summary_student`
- `overall_summary_guardian`
- `status` (`DRAFT`, `CHECKED`, `APPROVED`, `READY_TO_PUBLISH`, `PUBLISHED`)
- `version`
- `approved_by`
- `approved_at`
- `published_at`

### ReviewAction
- `id`
- `student_report_id`
- `actor_id`
- `action` (`APPROVE`, `RETURN`, `ESCALATE`)
- `comment`
- `created_at`

### Notification
Outbox record, not the report itself.

- `id`
- `student_report_id`
- `recipient_actor_id`
- `channel` (`EMAIL`, future channels)
- `destination`
- `status` (`PENDING`, `SENT`, `FAILED`)
- `attempt_count`
- `sent_at`
- `last_error`

A uniqueness rule should prevent duplicate notification creation for the same report, recipient, and channel.

### AuditEvent
- `id`
- `actor_id`
- `event_type`
- `target_type`
- `target_id`
- `metadata`
- `created_at`

## Important rules

1. Names are display values, not relationship keys.
2. Email addresses are notification destinations, not student identity.
3. AI output must never create or overwrite guardian/student relationships.
4. Publication is a state transition, not an email-send action.
5. Report content should be versionable.
6. Real production fields containing personal information require explicit retention, access, and audit policies.
