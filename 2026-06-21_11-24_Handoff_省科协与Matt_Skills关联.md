# Handoff — 省科协科普视频 / Matt Pocock Skills 关联

> 生成时间：2026-06-21 11:00（北京时间）
> 建议下一个会话重点：继续推进 proposal 工作流的落地，或将依赖关系图应用到实际变更中

## 背景：用户想要什么

用户在管理"省科协科普视频"项目时，发现自己维护的文档体系（项目总览、目录导航、工程标准、管线手册、prompt 文件、分镜脚本、素材清单等）之间存在大量隐性交叉依赖。每次改一个东西——比如把拉片 prompt 从 v3 升级到 v4——都靠人脑记忆"还要改工程标准的素材标签那一章、还要改管线手册的步骤 0"。

目标是：让 AI Agent 在读取一套依赖关系地图之后，能**自动**算出任何一次修改的 blast radius，然后逐文件对齐，最后验证交叉引用没有断裂。用户希望跟 AI 的交互方式变成——"我提一个想法，AI 告诉我波及范围，我确认，AI 执行并验证"。

## 本轮已完成的工作

### 1. Matt Pocock Skills 完整解析文档

**文件：** `2026-06-21_10-56_Matt_Pocock_Skills_完整解析.md`

一份 2100+ 行的中文文档，逐技能解析了 Matt Pocock 仓库里全部 26 个技能，每个技能都配了完整 case（带代码、带数据、带流程走读）。最后给出了两个版本的推荐安装清单：
- **版本一 General**（4 个）：grill-me / teach / edit-article / writing-great-skills
- **版本二 General + Coding**（18 个）：分三级（必须装 / 建议装 / 按需装），覆盖日常开发全链路

### 2. 省科协科普视频项目依赖关系图

**文件：** `省科协科普视频/2026-06-21_10-55_文档依赖与影响关系图.md`

为用户的视频生产项目创建了一份结构性依赖地图，包含：
- **11 条核心依赖链**：覆盖 Prompt 升级、工程标准变更、旁白稿变化、分镜脚本变化、素材清单变化、目录调整、脚本变化、Few-Shot 变化、原片预处理、Proposal 工作流、素材 manifest/symlink 桥
- **章节级 blast radius 速查表**：告诉你"改 X → 触发链 Y → 至少改 Z 个文件"
- **全局路径约定**：声明文件中使用简写路径，精确路径查目录导航
- **AI Agent 行为指令**：修改前/中/后三步验证流程

四个核心入口文档（项目总览、目录导航、工程标准、管线手册）的 IMPORTANT 区块都已加入对这个依赖关系图的引用。

### 3. 归档

根目录清理了 53 个旧文件（36 md + 7 word/excel + 10 杂物）移入 `2026-04-27_11-35_日常交流文档归档/`。antigravity 相关的 14 个文件单独收进 `antigravity网络排查/`。

### 4. 规则更新

在 `AGENTS.md` 和 `GEMINI.md` 中新增了"长文档目录规则"——超过 80 行的文档必须带锚点目录，并定义了锚点格式化规则。`Matt_Pocock_Skills_完整解析.md` 已按要求插入完整目录。

## 与 Matt Pocock Skills 的关联

用户最初问"能否借用 Matt 的技能达到我要的效果"。结论是**不能直接复用**——Matt 的技能是软件工程管线（面向代码、测试、issue tracker），用户的需求是文档体系一致性维护。但三个设计模式可借用：

1. `/domain-modeling` 的"主动维护术语表 + 检测冲突即打断"模式 → 需要的"依赖图 + blast radius 自动识别"
2. `/grilling` 的"一次一个问题 + 逐分支追问"节奏 → proposal 工作流中"发现影响 → 停住确认 → 不盲改"
3. SKILL.md 的文件格式和安装机制 → 未来写 `doc-proposal-workflow` skill 时采用

## 待落地的事项

### 优先级最高：PROPOSALS.md + doc-proposal-workflow skill

实施计划已有（`省科协科普视频/2026-06-17_15-50_轻量Proposal工作流Skill实施计划.md`），依赖关系图已有，但两个核心文件尚未创建：

1. `PROPOSALS.md` — 结构性变更账本（单文件，追加式，六段格式：Intent / Impact / Plan / Apply / Verify / Close）
2. `_skills/doc-proposal-workflow/SKILL.md` — 驱动的 skill 文件

依赖关系图在当前版本中已经把所有对 PROPOSALS.md 的引用标注为 `[计划中]` 和 `[待实施]`，第五节的"与 PROPOSALS.md 的配合"也标注了当前状态和落地前的手动替代方案。

### 建议的落地顺序

1. 用依赖关系图做一次"手动"的 blast radius 验证——比如改一下 v4 Prompt 里某个标签定义，AI 对照 11 条链条逐文件检查，确认依赖关系图的覆盖度没问题
2. 创建 PROPOSALS.md，把上面这次验证作为第一条 bootstrap proposal 写进去
3. 写 SKILL.md，定义 `/proposal` 的行为（读取核心文档 + 依赖图 → 算出 blast radius → 停住确认 → 逐文件执行 → git diff + rg 验证 → 回写 PROPOSALS.md）
4. 用一个小变更跑完整条 proposal 流程，验证 skill 可用
5. 安装到全局 `~/.codex/skills/` 或 `~/.claude/skills/`

### 当前可用的"手动"替代方案

在 PROPOSALS.md 和 skill 落地之前，任何结构性修改可以先这样做：
1. AI 读四个核心文档 + 依赖关系图
2. AI 对照 11 条链算出 blast radius，在聊天里汇报
3. 你确认后 AI 逐文件执行
4. AI 跑 `git diff --name-only` + `rg` 交叉引用验证

## 关键文件路径索引

| 文件 | 位置 |
|------|------|
| Matt Pocock Skills 完整解析 | `2026-06-21_10-56_Matt_Pocock_Skills_完整解析.md` |
| 省科协项目依赖关系图 | `省科协科普视频/2026-06-21_10-55_文档依赖与影响关系图.md` |
| 提案工作流实施计划 | `省科协科普视频/2026-06-17_15-50_轻量Proposal工作流Skill实施计划.md` |
| 四个核心入口文档 | `省科协科普视频/2026-06-17_17-57_项目总览.md` / `目录导航.md` / `工程标准_物理字典与素材协议.md` / `端到端管线操作手册.md` |
| AGENTS.md | `AGENTS.md`（含长文档目录规则） |
| GEMINI.md | `GEMINI.md`（含长文档目录规则） |
| 归档目录 | `2026-04-27_11-35_日常交流文档归档/` |
| antigravity 子文件夹 | `antigravity网络排查/` |

## Suggested Skills

如果下一个会话要推进 proposal 工作流落地：

- 先读四个核心入口文档 + 依赖关系图，确保理解当前项目状态
- 读 `轻量Proposal工作流Skill实施计划.md`，理解 Task 1-6 的设计意图
- 先动手写 SKILL.md（参考 `/writing-great-skills` 的编写方法论——如果已安装该技能的话）
- 写完后用一个小变更试跑全流程
