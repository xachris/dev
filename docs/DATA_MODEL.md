# 数据模型

## 设计原则

平台数据模型围绕稳定身份、真实业务关系和学校作用域设计，不以“传统 SIS 有哪些字段”为起点。

核心原则：

1. 姓名只是显示值，不作为关系主键。
2. 登录账号、学生业务身份、家长授权和工作人员角色彼此分离。
3. 同一个真实人应尽量只有一个 `UserAccount`，不同业务身份通过关系表达。
4. 学校内可见学号属于 `StudentSchoolMembership`；平台内部 `Student.id` 是稳定 UUID。
5. 不自动根据姓名、邮箱、生日或 AI 推断跨学校学生身份。
6. 没有明确业务消费者的字段不提前加入。
7. 数据库负责确定性的唯一性和关系约束，人类负责业务判断。

> 产品界面使用中文名称；代码层继续使用英文模型名和字段名。

---

# 已实现核心实体

## 学校 `School`

表示平台中的学校 / Tenant。

主要字段：

- `id`：UUID
- `code`：稳定唯一学校代码
- `name`
- `status`：`ACTIVE / SUSPENDED / ARCHIVED`
- `language_code`
- `timezone`

删除策略：已有业务关联数据时使用 `PROTECT`，优先归档，不直接级联删除历史。

## 学年 `AcademicYear`

属于某一所学校。

主要字段：

- `id`
- `school`
- `name`
- `starts_on`
- `ends_on`
- `is_active`

约束：

- 同一学校学年名称唯一；
- 结束日期必须晚于开始日期。

## 用户账号 `UserAccount`

表示一个可认证的真实操作身份。

基于 Django `AbstractUser`，当前额外定义：

- `id`：UUID
- `username`：全平台技术登录标识，当前唯一
- `display_name`：仅用于界面显示
- Django 标准密码、启用状态、登录时间、权限字段

重要规则：

- 账号不是“学生账号 / 家长账号 / 教师账号”三套独立体系；
- 同一个账号可以同时拥有多个业务身份，例如教师兼家长；
- 最终登录方式尚未冻结，未来可以扩展学校代码 + 学号、邮箱、SSO 等方式，而不改变业务实体主键。

## 学校角色授权 `RoleAssignment`

只记录需要显式授予的学校工作人员基础角色。

当前角色：

- `TEACHER`
- `ACADEMIC_ADMIN`
- `SYSTEM_ADMIN`

主要字段：

- `id`
- `school`
- `user`
- `role`
- `is_active`
- `created_at / updated_at`

数据库约束：同一学校、同一用户、同一角色只能存在一条授权记录。

不在这里重复保存：

- 学生身份；
- 家长身份；
- 学科教师具体任课范围；
- 班主任具体管理范围。

后两者由下一阶段的学术关系模型表达。

## 学生 `Student`

平台层面的稳定学生身份。

主要字段：

- `id`：稳定 UUID
- `user_account`：可为空；学生不必为了进入学校系统而先拥有登录账号
- `full_name`
- `created_at / updated_at`

当前不保存出生日期、性别、国籍等资料，因为首个报告闭环尚未消费这些字段。

## 学生学校关系 `StudentSchoolMembership`

表示一名学生在一所学校中的稳定成员身份。

主要字段：

- `id`
- `school`
- `student`
- `student_number`：学校内部稳定学号
- `status`：`ACTIVE / SUSPENDED / WITHDRAWN / ALUMNI`
- `created_at / updated_at`

数据库约束：

- 同一学生在同一学校只存在一条成员关系；
- 同一学校内 `student_number` 唯一；
- 不同学校可以使用相同格式或相同数值的学号。

设计目的：学生转学、教育集团多校区等场景不需要重新发明平台身份，同时学校日常业务继续使用自己的学生编号。

## 家长学生关系 `GuardianRelationship`

表示某一个用户账号被某所学校授权为某名学生的家长 / 监护人。

主要字段：

- `id`
- `student_membership`
- `guardian`：`UserAccount`
- `relationship_type`：`PARENT / LEGAL_GUARDIAN / OTHER_AUTHORISED`
- `is_active`
- `created_at / updated_at`

关键设计：关系绑定 `StudentSchoolMembership`，而不是只绑定全局 `Student`。

因此：

> 家长获准查看学生在 School A 中的资料，不代表自动获准查看同一 Student 在 School B 中的资料。

数据库约束：同一学生学校关系与同一家长账号只保留一条授权记录。

---

# 下一阶段计划实体

以下模型必须直接服务学习报告权限，不为“完整 SIS”而提前扩展。

## 班级 `ClassGroup`

预计至少表达：

- `school`
- `academic_year`
- `name`
- 必要的年级 / 展示信息

用途：定义学生当前学习组织和班主任管理范围。

## 学科 `Subject`

预计至少表达：

- `school`
- `code`
- `name`

用途：定义任课与学习报告的学科维度。

## 学生班级关系 `StudentClassMembership`

连接：

- `StudentSchoolMembership`
- `ClassGroup`

用途：回答“这名学生在当前学年属于哪个班”。

## 任课关系 `TeachingAssignment`

连接：

- 教师 `UserAccount`
- `Subject`
- `ClassGroup`

用途：决定教师能为哪些学生、哪门学科创建评价。

## 班主任关系 `HomeroomAssignment`

连接：

- 教师 `UserAccount`
- `ClassGroup`

用途：决定谁能审核某班学生完整报告。

---

# 后续报告实体

以下仍属于后续阶段设计，字段将在真正开发时根据业务闭环再次核验，不视为已经冻结。

## 报告周期 `ReportCycle`

用于定义某个学年中的评价与发布时间窗口。

## 学科评价 `SubjectComment`

预计至少区分：

- 学生可见反馈；
- 家长专属信息；
- 教职工内部备注；
- 工作流状态。

## 学生整体报告 `StudentReport`

用于组合一个报告周期内的学科评价、审核状态与最终发布状态。

## 审核动作 `ReviewAction`

记录退回、批准、升级等业务动作。

## 通知 `Notification`

通知是 Outbox 记录，不是正式报告本体。

正式报告留在学校系统内，外部渠道只负责通知。

## 审计事件 `AuditEvent`

用于记录权限变更、关系变更、报告发布和高权限操作等安全相关事实。

---

# 关键业务规则

1. **一个真实人尽量一个登录账号，多种业务身份通过关系表达。**
2. **一个 Student 使用稳定平台 UUID；学校使用自己的稳定 student_number。**
3. **跨校 Student 身份不得自动匹配或 AI 推断。**
4. **家长授权必须是学校范围内的明确关系。**
5. **教师角色不等于任课权限，具体学生访问范围必须由 TeachingAssignment / HomeroomAssignment 决定。**
6. 邮箱、姓名、显示名称都不是学生或家长关系主键。
7. AI 不得创建、修改或覆盖学生—家长关系、跨校身份关系或权限授权。
8. “发布报告”是一种业务状态变更，不等于“发送邮件”。
9. 正式环境个人信息字段必须有明确消费者、访问范围、留存和审计规则。
10. 请求级学校隔离和权限系统完成前，不接入真实学生数据。
