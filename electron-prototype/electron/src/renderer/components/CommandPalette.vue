<script setup lang="ts">
// CommandPalette：Cmd+K 全局命令面板（设计规范 v1）
// 最近运行 5 条置顶；输入按名称/标题匹配 Top 12；↑↓ 导航，Enter 打开详情，
// Cmd+Enter 直接运行，Esc 关闭。数据全部来自 store 派生。
// 壳 = reka-ui Dialog（Portal / 遮罩 / 焦点圈定 / aria）；键盘导航仍由本组件在
// window 捕获阶段统一接管——Esc 在这里 stopPropagation 后自行关闭，
// 不让事件落到面板下方的弹层（reka-ui 的分层只管 reka 自家的弹层）。
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { DialogContent, DialogOverlay, DialogPortal, DialogRoot, DialogTitle } from 'reka-ui'
import { Clock, CornerDownLeft, FileCode2, Play, Search, Wrench } from 'lucide-vue-next'
import { examples } from '../src/store/catalog'
import { openDetail, runFromCard } from '../src/store/detail'
import { runHistory } from '../src/store/prefs'
import { modKeyLabel } from '../src/platform'

const emit = defineEmits<{ close: [] }>()

const modKey = modKeyLabel()

const query = ref('')
const idx = ref(0)
const listEl = ref<HTMLElement | null>(null)
const inputEl = ref<HTMLInputElement | null>(null)

interface PaletteItem {
  id: string
  name: string
  category: string
  source: 'recent' | 'match'
}

const exMap = computed(() => new Map(examples.value.map((e) => [e.id, e])))

// 最近运行：按 id 去重取前 5
const recents = computed<PaletteItem[]>(() => {
  const seen = new Set<string>()
  const list: PaletteItem[] = []
  for (const h of runHistory.value) {
    if (seen.has(h.id)) continue
    seen.add(h.id)
    const ex = exMap.value.get(h.id)
    list.push({ id: h.id, name: h.name || ex?.name || h.id, category: ex?.category || '', source: 'recent' })
    if (list.length >= 5) break
  }
  return list
})

const matches = computed<PaletteItem[]>(() => {
  const q = query.value.trim().toLowerCase()
  const pool = examples.value
  const to = (e: { id: string; name?: string; category: string }): PaletteItem => ({
    id: e.id,
    name: e.name || e.id,
    category: e.category,
    source: 'match'
  })
  if (!q) return pool.slice(0, 12).map(to)
  const recentIds = new Set(recents.value.map((r) => r.id))
  return pool
    .filter(
      (e) =>
        (e.name || '').toLowerCase().includes(q) ||
        (e.title || '').toLowerCase().includes(q) ||
        (e._tagsAll || []).some((t) => t.toLowerCase().includes(q))
    )
    .filter((e) => !recentIds.has(e.id))
    .slice(0, 12)
    .map(to)
})

// 键盘导航的平铺序列：查询时只有匹配项；空闲时最近 + 示例
const flat = computed<PaletteItem[]>(() => (query.value.trim() ? matches.value : [...recents.value, ...matches.value]))
const active = computed(() => flat.value[Math.min(idx.value, flat.value.length - 1)])

watch([query, flat], () => {
  idx.value = 0
})

watch(idx, async () => {
  await nextTick()
  listEl.value?.querySelector('[data-active="true"]')?.scrollIntoView({ block: 'nearest' })
})

function openItem(item: PaletteItem, run = false): void {
  if (run) void runFromCard(item.id)
  else openDetail(item.id)
  emit('close')
}

function onKeydown(e: KeyboardEvent): void {
  // 面板是最上层：Esc/方向键/Enter 一律由面板消费，不再向下传给底下的弹层
  // （否则一次 Esc 会同时关掉面板与其下方的对话框）
  if (e.key === 'Escape' || e.key === 'ArrowDown' || e.key === 'ArrowUp' || e.key === 'Enter') {
    e.stopPropagation()
  }
  if (e.key === 'Escape') {
    e.preventDefault()
    emit('close')
  } else if (e.key === 'ArrowDown') {
    e.preventDefault()
    if (flat.value.length) idx.value = (idx.value + 1) % flat.value.length
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    if (flat.value.length) idx.value = (idx.value - 1 + flat.value.length) % flat.value.length
  } else if (e.key === 'Enter') {
    e.preventDefault()
    if (active.value) openItem(active.value, e.metaKey || e.ctrlKey)
  }
}

onMounted(() => {
  // 键盘只在这里统一接管：window 捕获阶段能收到面板内任意位置（含搜索框）的按键。
  // 搜索框上**不要**再挂 @keydown —— 那会让同一个按键被处理两次（捕获一次 + 目标一次），
  // ↑↓ 一次跨两行、Enter 触发两次打开。
  window.addEventListener('keydown', onKeydown, true)
  inputEl.value?.focus()
})
onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown, true))
</script>

<template>
  <DialogRoot :open="true" @update:open="(v: boolean) => !v && emit('close')">
    <DialogPortal>
      <DialogOverlay class="scrim z-[1200]" />
      <DialogContent
        aria-label="命令面板"
        :aria-describedby="undefined"
        class="fixed left-1/2 top-[14vh] z-[1200] w-[560px] max-w-full -translate-x-1/2 bg-card border border-line-hairline rounded-overlay shadow-elev-3 overflow-hidden animate-modal-in outline-none"
      >
        <DialogTitle class="sr-only">命令面板</DialogTitle>

        <!-- 搜索行（页稿板 3：44px 高，输入占主，右侧 Esc 提示） -->
        <div class="flex items-center gap-2.5 px-3 h-11 border-b border-line-hairline">
          <Search :size="15" :stroke-width="1.5" class="text-ink-mute shrink-0" />
          <input
            ref="inputEl"
            v-model="query"
            type="text"
            placeholder="搜索示例（名称 / 标题 / 标签）…"
            aria-label="全局搜索示例"
            spellcheck="false"
            class="flex-1 bg-transparent border-0 outline-none text-body text-ink placeholder:text-ink-faint"
          />
          <kbd
            class="px-1 py-px text-caption font-mono border border-line-hairline rounded-control text-ink-mute shrink-0"
            >Esc</kbd
          >
        </div>

        <div ref="listEl" class="max-h-[380px] overflow-y-auto py-1.5">
          <!-- 空查询：最近运行分组（行容器用 div role=button：内嵌「运行」钮不允许 button 套 button） -->
          <template v-if="!query.trim() && recents.length">
            <div class="flex items-center gap-1.5 px-3 pt-1.5 pb-1 text-caption text-ink-mute">
              <Clock :size="12" :stroke-width="1.5" /> 最近运行
            </div>
            <div
              v-for="(item, i) in recents"
              :key="`r-${item.id}`"
              class="p-row mx-1.5"
              :data-active="i === idx"
              role="button"
              tabindex="0"
              @click="openItem(item)"
              @mousemove="idx = i"
              @keydown.enter.prevent="openItem(item)"
              @keydown.space.prevent="openItem(item)"
            >
              <FileCode2 :size="14" :stroke-width="1.5" class="shrink-0 text-ink-mute" />
              <span class="r-name truncate">{{ item.name }}</span>
              <span class="ml-auto flex items-center gap-1 shrink-0">
                <button
                  class="r-mark flex items-center gap-1 px-1.5 h-5 rounded-control border border-line-hairline bg-transparent text-caption text-ink-mute hover:text-ink hover:border-line-strong cursor-pointer"
                  title="直接运行（面板内 Cmd+Enter）"
                  aria-label="直接运行"
                  @click.stop="openItem(item, true)"
                >
                  <Play :size="10" :stroke-width="1.5" /> 运行
                </button>
              </span>
            </div>
          </template>

          <!-- 示例分组 -->
          <div class="flex items-center gap-1.5 px-3 pt-1.5 pb-1 text-caption text-ink-mute">
            <Search :size="12" :stroke-width="1.5" /> {{ query.trim() ? '匹配结果' : '示例' }}
          </div>
          <div v-if="matches.length === 0" class="px-3 py-3 text-control text-ink-mute">
            {{ query.trim() ? '没有匹配的示例' : '库中暂无示例' }}
          </div>
          <button
            v-for="(item, i) in matches"
            :key="`m-${item.id}`"
            class="p-row mx-1.5"
            :data-active="(query.trim() ? i : recents.length + i) === idx"
            @click="openItem(item)"
            @mousemove="idx = query.trim() ? i : recents.length + i"
          >
            <component
              :is="item.category === 'tools' ? Wrench : FileCode2"
              :size="14"
              :stroke-width="1.5"
              class="shrink-0 text-ink-mute"
            />
            <span class="r-name truncate">{{ item.name }}</span>
            <span v-if="item.category" class="shrink-0 text-caption text-ink-mute">{{ item.category }}</span>
            <CornerDownLeft
              v-if="(query.trim() ? i : recents.length + i) === idx"
              :size="12"
              :stroke-width="1.5"
              class="r-mark ml-auto shrink-0 text-ink-mute"
            />
          </button>
        </div>

        <div class="flex items-center gap-3 px-3 h-8 border-t border-line-hairline text-caption text-ink-mute">
          <span>↑↓ 选择</span>
          <span>↵ 打开详情</span>
          <span>{{ modKey }}↵ 直接运行</span>
        </div>
      </DialogContent>
    </DialogPortal>
  </DialogRoot>
</template>
