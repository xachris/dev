# 数据模型

## 设计原则

永久学号是整个业务模型的中心。账号、家长关系、班级、教师、报告和通知都通过结构化关系引用学生记录，不依赖自由文本姓名，也不允许通过 AI 推断关系。

> 产品界面使用中文名称；代码层继续使用英文模型名和字段名。

## 核心实体

### 学生 `Student`

- `id`
- `student_id`：永久学号，唯一
- `full_name`：姓名
- `status`：`ACTIVE` / `SUSPENDED` / `WITHDRAWN` / `ALUMNI`
- `date_of_birth`：出生日期，正式环境敏感字段
- `created_at`
- `updated_at`

### 用户账号 `UserAccount`

表示一个可认证的实际操作身份。

- `id`
- `username`
- `password_hash`
- `actor_type`：`STUDENT` / `GUARDIAN` / `STAFF`
- `status`
- `last_login_at`

### 家长关系 `GuardianRelationship`

将一个家长账号绑定到一个或多个学生。

- `id`
- `guardian_account_id`
- `student_id`
- `relationship_type`
- `is_active`

### 教师档案 `TeacherProfile`

- `id`
- `user_account_id`
- `staff_id`
- `display_name`
- `status`

### 学年 `AcademicYear`

- `id`
- `name`
- `starts_on`
- `ends_on`
- `is_active`

### 班级 `ClassGroup`

- `id`
- `academic_year_id`
- `name`
- `grade_level`

### 学科 `Subject`

- `id`
- `code`
- `name`

### 任课关系 `TeachingAssignment`

连接教师、学科和班级。

- `id`
- `teacher_id`
- `subject_id`
- `class_group_id`
- `starts_on`
- `ends_on`
- `is_active`

### 班主任关系 `HomeroomAssignment`

- `id`
- `teacher_id`
- `class_group_id`
- `starts_on`
- `ends_on`
- `is_active`

### 学生班级关系 `StudentClassMembership`

- `id`
- `student_id`
- `class_group_id`
- `starts_on`
- `ends_on`
- `is_active`

### 报告周期 `ReportCycle`

- `id`
- `academic_year_id`
- `name`
- `starts_on`
- `ends_on`
- `submission_deadline`
- `publication_at`
- `status`

### 学科评价 `SubjectComment`

表示一位学科教师对一名学生在某个报告周期内的结构化输入。

- `id`
- `report_cycle_id`
- `student_id`
- `subject_id`
- `teacher_id`
- `student_feedback`：学生可见学习反馈
- `guardian_message`：仅家长可见留言
- `staff_note`：教职工内部备注
- `status`：`DRAFT` / `SUBMITTED` / `RETURNED` / `ACCEPTED`
- `submitted_at`
- `updated_at`

### 学生整体报告 `StudentReport`

表示一名学生在一个报告周期中的完整报告。

- `id`
- `report_cycle_id`
- `student_id`
- `overall_summary_student`：学生可见总评
- `overall_summary_guardian`：家长可见总评
- `status`：`DRAFT` / `CHECKED` / `APPROVED` / `READY_TO_PUBLISH` / `PUBLISHED`
- `version`
- `approved_by`
- `approved_at`
- `published_at`

### 审核动作 `ReviewAction`

- `id`
- `student_report_id`
- `actor_id`
- `action`：`APPROVE` / `RETURN` / `ESCALATE`
- `comment`
- `created_at`

### 通知 `Notification`

通知只是 Outbox 记录，不是正式报告本体。

- `id`
- `student_report_id`
- `recipient_actor_id`
- `channel`：`EMAIL`，未来可增加其他渠道
- `destination`
- `status`：`PENDING` / `SENT` / `FAILED`
- `attempt_count`
- `sent_at`
- `last_error`

应建立唯一约束，防止同一报告、同一接收人、同一渠道重复生成通知。

### 审计事件 `AuditEvent`

- `id`
- `actor_id`
- `event_type`
- `target_type`
- `target_id`
- `metadata`
- `created_at`

## 关键业务规则

1. 姓名只是显示字段，不是关系主键。
2. 邮箱只是通知地址，不是学生身份。
3. AI 不得创建、修改或覆盖学生—家长关系。
4. “发布报告”是一种业务状态变更，不等于“发送邮件”。
5. 正式报告必须支持版本记录。
6. 正式环境中的个人信息字段必须配置明确的访问、留存和审计规则。
7. 家长与学生访问同一学生档案，但服务器必须根据实际登录角色控制字段可见性。
