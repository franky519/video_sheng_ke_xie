#!/usr/bin/env python3
"""
使用 Google Vertex AI 调用 Gemini 进行视频拉片分析（付费模式）

认证：Service Account JSON → Bearer Token
端点：us-central1-aiplatform.googleapis.com
视频：inline base64（<20MB 直接内嵌）

用法：
  # 文本测试
  python3 2026-06-10_20-30_vertex_ai_gemini_analyze.py --text "你好"

  # 默认：前30秒视频分析
  python3 2026-06-10_20-30_vertex_ai_gemini_analyze.py

  # 指定时段
  python3 2026-06-10_20-30_vertex_ai_gemini_analyze.py --start 30 --end 60
"""

import os
import sys
import cv2
import time
import json
import base64
import argparse
from pathlib import Path
from datetime import datetime, timezone, timedelta
from urllib import request, error, parse

BEIJING = timezone(timedelta(hours=8))
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
ENV_PATH = PROJECT_DIR / "Gemini本地私密配置.env"
VIDEO_PATH = (
    PROJECT_DIR / "02_别人视频的拆解分析"
    / "2026-06-02_抖音参考视频切片分析包" / "raw_downloads"
    / "01_7634456235240164659_AI集体涨价，免费额度越来越少了？ #AI#GPT#应用.mp4"
)
PROMPT_FILE_PATH = (
    PROJECT_DIR / "04_教AI拉片的提示词"
    / "2026-06-09_17-30_Gemini物理拉片分析prompt_v2.txt"
)
CLIP_PATH = PROJECT_DIR / "temp_vertex_clip.mp4"

# 需要用 google-auth 来生成 Bearer Token
try:
    from google.oauth2 import service_account
    from google.auth.transport.requests import Request as GoogleAuthRequest
    GOOGLE_AUTH_AVAILABLE = True
except ImportError:
    GOOGLE_AUTH_AVAILABLE = False


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


def get_access_token(credentials_path: str) -> str:
    if not GOOGLE_AUTH_AVAILABLE:
        print("错误: 需要安装 google-auth 库")
        print("请运行: pip install google-auth google-auth-httplib2")
        sys.exit(1)

    if not os.path.isabs(credentials_path):
        credentials_path = os.path.join(PROJECT_DIR, credentials_path)

    credentials = service_account.Credentials.from_service_account_file(
        credentials_path,
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )
    credentials.refresh(GoogleAuthRequest())
    return credentials.token


def crop_video_segment(start_sec: int, end_sec: int, max_dim: int = 640) -> Path:
    print(f"正在读取源视频: {VIDEO_PATH}")
    if not VIDEO_PATH.exists():
        raise FileNotFoundError(f"找不到源视频: {VIDEO_PATH}")

    cap = cv2.VideoCapture(str(VIDEO_PATH))
    if not cap.isOpened():
        raise RuntimeError("无法打开源视频")

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    if width > max_dim or height > max_dim:
        if width > height:
            target_w, target_h = max_dim, int(height * (max_dim / width))
        else:
            target_h, target_w = max_dim, int(width * (max_dim / height))
    else:
        target_w, target_h = width, height

    duration = end_sec - start_sec
    total_frames = int(fps * duration)
    start_frame = int(fps * start_sec)

    print(f"视频属性: FPS={fps:.2f}, {width}x{height} → {target_w}x{target_h}")
    print(f"裁剪时段: {start_sec}s - {end_sec}s ({duration}s, {total_frames} 帧)")

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(CLIP_PATH), fourcc, fps, (target_w, target_h))

    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    frame_count = 0
    while frame_count < total_frames:
        ret, frame = cap.read()
        if not ret:
            break
        if width != target_w or height != target_h:
            frame = cv2.resize(frame, (target_w, target_h), interpolation=cv2.INTER_AREA)
        out.write(frame)
        frame_count += 1

    cap.release()
    out.release()
    print(f"裁剪完成: {CLIP_PATH} ({frame_count} 帧, {CLIP_PATH.stat().st_size / 1024 / 1024:.2f} MB)")
    return CLIP_PATH


def load_prompt(start_sec: int, end_sec: int) -> str:
    if not PROMPT_FILE_PATH.exists():
        raise FileNotFoundError(f"找不到 prompt 模板: {PROMPT_FILE_PATH}")
    text = PROMPT_FILE_PATH.read_text(encoding="utf-8")
    text = text.replace("前 30 秒（00:00 - 00:30）", f"{start_sec:02d}:00 - {start_sec // 60:02d}:{start_sec % 60:02d} - {end_sec // 60:02d}:{end_sec % 60:02d}")
    text = text.replace("00:00 - 00:30", f"{start_sec // 60:02d}:{start_sec % 60:02d} - {end_sec // 60:02d}:{end_sec % 60:02d}")
    return text


def call_vertex_api(env: dict, payload: dict, timeout: int = 300) -> str:
    token = get_access_token(env["VERTEX_CREDENTIALS_PATH"])
    project_id = env["VERTEX_PROJECT_ID"]
    location = env.get("VERTEX_LOCATION", "us-central1")
    model = env.get("GEMINI_MODEL", "gemini-2.5-flash")
    proxy = env.get("GEMINI_PROXY")

    url = (
        f"https://{location}-aiplatform.googleapis.com"
        f"/v1/projects/{project_id}/locations/{location}"
        f"/publishers/google/models/{model}:streamGenerateContent"
    )

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": "vertex-ai-gemini-video/1.0",
    }

    print(f"模型: {model} | 端点: {location} | 项目: {project_id}")

    proxy_handler = request.ProxyHandler({"http": proxy, "https": proxy}) if proxy else request.ProxyHandler({})
    opener = request.build_opener(proxy_handler)

    try:
        req = request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
    except Exception as e:
        raise RuntimeError(f"构建请求失败: {e}")

    start_time = time.time()
    all_text = []

    try:
        with opener.open(req, timeout=timeout) as resp:
            for line in resp:
                line_str = line.decode("utf-8").strip()
                if not line_str.startswith("data: "):
                    continue
                json_str = line_str[len("data: "):].strip()
                if not json_str:
                    continue
                try:
                    chunk = json.loads(json_str)
                    candidates = chunk.get("candidates", [])
                    if not candidates:
                        continue
                    parts = candidates[0].get("content", {}).get("parts", [])
                    text = "".join(p.get("text", "") for p in parts)
                    if text:
                        print(text, end="", flush=True)
                        all_text.append(text)
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue

        elapsed = time.time() - start_time
        print(f"\n用时 {elapsed:.1f}s")
        return "".join(all_text)

    except error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Vertex AI 请求失败 (HTTP {exc.code}): {err_body[:500]}")
    except Exception as exc:
        raise RuntimeError(f"网络请求失败: {exc}")


def run_text_chat(env: dict):
    question = sys.argv[sys.argv.index("--text") + 1] if "--text" in sys.argv else "你好，简单介绍一下你自己"
    payload = {
        "contents": [{
            "role": "user",
            "parts": [{"text": question}]
        }]
    }
    result = call_vertex_api(env, payload)
    output_file = PROJECT_DIR / "02_别人视频的拆解分析" / "vertex_text_test_output.md"
    output_file.write_text(
        f"# Vertex AI 文本测试\n\n"
        f"时间: {datetime.now(BEIJING).strftime('%Y-%m-%d %H:%M（北京时间）')}\n"
        f"模型: {env.get('GEMINI_MODEL', 'gemini-2.5-flash')}\n\n"
        f"## 问题\n\n{question}\n\n## 回答\n\n{result}\n",
        encoding="utf-8",
    )
    print(f"\n结果已保存: {output_file}")


def run_video_analysis(env: dict, start_sec: int, end_sec: int):
    clip_path = crop_video_segment(start_sec, end_sec)
    video_bytes = clip_path.read_bytes()
    video_b64 = base64.b64encode(video_bytes).decode("ascii")

    mime_type = "video/mp4"
    prompt_text = load_prompt(start_sec, end_sec)

    payload = {
        "contents": [{
            "role": "user",
            "parts": [
                {"text": prompt_text},
                {"inlineData": {"mimeType": mime_type, "data": video_b64}},
            ]
        }]
    }

    model = env.get("GEMINI_MODEL", "gemini-2.5-flash")
    print(f"\n=== Vertex AI 视频分析: {start_sec}s-{end_sec}s ({model}) ===\n")

    result = call_vertex_api(env, payload)

    ts = datetime.now(BEIJING).strftime("%Y-%m-%d_%H-%M")
    output_name = f"{ts}_VertexAI_视频分析结果_抖音AI涨价_{start_sec}-{end_sec}s_{model}.md"
    output_path = PROJECT_DIR / "02_别人视频的拆解分析" / output_name
    output_path.write_text(
        f"# Vertex AI 视频分析结果\n\n"
        f"分析时间: {datetime.now(BEIJING).strftime('%Y-%m-%d %H:%M（北京时间）')}\n"
        f"模型: `{model}` | 认证: Service Account\n"
        f"分析时段: {start_sec}s - {end_sec}s\n\n"
        f"## 结果\n\n{result}\n",
        encoding="utf-8",
    )
    print(f"\n结果已保存: {output_path}")

    if clip_path.exists():
        clip_path.unlink()
        print("已清理临时视频文件")


def main():
    parser = argparse.ArgumentParser(description="Vertex AI Gemini 视频分析")
    parser.add_argument("--text", type=str, nargs="?", const="你好", help="文本对话模式")
    parser.add_argument("--start", type=int, default=0, help="起始秒数（默认 0）")
    parser.add_argument("--end", type=int, default=30, help="结束秒数（默认 30）")
    args = parser.parse_args()

    env = load_env()

    required = ["VERTEX_PROJECT_ID", "VERTEX_CREDENTIALS_PATH"]
    missing = [k for k in required if not env.get(k)]
    if missing:
        print(f"错误: .env 文件缺少必要配置: {', '.join(missing)}")
        print("请参考教程: 2026-06-10_20-30_Google_Vertex_AI_Gemini接入教程.md")
        return

    if not os.path.isabs(env["VERTEX_CREDENTIALS_PATH"]):
        creds_full = os.path.join(PROJECT_DIR, env["VERTEX_CREDENTIALS_PATH"])
    else:
        creds_full = env["VERTEX_CREDENTIALS_PATH"]
    if not os.path.exists(creds_full):
        print(f"错误: 找不到服务账号密钥文件: {creds_full}")
        return

    if "--text" in sys.argv:
        run_text_chat(env)
    else:
        run_video_analysis(env, args.start, args.end)


if __name__ == "__main__":
    main()
