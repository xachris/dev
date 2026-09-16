# Roadmap

## V0.1 Goal

Prove the core school learning-report workflow with synthetic data only.

## Milestone 1 - Core workflow

- Project skeleton
- Synthetic users and students
- Student permanent ID
- Student / guardian / teacher / homeroom / admin roles
- Teacher creates subject feedback
- Draft and submit states
- Homeroom review
- Approve / return for revision
- Publish
- Guardian view
- Student view with restricted content

Acceptance criterion:

`Teacher -> Submit -> Homeroom Review -> Approve -> Publish -> Guardian View / Student View`

must work end-to-end with test data.

## Milestone 2 - Audit and permission hardening

- Server-side role and relationship checks
- Audit events
- Login tracking
- Report version history
- Privileged-action logging
- Permission tests

## Milestone 3 - Notification service

- Notification outbox
- Console/test email adapter
- Outlook/SMTP adapter
- Retry handling
- Delivery state
- Duplicate-send prevention

## Milestone 4 - Staging deployment

- Linux server
- PostgreSQL
- Nginx
- HTTPS
- Environment configuration
- Backup automation
- Restore procedure
- Basic monitoring

## Milestone 5 - AI assistance

- AI provider interface
- `none` provider
- local model provider
- optional external provider
- teacher comment polishing
- report consistency checks
- strict rule: AI must not infer recipients or invent educational facts

## Milestone 6 - Security baseline

- Security review
- Least-privilege review
- Data-retention policy hooks
- Backup encryption
- Admin access controls
- Incident-response documentation
- Preparation for formal compliance assessment before real-student production use

## Milestone 7 - Production pilot

- Limited real-world pilot after school approval
- Production operating procedures
- User training
- Support model
- Rollback plan
- Review before broader deployment

## Explicitly out of scope for V0.1

- Timetabling
- Finance
- Admissions
- Library management
- Dormitory management
- Full LMS replacement
- Full SIS replacement
- Real student data
- Production AI
