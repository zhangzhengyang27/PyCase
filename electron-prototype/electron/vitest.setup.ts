// vitest.setup.ts：组件测试的全局环境桩。
//
// 为什么需要「全局」而不是每个测试各自 mock：
//   store.ts 在模块顶层 `import { api } from './src/sidecar-client'`，而
//   sidecar-client.ts 又在模块顶层立刻读 `window.sidecar` 并调用
//   bridge.onStatus/onRunOutput/onRunFinished/onRunImages/onNotification。
//   也就是说：只要某个组件 import 了 '../store'，window.sidecar 就必须在
//   **模块求值之前**存在，否则 import 阶段直接 TypeError。
//   用 setupFiles 在所有测试文件之前装好桩，比在 22 个测试里各写一遍 vi.mock 更可靠，
//   也不会因为「某个测试忘了 mock」而整文件崩溃。
//
// 这里的桩是**惰性**的：默认所有方法返回 resolved undefined，测试需要断言调用时
// 用 vi.mocked(...) 或直接在测试内覆写 api.xxx —— 桩只保证「能 import、能跑」。
import { afterEach, vi } from 'vitest'
import { enableAutoUnmount } from '@vue/test-utils'

/** 与 src/preload/index.ts 的 SidecarAPI 保持同形的空实现。 */
function createSidecarStub() {
  const noopUnsub = () => {}
  const stub: Record<string, unknown> = {
    ping: vi.fn(async () => ({ ok: true })),
    listExamples: vi.fn(async () => []),
    getExample: vi.fn(async () => null),
    parseArgs: vi.fn(async () => []),
    saveExample: vi.fn(async () => ({ ok: true })),
    runExample: vi.fn(async () => ({ runId: 'stub-run' })),
    stopRun: vi.fn(async () => ({ ok: true })),
    uploadAsset: vi.fn(async () => ({ ok: true })),
    listAssets: vi.fn(async () => []),
    deleteAsset: vi.fn(async () => ({ ok: true })),
    downloadResultImage: vi.fn(async () => ({ ok: true })),
    saveTextFile: vi.fn(async () => ({ ok: true })),
    restart: vi.fn(async () => ({ ok: true })),

    pickDirectory: vi.fn(async () => null),
    scanImportSource: vi.fn(async () => ({ examples: [] })),
    importExamples: vi.fn(async () => ({ ok: true })),
    deleteExample: vi.fn(async () => ({ ok: true })),

    store: {
      get: vi.fn(async () => null),
      set: vi.fn(async () => ({ ok: true }))
    },

    ai: {
      getSettings: vi.fn(async () => ({})),
      setSettings: vi.fn(async () => ({ ok: true })),
      explain: vi.fn(async () => ({ ok: true })),
      stop: vi.fn(async () => ({ ok: true }))
    },

    app: {
      info: vi.fn(async () => ({ name: 'PyCase', version: '0.10.0', electron: '33.0.0' })),
      openLog: vi.fn(async () => ({ ok: true }))
    },

    env: {
      status: vi.fn(async () => ({
        phase: 'ready',
        mode: 'shared',
        venv_path: '/tmp/PyCase/.venv',
        venv_ready: true,
        python_version: '3.13.0',
        examples: 1496
      })),
      setRunEnv: vi.fn(async () => ({ phase: 'ready', mode: 'system' })),
      onProgress: vi.fn(() => noopUnsub)
    },

    win: {
      minimize: vi.fn(async () => ({ ok: true })),
      toggleMaximize: vi.fn(async () => true),
      close: vi.fn(async () => ({ ok: true })),
      isMaximized: vi.fn(async () => false),
      onMaximizedChange: vi.fn(() => noopUnsub)
    },

    onStatus: vi.fn(() => noopUnsub),
    onRunOutput: vi.fn(() => noopUnsub),
    onRunFinished: vi.fn(() => noopUnsub),
    onRunImages: vi.fn(() => noopUnsub),
    onNotification: vi.fn(() => noopUnsub)
  }
  return stub
}

// jsdom 未实现 PointerEvent（`'PointerEvent' in window === false`），
// 而 AppModal 的拖拽、以及任何手势类组件都依赖 pointerdown/pointermove。
// 用 MouseEvent 派生一个最小可用版本：clientX/clientY 由父类提供，
// 补上指针特有的 pointerId/pointerType/isPrimary 即可满足组件读取需求。
if (!('PointerEvent' in globalThis)) {
  class PointerEventPolyfill extends MouseEvent {
    readonly pointerId: number
    readonly pointerType: string
    readonly isPrimary: boolean

    constructor(type: string, params: PointerEventInit = {}) {
      super(type, params)
      this.pointerId = params.pointerId ?? 1
      this.pointerType = params.pointerType ?? 'mouse'
      this.isPrimary = params.isPrimary ?? true
    }
  }
  Object.defineProperty(globalThis, 'PointerEvent', {
    value: PointerEventPolyfill,
    writable: true,
    configurable: true
  })
}

// jsdom 未实现 IntersectionObserver，而 GalleryView 在 onMounted 里实例化它做触底加载。
// 这是个「空转」桩：observe/unobserve/disconnect 全为 no-op，**不会触发回调**。
// 因此它只保证 mount 不抛错；要验证「触底 → 加载更多」的用例必须自行替换本桩来驱动回调。
if (!('IntersectionObserver' in globalThis)) {
  class IntersectionObserverStub {
    readonly root = null
    readonly rootMargin = ''
    readonly thresholds: readonly number[] = []
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
    takeRecords(): IntersectionObserverEntry[] {
      return []
    }
  }
  Object.defineProperty(globalThis, 'IntersectionObserver', {
    value: IntersectionObserverStub,
    writable: true,
    configurable: true
  })
}

// jsdom 的 Blob 未实现异步读取方法（`typeof new File([], 'x').arrayBuffer === 'undefined'`），
// 而上传资源（store.uploadAssets）要经 File.arrayBuffer() 取二进制。
// 用 jsdom 已实现的 FileReader 兜底——补 Blob.prototype 即可同时覆盖 File。
function readBlob<T>(blob: Blob, method: 'readAsArrayBuffer' | 'readAsText'): Promise<T> {
  return new Promise<T>((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result as T)
    reader.onerror = () => reject(reader.error)
    reader[method](blob)
  })
}
if (typeof Blob.prototype.arrayBuffer !== 'function') {
  Blob.prototype.arrayBuffer = function (this: Blob): Promise<ArrayBuffer> {
    return readBlob<ArrayBuffer>(this, 'readAsArrayBuffer')
  }
}
if (typeof Blob.prototype.text !== 'function') {
  Blob.prototype.text = function (this: Blob): Promise<string> {
    return readBlob<string>(this, 'readAsText')
  }
}

// jsdom 未实现 matchMedia，主题解析（system 三态）会用到。
if (!window.matchMedia) {
  window.matchMedia = ((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false
  })) as unknown as typeof window.matchMedia
}

Object.defineProperty(window, 'sidecar', {
  value: createSidecarStub(),
  writable: true,
  configurable: true
})

// 自动卸载：@vue/test-utils 默认不会卸载已 mount 的组件，实例会跨用例存活，
// 其上仍挂着 store 的 watch——像 pendingBackfillTokens 这类「一次性」模块级 ref
// 会被上一个用例遗留的实例抢先消费，制造出「单例跑通过、整文件跑失败」的隐蔽串扰。
// 统一在每个用例结束后卸载，是这一整类问题的根治点。
enableAutoUnmount(afterEach)
