# 部署

本目录用于保存服务器和生产环境相关配置。

计划内容：

- Linux 服务器配置
- Nginx 反向代理
- HTTPS
- PostgreSQL 配置
- 环境变量与密钥管理
- 自动备份
- 恢复流程
- Staging / Production 部署说明
- 基础监控与日志

## 中国学校默认配置

- 应用默认语言：简体中文
- Django `LANGUAGE_CODE`：`zh-hans`
- 默认时区：`Asia/Shanghai`
- 正式环境域名示例：`portal.school.edu.cn` 或学校自有域名
- 正式生产前完成学校要求的安全、合规和数据治理评估

在 Milestone 1 使用虚拟数据稳定跑通之前，不进入正式生产部署。
