# 学校数字化平台

一个面向现代学校、以中国学校为核心使用场景、可由学校自主部署和控制的数字化运营平台。

项目不以复制传统 SIS 的功能清单为目标，而以“减少重复录入、减少等待、减少错误、提高自动化和业务质量”为核心。平台从统一身份、关系、权限、事件、状态、工作流和学生时间线出发，再逐步组合出学习报告、请假与出勤、课表、任务等具体业务能力。

> 当前首个完整业务闭环：**学习报告系统 V0.1**

## 核心产品原则

- **一个学生，一个永久学号，多种身份，不同视图。**
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
- [`docs/ROADMAP.md`](docs/ROADMAP.md)：平台级版本路线图
- [`docs/PROJECT_OVERVIEW.md`](docs/PROJECT_OVERVIEW.md)：项目定位与范围
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)：总体架构
- [`docs/DATA_MODEL.md`](docs/DATA_MODEL.md)：核心数据模型
- [`docs/PERMISSION_MODEL.md`](docs/PERMISSION_MODEL.md)：角色与权限模型
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
- Student ID
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

- `docs/`：产品哲学、开发计划、架构、数据模型、权限、安全和路线图
- `backend/`：Django 后端应用
- `tests/`：自动化测试和完整流程测试
- `deployment/`：服务器、反向代理、备份和部署配置
- `archive/`：本项目初始化前的旧仓库内容

## 当前开发阶段

当前正式进入：

> **Phase 1：工程初始化**

后续开发默认严格按照 [`docs/DEVELOPMENT_PLAN.md`](docs/DEVELOPMENT_PLAN.md) 的顺序推进。除非发现基础架构存在重大问题，不因临时需求跳过底层阶段或提前堆叠新业务模块。
