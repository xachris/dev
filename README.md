# School Digital Platform

A self-hosted school digital platform designed for student-centred workflows, secure family access, structured learning reports, and future AI-assisted school operations.

## Current product scope

The first implementation is **Learning Report System V0.1**.

Core workflow:

1. Subject teacher enters feedback.
2. Teacher submits the report.
3. Automated checks run.
4. Homeroom teacher reviews.
5. Report is approved.
6. School publishes the report.
7. Student and guardian views are generated according to permissions.
8. External email is used only as a notification channel.

## Core product principles

- **One Student, One Permanent ID, Multiple Roles, Different Views.**
- **Report stays inside the school. Notification goes outside.**
- School-controlled data and infrastructure are preferred over vendor lock-in.
- Student, guardian, teacher, and administrator permissions are separated.
- AI is optional and must never be required for the core workflow to function.
- Production data must remain auditable, access-controlled, backed up, and recoverable.

## Planned roles

- Student
- Guardian
- Subject Teacher
- Homeroom Teacher
- Academic Admin
- System Admin

## Milestone 1

Run the complete workflow with test data only:

`Teacher -> Submit -> Homeroom Review -> Approve -> Publish -> Guardian View / Student View`

No real student data, Outlook integration, or production deployment is required for Milestone 1.

## Repository structure

- `docs/` - architecture, product, permissions, security, and roadmap documentation
- `backend/` - Django application code
- `tests/` - automated and workflow tests
- `deployment/` - server, reverse proxy, backup, and deployment configuration
- `archive/` - material that existed before this project was initialized

## Status

Project initialized for prototype development.
