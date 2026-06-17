#!/usr/bin/env python3
"""
实验脚本：上传完整视频（缩放到 max_dim=640），通过 Prompt 指定时段进行拉片分析。
用于验证"全量上传 + 分段 Prompt"策略的可行性。

使用 OpenRouter + google/gemini-3.5-flash, reasoning effort=high
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
from urllib import request, error

# 配置路径
SCRIPT_DIR = Path(__file__).resolve().parent
VIDEO_PATH = SCRIPT_DIR.parent / "02_别人视频的拆解分析" / "2026-06-02_抖音参考视频切片分析包" / "raw_downloads" / "01_7634456235240164659_AI集体涨价，免费额度越来越少了？ #AI#GPT#应用.mp4"
ENV_PATH = SCRIPT_DIR.parent / "Gemini本地私密配置.env"
PROMPT_FILE_PATH = SCRIPT_DIR.parent / "提示词" / "2026-06-17_15-50_Gemini工业级原片后期解耦拉片分析prompt_v4.txt"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OUTPUT_DIR = SCRIPT_DIR.parent / "02_别人视频的拆解分析"

# 北京时区
BEIJING = timezone(timedelta(hours=8))

# gemini-3.5-flash 在 OpenRouter 上的定价
# Input: $0.15/M tokens, Output: $0.60/M tokens (非思考)
# 思考 tokens: $0.60/M tokens
# 参考 https://openrouter.ai/google/gemini-3.5-flash
INPUT_PRICE_PER_M = 0.15
OUTPUT_PRICE_PER_M = 0.60


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


def encode_full_video(max_dim=640, target_fps=10) -> str:
    """读取完整视频，缩放到 max_dim 并降帧率到 target_fps，编码为 base64 字符串。

    降帧率是因为 OpenCV mp4v 编码器压缩效率远低于 H.264，
    30fps 全帧输出会导致文件膨胀（原始 12MB → mp4v 46MB），
    降到 10fps 可以控制在 ~20MB，base64 后 ~27MB，在 OpenRouter 可接受范围内。
    """
    print(f"正在读取源视频文件: {VIDEO_PATH}")
    if not VIDEO_PATH.exists():
        raise FileNotFoundError(f"找不到源视频：{VIDEO_PATH}")

    cap = cv2.VideoCapture(str(VIDEO_PATH))
    if not cap.isOpened():
        raise RuntimeError("无法打开源视频")

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0

    # 计算缩放尺寸
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

    # 帧率降采样间隔
    frame_interval = max(1, round(fps / target_fps))
    actual_fps = fps / frame_interval

    print(f"视频属性: FPS={fps:.2f}, 原始尺寸={width}x{height}, 时长={duration:.1f}s, 总帧数={total_frames}")
    print(f"缩放目标: {target_width}x{target_height} (max_dim={max_dim})")
    print(f"帧率降采样: {fps:.0f}fps → {actual_fps:.1f}fps (每 {frame_interval} 帧取 1 帧)")

    # 写入临时文件
    temp_path = SCRIPT_DIR.parent / "temp_fullvideo_scaled.mp4"
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(temp_path), fourcc, actual_fps, (target_width, target_height))

    print("开始缩放并降采样完整视频...")
    frame_idx = 0
    written = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % frame_interval == 0:
            if width != target_width or height != target_height:
                frame = cv2.resize(frame, (target_width, target_height), interpolation=cv2.INTER_AREA)
            out.write(frame)
            written += 1
        frame_idx += 1
        if frame_idx % 300 == 0:
            print(f"  已处理 {frame_idx}/{total_frames} 帧 (已写入 {written})...")

    cap.release()
    out.release()
    print(f"缩放完成! 读取 {frame_idx} 帧，写入 {written} 帧，临时文件: {temp_path}")

    # 读取并编码为 base64
    print("正在将完整视频转换为 Base64 编码...")
    video_bytes = temp_path.read_bytes()
    file_size_mb = len(video_bytes) / (1024 * 1024)
    print(f"缩放后视频大小: {file_size_mb:.2f} MB")

    base64_str = base64.b64encode(video_bytes).decode("utf-8")
    base64_size_mb = len(base64_str) / (1024 * 1024)
    print(f"Base64 编码后大小: {base64_size_mb:.2f} MB")

    # 清理临时文件
    temp_path.unlink()
    print("已清理临时视频文件")

    return base64_str


def build_prompt(start_sec: int, end_sec: int) -> str:
    """加载 v4 prompt 模板并追加当前分段时间范围。"""
    if not PROMPT_FILE_PATH.exists():
        raise FileNotFoundError(f"找不到 prompt 模板文件: {PROMPT_FILE_PATH}")

    prompt_text = PROMPT_FILE_PATH.read_text(encoding="utf-8")

    start_mm_ss = f"{start_sec // 60:02d}:{start_sec % 60:02d}"
    end_mm_ss = f"{end_sec // 60:02d}:{end_sec % 60:02d}"
    segment_desc = f"{start_mm_ss} - {end_mm_ss}"

    prompt_text = (
        f"{prompt_text.rstrip()}\n\n"
        f"本次只分析目标视频的 **{segment_desc}** 时段。"
        "如果视频是完整上传的，请不要分析这个时间段之外的内容。"
    )

    print(f"Prompt 已配置为分析时段: {segment_desc}")
    return prompt_text


def call_openrouter(api_key: str, proxy: str, base64_video: str, prompt_text: str, timeout: int = 600):
    """调用 OpenRouter API 进行流式多模态分析。"""
    payload = {
        "model": "google/gemini-3.5-flash",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_text},
                    {
                        "type": "video_url",
                        "video_url": {
                            "url": f"data:video/mp4;base64,{base64_video}"
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

    print(f"正在连接 OpenRouter (google/gemini-3.5-flash, reasoning=high)...")
    print(f"Timeout 设置: {timeout}s")

    proxy_handler = request.ProxyHandler({"http": proxy, "https": proxy}) if proxy else request.ProxyHandler({})
    opener = request.build_opener(proxy_handler)

    req = request.Request(
        OPENROUTER_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "gemini-video-segment-experiment/1.0"
        },
        method="POST"
    )

    full_content_chunks = []
    usage_data = {}
    start_time = time.time()

    with opener.open(req, timeout=timeout) as resp:
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
                        # 打印错误信息
                        if "error" in chunk:
                            print(f"\n[API ERROR] {chunk['error']}", flush=True)
                        # 提取 usage
                        if "usage" in chunk and chunk["usage"]:
                            usage_data = chunk["usage"]
                    except Exception as e:
                        print(f"\n[PARSE ERROR] {e}: {json_str[:200]}", flush=True)
                        continue
        print("\n=============================\n")

    elapsed = time.time() - start_time
    content = "".join(full_content_chunks)

    return content, usage_data, elapsed


def main():
    parser = argparse.ArgumentParser(description="全量视频上传 + 分段 Prompt 实验")
    parser.add_argument("--start", type=int, required=True, help="分析起始秒数")
    parser.add_argument("--end", type=int, required=True, help="分析结束秒数")
    parser.add_argument("--fps", type=int, default=10, help="目标帧率，默认 10fps（降低以减小传输体积）")
    parser.add_argument("--timeout", type=int, default=600, help="API 请求超时时间（秒），默认 600")
    args = parser.parse_args()

    start_sec = args.start
    end_sec = args.end

    if start_sec >= end_sec:
        print("错误: --start 必须小于 --end")
        sys.exit(1)

    print(f"=== 全量视频分段实验 ===")
    print(f"分析时段: {start_sec}s - {end_sec}s")
    print(f"时间: {datetime.now(BEIJING).strftime('%Y-%m-%d %H:%M:%S (北京时间)')}")
    print()

    # 加载环境
    env = load_env()
    openrouter_key = env.get("OPENROUTER_API_KEY")
    proxy = env.get("GEMINI_PROXY")

    if not openrouter_key:
        print("错误: 未在 env 文件中找到 OPENROUTER_API_KEY。")
        sys.exit(1)

    try:
        # 1. 编码完整视频
        base64_video = encode_full_video(max_dim=640, target_fps=args.fps)

        # 2. 构建 Prompt
        prompt_text = build_prompt(start_sec, end_sec)

        # 3. 调用 API
        content, usage_data, elapsed = call_openrouter(
            api_key=openrouter_key,
            proxy=proxy,
            base64_video=base64_video,
            prompt_text=prompt_text,
            timeout=args.timeout
        )

        if not content:
            print("警告: API 未返回任何内容！")
            print(f"Usage data: {usage_data}")
            return

        # 4. 计算费用
        prompt_tokens = usage_data.get("prompt_tokens", 0)
        completion_tokens = usage_data.get("completion_tokens", 0)
        cached_tokens = usage_data.get("prompt_tokens_details", {}).get("cached_tokens", 0) if isinstance(usage_data.get("prompt_tokens_details"), dict) else 0

        usd_cost = (prompt_tokens * INPUT_PRICE_PER_M + completion_tokens * OUTPUT_PRICE_PER_M) / 1_000_000
        rmb_cost = usd_cost * 7.25

        start_mm_ss = f"{start_sec // 60:02d}:{start_sec % 60:02d}"
        end_mm_ss = f"{end_sec // 60:02d}:{end_sec % 60:02d}"

        billing_info = (
            f"### Token 消耗与计费统计\n"
            f"- **模型:** google/gemini-3.5-flash (reasoning=high)\n"
            f"- **分析时段:** {start_mm_ss} - {end_mm_ss}\n"
            f"- **视频上传方式:** 完整视频（缩放到 640p, {args.fps}fps）\n"
            f"- **输入 Token (Prompt Tokens):** {prompt_tokens}\n"
            f"- **输出 Token (Completion Tokens):** {completion_tokens}\n"
            f"- **缓存 Token (Cached Tokens):** {cached_tokens}\n"
            f"- **估算费用:** ${usd_cost:.6f} USD (折合人民币约 ¥{rmb_cost:.4f} 元)\n"
            f"- **响应耗时:** {elapsed:.1f}s\n"
        )

        print(billing_info)
        print(f"输出字符数: {len(content)}")

        # 5. 判断是否截断
        is_truncated = not content.rstrip().endswith(("。", "）", "}", "|", "）", "\n"))
        # 更精确的判断：检查输出是否在表格中途断裂
        if completion_tokens >= 65000:
            is_truncated = True
        truncation_note = "可能截断" if is_truncated else "完整"

        print(f"完整度判断: {truncation_note}")

        # 6. 保存结果
        now_str = datetime.now(BEIJING).strftime('%Y-%m-%d_%H-%M')
        output_file_name = f"{now_str}_E{'1' if start_sec == 0 else '2'}_全量视频分段分析_{start_mm_ss}-{end_mm_ss}_gemini-3.5-flash.md"
        output_path = OUTPUT_DIR / output_file_name

        output_content = (
            f"# 全量视频分段实验：分析 {start_mm_ss} - {end_mm_ss}\n\n"
            f"分析时间：{datetime.now(BEIJING).strftime('%Y-%m-%d %H:%M（北京时间）')}\n"
            f"模型：`google/gemini-3.5-flash` (reasoning=high)\n"
            f"视频上传方式：完整视频缩放到 640p@{args.fps}fps 后上传\n\n"
            f"{billing_info}\n"
            f"### 完整度\n"
            f"- 状态: {truncation_note}\n"
            f"- 输出字符数: {len(content)}\n\n"
            f"---\n\n"
            f"## 分析结果\n\n{content}\n"
        )

        output_path.write_text(output_content, encoding="utf-8")
        print(f"\n分析结果已保存至: {output_path}")

        # 7. 打印汇总（方便复制到实验计划文档）
        print(f"\n=== 实验结果汇总行 ===")
        print(f"| {datetime.now(BEIJING).strftime('%m-%d %H:%M')} | gemini-3.5-flash | OpenRouter | {start_mm_ss}-{end_mm_ss} (全量) | {prompt_tokens} | {completion_tokens} | ¥{rmb_cost:.2f} | {truncation_note} | 全量上传实验 |")

    except error.HTTPError as exc:
        err_body = exc.read().decode('utf-8', errors='replace')
        print(f"OpenRouter API 请求失败 (HTTP {exc.code}): {err_body}")
    except Exception as exc:
        import traceback
        print(f"执行过程中发生异常: {exc}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
