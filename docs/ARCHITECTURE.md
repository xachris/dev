# Architecture

## Goal

Build a self-hosted, school-controlled platform that can run on a school-managed or cloud Linux server while keeping core data, permissions, workflows, and audit history independent from large third-party platforms.

## Initial stack

- Python
- Django
- PostgreSQL
- Django templates + minimal JavaScript for V0.1
- Nginx in front of the application
- Linux server deployment
- Optional local AI adapter
- Pluggable email notification adapter

## Logical architecture

```text
Browser
  |
  v
Nginx / HTTPS
  |
  v
Django Application
  |-- Accounts & Roles
  |-- Students
  |-- Academics
  |-- Reports
  |-- Notifications
  |-- Audit
  |
  +--> PostgreSQL
  |
  +--> Mail Adapter --> Outlook / SMTP
  |
  +--> AI Adapter --> none / local / external
```

## Deployment environments

### Development
Developer machine or controlled development environment. Synthetic data only.

### Staging
Server environment that mirrors production architecture. Synthetic or explicitly sanitised data only unless authorised otherwise.

### Production
School-operated service containing real school data. Production must have security hardening, backups, monitoring, and controlled administrative access.

## Core architectural rules

### 1. Student ID is the stable domain identifier
A student record is centred on a permanent student ID. Email addresses, login methods, and vendors may change without changing the student identity.

### 2. Identity and role are separate concepts
A student record can be accessed through different authorised actors. Student, guardian, teacher, and administrator access must be distinguished in the application layer.

### 3. Visibility is data-driven
Content is stored once and rendered according to visibility policy. Student-visible, guardian-visible, and staff-only content are not duplicated into separate independent systems.

### 4. AI is an adapter, not a dependency
Core workflows must remain operational with `AI_PROVIDER=none`.

### 5. Email is an adapter, not the system of record
Learning reports remain in the school database. Email is used to send notifications and authentication messages when required.

### 6. Auditability is mandatory
Important changes must record actor, action, target, timestamp, and relevant before/after information where appropriate.

### 7. Least privilege
Technical administration, academic administration, and educational-content access should not automatically imply one another.

## Initial application modules

### accounts
Authentication, credentials, role memberships, login state, access policy helpers.

### students
Student identity, guardian relationships, enrolment state, class membership.

### academics
Subjects, teaching assignments, homeroom relationships, academic years, report cycles.

### reports
Teacher comments, report assembly, workflow state, visibility, review, approval, publication.

### notifications
Notification outbox, delivery state, retry metadata, mail adapter.

### audit
Security-relevant and business-relevant audit events.

## Background processing

V0.1 can operate synchronously where safe, but notification delivery should evolve toward an outbox/worker model before production. Publication must not depend on successfully sending every email in the same HTTP request.

## Backup model

Production target:

```text
Production PostgreSQL
   |-- automated cloud/server backup
   |-- encrypted off-host backup
   `-- encrypted school-controlled local backup
```

Backup success alone is insufficient; restore procedures must be tested periodically.
