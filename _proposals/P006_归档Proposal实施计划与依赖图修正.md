# P006：归档旧 Proposal 实施计划 + 依赖关系图状态修正

> 创建时间：2026-06-25（北京时间）
> 最后更新：2026-06-25（北京时间）
> 更新次数：1

## 背景

旧 Codex skill 方案（`doc-proposal-workflow`）的实施计划文件 `2026-06-22_15-30_轻量Proposal工作流Skill实施计划.md` 描述了一个基于 Codex 自定义 skill + `PROPOSALS.md` 单文件账本的方案，该方案从未完全落地。

当前 Proposal 工作流已由 Superpowers 主导：brainstorming → writing-plans → executing-plans 流程，产出写入 `_proposals/P00N_*.md`。AGENTS.md 已定义此流程。

## 目标

1. 将旧实施计划文件归档至 `_归档_/`
2. 修正依赖关系图中链 10 和第五节状态——从错误的 `[已废弃]` 改为反映 Superpowers 驱动的当前状态

## 执行

- 文件移至 `_归档_/2026-06-22_15-30_轻量Proposal工作流Skill实施计划.md` ✓
- 依赖关系图 3 处修正：

| # | 位置 | 修正内容 |
|---|------|---------|
| 1 | 文档层级总览图 | `[已废弃]` → Superpowers 驱动描述 |
| 2 | 链 10 标题 + 状态 | 改为反映 Superpowers 方案 + 旧实施计划已归档 |
| 3 | 第五节 | 描述 Superpowers proposal 与依赖关系图的配合 |

## 验证

- `git diff --name-only` 确认仅修改依赖关系图
- `rg` 检查不再有对 `轻量Proposal工作流Skill实施计划.md` 的引用
