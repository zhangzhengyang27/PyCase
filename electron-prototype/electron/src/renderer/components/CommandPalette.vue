<script setup lang="ts">
// CommandPalette：Cmd+K 全局命令面板（设计规范 v1）
// 最近运行 5 条置顶；输入按名称/标题匹配 Top 12；↑↓ 导航，Enter 打开详情，
// Cmd+Enter 直接运行，Esc 关闭。数据全部来自 store 派生。
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Clock, CornerDownLeft, FileCode2, Play, Search, Wrench } from 'lucide-vue-next'
import { examples, openDetail, runFromCard, runHistory } from '../store'

const emit = defineEmits<{ close: [] }>()

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
  <Teleport to="body">
    <div class="fixed inset-0 z-[1200] flex items-start justify-center pt-[14vh] bg-black/50 px-6" @click.self="emit('close')">
      <div class="w-[560px] max-w-full bg-panel border border-line-subtle edge-highlight-top rounded-panel shadow-elev-3 overflow-hidden animate-modal-in">
        <div class="flex items-center gap-2.5 px-3.5 h-11 border-b border-line-subtle">
          <Search :size="15" class="text-ink-faint shrink-0" />
          <input
            ref="inputEl"
            v-model="query"
            type="text"
            placeholder="搜索示例（名称 / 标题 / 标签）…"
            aria-label="全局搜索示例"
            spellcheck="false"
            class="flex-1 bg-transparent border-0 outline-none text-body text-ink placeholder:text-ink-faint"
          />
          <kbd class="px-1 py-px text-badge font-mono bg-card border border-line-subtle rounded-badge text-ink-faint shrink-0">Esc</kbd>
        </div>

        <div ref="listEl" class="max-h-[380px] overflow-y-auto p-1.5">
          <!-- 空查询：最近运行分组（行容器用 div role=button：内嵌「运行」钮不允许 button 套 button） -->
          <template v-if="!query.trim() && recents.length">
            <div class="flex items-center gap-1.5 px-2.5 pt-1.5 pb-1 text-caption text-ink-faint">
              <Clock :size="11" /> 最近运行
            </div>
            <div
              v-for="(item, i) in recents"
              :key="`r-${item.id}`"
              class="w-full flex items-center gap-2.5 h-9 px-2.5 rounded-control bg-transparent text-control cursor-pointer text-left border-0"
              :class="i === idx ? 'bg-accent/15 text-ink' : 'text-ink-dim hover:bg-hover hover:text-ink'"
              :data-active="i === idx"
              role="button"
              tabindex="0"
              @click="openItem(item)"
              @mousemove="idx = i"
              @keydown.enter.prevent="openItem(item)"
              @keydown.space.prevent="openItem(item)"
            >
              <FileCode2 :size="14" class="shrink-0 text-ink-faint" />
              <span class="truncate">{{ item.name }}</span>
              <span class="ml-auto flex items-center gap-1 shrink-0">
                <button
                  class="flex items-center gap-1 px-1.5 h-5 rounded-badge border border-line-subtle bg-transparent text-caption text-ink-mute hover:text-ink hover:border-line-strong cursor-pointer"
                  title="直接运行（面板内 Cmd+Enter）"
                  aria-label="直接运行"
                  @click.stop="openItem(item, true)"
                >
                  <Play :size="10" /> 运行
                </button>
              </span>
            </div>
          </template>

          <!-- 示例分组 -->
          <div class="flex items-center gap-1.5 px-2.5 pt-1.5 pb-1 text-caption text-ink-faint">
            <Search :size="11" /> {{ query.trim() ? '匹配结果' : '示例' }}
          </div>
          <div v-if="matches.length === 0" class="px-2.5 py-3 text-control text-ink-faint">
            {{ query.trim() ? '没有匹配的示例' : '库中暂无示例' }}
          </div>
          <button
            v-for="(item, i) in matches"
            :key="`m-${item.id}`"
            class="w-full flex items-center gap-2.5 h-9 px-2.5 rounded-control border-0 bg-transparent text-control cursor-pointer text-left"
            :class="(query.trim() ? i : recents.length + i) === idx ? 'bg-accent/15 text-ink' : 'text-ink-dim hover:bg-hover hover:text-ink'"
            :data-active="(query.trim() ? i : recents.length + i) === idx"
            @click="openItem(item)"
            @mousemove="idx = (query.trim() ? i : recents.length + i)"
          >
            <component :is="item.category === 'tools' ? Wrench : FileCode2" :size="14" class="shrink-0 text-ink-faint" />
            <span class="truncate">{{ item.name }}</span>
            <span v-if="item.category" class="shrink-0 text-caption text-ink-faint">{{ item.category }}</span>
            <CornerDownLeft v-if="(query.trim() ? i : recents.length + i) === idx" :size="12" class="ml-auto shrink-0 text-ink-faint" />
          </button>
        </div>

        <div class="flex items-center gap-3 px-3.5 h-7 border-t border-line-subtle text-caption text-ink-faint">
          <span>↑↓ 选择</span>
          <span>↵ 打开详情</span>
          <span>⌘↵ 直接运行</span>
        </div>
      </div>
    </div>
  </Teleport>
</template>
