# 开发日志索引

从 Phase 3 起，开发日志按阶段拆分为独立文件，避免单个 `WORKLOG.md` 无限膨胀。

每个阶段日志必须记录：

1. 做了什么；
2. 对业务可能产生的影响；
3. 带来的收益；
4. 遗留风险；
5. 功能核验结论；
6. 业务意义核验结论；
7. 是否允许进入下一阶段，以及理由。

## 历史日志

- Phase 1–2：[`../WORKLOG.md`](../WORKLOG.md)
- Phase 3：[`PHASE_03_IDENTITY_RELATIONS.md`](PHASE_03_IDENTITY_RELATIONS.md)
- Phase 4：[`PHASE_04_ACADEMIC_STRUCTURE.md`](PHASE_04_ACADEMIC_STRUCTURE.md)
- Phase 5：[`PHASE_05_CONTEXTUAL_PERMISSIONS.md`](PHASE_05_CONTEXTUAL_PERMISSIONS.md)
- Phase 6：[`PHASE_06_REPORT_WORKFLOW.md`](PHASE_06_REPORT_WORKFLOW.md)
- Pilot UI / Phase 7–9 可测试切片：[`PILOT_UI_ONLINE_STAGING.md`](PILOT_UI_ONLINE_STAGING.md)
- 首次真实线上 Pilot Staging 部署：[`PILOT_STAGING_DEPLOYMENT.md`](PILOT_STAGING_DEPLOYMENT.md)
- Phase 7 教师高吞吐录入：[`PHASE_07_TEACHER_THROUGHPUT.md`](PHASE_07_TEACHER_THROUGHPUT.md)
- 架构稳定性治理与前端决策固化：[`ARCHITECTURE_GOVERNANCE_2026-09-17.md`](ARCHITECTURE_GOVERNANCE_2026-09-17.md)

后续每一个可独立验收的 Phase 都应新增一份日志，而不是覆盖历史判断。
