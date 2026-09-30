<script setup lang="ts">
// AppModal：轻量弹窗（ElDialog 替代）：backdrop 点击 / Esc 关闭，180ms 面板动效，
// 头部可拖拽移动（边界钳制在视口内，关闭按钮等控件不触发拖拽）。
// 焦点管理：打开时聚焦面板、Tab 在弹窗内循环、关闭后归还触发点焦点。
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
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

function focusablesIn(panel: HTMLElement): HTMLElement[] {
  return Array.from(
    panel.querySelectorAll<HTMLElement>('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])')
  ).filter((el) => !el.hasAttribute('disabled') && el.offsetParent !== null)
}

function onKey(e: KeyboardEvent): void {
  if (e.key === 'Escape') {
    emit('close')
    return
  }
  if (e.key !== 'Tab' || !panelRef.value) return
  const focusables = focusablesIn(panelRef.value)
  if (focusables.length === 0) {
    e.preventDefault()
    panelRef.value.focus()
    return
  }
  const first = focusables[0]
  const last = focusables[focusables.length - 1]
  const active = document.activeElement
  if (e.shiftKey && (active === first || active === panelRef.value)) {
    e.preventDefault()
    last.focus()
  } else if (!e.shiftKey && (active === last || active === document.body || active === null)) {
    e.preventDefault()
    first.focus()
  }
}

function onHeaderDown(e: PointerEvent): void {
  const el = panelRef.value
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

onMounted(() => {
  prevFocus = document.activeElement as HTMLElement | null
  window.addEventListener('keydown', onKey)
  void nextTick(() => panelRef.value?.focus())
})
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKey)
  onPointerUp()
  prevFocus?.focus?.()
})
</script>

<template>
  <Teleport to="body">
    <div class="scrim z-[1000] flex items-center justify-center p-6" @click.self="emit('close')">
      <div
        ref="panelRef"
        role="dialog"
        aria-modal="true"
        :aria-label="title"
        tabindex="-1"
        class="bg-panel border border-line-hairline rounded-overlay shadow-elev-3 max-w-[92vw] max-h-[86vh] flex flex-col animate-modal-in outline-none"
        :style="{ width: width, transform: `translate(${dx}px, ${dy}px)` }"
      >
        <div
          class="flex items-center justify-between px-4 h-11 border-b border-line-hairline shrink-0 select-none"
          :class="draggable ? 'cursor-grab active:cursor-grabbing' : ''"
          @pointerdown="draggable && onHeaderDown($event)"
        >
          <span class="text-title font-semibold text-ink">{{ title }}</span>
          <button
            class="w-6 h-6 flex items-center justify-center rounded-control text-ink-mute hover:text-ink hover:bg-hover cursor-pointer border-0 bg-transparent"
            title="关闭"
            aria-label="关闭"
            @click="emit('close')"
          >
            <X :size="14" />
          </button>
        </div>
        <div class="px-4 py-3.5 overflow-y-auto overscroll-contain">
          <slot />
        </div>
        <div v-if="$slots.footer" class="flex justify-end gap-2 px-4 py-3 border-t border-line-hairline shrink-0">
          <slot name="footer" />
        </div>
      </div>
    </div>
  </Teleport>
</template>
