# 开发实施计划

本文档是“学校数字化平台”的主开发计划，规定开发顺序、阶段边界、交付物、验收标准和进入下一阶段的条件。

新增需求必须先检查 `PRODUCT_PHILOSOPHY.md`，再决定是否调整本计划。不得因为临时需求破坏底层模型、权限边界和核心工作流。

从 Phase 3 起，每个阶段同时接受：

1. **功能核验**：代码、数据库、权限、状态和测试是否正确；
2. **业务意义核验**：是否减少人工、减少重复、提高准确性，并避免制造死数据和新的维护负担。

只有两类核验都能解释清楚，阶段才允许继续。

---

# 0. 总体目标

平台不是为单一学校定制的周报工具，而是面向多所学校、可持续扩展的现代学校运营平台。

第一轮不追求“功能数量”，而是验证以下基础能力可以稳定组合：

```text
School / Tenant
    ↓
Identity & Relationship
    ↓
Contextual Permission
    ↓
Event / State / Workflow
    ↓
Student Timeline
    ↓
Learning Report
```

首个完整业务闭环选择“学习报告”，因为它同时验证：

- 学生身份；
- 家长关系；
- 教师任课关系；
- 班主任关系；
- 对象级内容权限；
- 状态流转；
- 审核与发布；
- 家长 / 学生不同视图；
- 审计；
- 通知。

只有这个闭环稳定后，才进入考勤、请假、课表、作业等更广泛模块。

---

# 第一阶段：工程与架构底座

## Phase 1：工程初始化 ✅

### 目标

建立长期可维护的 Django 工程，而不是一次性 Demo。

### 已实现

- Django 5.2 LTS；
- PostgreSQL；
- Development / Test / Staging / Production 配置分层；
- `zh-hans`；
- `Asia/Shanghai`；
- 环境变量；
- 基础错误页；
- 健康检查；
- GitHub Actions；
- 自动化测试骨架。

### 明确不提前引入

- React / Next.js；
- Redis；
- Celery；
- 消息队列；
- Kubernetes；
- AI；
- 正式邮箱。

只有现实需求出现时才增加复杂度。

---

# 第二阶段：多学校与身份底座

## Phase 2：School / Tenant ✅

### 目标

从第一天避免把系统写死成“只有一所学校”。

### 已实现

- `School`；
- `AcademicYear`；
- 学校作用域基础模型与查询；
- PostgreSQL 约束；
- 多学校隔离测试。

### 设计调整

原计划中的通用 `SchoolSettings` **暂缓**。

原因：目前没有具体业务消费者。只有第一个真实“按学校配置行为”的需求出现时，才建立配置模型，避免制造空配置仓库。

---

## Phase 3：统一身份与关系模型 ✅

### 目标

建立全平台最重要的基础：谁是谁，以及谁和谁存在什么关系。

### 已实现

- `UserAccount`；
- `Student`；
- `StudentSchoolMembership`；
- `GuardianRelationship`；
- `RoleAssignment`。

### 核心规则

- 一个真实人尽量一个登录账号；
- 学生平台身份与学校学号分离；
- 同一个账号可以同时是教师和家长；
- 家长授权绑定学校范围内的学生成员关系；
- 学校角色有明确学校作用域；
- 姓名、邮箱不是关系主键；
- 跨学校学生身份禁止自动匹配和 AI 推断。

### 设计调整

原计划中的 `GuardianProfile / StaffProfile` 暂不建立。

当前没有独立业务字段需要它们；家长身份和员工权限可以由真实关系完整表达。以后有明确字段消费者时再增加。

---

# 第三阶段：学术关系与权限

## Phase 4：最小学术结构 ✅

### 目标

只建立后续工作流真正需要的学术关系，不复制传统 SIS 的字段大全。

### 已实现

- `ClassGroup`；
- `Subject`；
- `StudentClassMembership`；
- `TeachingAssignment`；
- `HomeroomAssignment`。

### 关键设计

`ClassGroup` 区分：

- `HOMEROOM`：行政 / 班主任班级；
- `TEACHING`：数学分层、语言组、选课组等真实教学组织。

系统已经可以回答：

- 某学生当前属于哪些组织；
- 某教师实际教哪些学生、哪门学科；
- 谁是某班班主任；
- 上游账号 / 角色 / 学生状态变化后，哪些学术关系仍实际有效。

未提前增加教室、课表、课程颜色、部门等首个报告闭环不消费的数据。

---

## Phase 5：RBAC + Contextual Permission ✅

### 目标

建立“学校 + 身份 + 真实关系 + 操作类型”的集中式服务器端权限体系。

权限不是第二份人工维护名单，而是从现有真实关系自动推导。

### Phase 5A：Policy 核心

已建立：

- `visible_student_memberships_for()`；
- `can_access_student_space()`；
- `writable_student_memberships_for_subject()`；
- `can_write_subject_comment()`；
- `reviewable_student_memberships_for()`；
- `can_review_student_report()`；
- `can_manage_academic_structure()`；
- `can_manage_school_accounts()`。

### Phase 5B：负向权限矩阵

重点验证拒绝路径：

- A 校关系不能访问 B 校；
- 学生只能进入自己的学生空间；
- 家长只能进入明确绑定学生；
- 教师只能覆盖真实有效任课范围；
- 普通学科教师不能审核完整报告；
- 班主任只能覆盖真实 HOMEROOM；
- 停用关系、角色、账号后权限失效；
- 旧学年关系不继续产生当前教师权限；
- 学术管理员 / 系统管理员不会因为“管理员”身份自动读取学生内容；
- Django superuser 不自动获得学校业务权限。

当前全仓库自动化测试：**62 个通过**。

### Phase 5C：安全 QuerySet

后续 View / API 应优先使用 Policy 返回的已过滤 QuerySet，而不是：

```text
先查全校数据
↓
再依赖页面 / 开发者手工过滤
```

### 内容权限边界调整

`STUDENT_GUARDIAN / GUARDIAN_ONLY / STAFF_ONLY` 仍是正式设计，但**完整对象级内容权限移到 Phase 6**。

原因：Phase 5 尚无真实 `SubjectComment / StudentReport` 对象。提前写万能内容权限容易把关系权限错误放大为所有内容读取权。

### Phase 5 结论

- 功能核验：`PASS`
- 业务意义核验：`PASS WITH RISK`

主要风险：真实 View/API 尚未接入 Policy；历史内容访问政策和细粒度 Academic Admin scope 尚未冻结。

因此仍然只使用虚拟数据。

---

# 第四阶段：首个完整业务闭环——学习报告

## Phase 6：报告模型、状态机与对象级内容权限 ← 当前

### 目标

建立首个真正可运行的学校业务流程，并把 Phase 5 的关系权限落实到真实对象。

### 核心模型

- `ReportCycle`；
- `SubjectComment`；
- `StudentReport`；
- `ReviewAction`。

### `SubjectComment` 内容边界

至少区分：

- 学生可见反馈；
- 家长专属信息；
- 教职工内部备注。

这三类字段必须在真实对象上实现服务器端可见性规则。

### 第一版状态流

```text
DRAFT
→ SUBMITTED
→ REVIEW
→ APPROVED
→ READY_TO_PUBLISH
→ PUBLISHED
```

允许退回：

```text
REVIEW → RETURNED → SUBMITTED
```

最终状态名可在开发时根据最小真实工作流再次核验，但不得出现模糊或无业务动作对应的状态。

### 核心要求

- 每次状态变化有明确动作、操作者和时间；
- 状态跳转由服务器端验证；
- 教师只能创建 / 修改自己实际任课范围的学科评价；
- 班主任只能审核真实 HOMEROOM 范围；
- Academic Admin 的升级 / 发布能力不自动等于读取全部内部内容；
- 学生、家长、教师、班主任对同一对象得到不同字段视图；
- 发布是系统状态变化，不等于发送邮件。

### Phase 6 业务核验重点

必须回答：

> 老师是否只产生一次学习事实，系统就能让后续审核、家长查看、时间线和通知自然消费，而不是要求不同角色重复填写？

---

## Phase 7：教师端高效率录入

### 目标

验证平台不是“电子表格搬家”，而是真的减少教师操作。

### 第一版 UX

- 一个页面处理一个班级；
- 快速切换学生；
- 自动保存草稿；
- 已完成 / 未完成状态一眼可见；
- 可连续提交；
- 不重复输入系统已知学生资料；
- 高信息密度，避免无意义卡片化。

### 关键指标

- 完成一个班报告所需时间；
- 每名学生平均点击次数；
- 重复输入次数；
- 未保存 / 丢失内容事件。

目标不是页面漂亮，而是明显减少人工。

---

## Phase 8：班主任审核与发布

### 目标

让班主任重点处理异常，而不是逐条机械确认。

### 功能

- 查看缺失学科；
- 识别未提交评价；
- 查看异常 / 待处理项目；
- 退回单个学科评价；
- 批准完整学生报告；
- 批量查看发布准备状态；
- 学术管理员执行发布流程。

### 原则

正常完整性尽量由状态和规则自动确认，人处理异常和判断。

---

## Phase 9：学生端 / 家长端

### 目标

验证“同一个学生，不同角色，不同视图”。

### 学生端

显示学生可见学习反馈和报告。

### 家长端

显示：

- 学生可见内容；
- 家长专属信息。

不得显示 Staff-only 内部信息。

### 验收标准

使用同一名虚拟学生分别以学生、Guardian A、Guardian B、教师、班主任和管理员访问，所有字段视图符合对象级 Policy。

---

# 第五阶段：事件、时间线与审计

## Phase 10：Event 基础层

### 目标

避免未来每个业务模块形成孤岛。

首批事件：

```text
SubjectCommentCreated
SubjectCommentSubmitted
ReportReturned
ReportApproved
ReportPublished
GuardianViewedReport
```

事件表达发生过的业务事实，不等于普通日志。

第一版不引入复杂 Event Bus，在模块化单体内实现稳定事件接口。

---

## Phase 11：Student Timeline

### 目标

建立“一名学生，一条持续时间线”的第一版。

首批只纳入已有业务：

- 学习反馈；
- 报告审核；
- 报告发布；
- 家长查看。

Timeline 是统一事实的视图，不复制第二份业务数据。

---

## Phase 12：Audit Log

### 目标

建立安全审计和责任追踪。

至少记录：

- 登录关键事件；
- 权限 / 角色变化；
- 家长关系变化；
- 报告提交、退回、批准、发布；
- 高权限操作；
- 敏感数据导出。

业务 Event 与安全 Audit 概念分离，但可以关联。

---

# 第六阶段：通知与外部连接

## Phase 13：Notification Outbox

### 目标

把“业务发布”和“外部通知”彻底解耦。

```text
ReportPublished
↓
Create Notification
↓
Outbox
↓
Send
↓
SENT / FAILED
```

### 要求

- 幂等；
- 防重复发送；
- 失败可重试；
- 邮件故障不能回滚已经发布的报告；
- 第一版使用 Console / Test Adapter；
- 后续再接 Outlook / SMTP。

---

# 第七阶段：预发布环境与质量门槛

## Phase 14：Staging

### 目标

在真实服务器架构上验证系统，但仍只使用虚拟或经授权的脱敏数据。

### 组成

- Linux；
- PostgreSQL；
- Gunicorn / ASGI Server；
- Nginx；
- HTTPS；
- 自动备份；
- 恢复脚本；
- 基础监控。

### 验收标准

- 从零可部署；
- 数据库可备份；
- 备份可恢复；
- 服务重启不丢数据；
- 权限测试通过；
- 没有秘密进入 Git 仓库。

---

## Phase 15：性能与 UX 验证

### 目标

只优化真实高频路径，不提前做无意义性能工程。

重点测试：

- 教师批量填写；
- 班主任审核；
- 报告统一发布；
- 家长集中查看。

优化依据必须来自测量结果。

没有测量证据，不提前加入 Redis、微服务或复杂缓存。

---

# 第八阶段：AI 辅助

## Phase 16：AI Provider

AI 必须是可拔插能力：

```text
AI_PROVIDER=none | local | external
```

### 第一批 AI 功能

- 评价润色；
- 重复表达检查；
- 内容完整性提醒；
- 报告汇总草稿；
- 长期学习反馈摘要。

### 禁止事项

AI 不得：

- 创建学生与家长关系；
- 猜测收件人；
- 自主改变权限；
- 编造学习事实；
- 绕过人工审核直接发布。

---

# 第九阶段：有限生产试点

## Phase 17：Production Pilot

只有完成安全、隐私、备份、恢复和学校内部审批后，才允许接触有限真实用户。

### 试点范围

优先：

- 少量班级；
- 少量教师；
- 一个报告周期。

### 必须测量

- 教师平均填写时间；
- 班主任平均审核时间；
- 报告发布所需人工步骤；
- 家长查看成功率；
- 错误和返工率；
- 支持请求数量；
- 用户真正抱怨的操作。

用业务结果决定是否扩展，而不是因为“功能写完了”就宣布成功。

---

# 第十阶段：平台扩展

学习报告闭环稳定后，才按业务价值选择下一模块。

优先级由“能删除多少人工动作、能提升多少业务质量”决定，而不是传统 SIS 菜单决定。

## 候选 A：请假 + 出勤统一系统

```text
LeaveApproved
↓
自动改变 Expected Attendance
↓
教师只处理异常
```

禁止重新造两个互不相干的请假和考勤孤岛。

## 候选 B：Schedule / Timetable

课表首先是系统状态来源：系统知道谁在何时应该在哪里。

未来按真实价值增加：冲突检测、自动调课、教室分配、替课建议。

## 候选 C：Assignments / Learning Tasks

目标：

```text
布置 → 提交 → 反馈 → 学习记录 → 报告
```

形成连续数据链，而不是复制一个巨型 LMS。

## 候选 D：家长沟通与任务

把真正需要家长处理的事项统一为 Action，而不是制造更多消息渠道。

---

# 开发工作方式

## 1. 小步提交

每个 Commit 应有一个清晰目的，避免同时混入数据库、UI、权限、AI 和通知等多类变化。

## 2. 每个 Phase 至少两类核验

### 功能核验

至少覆盖：

- 正常路径；
- 权限拒绝路径；
- 状态非法跳转；
- 跨学校隔离；
- 边界条件；
- migration 漂移。

### 业务意义核验

至少回答：

- 真实业务问题是什么？
- 删除了哪些人工动作？
- 是否重复保存系统已经知道的信息？
- 新数据由谁消费？
- 正常状态能否自动推导？
- 风险和失败模式是什么？

测试全绿不等于业务阶段自动通过。

## 3. Definition of Done

一个功能只有同时满足以下条件才算完成：

- 业务问题明确；
- 数据模型合理；
- 权限检查存在；
- 自动化测试通过；
- 中文业务语义清晰；
- 错误状态可理解；
- 关键行为具备审计路径设计；
- 没有制造重复数据；
- 没有要求用户重复输入系统已知信息；
- 开发日志记录收益与风险；
- 文档同步更新。

## 4. No Dead Data

每一个新字段必须说明：

```text
Producer：谁产生？
Consumer：谁使用？
Action：会触发什么？
Retention：为什么值得保留？
```

无法回答则默认不新增。

## 5. Complexity on demand

只有出现测量证据后才考虑：

- Redis；
- Worker；
- 独立前端；
- 微服务；
- 消息队列；
- Kubernetes。

先保持简单、透明、可维护。

---

# 当前进度

```text
Phase 1  工程初始化                         ✅
Phase 2  School / Tenant                  ✅
Phase 3  统一身份与关系                    ✅
Phase 4  最小学术结构                      ✅
Phase 5  Contextual Permission            ✅
Phase 6  报告模型 + 状态机 + 对象级权限    ← 当前
Phase 7  教师高效率录入
Phase 8  班主任审核与发布
Phase 9  学生 / 家长视图
Phase 10 Event
Phase 11 Student Timeline
Phase 12 Audit
Phase 13 Notification Outbox
Phase 14 Staging
Phase 15 UX / 性能验证
Phase 16 AI
Phase 17 有限生产试点
```

当前下一步：

> **Phase 6：建立学习报告核心对象、状态机和内容级对象权限。**

在 Phase 6、真实 endpoint 权限测试和后续 Staging 安全验证完成前，继续只使用虚拟数据，不接入真实学生生产数据。
