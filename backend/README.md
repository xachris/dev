# 后端工程

当前后端采用 Django 5.2 LTS + PostgreSQL，保持模块化单体架构。

## 本地启动

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python backend/manage.py migrate
python backend/manage.py runserver
```

Windows 没有 `cp` 时可手动复制 `.env.example` 为 `.env`。

默认页面：`http://127.0.0.1:8000/`
健康检查：`http://127.0.0.1:8000/health/`

## 测试

需要可连接的 PostgreSQL：

```bash
DJANGO_SETTINGS_MODULE=config.settings.test python backend/manage.py test apps
```

开发阶段禁止使用真实学生数据。
