# 深邃层次 UI 视觉重构 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 按 `docs/superpowers/specs/2026-09-12-ui-visual-overhaul-design.md`，在不改动任何功能逻辑的前提下完成渲染层视觉重构：令牌升级、卡片「深邃层次」、分区色相体系、面包屑结果条、详情页分段控件与终端容器、入场动效。

**Architecture:** 全部改动集中在 `electron-prototype/electron/src/renderer`。做法是三层递进：① `theme.css` 令牌值 + `main.css` 公共表面类（`.surface-card` / `.hue-chip` / `.btn-primary-deep` 等，放 `@layer components` 使 Tailwind 工具类仍可覆盖）；② 纯数据色相表（`category-meta.ts`、`overview.ts`）；③ 各组件按新语言改类名与少量模板。每个 Task 独立可验证、独立提交。

**Tech Stack:** Vue 3 `<script setup>` + Tailwind 4（CSS-first @theme）+ TypeScript。仓库无单测框架——验证命令为 `npm run typecheck` / `npm run build` / `npm run smoke` / `E2E_TEST=1`，外加 Task 2 的对比度 node 脚本。

**注意事项（执行者必读）：**

- 所有命令在 `cd /Users/xiaoye/Desktop/20260803/Python/desktop-app/electron-prototype/electron` 下执行。
- `theme.css` 是**新旧两个渲染层共享**的令牌层，本计划只改值与追加内容，不改任何已有令牌名（旧渲染层页面会同步换色，这是预期行为）。
- 新公共类必须写在 `@layer components { }` 内（`theme.css` 已声明层顺序 `theme, base, components, utilities`），否则未分层 CSS 会压过 Tailwind 工具类，导致 `border-accent` 等覆盖失效。
- `prefers-reduced-motion` 全局降级已存在于 `main.css`，新增动画无需单独处理。
- 提交信息用仓库惯例：conventional commits + 中文描述。**不要**提交 `scripts/gen_sciviz_examples.py`（用户自己的工作区改动）与 `.gitignore`。

---

## File Structure

| 文件 | 动作 | 职责 |
| --- | --- | --- |
| `src/renderer/src/theme.css` | 修改 | 令牌值更新 + 卡片变量 + `--radius-card` + 两个入场动画 |
| `src/renderer/main.css` | 修改 | `@layer components` 公共表面类（8 个类） |
| `src/renderer/src/category-meta.ts` | 修改 | 分类色相 `hue` 字段替换 `cls` |
| `src/renderer/src/overview.ts` | 修改 | 追加 `SECTION_HUES` 常量（纯数据） |
| `src/renderer/components/ExampleCard.vue` | 修改 | `.surface-card` + hue 徽章 + hover 抬升 + 入场 stagger |
| `src/renderer/components/ExampleListItem.vue` | 修改 | 同上（行式） |
| `src/renderer/components/GalleryOverview.vue` | 修改 | hero 极光 + 统计 chips + 区头色相徽章 |
| `src/renderer/App.vue` | 修改 | 导航激活胶囊 `.surface-raised` |
| `src/renderer/components/BrowseToolbar.vue` | 修改 | 双行：面包屑结果条 + 芯片工具条 |
| `src/renderer/components/GalleryView.vue` | 修改 | 视图切换动画类 + 传 `enter-index` |
| `src/renderer/components/ToolboxView.vue` | 修改 | 区头色相徽章 + 传 `enter-index` |
| `src/renderer/components/FilterSidebar.vue` | 修改 | 「筛选」小标与组头字距精修 |
| `src/renderer/components/base/SkeletonCard.vue` | 修改 | 对齐新卡片圆角/底色 |
| `src/renderer/components/DetailPage.vue` | 修改 | 路径副标题 + hue 徽章 + 分段控件 |
| `src/renderer/components/OutputPanel.vue` | 修改 | 终端容器（内嵌圆角边框） |
| `src/renderer/components/base/BaseButton.vue` | 修改 | primary → `.btn-primary-deep` |
| `src/renderer/components/base/AppModal.vue` | 修改 | 面板顶边高光 |
| `src/renderer/components/CommandPalette.vue` | 修改 | 面板顶边高光 |

---

### Task 1: 令牌层与公共表面类

**Files:**
- Modify: `src/renderer/src/theme.css`
- Modify: `src/renderer/main.css`

- [ ] **Step 1: 更新 `theme.css` 的 `:root` 表面令牌值**

在 `:root` 中做如下值替换（只动值，不动令牌名与注释结构）：

```css
  --bg-marketing: #0a0b0d;
  --bg-panel: #0e0f12;
  --bg-level3: #15171c;
  --bg-hover: rgba(255, 255, 255, 0.05);
  --bg-inset: #08090a;
```

- [ ] **Step 2: 在 `:root` 追加卡片变量组（放在「12. 状态底色」之后）**

```css
  /* 13. 卡片「深邃层次」（.surface-card 消费；浅色主题在 [data-theme] 覆盖） */
  --card-grad-top: #1c1e26;
  --card-grad-bottom: #16181f;
  --card-highlight: rgba(255, 255, 255, 0.11);
  --card-highlight-hover: rgba(255, 255, 255, 0.18);
  --shadow-card: 0 1px 2px rgba(0, 0, 0, 0.25);
  --shadow-card-hover: 0 6px 18px rgba(0, 0, 0, 0.4);

  /* 14. 卡片圆角（卡片 9px，控件 5px 不变） */
  --radius-card: 9px;
```

- [ ] **Step 3: 在 `theme.css` 的 `[data-theme="light"]` 块追加覆盖**

```css
  --card-highlight: rgba(0, 0, 0, 0.06);
  --card-highlight-hover: rgba(0, 0, 0, 0.1);
  --shadow-card: 0 2px 8px rgba(24, 28, 34, 0.06);
  --shadow-card-hover: 0 6px 18px rgba(24, 28, 34, 0.1);
```

- [ ] **Step 4: 在 `@theme` 块追加圆角映射与两个入场动画（放在 `--animate-indeterminate` 之后）**

```css
  /* 卡片圆角（rounded-card） */
  --radius-card: 9px;

  /* 卡片/列表行入场（stagger 由消费方内联 animation-delay 控制，backwards 保证延迟期不可见） */
  --animate-card-in: card-in 240ms var(--ease-panel) backwards;
  @keyframes card-in {
    from {
      opacity: 0;
      transform: translateY(4px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  /* 视图切换（v-show 分支从 display:none 恢复时自动重放） */
  --animate-view-in: view-in 200ms var(--ease-panel);
  @keyframes view-in {
    from {
      opacity: 0;
      transform: translateY(4px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
```

- [ ] **Step 5: 在 `main.css` 末尾追加公共表面类（必须包在 `@layer components` 内）**

```css
/* ===== 深邃层次：公共表面类（specs §3；放 components 层让 utilities 可覆盖） ===== */
@layer components {
  /* 卡片：渐变表面 + 顶部受光高边 + hover 抬升。
     边框/圆角/阴影由本类全权负责，消费方不要再叠加 border/rounded/shadow 静态工具类 */
  .surface-card {
    background: linear-gradient(180deg, var(--card-grad-top), var(--card-grad-bottom));
    border: 1px solid var(--border-subtle);
    border-top-color: var(--card-highlight);
    border-radius: var(--radius-card);
    box-shadow: var(--shadow-card);
    transition:
      box-shadow 160ms var(--ease-standard),
      border-color 160ms var(--ease-standard),
      transform 160ms var(--ease-standard);
  }
  .surface-card:hover {
    transform: translateY(-1px);
    border-top-color: var(--card-highlight-hover);
    box-shadow: var(--shadow-card-hover);
  }
  [data-theme='light'] .surface-card {
    background: #ffffff;
    border-color: #e7e8ea;
    border-top-color: #e7e8ea;
  }

  /* 无 hover 抬升的凸起表面：导航激活胶囊 / 分段控件激活段 */
  .surface-raised {
    background: linear-gradient(180deg, #1e2030, #181a24);
    border: 1px solid rgba(133, 132, 255, 0.22);
    border-top-color: rgba(255, 255, 255, 0.14);
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.3);
  }
  [data-theme='light'] .surface-raised {
    background: #f3f4f5;
    border-color: #d0d6e0;
    border-top-color: #d0d6e0;
    box-shadow: 0 1px 2px rgba(24, 28, 34, 0.06);
  }

  /* 色相徽章：--hue 由消费方内联注入（specs §3.2 分类/分区色相体系） */
  .hue-chip {
    background: color-mix(in srgb, var(--hue) 14%, transparent);
    border: 1px solid color-mix(in srgb, var(--hue) 35%, transparent);
    color: color-mix(in srgb, var(--hue) 70%, white 30%);
  }
  [data-theme='light'] .hue-chip {
    color: color-mix(in srgb, var(--hue) 55%, black 45%);
  }

  /* 总览统计 chips（specs §3.6） */
  .stat-chip {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 2px 7px;
    border-radius: var(--radius-control);
    background: rgba(255, 255, 255, 0.045);
    border: 1px solid rgba(255, 255, 255, 0.07);
    font-size: var(--text-caption-size);
    color: var(--text-quaternary);
  }
  .stat-chip b {
    font-weight: 590;
    color: var(--text-secondary);
  }
  [data-theme='light'] .stat-chip {
    background: rgba(0, 0, 0, 0.035);
    border-color: rgba(0, 0, 0, 0.08);
  }
  .stat-chip-ok {
    background: color-mix(in srgb, var(--status-green) 10%, transparent);
    border-color: color-mix(in srgb, var(--status-green) 25%, transparent);
    color: var(--status-green);
  }
  .stat-chip-ok b {
    color: var(--status-green);
  }

  /* 主按钮「深邃层次」变体（BaseButton variant=primary 消费） */
  .btn-primary-deep {
    background: linear-gradient(180deg, #6a79e0, #5662c8);
    border: 1px solid rgba(255, 255, 255, 0.16);
    border-top-color: rgba(255, 255, 255, 0.3);
    color: #fff;
    box-shadow: 0 2px 8px rgba(94, 106, 210, 0.35);
  }
  .btn-primary-deep:hover {
    background: linear-gradient(180deg, #7484e8, #5e6ad2);
    box-shadow: 0 2px 10px rgba(94, 106, 210, 0.45);
  }
  [data-theme='light'] .btn-primary-deep {
    background: #4f51c0;
    border-color: #4f51c0;
    border-top-color: #5a5cd0;
    box-shadow: 0 2px 6px rgba(79, 81, 192, 0.25);
  }
  [data-theme='light'] .btn-primary-deep:hover {
    background: #4547b3;
    box-shadow: 0 2px 8px rgba(79, 81, 192, 0.32);
  }

  /* 顶边高光（弹窗/命令面板大面板，不改背景） */
  .edge-highlight-top {
    border-top-color: rgba(255, 255, 255, 0.14);
  }
  [data-theme='light'] .edge-highlight-top {
    border-top-color: rgba(0, 0, 0, 0.06);
  }

  /* 画廊总览 hero 极光（浅色降为 6%/3%） */
  .aurora-hero {
    background:
      radial-gradient(600px 130px at 18% 0%, rgba(94, 106, 210, 0.13), transparent 65%),
      radial-gradient(500px 120px at 85% -20%, rgba(133, 132, 255, 0.07), transparent 60%);
  }
  [data-theme='light'] .aurora-hero {
    background:
      radial-gradient(600px 130px at 18% 0%, rgba(94, 106, 210, 0.06), transparent 65%),
      radial-gradient(500px 120px at 85% -20%, rgba(94, 106, 210, 0.03), transparent 60%);
  }
}
```

- [ ] **Step 6: 验证编译**

Run: `npm run typecheck && npm run build`
Expected: 两条命令均 exit 0，无新增报错。

- [ ] **Step 7: Commit**

```bash
git add src/renderer/src/theme.css src/renderer/main.css
git commit -m "feat(ui): 深邃层次令牌层——表面压深/卡片渐变高光/公共表面类/入场动画"
```

---

### Task 2: 色相数据 + 对比度抽检

**Files:**
- Modify: `src/renderer/src/category-meta.ts`
- Modify: `src/renderer/src/overview.ts`

- [ ] **Step 1: 重写 `category-meta.ts` 的元数据表（`cls` → `hue`）**

```ts
// category-meta.ts：分类（topics/tools/projects/user）的展示元数据（卡片与详情页共用）
// 色相驱动：.hue-chip 类 + 内联 --hue 变量（specs §3.2）；accent-violet 留给 Monaco 语法色。
import { FileCode2, FolderUp, Package, Wrench, type LucideIcon } from 'lucide-vue-next'

export const CATEGORY_META: Record<string, { hue: string; icon: LucideIcon }> = {
  topics: { hue: '#5e6ad2', icon: FileCode2 },
  tools: { hue: '#2fa866', icon: Wrench },
  projects: { hue: '#d9a03d', icon: Package },
  // 用户导入的示例（导入向导产物）
  user: { hue: '#2fb8a6', icon: FolderUp }
}
```

- [ ] **Step 2: 在 `overview.ts` 的 `TAG_SECTIONS` 定义之后追加分区色相表**

```ts
/** 分区色相（specs §3.2）：区头图标徽章经 .hue-chip + 内联 --hue 消费；others 不配色相（中性灰） */
export const SECTION_HUES: Record<string, string> = {
  viz: '#5e6ad2',
  turtle: '#2fa866',
  games: '#9a6bf2',
  opencv: '#3d8fe0',
  images: '#e0566a',
  'tag:basics': '#64748b',
  'tag:advanced': '#d9a03d',
  'tag:crawling': '#e07840',
  'tag:webapp': '#38a8e0',
  'tag:office': '#8a7dd8',
  'tag:database': '#2fb8a6',
  'tag:testing': '#7fb846',
  'tag:algo': '#5f8dd9',
  projects: '#d471a8'
}
```

- [ ] **Step 3: 运行对比度抽检脚本（specs §8 第 2 条的机械校验）**

Run:

```bash
node -e '
const L=h=>{const c=[1,3,5].map(i=>parseInt(h.slice(i,i+2),16)/255).map(v=>v<=0.03928?v/12.92:Math.pow((v+0.055)/1.055,2.4));return 0.2126*c[0]+0.7152*c[1]+0.0722*c[2]};
const mix=(a,b,t)=>{const p=h=>[1,3,5].map(i=>parseInt(h.slice(i,i+2),16));const A=p(a),B=p(b);return "#"+A.map((v,i)=>Math.round(v+(B[i]-v)*t).toString(16).padStart(2,"0")).join("")};
const ratio=(f,b)=>{const a=L(f),c=L(b);return ((Math.max(a,c)+0.05)/(Math.min(a,c)+0.05)).toFixed(2)};
const card="#15171c";
let fail=0;
for (const hue of ["#5e6ad2","#e0566a","#64748b","#7fb846"]) {
  const dFg=mix(hue,"#ffffff",0.30), dBg=mix(card,hue,0.14);
  const lFg=mix(hue,"#000000",0.45), lBg=mix("#ffffff",hue,0.14);
  const rd=+ratio(dFg,dBg), rl=+ratio(lFg,lBg);
  if (rd<4.5||rl<4.5) fail++;
  console.log(hue,"dark",rd,"light",rl);
}
process.exit(fail?1:0);'
```

Expected: 8 个比值全部 ≥ 4.50，exit 0。若有行 < 4.5：把 `main.css` 中 `.hue-chip` 深色的白混比 `70%` 提到 `75%`、浅色的黑混比 `45%` 提到 `50%`，重跑直至通过（同步更新该文件注释）。

- [ ] **Step 4: 提交（注意：此时 `meta.cls` 消费方尚未改，typecheck 会报错——本 Task 只提交数据文件，组件消费在 Task 3/6 修复，因此本 Task 先跑 build 之外的语法检查即可）**

Run: `npx tsc --noEmit -p tsconfig.node.json`
Expected: exit 0（category-meta/overview 属 node 侧可编译范围之外则跳过，直接进入组件 Task，在 Task 3 完成后由全量 typecheck 兜底）。

```bash
git add src/renderer/src/category-meta.ts src/renderer/src/overview.ts
git commit -m "feat(ui): 分类/分区色相数据表——cls 语义类迁移为 hue 驱动"
```

---

### Task 3: 卡片与列表行换新语言

**Files:**
- Modify: `src/renderer/components/ExampleCard.vue`
- Modify: `src/renderer/components/ExampleListItem.vue`

- [ ] **Step 1: 改 `ExampleCard.vue` 脚本区**

props 增加 `enterIndex`，替换 `CARD_CLS` 与新增 `enterDelay`：

```ts
const props = defineProps<{ ex: VExample; selected?: boolean; faved?: boolean; enterIndex?: number }>()
```

```ts
// content-visibility：触底加载后 DOM 只增不减（可能上千张卡），屏外卡片跳过布局/绘制；
// contain-intrinsic-size 的 auto 让渲染过的卡片记住真实高度，滚动条不跳动。
// 表面语言（边框/圆角/阴影/hover 抬升）由 .surface-card 全权负责（specs §3.1）
const CARD_CLS =
  'surface-card group cursor-pointer animate-card-in flex flex-col text-left w-full [content-visibility:auto] [contain-intrinsic-size:auto_170px]'
```

```ts
// 入场 stagger：每屏前 8 项依次延迟 20ms，其后不延迟（specs §5）
const enterDelay = computed(() => ({
  animationDelay: `${props.enterIndex !== undefined && props.enterIndex < 8 ? props.enterIndex * 20 : 0}ms`
}))
```

- [ ] **Step 2: 改 `ExampleCard.vue` 模板区**

根节点（选中态保留工具类覆盖，普通态交给 `.surface-card`）：

```html
  <div
    :class="[CARD_CLS, selected ? 'border-accent shadow-[0_0_0_2px_rgba(94,106,210,0.3)]' : '']"
    :style="enterDelay"
    role="button"
    tabindex="0"
    :aria-label="`${title}（详情）`"
    @click="emit('open')"
    @keydown.enter="emit('open')"
    @keydown.space.prevent="emit('open')"
  >
```

图标块（两处 `meta.cls` 消费都换 hue-chip）：

```html
      <div
        class="hue-chip w-9 h-9 rounded-control flex items-center justify-center shrink-0"
        :style="{ '--hue': meta.hue }"
      >
        <component :is="icon" :size="17" />
      </div>
```

```html
          <span
            class="hue-chip inline-flex items-center px-1.5 py-px rounded-badge text-badge font-[590] uppercase tracking-[0.03em] shrink-0"
            :style="{ '--hue': meta.hue }"
            >{{ ex.category }}</span
          >
```

运行钮强化 hover 显形（footer 第三个按钮）：

```html
      <button
        :class="[ICON_BTN, 'text-ink-faint group-hover:text-accent group-hover:border-accent/40']"
        title="运行"
        :aria-label="`运行 ${title}`"
        @click.stop="emit('run')"
      >
```

- [ ] **Step 3: 改 `ExampleListItem.vue`**

props 与 `enterDelay` 同 Step 1（`CARD_CLS` 无，其余一致）：

```ts
const props = defineProps<{ ex: VExample; faved?: boolean; enterIndex?: number }>()
```

```ts
const enterDelay = computed(() => ({
  animationDelay: `${props.enterIndex !== undefined && props.enterIndex < 8 ? props.enterIndex * 20 : 0}ms`
}))
```

根节点加动画类与 style（其余类保持不变）：

```html
  <div
    class="group flex items-center gap-2.5 h-11 px-3 bg-panel cursor-pointer transition-colors duration-150 border-b border-line-subtle/50 hover:bg-hover animate-card-in [content-visibility:auto] [contain-intrinsic-size:auto_45px]"
    :style="enterDelay"
    role="button"
    tabindex="0"
    :aria-label="`${title}（详情）`"
    @click="emit('open')"
    @keydown.enter="emit('open')"
    @keydown.space.prevent="emit('open')"
  >
```

图标块：

```html
    <div class="hue-chip w-6 h-6 rounded-control flex items-center justify-center shrink-0" :style="{ '--hue': meta.hue }">
      <component :is="icon" :size="13" />
    </div>
```

- [ ] **Step 4: 全量 grep 确认 `meta.cls` 无残留消费**

Run: `grep -rn "\.cls" src/renderer/components src/renderer/src/category-meta.ts`
Expected: 只剩 `category-meta.ts` 之外无 `meta.cls` / `meta?.cls` 命中（DetailPage 的在 Task 6 清理，此步允许 DetailPage 一处，其余必须为零）。

- [ ] **Step 5: Commit**

```bash
git add src/renderer/components/ExampleCard.vue src/renderer/components/ExampleListItem.vue
git commit -m "feat(ui): 示例卡片/列表行换深邃层次语言——渐变高光面、色相徽章、hover 抬升与入场 stagger"
```

---

### Task 4: 画廊总览 + 导航激活胶囊

**Files:**
- Modify: `src/renderer/components/GalleryOverview.vue`
- Modify: `src/renderer/App.vue`

- [ ] **Step 1: `GalleryOverview.vue` 脚本区——引入色相表与收藏计数**

import 区追加（合并进现有 store import）：

```ts
import { SECTION_HUES } from '../src/overview'
```

```ts
// store import 列表中追加 favorites
import { favorites, facetCounts, galleryExamples, isFavorite, openDetail, openGalleryBrowse, runFromCard, toggleFavorite } from '../store'
```

新增辅助函数（`moreCount` 旁）：

```ts
/** 区头色相：others 等无色相分区返回 undefined，模板回退中性 chip */
function secHue(key: string): Record<string, string> | undefined {
  return SECTION_HUES[key] ? { '--hue': SECTION_HUES[key] } : undefined
}
```

- [ ] **Step 2: `GalleryOverview.vue` 模板——页头换极光 + 统计 chips**

```html
    <div class="app-drag select-none px-8 pt-7 pb-3 aurora-hero">
      <div class="max-w-[1200px] mx-auto flex items-end justify-between gap-4">
        <div>
          <h1 class="text-page font-[650] text-ink m-0 tracking-[-0.02em]">示例库</h1>
          <div class="flex items-center gap-1.5 mt-2.5 app-no-drag">
            <span class="stat-chip"><b class="font-mono">{{ galleryExamples.length }}</b> 个示例</span>
            <span class="stat-chip"><b class="font-mono">{{ THEMES.length }}</b> 大主题</span>
            <span class="stat-chip stat-chip-ok"><b class="font-mono">{{ runnablePct }}%</b> 可运行</span>
            <span class="stat-chip"><b class="font-mono">{{ favorites.size }}</b> 收藏</span>
          </div>
        </div>
        <div class="app-no-drag flex items-center gap-2 shrink-0">
          <BaseButton @click="openGalleryBrowse({ theme: 'all' })">浏览全部</BaseButton>
          <BaseButton variant="primary" @click="openGalleryBrowse({ favOnly: true })">我的收藏</BaseButton>
        </div>
      </div>
    </div>
```

THEMES 需已在 import（现有 `import { THEMES } from '../src/themes'` 保留）。

- [ ] **Step 3: `GalleryOverview.vue` 模板——区头图标换色相徽章**

把区头的 `<span class="text-title leading-none">{{ sec.icon }}</span>` 替换为：

```html
            <span
              class="hue-chip w-[18px] h-[18px] rounded-control flex items-center justify-center text-[11px] leading-none shrink-0"
              :class="secHue(sec.key) ? '' : 'bg-card border-line-subtle text-ink-faint'"
              :style="secHue(sec.key)"
              aria-hidden="true"
              >{{ sec.icon }}</span
            >
```

- [ ] **Step 4: `GalleryOverview.vue` 模板——总览预览卡片传入场序号**

`<div v-for="ex in sec.items.slice(0, PREVIEW_COUNT)" ...>` 改为带索引，并传给卡片：

```html
            <div v-for="(ex, i) in sec.items.slice(0, PREVIEW_COUNT)" :key="ex.id" class="w-[220px] shrink-0 flex">
              <ExampleCard
                :ex="ex"
                :enter-index="i"
                :faved="isFavorite(ex.id)"
                @open="openDetail(ex.id)"
                @fav="toggleFavorite(ex.id)"
                @run="onRun(ex.id)"
              />
            </div>
```

- [ ] **Step 5: `App.vue` 导航激活胶囊**

导航按钮的激活类 `'bg-card text-ink shadow-elev-1 font-medium'` 改为：

```ts
          :class="activeView === item.key
            ? 'surface-raised text-ink font-medium'
            : 'bg-transparent text-ink-mute hover:text-ink hover:bg-hover font-normal'"
```

（左缘强调条 span 保留不动。）

- [ ] **Step 6: 验证**

Run: `npm run typecheck`
Expected: exit 0（若此处因 Task 2 的 `cls` 移除报 DetailPage 错误，属预期，Task 6 修复；如报错阻塞验证，可先给 `category-meta.ts` 临时加回 `cls?: string` 可选字段并在 Task 6 移除——两种处理选其一，最终态必须无 `cls`）。

- [ ] **Step 7: Commit**

```bash
git add src/renderer/components/GalleryOverview.vue src/renderer/App.vue
git commit -m "feat(ui): 画廊总览极光页头与统计 chips、区头色相徽章；导航激活胶囊凸起化"
```

---

### Task 5: 下钻浏览态——面包屑结果条 + 筛选栏精修 + 工具箱串联

**Files:**
- Modify: `src/renderer/components/BrowseToolbar.vue`
- Modify: `src/renderer/components/GalleryView.vue`
- Modify: `src/renderer/components/ToolboxView.vue`
- Modify: `src/renderer/components/FilterSidebar.vue`
- Modify: `src/renderer/components/base/SkeletonCard.vue`

- [ ] **Step 1: `BrowseToolbar.vue`——改双行（面包屑 + 工具条），脚本区加 `filtered`**

脚本 import 追加：

```ts
import { activeCategory, activeSectionTags, activeTheme, clearAllFilters, filtered, galleryChips, galleryMode, persistViewPrefs, removeChip, sortBy, viewMode } from '../store'
```

模板整体替换为：

```html
<template>
  <div class="app-drag select-none shrink-0 bg-panel border-b border-line-subtle">
    <!-- 行 1：面包屑结果条（specs §4.2） -->
    <div class="flex items-center gap-1.5 px-4 h-[26px] border-b border-line-subtle/60 text-caption">
      <button
        class="app-no-drag flex items-center gap-1 h-5 px-1.5 rounded-control border-0 bg-transparent text-caption text-ink-mute hover:text-ink hover:bg-hover cursor-pointer shrink-0 transition-colors duration-150"
        title="返回总览"
        @click="backToOverview()"
      >
        <ArrowLeft :size="12" /> 示例库
      </button>
      <span class="text-ink-faint" aria-hidden="true">/</span>
      <span class="font-[590] text-ink-dim truncate" :title="title">{{ title }}</span>
      <span class="app-no-drag ml-auto text-ink-faint font-mono shrink-0" aria-live="polite">{{ filtered.length }} 个结果</span>
    </div>

    <!-- 行 2：筛选芯片 + 排序 + 密度 -->
    <div class="flex items-center gap-2 px-4 h-10">
      <div v-if="galleryChips.length" class="app-no-drag flex-1 min-w-0 flex items-center gap-1.5 overflow-x-auto [scrollbar-width:none]">
        <span
          v-for="chip in galleryChips"
          :key="chip.key + ':' + chip.value"
          class="inline-flex items-center gap-1 h-6 pl-2 pr-1 rounded-badge bg-accent/10 text-accent-strong text-caption shrink-0 whitespace-nowrap"
        >
          {{ chip.label }}
          <button
            class="w-4 h-4 flex items-center justify-center rounded-full border-0 bg-transparent cursor-pointer text-accent-strong/70 hover:text-ink hover:bg-accent/20 transition-colors duration-150"
            :title="`移除筛选：${chip.label}`"
            :aria-label="`移除筛选：${chip.label}`"
            @click="removeChip(chip)"
          >
            <X :size="10" />
          </button>
        </span>
        <button
          class="shrink-0 border-0 bg-transparent text-caption text-ink-mute hover:text-ink cursor-pointer whitespace-nowrap"
          @click="clearAllFilters()"
        >
          清空
        </button>
      </div>
      <div v-else class="flex-1"></div>

      <BaseSelect v-model="sortBy" title="排序" class="app-no-drag shrink-0">
        <option value="quality_desc">质量分优先</option>
        <option value="name">按名称</option>
        <option value="last_run">最近运行</option>
      </BaseSelect>

      <div class="app-no-drag flex items-center rounded-control border border-line-subtle overflow-hidden shrink-0 bg-page" role="group" aria-label="浏览密度">
        <button
          :class="[SEG_BTN, viewMode === 'grid' ? 'bg-accent/15 text-ink' : '']"
          title="网格视图"
          aria-label="网格视图"
          :aria-pressed="viewMode === 'grid'"
          @click="setMode('grid')"
        >
          <LayoutGrid :size="13" />
        </button>
        <button
          :class="[SEG_BTN, viewMode === 'list' ? 'bg-accent/15 text-ink' : '']"
          title="列表视图"
          aria-label="列表视图"
          :aria-pressed="viewMode === 'list'"
          @click="setMode('list')"
        >
          <List :size="13" />
        </button>
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 2: `GalleryView.vue`——视图切换动画 + 卡片传入场序号**

总览分支根 div（`v-show="galleryMode === 'overview'"` 的那个）类追加 `animate-view-in`；浏览分支根 div（`v-show="galleryMode === 'browse'"`）同样追加。

网格循环加索引并传参：

```html
            <ExampleCard
              v-for="(ex, i) in shownGallery"
              :key="ex.id"
              :ex="ex"
              :enter-index="i"
              :faved="isFavorite(ex.id)"
              @open="openDetail(ex.id)"
              @fav="toggleFavorite(ex.id)"
              @run="onRun(ex.id)"
            />
```

清单循环同理：

```html
            <ExampleListItem
              v-for="(ex, i) in shownGallery"
              :key="ex.id"
              :ex="ex"
              :enter-index="i"
              :faved="isFavorite(ex.id)"
              @open="openDetail(ex.id)"
              @fav="toggleFavorite(ex.id)"
              @run="onRun(ex.id)"
            />
```

- [ ] **Step 3: `ToolboxView.vue`——区头色相徽章 + 入场序号**

脚本区追加色相映射与辅助函数（`PROJECT_ICONS` 定义之后）：

```ts
// 区头色相（specs §3.2 工具箱侧；键与 PROJECT_ICONS 对齐，未收录回退石板灰）
const TOOLBOX_HUES: Record<string, string> = {
  'db-table-dictionary-generator': '#2fb8a6',
  'excel-row-to-in-clause': '#2fa866',
  'python-black-magic': '#9a6bf2',
  'remote-sftp-downloader': '#38a8e0',
  'tkinter-work-countdown': '#d9a03d',
  'utility-crawlers': '#e07840',
  'wechat-official-account': '#2fa866',
  standalone: '#64748b'
}
function groupHue(key: string): Record<string, string> {
  return { '--hue': TOOLBOX_HUES[key] || '#64748b' }
}
```

区头图标块替换：

```html
              <div class="hue-chip w-7 h-7 rounded-control flex items-center justify-center shrink-0" :style="groupHue(g.key)">
                <component :is="iconOf(g.key)" :size="15" />
              </div>
```

卡片循环加索引并传参：

```html
              <ExampleCard
                v-for="(ex, i) in isExpanded(g.key) ? g.items : g.items.slice(0, PREVIEW_COUNT)"
                :key="ex.id"
                :ex="ex"
                :enter-index="i"
                :faved="isFavorite(ex.id)"
                @open="openDetail(ex.id)"
                @fav="toggleFavorite(ex.id)"
                @run="onRun(ex.id)"
              />
```

- [ ] **Step 4: `FilterSidebar.vue`——「筛选」小标与组头字距**

`ICON_BTN` 定义之后的标题 span 改为：

```html
      <span v-if="!collapsed" class="ml-1.5 text-caption font-[650] text-ink-faint tracking-[0.08em]">筛选</span>
```

`GROUP_CLS` 字符串中 `text-caption font-[590] text-ink-faint` 改为 `text-caption font-[650] text-ink-faint tracking-[0.04em]`（其余不变）。

- [ ] **Step 5: `SkeletonCard.vue`——对齐新卡片**

```html
<template>
  <!-- SkeletonCard：画廊首载骨架卡（与 ExampleCard 同构的占位块） -->
  <div class="surface-card p-3.5 flex flex-col gap-3 animate-pulse [content-visibility:auto] [contain-intrinsic-size:auto_170px]">
    <div class="flex items-center gap-2.5">
      <div class="w-9 h-9 rounded-control bg-card shrink-0"></div>
      <div class="flex-1 min-w-0 space-y-1.5">
        <div class="h-3 w-3/5 rounded bg-card"></div>
        <div class="h-2.5 w-2/5 rounded bg-card"></div>
      </div>
    </div>
    <div class="space-y-1.5">
      <div class="h-2.5 w-full rounded bg-card"></div>
      <div class="h-2.5 w-4/5 rounded bg-card"></div>
      <div class="h-2.5 w-3/5 rounded bg-card"></div>
    </div>
  </div>
</template>
```

- [ ] **Step 6: 验证**

Run: `npm run typecheck`
Expected: exit 0 或仅剩 DetailPage 的 `meta.cls` 报错（Task 6 处理）。

- [ ] **Step 7: Commit**

```bash
git add src/renderer/components/BrowseToolbar.vue src/renderer/components/GalleryView.vue src/renderer/components/ToolboxView.vue src/renderer/components/FilterSidebar.vue src/renderer/components/base/SkeletonCard.vue
git commit -m "feat(ui): 下钻浏览态双行结果条(面包屑+计数)、工具箱色相区头、筛选栏精修"
```

---

### Task 6: 详情页——路径副标题 + 分段控件 + 终端容器

**Files:**
- Modify: `src/renderer/components/DetailPage.vue`
- Modify: `src/renderer/components/OutputPanel.vue`

- [ ] **Step 1: `DetailPage.vue` 脚本区**

`meta` computed 之后追加：

```ts
// 路径副标题（specs §4.3）：分类 / 示例 id（无 id 回退文件名）
const pathLabel = computed(() => [ex.value?.category, ex.value?.id || ex.value?.name].filter(Boolean).join(' / '))
```

tab 类替换为分段控件语义：

```ts
const TAB_IDLE =
  'px-2.5 h-6 inline-flex items-center rounded-[5px] text-control font-[510] font-sans cursor-pointer border border-transparent bg-transparent text-ink-mute hover:text-ink transition-colors duration-[120ms]'
const TAB_ACTIVE = `${TAB_IDLE} surface-raised !border-transparent text-ink`
```

- [ ] **Step 2: `DetailPage.vue` 模板——图标块与分类徽章换 hue-chip**

图标块：

```html
      <div class="hue-chip w-7 h-7 rounded-control flex items-center justify-center shrink-0" :style="{ '--hue': meta?.hue }">
        <component :is="metaIcon" :size="15" />
      </div>
```

分类徽章：

```html
          <span
            v-if="meta"
            class="hue-chip inline-flex items-center px-1.5 py-px rounded-badge text-badge font-[590] uppercase tracking-[0.03em] shrink-0"
            :style="{ '--hue': meta.hue }"
            >{{ ex.category }}</span
          >
```

- [ ] **Step 3: `DetailPage.vue` 模板——标题下第二行加路径副标题（保留标签 chips）**

把第二行 `<div class="flex items-center gap-1 min-w-0">…tags…</div>` 替换为：

```html
        <div class="flex items-center gap-1.5 min-w-0">
          <span class="text-badge font-mono text-ink-faint truncate lowercase tracking-[0.02em]" :title="pathLabel">{{ pathLabel }}</span>
          <span
            v-for="tag in (ex.tags || []).slice(0, 3)"
            :key="tag"
            class="text-caption px-1.5 py-px bg-card rounded-badge text-ink-mute font-mono truncate shrink-0"
            >{{ tag }}</span
          >
          <span v-if="(ex.tags || []).length > 3" class="text-caption text-ink-faint shrink-0"
            >+{{ (ex.tags || []).length - 3 }}</span
          >
        </div>
```

- [ ] **Step 4: `OutputPanel.vue`——输出包终端容器**

把 viewer div（`<div ref="viewer" class="flex-1 min-h-0 overflow-auto bg-inset px-4 py-3 …">`）及其外层改为：

```html
    <div class="flex-1 min-h-0 m-2 rounded-panel border border-line-subtle/60 bg-inset overflow-hidden flex flex-col">
      <div ref="viewer" class="flex-1 min-h-0 overflow-auto px-3.5 py-3 font-mono text-control leading-[1.6]">
        <div v-if="state.lines.length === 0" class="text-ink-faint text-caption">点击「运行」，输出将实时显示在这里</div>
        <div v-if="state.truncated" class="text-ink-faint italic text-caption whitespace-pre-wrap break-all">
          [系统] 输出超过上限，已自动截断，仅保留最近的输出
        </div>
        <div v-for="(line, i) in state.lines" :key="i" class="whitespace-pre-wrap break-all" :class="LINE_CLS[line.cls]">
          {{ line.text }}
        </div>
      </div>
    </div>
```

（进度条块与结果图片块位置不变。）

- [ ] **Step 5: 验证**

Run: `grep -rn "meta.cls\|meta?.cls" src/renderer/ ; npm run typecheck`
Expected: grep 无命中（exit 1）；typecheck exit 0。

- [ ] **Step 6: Commit**

```bash
git add src/renderer/components/DetailPage.vue src/renderer/components/OutputPanel.vue
git commit -m "feat(ui): 详情页路径副标题与分段控件标签、终端输出内嵌容器"
```

---

### Task 7: 主按钮 / 弹窗高光 / 全量验证

**Files:**
- Modify: `src/renderer/components/base/BaseButton.vue`
- Modify: `src/renderer/components/base/AppModal.vue`
- Modify: `src/renderer/components/CommandPalette.vue`

- [ ] **Step 1: `BaseButton.vue`——primary 换 `.btn-primary-deep`**

```ts
const VARIANT_CLS: Record<string, string> = {
  ghost:
    'border border-line-subtle bg-transparent text-ink-dim hover:bg-hover hover:text-ink hover:border-line-strong',
  primary: 'btn-primary-deep',
  danger: 'border border-danger bg-danger text-white hover:opacity-90'
}
```

- [ ] **Step 2: `AppModal.vue`——面板顶边高光**

面板 class（`ref="panelRef"` 那个 div）中 `bg-panel border border-line-subtle rounded-panel` 追加 `edge-highlight-top`：

```html
        class="bg-panel border border-line-subtle edge-highlight-top rounded-panel shadow-elev-3 max-w-[92vw] max-h-[86vh] flex flex-col animate-modal-in outline-none"
```

- [ ] **Step 3: `CommandPalette.vue`——面板顶边高光**

`<div class="w-[560px] max-w-full bg-panel border border-line-subtle rounded-panel shadow-elev-3 overflow-hidden animate-modal-in">` 改为：

```html
      <div class="w-[560px] max-w-full bg-panel border border-line-subtle edge-highlight-top rounded-panel shadow-elev-3 overflow-hidden animate-modal-in">
```

- [ ] **Step 4: 全量验证（验收标准 §8）**

Run（依次）:

```bash
npm run typecheck        # 期望 exit 0
npm run build            # 期望 exit 0
npm run smoke            # 期望 exit 0；输出含六链路与渲染层 0 console 错误
E2E_TEST=1 ./node_modules/.bin/electron . > /tmp/e2e-ui-overhaul.log 2>&1; echo EXIT=$?   # 期望 EXIT=0
```

补充人工检查（运行 `npm start` 后目测，不需要截图回传）：深/浅主题下总览极光、卡片 hover 抬升、面包屑、详情页分段控件与终端容器、主按钮渐变；`prefers-reduced-motion`（系统辅助功能开启）下无位移动画。

- [ ] **Step 5: Commit**

```bash
git add src/renderer/components/base/BaseButton.vue src/renderer/components/base/AppModal.vue src/renderer/components/CommandPalette.vue
git commit -m "feat(ui): 主按钮渐变发光、弹窗与命令面板顶边高光；全量验证通过"
```

---

## Self-Review 记录

- **Spec coverage**: §3.1→Task 1/3；§3.2→Task 1/2/3/4/5/6；§3.3/3.4→Task 1；§3.5→Task 1/7；§3.6→Task 1/4；§4.1→Task 4；§4.2→Task 5；§4.3→Task 6；§4.4→Task 5；§4.5→经 OutputPanel（Task 6）与 BaseButton（Task 7）覆盖，RunnerView 自身无文件改动（规格为「轻改、令牌对齐」，由共享类自动生效）；§4.6→Task 4/7；§5 动效→Task 1（keyframes）/3/5（应用）；§6 约束→各 Task 保留 aria + Task 2 Step 3 对比度脚本；§7 清单→上文 File Structure 一致（AppToast/Skeleton 规格允许「视需要」，Skeleton 已做、AppToast 不动）；§8→Task 7 Step 4。
- **Placeholder scan**: 无 TBD/TODO；所有代码步骤含完整代码。
- **Type consistency**: `enterIndex` prop 名与 `enter-index` 传参一致；`SECTION_HUES`/`CATEGORY_META.hue`/`TOOLBOX_HUES` 消费方式统一为 `--hue` 内联变量 + `.hue-chip`；`secHue`/`groupHue`/`pathLabel` 均在对应 Task 中定义。
