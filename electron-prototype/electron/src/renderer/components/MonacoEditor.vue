<script setup lang="ts">
// MonacoEditor：单例编辑器封装（v0.10 详情页源码区；由旧渲染层组件适配而来，
// 实例经 store.registerEditor 注册，内容变更回调判定 isDirty）
// value 变化（切换示例）经 watch 同步 setValue；内容变更回调到 store 判定 isDirty。
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { applyMonacoTheme, currentMonacoTheme, monaco } from '../monaco'
import { onEditorContentChanged, originalCode, registerEditor, selectedId } from '../src/store/detail'

// 占位串只属于「未选中任何示例」：已选中时即使源码还在拉取（或拉取失败）也保持空白，
// 否则用户会看到「请选择示例」——正是「详情页代码块全空白」的观感来源。
const PLACEHOLDER = '# 在画廊或工具箱中选择示例查看与编辑代码\n'

const container = ref<HTMLDivElement | null>(null)
let editor: monaco.editor.IStandaloneCodeEditor | null = null

onMounted(() => {
  if (!container.value) return
  applyMonacoTheme()
  editor = monaco.editor.create(container.value, {
    value: selectedId.value ? originalCode.value : originalCode.value || PLACEHOLDER,
    language: 'python',
    theme: currentMonacoTheme(),
    fontSize: 13,
    fontLigatures: true,
    minimap: { enabled: true, renderCharacters: false },
    scrollBeyondLastLine: false,
    smoothScrolling: true,
    cursorBlinking: 'smooth',
    renderWhitespace: 'selection',
    tabSize: 4,
    insertSpaces: true,
    automaticLayout: true,
    readOnly: false,
    wordWrap: 'on',
    padding: { top: 8, bottom: 8 }
  })
  editor.onDidChangeModelContent(() => {
    if (selectedId.value) onEditorContentChanged(editor!.getValue())
  })
  registerEditor({ getValue: () => editor!.getValue(), setValue: (v: string) => editor!.setValue(v) })
})

// 切换示例：装载新代码（plain setValue，与旧行为一致）
watch(originalCode, (v) => {
  if (editor && editor.getValue() !== v) editor.setValue(v || '')
})

onBeforeUnmount(() => {
  editor?.dispose()
  editor = null
})
</script>

<template>
  <div ref="container" class="absolute inset-0"></div>
</template>
