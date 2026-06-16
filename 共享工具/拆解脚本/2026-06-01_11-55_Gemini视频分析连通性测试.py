#!/usr/bin/env python3
"""Gemini API 最小连通性测试。

第一步只验证两件事：
1. 这台机器能不能通过本地代理 127.0.0.1:10808 访问 Gemini 后端。
2. 填入 GEMINI_API_KEY 后，Gemini 文本请求能不能成功。

用法：
  python3 2026-06-01_11-55_Gemini视频分析连通性测试.py --mode diagnose
  GEMINI_API_KEY=你的key python3 2026-06-01_11-55_Gemini视频分析连通性测试.py --mode text
  GEMINI_API_KEY=你的key python3 2026-06-01_11-55_Gemini视频分析连通性测试.py --mode models
  GEMINI_API_KEY=你的key python3 2026-06-01_11-55_Gemini视频分析连通性测试.py --mode video --video ./sample.mp4

持久存储：
  可在脚本同目录新建 Gemini本地私密配置.env，写入：
    GEMINI_API_KEY=你的key
    GEMINI_MODEL=gemini-3.5-flash
    GEMINI_PROXY=http://127.0.0.1:10808

可选：
  --proxy http://127.0.0.1:10808
  --proxy direct
  --model gemini-3.5-flash
  --prompt-file ./prompt.txt
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import socket
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib import error, parse, request


DEFAULT_PROXY = "http://127.0.0.1:10808"
BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
UPLOAD_URL = "https://generativelanguage.googleapis.com/upload/v1beta/files"
LOCAL_ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Gemini本地私密配置.env")
SCRIPT_DIR = Path(__file__).resolve().parent
BEIJING = timezone(timedelta(hours=8))
SUPPORTED_VIDEO_MIME_TYPES = {
    "video/mp4",
    "video/mpeg",
    "video/mov",
    "video/avi",
    "video/x-flv",
    "video/mpg",
    "video/webm",
    "video/wmv",
    "video/3gpp",
}


def load_local_env(path: str = LOCAL_ENV_PATH) -> dict[str, str]:
    values: dict[str, str] = {}
    if not os.path.exists(path):
        return values

    with open(path, "r", encoding="utf-8") as file:
        for line_number, raw_line in enumerate(file, 1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                raise SystemExit(f"{path}:{line_number} 格式错误，应写成 KEY=value")
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                values[key] = value
    return values


LOCAL_ENV = load_local_env()
DEFAULT_MODEL = os.environ.get("GEMINI_MODEL") or LOCAL_ENV.get("GEMINI_MODEL") or "gemini-3.5-flash"
DEFAULT_PROXY = os.environ.get("GEMINI_PROXY") or LOCAL_ENV.get("GEMINI_PROXY") or DEFAULT_PROXY


def normalize_proxy(value: str | None) -> str | None:
    if not value or value.lower() == "direct":
        return None
    if "://" not in value:
        return "http://" + value
    return value


def redact_proxy(value: str | None) -> str:
    if not value:
        return "direct"
    parsed = parse.urlsplit(value)
    port = f":{parsed.port}" if parsed.port else ""
    return f"{parsed.scheme}://{parsed.hostname}{port}"


def check_proxy_port(proxy_url: str | None) -> tuple[bool, str]:
    if not proxy_url:
        return True, "直连模式，不检查本地端口"

    parsed = parse.urlsplit(proxy_url)
    if parsed.scheme not in {"http", "https"}:
        return False, f"当前脚本只测试 HTTP 代理，不测试 {parsed.scheme} 代理"
    if not parsed.hostname or not parsed.port:
        return False, "代理地址缺少 host 或 port"

    try:
        with socket.create_connection((parsed.hostname, parsed.port), timeout=3):
            return True, f"{parsed.hostname}:{parsed.port} 端口可连接"
    except OSError as exc:
        return False, f"{parsed.hostname}:{parsed.port} 端口不可连接：{exc}"


def opener_for(proxy_url: str | None):
    if proxy_url:
        return request.build_opener(request.ProxyHandler({"http": proxy_url, "https": proxy_url}))
    return request.build_opener(request.ProxyHandler({}))


def http_call(
    url: str,
    *,
    proxy_url: str | None,
    method: str = "GET",
    body: dict | None = None,
    raw_body: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 30,
) -> tuple[int | None, str]:
    data = raw_body
    req_headers = {"User-Agent": "gemini-minimal-probe/1.0"}
    if headers:
        req_headers.update(headers)
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        req_headers.setdefault("Content-Type", "application/json; charset=utf-8")

    req = request.Request(url, data=data, headers=req_headers, method=method)
    try:
        with opener_for(proxy_url).open(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")
    except error.URLError as exc:
        return None, str(exc.reason)
    except OSError as exc:
        return None, str(exc)


def api_key() -> str:
    key = (os.environ.get("GEMINI_API_KEY") or LOCAL_ENV.get("GEMINI_API_KEY") or "").strip()
    if not key:
        raise SystemExit(
            "缺少 GEMINI_API_KEY。你可以设置系统环境变量，或在脚本同目录新建 "
            "Gemini本地私密配置.env，写入 GEMINI_API_KEY=你的key。"
        )
    return key


def with_key(path: str, key: str) -> str:
    return f"{BASE_URL}/{path}?key={parse.quote(key)}"


def mode_diagnose(proxy_url: str | None) -> int:
    print(f"使用代理：{redact_proxy(proxy_url)}")
    print(f"本地私密配置：{'已读取 ' + LOCAL_ENV_PATH if LOCAL_ENV else '未找到'}")
    print(f"API Key 来源：{'系统环境变量' if os.environ.get('GEMINI_API_KEY') else ('本地私密配置' if LOCAL_ENV.get('GEMINI_API_KEY') else '未设置')}")
    ok, detail = check_proxy_port(proxy_url)
    print(f"本地代理端口：{detail}")
    if not ok:
        return 2

    status, text = http_call(f"{BASE_URL}/models", proxy_url=proxy_url, timeout=20)
    if status is None:
        print(f"Gemini 域名不可达：{text}")
        return 2

    print(f"Gemini 域名可达：HTTP {status}")
    if status in {401, 403}:
        print("这类认证错误是正常的：diagnose 没带 API Key，但已经说明网络打到 Google 了。")
    else:
        print(text[:500])
    return 0


def mode_models(proxy_url: str | None) -> int:
    key = api_key()
    status, text = http_call(with_key("models", key), proxy_url=proxy_url, timeout=30)
    if status != 200:
        print(f"获取模型列表失败：HTTP {status}\n{text[:2000]}")
        return 1

    data = json.loads(text)
    for item in data.get("models", []):
        name = item.get("name", "")
        methods = ",".join(item.get("supportedGenerationMethods", []))
        print(f"{name:<45} {methods}")
    return 0


def extract_text(response_text: str) -> str:
    data = json.loads(response_text)
    chunks: list[str] = []
    for candidate in data.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            if "text" in part:
                chunks.append(part["text"])
    return "\n".join(chunks) or response_text


def mode_text(proxy_url: str | None, model: str) -> int:
    key = api_key()
    body = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": "请用一句中文回复：Gemini API 连通性测试成功。"}],
            }
        ]
    }
    status, text = http_call(
        with_key(f"models/{model}:generateContent", key),
        proxy_url=proxy_url,
        method="POST",
        body=body,
        timeout=60,
    )
    if status != 200:
        print(f"文本请求失败：HTTP {status}\n{text[:2000]}")
        return 1
    print(extract_text(text))
    return 0


def now_stamp() -> str:
    return datetime.now(BEIJING).strftime("%Y-%m-%d_%H-%M")


def detect_mime_type(video_path: Path) -> str:
    mime_type = mimetypes.guess_type(video_path.name)[0] or "video/mp4"
    if mime_type == "video/quicktime":
        mime_type = "video/mov"
    if mime_type not in SUPPORTED_VIDEO_MIME_TYPES:
        raise SystemExit(f"Gemini 官方支持的视频 MIME 类型里没有 {mime_type}，请先转成 mp4/webm/mov。")
    return mime_type


def upload_video_file(video_path: Path, key: str, proxy_url: str | None) -> dict:
    if not video_path.exists():
        raise SystemExit(f"视频文件不存在：{video_path}")
    if not video_path.is_file():
        raise SystemExit(f"不是视频文件：{video_path}")

    mime_type = detect_mime_type(video_path)
    video_bytes = video_path.read_bytes()
    size = len(video_bytes)
    display_name = video_path.name

    print(f"准备上传：{video_path}")
    print(f"视频大小：{size / 1024 / 1024:.2f} MB，MIME：{mime_type}")

    init_body = json.dumps({"file": {"display_name": display_name}}, ensure_ascii=False).encode("utf-8")
    init_req = request.Request(
        UPLOAD_URL,
        data=init_body,
        method="POST",
        headers={
            "User-Agent": "gemini-minimal-probe/1.0",
            "Content-Type": "application/json; charset=utf-8",
            "x-goog-api-key": key,
            "X-Goog-Upload-Protocol": "resumable",
            "X-Goog-Upload-Command": "start",
            "X-Goog-Upload-Header-Content-Length": str(size),
            "X-Goog-Upload-Header-Content-Type": mime_type,
        },
    )
    try:
        with opener_for(proxy_url).open(init_req, timeout=60) as resp:
            upload_url = resp.headers.get("X-Goog-Upload-URL")
            resp.read()
    except error.HTTPError as exc:
        raise SystemExit(f"初始化上传失败：HTTP {exc.code}\n{exc.read().decode('utf-8', errors='replace')[:2000]}")
    if not upload_url:
        raise SystemExit("初始化上传失败：Gemini 没有返回 X-Goog-Upload-URL")

    upload_req = request.Request(
        upload_url,
        data=video_bytes,
        method="POST",
        headers={
            "User-Agent": "gemini-minimal-probe/1.0",
            "Content-Type": mime_type,
            "Content-Length": str(size),
            "X-Goog-Upload-Offset": "0",
            "X-Goog-Upload-Command": "upload, finalize",
        },
    )
    try:
        with opener_for(proxy_url).open(upload_req, timeout=300) as resp:
            uploaded = json.loads(resp.read().decode("utf-8", errors="replace"))
    except error.HTTPError as exc:
        raise SystemExit(f"上传视频失败：HTTP {exc.code}\n{exc.read().decode('utf-8', errors='replace')[:2000]}")

    file_obj = uploaded.get("file", uploaded)
    if not file_obj.get("uri"):
        raise SystemExit(f"上传成功但没有拿到 file.uri：{json.dumps(uploaded, ensure_ascii=False)[:2000]}")
    return file_obj


def wait_file_active(file_obj: dict, key: str, proxy_url: str | None, wait_seconds: int) -> dict:
    name = file_obj.get("name")
    if not name:
        return file_obj

    deadline = time.time() + wait_seconds
    state = file_obj.get("state", "UNKNOWN")
    while state not in {"ACTIVE", "SUCCEEDED"}:
        if state == "FAILED":
            raise SystemExit(f"Gemini 文件处理失败：{json.dumps(file_obj, ensure_ascii=False)[:2000]}")
        if time.time() > deadline:
            raise SystemExit(f"等待视频处理超时，最后状态：{state}")
        print(f"Gemini 文件处理状态：{state}，等待 5 秒...")
        time.sleep(5)
        status, text = http_call(with_key(parse.quote(name, safe="/"), key), proxy_url=proxy_url, timeout=30)
        if status != 200:
            raise SystemExit(f"查询文件状态失败：HTTP {status}\n{text[:2000]}")
        file_obj = json.loads(text)
        state = file_obj.get("state", "UNKNOWN")
    print(f"Gemini 文件处理状态：{state}")
    return file_obj


def default_video_prompt() -> str:
    return """请分析这个视频的画面制作方式，不要只复述内容。

请重点输出：
1. 前 3-5 分钟里主要画面类型：资料卡、截图、表格、红框、字幕、B-roll、人物出镜、UI、动画结构图等；
2. 画面变化节奏：大概多久切一次主要画面，红框/下划线/卡片入场大概多快；
3. 哪些画面方法可以迁移到“省科协豆包科普视频”；
4. 分别适合用 Remotion、Motion Canvas、Manim、D3/HTML、AI B-roll、传统剪辑/AE 中的哪个工具复刻；
5. 哪些素材不能直接照搬，需要重绘、转绘或授权。

请用中文 Markdown 输出，尽量带时间戳。"""


def safe_file_stem(path: Path) -> str:
    stem = path.stem
    for char in '\\/:*?"<>|':
        stem = stem.replace(char, "_")
    return stem[:80] or "video"


def save_video_result(video_path: Path, model: str, result_text: str) -> Path:
    output_path = SCRIPT_DIR.parent / "02_参考拉片库" / "AI_原始输出" / f"{now_stamp()}_Gemini_视频分析结果_{safe_file_stem(video_path)}.md"
    output_path.write_text(
        f"""# Gemini 视频分析结果：{video_path.name}

创建时间：{datetime.now(BEIJING).strftime('%Y-%m-%d %H:%M（北京时间）')}

模型：`{model}`

源视频：`{video_path}`

## 结果

{result_text}
""",
        encoding="utf-8",
    )
    return output_path


def read_prompt(prompt: str | None, prompt_file: str | None) -> str:
    if prompt_file:
        return Path(prompt_file).expanduser().read_text(encoding="utf-8")
    return prompt or default_video_prompt()


def mode_video(
    proxy_url: str | None,
    model: str,
    video: str,
    prompt: str | None,
    prompt_file: str | None,
    wait_seconds: int,
) -> int:
    key = api_key()
    video_path = Path(video).expanduser().resolve()
    file_obj = upload_video_file(video_path, key, proxy_url)
    file_obj = wait_file_active(file_obj, key, proxy_url, wait_seconds)
    mime_type = file_obj.get("mimeType") or detect_mime_type(video_path)
    file_uri = file_obj["uri"]

    body = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"file_data": {"mime_type": mime_type, "file_uri": file_uri}},
                    {"text": read_prompt(prompt, prompt_file)},
                ],
            }
        ]
    }
    status, text = http_call(
        with_key(f"models/{model}:generateContent", key),
        proxy_url=proxy_url,
        method="POST",
        body=body,
        timeout=300,
    )
    if status != 200:
        print(f"视频分析失败：HTTP {status}\n{text[:4000]}")
        return 1

    result_text = extract_text(text)
    output_path = save_video_result(video_path, model, result_text)
    print(result_text)
    print(f"\n分析结果已保存：{output_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Gemini API 最小连通性测试")
    parser.add_argument("--mode", choices=["diagnose", "text", "models", "video"], default="diagnose")
    parser.add_argument("--video", help="本地视频文件路径，供 --mode video 使用")
    parser.add_argument("--prompt", help="可选：覆盖默认视频分析提示词")
    parser.add_argument("--prompt-file", help="可选：从文本文件读取视频分析提示词，适合长 prompt")
    parser.add_argument("--wait-seconds", type=int, default=240, help="等待 Gemini 处理上传视频的最长秒数")
    parser.add_argument("--proxy", default=DEFAULT_PROXY, help="默认 http://127.0.0.1:10808；可传 direct")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()

    proxy_url = normalize_proxy(args.proxy)
    if args.mode == "diagnose":
        return mode_diagnose(proxy_url)
    if args.mode == "models":
        return mode_models(proxy_url)
    if args.mode == "text":
        return mode_text(proxy_url, args.model)
    if args.mode == "video":
        if not args.video:
            parser.error("--mode video 需要 --video 本地视频路径")
        return mode_video(proxy_url, args.model, args.video, args.prompt, args.prompt_file, args.wait_seconds)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
