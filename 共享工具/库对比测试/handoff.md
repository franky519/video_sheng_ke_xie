# 库对比测试 — Handoff 文档

创建时间：2026-06-06 15:30（北京时间）
最后更新时间：2026-06-11 20:30（北京时间）
更新次数：第 2 次

本文件是 `06_库对比测试/` 的主入口。既是设计方案（给人审阅），也是执行手册（给 AI 照着跑）。最终产出是一份 `conclusion.md`（10 个 case 的汇总结论），指导省科协正片的库选型。

---

## 一、意图

### 1.1 问题演化（从历史聊天记录追溯）

**阶段 1：选题与立项（2026-05-25 前后）**
决定参加湖北省科普短视频大赛，主题为"豆包快速模式 vs 专家模式"，确定用代码程序化制作视频。

**阶段 2：参考视频分析与工程化（2026-05-30 ~ 06-02）**
反复追问"差评君和冲浪普拉斯为什么画面好"，发现核心答案：高密度证据卡片 + 持续画面变化 + 物理阻尼感。建立了闭环物理动作字典，用 Gemini 对参考视频做了程序化拉片。

**阶段 3：首次样片与差距诊断（2026-06-03 ~ 06-04）**
用 Remotion 出了 30s 工程样片，但效果不理想。诊断出核心差距：

> "事件流只是描述每个东西大概是怎么运动的，但缺少对于画面有什么、是什么、该可以用哪些工具达到的方式。工具层是缺失的。"

**阶段 4：库的认知缺口（当前）**
在讨论不同框架时，意识到对库的实际产出效果没有直观认知。之前只做了理论层面的对比，没有视觉 A/B 测试。

### 1.2 核心目标

对省科协视频中用到的每种特效类型，用**同一个画面需求**让不同库各自实现，录成视频，用 Gemini **客观评判**哪个效果最好。

---

## 二、架构

### 2.1 库的分层

```
框架层：Remotion（已确定，不做对比）
  └── 负责时间轴、合成、MP4 输出

视觉层：需要比较的库（在 Remotion 之上使用）
  ├── GSAP          — 通用动画引擎（项目已用）
  ├── Motion(React) — React 声明式动画
  ├── Anime.js      — 轻量 JS 动画
  ├── PixiJS        — WebGL 2D 渲染
  ├── CSS filter/transition — 浏览器原生（基线）
  └── Canvas 2D     — 逐帧像素级控制
```

关键原则：**Remotion 不参与比较**，它是框架不是视觉库。每个 case 只选该特效下真正有竞争力的库。

### 2.2 目录结构

```
06_库对比测试/
├── handoff.md              ← 本文件
├── conclusion.md            ← 汇总结论（最终产出）
├── _shared/                 ← Playwright + Gemini 脚本
├── case_01_高斯模糊+透明度/
│   ├── source.md            ← 源画面需求
│   ├── html/                ← 各库实现
│   └── videos/              ← 录制结果
├── case_02_弹性弹出/
│   ├── source.md
│   ├── html/
│   └── videos/
├── ...（共 10 个 case）
└── case_10_SVG路径描边/
```

设计要点：
- 每个 case 只有 2 层子目录（html + videos），`source.md` 放顶层
- **没有**独立 `judgment.md`，所有评判结果汇总到顶层 `conclusion.md`
- 所有录制视频保留（不是只保留最佳），方便后续回溯对比

---

## 三、Case 列表

### P0 级（5 个，当前样片直接依赖）

| # | Case | 源脚本位置 | 核心参数 | 比对库 |
|---|------|-----------|---------|--------|
| 1 | 高斯模糊 + 透明度 | `_归档_/视频项目/01_为什么他的豆包更聪明/旧版渲染方案/2026-06-03_09-20_豆包科普视频_0_30s图层运动工程调整与待办脚本.md` 第49行 | Opacity 100%→35%, Blur 0→18px, 1.5s线性 | CSS filter · Canvas 2D · GSAP · PixiJS |
| 2 | 弹性弹出 | 同上第47行 | Scale 0%→100%, spring(damping:15, mass:0.6), 左侧0s/右侧延迟1s | GSAP · Motion · Anime.js · CSS keyframes |
| 3 | ClipPath 擦除 | 同上第49行 | inset(0% 100% 0% 0%) → inset(0% 0% 0% 0%), 绿色1s/橙色1s | CSS clip-path · GSAP · Motion · Canvas 2D |
| 4 | 局部放大镜 | 同上第49-50行 | circle(120px), 内部scale(2.5), ±2px正弦抖动 | CSS clip-path · Canvas 2D · PixiJS |
| 5 | 错层入场 | 同上第49行; `_归档_/共享工具/旧版prompt/2026-06-04_11-40_豆包前30秒Few-Shot视觉语法迁移示例.md` 第37行 | 3条卡片staggered, 间隔0.8-1.2s | GSAP stagger · Motion staggerChildren · CSS delay · Anime.js |

### P1 级（2 个）

| # | Case | 源脚本位置 | 核心参数 | 比对库 |
|---|------|-----------|---------|--------|
| 6 | 打字机 + 光标 | `_归档_/共享工具/旧版prompt/2026-06-04_11-40_豆包前30秒Few-Shot视觉语法迁移示例.md` 第34行 | 逐字出现1-1.4s, 光标0.3s闪烁 | JS interval · GSAP · CSS steps · Canvas |
| 7 | 阴影发光 | `_归档_/视频项目/01_为什么他的豆包更聪明/旧版渲染方案/2026-06-03_09-20_豆包科普视频_0_30s图层运动工程调整与待办脚本.md` 第50行 | drop-shadow 0→30px, spring(damping:10, mass:0.5), Scale 0→120%→100% | CSS filter · Canvas · PixiJS · GSAP |

### P2 级（3 个）

| # | Case | 源脚本位置 | 核心参数 | 比对库 |
|---|------|-----------|---------|--------|
| 8 | 贝塞尔路径 | `共享工具/提示词/2026-06-09_17-30_Gemini物理拉片分析prompt_v2.txt` 第40-43行（Bezier参数规范） | cubic-bezier(0.25,0.1,0.25,1.0) 路径运动 | CSS bezier · GSAP motionPath · Motion · Anime.js |
| 9 | 数字滚动 | `_归档_/视频项目/01_为什么他的豆包更聪明/旧版素材表/2026-05-31_13-06_豆包科普视频逐镜头素材实现表.csv` S14行 | 12-18帧滚动到位, 柱子0.6-1s升起 | GSAP · Anime.js · JS rAF · CSS @property |
| 10 | SVG 路径描边 | 同上 S08行 | 三层结构图每层0.5-0.8s出现, 箭头逐段点亮 | CSS stroke-dasharray · GSAP drawSVG · Anime.js |

### 执行顺序

```
第一批（试点）：Case 1 → 你审阅 → 确认流程 OK
    ↓
第二批（验证）：Case 2 → 你审阅
    ↓
第三批：Case 3-5（P0 剩余）
    ↓
第四批：Case 6-7（P1）
    ↓
第五批：Case 8-10（P2）
    ↓
最终：conclusion.md 汇总
```

---

## 四、工作流

每个 case 走相同的 5 步标准流程，全自动执行（用户不参与中间步骤）。

### Step 1：创建 source.md

从省科协动效脚本中提取该 case 对应场景的物理参数描述，写入 `case_XX_xxx/source.md`。

内容要求：
- 场景描述（这个画面在视频的哪个位置、什么作用）
- 物理参数（精确的数值：时间、百分比、像素、缓动参数）
- 画面内容（卡片颜色/尺寸/文字内容/背景色）
- 源脚本引用（来自哪个文件的哪一行）

### Step 2：生成 HTML 实现

对每个比对库，生成一个独立的 HTML 文件，放入 `case_XX_xxx/html/{库名}.html`。

**所有 HTML 必须遵循的统一规范**：

| 规范 | 要求 |
|------|------|
| 自包含 | 单文件，库通过 CDN 引入，打开即播放 |
| 分辨率 | 1280x720，背景 RGB(30,32,35) |
| 画面内容 | 统一卡片样式（灰色圆角、4行中文占位文字、居中） |
| 动画 | 精确按 source.md 的参数，页面加载后自动播放，不循环 |
| 无杂质 | 不可有任何控制面板、字幕、进度条、调试信息 |

### Step 3：Playwright 录制

用 `_shared/record_case.mjs` 对每个 HTML 录制 webm：

```bash
node _shared/record_case.mjs \
  case_01_高斯模糊+透明度/html/css_filter.html \
  case_01_高斯模糊+透明度/videos/ \
  2000
```

输出：`case_XX_xxx/videos/{库名}.webm`（1280x720, 动画时长+500ms缓冲）

### Step 4：Gemini 评判

用 `_shared/gemini_judge.py` 将 N 个视频 + source.md 发给 Gemini 原生 API：

```bash
python3 _shared/gemini_judge.py case_01_高斯模糊+透明度
```

**发给 Gemini 的内容**：
1. 源画面需求（source.md 全文）
2. N 个录制视频（通过 Files API 上传）
3. 库映射表（"视频1 = CSS filter"）

**评判维度**：效果准确性 / 视觉质感 / 过渡平滑度 / 细节表现

**输出**：四维度排名表 + 综合排名 + 第1名关键理由

### Step 5：写入 conclusion.md

将 Gemini 评判结果追加到顶层 `conclusion.md` 中：

- 更新全局汇总表（该 case 的获胜库 + 理由）
- 附上 Gemini 评判原文（折叠引用）
- 标记该 case 状态为 `[DONE]`

---

## 五、技术约定

### 5.1 Playwright 录制

`_shared/record_case.mjs`：用 Chromium headless 打开 HTML → 等待动画 → 输出 webm。

### 5.2 Gemini API

`_shared/gemini_judge.py`：基于 `03_视频抽帧与裁剪工具/2026-06-02_17-45_gemini_native_analyze_30s.py` 改造。
- 支持多视频上传
- 使用评判专用 prompt（四维度对比）
- API 密钥从 `省科协科普视频/Gemini本地私密配置.env` 读取

### 5.3 文件命名

| 类型 | 格式 | 示例 |
|------|------|------|
| HTML | `{库名}.html` | `gsap.html` |
| 视频 | `{库名}.webm` | `gsap.webm` |
| 源需求 | `source.md` | — |

### 5.4 Case 状态标记

`[TODO]` → `[BUILDING]` → `[JUDGING]` → `[DONE]`

---

## 六、增量问答 / QA

（待后续补充）
