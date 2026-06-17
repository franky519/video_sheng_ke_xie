#!/usr/bin/env python3
"""
分段拉片脚本：按指定时间范围裁剪视频片段，通过 OpenRouter + gemini-3.5-flash 进行拉片分析。

用法：
  python3 此脚本.py --video 源视频.mp4 --start 0 --end 30 --output-dir 输出目录/
  python3 此脚本.py --video 源视频.mp4 --batch  # 自动执行所有 12 段（30s 步进 25s）
"""

import argparse
import base64
import cv2
import json
import sys
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta
from urllib import request, error

SCRIPT_DIR = Path(__file__).resolve().parent
ENV_PATH = SCRIPT_DIR.parent / "Gemini本地私密配置.env"
PROMPT_FILE_PATH = SCRIPT_DIR.parent / "提示词" / "2026-06-17_15-50_Gemini工业级原片后期解耦拉片分析prompt_v4.txt"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
BEIJING = timezone(timedelta(hours=8))

MAX_DIM = 480
MODEL = "google/gemini-3.5-flash"


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


def fmt_time(seconds: int) -> str:
    """将秒数格式化为 MM:SS"""
    m, s = divmod(seconds, 60)
    return f"{m:02d}:{s:02d}"


def fmt_time_filename(seconds: int) -> str:
    """将秒数格式化为文件名友好的 XmYYs"""
    m, s = divmod(seconds, 60)
    return f"{m}m{s:02d}s"


def segment_label(start: int, end: int) -> str:
    """根据起止秒数计算段号标签 S01, S02, ..."""
    # 步进 25s 的段号计算
    idx = start // 25 + 1
    return f"S{idx:02d}"


def crop_video(video_path: Path, clip_path: Path, start_sec: int, end_sec: int):
    """从源视频中裁剪指定时间段，缩放至 MAX_DIM"""
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"无法打开源视频: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    if width > MAX_DIM or height > MAX_DIM:
        if width > height:
            tw = MAX_DIM
            th = int(height * (MAX_DIM / width))
        else:
            th = MAX_DIM
            tw = int(width * (MAX_DIM / height))
    else:
        tw, th = width, height

    start_frame = int(fps * start_sec)
    end_frame = int(fps * end_sec)
    total_frames_in_video = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    end_frame = min(end_frame, total_frames_in_video)

    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(clip_path), fourcc, fps, (tw, th))

    frame_count = 0
    current_frame = start_frame
    while current_frame < end_frame:
        ret, frame = cap.read()
        if not ret:
            break
        if width != tw or height != th:
            frame = cv2.resize(frame, (tw, th), interpolation=cv2.INTER_AREA)
        out.write(frame)
        frame_count += 1
        current_frame += 1

    cap.release()
    out.release()
    actual_duration = frame_count / fps if fps > 0 else 0
    print(f"  裁剪完成: {fmt_time(start_sec)}-{fmt_time(end_sec)}, {frame_count} 帧, {actual_duration:.1f}s, {tw}x{th}")
    return clip_path


def build_prompt(start_sec: int, end_sec: int) -> str:
    """加载 v4 prompt 模板并追加当前分段时间范围。"""
    if not PROMPT_FILE_PATH.exists():
        raise FileNotFoundError(f"找不到 prompt 模板: {PROMPT_FILE_PATH}")
    template = PROMPT_FILE_PATH.read_text(encoding="utf-8")
    start_str = fmt_time(start_sec)
    end_str = fmt_time(end_sec)
    prompt = (
        f"{template.rstrip()}\n\n"
        f"本次只分析目标视频的 **{start_str} - {end_str}** 时段。"
        "如果视频片段本身已经裁剪为这段内容，也请按原片时间轴标注为该绝对时间范围。"
    )
    return prompt


def analyze_segment(openrouter_key: str, proxy: str, video_path: Path,
                    start_sec: int, end_sec: int, output_dir: Path) -> bool:
    """裁剪、上传、分析单个视频段"""
    seg = segment_label(start_sec, end_sec)
    output_name = f"{seg}_{fmt_time_filename(start_sec)}-{fmt_time_filename(end_sec)}.md"
    output_path = output_dir / output_name

    if output_path.exists():
        print(f"[跳过] {output_name} 已存在")
        return True

    clip_path = SCRIPT_DIR.parent / f"temp_clip_{seg}.mp4"
    print(f"\n{'='*60}")
    print(f"[{seg}] {fmt_time(start_sec)} - {fmt_time(end_sec)}")
    print(f"{'='*60}")

    try:
        # 1. 裁剪
        crop_video(video_path, clip_path, start_sec, end_sec)

        # 2. Base64 编码
        video_bytes = clip_path.read_bytes()
        base64_str = base64.b64encode(video_bytes).decode("utf-8")
        payload_size_mb = len(video_bytes) / 1024 / 1024
        print(f"  Base64 payload: {payload_size_mb:.1f} MB")

        # 3. 构造 prompt
        prompt_text = build_prompt(start_sec, end_sec)

        # 4. 发送请求
        payload = {
            "model": MODEL,
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
            "reasoning": {"effort": "high"},
            "stream": True,
            "stream_options": {"include_usage": True}
        }

        proxy_handler = request.ProxyHandler({"http": proxy, "https": proxy}) if proxy else request.ProxyHandler({})
        opener = request.build_opener(proxy_handler)

        req = request.Request(
            OPENROUTER_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {openrouter_key}",
                "Content-Type": "application/json",
                "User-Agent": "video-segment-analyzer/1.0"
            },
            method="POST"
        )

        full_content_chunks = []
        usage_data = {}

        print(f"  正在调用 {MODEL} ...")
        with opener.open(req, timeout=300) as resp:
            for line in resp:
                line_str = line.decode("utf-8").strip()
                if line_str.startswith("data: "):
                    json_str = line_str[len("data: "):].strip()
                    if json_str == "[DONE]":
                        break
                    if json_str:
                        try:
                            chunk = json.loads(json_str)
                            if "choices" in chunk and chunk["choices"]:
                                delta = chunk["choices"][0].get("delta", {})
                                if "content" in delta and delta["content"]:
                                    text = delta["content"]
                                    print(text, end="", flush=True)
                                    full_content_chunks.append(text)
                            if "error" in chunk:
                                print(f"\n  [API ERROR] {chunk['error']}", flush=True)
                            if "usage" in chunk and chunk["usage"]:
                                usage_data = chunk["usage"]
                        except (json.JSONDecodeError, KeyError):
                            continue
            print()

        content = "".join(full_content_chunks)
        if not content:
            print(f"  [失败] {seg} 无输出内容")
            return False

        # 5. 统计 token
        prompt_tokens = usage_data.get("prompt_tokens", 0)
        completion_tokens = usage_data.get("completion_tokens", 0)
        # gemini-3.5-flash OpenRouter: Input ~$0.10/M, Output ~$0.70/M (estimated)
        usd_cost = usage_data.get("cost", (prompt_tokens * 0.10 + completion_tokens * 0.70) / 1000000)

        billing_line = f"Input: {prompt_tokens} tokens, Output: {completion_tokens} tokens"
        print(f"\n  {billing_line}")

        # 6. 保存
        now_str = datetime.now(BEIJING).strftime('%Y-%m-%d %H:%M')
        output_path.write_text(
            f"# 拉片分析 {seg}: {fmt_time(start_sec)}-{fmt_time(end_sec)}\n\n"
            f"分析时间: {now_str}（北京时间）\n"
            f"模型: `{MODEL}` (reasoning=high)\n"
            f"Token: {billing_line}\n\n"
            f"---\n\n{content}\n",
            encoding="utf-8"
        )
        print(f"  已保存: {output_path.name}")
        return True

    except error.HTTPError as exc:
        err_body = exc.read().decode('utf-8', errors='replace')[:500]
        print(f"  [HTTP {exc.code}] {err_body}")
        return False
    except Exception as exc:
        print(f"  [异常] {exc}")
        return False
    finally:
        if clip_path.exists():
            clip_path.unlink()


def get_segments(video_duration_sec: int) -> list[tuple[int, int]]:
    """生成 30s 分段 + 5s 重叠的段列表"""
    segments = []
    start = 0
    step = 25
    seg_len = 30
    while start < video_duration_sec:
        end = min(start + seg_len, video_duration_sec)
        if end - start < 5:  # 末尾碎片太短就跳过
            break
        segments.append((start, end))
        start += step
    return segments


def get_video_duration(video_path: Path) -> float:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"无法打开视频: {video_path}")
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    cap.release()
    return frame_count / fps if fps > 0 else 0


def main():
    parser = argparse.ArgumentParser(description="分段拉片分析脚本")
    parser.add_argument("--video", type=str, required=True, help="源视频路径")
    parser.add_argument("--output-dir", type=str, required=True, help="输出目录")
    parser.add_argument("--start", type=int, help="起始秒数（单段模式）")
    parser.add_argument("--end", type=int, help="结束秒数（单段模式）")
    parser.add_argument("--batch", action="store_true", help="批量模式：自动分段执行所有段")
    args = parser.parse_args()

    video_path = Path(args.video).resolve()
    output_dir = Path(args.output_dir).resolve()

    if not video_path.exists():
        print(f"错误: 找不到视频 {video_path}")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    env = load_env()
    openrouter_key = env.get("OPENROUTER_API_KEY")
    proxy = env.get("GEMINI_PROXY")

    if not openrouter_key:
        print("错误: 未找到 OPENROUTER_API_KEY，请检查 Gemini本地私密配置.env")
        sys.exit(1)

    if args.batch:
        duration = get_video_duration(video_path)
        segments = get_segments(int(duration))
        print(f"视频时长: {duration:.1f}s, 共 {len(segments)} 段")
        print(f"分段列表: {', '.join(f'{fmt_time(s)}-{fmt_time(e)}' for s, e in segments)}")
        print()

        results = []
        for start, end in segments:
            ok = analyze_segment(openrouter_key, proxy, video_path, start, end, output_dir)
            results.append((segment_label(start, end), start, end, ok))
            if ok and (start, end) != segments[-1]:
                print("\n  等待 3s 后继续下一段...")
                time.sleep(3)

        print(f"\n{'='*60}")
        print("批量执行完毕:")
        for seg, s, e, ok in results:
            status = "OK" if ok else "FAIL"
            print(f"  {seg} {fmt_time(s)}-{fmt_time(e)}: {status}")

    elif args.start is not None and args.end is not None:
        analyze_segment(openrouter_key, proxy, video_path, args.start, args.end, output_dir)

    else:
        print("错误: 请指定 --batch 或 --start/--end")
        sys.exit(1)


if __name__ == "__main__":
    main()
