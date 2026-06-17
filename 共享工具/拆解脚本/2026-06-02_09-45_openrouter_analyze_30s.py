#!/usr/bin/env python3
"""
使用 OpenRouter API (google/gemini-3.1-pro-preview) 分析视频前 30 秒，并统计 Token 消耗与计费。
"""

import os
import cv2
import time
import json
import base64
from pathlib import Path
from datetime import datetime, timezone, timedelta
from urllib import request, error, parse

# 配置路径
SCRIPT_DIR = Path(__file__).resolve().parent
VIDEO_PATH = SCRIPT_DIR.parent / "02_别人视频的拆解分析" / "2026-06-02_抖音参考视频切片分析包" / "raw_downloads" / "01_7634456235240164659_AI集体涨价，免费额度越来越少了？ #AI#GPT#应用.mp4"
CLIP_PATH = SCRIPT_DIR.parent / "temp_30s_clip.mp4"
ENV_PATH = SCRIPT_DIR.parent / "Gemini本地私密配置.env"
PROMPT_FILE_PATH = SCRIPT_DIR.parent / "提示词" / "2026-06-17_15-50_Gemini工业级原片后期解耦拉片分析prompt_v4.txt"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

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

def crop_30s_video():
    print(f"正在读取源视频文件: {VIDEO_PATH}")
    if not VIDEO_PATH.exists():
        raise FileNotFoundError(f"找不到源视频：{VIDEO_PATH}")
        
    cap = cv2.VideoCapture(str(VIDEO_PATH))
    if not cap.isOpened():
        raise RuntimeError("无法打开源视频")
        
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # 计算缩放尺寸：最大边限制为 640 像素，等比例缩放以压缩 Base64 传输体积
    max_dim = 640
    if width > max_dim or height > max_dim:
        if width > height:
            target_width = max_dim
            target_height = int(height * (max_dim / width))
        else:
            target_height = max_dim
            target_width = int(width * (max_dim / height))
    else:
        target_width = width
        target_height = height
        
    print(f"视频属性: FPS={fps:.2f}, 宽度={width}, 高度={height} -> 压缩缩放为: {target_width}x{target_height}")
    
    # 截取30秒
    duration_sec = 30
    total_frames = int(fps * duration_sec)
    
    # 使用 mp4v 编码器
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(CLIP_PATH), fourcc, fps, (target_width, target_height))
    
    print("开始裁剪并缩放前 30 秒画面...")
    frame_count = 0
    while frame_count < total_frames:
        ret, frame = cap.read()
        if not ret:
            break
        if width != target_width or height != target_height:
            frame = cv2.resize(frame, (target_width, target_height), interpolation=cv2.INTER_AREA)
        out.write(frame)
        frame_count += 1
        
    cap.release()
    out.release()
    print(f"裁剪完成! 已保存至: {CLIP_PATH} (共写入 {frame_count} 帧)")

def main():
    env = load_env()
    openrouter_key = env.get("OPENROUTER_API_KEY")
    proxy = env.get("GEMINI_PROXY")
    
    if not openrouter_key:
        print("【提示】未在 env 文件中找到 OPENROUTER_API_KEY。")
        print("请提供你的 OpenRouter API key (直接回车输入，或先写入 'Gemini本地私密配置.env' 中):")
        openrouter_key = input("API Key: ").strip()
        if not openrouter_key:
            print("错误: 缺少 OpenRouter API Key，无法继续。")
            return
            
    try:
        # 1. 裁剪视频到 30 秒
        crop_30s_video()
        
        # 2. 读取并 base64 编码
        print("正在将 30秒 视频转换为 Base64 编码...")
        video_bytes = CLIP_PATH.read_bytes()
        base64_str = base64.b64encode(video_bytes).decode("utf-8")
        
        # 3. 加载 prompt
        if not PROMPT_FILE_PATH.exists():
            raise FileNotFoundError(f"找不到 prompt 模板文件: {PROMPT_FILE_PATH}")
        prompt_text = PROMPT_FILE_PATH.read_text(encoding="utf-8")
        
        # 4. 构造 Payload（启用最大思考预算）
        payload = {
            "model": "google/gemini-3.1-pro-preview",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_text},
                        {
                            "type": "video_url",
                            "video_url": {
                                "url": f"data:video/mp4;base64,{base64_str}"
                            }
                        }
                    ]
                }
            ],
            "reasoning": {
                "effort": "high"
            },
            "stream": True,
            "stream_options": {
                "include_usage": True
            }
        }
        
        # 5. 发送 OpenRouter 请求
        print("正在连接 OpenRouter (google/gemini-3.1-pro-preview) 进行流式多模态分析...")
        proxy_handler = request.ProxyHandler({"http": proxy, "https": proxy}) if proxy else request.ProxyHandler({})
        opener = request.build_opener(proxy_handler)
        
        req = request.Request(
            OPENROUTER_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {openrouter_key}",
                "Content-Type": "application/json",
                "User-Agent": "gemini-video-analysis/1.0"
            },
            method="POST"
        )
        
        full_content_chunks = []
        usage_data = {}
        
        with opener.open(req, timeout=300) as resp:
            print("\n=== OpenRouter 流式分析中 ===")
            for line in resp:
                line_str = line.decode("utf-8").strip()
                if line_str.startswith("data: "):
                    json_str = line_str[len("data: "):].strip()
                    if json_str == "[DONE]":
                        break
                    if json_str:
                        try:
                            chunk = json.loads(json_str)
                            # 提取内容
                            if "choices" in chunk and chunk["choices"]:
                                delta = chunk["choices"][0].get("delta", {})
                                if "content" in delta and delta["content"]:
                                    text = delta["content"]
                                    print(text, end="", flush=True)
                                    full_content_chunks.append(text)
                                elif not delta.get("content"):
                                    # 调试：打印非 content 的 delta 键
                                    keys = list(delta.keys())
                                    if keys and keys != ["role"]:
                                        print(f"\n[DEBUG delta keys: {keys}]", flush=True)
                            # 打印错误信息（如果有）
                            if "error" in chunk:
                                print(f"\n[API ERROR] {chunk['error']}", flush=True)
                            # 提取 usage
                            if "usage" in chunk and chunk["usage"]:
                                usage_data = chunk["usage"]
                        except Exception as e:
                            print(f"\n[PARSE ERROR] {e}: {json_str[:200]}", flush=True)
                            continue
            print("\n=============================\n")
            
        content = "".join(full_content_chunks)
        if content:
            # 6. 计算费用
            # OpenRouter 定价: Input = $1.50/M tokens, Output = $9.00/M tokens
            prompt_tokens = usage_data.get("prompt_tokens", 0)
            completion_tokens = usage_data.get("completion_tokens", 0)
            
            usd_cost = (prompt_tokens * 1.50 + completion_tokens * 9.00) / 1000000
            rmb_cost = usd_cost * 7.25  # 估算汇率 7.25
            
            billing_info = (
                f"### Token 消耗与计费统计\n"
                f"- **输入 Token (Prompt Tokens):** {prompt_tokens} (计费单价: $1.50/M tokens)\n"
                f"- **输出 Token (Completion Tokens):** {completion_tokens} (计费单价: $9.00/M tokens)\n"
                f"- **估算费用:** ${usd_cost:.6f} USD (折合人民币约 **¥{rmb_cost:.4f}** 元)\n"
            )
            
            print(billing_info)
            
            # 7. 保存 Markdown
            output_file_name = f"2026-06-09_19-30_OpenRouter_视频分析结果_抖音AI涨价_30s_v2_gemini-3.1-pro.md"
            output_path = SCRIPT_DIR.parent / "02_别人视频的拆解分析" / output_file_name
            output_path.write_text(
                f"# OpenRouter 视频分析结果：抖音AI涨价_30s（使用 gemini-3.5-flash）\n\n"
                f"分析时间：{datetime.now(BEIJING).strftime('%Y-%m-%d %H:%M（北京时间）')}\n"
                f"计费模型：`google/gemini-3.1-pro-preview`\n\n"
                f"{billing_info}\n"
                f"## 结果内容\n\n{content}\n",
                encoding="utf-8"
            )
            print(f"分析结果已保存至本地文件: {output_path}")
            
    except error.HTTPError as exc:
        print(f"OpenRouter API 请求失败 (HTTP {exc.code}): {exc.read().decode('utf-8', errors='replace')}")
    except Exception as exc:
        print(f"执行过程中发生异常: {exc}")
    finally:
        # 清理临时截取的 30 秒视频文件
        if CLIP_PATH.exists():
            try:
                CLIP_PATH.unlink()
                print("已自动清理本地临时视频缓存")
            except Exception as e:
                print(f"清理临时文件失败: {e}")

if __name__ == "__main__":
    main()
