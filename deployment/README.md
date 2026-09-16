# 部署

本目录用于保存服务器和生产环境相关配置。

长期计划包括：

- Linux 服务器配置；
- Nginx 反向代理；
- HTTPS；
- PostgreSQL；
- 环境变量与密钥管理；
- 自动备份与恢复；
- Staging / Production；
- 监控与日志。

## 当前 Pilot：Railway Staging

当前只部署**虚拟测试数据**，目的不是进入正式生产，而是让教师、班主任、学术管理员、学生和家长可以通过真实浏览器完整走通学习报告流程。

### Web 服务

仓库根目录 `Procfile`：

```text
web: bash deployment/start.sh
```

`deployment/start.sh` 在启动时执行：

1. PostgreSQL migrations；
2. `collectstatic`；
3. `DEMO_MODE=true` 时执行幂等 `seed_demo`；
4. 启动 Gunicorn。

### Railway 变量

Web 服务至少需要：

```text
DJANGO_SETTINGS_MODULE=config.settings.production
DJANGO_SECRET_KEY=<随机长密钥>
DEMO_MODE=true
DEMO_PASSWORD=<仅用于本次 Pilot 的演示密码>
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

Railway 会提供 `PORT` 与公开域名相关变量；Django 会自动读取 `RAILWAY_PUBLIC_DOMAIN` 加入允许域名和 CSRF trusted origin。

### PostgreSQL

Pilot Web 服务绑定独立 Railway PostgreSQL，不连接学校真实数据库，不导入真实学生资料。

### 健康检查

```text
GET /health/
```

预期：

```json
{"status":"ok","service":"school-platform"}
```

### Pilot 安全边界

- 仅虚拟学生数据；
- 不连接学校 Outlook；
- 不连接真实 AI API；
- 不导入真实家长邮箱、电话号码或出生日期；
- System Admin 默认没有教育内容读取权；
- Pilot 通过后仍需 Event / Audit / Notification、安全评估、备份恢复验证，才可讨论真实数据试点。

## 中国学校默认配置

- 应用默认语言：简体中文；
- Django `LANGUAGE_CODE`：`zh-hans`；
- 默认时区：`Asia/Shanghai`；
- 正式生产域名应使用学校或平台自有域名；
- 正式生产前完成学校要求的安全、合规和数据治理评估。

Railway Pilot 是功能与业务体验验证环境，不代表最终中国大陆生产部署方案。
