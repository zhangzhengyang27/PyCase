// 渲染层 TS 模块测试加载器（供 test_filter_engine.mjs / test_renderer_utils.mjs 共用）
//
// 渲染层已是 vite + TypeScript + ESM（src/renderer/src/*.ts），且模块间按 bundler
// 风格省略扩展名互相导入。本加载器用 electron 工程自带的 typescript 把目标模块
// 转译为 CommonJS，在受控的 require 环境中执行：
//   - 纯模块（filter-engine / utils 等）加载真实源码；
//   - 带 DOM/IPC 副作用的模块（'./state'、'./app'、'./sidecar-client'）由测试
//     通过 mocks 注入替身，避免拉起 document/monaco/electron 依赖图。
// 需要 electron-prototype/electron 下已安装依赖（CI 对应 job 会先 npm ci）。
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ELECTRON_DIR = join(__dirname, "..", "electron-prototype", "electron");
const RENDERER_SRC = join(ELECTRON_DIR, "src", "renderer", "src");

const ts = createRequire(join(ELECTRON_DIR, "package.json"))("typescript");

/**
 * 创建一个渲染层模块加载器。
 * @param {Record<string, object>} [mocks] 模块说明符（如 './state'）→ 替身 module.exports
 * @returns {{ load: (name: string) => object }} load('filter-engine') 返回该模块 exports
 */
export function createRendererLoader(mocks = {}) {
  const cache = new Map();

  function resolve(spec) {
    if (Object.prototype.hasOwnProperty.call(mocks, spec)) {
      return mocks[spec];
    }
    if (!spec.startsWith(".")) {
      throw new Error(
        `renderer-loader: 模块导入 "${spec}" 既未 mock 也不是相对导入；` +
          `如为新的副作用依赖，请在测试的 mocks 中提供替身`
      );
    }
    return load(spec.replace(/^\.\//, "").replace(/\.ts$/, ""));
  }

  function load(name) {
    if (cache.has(name)) return cache.get(name);
    const file = join(RENDERER_SRC, `${name}.ts`);
    const js = ts
      .transpileModule(readFileSync(file, "utf-8"), {
        compilerOptions: {
          module: ts.ModuleKind.CommonJS,
          target: ts.ScriptTarget.ES2022,
          esModuleInterop: true
        },
        fileName: `${name}.ts`
      }).outputText;
    // 先入缓存再执行，兼容模块间循环导入（执行中再次 load 返回部分填充的 exports）
    const module = { exports: {} };
    cache.set(name, module);
    new Function("require", "module", "exports", "__filename", js)(
      (spec) => resolve(spec),
      module,
      module.exports,
      file
    );
    return module.exports;
  }

  return { load };
}
