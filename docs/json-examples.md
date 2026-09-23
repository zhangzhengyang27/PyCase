# JSON 示例集数据源（全面改造）

> 状态：**已全面落地**。应用现在以 JSON 为**唯一数据源**，不再扫描 `topics/`、`tools/`、`projects/` 目录。

## 1. 目标

把示例代码与元数据统一收纳进 JSON 文件，作为**唯一可编辑真相源**；UI 加载 JSON、展示、运行、编辑，保存时回写 JSON。大型项目的真实 `.py` 文件可通过迁移脚本批量导入 JSON（原文件保留），不破坏既有工程。

## 2. 架构

- **唯一数据源**：`app/json_examples.py` 中的 `ExampleStore`。
  - `load()` 读取 `desktop-app/json_examples/*.json`，构建目录树（根 → 各集合根 `📦 集合名` → 示例）。
  - `search(query, root)` 在名称 / 说明 / 内联代码中检索。
  - `save_item(item, code)` 把编辑结果回写到对应 JSON 文件。
  - `categories` 暴露当前已加载示例涉及的分类。
- **物化（materialize）**：按示例在 JSON 中记录的原始目录 `dir`，把**整个原始目录树**（含同目录兄弟模块、数据文件、`requirements.txt`）拷贝到
  `desktop-app/.json_examples_cache/<dir_rel>/`，再在该重建的目录结构里用 JSON 代码覆盖运行目标文件。
  该缓存可随时由 JSON + 原始目录重建，不视为源码（已在 `.gitignore` 忽略）。
- **运行期 `sys.path`**：运行器会把示例所在目录及其**所有祖先目录**（向上到仓库根）加入 `PYTHONPATH`（`item.run_pythonpath`），
  以解析同目录兄弟模块与祖先包导入（例如 `common/` 目录内的示例 `import common` 时需其父目录在路径上）。
- **共享运行环境**：本项目是一个应用，示例是它的模块——全项目共用仓库根 `.venv` 一份环境，首次创建时按项目级 `requirements.txt`（`scripts/gen_shared_requirements.py` 汇总全部示例的依赖声明生成）一次装齐；示例声明的 `requirements` 物化为目录内 `requirements.txt`，仅在运行时兜底补装清单外的新依赖。
- **复用既有链路**：`item.path` 指向物化后的缓存文件，因此安全扫描、运行、评分、编辑、收藏、历史、学习路径、进度全部复用原有逻辑，无需为 JSON 单独实现。

## 3. JSON Schema

集合文件位于 `desktop-app/json_examples/*.json`：

```json
{
  "name": "基础示例集",
  "description": "可选的集合说明",
  "examples": [
    {
      "id": "hello_world",        // 必填，唯一，用作缓存目录名（仅允许字母数字 - _ .）
      "name": "hello.py",         // 展示文件名（物化后的文件名）
      "category": "topics",       // 分类（topics/tools/projects 或自定义）
      "dir": "topics/.../code",   // 可选，由迁移脚本生成：示例原始目录（相对仓库根），用于整体物化兄弟/数据
      "tags": ["基础", "入门"],    // 可选
      "description": "打印问候语",  // 可选
      "requirements": ["requests"],// 可选，装入共享 .venv 运行环境
      "code": "print('Hello')\n"   // 必填，示例代码
    }
  ]
}
```

## 4. 数据流

```
json_examples/*.json
        │  ExampleStore.load()
        ▼
   目录树（📦 集合 → 示例），每个示例 ExampleItem(source="json", path=.json_examples_cache/<id>/<name>.py)
        │
        ▼
  用户点击 → 编辑器加载物化文件 → 运行（统一使用共享 .venv）/ 安全扫描 / 评分
        │  编辑保存
        ▼
  写回 .json_examples_cache/<id>/<name>.py ──► 回写 *.json（真相源）
```

## 5. 与旧版目录扫描对比

| 维度 | 旧版（目录扫描） | 全面 JSON 版 |
|---|---|---|
| 代码位置 | 磁盘真实 `.py`（topics/tools/projects） | JSON 内联 `code`，物化为缓存 `.py` |
| 加载 | `ExampleIndexer` 扫描目录 | `ExampleStore.load()` 读 JSON |
| 运行 | 直接运行文件 | 物化后运行（统一使用共享 `.venv`，requirements 按需装入） |
| 编辑保存 | 写回原文件 | 回写 JSON + 更新缓存 |
| 搜索 | `indexer.search` | `ExampleStore.search` |
| 收藏/历史/进度标识 | 真实文件路径 | 稳定的缓存文件路径（由 `id` 决定） |

## 6. 迁移现有示例

使用迁移脚本把目录中的真实 `.py` 批量导入 JSON（**原文件保留**）：

```bash
# 自动查找仓库根并预览
python scripts/migrate_to_json.py --dry-run

# 实际生成 desktop-app/json_examples/migrated.json
python scripts/migrate_to_json.py

# 指定来源与输出
python scripts/migrate_to_json.py --source /path/to/repo --output my_examples.json

# 自动猜测缺失的第三方依赖，并用 pip install --dry-run 校验包名合法性后写入 JSON
python scripts/migrate_to_json.py --validate-reqs
```

脚本会自动提取分类、标签（基于目录层级与导入库）、说明（README 首行）与依赖（同目录 `requirements.txt`），生成可直接加载的 JSON 集合。

- **依赖自动补全（`--validate-reqs`）**：脚本会扫描每个示例的 `import`，排除标准库、已安装包与仓库本地模块（靠 `run_pythonpath` 解析），把剩余顶层导入按 `import 名 → PyPI 包名` 映射（见 `IMPORT_TO_PKG`）猜测为第三方依赖并合并进该示例的 `requirements`；加 `--validate-reqs` 时会用 `pip install --dry-run` 校验包名是否在 PyPI 存在，丢弃非法包名（如源码里的无效导入 `C01`/`autotest` 等）。物化时同一目录的多个示例会合并各自依赖到同一个 `requirements.txt`。
- 注意：自动补全只解决「缺依赖且有合法包名」这一类；包名巧合存在但并非所需、或需要系统级库（如 `psycopg2`/`opencv`/`tesseract`）的情况仍可能安装后运行失败。

## 7. 用户集合（user_examples/，示例库与应用解耦）

除内置集合外，应用支持导入**用户自己的示例目录**：

- 存放位置：打包版为 `userData/user_examples/*.json`（可写、随应用数据存续），开发模式为仓库根
  `user_examples/`（已 gitignore）。`ExampleStore` 加载时与内置库并存，集合以独立 `📦` 节点出现。
- 导入入口：顶栏「导入示例目录」三步向导（sidecar RPC `scan_import_source` 预览 →
  `import_examples` 写入 → 索引即时重建）；核心逻辑在 `app/importer.py`（与
  `scripts/migrate_to_json.py` 共用单一实现）。
- 导入行为：每条 spec **不写 `dir` 字段**（用户目录无稳定仓库根，走单文件物化），`category='user'`；
  id 对内置库与既有用户集合去重（冲突自动 `_2/_3` 后缀）；依赖由 `IMPORT_TO_PKG` 映射自动猜测。
- 删除：仅用户集合示例可删（详情页删除按钮 / RPC `delete_example`），原子写回集合 JSON
  并清理该示例的物化缓存；内置集合受保护。
- **已知限制**：导入示例的同目录兄弟模块与数据文件暂不解析（单文件物化）——需要目录级
  依赖的工程请使用 `scripts/migrate_to_json.py` 迁移（生成 `dir` 字段以整体物化）。

## 8. 局限

- 缓存目录 `.json_examples_cache/` 不应纳入版本控制（已忽略）。
- 收藏/历史的标识是缓存文件路径，依赖 `id` 稳定；换机器或清理缓存后重新物化仍可匹配（同机器同应用目录）。
- 当前集合的编辑通过回写 JSON 完成，尚不支持「从应用内新建示例并写 JSON」的可视化向导（可后续补充）。
- **部分示例天生无法运行**（与 JSON 化无关，源自原始工程本身），排查发现的主要类别：
  1. **缺少第三方依赖且无 `requirements.txt`**：如 `django/vega/xlrd/pytesseract/pptx` 等，其所在目录未声明依赖，未触发 venv 安装。已通过迁移脚本 `--validate-reqs` 自动猜测并补全大部分（原统计 86 个，补全后仍有少量因包名非法/需系统库而失败）。
  2. **需以模块方式运行 / 包名含连字符**：如 `import common` 要求父目录在 `sys.path` 上（已通过 `run_pythonpath` 修复大部分），但若文件名含连字符（如 `yaml-config.py` 被 `import yaml_config`）则 Python 语法上无法导入，属原始代码缺陷。
  3. **依赖外部资源**：数据库、网络服务、付费 API、特定文件路径等运行环境相关失败。
  4. **交互输入 `input()`**：会一直阻塞到超时（共约 56 个）。
  5. **示例本身是库/模块而非可运入口**：无 `if __name__ == "__main__"`，运行即无输出或报 `NameError`（共约 905 个，多为被导入的工具模块）。
- 对于类别 1，运行迁移脚本时加 `--validate-reqs` 即可自动补全；类别 2/3/4/5 需针对具体示例修正源码，无法靠物化策略统一解决。

## 数据变更生效时机

sidecar 进程启动时一次性加载 `json_examples/*.json` 与 `user_examples/*.json` 并缓存
（质量分、安全高危、可运行性判定均惰性计算后缓存）。**外部直接改 JSON 后须重启应用**
（或在应用内点「重新加载」触发 list_examples 重读内存缓存——注意这只重读启动时快照，
不改盘的编辑无效）。应用内编辑保存走 `save_example` 回写 JSON 并同步失效
质量分/高危/可运行性缓存，无需重启；**导入与删除用户集合会自动重建索引**，列表即时生效。

## 可运行性判定（run_status，派生数据不落盘）

每个示例向前端暴露一个 `run_status` 字段（`app/run_status.py`），与质量分、
高危判定同为**惰性计算的派生数据**，不写入 JSON——JSON 只存人写的元数据。

| 状态 | 含义 | 卡片徽章 |
|---|---|---|
| `runnable` | 静态检查全部通过（**推定**可运行，不保证运行结果符合预期） | 不显示 |
| `missing_deps` | 第三方 import 在共享 .venv 中不存在，运行必 ImportError | 显示「缺依赖」 |
| `empty` | 去除 docstring 后无有效语句（或有效代码 <30 字符） | 显示「空壳」 |
| `broken` | 语法错误，无法 ast.parse | 显示「语法损坏」 |
| `risky` | 含 HIGH 风险操作（与高危徽章同源判定），可运行但需确认 | 由高危徽章承担 |

判定优先级：`broken > empty > missing_deps > risky > runnable`（能不能跑优先于风险提示）。
缺依赖判定基于对共享 .venv 解释器一次性枚举的模块索引（`ModuleIndex`），
索引不可用时跳过该维度（宁可漏报不误报）。sidecar 启动预热线程在 venv 就绪后
批量预热全量状态；应用内编辑保存后该示例状态即时重算。

全量静态判定与抽样实跑的交叉校准基线见 [run-status-baseline.md](run-status-baseline.md)。
