#!/usr/bin/env python3
"""
gemini_judge.py

将多个特效实现视频 + 源画面需求发给 Gemini 原生 API 进行评判。

用法：
  python3 _shared/gemini_judge.py <case_dir>
  python3 _shared/gemini_judge.py case_01_高斯模糊+透明度
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta
from urllib import request, error

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent          # 06_库对比测试/
SHENGKEXIE_DIR = PROJECT_DIR.parent      # 省科协科普视频/
ENV_PATH = SHENGKEXIE_DIR / "Gemini本地私密配置.env"

BEIJING = timezone(timedelta(hours=8))
BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
UPLOAD_URL = "https://generativelanguage.googleapis.com/upload/v1beta/files"


def load_env() -> dict:
    values = {}
    if not ENV_PATH.exists():
        print(f"WARNING: 找不到 .env: {ENV_PATH}", file=sys.stderr)
        return values
    with open(ENV_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            values[k.strip()] = v.strip().strip('"').strip("'")
    return values


def build_judge_prompt(source_text: str, lib_video_map: list[dict]) -> str:
    lib_table = ""
    for item in lib_video_map:
        lib_table += f"| {item['index']} | {item['lib_name']} | (视频{item['index']}) |\n"

    return f"""你是顶级视频特效评判专家。有 {len(lib_video_map)} 个不同库实现了同一个画面需求。请观看所有视频，评判哪个库效果最好，给出详细理由。

## 源画面需求

{source_text}

## 视频与库的对应关系

| 编号 | 库 | 视频 |
| :--- | :--- | :--- |
{lib_table}

## 评判维度

1. **效果准确性**：是否精确实现了源需求的物理参数？
2. **视觉质感**：是否高级、自然、不廉价？
3. **过渡平滑度**：有无闪烁、跳变、断层？
4. **细节表现**：文字可读性、边缘处理、色彩保真？

## 输出格式

### 各维度排名
| 维度 | 第1 | 第2 | 第3 | ... |
| :--- | :--- | :--- | :--- | :--- |
| 效果准确性 | | | | |
| 视觉质感 | | | | |
| 过渡平滑度 | | | | |
| 细节表现 | | | | |

### 综合排名
1. **第1名：库X** — （2-3句原因）
2. **第2名：库Y** — （1-2句）
...

### 选库建议
针对省科协豆包科普视频，推荐第1名实现本特效，原因：（1-2句）
"""


def upload_video(api_key: str, video_path: Path) -> dict:
    file_size = video_path.stat().st_size
    display_name = video_path.name

    init_body = json.dumps({"file": {"display_name": display_name}})
    req = request.Request(
        UPLOAD_URL,
        data=init_body.encode(),
        headers={
            "x-goog-api-key": api_key,
            "X-Goog-Upload-Protocol": "resumable",
            "X-Goog-Upload-Command": "start",
            "X-Goog-Upload-Header-Content-Length": str(file_size),
            "X-Goog-Upload-Header-Content-Type": "video/webm",
            "Content-Type": "application/json; charset=utf-8",
        },
        method="POST",
    )
    resp = request.urlopen(req, timeout=30)
    upload_url = resp.headers.get("X-Goog-Upload-URL")
    if not upload_url:
        raise RuntimeError("未获取到上传 URL")

    with open(video_path, "rb") as f:
        data = f.read()
    req2 = request.Request(upload_url, data=data,
        headers={
            "Content-Type": "video/webm",
            "Content-Length": str(len(data)),
            "X-Goog-Upload-Offset": "0",
            "X-Goog-Upload-Command": "upload, finalize",
        }, method="POST")
    resp2 = request.urlopen(req2, timeout=300)
    return json.loads(resp2.read().decode())


def wait_for_active(api_key: str, file_name: str, max_retries: int = 20) -> dict:
    for i in range(max_retries):
        req = request.Request(
            f"{BASE_URL}/{file_name}", method="GET",
            headers={"x-goog-api-key": api_key})
        resp = request.urlopen(req, timeout=10)
        info = json.loads(resp.read().decode())
        state = info.get("state", "UNKNOWN")
        print(f"  状态({i+1}): {state}")
        if state == "ACTIVE":
            return info
        if state == "FAILED":
            raise RuntimeError(f"文件处理失败: {info}")
        time.sleep(3)
    raise RuntimeError("文件处理超时")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    case_dir = Path(sys.argv[1]).resolve()
    model = sys.argv[3] if len(sys.argv) > 3 and sys.argv[2] == "--model" else "gemini-2.5-flash"

    source_path = case_dir / "source.md"
    videos_dir = case_dir / "videos"
    conclusion_path = PROJECT_DIR / "conclusion.md"

    if not source_path.exists():
        print(f"ERROR: 找不到 {source_path}", file=sys.stderr)
        sys.exit(1)
    if not videos_dir.exists() or not list(videos_dir.glob("*.webm")):
        print(f"ERROR: {videos_dir} 中没有 webm 视频", file=sys.stderr)
        sys.exit(1)

    source_text = source_path.read_text(encoding="utf-8").strip()
    video_files = sorted(videos_dir.glob("*.webm")) + sorted(videos_dir.glob("*.mp4"))

    lib_video_map = []
    for idx, vf in enumerate(video_files, 1):
        lib_video_map.append({
            "index": idx,
            "lib_name": vf.stem,
            "path": vf,
        })

    print(f"\n{'='*60}")
    print(f"Case: {case_dir.name}")
    print(f"模型: {model}")
    print(f"视频: {len(video_files)} 个")
    print(f"{'='*60}\n")

    env = load_env()
    api_key = env.get("GEMINI_API_KEY", "")
    if not api_key:
        print("ERROR: 未设置 GEMINI_API_KEY", file=sys.stderr)
        sys.exit(1)

    # 上传所有视频
    uploaded = []
    for item in lib_video_map:
        print(f"上传 [{item['index']}/{len(lib_video_map)}]: {item['lib_name']}")
        for attempt in range(3):
            try:
                info = upload_video(api_key, item["path"])
                break
            except Exception as e:
                if attempt < 2:
                    print(f"  上传失败 (尝试 {attempt+1}): {e}, 5秒后重试...")
                    time.sleep(5)
                else:
                    raise
        file_name = info.get("file", {}).get("name", "")
        if file_name:
            info = wait_for_active(api_key, file_name)
            file_uri = info.get("uri", info.get("file", {}).get("uri", ""))
            uploaded.append({**item, "file_name": file_name, "uri": file_uri})
        time.sleep(2)  # 避免连续上传触发限流
        print()

    # 构造请求
    prompt = build_judge_prompt(source_text, uploaded)
    parts = [{"text": prompt}]
    for u in uploaded:
        parts.append({"file_data": {"mime_type": "video/webm", "file_uri": u["uri"]}})

    payload = {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {"temperature": 0.4, "topP": 0.95, "maxOutputTokens": 4096},
    }

    url = f"{BASE_URL}/models/{model}:generateContent"
    print(f"发送评判请求到 {model}...")
    print(f"Files: {[u['file_name'] for u in uploaded]}")
    print(f"URIs: {[u['uri'][:60]+'...' for u in uploaded]}")

    req_body = json.dumps(payload).encode()
    print(f"Payload size: {len(req_body)} bytes")

    req = request.Request(url, data=req_body,
        headers={"x-goog-api-key": api_key, "Content-Type": "application/json"}, method="POST")

    try:
        import time as _time
        for g_attempt in range(5):
            try:
                resp = request.urlopen(req, timeout=120)
                break
            except Exception as e:
                err_str = str(e)
                if ("503" in err_str or "UNAVAILABLE" in err_str or "429" in err_str) and g_attempt < 4:
                    wait_s = (g_attempt + 1) * 10
                    print(f"  Gemini 繁忙，{wait_s}秒后重试 ({g_attempt+1}/5)...")
                    _time.sleep(wait_s)
                else:
                    raise
        result = json.loads(resp.read().decode())
    except Exception as e:
        print(f"Error: {e}")
        if hasattr(e, 'read'):
            print(f"Response body: {e.read().decode()[:500]}")
        raise

    candidates = result.get("candidates", [])
    if not candidates:
        print("ERROR: Gemini 无返回", file=sys.stderr)
        sys.exit(1)

    text = "".join(p.get("text", "") for p in candidates[0].get("content", {}).get("parts", []) if "text" in p)
    if not text:
        print("ERROR: 响应无文本", file=sys.stderr)
        sys.exit(1)

    # 写入 conclusion.md
    now = datetime.now(BEIJING).strftime("%Y-%m-%d %H:%M")
    entry = f"""

---

## Case: {case_dir.name}

- 评判时间：{now}（北京时间）
- 参与库：{', '.join(i['lib_name'] for i in lib_video_map)}

{text}
"""
    with open(conclusion_path, "a", encoding="utf-8") as f:
        f.write(entry)

    print(f"评判结果已追加到: {conclusion_path}")
    print(f"\n{'='*60}")
    print(text[:500] + ("..." if len(text) > 500 else ""))


if __name__ == "__main__":
    main()
