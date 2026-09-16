# 学校数字化平台

一个以中国学校为核心使用场景、可由学校自主部署和控制的数字化平台。项目优先解决学生身份、家校访问、学习报告、权限、审核、发布、通知和审计等基础问题，并为后续 AI 辅助学校运营预留接口。

> 当前第一阶段产品：**学习报告系统 V0.1**

## 核心业务流程

1. 学科教师填写学生学习反馈。
2. 教师提交本学科评价。
3. 系统执行自动校验。
4. 班主任查看学生整体报告。
5. 班主任审核、退回或批准。
6. 学校统一发布报告。
7. 学生与家长根据不同权限查看各自可见内容。
8. 外部邮箱只用于“报告已发布”等通知，不承载正式学习报告正文。

## 核心产品原则

- **一个学生，一个永久学号，多种身份，不同视图。**
- **报告留在学校系统内，外部只发送通知。**
- **不产生无用途的“死数据”。**
- **一份数据，只产生一次，多处复用。**
- **正常状态自动推导，人只处理异常。**
- **系统不是记录系统，而是行动系统。**
- 学生学号是稳定身份主键，邮箱、登录方式和供应商可以变化。
- 学生、家长、教师和管理员权限必须分离。
- 家长与学生可以访问同一个学生空间，但看到的内容不同。
- AI 只作为辅助能力，核心业务流程不能依赖 AI 才能运行。
- 收件人、学生关系和权限必须来自结构化学校数据，不能由 AI 猜测。
- 优先采用学校可控、可迁移、低供应商锁定的技术架构。
- 正式数据必须可审计、可备份、可恢复、可追踪。

完整设计原则见：[`docs/PRODUCT_PHILOSOPHY.md`](docs/PRODUCT_PHILOSOPHY.md)。后续新增功能、数据字段、工作流和 AI 能力时，应优先以该文档作为产品和架构判断依据。

## 核心设计文档

- [`docs/PRODUCT_PHILOSOPHY.md`](docs/PRODUCT_PHILOSOPHY.md)：产品设计哲学与新增功能检查清单
- [`docs/PROJECT_OVERVIEW.md`](docs/PROJECT_OVERVIEW.md)：项目定位与范围
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)：总体架构
- [`docs/DATA_MODEL.md`](docs/DATA_MODEL.md)：核心数据模型
- [`docs/PERMISSION_MODEL.md`](docs/PERMISSION_MODEL.md)：角色与权限模型
- [`docs/SECURITY_BASELINE.md`](docs/SECURITY_BASELINE.md)：安全基线
- [`docs/LOCALIZATION.md`](docs/LOCALIZATION.md)：中文产品与代码语言规范
- [`docs/ROADMAP.md`](docs/ROADMAP.md)：开发路线图

## 默认使用环境

- 核心用户：中国境内学校
- 默认产品语言：简体中文（`zh-CN`）
- 默认时区：`Asia/Shanghai`
- 用户界面、通知、业务术语和操作说明：中文优先
- 代码、数据库字段、API、枚举值：英文优先，便于开发维护

## 初始角色

- 学生（Student）
- 家长 / 监护人（Guardian）
- 学科教师（Subject Teacher）
- 班主任（Homeroom Teacher）
- 学术管理员（Academic Admin）
- 系统管理员（System Admin）

## Milestone 1：跑通最小闭环

仅使用虚拟测试数据完成：

`教师填写 -> 提交 -> 班主任审核 -> 批准 -> 发布 -> 家长查看 / 学生查看`

Milestone 1 暂不接入真实学生数据、正式 Outlook 邮件、本地或外部 AI，也不部署正式生产环境。

## 仓库结构

- `docs/`：项目、架构、数据模型、权限、安全和路线图文档
- `backend/`：Django 后端应用
- `tests/`：自动化测试和完整流程测试
- `deployment/`：服务器、反向代理、备份和部署配置
- `archive/`：本项目初始化前的旧仓库内容

## 当前状态

项目已完成基础规范初始化，下一步进入 Django 工程和核心数据模型开发。
