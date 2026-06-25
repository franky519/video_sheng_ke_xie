# data2motion-skill 端到端测试结果

> 创建时间：2026-06-25 00:17（北京时间）
> 最后更新：2026-06-25 00:17（北京时间）
> 更新次数：1

## 测试链路

旁白稿 Chatbot Arena 排名段落 → JSON spec → build.py → HTML → Playwright → MP4

## 图表选型与设计理由

选型：**dumbbell（哑铃图）**

理由：旁白稿的核心叙事是"三四月排进前十 → 两个月后跌至第 35 名"，这是一个明确的 before/after 对比。dumbbell 图天然适配时间轴上的起止变化，start=8 / end=35 的视觉呈现让"排名倒退"（从左向右移动）一目了然，与旁白稿的情感基调一致。单行 dumbbell 略稀疏，但语义契合度最高。

## build.py 输出

- 状态：成功
- 命令：`python3 共享工具/data2motion-skill/scripts/build.py spec_d2m_chatbotarena.json chart_d2m_chatbotarena.html`
- 输出：`OK wrote chart_d2m_chatbotarena.html (chart=dumbbell)`
- HTML 大小：60 KB（自包含，含 dark console 主题 CSS + JS）

## HTML 生成结果

- 文件：`_探索/P004/CODE_DATA测试_AI设计/chart_d2m_chatbotarena.html`
- 大小：60 KB
- 渲染引擎：纯前端 SVG/CSS 动画，无外部依赖
- 动画时长：2200ms（spec 中指定）
- 主题：essential（dark console，默认）

## MP4 录制结果

- 文件：`_探索/P004/CODE_DATA测试_AI设计/chart_d2m_chatbotarena.mp4`
- 大小：734 KB
- 分辨率：1280x720
- 帧率：25 fps
- 总帧数：149 帧（约 6 秒，含动画播放 + 停留余量）
- 录制方式：Playwright headless Chromium → webm → OpenCV transcode 为 mp4
- 注意：系统无 ffmpeg，使用 cv2 + mp4v 编码转码，兼容性略低于 H.264，若需高兼容性 MP4 可在有 ffmpeg 的机器上重新转码

## 与手写 Remotion 版本的对比感受

| 维度 | data2motion-skill | 手写 Remotion |
|------|-------------------|---------------|
| 开发时间 | ~5 分钟（写 spec JSON + 跑命令） | 30 分钟+（写 React 组件、调动画参数） |
| 产出质量 | 专业的 dark console 风格，动画流畅 | 可高度定制但依赖开发者审美 |
| 灵活性 | 受限于 10 种预定义图表类型 | 完全自由 |
| 可维护性 | 改数据只需编辑 JSON | 改数据或样式需改代码 |
| 视频集成 | 需额外录制（Playwright） | 原生渲染 MP4 |
| 适用场景 | 标准图表、数据驱动、快速迭代 | 非标定制动画、复杂交互 |

结论：对于 Chatbot Arena 排名变化这类标准数据图表，data2motion-skill 在开发效率和产出质量上均有明显优势。唯一代价是需要 Playwright 录制环节，但这可以脚本化一次后复用。

## 文件清单

| 文件 | 大小 | 说明 |
|------|------|------|
| spec_d2m_chatbotarena.json | 372 B | JSON 数据规格 |
| chart_d2m_chatbotarena.html | 60 KB | 自包含动画 HTML |
| chart_d2m_chatbotarena.webm | 217 KB | Playwright 原始录制 |
| chart_d2m_chatbotarena.mp4 | 734 KB | MP4 视频素材（供 Remotion 使用） |
