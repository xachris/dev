# Permission Model

## Core rule

**One Student, One Permanent ID, Multiple Roles, Different Views.**

A student record is stable. Different authenticated actors may access different portions of that record according to role, relationship, assignment, and content visibility.

## Primary roles

- Student
- Guardian
- Subject Teacher
- Homeroom Teacher
- Academic Admin
- System Admin

## Visibility classes

### STUDENT_GUARDIAN
Visible to the student and authorised guardians, as well as authorised staff.

Examples:
- homework and assignment information
- general learning progress
- strengths
- student-facing next steps
- ordinary school notices

### GUARDIAN_ONLY
Visible to authorised guardians and authorised staff, but not the student.

Examples:
- teacher message to parent
- parent guidance
- selected behavioural concerns
- selected academic concerns not intended for student display

### STAFF_ONLY
Visible only to authorised staff with a legitimate role-based need.

Examples:
- internal review notes
- workflow comments
- escalation notes
- sensitive internal operational information

## Initial permission matrix

| Capability | Student | Guardian | Subject Teacher | Homeroom Teacher | Academic Admin | System Admin |
|---|---:|---:|---:|---:|---:|---:|
| View student-visible report | Own | Linked student | Assigned students | Homeroom students | Scoped | Technical support only when authorised |
| View guardian-only content | No | Linked student | Assigned content where required | Homeroom students | Scoped | Not by default |
| View staff-only report content | No | No | Assigned content | Homeroom students | Scoped | Not by default |
| Create subject feedback | No | No | Assigned students/subjects | If assigned | No | No |
| Submit subject feedback | No | No | Own drafts | If assigned | No | No |
| Review full student report | No | No | No | Homeroom students | Scoped | No |
| Approve report | No | No | No | Homeroom students | Escalation/override by policy | No |
| Publish report | No | No | No | No by default | Yes | Technical execution only |
| Manage technical accounts | No | No | No | No | Limited | Yes |
| Change academic relationships | No | No | No | No | Yes | No by default |

## Relationship checks

Role alone is insufficient. Access must also satisfy contextual relationships.

Examples:

- A guardian must be linked to the student.
- A subject teacher must have an active teaching assignment for the student/class and subject.
- A homeroom teacher must have an active homeroom assignment for the student/class.
- Academic administrator access should be scoped by school, division, year group, or assigned responsibility where possible.

## Guardian access model

A student may have multiple authorised guardians. Each guardian should have distinct credentials or an auditable actor identity even when they access the same student record.

Example:

```text
Student S000381
  |- Student access
  |- Guardian A access
  `- Guardian B access
```

The permanent student ID remains unchanged.

## Security principles

1. Deny by default.
2. Permission checks occur server-side.
3. Hiding a button is not an access-control mechanism.
4. Every privileged action should be auditable.
5. Administrative technical access does not automatically grant educational-content access.
6. Direct database access should not be part of normal school operations.
