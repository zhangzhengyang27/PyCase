#!/usr/bin/env bash
# 本地门禁分层运行器（2026-10 体检「高效」项）：命令必须逐条读完输出判定，管道吞退出码是本项目反复踩过的坑，
# 本脚本用 set -euo pipefail 保证任一门禁红即整体红。
#
# 用法：
#   scripts/gate.sh fast   日常迭代档：ruff + 前端类型/lint/格式 + vitest + 9 份 mjs 纯函数测试
#   scripts/gate.sh full   推送/发版前档：fast + mypy + 5 个数据门禁 + pytest（对齐 CI python/frontend 两 job）
#
# 不在本脚本内：npm run smoke（需 electron-vite 构建 + 干净环境，跑前 pkill Electron 孤儿）、
# 打包冒烟——按 ROADMAP 口径在推送/打 tag 前单独跑。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ELECTRON="$ROOT/electron-prototype/electron"
PY="$ROOT/.venv/bin/python"

step() { printf '\n▶ %s\n' "$*"; }

fast() {
  step "ruff（app scripts tests sidecar）"
  (cd "$ROOT" && .venv/bin/ruff check app scripts tests electron-prototype/sidecar)

  step "typecheck（tsc + vue-tsc）"
  (cd "$ELECTRON" && npm run typecheck)

  step "lint（eslint + stylelint）"
  (cd "$ELECTRON" && npm run lint)

  step "format:check（prettier）"
  (cd "$ELECTRON" && npm run format:check)

  step "vitest"
  (cd "$ELECTRON" && npm test)

  # mjs 纯函数测试汇总跑（CI 里逐条跑 9 份；不在 pytest/vitest 射程，本地曾因此漏跑）
  step "mjs 纯函数测试（tests/test_*.mjs）"
  (cd "$ROOT" && for t in tests/test_*.mjs; do echo "--- node $t"; node "$t"; done)
}

full() {
  fast

  step "mypy"
  (cd "$ROOT" && "$PY" -m mypy)

  step "对比度门禁"
  (cd "$ROOT" && "$PY" scripts/check_contrast.py)

  step "文档引用防漂移"
  (cd "$ROOT" && "$PY" scripts/check_doc_refs.py)

  step "派生数据门禁（facts / requirements）"
  (cd "$ROOT" && "$PY" -m app.facts_cli check && "$PY" -m app.facts_cli requirements --check)

  step "依赖锁一致性"
  (cd "$ROOT" && "$PY" scripts/check_requirements_lock.py)

  step "版本一致性"
  (cd "$ROOT" && "$PY" scripts/sync_version.py --check)

  step "pytest（本地口径，覆盖率门禁只在 CI）"
  (cd "$ROOT" && "$PY" -m pytest tests/ -q --tb=short)
}

case "${1:-}" in
  fast) fast ;;
  full) full ;;
  *)
    echo "用法: scripts/gate.sh fast|full" >&2
    exit 1
    ;;
esac

printf '\n✅ 门禁全部通过：%s\n' "${1}"
