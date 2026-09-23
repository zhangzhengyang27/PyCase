/** @type {import('tailwindcss').Config} */
// 颜色/阴影全部指向 style.css 的 :root 设计令牌（CSS 变量），
// 这样 dark/light（[data-theme]）切换对 Tailwind 工具类同样生效。
export default {
  content: [
    './src/renderer/index.html',
    './src/renderer/src/**/*.{ts,js}'
  ],
  theme: {
    extend: {
      colors: {
        // 表面（背景）
        page: 'var(--bg-marketing)',     // 窗口最底色
        panel: 'var(--bg-panel)',        // 工具栏/侧栏/面板
        card: 'var(--bg-level3)',        // 卡片、激活分段
        surface: 'var(--bg-secondary)',  // hover 后的次级表面
        hover: 'var(--bg-hover)',        // 半透明 hover 覆盖层
        inset: 'var(--bg-inset)',        // 输出终端内嵌背景
        // 前景（文字）
        ink: {
          DEFAULT: 'var(--text-primary)',
          dim: 'var(--text-secondary)',
          mute: 'var(--text-tertiary)',
          faint: 'var(--text-quaternary)'
        },
        // 品牌与强调
        accent: {
          DEFAULT: 'var(--brand-indigo)',
          violet: 'var(--accent-violet)',
          hover: 'var(--accent-hover)',
          ring: 'var(--accent-ring)'
        },
        // 状态
        ok: 'var(--status-green)',
        danger: 'var(--status-red)',
        warn: 'var(--status-amber)',
        // 边框分隔线
        line: {
          DEFAULT: 'var(--border-standard)',
          subtle: 'var(--border-subtle)',
          strong: 'var(--border-primary)',
          mid: 'var(--border-secondary)',
          deep: 'var(--border-tertiary)',
          tint: 'var(--line-tint)'
        }
      },
      boxShadow: {
        'elev-1': 'var(--elevation-1)',
        'elev-2': 'var(--elevation-2)',
        'elev-3': 'var(--elevation-3)',
        'elev-focus': 'var(--elevation-focus)',
        'elev-inset': 'var(--elevation-inset)'
      },
      fontFamily: {
        sans: ['"Inter Variable"', '"Inter"', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', '"PingFang SC"', '"Hiragino Sans GB"', '"Microsoft YaHei"', 'sans-serif'],
        mono: ['"Berkeley Mono"', '"JetBrains Mono"', '"Fira Code"', '"SF Mono"', 'Consolas', 'monospace']
      },
      keyframes: {
        // 覆盖内置 pulse：状态点呼吸（0.35/0.4 取后者，与原 CSS 末位定义一致）
        pulse: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.4' }
        }
      },
      animation: {
        pulse: 'pulse 1.5s infinite'
      }
    }
  },
  plugins: [],
  corePlugins: {
    preflight: false // 保持关闭：应用自带精简 reset，避免与既有样式冲突
  }
}
