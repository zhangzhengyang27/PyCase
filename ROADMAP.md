# ROADMAP

> **当前进度以 [docs/redesign-plan.md](docs/redesign-plan.md) 为准**——2026-09 起本项目按
> A（体验）× B（工程）双轨重设计推进，护栏 G1–G10、验收标准与逐批落地记录都在那份计划里。
> 本文件只保留两件事：里程碑索引与发版对账的口径。

## 1. 里程碑

| 里程碑 | 内容 | 状态 |
|---|---|---|
| M0–B1 | 审计取证、重设计蓝图、护栏 G1–G6、数据契约 v2 设计 | ✅ 2026-09-29 |
| A1–A5.5 | 视觉基线、壳与导航、画廊/工具箱、运行器/详情、全局层、帮助与首启 | ✅ 2026-09-29 |
| B2 | Python/sidecar 按契约 v2 重写：数据迁移、烘焙事实索引、G1–G8 全绿 | ✅ 2026-09-29 |
| B3 | 渲染层与壳重写：单一来源、类型化客户端、store 分域、双平台打包 | ✅ 2026-09-29 |
| A6 | 产品化补课：失败恢复、可恢复编辑、缓存入口、外发同意复核 | ✅ 2026-09-30 |
| M6 | 工程门禁、性能实测、双平台安装冒烟、文档 reconcile、v1.0.0 | 进行中 |

## 2. 发版对账口径

- 版本号单一来源 = 仓库根 `VERSION`，`scripts/sync_version.py` 同步到
  `package.json` / `pyproject.toml` / `app/_version.py`（CI 有 `--check` 门禁）。
- tag 只在**验收全绿后**创建，命名 `v<主>.<次>.<修订>`；创建前须跑：
  `pytest`（含覆盖率门禁）、`npm run lint / format:check / test / typecheck`、`npm run smoke`、
  `SMOKE_TEST=1 E2E_TEST=1 npx electron .`、`npm run dist:mac`（本机）与 CI `packaging` 矩阵（双平台）。
- 发布说明与签名现状见 [docs/release.md](docs/release.md)。

## 3. 历史交付（归档）

v0.5–v0.10 的逐版内容（信息架构重设计、示例库与应用解耦、导入向导、工具箱分区等）保留在
git 历史与 `docs/` 的归档文档中；其中 v0.10 之后的变化已被本仓库的双轨重设计覆盖，不再逐条回填。
