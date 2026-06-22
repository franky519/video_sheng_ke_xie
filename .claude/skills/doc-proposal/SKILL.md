---
name: doc-proposal
version: 1.0.0
description: '省科协文档体系结构性变更的入口导航。涉及多文件的结构性变更时触发。'
triggers:
  - "/doc-proposal"
  - "/proposal"
---

# doc-proposal — 结构性变更入口导航

这是一个调用链。按顺序依次执行三个子 Skill，不要合并成一步。

## 调用顺序

```
/doc-grilling（追问确认）
    写 _proposals/P00N_功能名.md（状态：GRILLED）
    ↓
/doc-prd（PRD 综合 + 任务拆解）
    读 proposal → 写 BACKLOG 任务 → 回写 proposal（状态：PLANNED）→ 等用户确认
    ↓
/doc-execute T-NNN（执行单个任务，每个任务调用一次）
    读 BACKLOG 任务 → Gate（展示文件清单，等确认）→ 执行 → 回写 proposal 进度
```

## 阅读前置

在调用 `/doc-grilling` 之前，先按 [AGENTS.md 强制阅读清单](./AGENTS.md) 读完五个文件（项目总览、目录导航、工程标准、管线手册、依赖关系图）。

## 状态层说明

`_proposals/` 是运行时 scratch 目录，不纳入目录导航。Proposal 文件是流程账本（记录每阶段决策），BACKLOG.md 是任务看板（跟踪执行状态）。两者互相引用，不重复内容。
