// tool-schemas-basics.ts：Python 语法实验室（bulk_basics 教学单例 7 家族归并单页）。
// 前端即时计算（text 结果）+ 抽屉给等价 pyCode——教的是语法本体，参数即语法要素。
// 画廊路由专用注册。
import type { FieldSpec, InteractiveToolSchema, ToolResult } from './interactive-tools'

export interface BasicsType {
  value: string
  label: string
  description: string
  fields: FieldSpec[]
  compute: (v: Record<string, unknown>) => ToolResult
  pyCode: (v: Record<string, unknown>) => string
}

const S = (key: string, label: string, def: string, opts: Array<[string, string]>, help?: string): FieldSpec => ({
  key, label, type: 'select', default: def, width: 'half',
  options: opts.map(([value, olabel]) => ({ value, label: olabel })), ...(help ? { help } : {})
})
const T = (key: string, label: string, def: string, help?: string): FieldSpec => ({
  key, label, type: 'text', default: def, width: 'half', ...(help ? { help } : {})
})

const NUMS = (raw: unknown): number[] =>
  String(raw ?? '')
    .split(',')
    .map((x) => Number(x.trim()))
    .filter((x) => Number.isFinite(x))

const P0 = (key: string, label: string, def: number): FieldSpec => ({
  key, label, type: 'number', default: def, width: 'half'
})

export const BASICS_TYPES: BasicsType[] = [
  {
    value: 'comprehension',
    label: '推导式',
    description: '列表推导式的「变换 + 过滤」组合：[表达式 for x in 序列 if 条件]。',
    fields: [
      T('data', '序列（逗号分隔数字）', '1,2,3,4,5,6,7,8'),
      S('expr', '变换', 'square', [['square', 'x*x'], ['double', 'x*2'], ['neg', '-x'], ['id', 'x 原样']]),
      S('cond', '过滤', 'even', [['none', '不过滤'], ['even', 'x 为偶数'], ['gt5', 'x > 5']])
    ],
    compute: (v) => {
      const nums = NUMS(v.data)
      if (!nums.length) return { error: '请输入数字序列' }
      const fns: Record<string, (x: number) => number> = {
        square: (x) => x * x, double: (x) => x * 2, neg: (x) => -x, id: (x) => x
      }
      const conds: Record<string, (x: number) => boolean> = {
        none: () => true, even: (x) => x % 2 === 0, gt5: (x) => x > 5
      }
      const out = nums.filter(conds[String(v.cond ?? 'even')]).map(fns[String(v.expr ?? 'square')])
      return { text: `[${out.join(', ')}]`, rows: [{ label: '输出个数', value: String(out.length) }] }
    },
    pyCode: (v) => `data = [${NUMS(v.data).join(', ')}]
exprs = {"square": lambda x: x * x, "double": lambda x: x * 2, "neg": lambda x: -x, "id": lambda x: x}
conds = {"none": lambda x: True, "even": lambda x: x % 2 == 0, "gt5": lambda x: x > 5}
out = [exprs[${JSON.stringify(String(v.expr ?? 'square'))}](x) for x in data if conds[${JSON.stringify(String(v.cond ?? 'even'))}](x)]
print(out)`
  },
  {
    value: 'decorator',
    label: '装饰器',
    description: '装饰器堆叠的调用顺序：@计时 @日志 包裹函数，先外后内。',
    fields: [S('stack', '装饰器组合', 'timer+logger', [['timer', '@timer'], ['logger', '@logger'], ['timer+logger', '@timer @logger'], ['logger+timer', '@logger @timer']])],
    compute: (v) => {
      const stack = String(v.stack ?? 'timer+logger')
      const names = stack.split('+')
      const enter = names.map((n) => `→ 进入 @${n} 包装`)
      const exit = [...names].reverse().map((n) => `← 离开 @${n}`)
      const flow = [...enter, '→ 执行原函数 work()', ...exit]
      return { text: flow.join('\n'), rows: [{ label: '装饰器层数', value: String(names.length) }] }
    },
    pyCode: (v) => {
      const stack = String(v.stack ?? 'timer+logger')
      const needTimer = stack.split('+').includes('timer')
      const needLog = stack.split('+').includes('logger')
      const defs = [
        needTimer
          ? 'import time, functools\ndef timer(fn):\n    @functools.wraps(fn)\n    def inner(*a, **kw):\n        t0 = time.perf_counter()\n        try:\n            return fn(*a, **kw)\n        finally:\n            print(f"[timer] {time.perf_counter() - t0:.4f}s")\n    return inner'
          : '',
        needLog
          ? 'def logger(fn):\n    @functools.wraps(fn)\n    def inner(*a, **kw):\n        print("[logger] 进入", fn.__name__)\n        r = fn(*a, **kw)\n        print("[logger] 离开", fn.__name__)\n        return r\n    return inner'
          : ''
      ]
        .filter(Boolean)
        .join('\n\n')
      const decs = stack
        .split('+')
        .map((n) => `@${n}`)
        .join('\n')
      return `${defs}\n\n${decs}\ndef work():\n    print("work 运行中")\n\nwork()`
    }
  },
  {
    value: 'generator',
    label: '生成器',
    description: 'yield 的惰性求值：逐次 next() 取值，取到多少算多少。',
    fields: [T('data', '序列', '1,2,3,4,5'), P0('take', '取前 K 个', 3)],
    compute: (v) => {
      const nums = NUMS(v.data)
      const take = Math.max(0, Math.trunc(Number(v.take) || 0))
      const taken = nums.slice(0, take)
      const lines = taken.map((x, i) => `next() #${i + 1} → yield ${x}`)
      if (take < nums.length) lines.push(`... 还有 ${nums.length - take} 个未消费（惰性，不计算）`)
      else if (take > nums.length) lines.push('next() 耗尽 → StopIteration')
      return { text: lines.join('\n') || '（空）' }
    },
    pyCode: (v) => `data = [${NUMS(v.data).join(', ')}]
take = ${Math.max(0, Math.trunc(Number(v.take) || 0))}

def gen(seq):
    for x in seq:
        yield x

g = gen(data)
for i in range(take):
    try:
        print(f"next() #{i + 1} -> {next(g)}")
    except StopIteration:
        print("StopIteration")`
  },
  {
    value: 'dataclass',
    label: 'dataclass',
    description: '@dataclass 从字段声明自动生成 __init__/__repr__。',
    fields: [T('spec', '字段（名:类型 逗号分隔）', 'name:str,price:float,stock:int')],
    compute: (v) => {
      const fields = String(v.spec ?? '')
        .split(',')
        .map((x) => x.trim())
        .filter((x) => x.includes(':'))
      if (!fields.length) return { error: '至少一个「名:类型」字段' }
      const repr = fields
        .map((f) => {
          const [name, type] = f.split(':')
          const sample = type === 'int' ? '3' : type === 'float' ? '9.5' : type === 'bool' ? 'True' : "'示例'"
          return `${name}=${sample}`
        })
        .join(', ')
      return { text: `Item(${repr})`, rows: [{ label: '字段数', value: String(fields.length) }] }
    },
    pyCode: (v) => {
      const fields = String(v.spec ?? '')
        .split(',')
        .map((x) => x.trim())
        .filter((x) => x.includes(':'))
        .map((f) => {
          const [name, type] = f.split(':')
          const py = { str: 'str', int: 'int', float: 'float', bool: 'bool' }[type.trim()] ?? 'str'
          return `    ${name.trim()}: ${py}`
        })
        .join('\n')
      return `from dataclasses import dataclass

@dataclass
class Item:
${fields}

print(Item(name='示例', price=9.5, stock=3))`
    }
  },
  {
    value: 'error-handling',
    label: '异常处理',
    description: 'try/except/else/finally 执行流：抛什么、接什么、谁必然执行。',
    fields: [
      S('exc', '抛出的异常', 'value', [['none', '不抛异常'], ['value', 'ValueError'], ['key', 'KeyError'], ['type', 'TypeError']]),
      S('catch', 'except 子句', 'value', [['value', 'except ValueError'], ['broad', 'except Exception'], ['none', '不接（向上抛）']])
    ],
    compute: (v) => {
      const exc = String(v.exc ?? 'value')
      const catch_ = String(v.catch ?? 'value')
      const flow = ['→ try 块开始']
      if (exc === 'none') {
        flow.push('→ try 块正常结束', '→ else 块（无异常才执行）')
        flow.push('→ finally 块（必然执行）')
      } else {
        flow.push(`→ 抛出 ${exc === 'value' ? 'ValueError' : exc === 'key' ? 'KeyError' : 'TypeError'}`)
        const caught = catch_ === 'broad' || (catch_ === 'value' && exc === 'value')
        flow.push(caught ? '→ except 命中，异常被处理' : '→ 没有匹配的 except → 向上传播')
        flow.push('→ finally 块（必然执行）')
      }
      return { text: flow.join('\n') }
    },
    pyCode: (v) => `exc = ${JSON.stringify(String(v.exc ?? 'value'))}
def risky():
    if exc == "value":
        raise ValueError("非法值")
    if exc == "key":
        raise KeyError("缺失键")
    if exc == "type":
        raise TypeError("类型错误")

try:
    risky()
except ValueError as e:
    print("except ValueError:", e)
except Exception as e:
    print("except Exception:", e)
else:
    print("else: 无异常")
finally:
    print("finally: 必然执行")`
  },
  {
    value: 'string-format',
    label: '字符串格式化',
    description: '%-format / str.format / f-string 三代格式化对照。',
    fields: [
      T('name', '名字', 'PyCase'),
      T('value', '数值', '42.5678'),
      S('spec', '数值格式', '.2f', [['.2f', '两位小数'], ['.0f', '整数'], ['10.2f', '右对齐宽 10'], ['>10', '右对齐字符串']]),
      S('style', '展示风格', 'all', [['all', '三代对照'], ['f', '仅 f-string'], ['pct', '仅 %-format']])
    ],
    compute: (v) => {
      const name = String(v.name ?? 'PyCase')
      const num = Number(v.value)
      if (!Number.isFinite(num)) return { error: '数值不合法' }
      const spec = String(v.spec ?? '.2f')
      const pct = spec.endsWith('f') ? `%${spec}` : '%s'
      const pctVal = spec.endsWith('f') ? num.toFixed(Number(spec.split('.')[1]?.split('f')[0] ?? 2)) : String(num)
      const fstr =
        spec === '.2f'
          ? `${num.toFixed(2)}`
          : spec === '.0f'
            ? `${Math.round(num)}`
            : spec === '10.2f'
              ? num.toFixed(2).padStart(10)
              : name.padStart(10)
      const lines = [
        `%-format : "%s 的值是 ${pct}" % ("${name}", ${pctVal})  →  ${name} 的值是 ${pctVal}`,
        `format() : "{} 的值是 {:${spec}}".format("${name}", ${num})  →  ${name} 的值是 ${fstr}`,
        `f-string : f"${name} 的值是 {${num}:${spec}}"  →  ${name} 的值是 ${fstr}`
      ]
      const style = String(v.style ?? 'all')
      return {
        text: style === 'all' ? lines.join('\n') : style === 'f' ? lines[2]! : lines[0]!
      }
    },
    pyCode: (v) => `name = ${JSON.stringify(String(v.name ?? 'PyCase'))}
value = ${Number(v.value) || 0}
print("%s 的值是 %.2f" % (name, value))
print("{} 的值是 {:${String(v.spec ?? '.2f')}}".format(name, value))
print(f"{name} 的值是 {value:${String(v.spec ?? '.2f')}}")`
  },
  {
    value: 'pathlib',
    label: 'pathlib 路径',
    description: 'Path 的 glob 模式匹配与常用属性（对合成目录树演示）。',
    fields: [
      S('glob', 'glob 模式', '*.py', [['*.py', '*.py'], ['data*/*', 'data*/*'], ['**/*.txt', '**/*.txt（递归）']]),
      S('show', '展示', 'name', [['name', '文件名'], ['stem', '主名'], ['suffix', '后缀']])
    ],
    compute: (v) => {
      const tree = ['main.py', 'utils.py', 'data/train.csv', 'data/test.csv', 'docs/readme.txt', 'notes.txt']
      const glob = String(v.glob ?? '*.py')
      const show = String(v.show ?? 'name')
      const match = (p: string): boolean => {
        if (glob === '*.py') return p === p.split('/').pop() && p.endsWith('.py')
        if (glob === 'data*/*') return p.startsWith('data/')
        return p.endsWith('.txt')
      }
      const hits = tree.filter(match).map((p) => {
        if (show === 'stem') return p.split('/').pop()!.replace(/\.[^.]+$/, '')
        if (show === 'suffix') return p.includes('.') ? '.' + p.split('.').pop()! : ''
        return p.split('/').pop()!
      })
      return { text: hits.join('\n') || '（无匹配）', rows: [{ label: '命中', value: String(hits.length) }] }
    },
    pyCode: (v) => `from pathlib import Path

root = Path("project")
tree = ["main.py", "utils.py", "data/train.csv", "data/test.csv", "docs/readme.txt", "notes.txt"]
for rel in tree:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.touch()

for p in sorted(root.rglob("*")):
    if p.match(${JSON.stringify(String(v.glob ?? '*.py'))}):
        print(p.${String(v.show ?? 'name')})`
  }
]

// ---------------------------------------------------------------------------
// 语法实验室：7 家族归并单页
// ---------------------------------------------------------------------------
const BASICS_TYPE_FIELD: FieldSpec = {
  key: 'type',
  label: '语法主题',
  type: 'select',
  default: 'comprehension',
  width: 'full',
  options: BASICS_TYPES.map((t) => ({ value: t.value, label: t.label }))
}

export const basicsLabSchema: InteractiveToolSchema = {
  id: 'interactive:basics-lab',
  title: 'Python 语法实验室',
  description: '推导式 / 装饰器 / 生成器 / dataclass / 异常处理 / 字符串格式化 / pathlib——改参数看执行流，抽屉给等价脚本。',
  tags: ['语法', '教学'],
  fields: (v) => {
    const t = BASICS_TYPES.find((x) => x.value === v.type) ?? BASICS_TYPES[0]!
    return [BASICS_TYPE_FIELD, ...t.fields]
  },
  compute: (v) => {
    const t = BASICS_TYPES.find((x) => x.value === v.type) ?? BASICS_TYPES[0]!
    return t.compute(v)
  },
  headerFor: (v) => {
    const t = BASICS_TYPES.find((x) => x.value === v.type) ?? BASICS_TYPES[0]!
    return { title: t.label, description: t.description }
  },
  pyCode: (v) => {
    const t = BASICS_TYPES.find((x) => x.value === v.type) ?? BASICS_TYPES[0]!
    return t.pyCode(v)
  }
}
