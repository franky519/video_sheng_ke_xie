# P005 vibe-motion Monorepo 迁移

状态：EXECUTING

> 2026-06-25 brainstorming 产出。将所有 Remotion 项目统一迁移到 vibe-motion pnpm monorepo。

## 问题

仓库内 4 个 Remotion 项目各自独立安装 node_modules（remotion + react + webpack），每个约 150-200MB，重复下载 3-4 次。探索目录下三个测试各自一套依赖，命名不一致。

## 目标

用 create-vibe-motion 搭 pnpm workspace monorepo，4 个 Remotion 项目共享一套 node_modules。只改工程组织方式，不改任何组件代码逻辑。

## 涉及项目

| # | 原位置 | monorepo 包名 |
|---|--------|-------------|
| 1 | 05_渲染工程/...工程样片/ | main-rendering |
| 2 | _探索/P004/...SCREEN_RECORD_组装验证/ | screen-record-assembly |
| 3 | _探索/P004/...test0_CODE_DATA_手写参考/ | code-data-handwritten |
| 4 | _探索/P004/...test1_CODE_DATA_Remotion-AI设计/ | code-data-ai-design |

## 不动

- 组件代码逻辑一字不改
- data2motion 测试（不需要 node_modules）
- 探索文档和 P004 proposal
