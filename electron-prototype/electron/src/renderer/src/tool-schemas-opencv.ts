// tool-schemas-opencv.ts：bulk_opencv 25 处理家族交互页（21 个 8 变体家族 + 5 个单例家族
// = 166 变体归并）。变体 = 合成场景 + cv2 处理链 + 参数逐档；页面 = 同场景 + 同处理链 +
// 参数可调，语义与 bulk_opencv 同源。画廊路由专用注册（interactiveGallerySchemas）。
import type { FieldSpec, InteractiveToolSchema } from './interactive-tools'

const CV_HEAD = `import json
import cv2
import numpy as np

# 合成场景：矩形 + 圆 + 斜线 + 方块（处理效果可辨识），与 bulk_opencv 变体同思路
img = np.zeros((360, 480), dtype=np.uint8)
cv2.rectangle(img, (60, 60), (200, 200), 200, -1)
cv2.circle(img, (340, 140), 80, 140, -1)
cv2.line(img, (40, 300), (440, 320), 220, 6)
cv2.rectangle(img, (240, 220), (400, 330), 90, -1)
`

const CV_OUT = `cv2.imwrite("effect.png", result if result is not None else img)
print("已输出 effect.png")
print("<<<JSON>>>")
print(json.dumps({"rows": [{"label": "产物", "value": "effect.png", "copy": True}]}, ensure_ascii=False))
print("<<<END>>>")
`

export interface CvOp {
  value: string
  label: string
  description: string
  fields: FieldSpec[]
  body: (v: Record<string, unknown>) => string
}

const cvFamily = (
  value: string,
  label: string,
  description: string,
  fields: FieldSpec[],
  body: (v: Record<string, unknown>) => string
): CvOp => ({ value, label, description, fields, body })


const P = (key: string, label: string, def: number, help?: string) => ({
  key, label, type: 'number' as const, default: def, width: 'half' as const, ...(help ? { help } : {})
})

const SEL = (key: string, label: string, def: string, opts: Array<[string, string]>) => ({
  key, label, type: 'select' as const, default: def, width: 'half' as const,
  options: opts.map(([value, olabel]) => ({ value, label: olabel }))
})

export const CV_OPS: CvOp[] = [
  cvFamily('canny', 'Canny 边缘',
    '高斯去噪 + 双阈值边缘提取（canny 家族）。',
    [P('t1', '低阈值', 100), P('t2', '高阈值', 200)],
    (v) => `blur = cv2.GaussianBlur(img, (5, 5), 0)
result = cv2.Canny(blur, ${Math.trunc(Number(v.t1) || 100)}, ${Math.trunc(Number(v.t2) || 200)})`),
  cvFamily('threshold', '阈值二值化',
    '全局阈值 / Otsu 自动阈值（threshold 家族）。',
    [P('th', '阈值', 127), SEL('mode', '模式', 'binary', [['binary', 'BINARY'], ['otsu', 'OTSU 自动'], ['tri', 'TRIANGLE 自动']])],
    (v) => `mode = ${JSON.stringify(String(v.mode ?? 'binary'))}
th = ${Math.trunc(Number(v.th) || 127)}
if mode == "binary":
    _, result = cv2.threshold(img, th, 255, cv2.THRESH_BINARY)
else:
    flag = cv2.THRESH_OTSU if mode == "otsu" else cv2.THRESH_TRIANGLE
    _, result = cv2.threshold(img, th, 255, cv2.THRESH_BINARY + flag)`),
  cvFamily('adaptive', '自适应阈值',
    '局部均值 / 高斯加权的自适应阈值（adaptive 家族）。',
    [P('block', '邻域块大小', 21, '奇数'), P('c', '偏移 C', 5)],
    (v) => `block = max(3, ${Math.trunc(Number(v.block) || 21)} | 1)
result = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, block, ${Math.trunc(Number(v.c) || 5)})`),
  cvFamily('morph-open', '形态学开运算',
    '腐蚀再膨胀，去小白点（morph-open 家族）。',
    [P('k', '核大小', 5)],
    (v) => `k = max(1, ${Math.trunc(Number(v.k) || 5)})
kernel = np.ones((k, k), np.uint8)
result = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)`),
  cvFamily('morph-close', '形态学闭运算',
    '膨胀再腐蚀，填小黑洞（morph-close 家族）。',
    [P('k', '核大小', 5)],
    (v) => `k = max(1, ${Math.trunc(Number(v.k) || 5)})
kernel = np.ones((k, k), np.uint8)
result = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel)`),
  cvFamily('gradient', '形态学梯度',
    '膨胀 - 腐蚀 = 边缘（gradient 家族）。',
    [P('k', '核大小', 5)],
    (v) => `k = max(1, ${Math.trunc(Number(v.k) || 5)})
kernel = np.ones((k, k), np.uint8)
result = cv2.morphologyEx(img, cv2.MORPH_GRADIENT, kernel)`),
  cvFamily('sobel', 'Sobel 梯度',
    'x/y 方向一阶导数幅值（sobel 家族）。',
    [P('k', '核大小', 3)],
    (v) => `k = min(7, max(1, ${Math.trunc(Number(v.k) || 3)} | 1))
gx = cv2.Sobel(img, cv2.CV_64F, 1, 0, ksize=k)
gy = cv2.Sobel(img, cv2.CV_64F, 0, 1, ksize=k)
result = cv2.convertScaleAbs(np.sqrt(gx ** 2 + gy ** 2))`),
  cvFamily('laplacian', 'Laplacian 边缘',
    '二阶导数算子（laplacian 家族）。',
    [P('k', '核大小', 3)],
    (v) => `k = min(7, max(1, ${Math.trunc(Number(v.k) || 3)} | 1))
result = cv2.convertScaleAbs(cv2.Laplacian(img, cv2.CV_64F, ksize=k))`),
  cvFamily('blur-stack', '高斯模糊栈',
    '核尺寸逐级加大的模糊（blur-stack 家族）。',
    [P('k', '核大小', 9)],
    (v) => `k = max(1, ${Math.trunc(Number(v.k) || 9)} | 1)
result = cv2.GaussianBlur(img, (k, k), 0)`),
  cvFamily('sharpen', '锐化',
    '卷积核锐化（sharpen 家族）。',
    [P('amount', '锐化量', 1.0)],
    (v) => `amount = max(0.1, ${Number(v.amount) || 1})
kernel = np.array([[0, -1, 0], [-1, 4 + amount, -1], [0, -1, 0]], dtype=np.float64)
result = cv2.filter2D(img, -1, kernel)`),
  cvFamily('equalize', '直方图均衡',
    'equalizeHist 对比度均衡（equalize 家族）。',
    [],
    () => `result = cv2.equalizeHist(img)`),
  cvFamily('gamma', 'Gamma 校正',
    'LUT 查表伽马变换（gamma 家族）。',
    [P('gamma', '伽马值', 0.5, '<1 提亮 >1 压暗')],
    (v) => `gamma = max(0.05, ${Number(v.gamma) || 0.5})
lut = (np.arange(256) / 255.0) ** (1.0 / gamma) * 255
result = cv2.LUT(img, lut.astype(np.uint8))`),
  cvFamily('rotate', '旋转',
    '仿射旋转 + 缩放（rotate 家族）。',
    [P('angle', '角度', 30), P('scale', '缩放', 1.0)],
    (v) => `h, w = img.shape[:2]
M = cv2.getRotationMatrix2D((w / 2, h / 2), ${Number(v.angle) || 0}, ${Number(v.scale) || 1})
result = cv2.warpAffine(img, M, (w, h))`),
  cvFamily('perspective', '透视变换',
    '四点透视 warp（perspective 家族）。',
    [P('skew', '斜切量', 60)],
    (v) => `h, w = img.shape[:2]
skew = ${Math.trunc(Number(v.skew) || 60)}
src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
dst = np.float32([[skew, 0], [w - skew, 0], [w, h], [0, h]])
result = cv2.warpPerspective(img, cv2.getPerspectiveTransform(src, dst), (w, h))`),
  cvFamily('resize-pyramid', '金字塔缩放',
    'pyrDown / pyrUp 金字塔采样（resize-pyramid 家族）。',
    [P('level', '金字塔层数', 2)],
    (v) => `small = img
for _ in range(${Math.max(1, Math.trunc(Number(v.level) || 2))}):
    small = cv2.pyrDown(small)
result = small
for _ in range(${Math.max(1, Math.trunc(Number(v.level) || 2))}):
    result = cv2.pyrUp(result)
result = cv2.resize(result, (480, 360))`),
  cvFamily('contours-area', '轮廓面积筛选',
    'findContours + 按面积过滤绘制（contours-area 家族）。',
    [P('min-area', '最小面积', 500)],
    (v) => `_, thresh = cv2.threshold(img, 60, 255, cv2.THRESH_BINARY)
cnts, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
result = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
kept = 0
for c in cnts:
    if cv2.contourArea(c) >= ${Math.trunc(Number(v['min-area']) || 500)}:
        cv2.drawContours(result, [c], -1, (0, 200, 255), 2)
        kept += 1
print(f"保留轮廓 {kept} 个")`),
  cvFamily('hough-lines', '霍夫直线',
    '概率霍夫变换检线（hough-lines 家族）。',
    [P('th', '累加器阈值', 80), P('min-len', '最短线长', 50)],
    (v) => `edges = cv2.Canny(img, 50, 150)
lines = cv2.HoughLinesP(edges, 1, np.pi / 180, ${Math.trunc(Number(v.th) || 80)}, minLineLength=${Math.trunc(Number(v['min-len']) || 50)}, maxLineGap=10)
result = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
count = 0
if lines is not None:
    for x1, y1, x2, y2 in lines.reshape(-1, 4)[:40]:
        cv2.line(result, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), 2)
        count += 1
print(f"检出直线 {count} 条")`),
  cvFamily('distance-transform', '距离变换',
    '前景像素到背景的距离场（distance-transform 家族）。',
    [],
    () => `_, th = cv2.threshold(img, 60, 255, cv2.THRESH_BINARY)
result = cv2.normalize(cv2.distanceTransform(th, cv2.DIST_L2, 5), None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)`),
  cvFamily('bitwise-mix', '位运算合成',
    'AND/OR/XOR 与几何掩码合成（bitwise-mix 家族）。',
    [SEL('op', '运算', 'and', [['and', 'AND'], ['or', 'OR'], ['xor', 'XOR']])],
    (v) => `mask = np.zeros_like(img)
cv2.circle(mask, (240, 180), 110, 255, -1)
op = ${JSON.stringify(String(v.op ?? 'and'))}
result = cv2.bitwise_and(img, mask) if op == "and" else cv2.bitwise_or(img, mask) if op == "or" else cv2.bitwise_xor(img, mask)`),
  cvFamily('colormap', '伪彩色映射',
    'applyColorMap 风格选择（colormap 家族）。',
    [SEL('cm', '色图', 'jet', [['jet', 'JET'], ['hot', 'HOT'], ['cool', 'COOL'], ['bone', 'BONE'], ['turbo', 'TURBO'], ['viridis', 'VIRIDIS']])],
    (v) => `cm = ${JSON.stringify(String(v.cm ?? 'jet'))}
maps = {"jet": cv2.COLORMAP_JET, "hot": cv2.COLORMAP_HOT, "cool": cv2.COLORMAP_COOL, "bone": cv2.COLORMAP_BONE, "turbo": cv2.COLORMAP_TURBO, "viridis": cv2.COLORMAP_VIRIDIS}
result = cv2.applyColorMap(img, maps.get(cm, cv2.COLORMAP_JET))`),
  // ---- 单例家族 ----
  cvFamily('edge', '边缘检测组合',
    '高斯去噪 + Laplacian 与 Canny 对比（opencv-edge 单例）。',
    [],
    () => `lap = cv2.convertScaleAbs(cv2.Laplacian(cv2.GaussianBlur(img, (3, 3), 0), cv2.CV_64F))
cny = cv2.Canny(img, 100, 200)
result = np.hstack([lap, cny])`),
  cvFamily('colorspace', '色彩空间',
    'GRAY / HSV / LAB 通道转换（opencv-colorspace 单例）。',
    [SEL('cs', '色彩空间', 'hsv', [['gray', 'GRAY'], ['hsv', 'HSV'], ['lab', 'LAB']])],
    (v) => `cs = ${JSON.stringify(String(v.cs ?? 'hsv'))}
conv = {"gray": cv2.COLOR_BGR2GRAY, "hsv": cv2.COLOR_BGR2HSV, "lab": cv2.COLOR_BGR2LAB}[cs]
result = cv2.cvtColor(np.stack([img] * 3, axis=-1), conv) if img.ndim == 2 else cv2.cvtColor(img, conv)`),
  cvFamily('geometric', '几何变换组',
    '平移 / 旋转 / 缩放组合（opencv-geometric 单例）。',
    [P('tx', '平移 X', 40), P('ang', '旋转角', 15), P('scale', '缩放', 0.8)],
    (v) => `h, w = img.shape[:2]
M = np.float32([[1, 0, ${Math.trunc(Number(v.tx) || 0)}], [0, 1, 0]])
shifted = cv2.warpAffine(img, M, (w, h))
rot = cv2.getRotationMatrix2D((w / 2, h / 2), ${Number(v.ang) || 0}, ${Number(v.scale) || 1})
result = cv2.warpAffine(shifted, rot, (w, h))`),
  cvFamily('histogram', '直方图可视化',
    'calcHist 灰度分布绘制（opencv-histogram 单例）。',
    [],
    () => `hist = cv2.calcHist([img], [0], None, [64], [0, 256]).flatten()
bar_w, hist_h = 480 // 64, 360
result = np.zeros((hist_h, 480), dtype=np.uint8)
peak = hist.max() or 1
for i, hgt in enumerate(hist):
    bh = int(hgt / peak * (hist_h - 10))
    cv2.rectangle(result, (i * bar_w, hist_h - bh), ((i + 1) * bar_w - 1, hist_h - 1), 255, -1)`)
]

// ---------------------------------------------------------------------------
// OpenCV 处理实验室：25 处理家族归并单页
// ---------------------------------------------------------------------------
const CV_OP_FIELD: FieldSpec = {
  key: 'type',
  label: '处理操作',
  type: 'select',
  default: 'canny',
  width: 'full',
  options: CV_OPS.map((o) => ({ value: o.value, label: o.label }))
}

export const cvLabSchema: InteractiveToolSchema = {
  id: 'interactive:cv-lab',
  title: 'OpenCV 处理实验室',
  description: 'bulk_opencv 25 处理家族的归并页：合成场景 + 处理链，选操作、调参数，OpenCV 出图。',
  tags: ['图像', 'OpenCV'],
  fields: (v) => {
    const o = CV_OPS.find((x) => x.value === v.type) ?? CV_OPS[0]!
    return [CV_OP_FIELD, ...o.fields]
  },
  computeVia: 'sidecar',
  compute: (v) => ({ rows: [{ label: '处理操作', value: String(v.type ?? 'canny') }] }),
  headerFor: (v) => {
    const o = CV_OPS.find((x) => x.value === v.type) ?? CV_OPS[0]!
    return { title: o.label, description: o.description }
  },
  pyCode: (v) => {
    const o = CV_OPS.find((x) => x.value === v.type) ?? CV_OPS[0]!
    return `${CV_HEAD}\n${o.body(v)}\n${CV_OUT}`
  }
}
