---
name: doc-execute
version: 1.0.0
description: '执行 BACKLOG 中的单个任务。执行前必须展示文件清单并等用户确认。用法：/doc-execute T-NNN'
triggers:
  - "/doc-execute"
---

# doc-execute — BACKLOG 任务执行器

**完成标准（硬约束）：** 任务的所有子任务 checkbox 已勾选 + git diff 验证通过 + BACKLOG 状态更新为"已完成" + proposal 进度已回写。

## Step 1：读取任务（硬约束）

读 `BACKLOG.md` 中 T-NNN 的完整内容。如果任务不存在，停止并说："请先运行 `/doc-prd` 生成任务。"

## Step 2：展示执行计划（门控，硬约束）

展示以下内容，**等用户说"开始"之后才能动任何文件**：

```
即将执行 T-NNN：[任务标题]
影响文件：
  - [文件 A]：[做什么]
  - [文件 B]：[做什么]
不动的文件：
  - [文件 X]（不在本任务范围）
确认执行？
```

## Step 3：执行

按 [AGENTS.md Blast Radius 行为](./AGENTS.md#blast-radius-行为硬约束) 逐文件执行。每改完一个文件，确认关键路径和文件名无矛盾，再改下一个。

## Step 4：验证

1. `git diff --name-only` — 确认改动文件列表符合计划（无超出范围的文件）
2. `rg` 检查关键路径交叉引用无断裂

## Step 5：收尾

1. 在 BACKLOG.md 中将 T-NNN 标记为已完成，所有子任务 checkbox 勾上
2. 在对应的 proposal 文件中更新进度（标记已完成的任务）
3. 如果该 proposal 的所有任务都已完成，将 proposal 状态改为 `DONE`

如果还有未执行的任务，说："T-NNN 完成。下一个任务是 T-MMM，运行 `/doc-execute T-MMM` 继续。"
