// Stylelint 配置（M6-1）：只做**正确性**门禁，格式化归 Prettier。
//
// 为什么不用 standard 集：它含大量格式类规则（空行/颜色函数写法/alpha 记法），
// 与 Prettier 的输出互相打架（实测 277 条里绝大多数是这类），两套规则只会制造噪音。
// 这里用 recommended 集（错拼 at-rule/属性、重复声明、非法值等真问题）+ 两处显式豁免。
export default {
  extends: ['stylelint-config-recommended'],
  rules: {
    // Tailwind v4 的 at-rule（@theme/@utility/@apply/@custom-variant…）不在规范集里，属正常用法
    'at-rule-no-unknown': [
      true,
      {
        ignoreAtRules: [
          'theme',
          'utility',
          'apply',
          'import',
          'source',
          'custom-variant',
          'variant',
          'reference',
          'plugin',
          'layer',
          'screen',
          'responsive',
          'tailwind'
        ]
      }
    ],
    // 层叠顺序是本项目 token 体系的有意设计（base → platform → theme → accent；
    // 焦点环需在静置阴影之后显式恢复），按选择器权重排序会破坏分层语义
    'no-descending-specificity': null
  }
}
