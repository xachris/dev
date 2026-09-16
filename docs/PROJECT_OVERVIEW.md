# Project Overview

## Project name

School Digital Platform

## Initial product

Learning Report System V0.1

## Problem statement

Schools often distribute learning reports through fragmented teacher-to-parent email workflows. This creates duplication, inconsistent formatting, weak auditability, privacy risk, recipient mistakes, and unnecessary staff workload.

The platform replaces distributed email reporting with a school-controlled publication workflow. Reports remain inside the school system. External email is used only to notify guardians that a report is available.

## Core principles

1. One Student, One Permanent ID, Multiple Roles, Different Views.
2. Report stays inside the school. Notification goes outside.
3. Teachers provide educational facts and judgements; AI may assist expression but must not invent facts.
4. Recipient identity and permissions come from structured school data, never from AI inference.
5. Student and guardian views may differ.
6. Staff-only notes must remain inaccessible to students and guardians unless explicitly published.
7. The platform must function without AI.
8. The architecture should minimize vendor lock-in.
9. Production changes must be auditable.
10. Development and testing must use synthetic data until production readiness is established.

## Initial roles

### Student
Can access student-visible notices, assignments, reports, assessment information, and other authorised resources.

### Guardian
Can access guardian-visible information associated with the student, including parent-only learning comments where permitted.

### Subject Teacher
Can create and submit subject-level feedback for assigned students.

### Homeroom Teacher
Can review the whole-student report, detect missing or inconsistent content, return content for revision, and approve reports.

### Academic Admin
Can manage report cycles, inspect exceptions, oversee publication readiness, and escalate cases.

### System Admin
Can manage platform operation, accounts, infrastructure, and technical configuration. System administration does not imply unrestricted educational-content access.

## Initial workflow

1. Report cycle is created.
2. Subject teachers enter structured feedback.
3. Teachers save drafts and submit.
4. Automated validation runs.
5. Homeroom teacher reviews the complete student report.
6. Missing or problematic items are returned for correction.
7. Approved reports become ready for publication.
8. School publishes reports.
9. Guardian and student views are rendered according to visibility rules.
10. Notification service sends external alerts only.
11. Views, approvals, publication, and administrative actions are logged.

## Milestone 1

Use synthetic data only and complete the following path:

Teacher -> Submit -> Homeroom Review -> Approve -> Publish -> Guardian View / Student View

Milestone 1 deliberately excludes production email, real students, external AI, and production deployment.

## Long-term direction

Future modules may include notices, homework, attendance, assessment, parent meetings, longitudinal learning analysis, and AI-assisted summaries. These should reuse the same identity, permission, audit, and student-data foundations rather than creating separate silos.
