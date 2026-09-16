# 开发实施计划

本文档是“学校数字化平台”的主开发计划。它规定开发顺序、阶段边界、交付物、验收标准和进入下一阶段的条件。

开发过程中如出现新需求，应首先检查 `PRODUCT_PHILOSOPHY.md`，再判断是否调整本计划。不得因为临时需求随意破坏底层模型、权限边界和核心工作流。

---

## 0. 总体目标

平台不是为单一学校定制的周报工具，而是面向多所学校、可持续扩展的现代学校运营平台。

第一阶段不追求“功能多”，而是证明以下基础能力可以稳定组合：

```text
School / Tenant
    ↓
Identity & Relationship
    ↓
Permission
    ↓
Event / State / Workflow
    ↓
Student Timeline
    ↓
Learning Report
```

首个完整业务闭环仍然选择“学习报告”，因为它同时验证：

- 学生身份
- 家长关系
- 教师任课关系
- 内容权限
- 状态流转
- 审核
- 发布
- 家长 / 学生不同视图
- 审计
- 通知

只有这个闭环跑通，才进入更广泛的学校业务模块。

---

# 第一阶段：工程与架构底座

## Phase 1：工程初始化

### 目标

建立长期可维护的 Django 工程，而不是一次性 Demo。

### 开发内容

- Django 5.2 LTS 项目
- Python 虚拟环境与依赖管理
- PostgreSQL 作为标准数据库
- Development / Test / Staging / Production 配置分层
- `zh-hans` 默认语言
- `Asia/Shanghai` 默认时区
- 环境变量配置
- 基础日志
- 测试框架
- 静态文件与模板目录
- 基础错误页
- 健康检查接口

### 初始 Django Apps

```text
core
schools
accounts
students
academics
reports
events
notifications
audit
```

模块边界先建立，但保持模块化单体，不拆微服务。

### 验收标准

- 本地可一条命令启动
- PostgreSQL migration 正常
- 测试可独立运行
- 中文界面设置生效
- 不包含任何真实学生数据
- `.env` 等敏感信息不会进入 Git

### 明确不做

- React / Next.js
- Redis
- Celery
- 消息队列
- Kubernetes
- AI
- 正式邮箱

只有现实需求出现时才增加复杂度。

---

# 第二阶段：多学校与身份底座

## Phase 2：School / Tenant 模型

### 目标

从第一天避免把系统写死成“只有一所学校”。

### 核心模型

- `School`
- `SchoolSettings`
- `AcademicYear`

所有核心业务记录必须可以明确归属于一个学校。

### 第一版策略

采用共享应用、共享数据库、所有业务数据带 `school_id` 的简单多租户模式。

暂不引入复杂 schema-per-tenant 或 database-per-tenant 架构。

### 验收标准

- 两所虚拟学校可同时存在
- A 学校用户无法访问 B 学校数据
- 核心查询默认具备学校作用域
- 自动化测试覆盖跨学校数据隔离

---

## Phase 3：统一身份与关系模型

### 目标

建立全平台最重要的基础：谁是谁，以及谁和谁存在什么关系。

### 核心模型

- `UserAccount`
- `Student`
- `GuardianProfile`
- `StaffProfile`
- `GuardianRelationship`
- `StudentSchoolMembership`
- `RoleAssignment`

### 核心规则

- 一个学生拥有稳定永久 ID
- 登录账号和学生实体分离
- 一个学生可关联多个家长 / 监护人
- 一个家长可关联多个学生
- 一个员工可拥有多个角色
- 角色必须有学校作用域
- 姓名和邮箱不能作为关系主键

### 验收标准

能构造以下测试场景：

```text
School A
├── Student S001
│   ├── Student Account
│   ├── Guardian A
│   └── Guardian B
└── Teacher T001
```

并验证每个角色只能访问授权范围。

---

# 第三阶段：学术关系与权限

## Phase 4：最小学术结构

### 目标

只建立后续工作流真正需要的学术关系，不先复制传统 SIS 的全部字段。

### 核心模型

- `ClassGroup`
- `Subject`
- `StudentClassMembership`
- `TeachingAssignment`
- `HomeroomAssignment`

### 第一性原理要求

每个字段都必须说明后续用途。

例如：

- TeachingAssignment 用于决定教师可评价哪些学生
- HomeroomAssignment 用于决定谁可以审核完整报告

不得为了“以后也许有用”大量增加字段。

### 验收标准

系统能够回答：

- 某学生属于哪个班
- 某教师教哪个班的哪门学科
- 某班班主任是谁
- 某教师当前是否有权访问某学生

---

## Phase 5：RBAC + Contextual Permission

### 目标

建立“角色 + 关系 + 学校作用域”的服务器端权限体系。

### 权限判断示例

```text
是否允许访问学生？
=
学校一致
AND
角色允许
AND
业务关系成立
AND
内容可见级别允许
```

### 首批角色

- 学生
- 家长 / 监护人
- 学科教师
- 班主任
- 学术管理员
- 系统管理员

### 内容可见级别

- `STUDENT_GUARDIAN`
- `GUARDIAN_ONLY`
- `STAFF_ONLY`

### 验收标准

建立权限自动化测试矩阵，重点验证“禁止访问”的场景。

隐藏按钮不算权限控制，服务端必须拒绝越权请求。

---

# 第四阶段：首个完整业务闭环——学习报告

## Phase 6：报告数据模型与状态机

### 目标

建立首个真正可运行的学校业务流程。

### 核心模型

- `ReportCycle`
- `SubjectComment`
- `StudentReport`
- `ReviewAction`

### SubjectComment 结构

至少区分：

- 学生可见反馈
- 家长专属信息
- 教职工内部备注

### 状态流

```text
DRAFT
→ SUBMITTED
→ REVIEW
→ APPROVED
→ READY_TO_PUBLISH
→ PUBLISHED
```

允许：

```text
REVIEW → RETURNED → SUBMITTED
```

### 核心要求

状态变化必须有明确动作、操作者、时间和权限。

发布是系统状态变化，不是“发送邮件”。

---

## Phase 7：教师端高效率录入

### 目标

验证平台不是“电子表格搬家”，而是真的减少教师操作。

### 第一版 UX

- 一个页面处理一个班级
- 快速切换学生
- 自动保存草稿
- 已完成 / 未完成状态一眼可见
- 可连续提交
- 不要求重复输入已有学生信息
- 高信息密度，避免无意义卡片化

### 关键指标

记录：

- 完成一个班报告所需时间
- 每名学生平均点击次数
- 重复输入次数
- 未保存 / 丢失内容事件

目标不是页面漂亮，而是比原人工流程明显省事。

---

## Phase 8：班主任审核与发布

### 目标

让班主任只处理异常，而不是逐条机械确认。

### 功能

- 一眼查看缺失学科
- 识别未提交评价
- 查看异常 / 待处理项目
- 退回单个学科评价
- 批准完整学生报告
- 批量查看发布准备状态
- 学术管理员统一发布

### 核心原则

正常内容尽量通过状态和规则自动确认完整性；人工重点处理异常。

---

## Phase 9：学生端 / 家长端

### 目标

验证“同一个学生，不同角色，不同视图”。

### 学生端

显示学生可见的学习反馈和报告。

### 家长端

显示：

- 学生可见内容
- 家长专属信息

不得显示：

- Staff-only 内部信息

### 验收标准

用同一名虚拟学生分别以学生、Guardian A、Guardian B、教师、管理员身份访问，所有视图符合权限模型。

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

事件不等于日志。事件用于表达发生过的业务事实，并允许未来触发后续动作。

第一版不需要复杂 Event Bus，先在单体应用内实现稳定事件接口。

---

## Phase 11：Student Timeline

### 目标

建立“一名学生，一条持续时间线”的第一版。

首批时间线内容只纳入当前已有业务：

- 学习反馈
- 报告审核
- 报告发布
- 家长查看

以后请假、出勤、作业等事件再自然接入。

### 原则

Timeline 是统一底层事实的视图，不复制第二份业务数据。

---

## Phase 12：Audit Log

### 目标

建立安全审计和责任追踪。

至少记录：

- 登录关键事件
- 权限 / 角色变化
- 家长关系变化
- 报告提交、退回、批准、发布
- 高权限操作
- 敏感数据导出

业务 Event 与安全 Audit 概念分离，但可以关联。

---

# 第六阶段：通知与外部连接

## Phase 13：Notification Outbox

### 目标

把“业务发布”和“外部通知”彻底解耦。

### 流程

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

- 幂等
- 防重复发送
- 失败可重试
- 发布失败不能因为邮件服务故障而回滚
- 第一版先使用 Console/Test Adapter
- 后续再接 Outlook / SMTP

---

# 第七阶段：预发布环境与质量门槛

## Phase 14：Staging

### 目标

在真实服务器架构上验证系统，但仍然只使用虚拟或经过授权的脱敏数据。

### 组成

- Linux
- PostgreSQL
- Gunicorn / ASGI Server
- Nginx
- HTTPS
- 自动备份
- 恢复脚本
- 基础监控

### 验收标准

- 从零可部署
- 数据库可备份
- 备份可恢复
- 服务重启不丢数据
- 权限测试通过
- 没有秘密写入代码仓库

---

## Phase 15：性能与 UX 验证

### 目标

优化真实高频路径，而不是提前进行无意义的性能工程。

重点测试：

- 教师批量填写
- 班主任审核
- 报告统一发布
- 家长集中查看

优化依据必须来自测量结果。

不因为“可能以后会慢”就提前加入 Redis、微服务或复杂缓存。

---

# 第八阶段：AI 辅助

## Phase 16：AI Provider

### 原则

AI 必须是可拔插能力：

```text
AI_PROVIDER=none | local | external
```

### 第一批 AI 功能

- 中文评价润色
- 重复表达检查
- 内容完整性提醒
- 报告汇总草稿
- 长期学习反馈摘要

### 禁止事项

AI 不得：

- 创建学生与家长关系
- 猜测收件人
- 自主改变权限
- 编造学习事实
- 绕过人工审核直接发布

---

# 第九阶段：有限生产试点

## Phase 17：Production Pilot

在完成安全、隐私、备份、恢复和学校内部审批之后，才允许接触有限真实用户。

### 试点范围

优先选择：

- 少量班级
- 少量教师
- 一个报告周期

### 必须测量

- 教师平均填写时间
- 班主任平均审核时间
- 报告发布所需人工步骤
- 家长查看成功率
- 错误和返工率
- 支持请求数量
- 用户真正抱怨的操作

### 试点原则

用业务结果决定是否扩展，而不是因为“功能已经写完”就宣布成功。

---

# 第十阶段：平台扩展

学习报告闭环稳定后，才按业务价值选择下一模块。

优先候选不是由传统 SIS 菜单决定，而由“能够删除多少人工动作”决定。

## 候选 A：请假 + 出勤统一系统

目标：

```text
LeaveApproved
↓
自动改变 Expected Attendance
↓
教师只处理异常
```

禁止重新造两个互不相干的“请假模块”和“考勤模块”。

## 候选 B：Schedule / Timetable

课表首先作为“系统知道谁在何时应该在哪里”的基础状态来源。

未来再根据真实需求增加：

- 冲突检测
- 自动调课
- 教室分配
- 替课建议

## 候选 C：Assignments / Learning Tasks

目标不是复制大型 LMS，而是让：

```text
布置 → 提交 → 反馈 → 学习记录 → 报告
```

形成一个连续数据链。

## 候选 D：家长沟通与任务

把真正需要家长处理的事项统一为 Action，而不是制造更多消息渠道。

---

# 开发工作方式

## 1. 小步提交

每个 Commit 应只有一个清晰目的。

避免一次提交同时：

- 改数据库
- 重写 UI
- 重构权限
- 加 AI
- 改通知

这样出了问题才能快速定位和回滚。

## 2. 每个 Phase 都有测试

不得用“页面看起来能点”作为完成标准。

至少测试：

- 正常路径
- 权限拒绝路径
- 状态非法跳转
- 跨学校数据隔离
- 边界条件

## 3. Definition of Done

一个功能只有同时满足以下条件才算完成：

- 业务问题明确
- 数据模型合理
- 权限检查存在
- 自动化测试通过
- 中文界面可用
- 错误状态可理解
- 关键行为可审计
- 没有制造重复数据
- 没有要求用户重复输入系统已知信息
- 文档同步更新

## 4. 新功能必须通过 No Dead Data 检查

每一个新字段必须说明：

```text
Producer：谁产生？
Consumer：谁使用？
Action：会触发什么？
Retention：为什么值得保留？
```

无法回答则默认不新增。

## 5. 不提前优化

只有出现测量证据后才考虑：

- Redis
- Worker
- 独立前端
- 微服务
- 消息队列
- Kubernetes

先保持简单、透明、可维护。

---

# 第一轮实际开发顺序

从现在开始，严格按以下顺序推进：

```text
01 Django 工程初始化
02 PostgreSQL + 环境配置
03 School / Tenant
04 UserAccount / Student / Guardian / Staff
05 RoleAssignment + Permission 基础
06 AcademicYear / Class / Subject / TeachingAssignment
07 测试数据生成
08 登录与角色首页
09 ReportCycle / SubjectComment / StudentReport
10 教师填写页面
11 提交与状态机
12 班主任审核
13 发布
14 家长 / 学生不同视图
15 Permission Tests
16 Event / Timeline
17 Audit
18 Notification Outbox
19 Staging
20 UX / 性能验证
21 AI
22 有限生产试点
```

在第 14 步之前，不主动扩展考勤、请假、作业、排课等新业务模块。

---

# 当前最近目标

当前正式进入：

> **Phase 1：工程初始化**

完成 Phase 1 后，再进入多学校和身份底座。

除非发现基础架构存在重大问题，否则后续开发默认按本文档顺序推进。
