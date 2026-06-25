#!/usr/bin/env python3
"""
使用 Gemini 原生 Files API 对抖音AI涨价视频前30秒进行视觉设计系统提取分析
"""

import cv2
import time
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from urllib import request, error, parse

SCRIPT_DIR = Path(__file__).resolve().parent
VIDEO_PATH = SCRIPT_DIR.parent / "02_别人视频的拆解分析" / "2026-06-02_抖音参考视频切片分析包" / "raw_downloads" / "01_7634456235240164659_AI集体涨价，免费额度越来越少了？ #AI#GPT#应用.mp4"
CLIP_PATH = SCRIPT_DIR.parent / "temp_30s_design_clip_douyin.mp4"
ENV_PATH = SCRIPT_DIR.parent / "Gemini本地私密配置.env"
PROMPT_FILE_PATH = SCRIPT_DIR.parent.parent / "_归档_" / "共享工具" / "旧版prompt" / "2026-06-05_Gemini视觉设计系统提取prompt.txt"
OUTPUT_PATH = SCRIPT_DIR.parent / "02_别人视频的拆解分析" / "AI_原始输出" / "2026-06-05_Gemini_抖音AI涨价视觉设计系统分析.md"
BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
UPLOAD_URL = "https://generativelanguage.googleapis.com/upload/v1beta/files"
BEIJING = timezone(timedelta(hours=8))

def load_env() -> dict:
    values = {}
    if not ENV_PATH.exists():
        return values
    with open(ENV_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            values[k.strip()] = v.strip().strip('"').strip("'")
    return values

def http_call(url, proxy, method="GET", body=None, headers=None, timeout=120):
    data = None
    req_headers = {"User-Agent": "gemini-design-extract/1.0"}
    if headers:
        req_headers.update(headers)
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        req_headers["Content-Type"] = "application/json; charset=utf-8"
    proxy_handler = request.ProxyHandler({"http": proxy, "https": proxy}) if proxy else request.ProxyHandler({})
    opener = request.build_opener(proxy_handler)
    req = request.Request(url, data=data, headers=req_headers, method=method)
    try:
        with opener.open(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8")
    except error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")
    except Exception as exc:
        return None, str(exc)

def crop_video():
    print(f"正在读取源视频: {VIDEO_PATH}")
    if not VIDEO_PATH.exists():
        raise FileNotFoundError(f"找不到源视频：{VIDEO_PATH}")
    cap = cv2.VideoCapture(str(VIDEO_PATH))
    if not cap.isOpened():
        raise RuntimeError("无法打开源视频")
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    max_dim = 720
    if width > max_dim or height > max_dim:
        if width > height:
            tw = max_dim
            th = int(height * (max_dim / width))
        else:
            th = max_dim
            tw = int(width * (max_dim / height))
    else:
        tw, th = width, height
    tw -= tw % 2
    th -= th % 2
    print(f"视频属性: FPS={fps:.2f}, {width}x{height} -> {tw}x{th}")
    total_frames = int(fps * 30)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(CLIP_PATH), fourcc, fps, (tw, th))
    frame_count = 0
    while frame_count < total_frames:
        ret, frame = cap.read()
        if not ret:
            break
        if width != tw or height != th:
            frame = cv2.resize(frame, (tw, th), interpolation=cv2.INTER_AREA)
        out.write(frame)
        frame_count += 1
    cap.release()
    out.release()
    print(f"裁剪完成! {frame_count} 帧")

def upload_and_analyze(api_key, proxy):
    print(f"上传视频 ({CLIP_PATH.stat().st_size / 1024 / 1024:.2f} MB)...")
    video_bytes = CLIP_PATH.read_bytes()
    size = len(video_bytes)
    mime_type = "video/mp4"
    proxy_handler = request.ProxyHandler({"http": proxy, "https": proxy}) if proxy else request.ProxyHandler({})
    opener = request.build_opener(proxy_handler)
    init_req = request.Request(
        UPLOAD_URL,
        data=json.dumps({"file": {"display_name": "temp_30s_douyin.mp4"}}).encode("utf-8"),
        headers={
            "x-goog-api-key": api_key,
            "X-Goog-Upload-Protocol": "resumable",
            "X-Goog-Upload-Command": "start",
            "X-Goog-Upload-Header-Content-Length": str(size),
            "X-Goog-Upload-Header-Content-Type": mime_type,
            "Content-Type": "application/json; charset=utf-8"
        },
        method="POST"
    )
    with opener.open(init_req, timeout=60) as resp:
        upload_url = resp.headers.get("X-Goog-Upload-URL")
    if not upload_url:
        raise RuntimeError("未获取到上传 URL")
    upload_req = request.Request(
        upload_url,
        data=video_bytes,
        headers={"Content-Type": mime_type, "Content-Length": str(size), "X-Goog-Upload-Offset": "0", "X-Goog-Upload-Command": "upload, finalize"},
        method="POST"
    )
    with opener.open(upload_req, timeout=300) as resp:
        uploaded_data = json.loads(resp.read().decode("utf-8"))
    file_info = uploaded_data.get("file", uploaded_data)
    file_uri = file_info["uri"]
    file_name = file_info["name"]
    print(f"上传成功! URI: {file_uri}")
    state = file_info.get("state", "UNKNOWN")
    while state in {"PROCESSING", "UNKNOWN"}:
        print(f"转码中 ({state})，等待 5 秒...")
        time.sleep(5)
        status, text = http_call(f"{BASE_URL}/{parse.quote(file_name, safe='/')}?key={api_key}", proxy)
        if status == 200:
            file_info = json.loads(text)
            state = file_info.get("state", "UNKNOWN")
        else:
            raise RuntimeError(f"查询失败 (HTTP {status}): {text}")
    if state == "FAILED":
        raise RuntimeError("转码失败")
    print(f"视频已激活! 状态: {state}")
    prompt_text = PROMPT_FILE_PATH.read_text(encoding="utf-8")
    model_name = "gemini-2.5-flash"
    generate_url = f"{BASE_URL}/models/{model_name}:streamGenerateContent?key={api_key}&alt=sse"
    payload = {"contents": [{"role": "user", "parts": [{"file_data": {"mime_type": mime_type, "file_uri": file_uri}}, {"text": prompt_text}]}]}
    print(f"向 {model_name} 发起分析请求...")
    proxy_handler = request.ProxyHandler({"http": proxy, "https": proxy}) if proxy else request.ProxyHandler({})
    opener = request.build_opener(proxy_handler)
    req = request.Request(generate_url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json", "User-Agent": "gemini-design-extract/1.0"}, method="POST")
    chunks = []
    with opener.open(req, timeout=600) as resp:
        print(f"\n=== {model_name} 分析中 ===")
        for line in resp:
            line_str = line.decode("utf-8").strip()
            if line_str.startswith("data: "):
                json_str = line_str[len("data: "):].strip()
                if json_str:
                    try:
                        chunk = json.loads(json_str)
                        text = chunk["candidates"][0]["content"]["parts"][0]["text"]
                        print(text, end="", flush=True)
                        chunks.append(text)
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue
        print("\n====================================\n")
    content = "".join(chunks)
    if content:
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_PATH.write_text(
            f"# Gemini 视觉设计系统分析：抖音AI涨价_前30秒\n\n"
            f"分析时间：{datetime.now(BEIJING).strftime('%Y-%m-%d %H:%M（北京时间）')}\n"
            f"使用模型：`{model_name}`\n\n"
            f"## 分析结果\n\n{content}\n",
            encoding="utf-8"
        )
        print(f"结果已保存至: {OUTPUT_PATH}")

def main():
    env = load_env()
    api_key = env.get("GEMINI_API_KEY")
    proxy = env.get("GEMINI_PROXY") or "http://127.0.0.1:10808"
    if not api_key:
        print("错误: 找不到 GEMINI_API_KEY")
        return
    try:
        crop_video()
        upload_and_analyze(api_key, proxy)
    finally:
        if CLIP_PATH.exists():
            try:
                CLIP_PATH.unlink()
                print("已清理临时缓存")
            except Exception as e:
                print(f"清理失败: {e}")

if __name__ == "__main__":
    main()
