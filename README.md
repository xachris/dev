# 学校数字化平台

一个面向现代学校、以中国学校为核心使用场景、可由学校自主部署和控制的数字化运营平台。

项目不以复制传统 SIS 的功能清单为目标，而以“减少重复录入、减少等待、减少错误、提高自动化和业务质量”为核心。平台从统一身份、关系、权限、事件、状态、工作流和学生时间线出发，再逐步组合出学习报告、请假与出勤、课表、任务等具体业务能力。

> 当前首个完整业务闭环：**学习报告系统 V0.1**

## 核心产品原则

- **一个学生，一个稳定平台身份；每所学校使用自己的稳定学号；多种身份，不同视图。**
- **一个真实人尽量只维护一个登录账号，多种业务身份通过关系表达。**
- **报告留在学校系统内，外部只发送通知。**
- **不产生无用途的“死数据”。**
- **一份数据，只产生一次，多处复用。**
- **正常状态自动推导，人只处理异常。**
- **系统不是记录系统，而是行动系统。**
- 数据应作为业务流程自然留下的副产品，而不是要求教职工为了“填系统”额外制造。
- AI 只作为辅助能力，核心业务流程不能依赖 AI 才能运行。
- 收件人、学生关系和权限必须来自结构化学校数据，不能由 AI 猜测。
- 优先采用学校可控、可迁移、低供应商锁定的技术架构。
- 正式数据必须可审计、可备份、可恢复、可追踪。

完整设计原则见：[`docs/PRODUCT_PHILOSOPHY.md`](docs/PRODUCT_PHILOSOPHY.md)。后续新增功能、数据字段、工作流和 AI 能力时，应优先以该文档作为产品和架构判断依据。

## 核心设计文档

- [`docs/PRODUCT_PHILOSOPHY.md`](docs/PRODUCT_PHILOSOPHY.md)：产品设计哲学与新增功能检查清单
- [`docs/DEVELOPMENT_PLAN.md`](docs/DEVELOPMENT_PLAN.md)：主开发实施计划、阶段顺序与验收标准
- [`docs/VERIFICATION_STANDARD.md`](docs/VERIFICATION_STANDARD.md)：功能核验 + 业务意义核验双重标准
- [`docs/worklog/README.md`](docs/worklog/README.md)：分阶段开发日志索引
- [`docs/ROADMAP.md`](docs/ROADMAP.md)：平台级版本路线图
- [`docs/PROJECT_OVERVIEW.md`](docs/PROJECT_OVERVIEW.md)：项目定位与范围
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)：总体架构
- [`docs/DATA_MODEL.md`](docs/DATA_MODEL.md)：当前实际数据模型与后续计划
- [`docs/PERMISSION_MODEL.md`](docs/PERMISSION_MODEL.md)：身份、关系与权限模型
- [`docs/SECURITY_BASELINE.md`](docs/SECURITY_BASELINE.md)：安全基线
- [`docs/LOCALIZATION.md`](docs/LOCALIZATION.md)：中文产品与代码语言规范

## 默认使用环境

- 核心用户：中国学校及国际学校
- 默认产品语言：简体中文（`zh-CN`）
- 默认时区：`Asia/Shanghai`
- 用户界面、通知、业务术语和操作说明：中文优先
- 代码、数据库字段、API、枚举值：英文优先，便于开发维护
- 平台从底层考虑多学校 / 多租户，而不是只服务单一学校

## 首个完整业务闭环

仅使用虚拟测试数据完成：

`教师填写 -> 提交 -> 班主任审核 -> 批准 -> 发布 -> 家长查看 / 学生查看`

这个闭环将用于验证：

- School / Tenant
- Student Identity / 学校学号
- 学生 / 家长 / 教师关系
- 任课关系
- RBAC 与内容可见级别
- 状态机
- 审核与发布
- 学生 / 家长不同视图
- Event / Timeline
- Audit
- Notification Outbox

首轮开发暂不接入真实学生数据、正式 Outlook 邮件或正式生产 AI。

## 仓库结构

- `docs/`：产品哲学、开发计划、架构、数据模型、权限、安全、开发日志和路线图
- `backend/`：Django 后端应用
- `tests/`：自动化测试和完整流程测试
- `deployment/`：服务器、反向代理、备份和部署配置
- `archive/`：本项目初始化前的旧仓库内容

## 当前开发阶段

已完成并通过双重验收：

- Phase 1：工程初始化
- Phase 2：School / Tenant 多学校底座
- Phase 3：统一身份与关系模型
- Phase 4：最小学术结构
- Phase 5：RBAC + Contextual Permission

下一阶段：

> **Phase 6：学习报告数据模型、状态机与对象级内容权限**

Phase 5 已建立集中式服务器端 Policy 层，并通过 62 个自动化测试验证跨校、任课、班主任、家长、管理员、账号停用、学年失效等允许与拒绝路径。

Phase 5 的功能核验结论为 `PASS`，业务意义核验结论为 `PASS WITH RISK`。关系型权限已经成立，但真实 View/API 尚未接入，报告对象级内容权限与历史访问政策仍需在 Phase 6 继续完成。

因此当前仍然只使用虚拟数据，不接入真实学生生产数据。

后续开发默认严格按照 [`docs/DEVELOPMENT_PLAN.md`](docs/DEVELOPMENT_PLAN.md) 的顺序推进，并按照 [`docs/VERIFICATION_STANDARD.md`](docs/VERIFICATION_STANDARD.md) 进行功能 + 业务意义双重核验。
