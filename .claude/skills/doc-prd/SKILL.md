---
name: doc-prd
version: 1.0.0
description: '读取最新 GRILLED 状态的 proposal，生成 PRD，拆解为 BACKLOG 任务，回写 proposal 状态为 PLANNED。'
triggers:
  - "/doc-prd"
---

# doc-prd — PRD 综合与任务拆解

**完成标准（硬约束）：** 本 Skill 完成 = 任务已追加到 `BACKLOG.md` + proposal 状态已更新为 PLANNED + 用户明确说"可以执行"。

## Step 1：读取 proposal

扫描 `_proposals/P*.md`，找到最新一个状态为 `GRILLED` 的 proposal。如果找不到，停止并说："请先运行 `/doc-grilling`。"

## Step 2：综合 PRD

直接基于 proposal 的变更描述和影响文件，不再追问，生成 PRD 并输出到聊天：

```
### Proposal：[变更标题]
**问题陈述：** [什么东西存在什么问题]
**目标状态：** [变更后的状态，不是操作步骤]
**变更决策清单：** [逐文件列出]
**不动的范围：** [排除文件]
**完成验证：** [验证方式]
```

## Step 3：拆解任务并写入 BACKLOG

把变更决策清单拆成独立任务，追加到 `BACKLOG.md`（就绪队列）：

- 每个任务独立可完成（不能是"改文件的前半段"）
- 标注前置依赖和 `[P]`（可并行）
- 格式沿用 BACKLOG.md 现有任务格式

## Step 4：回写 proposal（硬约束）

在 proposal 文件末尾追加：

```markdown
## PRD 综合

[PRD 正文内容]

## 已生成 BACKLOG 任务
- T-NNN：[任务标题]
- T-MMM：[任务标题]

状态：PLANNED
下一步：运行 /doc-execute T-NNN
```

将 proposal 开头的 `状态：GRILLED` 改为 `状态：PLANNED`。

## Step 5：等用户确认（硬约束）

说："以上任务已写入 BACKLOG，proposal 已更新为 PLANNED。用 `/doc-execute T-NNN` 开始执行第一个任务。" 等用户确认，不自动进入执行。
