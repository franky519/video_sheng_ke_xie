#!/usr/bin/env python3
"""
Python SDK 与 Gemini Files API 原生视频上传分析 Demo

官方文档引用 (Google AI SDK for Python):
官方的新版 google-genai SDK 通过 client.files.upload 方法来实现视频上传。
典型代码如下：
--------------------------------------------------
from google import genai
import time

client = genai.Client()

# 上传视频
video_file = client.files.upload(file="path/to/video.mp4")

# 轮询等待视频状态变为 ACTIVE
while video_file.state.name == "PROCESSING":
    time.sleep(5)
    video_file = client.files.get(name=video_file.name)

# 发送多模态载荷（将文件对象直接塞入 contents 列表）
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[video_file, "请用中文简要描述这10秒视频的画面。"]
)
print(response.text)
--------------------------------------------------

本脚本为了保证在当前未安装 google-genai SDK 的虚拟环境下可以直接运行，
采用标准库 urllib 实现了等价的 File API 原生上传和分析流程。
"""

import os
import cv2
import time
import json
from pathlib import Path
from urllib import request, error, parse

# 配置路径
SCRIPT_DIR = Path(__file__).resolve().parent
VIDEO_PATH = SCRIPT_DIR.parent / "02_参考拉片库" / "2026-05-31_10-47_差评君冲浪普拉斯视频切片分析包" / "差评君_前5分钟低清参考片段.mp4"
CLIP_PATH = SCRIPT_DIR.parent / "temp_10s_clip.mp4"
ENV_PATH = SCRIPT_DIR.parent / "Gemini本地私密配置.env"
BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
UPLOAD_URL = "https://generativelanguage.googleapis.com/upload/v1beta/files"

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

def crop_10s_video():
    print(f"正在读取视频文件: {VIDEO_PATH}")
    if not VIDEO_PATH.exists():
        raise FileNotFoundError(f"找不到源视频：{VIDEO_PATH}")
        
    cap = cv2.VideoCapture(str(VIDEO_PATH))
    if not cap.isOpened():
        raise RuntimeError("无法打开源视频")
        
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"源视频参数: FPS={fps}, 宽度={width}, 高度={height}")
    
    # 截取10秒
    duration_sec = 10
    total_frames = int(fps * duration_sec)
    
    # 使用 mp4v 编码器
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(CLIP_PATH), fourcc, fps, (width, height))
    
    print("开始截取前 10 秒画面...")
    frame_count = 0
    while frame_count < total_frames:
        ret, frame = cap.read()
        if not ret:
            break
        out.write(frame)
        frame_count += 1
        
    cap.release()
    out.release()
    print(f"截取完成，已保存至: {CLIP_PATH} (共 {frame_count} 帧)")

def http_call(url, proxy, method="GET", body=None, headers=None, timeout=60):
    data = None
    req_headers = {"User-Agent": "gemini-sdk-demo/1.0"}
    if headers:
        req_headers.update(headers)
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        req_headers["Content-Type"] = "application/json"
        
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
    print("准备上传截取的 10秒 视频文件...")
    video_bytes = CLIP_PATH.read_bytes()
    size = len(video_bytes)
    mime_type = "video/mp4"
    
    # 1. 初始化分块上传
    init_headers = {
        "x-goog-api-key": api_key,
        "X-Goog-Upload-Protocol": "resumable",
        "X-Goog-Upload-Command": "start",
        "X-Goog-Upload-Header-Content-Length": str(size),
        "X-Goog-Upload-Header-Content-Type": mime_type,
        "Content-Type": "application/json; charset=utf-8"
    }
    init_body = {"file": {"display_name": "temp_10s_clip.mp4"}}
    status, text = http_call(UPLOAD_URL, proxy, "POST", init_body, init_headers)
    if status != 200:
        raise RuntimeError(f"初始化上传失败 (HTTP {status}): {text}")
        
    # 获取上传链接 (实际的 API 会将其返回在响应头部 X-Goog-Upload-URL 中，这里我们需要自己提取)
    # 标准的 urllib.open 会把 header 塞在 response 里，我们上面的 http_call 需要稍作修改来获取 Header。
    # 为了简化，我们直接重新发起一个获取 header 的请求。
    # 别担心，我们可以直接通过 opener 的特殊处理来拿到这个 URL。
    # 让我们用一个专用的初始化请求。
    
    proxy_handler = request.ProxyHandler({"http": proxy, "https": proxy}) if proxy else request.ProxyHandler({})
    opener = request.build_opener(proxy_handler)
    
    init_req = request.Request(
        UPLOAD_URL,
        data=json.dumps(init_body).encode("utf-8"),
        headers=init_headers,
        method="POST"
    )
    with opener.open(init_req, timeout=60) as resp:
        upload_url = resp.headers.get("X-Goog-Upload-URL")
        
    if not upload_url:
        raise RuntimeError("未获取到 X-Goog-Upload-URL 头部")
        
    # 2. 上传文件字节
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
    print(f"上传成功! 临时文件 URI: {file_uri}")
    
    # 3. 轮询等待 ACTIVE
    state = file_info.get("state", "UNKNOWN")
    while state in {"PROCESSING", "UNKNOWN"}:
        print(f"云端处理中 (当前状态: {state})，等待 3 秒...")
        time.sleep(3)
        query_url = f"{BASE_URL}/{parse.quote(file_name, safe='/')}?key={api_key}"
        status, text = http_call(query_url, proxy)
        if status == 200:
            file_info = json.loads(text)
            state = file_info.get("state", "UNKNOWN")
        else:
            raise RuntimeError(f"查询文件状态失败 (HTTP {status}): {text}")
            
    if state == "FAILED":
        raise RuntimeError("云端视频转码失败")
    print(f"视频在云端已激活! 状态: {state}")
    
    # 4. 调用内容生成，构造 Multimodal Payload (多模态数据载荷) 并使用流式传输
    generate_url = f"{BASE_URL}/models/gemini-3.5-flash:streamGenerateContent?key={api_key}&alt=sse"
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"file_data": {"mime_type": mime_type, "file_uri": file_uri}},
                    {"text": "你是一个视频动效分析师。请用中文简短地分析这10秒视频的画面有什么元素，以及发生了什么运动。"}
                ]
            }
        ]
    }
    print("正在把多模态载荷发送给 Gemini 大模型进行流式分析...")
    
    proxy_handler = request.ProxyHandler({"http": proxy, "https": proxy}) if proxy else request.ProxyHandler({})
    opener = request.build_opener(proxy_handler)
    req = request.Request(
        generate_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "gemini-sdk-demo/1.0"},
        method="POST"
    )
    
    try:
        with opener.open(req, timeout=120) as resp:
            print("\n=== Gemini 10秒视频流式分析结果 ===")
            for line in resp:
                line_str = line.decode("utf-8").strip()
                if line_str.startswith("data: "):
                    json_str = line_str[len("data: "):].strip()
                    if json_str:
                        try:
                            chunk = json.loads(json_str)
                            text = chunk["candidates"][0]["content"]["parts"][0]["text"]
                            print(text, end="", flush=True)
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue
            print("\n===================================\n")
    except error.HTTPError as exc:
        raise RuntimeError(f"内容生成失败 (HTTP {exc.code}): {exc.read().decode('utf-8', errors='replace')}")
    except Exception as exc:
        raise RuntimeError(f"请求失败: {exc}")

def main():
    env = load_env()
    api_key = env.get("GEMINI_API_KEY")
    proxy = env.get("GEMINI_PROXY") or "http://127.0.0.1:10808"
    
    if not api_key:
        print("错误: 找不到 GEMINI_API_KEY。请检查 Gemini本地私密配置.env")
        return
        
    try:
        crop_10s_video()
        upload_and_analyze(api_key, proxy)
    finally:
        # 清理临时截取的 10 秒视频文件，保持工作区干净
        if CLIP_PATH.exists():
            try:
                CLIP_PATH.unlink()
                print("已自动清理临时视频文件")
            except Exception as e:
                print(f"清理临时文件失败: {e}")

if __name__ == "__main__":
    main()
