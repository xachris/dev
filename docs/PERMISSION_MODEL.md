# 权限模型

## 核心规则

**一个学生，一个稳定平台身份；在不同学校拥有各自稳定学号；多种身份，不同视图。**

权限不是一张独立的“万能授权表”，而应尽量由真实业务事实推导：学校关系、家长关系、任课关系、班主任关系和明确的管理角色共同决定用户能做什么。

平台内部 `Student.id` 使用稳定 UUID；学校日常使用 `StudentSchoolMembership.student_number`。UUID 的不可猜测性不是安全边界，也不能替代权限校验。

---

## 身份与角色来源

不同身份由最接近真实业务事实的数据产生：

- **学生身份**：`Student.user_account + StudentSchoolMembership`
- **家长 / 监护人身份**：有效 `GuardianRelationship`
- **教师基础身份**：学校范围内有效 `RoleAssignment(TEACHER)`
- **学科教师实际范围**：有效 `TeachingAssignment`
- **班主任实际范围**：有效 `HomeroomAssignment`
- **学术管理员**：有效 `RoleAssignment(ACADEMIC_ADMIN)`
- **学校系统管理员**：有效 `RoleAssignment(SYSTEM_ADMIN)`
- **Django superuser**：技术运维能力，不自动等于任何学校业务角色

同一个真实成年人可以同时承担多个身份，例如：

```text
同一个 UserAccount
├── School A / TEACHER
└── GuardianRelationship -> 自己孩子
```

不需要创建“教师账号”和“家长账号”两套凭证。

---

# Phase 5 已实现的集中 Policy 层

代码入口：`backend/apps/core/policies.py`

所有后续 View、API 和 Service 应复用集中 Policy，而不是各自复制权限判断。

## 学生业务空间范围

### `visible_student_memberships_for(user, school)`

返回该用户在指定学校中可以进入的在读学生业务空间。

当前来源：

- 学生本人；
- 有效家长关系；
- 当前有效学年的有效任课关系；
- 当前有效学年的有效班主任关系。

### `can_access_student_space(user, student_membership)`

判断用户是否可以进入某一名学生在该校的业务空间。

**重要：进入学生业务空间不等于可以读取学生的全部内容。**

例如一名学科教师需要进入学生上下文才能填写自己的学科评价，但这并不意味着可以读取其他教师的内部备注或全部家长专属信息。

因此禁止把 `can_access_student_space()` 当成未来所有内容对象的万能读取权限。

## 学科评价写入范围

### `writable_student_memberships_for_subject(user, school, subject)`

根据真实 `TeachingAssignment + StudentClassMembership` 自动计算教师可以为哪些学生填写指定学科评价。

### `can_write_subject_comment(user, student_membership, subject)`

单学生 / 单学科写入判断。

教师仅有 `TEACHER` 角色并不足够，必须存在实际有效任课关系。

## 班主任审核范围

### `reviewable_student_memberships_for(user, school)`

根据实际 `HomeroomAssignment + StudentClassMembership` 自动计算班主任可审核的学生范围。

### `can_review_student_report(user, student_membership)`

单学生完整报告审核判断。

普通学科教师不会因为能写某一学科评价就自动获得整份报告审核权限。

## 管理权限

### `can_manage_academic_structure(user, school)`

当前仅有效 `ACADEMIC_ADMIN` 角色可以维护学术组织结构。

### `can_manage_school_accounts(user, school)`

当前仅有效 `SYSTEM_ADMIN` 角色可以执行学校范围的业务账号管理。

**学校系统管理员的账号管理权限不等于读取学生教育内容。**

---

# 默认拒绝与状态联动

当前 Policy 遵守以下规则：

1. 未认证用户默认拒绝。
2. 停用账号默认拒绝。
3. 暂停 / 归档学校不提供当前运营权限。
4. 学生离校后不再进入当前在读学生权限范围。
5. 家长关系停用后立即失去对应学生空间权限。
6. 任课关系、班主任关系或教师角色停用后，相应权限立即失效。
7. 教师 / 班主任范围只使用当前有效学年中的关系。
8. A 校的业务关系不能产生 B 校权限。
9. Django `is_staff / is_superuser` 不自动获得学校业务权限。

核心目标是：

> 人员或组织关系发生变化时，只修改真实业务事实，权限随之自动变化，不维护第二份权限名单。

---

# 内容可见级别

以下内容级别仍然是正式产品设计的一部分：

### `STUDENT_GUARDIAN`

学生本人、有效家长，以及对该具体对象有业务需要的教职工可见。

### `GUARDIAN_ONLY`

有效家长以及对该具体对象有业务需要的教职工可见；学生本人不可见。

### `STAFF_ONLY`

仅对该具体对象具有明确业务职责的教职工可见。

## 为什么 Phase 5 不提前实现万能内容权限

Phase 5 当前只有身份、关系和学术组织，没有真实 `SubjectComment / StudentReport` 内容对象。

如果现在实现一个泛化的：

```text
can_view_guardian_only_content(user, student)
```

很容易错误地得出“只要这名教师教过这个学生，就能看所有家长专属信息”。这是权限过宽。

因此内容级权限将在 Phase 6 与真实报告字段、创建者、学科、审核状态和工作流一起实现对象级 Policy。

这是有意延后，不是遗漏。

---

# 初始业务权限矩阵

| 能力 | 学生 | 家长 | 学科教师 | 班主任 | 学术管理员 | 系统管理员 |
|---|---:|---:|---:|---:|---:|---:|
| 进入学生业务空间 | 本人 | 已绑定学生 | 当前任教学生 | 当前本班学生 | 默认否 | 默认否 |
| 创建学科评价 | 否 | 否 | 任教学科 / 学生 | 如有对应任课关系 | 否 | 否 |
| 审核完整报告 | 否 | 否 | 否 | 当前本班学生 | 默认否；升级机制后定 | 否 |
| 修改学术关系 | 否 | 否 | 否 | 否 | 是 | 否 |
| 管理学校账号 | 否 | 否 | 否 | 否 | 否 | 是 |
| 查看家长专属内容 | Phase 6 定义 | Phase 6 定义 | Phase 6 对象级定义 | Phase 6 对象级定义 | Phase 6 对象级定义 | 默认否 |
| 查看 Staff-only 内容 | 否 | 否 | Phase 6 对象级定义 | Phase 6 对象级定义 | Phase 6 对象级定义 | 默认否 |

管理员权限坚持最小化，不因为名称里有“管理员”就自动获得所有教育内容。

---

# 家长访问模型

一名学生在一所学校可以绑定多个授权家长，每位家长拥有独立、可审计的登录身份。

```text
Student（平台稳定 UUID）
└── School A Membership / S000381
    ├── Student Account
    ├── Guardian A Account
    └── Guardian B Account
```

家长授权绑定的是“这名学生在这所学校中的成员关系”，而不是自动获得该学生在其他学校中的资料。

---

# 跨学校身份规则

平台允许同一个 `Student` 拥有多所学校成员关系，以支持教育集团、多校区或经授权的转学连续性。但这是高敏感能力：

1. 禁止根据姓名、邮箱、生日、文本相似度或 AI 自动合并跨校学生身份。
2. 不同学校导入学生时，默认不得因为“看起来像同一个人”就复用既有 `Student`。
3. 跨校身份关联必须由明确、可审计、经过授权的流程完成。
4. 一所学校只能通过自己的 `StudentSchoolMembership` 进入该校学生业务数据。
5. Student Timeline 未来必须保持学校数据边界，不能把跨校记录默认拼接给任一学校用户。

---

# 技术管理员与业务管理员

`RoleAssignment.SYSTEM_ADMIN` 是学校范围的业务系统管理角色。

Django `is_staff / is_superuser` 是平台技术运维能力。

二者不得自动互相赋权。

技术超级管理员在基础设施层面客观上拥有很高能力，因此正式生产还需要：

- 运维账号隔离；
- 高权限审计；
- 最小化日常 superuser 使用；
- 后续 break-glass / 紧急访问制度。

不能靠“业务 Policy 不授权 superuser”就假装数据库管理员在物理上看不到数据。

---

# 安全原则

1. 默认拒绝，明确授权后才允许访问。
2. 所有权限检查必须在服务器端执行。
3. 前端隐藏按钮不等于权限控制。
4. 后续页面与 API 优先使用 Policy 返回的安全 QuerySet，而不是先查询全校数据再手工过滤。
5. 高权限操作必须写入审计日志。
6. 技术管理员权限不自动等于查看教育内容的权限。
7. 日常学校业务不应依赖直接访问数据库完成。
8. UUID 的不可猜测性不能被当作安全边界。
9. 内容级对象权限尚未完成前，继续只使用虚拟数据。
10. 每个新增业务模块必须复用集中 Policy 层或在同一 Policy 体系下扩展，禁止在 View / Template 中散落新的权限真相。
