#!/usr/bin/env python3
"""
使用 Gemini 原生 API 对视频前1分钟进行精细拆解分析 (支持流式输出与多模型 Fallback)
"""

import os
import cv2
import time
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from urllib import request, error, parse

# 配置路径
SCRIPT_DIR = Path(__file__).resolve().parent
VIDEO_PATH = SCRIPT_DIR.parent / "02_参考拉片库" / "2026-05-31_10-47_差评君冲浪普拉斯视频切片分析包" / "差评君_前5分钟低清参考片段.mp4"
CLIP_PATH = SCRIPT_DIR.parent / "temp_1m_clip.mp4"
ENV_PATH = SCRIPT_DIR.parent / "Gemini本地私密配置.env"
PROMPT_FILE_PATH = SCRIPT_DIR.parent / "04_提示词工程" / "2026-06-02_11-45_Gemini物理拉片分析prompt.txt"
BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
UPLOAD_URL = "https://generativelanguage.googleapis.com/upload/v1beta/files"

# 北京时区
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

def crop_60s_video():
    print(f"正在读取源视频文件: {VIDEO_PATH}")
    if not VIDEO_PATH.exists():
        raise FileNotFoundError(f"找不到源视频：{VIDEO_PATH}")
        
    cap = cv2.VideoCapture(str(VIDEO_PATH))
    if not cap.isOpened():
        raise RuntimeError("无法打开源视频")
        
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"视频属性: FPS={fps:.2f}, 宽度={width}, 高度={height}")
    
    # 截取60秒
    duration_sec = 60
    total_frames = int(fps * duration_sec)
    
    # 使用 mp4v 编码器
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(CLIP_PATH), fourcc, fps, (width, height))
    
    print("开始裁剪前 60 秒画面...")
    frame_count = 0
    while frame_count < total_frames:
        ret, frame = cap.read()
        if not ret:
            break
        out.write(frame)
        frame_count += 1
        
    cap.release()
    out.release()
    print(f"裁剪完成! 已保存至: {CLIP_PATH} (共写入 {frame_count} 帧)")

def http_call(url, proxy, method="GET", body=None, headers=None, timeout=120):
    data = None
    req_headers = {"User-Agent": "gemini-video-analysis/1.0"}
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

def upload_and_analyze(api_key, proxy):
    print(f"正在上传 60秒 视频 ({CLIP_PATH.stat().st_size / 1024 / 1024:.2f} MB)...")
    video_bytes = CLIP_PATH.read_bytes()
    size = len(video_bytes)
    mime_type = "video/mp4"
    
    proxy_handler = request.ProxyHandler({"http": proxy, "https": proxy}) if proxy else request.ProxyHandler({})
    opener = request.build_opener(proxy_handler)
    
    # 1. 初始化分块上传
    init_headers = {
        "x-goog-api-key": api_key,
        "X-Goog-Upload-Protocol": "resumable",
        "X-Goog-Upload-Command": "start",
        "X-Goog-Upload-Header-Content-Length": str(size),
        "X-Goog-Upload-Header-Content-Type": mime_type,
        "Content-Type": "application/json; charset=utf-8"
    }
    init_body = {"file": {"display_name": "temp_1m_clip.mp4"}}
    
    init_req = request.Request(
        UPLOAD_URL,
        data=json.dumps(init_body).encode("utf-8"),
        headers=init_headers,
        method="POST"
    )
    with opener.open(init_req, timeout=60) as resp:
        upload_url = resp.headers.get("X-Goog-Upload-URL")
        
    if not upload_url:
        raise RuntimeError("未获取到 X-Goog-Upload-URL 头部，无法初始化分块上传")
        
    # 2. 上传文件字节
    print("开始推送视频 data 字节...")
    upload_req = request.Request(
        upload_url,
        data=video_bytes,
        headers={
            "Content-Type": mime_type,
            "Content-Length": str(size),
            "X-Goog-Upload-Offset": "0",
            "X-Goog-Upload-Command": "upload, finalize",
        },
        method="POST"
    )
    with opener.open(upload_req, timeout=300) as resp:
        uploaded_data = json.loads(resp.read().decode("utf-8"))
        
    file_info = uploaded_data.get("file", uploaded_data)
    file_uri = file_info["uri"]
    file_name = file_info["name"]
    print(f"上传成功! 临时视频 URI: {file_uri}")
    
    # 3. 轮询等待 ACTIVE (每隔 5 秒检查一次)
    state = file_info.get("state", "UNKNOWN")
    while state in {"PROCESSING", "UNKNOWN"}:
        print(f"云端正在解码抽帧中 (状态: {state})，等待 5 秒...")
        time.sleep(5)
        query_url = f"{BASE_URL}/{parse.quote(file_name, safe='/')}?key={api_key}"
        status, text = http_call(query_url, proxy)
        if status == 200:
            file_info = json.loads(text)
            state = file_info.get("state", "UNKNOWN")
        else:
            raise RuntimeError(f"查询文件状态失败 (HTTP {status}): {text}")
            
    if state == "FAILED":
        raise RuntimeError("云端视频分析转码失败")
    print(f"视频在云端已转码激活! 状态: {state}")
    
    # 4. 加载并修改提示词
    if not PROMPT_FILE_PATH.exists():
        raise FileNotFoundError(f"找不到 prompt 模板文件: {PROMPT_FILE_PATH}")
    prompt_text = PROMPT_FILE_PATH.read_text(encoding="utf-8")
    
    # 将 prompt 中的分析时段限制从“前 30 秒”动态改为“前 1 分钟”
    prompt_text = prompt_text.replace("前 30 秒（00:00 - 00:30）", "前 1 分钟（00:00 - 01:00）")
    
    # 5. 调用 streamGenerateContent 端点 (支持 fallback)
    models_to_try = ["gemini-3.1-pro-preview", "gemini-3.1-flash-lite"]
    content = ""
    
    for model_name in models_to_try:
        generate_url = f"{BASE_URL}/models/{model_name}:streamGenerateContent?key={api_key}&alt=sse"
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"file_data": {"mime_type": mime_type, "file_uri": file_uri}},
                        {"text": prompt_text}
                    ]
                }
            ]
        }
        print(f"正在向 {model_name} 发起原生多模态视频流式分析请求...")

        proxy_handler = request.ProxyHandler({"http": proxy, "https": proxy}) if proxy else request.ProxyHandler({})
        opener = request.build_opener(proxy_handler)
        req = request.Request(
            generate_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "gemini-video-analysis/1.0"},
            method="POST"
        )
        
        full_content_chunks = []
        try:
            with opener.open(req, timeout=300) as resp:
                print(f"\n=== {model_name} 流式分析中 ===")
                for line in resp:
                    line_str = line.decode("utf-8").strip()
                    if line_str.startswith("data: "):
                        json_str = line_str[len("data: "):].strip()
                        if json_str:
                            try:
                                chunk = json.loads(json_str)
                                text = chunk["candidates"][0]["content"]["parts"][0]["text"]
                                print(text, end="", flush=True)
                                full_content_chunks.append(text)
                            except (json.JSONDecodeError, KeyError, IndexError):
                                continue
                print("\n====================================\n")
                
            content = "".join(full_content_chunks)
            if content:
                # 成功获取内容，写入 Markdown 分析文件并退出循环
                output_file_name = f"2026-06-01_21-20_Gemini_视频分析结果_差评君_1m.md"
                output_path = SCRIPT_DIR.parent / "02_参考拉片库" / "AI_原始输出" / output_file_name
                output_path.write_text(
                    f"# Gemini 视频分析结果：差评君_前5分钟低清参考片段.mp4（前 1 分钟）\n\n"
                    f"分析时间：{datetime.now(BEIJING).strftime('%Y-%m-%d %H:%M（北京时间）')}\n"
                    f"使用模型：`{model_name}`\n\n"
                    f"## 结果内容\n\n{content}\n",
                    encoding="utf-8"
                )
                print(f"分析结果已保存至本地文件: {output_path}")
                break
                
        except error.HTTPError as exc:
            err_body = exc.read().decode('utf-8', errors='replace')
            if exc.code in {429, 503} and model_name != models_to_try[-1]:
                print(f"\n[Fallback] 模型 {model_name} 返回 HTTP {exc.code} (可能负载过高或限频)，正在自动切换备用模型...")
                continue
            else:
                raise RuntimeError(f"视频流式分析生成失败 (HTTP {exc.code}): {err_body}")
        except Exception as exc:
            if model_name != models_to_try[-1]:
                print(f"\n[Fallback] 请求 {model_name} 失败: {exc}，正在尝试备用模型...")
                continue
            else:
                raise RuntimeError(f"网络请求失败: {exc}")

def main():
    env = load_env()
    api_key = env.get("GEMINI_API_KEY")
    proxy = env.get("GEMINI_PROXY") or "http://127.0.0.1:10808"
    
    if not api_key:
        print("错误: 找不到 GEMINI_API_KEY，请检查 Gemini本地私密配置.env")
        return
        
    try:
        crop_60s_video()
        upload_and_analyze(api_key, proxy)
    finally:
        # 清理临时截取的 1 分钟视频文件，保持工作区整洁
        if CLIP_PATH.exists():
            try:
                CLIP_PATH.unlink()
                print("已自动清理本地临时视频缓存")
            except Exception as e:
                print(f"清理临时文件失败: {e}")

if __name__ == "__main__":
    main()
