# Pilot Staging 部署日志：首次真实线上运行

日期：2026-09-17

## 1. 做了什么

将已经通过 110 个自动化测试的 Pilot UI 从 GitHub `main` 部署到 Railway 独立测试项目 `school-platform-pilot`。

线上环境包含：

- 独立 Railway PostgreSQL；
- Django Web 服务；
- Gunicorn；
- WhiteNoise 静态文件；
- production settings；
- `DEMO_MODE=true`；
- 幂等 `seed_demo` 虚拟演示数据；
- `/health/` 健康检查；
- Railway 公开测试域名。

当前公开域名：

`https://school-platform-web-production.up.railway.app`

Railway 环境本身名为 `production`，但本项目业务定义中它仍然只是 **Pilot Staging**，只允许虚拟数据。

## 2. 第一次部署失败与修复

第一次 Web 部署中，应用本体已经成功启动：

- migrations 成功；
- collectstatic 成功；
- `seed_demo` 成功；
- Gunicorn 成功启动。

但 Railway 健康检查使用 Host `healthcheck.railway.app` 请求 `/health/`，Django 因该 Host 不在 `ALLOWED_HOSTS` 中返回 HTTP 400，导致 Railway 判定部署失败。

修复：

- 将 `healthcheck.railway.app` 加入 Pilot Staging 的 `DJANGO_ALLOWED_HOSTS`；
- 同时保留 Railway 公共域名和本地开发 Host；
- 将服务端口统一为 8000，使 Gunicorn 与 Railway service domain 的 target port 保持一致。

修复后最新部署状态：

- PostgreSQL：`SUCCESS`；
- Web：`SUCCESS`；
- Gunicorn：监听 `0.0.0.0:8000`；
- `/health/`：HTTP 200；
- Demo 数据：成功初始化。

## 3. 对业务的影响

项目第一次从“仓库中存在可运行 UI”进入“用户可以通过公网浏览器真实登录和操作”的阶段。

现在可以由真人验证：

- 教师填写、保存、提交是否顺手；
- 班主任审核、单科退回、批准是否符合真实工作习惯；
- Academic Admin 发布是否清楚；
- 学生 / 家长看到的字段是否符合预期；
- 页面布局、信息密度、点击次数是否合理。

这类问题无法只靠单元测试判断，因此线上 Pilot 是进入下一轮产品设计所必需的业务验证。

## 4. 带来的好处

1. **真实浏览器验证成为可能**：后续不再只讨论模型、权限和状态机，可以直接基于用户操作反馈调整。
2. **部署链真实验证**：GitHub → Railway build → PostgreSQL migration → static → demo seed → Gunicorn → healthcheck 已完整跑通。
3. **问题暴露更早**：首次部署立即暴露了 Railway healthcheck Host 与端口配置问题，在进入真实数据阶段前解决。
4. **保持低风险**：当前全部为虚拟数据，即使 Pilot 被公开访问也不包含真实学生或家长信息。

## 5. 遗留风险

1. 当前只有 1 名虚拟学生和 2 门学科，尚未验证 20–30 人班级的连续录入效率；
2. 当前演示账号使用共享 Demo 密码，仅允许纯虚拟 Pilot，真实数据环境必须取消；
3. Event / Student Timeline / Audit / Notification Outbox 尚未完成，因此仍禁止真实学生数据；
4. 尚未验证备份恢复和生产级监控；
5. Railway 只是 Pilot Staging 承载平台，不代表中国大陆正式生产部署方案；
6. 真人测试可能暴露 UI / UX、状态提示、连续录入、自动保存等自动化测试无法识别的问题。

## 6. 功能核验

- Railway PostgreSQL：PASS；
- Web build：PASS；
- migrations：PASS；
- static collection：PASS；
- demo seed：PASS；
- Gunicorn：PASS；
- Railway healthcheck `/health/`：PASS，HTTP 200；
- Railway 最新 Web deployment：PASS / SUCCESS。

### 功能核验结论

**PASS**

## 7. 业务意义核验

线上 Pilot 的业务价值不是“终于有一个网址”，而是把后续判断从架构猜测转成真实用户行为证据。

下一阶段最重要的数据将是：

- 完成一次教师填写需要多少步骤；
- 哪些页面信息不足或过载；
- 班主任真正想先看什么异常；
- 用户在哪些位置需要来回切页；
- 哪些动作应该自动完成；
- 哪些字段实际上无人使用。

### 业务意义核验结论

**PASS WITH RISK**

允许进入真人 Pilot，但继续只使用虚拟数据。
