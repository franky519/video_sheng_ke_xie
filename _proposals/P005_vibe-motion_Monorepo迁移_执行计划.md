# P005 vibe-motion Monorepo 迁移 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 4 个独立 Remotion 项目迁移到 vibe-motion scaffold（pnpm 单项目），共享 node_modules。

**Architecture:** vibe-motion scaffold 是单 Remotion 项目 + shared 目录架构。我们简化其插件系统，改为在 `remotion/ProjectRoot.jsx` 直接注册 4 个 Composition，每个项目源码放在 `shared/` 下。

**Tech Stack:** Remotion 4.0.438, React 19, Vite, TailwindCSS, pnpm

---

## 文件结构

```
vibe-motion-monorepo/
├── package.json              # 修改：加 4 个 render 脚本
├── remotion.config.js        # 不动（entry point 已是 remotion/index.jsx）
├── remotion/
│   ├── index.jsx             # 不动（registerRoot）
│   └── ProjectRoot.jsx       # 重写：注册 4 个 Composition
├── shared/
│   ├── project-main/         # 新增：主渲染工程
│   │   ├── src/              # 从 05_渲染工程/src 搬来
│   │   ├── public/           # 从 05_渲染工程/public 搬来
│   │   ├── scripts/          # 从 05_渲染工程/scripts 搬来
│   │   └── asset-manifest.json
│   ├── project-screen-record/ # 新增：SCREEN_RECORD 组装验证
│   │   ├── src/
│   │   └── public/
│   ├── project-code-data-0/  # 新增：手写参考版
│   │   └── src/
│   └── project-code-data-1/  # 新增：AI Remotion 设计版
│       └── src/
│
├── public/                   # 不动（vibe-motion 模板静态资源）
├── scripts/                  # 不动（remotion render helpers）
└── preview/                  # 不动（vibe-motion 模板预览）
```

删除：
- `shared/features/demoMotion/`
- `shared/scaffold/`
- `shared/project/`
- `shared/styles/`（用各项目的 css 替代）

---

### Task 1: 清理 scaffold 模板

**Files:**
- Delete: `shared/features/demoMotion/`
- Delete: `shared/scaffold/`
- Delete: `shared/project/`
- Delete: `shared/styles/`
- Delete: `preview/`

- [ ] **删除 demo + scaffold + project 目录**

```bash
cd vibe-motion-monorepo
rm -rf shared/features shared/scaffold shared/project shared/styles preview
```

### Task 2: 移动 4 个项目的源码

**Files:**
- Create: `shared/project-main/`
- Create: `shared/project-screen-record/`
- Create: `shared/project-code-data-0/`
- Create: `shared/project-code-data-1/`

- [ ] **创建目标目录**

```bash
mkdir -p shared/project-main/src shared/project-main/public shared/project-main/scripts
mkdir -p shared/project-screen-record/src shared/project-screen-record/public
mkdir -p shared/project-code-data-0/src
mkdir -p shared/project-code-data-1/src
```

- [ ] **迁移主渲染工程**

```bash
cp -r 视频项目/01_为什么他的豆包更聪明/05_渲染工程/2026-06-03_10-20_remotion_豆包科普视频_0_30s工程样片/src/* shared/project-main/src/
cp -r 视频项目/01_为什么他的豆包更聪明/05_渲染工程/2026-06-03_10-20_remotion_豆包科普视频_0_30s工程样片/public/* shared/project-main/public/
cp -r 视频项目/01_为什么他的豆包更聪明/05_渲染工程/2026-06-03_10-20_remotion_豆包科普视频_0_30s工程样片/scripts/* shared/project-main/scripts/
cp 视频项目/01_为什么他的豆包更聪明/05_渲染工程/2026-06-03_10-20_remotion_豆包科普视频_0_30s工程样片/asset-manifest.json shared/project-main/
```

- [ ] **迁移 SCREEN_RECORD 组装验证**

```bash
cp -r _探索/P004/2026-06-23_SCREEN_RECORD_组装验证/src/* shared/project-screen-record/src/
cp -r _探索/P004/2026-06-23_SCREEN_RECORD_组装验证/public/* shared/project-screen-record/public/
```

- [ ] **迁移 code-data 手写参考版**

```bash
cp -r _探索/P004/2026-06-24_test0_CODE_DATA_手写参考/src/* shared/project-code-data-0/src/
```

- [ ] **迁移 code-data AI 设计版**

```bash
cp -r _探索/P004/2026-06-24_test1_CODE_DATA_Remotion-AI设计/src/* shared/project-code-data-1/src/
```

### Task 3: 写新的 ProjectRoot（注册 4 个 Composition）

**Files:**
- Modify: `remotion/ProjectRoot.jsx`

- [ ] **重写 ProjectRoot.jsx**

```javascript
import React from "react";
import { Composition } from "remotion";
import { CompositionMain } from "../shared/project-main/src/composition";
import { Sequence01Typing } from "../shared/project-screen-record/src/Sequence01_Typing";
import { RankingAnimation as RankingV0 } from "../shared/project-code-data-0/src/RankingAnimation";
import { RankingAnimation as RankingV1 } from "../shared/project-code-data-1/src/RankingAnimation";

export const ProjectRoot = () => {
  return <>
    <Composition
      id="DoubaoScience30"
      component={CompositionMain}
      durationInFrames={30 * 30}
      fps={30}
      width={1920}
      height={1080}
    />
    <Composition
      id="Sequence01"
      component={Sequence01Typing}
      durationInFrames={30 * 8}
      fps={30}
      width={1920}
      height={1080}
    />
    <Composition
      id="RankingV0"
      component={RankingV0}
      durationInFrames={30 * 8}
      fps={30}
      width={1920}
      height={1080}
    />
    <Composition
      id="RankingV1"
      component={RankingV1}
      durationInFrames={30 * 8}
      fps={30}
      width={1920}
      height={1080}
    />
  </>;
};
```

**Note:** 主渲染工程的 Composition 注册方式需根据其 `src/Root.tsx` 实际结构调整。上述 `CompositionMain` 是占位——任务执行时需读取实际 Root.tsx 内容后再写。

### Task 4: 修改迁移后文件的 import 路径

**Files:**
- Modify: 4 个项目的 `src/` 中的 import 路径

- [ ] **检查并修复 import 路径**

各项目的 `src/` 文件从原目录位置搬到 `shared/project-xxx/src/` 后，相对 import 可能需要调整。执行时：
1. 读每个项目的 `src/` 文件
2. 检查 `import from` 路径
3. 从 `../` 引用改为从 `shared/` 根引用

**Note:** 具体修改依赖实际文件内容，执行时逐文件检查。

### Task 5: 删除各项目的旧 index.ts/index.tsx（不用了——统一走 vibe-motion 的 index.jsx）

**Files:**
- Delete: `shared/project-main/src/index.tsx`
- Delete: `shared/project-screen-record/src/index.ts`
- Delete: `shared/project-code-data-0/src/index.ts`
- Delete: `shared/project-code-data-1/src/index.ts`

- [ ] **删除旧 entry point**

```bash
rm shared/project-main/src/index.tsx
rm shared/project-screen-record/src/index.ts
rm shared/project-code-data-0/src/index.ts
rm shared/project-code-data-1/src/index.ts
```

### Task 6: 在 package.json 添加 render 脚本

**Files:**
- Modify: `package.json`

- [ ] **追加 render 命令**

编辑 `package.json` 的 `scripts`，追加：

```json
"render:main": "REMOTION_OUTPUT=../../视频项目/01_为什么他的豆包更聪明/06_成片/main.mp4 node scripts/remotion-render.mjs DoubaoScience30",
"render:screen-record": "node scripts/remotion-render.mjs Sequence01",
"render:code-data-0": "node scripts/remotion-render.mjs RankingV0",
"render:code-data-1": "node scripts/remotion-render.mjs RankingV1"
```

**Note:** `scripts/remotion-render.mjs` 的用法需先验证——它用 `REMOTION_OUTPUT` 和 `REMOTION_PROPS_FILE` 环境变量。可能需要直接调 `remotion render` CLI。

### Task 7: 清理旧目录

**Files:**
- Delete: `_探索/P004/2026-06-23_SCREEN_RECORD_组装验证/node_modules`
- Delete: `_探索/P004/2026-06-24_test0_CODE_DATA_手写参考/node_modules`
- Delete: `_探索/P004/2026-06-24_test1_CODE_DATA_Remotion-AI设计/node_modules`
- Delete: `视频项目/01_.../05_渲染工程/...工程样片/node_modules`

- [ ] **删除旧 node_modules**

```bash
rm -rf _探索/P004/2026-06-23_SCREEN_RECORD_组装验证/node_modules
rm -rf _探索/P004/2026-06-24_test0_CODE_DATA_手写参考/node_modules
rm -rf _探索/P004/2026-06-24_test1_CODE_DATA_Remotion-AI设计/node_modules
rm -rf "视频项目/01_为什么他的豆包更聪明/05_渲染工程/2026-06-03_10-20_remotion_豆包科普视频_0_30s工程样片/node_modules"
```

- [ ] **原目录留说明文件**

```bash
echo "项目已迁移到 vibe-motion-monorepo/shared/project-main/" > "视频项目/01_为什么他的豆包更聪明/05_渲染工程/2026-06-03_10-20_remotion_豆包科普视频_0_30s工程样片/已迁移.md"
echo "项目已迁移到 vibe-motion-monorepo/shared/project-screen-record/" > _探索/P004/2026-06-23_SCREEN_RECORD_组装验证/已迁移.md
echo "项目已迁移到 vibe-motion-monorepo/shared/project-code-data-0/" > _探索/P004/2026-06-24_test0_CODE_DATA_手写参考/已迁移.md
echo "项目已迁移到 vibe-motion-monorepo/shared/project-code-data-1/" > _探索/P004/2026-06-24_test1_CODE_DATA_Remotion-AI设计/已迁移.md
```

### Task 8: 验证渲染

- [ ] **验证 Remotion studio 能启动**

```bash
cd vibe-motion-monorepo && npx remotion studio remotion/index.jsx --host 0.0.0.0
```

预期：Remotion Studio 打开，显示 4 个 Composition。

- [ ] **验证一个项目能渲染**

```bash
cd vibe-motion-monorepo && npx remotion render remotion/index.jsx RankingV1 out/test-ranking.mp4 --codec h264 --overwrite
```

预期：输出 MP4 文件。

---

## 自检

1. **Spec coverage**: 4 个项目的 src 迁移 ✅，node_modules 共享 ✅，旧目录清理 ✅，渲染验证 ✅
2. **Placeholder scan**: 无 TBD/TODO。Task 3 的 Composition 名和 Task 4 的 import 路径有轻微不确定性（依赖实际文件内容），标注了执行时需读文件再写
3. **Type consistency**: Composition ID 在全文中一致（DoubaoScience30 / Sequence01 / RankingV0 / RankingV1）
