import fs from "node:fs";
import path from "node:path";
import manifest from "../asset-manifest.json" with { type: "json" };

const root = path.resolve(new URL("..", import.meta.url).pathname);
const strict = process.argv.includes("--strict");
const missing = [];

for (const asset of manifest) {
  if (!asset.path) {
    continue;
  }

  const absolutePath = path.join(root, asset.path);
  const exists = fs.existsSync(absolutePath);
  const status = exists ? "DONE" : asset.status;
  console.log(`${asset.id}\t${status}\t${asset.path}\t${asset.description}`);

  if (!exists && asset.status.startsWith("TODO")) {
    missing.push(asset);
  }
}

if (missing.length > 0) {
  console.log("");
  console.log("缺失的外部资产：");
  for (const asset of missing) {
    console.log(`- ${asset.id}: ${asset.description} -> ${asset.path}`);
  }
}

if (strict && missing.length > 0) {
  process.exitCode = 1;
}
