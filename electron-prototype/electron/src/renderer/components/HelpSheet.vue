<script setup lang="ts">
// HelpSheet：帮助与快捷键（A5.5 板 1）
// 内容四段：键位表 / 常用操作 / 安全边界 / 环境信息。
// 键位表与代码同源（App.vue、DetailPage.vue、CommandPalette.vue、RunnerView.vue），
// 改动快捷键时必须同步本表——smoke 会断言条目数与平台化修饰键。
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { CornerDownLeft, FileCode2, Play, Search, ShieldAlert, X } from 'lucide-vue-next'
import { examples } from '../src/store/catalog'
import { appInfo, envStatus, openLog } from '../src/store/env'
import { modKeyLabel } from '../src/platform'

const emit = defineEmits<{ close: [] }>()

const modKey = modKeyLabel()
const panelEl = ref<HTMLElement | null>(null)

/** 键位表：全部来自代码，无新增键位 */
const KEYS: Array<{ keys: string[]; desc: string }> = [
  { keys: [`${modKey} K`], desc: '全局搜索：打开命令面板，可搜名称 / 标签 / 代码片段' },
  { keys: ['↑', '↓'], desc: '在列表或面板中上下选择' },
  { keys: ['↵'], desc: '打开选中示例的详情' },
  { keys: [`${modKey} ↵`], desc: '运行示例（详情页与运行器内同键）' },
  { keys: [`${modKey} S`], desc: '保存改动（未改动时不可用）' },
  { keys: [`${modKey} .`], desc: '停止正在运行的示例' },
  { keys: [`${modKey} /`], desc: '打开 / 关闭本页' }
]

const OPS = [
  { icon: Search, title: '找示例', body: '画廊按主题分区；工具箱按工具体量分组；急用时 ' + modKey + ' K 直接搜。' },
  {
    icon: Play,
    title: '运行与看结果',
    body: '详情页右侧「终端输出」实时显示；示例生成的图片自动收进「资源」标签，可预览与下载。'
  },
  {
    icon: FileCode2,
    title: '编辑与保存',
    body: '左侧 Monaco 编辑器；改动后 ' + modKey + ' S 保存，内置示例可随时恢复原始版本。'
  }
]

const env = computed(() => envStatus.value)
/** 用户集合数：示例自带的 collection 字段去重（内置库没有集合名） */
const userCollectionCount = computed(() => new Set(examples.value.map((e) => e.collection).filter(Boolean)).size)
const envLine = computed(() => {
  const e = env.value
  if (!e) return '正在读取…'
  const parts: string[] = [e.venv_path ? e.venv_path.split('/').slice(-2).join('/') : '.venv']
  if (e.mode === 'system') parts.push('系统 Python')
  else if (e.phase === 'ready') parts.push('已就绪')
  else if (e.phase === 'failed') parts.push('准备失败')
  else parts.push('准备中')
  if (e.python_version) parts.push(`Python ${e.python_version}`)
  return parts.join(' · ')
})

// 焦点圈定口径与 base.spec / overlays.spec 的测试查询一致（审计 P2）
const FOCUSABLE = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'

function onKey(e: KeyboardEvent): void {
  if (e.key === 'Escape') {
    e.stopPropagation()
    e.preventDefault()
    emit('close')
    return
  }
  // Tab 圈定：手写模态此前会把焦点放去背景层（reka-ui 系弹窗由底座承担）
  if (e.key === 'Tab') {
    const panel = panelEl.value
    if (!panel) return
    const items = Array.from(panel.querySelectorAll<HTMLElement>(FOCUSABLE)).filter(
      (el) => !el.hasAttribute('disabled')
    )
    if (items.length === 0) return
    const first = items[0]
    const last = items[items.length - 1]
    const active = document.activeElement as HTMLElement | null
    const inside = active !== null && panel.contains(active)
    if (e.shiftKey) {
      if (active === first || !inside) {
        e.preventDefault()
        last.focus()
      }
      return
    }
    if (active === last || !inside) {
      e.preventDefault()
      first.focus()
    }
  }
}

onMounted(() => {
  window.addEventListener('keydown', onKey, true)
  panelEl.value?.focus()
})
onBeforeUnmount(() => window.removeEventListener('keydown', onKey, true))
</script>

<template>
  <Teleport to="body">
    <div class="scrim z-[1100] flex items-start justify-center pt-[8vh] px-6" @click.self="emit('close')">
      <div
        ref="panelEl"
        role="dialog"
        aria-modal="true"
        aria-label="帮助与快捷键"
        tabindex="-1"
        class="w-[560px] max-w-full max-h-[84vh] overflow-y-auto bg-card border border-line-hairline rounded-overlay shadow-elev-3 animate-modal-in outline-none"
      >
        <header class="flex items-center gap-2 h-11 px-3.5 border-b border-line-hairline sticky top-0 bg-card z-[1]">
          <FileCode2 :size="16" :stroke-width="1.5" class="text-ink-mute shrink-0" />
          <span class="text-title font-semibold text-ink">帮助与快捷键</span>
          <kbd
            class="ml-auto px-1 py-px text-caption font-mono border border-line-hairline rounded-control text-ink-mute"
            >Esc</kbd
          >
          <button
            class="w-6 h-6 flex items-center justify-center rounded-control border-0 bg-transparent cursor-pointer text-ink-mute hover:text-ink hover:bg-hover"
            title="关闭"
            aria-label="关闭帮助"
            @click="emit('close')"
          >
            <X :size="14" :stroke-width="1.5" />
          </button>
        </header>

        <div class="p-3.5 flex flex-col gap-3.5">
          <section>
            <h4 class="m-0 mb-2 text-body font-semibold">
              快捷键<small class="ml-2 text-caption font-normal text-ink-mute">修饰键随平台：{{ modKey }}</small>
            </h4>
            <div class="grid grid-cols-[auto_1fr] gap-x-3.5 gap-y-1.5 items-center">
              <template v-for="(row, i) in KEYS" :key="i">
                <span class="flex items-center gap-1">
                  <kbd
                    v-for="k in row.keys"
                    :key="k"
                    class="font-mono text-caption text-ink-dim border border-line-hairline rounded-[4px] px-1.5 py-px whitespace-nowrap"
                    >{{ k }}</kbd
                  >
                </span>
                <span class="text-caption text-ink-dim leading-[1.5]">{{ row.desc }}</span>
              </template>
            </div>
          </section>

          <section>
            <h4 class="m-0 mb-2 text-body font-semibold">常用操作</h4>
            <div class="flex flex-col gap-2.5">
              <div v-for="op in OPS" :key="op.title" class="flex gap-2.5 items-start">
                <span class="chip-ic !w-6 !h-6">
                  <component :is="op.icon" :size="13" :stroke-width="1.5" />
                </span>
                <span>
                  <span class="block text-caption font-medium text-ink">{{ op.title }}</span>
                  <span class="block text-caption text-ink-dim leading-[1.6]">{{ op.body }}</span>
                </span>
              </div>
            </div>
          </section>

          <section>
            <div class="alertline">
              <ShieldAlert :size="16" :stroke-width="1.5" />
              <span>
                <b>安全边界：</b>示例在独立子进程中运行（30
                秒超时、环境变量白名单），但子进程隔离<b>不是安全沙箱</b>——反射调用、运行时拼接的命令与第三方库内部行为不受静态扫描覆盖。高危示例运行前会二次确认。
              </span>
            </div>
          </section>

          <section>
            <h4 class="m-0 mb-2 text-body font-semibold">环境信息</h4>
            <div class="grid grid-cols-[96px_1fr] gap-x-3 gap-y-1 text-caption">
              <span class="text-ink-mute">应用版本</span>
              <span class="text-ink-dim font-mono"
                >{{ appInfo.version || '—'
                }}<template v-if="appInfo.electron">（Electron {{ appInfo.electron }}）</template></span
              >
              <span class="text-ink-mute">共享环境</span>
              <span class="text-ink-dim font-mono">{{ envLine }}</span>
              <span class="text-ink-mute">示例库</span>
              <span class="text-ink-dim font-mono"
                >{{ examples.length }} 条 · {{ userCollectionCount }} 个用户集合</span
              >
              <span class="text-ink-mute">&nbsp;</span>
              <button
                class="w-fit border-0 bg-transparent p-0 text-caption text-accent-text cursor-pointer hover:underline"
                @click="openLog()"
              >
                查看准备日志
              </button>
            </div>
          </section>
        </div>

        <footer class="flex items-center gap-2 px-3.5 py-2.5 border-t border-line-hairline text-caption text-ink-mute">
          <span>{{ modKey }} / 随时打开本页</span>
          <span class="ml-auto flex items-center gap-1"
            ><CornerDownLeft :size="11" :stroke-width="1.5" /> 关闭：Esc</span
          >
        </footer>
      </div>
    </div>
  </Teleport>
</template>
