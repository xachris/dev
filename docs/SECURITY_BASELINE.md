# Security Baseline

## Scope

This document defines the minimum engineering baseline for prototype development so that later production hardening does not require redesigning the entire platform.

## Principles

1. Least privilege.
2. Deny by default.
3. Server-side authorization.
4. Audit important actions.
5. Separate environments.
6. Never store plaintext passwords.
7. Never commit secrets to Git.
8. Use synthetic data during development.
9. Separate technical administration from educational-content access where possible.
10. Design for backup and recovery from the beginning.

## Authentication

- Passwords must use Django's secure password hashing framework.
- Session cookies must be secure in production.
- Login rate limiting should be added before production.
- Guardian and student actors should be distinguishable even when attached to the same student ID.
- Privileged administrator accounts should support stronger authentication before production.

## Authorization

Every request that reads or changes student information must validate both:

1. the actor's role; and
2. the actor's relationship/scope for the target student.

Front-end hiding is not sufficient authorization.

## Data handling

- Real student data is prohibited in development fixtures.
- Sensitive production fields should be minimised.
- Bulk exports should be permission-controlled and audited.
- Staff-only content must not leak into student/guardian serializers or templates.
- AI adapters must receive only the minimum data required for their task.

## Secrets

Secrets belong in environment variables or a managed secret store, never source control.

Examples:
- Django secret key
- database password
- mail credentials/tokens
- AI credentials

`.env` is ignored by Git. `.env.example` contains placeholders only.

## Transport

Production must use HTTPS. Plain HTTP is acceptable only in isolated local development.

## Database

- Application database credentials must not be shared with ordinary users.
- Production database should not be exposed directly to the public internet.
- Direct database access is an exceptional maintenance activity, not a normal business workflow.

## Audit events

At minimum, log:

- authentication events of interest
- report submit/return/approve/publish actions
- privileged account changes
- guardian/student relationship changes
- permission changes
- exports of sensitive information
- administrative overrides

## Backup

Production target:

- automated database backups
- encrypted off-host copy
- encrypted school-controlled local copy
- retention policy
- periodic restoration tests

A backup that has never been restored is not yet proven usable.

## Environment separation

Development, staging, and production should use distinct credentials and databases.

No production secret may be copied into source code or test fixtures.

## Compliance preparation

Before the platform handles real student data, the school should conduct formal security and privacy review appropriate to the jurisdiction, including classification/filing or assessment obligations where applicable. Prototype development should not be mistaken for production compliance approval.
