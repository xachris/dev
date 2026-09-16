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

## 接手与架构变更规则

后续 AI 模型、开发者或供应商接手前，应先阅读 [`AGENTS.md`](AGENTS.md) 和 [`docs/decisions/README.md`](docs/decisions/README.md)。

已经接受的架构决策可以被未来新决策替代，但**不得在没有记录原因、现实变化、业务收益、迁移成本和验证方案的情况下被静默推翻**。

当前前端默认路线为 **Django Templates + CSS + 少量 JavaScript**。是否引入 React / Next.js 由真实交互复杂度和 Pilot 证据决定，不以框架流行度决定。详细原因、重新评估条件和迁移规则见 [`ADR-001：前端架构策略`](docs/decisions/ADR-001-frontend-strategy.md)。

## 核心设计文档

- [`AGENTS.md`](AGENTS.md)：后续 AI / 开发者接手顺序、架构变更纪律、业务与核验约束
- [`docs/PRODUCT_PHILOSOPHY.md`](docs/PRODUCT_PHILOSOPHY.md)：产品设计哲学与新增功能检查清单
- [`docs/decisions/README.md`](docs/decisions/README.md)：Architecture Decision Records 索引与变更规则
- [`docs/decisions/ADR-001-frontend-strategy.md`](docs/decisions/ADR-001-frontend-strategy.md)：当前前端路线、暂不全面 React 化的原因及未来触发条件
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

当前已经使用**纯虚拟测试数据**实现：

`教师填写 -> 提交 -> 班主任审核 -> 批准 -> 发布 -> 家长查看 / 学生查看`

当前闭环已真实验证：

- School / Tenant；
- Student Identity / 学校学号；
- 学生 / 家长 / 教师关系；
- 任课和班主任关系；
- RBAC + 对象级内容权限；
- 报告状态机；
- 单学科退回 / 重提；
- 审核与发布；
- 学生 / 家长不同字段视图；
- 真实登录、表单和浏览器页面。

仍未接入真实学生数据、正式 Outlook 邮件或正式生产 AI。

## 仓库结构

- `docs/`：产品哲学、开发计划、架构决策、架构、数据模型、权限、安全、开发日志和路线图
- `backend/`：Django 后端应用与 Pilot UI
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
- Phase 6：学习报告模型、状态机、学科快照与对象级内容权限

当前正在完成：

> **Phase 7–9 的线上 Pilot UI 切片：把已验证的业务核心做成真实浏览器可测试系统。**

Pilot 已包含：

- 学科教师工作台与评价页；
- 班主任审核 / 单学科退回 / 批准；
- Academic Admin 发布；
- 学生 Portal；
- 家长 Portal；
- System Admin 默认无教育内容视图；
- 幂等虚拟演示数据；
- Railway / 通用 PaaS 部署启动方式。

最新 Pilot 自动化核验：**110 个测试通过**，并额外通过 production settings 的静态文件收集和重复演示数据初始化检查。

业务意义核验中还专门发现并修复了“班主任可能提前看到教师草稿”的页面级权限问题，因此当前班主任页面只消费服务器端内容 Policy 返回的字段。

需要强调：这个 Pilot 证明了**流程能真实使用**，还没有证明“一个老师处理 20–30 名学生时效率已经最优”。后续真人测试要重点测完成时间、点击次数、连续录入和自动保存需求。

因此当前继续只使用虚拟数据，不接入真实学生生产数据。

后续开发默认严格按照 [`docs/DEVELOPMENT_PLAN.md`](docs/DEVELOPMENT_PLAN.md) 的顺序推进，并按照 [`docs/VERIFICATION_STANDARD.md`](docs/VERIFICATION_STANDARD.md) 进行功能 + 业务意义双重核验。
