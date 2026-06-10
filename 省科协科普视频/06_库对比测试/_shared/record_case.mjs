/**
 * record_case.mjs
 *
 * 用 Playwright headless 录制 HTML 动效为 webm 视频。
 *
 * 用法:
 *   node _shared/record_case.mjs <html路径> <输出目录> [动画时长ms]
 *   node _shared/record_case.mjs ../case_01/html/css_filter.html ../case_01/videos/ 2000
 */

import { chromium } from 'playwright';
import { resolve, basename } from 'path';
import { mkdirSync, existsSync, renameSync, readdirSync } from 'fs';

const htmlPath = resolve(process.argv[2]);
const outputDir = resolve(process.argv[3]);
const duration = parseInt(process.argv[4]) || 2500;

if (!htmlPath || !outputDir) {
  console.error('用法: node record_case.mjs <html路径> <输出目录> [动画时长ms]');
  process.exit(1);
}

if (!existsSync(outputDir)) {
  mkdirSync(outputDir, { recursive: true });
}

const libName = basename(htmlPath).replace('.html', '');
console.log(`录制: ${libName} -> ${outputDir}/${libName}.webm`);

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  viewport: { width: 1280, height: 720 },
  recordVideo: {
    dir: outputDir,
    size: { width: 1280, height: 720 },
  },
});

const page = await context.newPage();
await page.goto(`file://${htmlPath}`, { waitUntil: 'load' });
await page.waitForTimeout(duration + 1000);

await context.close();
await browser.close();

// Playwright 默认用随机名，重命名为库名
const files = readdirSync(outputDir);
const videoFile = files.find(f => f.endsWith('.webm'));
if (videoFile) {
  renameSync(`${outputDir}/${videoFile}`, `${outputDir}/${libName}.webm`);
  console.log(`完成: ${outputDir}/${libName}.webm`);
}
