# 轻量 Proposal 工作流 Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` or `superpowers:executing-plans` if this plan is executed task by task in a later session. This document is the implementation plan, not the proposal workflow itself.

**Goal:** 为“省科协科普视频”项目建立一个轻量版 OpenSpec 风格工作流，让结构性文档变更先经过 proposal，再由 AI 统一修改和对齐相关文件。

**Architecture:** 第一版不直接安装 OpenSpec / Spec Kit，也不做 hook 强制拦截。它只新增一个项目级 `PROPOSALS.md` 和一个可复用 skill，用户用显式 `/proposal` 触发流程；AI 在同一个 session 中完成意图记录、影响分析、变更计划、执行、验证和收尾回写。

**Tech Stack:** Markdown 文档、Codex skill、git diff / rg / find 等本地检查命令。

---

创建时间：2026-06-16 15:24（北京时间）
最后更新时间：2026-06-17 15:50（北京时间）
更新次数：2

## 先说结论

这个项目不适合直接套完整 OpenSpec，因为 OpenSpec 的强项是“软件行为变更”：proposal 后面通常跟 delta spec、design、tasks，然后改代码、跑测试、归档。你这里真正要管的是“文档体系和生产产物的一致性”：分镜脚本、素材清单、项目总览、端到端手册、渲染工程说明之间不能互相打架。

所以最小可用方案是借它的骨架，不借它的全部文件体系。也就是保留 `proposal -> impact -> plan -> apply -> verify -> close` 这条链，但 apply 和 verify 改成面向 Markdown / JSON / 项目产物的规则。

用户实际会看到的变化是：以后你不是让 AI 直接“更新分镜”或者“新增拉片”，而是先说 `/proposal 更新豆包视频 0-30s 分镜到 v2`。AI 先写出这次变更为什么要做、会影响哪些文件、每个文件怎么变、怎么验收。你只审这个 proposal 和 change plan，不需要自己逐个检查“项目总览有没有忘记改、素材清单路径有没有还指向旧版本”。执行后，AI 必须把实际修改、验证结果和未解决问题回写到 `PROPOSALS.md`。

## 第一版边界

第一版只服务 `省科协科普视频` 这个项目，不先推广到整个 `AI_workspace`。触发方式采用显式触发，只有用户明确说 `/proposal ...`、`走 proposal ...`、`按 proposal 流程 ...` 这类话时才进入流程。

需要走 proposal 的任务包括：分镜脚本版本更新、素材清单重建、新增标杆视频拉片、端到端管线结构调整、工程标准变化、项目总览中的核心状态变更。普通 bugfix 不强制走 proposal，比如修一个 Remotion 组件样式错位、改一个脚本参数、修 typo、补一个素材文件名。

第一版只保证“本次变更直接影响到的文件”互相对齐。比如 proposal 是更新分镜，那就检查分镜、素材清单、项目总览、端到端手册里和这次分镜产物有关的内容。不做每次全项目历史债扫描，因为那会把每个 proposal 都变成大扫除。

## 文件结构

第一版实施后，项目里新增或修改这些文件：

```text
省科协科普视频/
├── PROPOSALS.md
│   记录所有 proposal。新的 proposal 追加在文件顶部，每条 proposal 内部包含 Intent、Impact、Plan、Apply、Verify、Close 六段。
│
├── 2026-06-22_15-30_项目总览.md
│   增加一段“结构性变更入口”，指向 PROPOSALS.md，并说明项目总览只做状态入口，不再承载每次变更的完整过程。
│
├── 2026-06-22_15-30_目录导航.md
│   增加 PROPOSALS.md 入口，说明结构性变更账本的位置。
│
└── _skills/
    └── doc-proposal-workflow/
        └── SKILL.md
            项目内保存的 skill 源文件。验证可用后，再安装到 ~/.codex/skills/doc-proposal-workflow/。
```

这里故意不新建 `proposal/` 目录，也不让每个 proposal 变成一个独立文件。你的痛点就是文档太多，所以第一版只加一个 `PROPOSALS.md`，把它当成项目的变更账本。

## Proposal 记录格式

`PROPOSALS.md` 中每条 proposal 使用同一种结构。状态只允许这几个值：`DRAFT`、`PLANNED`、`APPLYING`、`VERIFYING`、`DONE`、`BLOCKED`。

```markdown
## [DRAFT] 2026-06-16_15-24_更新豆包视频0-30s分镜

触发人：用户
触发方式：/proposal 更新豆包视频 0-30s 分镜到 v2
当前状态：DRAFT

### 1. Intent

为什么要改：

这次要达成什么结果：

明确不做什么：

### 2. Impact

直接影响文件：

间接受影响文件：

不受影响但容易被误改的文件：

### 3. Change Plan

执行顺序：

每个文件的预期变化：

验收标准：

### 4. Apply Log

实际修改文件：

执行中发现的偏差：

### 5. Verify

已执行检查：

检查结果：

仍然存在的风险：

### 6. Close

最终状态：

需要回到总览的状态变化：

下一步建议：
```

第一版不要求把 `Intent`、`Impact`、`Change Plan` 拆成多个文件。这样保留 OpenSpec 的阶段感，但不复制它的文件数量。

## Skill 行为

skill 名称建议叫 `doc-proposal-workflow`。它触发后，AI 必须按下面的方式工作。

当用户触发 `/proposal`，AI 先读取项目总览、工程标准、端到端手册、当前目标视频项目目录，以及和用户请求直接相关的文件。读完后先写 `Intent` 和 `Impact`，再生成 `Change Plan`。如果影响范围很小，可以在同一个回复里请求用户批准；如果影响范围跨越多个产物，比如分镜、素材、渲染工程同时变，则先停在计划阶段，让用户确认后再执行。

执行阶段不能只改用户点名的那个文件。AI 必须以 `Impact` 为准，把直接影响文件逐个处理完。比如更新分镜后，如果素材清单里的镜头编号和分镜不一致，就必须同步更新素材清单；如果项目总览还写着旧分镜是当前版本，也必须同步改。

验证阶段至少做三类检查：第一，`git diff --name-only` 必须和 `Apply Log` 里的实际修改文件一致；第二，受影响文档中的关键路径和最新产物文件名必须一致；第三，不能把本次 proposal 明确标为“不受影响”的文件顺手改掉。

收尾阶段必须把 proposal 状态改成 `DONE` 或 `BLOCKED`。如果是 `DONE`，要写清楚最终修改了哪些文件、验证通过了哪些点、还有什么残留风险。如果是 `BLOCKED`，要写清楚卡在哪里，以及下次继续时应该从哪一步恢复。

## 实施任务

### Task 1: 新增项目级 PROPOSALS.md

**Files:**

Create: `省科协科普视频/PROPOSALS.md`

- [ ] Step 1: 创建 `PROPOSALS.md`，文件顶部写清楚它的职责：这是结构性变更账本，不是普通灵感记录，也不是替代项目总览。

- [ ] Step 2: 写入状态说明，限定状态值为 `DRAFT`、`PLANNED`、`APPLYING`、`VERIFYING`、`DONE`、`BLOCKED`。

- [ ] Step 3: 写入“什么任务需要 proposal，什么任务不需要”的边界。需要 proposal 的例子包括分镜更新、新增拉片、素材协议调整、管线结构调整；不需要的例子包括 typo、单文件 bugfix、一次性命令输出记录。

- [ ] Step 4: 写入一条 bootstrap proposal，记录“引入轻量 Proposal 工作流”本身。因为这是第一次建立流程，允许它作为初始化例外存在。

- [ ] Step 5: 检查文件名和正文时间，确保使用北京时间。

### Task 2: 在项目总览里增加变更入口

**Files:**

Modify: `省科协科普视频/2026-06-22_15-30_项目总览.md`

- [ ] Step 1: 在“配套文档”表格中加入 `PROPOSALS.md`，职责写成“结构性变更的 proposal、影响分析、执行记录和验证结果”。

- [ ] Step 2: 在靠前位置增加一段“结构性变更规则”：项目总览负责呈现当前状态，proposal 负责记录变更过程；用户可以主要阅读项目总览，但结构性修改必须进入 `PROPOSALS.md`。

- [ ] Step 3: 更新正文最后更新时间和更新次数。因为现有项目总览使用北京时间和更新次数，继续沿用它的格式。

- [ ] Step 4: 用 `rg -n "PROPOSALS|proposal|结构性变更" 省科协科普视频/2026-06-22_15-30_项目总览.md 省科协科普视频/2026-06-22_15-30_目录导航.md` 检查入口是否能被后续 agent 快速发现。

### Task 3: 编写项目内 skill 源文件

**Files:**

Create: `省科协科普视频/_skills/doc-proposal-workflow/SKILL.md`

- [ ] Step 1: 创建 skill frontmatter。`name` 使用 `doc-proposal-workflow`，`description` 写清楚触发条件：当用户要求用 proposal、OpenSpec 风格、Spec Kit 风格、文档变更流程来管理项目产物一致性时使用。

- [ ] Step 2: 写入硬性规则：没有显式 `/proposal` 时，不强制拦截普通工作；一旦进入 proposal 流程，不能跳过 Impact、Plan、Apply、Verify、Close。

- [ ] Step 3: 写入读取顺序：先读项目总览，再读 `PROPOSALS.md`，再读工程标准和端到端手册，最后只读取与本次变更直接相关的产物文件。

- [ ] Step 4: 写入 proposal 模板，和 `PROPOSALS.md` 中的结构保持一致。

- [ ] Step 5: 写入验证规则：`git diff --name-only` 对照 Apply Log；`rg` 检查关键文件名和路径；检查本次影响范围外的文件是否被误改。

- [ ] Step 6: 写入收尾规则：必须把结果回写到 `PROPOSALS.md`，必要时同步项目总览；不能只在聊天里说“完成了”。

### Task 4: 本地验证 skill 文本是否可用

**Files:**

Read: `省科协科普视频/_skills/doc-proposal-workflow/SKILL.md`

- [ ] Step 1: 用一次假想请求验证触发语义：`/proposal 更新豆包视频 0-30s 分镜到 v2`。

- [ ] Step 2: 检查 skill 是否会要求读取正确上下文：项目总览、`PROPOSALS.md`、工程标准、端到端手册、目标分镜文件、目标素材清单。

- [ ] Step 3: 检查 skill 是否会停在 Change Plan 等待用户确认，而不是直接开始改所有文件。

- [ ] Step 4: 检查 skill 是否写明 bugfix 不强制进入 proposal，避免日常小修被流程拖慢。

### Task 5: 安装 skill

**Files:**

Source: `省科协科普视频/_skills/doc-proposal-workflow/SKILL.md`

Target: `~/.codex/skills/doc-proposal-workflow/SKILL.md`

- [ ] Step 1: 确认项目内 skill 源文件已经可用。

- [ ] Step 2: 因为 `~/.codex/skills` 不在当前工作区写权限内，执行安装前需要单独请求授权。

- [ ] Step 3: 授权后复制 skill 到 `~/.codex/skills/doc-proposal-workflow/SKILL.md`。

- [ ] Step 4: 新开一次会话或重新加载技能后，确认技能列表能看到 `doc-proposal-workflow`。

### Task 6: 用一个小变更试跑

**Files:**

Modify only if proposal plan says so:

`省科协科普视频/PROPOSALS.md`

`省科协科普视频/2026-06-22_15-30_项目总览.md`

`省科协科普视频/视频项目/01_为什么他的豆包更聪明/04_素材清单/README.md`

- [ ] Step 1: 触发一个小 proposal，例如“对齐素材清单 README 和项目总览中的素材流程描述”。

- [ ] Step 2: 让 skill 生成 Intent、Impact、Change Plan。

- [ ] Step 3: 用户只审 Change Plan，不逐个检查所有交叉引用。

- [ ] Step 4: 执行修改。

- [ ] Step 5: 运行 `git diff --name-only`，确认实际修改文件和 Apply Log 一致。

- [ ] Step 6: 运行 `rg -n "素材流程|素材清单|assets" 省科协科普视频/2026-06-22_15-30_项目总览.md 省科协科普视频/2026-06-22_15-30_目录导航.md 省科协科普视频/视频项目/01_为什么他的豆包更聪明/04_素材清单/README.md`，确认关键表述没有互相冲突。

- [ ] Step 7: 把验证结果写回 `PROPOSALS.md`，状态改为 `DONE`。

## 验收标准

第一版完成后，一个新的 AI session 只要读取项目总览、`PROPOSALS.md` 和 skill，就能知道结构性变更应该怎么走。

一次 proposal 执行后，`PROPOSALS.md` 里记录的实际修改文件必须和 `git diff --name-only` 对得上。项目总览中列出的当前状态不能继续指向旧产物。直接受影响文档里的关键路径、文件名、版本描述不能互相冲突。

最重要的验收不是“文档变多了”，而是你以后可以少看文档。你看项目总览决定当前项目处于什么状态；你看 `PROPOSALS.md` 决定某次结构性变化为什么发生、改了什么、有没有验证完。其他具体文件由 proposal 流程带着 AI 去同步。

## 暂时不做

第一版不做 hook 强制拦截，因为你已经选择显式触发。如果后面发现 AI 还是经常绕过流程，再做第二版 hook。

第一版不做全项目一致性扫描。历史文档不一致的问题可以单独开一个 proposal 清理，不能让每次小 proposal 都承担全量审计。

第一版不引入 OpenSpec / Spec Kit 的完整目录结构，不创建 `spec.md`、`design.md`、`tasks.md`、`research.md`、`contracts/` 这些文件。它们适合代码型功能开发，但会加重你现在的文档痛苦。

## 后续升级路线

如果第一版跑顺，第二版可以加一个轻量检查脚本，自动读取 `PROPOSALS.md` 最近一条 `APPLYING` 或 `VERIFYING` proposal，比较 Apply Log 和 git diff。这个脚本不是第一版必需品，因为现在最重要的是先把人的交互习惯和 AI 的执行顺序固定下来。

第三版再考虑把 proposal 从单文件追加式升级成“单文件索引 + 少量归档文件”。只有当 `PROPOSALS.md` 真的长到影响阅读时才做，不提前增加文件数量。
