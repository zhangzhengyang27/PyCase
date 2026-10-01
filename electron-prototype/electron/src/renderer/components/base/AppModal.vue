<script setup lang="ts">
// AppModal：轻量弹窗（reka-ui Dialog 底座）——遮罩点击 / Esc 关闭、焦点圈定与
// 背景滚动锁由 reka-ui 承担；头部可拖拽移动（边界钳制在视口内，关闭按钮等
// 控件不触发拖拽）是本组件自留的唯一行为。
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { DialogClose, DialogContent, DialogOverlay, DialogPortal, DialogRoot, DialogTitle } from 'reka-ui'
import { X } from 'lucide-vue-next'

withDefaults(defineProps<{ title: string; width?: string; draggable?: boolean }>(), {
  width: '440px',
  draggable: true
})
const emit = defineEmits<{ close: [] }>()

const panelRef = ref<HTMLElement | null>(null)
const dx = ref(0)
const dy = ref(0)
let dragging = false
let startPointer = { x: 0, y: 0 }
let startOffset = { x: 0, y: 0 }
let startRect = { left: 0, top: 0, width: 0, height: 0 }
let prevFocus: HTMLElement | null = null

// reka-ui 的 ref 经 Primitive 落到 DOM 元素；兜底一层 $el（以防版本行为变化）
function panelEl(): HTMLElement | null {
  const v = panelRef.value as HTMLElement | { $el?: HTMLElement } | null
  if (!v) return null
  return v instanceof HTMLElement ? v : (v.$el ?? null)
}

function onHeaderDown(e: PointerEvent): void {
  const el = panelEl()
  if (!el || (e.target as HTMLElement).closest('button')) return
  dragging = true
  startPointer = { x: e.clientX, y: e.clientY }
  startOffset = { x: dx.value, y: dy.value }
  const rect = el.getBoundingClientRect()
  startRect = { left: rect.left, top: rect.top, width: rect.width, height: rect.height }
  window.addEventListener('pointermove', onPointerMove)
  window.addEventListener('pointerup', onPointerUp)
}

function onPointerMove(e: PointerEvent): void {
  if (!dragging) return
  // 钳制：面板至少留 16px 在视口内，拖拽不丢失
  const vw = window.innerWidth
  const vh = window.innerHeight
  const minX = 16 - startRect.left - startRect.width
  const maxX = vw - 16 - startRect.left
  const minY = 16 - startRect.top
  const maxY = vh - 48 - startRect.top
  dx.value = Math.min(maxX, Math.max(minX, startOffset.x + (e.clientX - startPointer.x)))
  dy.value = Math.min(maxY, Math.max(minY, startOffset.y + (e.clientY - startPointer.y)))
}

function onPointerUp(): void {
  dragging = false
  window.removeEventListener('pointermove', onPointerMove)
  window.removeEventListener('pointerup', onPointerUp)
}

// 关闭由父级 v-if 卸载本组件完成：reka-ui 的「归还焦点」挂在 open→false 过渡上，
// 覆盖不到卸载路径，这里自己记录并归还。
onMounted(() => {
  prevFocus = document.activeElement as HTMLElement | null
})
onBeforeUnmount(() => {
  onPointerUp()
  prevFocus?.focus?.()
})
</script>

<template>
  <DialogRoot :open="true" @update:open="(v: boolean) => !v && emit('close')">
    <DialogPortal>
      <DialogOverlay class="scrim z-[1000]" />
      <DialogContent
        ref="panelRef"
        :aria-label="title"
        aria-modal="true"
        :aria-describedby="undefined"
        class="fixed left-1/2 top-1/2 z-[1000] flex max-h-[86vh] max-w-[92vw] flex-col bg-panel border border-line-hairline rounded-overlay shadow-elev-3 outline-none animate-modal-in"
        :style="{ width: width, transform: `translate(-50%, -50%) translate(${dx}px, ${dy}px)` }"
      >
        <div
          class="flex items-center justify-between px-4 h-11 border-b border-line-hairline shrink-0 select-none"
          :class="draggable ? 'cursor-grab active:cursor-grabbing' : ''"
          @pointerdown="draggable && onHeaderDown($event)"
        >
          <DialogTitle as="span" class="text-title font-semibold text-ink">{{ title }}</DialogTitle>
          <DialogClose
            class="w-6 h-6 flex items-center justify-center rounded-control text-ink-mute hover:text-ink hover:bg-hover cursor-pointer border-0 bg-transparent"
            title="关闭"
            aria-label="关闭"
          >
            <X :size="14" />
          </DialogClose>
        </div>
        <div class="px-4 py-3.5 overflow-y-auto overscroll-contain">
          <slot />
        </div>
        <div v-if="$slots.footer" class="flex justify-end gap-2 px-4 py-3 border-t border-line-hairline shrink-0">
          <slot name="footer" />
        </div>
      </DialogContent>
    </DialogPortal>
  </DialogRoot>
</template>
