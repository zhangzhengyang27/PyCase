# 可运行性基线报告

> **存档**：可运行性统计快照（口径已由 app/run_status.py + 烘焙事实索引取代）。当前事实以 [docs/redesign-data-contract.md（§3 派生事实）与 tests/test_guard_*.py] 为准；本文件保留作历史记录，不再更新。

> 由 `scripts/run_status_report.py` 生成：静态判定全量 + 抽样实跑校准。
> 静态可运行率是「推定」（代码体检），实跑通过率是「真跑得通」的度量，两者互补。

- 生成时间：2026-09-11 02:23
- 示例总数：1187（解释器 3.14.6）
- 实跑抽样：ratio=0.1（seed=42），试跑 118 个，超时 8.0s

> ⚠️ **本基线已过期**：当前示例总量为 **1496**（2026-09-24 复核），示例集合此后又有增删，
> 下表的绝对值不再反映现状，仅作当时的校准口径参考。重新生成：
> `python scripts/run_status_report.py`（会抽取约 10% 示例真实运行，
> 含 pygame / turtle 等会弹出窗口的示例，请在无干扰环境下执行）。

## 静态判定（全量）

| 状态 | 数量 | 占比 |
|---|---|---|
| 可运行（runnable） | 1149 | 96.8% |
| 缺依赖（missing_deps） | 10 | 0.8% |
| 空壳（empty） | 11 | 0.9% |
| 语法损坏（broken） | 0 | 0.0% |
| 高危（risky） | 17 | 1.4% |

**静态可运行率：96.8%**

## 抽样实跑（与 regression_smoke 同管线同口径）

| 状态 | 数量 | 占比 |
|---|---|---|
| pass | 61 | 51.7% |
| missing_dependency | 10 | 8.5% |
| timeout | 30 | 25.4% |
| failed | 17 | 14.4% |

**实跑通过率：51.7%**（2026-09-09 首轮基线为 66.7%，同 ratio/seed 口径）

## 静态预测 × 实跑交叉校准

- 缺依赖预测命中：3/3（静态 missing_deps 且实跑 missing_dependency）

### 静态盲区（推定可运行但实跑失败，前 15 条）

- farm-scene.py → 实跑 timeout：超过 8.0s 未退出
- 09-xpath-basics.py → 实跑 timeout：超过 8.0s 未退出
- object-parent-child.py → 实跑 failed：AttributeError: 'Parent' object has no attribute 'play_pingp
- task-1001.py → 实跑 timeout：超过 8.0s 未退出
- set-edit.py → 实跑 failed：KeyError: 'flask'
- 04-network-info.py → 实跑 failed：psutil.AccessDenied: (pid=42919)
- use-config-file.py → 实跑 failed：configparser.NoSectionError: No section: 'work'
- 02-multiprocessing-case.py → 实跑 timeout：超过 8.0s 未退出
- 15.py → 实跑 timeout：超过 8.0s 未退出
- calculator.py → 实跑 failed：EOFError: EOF when reading a line
- UrlManager.py → 实跑 missing_dependency：ModuleNotFoundError: No module named 'flask._compat'
- 03-interceptor-error-handler.py → 实跑 timeout：超过 8.0s 未退出
- try-custom.py → 实跑 failed：NameLimitError: dewei不可以被填写
- orbit-flowers.py → 实跑 timeout：超过 8.0s 未退出
- gui3.py → 实跑 timeout：超过 8.0s 未退出
