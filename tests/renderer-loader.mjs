// 渲染层 TS 模块测试加载器（供 tests/test_*.mjs 共用）
//
// 渲染层已是 vite + TypeScript + ESM，且模块间按 bundler 风格省略扩展名互相导入。
// 本加载器用 electron 工程自带的 typescript 把目标模块转译为 CommonJS，在受控的
// require 环境中执行：
//   - 相对导入按「导入文件所在目录」解析（与 bundler 语义一致），因此渲染层根目录的
//     store.ts 与 src/ 下的纯函数模块都能被加载；
//   - 纯模块（filter-engine / utils / store 等）加载真实源码；
//   - 带 DOM/IPC 副作用的模块（'./toast'、'./src/sidecar-client' 等）由测试通过
//     mocks 注入替身，避免拉起 document/monaco/electron 依赖图；
//   - 裸模块默认一律报错（守卫语义），确需真实包时用 options.packages 显式放行
//     （如 store.ts 需要真实的 'vue' 提供 ref/computed 响应式）。
// 需要 electron-prototype/electron 下已安装依赖（CI 对应 job 会先 npm ci）。
import { existsSync, readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import { dirname, join, relative } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ELECTRON_DIR = join(__dirname, "..", "electron-prototype", "electron");
const RENDERER_DIR = join(ELECTRON_DIR, "src", "renderer");
const RENDERER_SRC = join(RENDERER_DIR, "src");

const ts = createRequire(join(ELECTRON_DIR, "package.json"))("typescript");

/**
 * 创建一个渲染层模块加载器。
 * @param {Record<string, object>} [mocks] 模块说明符（如 './toast'）→ 替身 module.exports
 * @param {{ packages?: string[] }} [options] packages：允许从工程 node_modules 真实加载的
 *   裸模块名（如 'vue'）。默认空数组——未列入白名单的裸模块一律报错，避免测试无意中
 *   拉起未 mock 的副作用依赖图。
 * @returns {{ load: (name: string) => object }} load('filter-engine') 或 load('store')
 *   返回该模块 exports；name 相对渲染层根目录（省略扩展名）。
 */
export function createRendererLoader(mocks = {}, options = {}) {
  const cache = new Map();
  const allowedPackages = options.packages || [];
  const nodeRequire = createRequire(join(ELECTRON_DIR, "package.json"));

  function fileFor(rel) {
    const candidates = [join(RENDERER_DIR, `${rel}.ts`), join(RENDERER_SRC, `${rel}.ts`)];
    for (const c of candidates) {
      if (existsSync(c)) return c;
    }
    throw new Error(`renderer-loader: 找不到模块 ${rel}.ts`);
  }

  function resolve(spec, fromDir) {
    if (Object.prototype.hasOwnProperty.call(mocks, spec)) {
      return mocks[spec];
    }
    if (!spec.startsWith(".")) {
      if (allowedPackages.includes(spec)) {
        return nodeRequire(spec);
      }
      throw new Error(
        `renderer-loader: 模块导入 "${spec}" 既未 mock 也不是相对导入；` +
          `如为新的副作用依赖，请在测试的 mocks 中提供替身`
      );
    }
    const rel = relative(RENDERER_DIR, join(fromDir, spec)).replace(/\.ts$/, "");
    return load(rel);
  }

  function load(rel) {
    // 缓存里存的是 module 包装对象（为了循环导入时能拿到部分填充的 exports），
    // 对外必须返回 module.exports —— 否则 require 拿到的是 {exports:{...}} 外壳，
    // 被依赖方访问具名导出会得到 undefined。
    if (cache.has(rel)) return cache.get(rel).exports;
    const file = fileFor(rel);
    const js = ts
      .transpileModule(readFileSync(file, "utf-8"), {
        compilerOptions: {
          module: ts.ModuleKind.CommonJS,
          target: ts.ScriptTarget.ES2022,
          esModuleInterop: true
        },
        fileName: file
      }).outputText;
    // 先入缓存再执行，兼容模块间循环导入（执行中再次 load 返回部分填充的 exports）
    const module = { exports: {} };
    cache.set(rel, module);
    new Function("require", "module", "exports", "__filename", js)(
      (spec) => resolve(spec, dirname(file)),
      module,
      module.exports,
      file
    );
    return module.exports;
  }

  return { load };
}
