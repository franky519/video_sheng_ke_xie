#!/usr/bin/env python3
"""
OpenRouter 完整视频连续追问探针。

目标：
1. 验证 google/gemini-3.5-flash 是否仍在 OpenRouter 可用，并确认 video 输入模态。
2. 上传一条完整视频后，按 0-20、20-40、40-60 这种方式连续提问。
3. 每一轮都从 OpenRouter generation metadata 读取 total_cost 并打印。
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib import error, parse, request


SCRIPT_DIR = Path(__file__).resolve().parent
ENV_PATH = SCRIPT_DIR.parent.parent / "Gemini本地私密配置.env"
OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"
OPENROUTER_GENERATION_URL = "https://openrouter.ai/api/v1/generation"
DEFAULT_MODEL = "google/gemini-3.5-flash"
DEFAULT_OUTPUT_DIR = SCRIPT_DIR.parent.parent / "标杆视频库" / "_实验记录" / "openrouter_fullvideo_followup"
BEIJING = timezone(timedelta(hours=8))


@dataclass
class VideoPayload:
    mime_type: str
    data_url: str
    byte_size: int = 0
    source_path: Path | None = None


@dataclass
class TurnResult:
    segment: tuple[int, int]
    content: str
    generation_id: str | None = None
    prompt_text: str = ""
    elapsed_sec: float = 0.0
    finish_reason: str | None = None
    cost_usd: float | None = None
    cost_source: str = "unavailable"
    usage: dict[str, Any] | None = None
    generation_metadata: dict[str, Any] | None = None


@dataclass
class CostInfo:
    usd: float | None
    source: str


def now_bj_for_file() -> str:
    return datetime.now(BEIJING).strftime("%Y-%m-%d_%H-%M")


def now_bj_display() -> str:
    return datetime.now(BEIJING).strftime("%Y-%m-%d %H:%M:%S 北京时间")


def fmt_time(seconds: int) -> str:
    minutes, secs = divmod(seconds, 60)
    return f"{minutes:02d}:{secs:02d}"


def load_env(env_path: Path = ENV_PATH) -> dict[str, str]:
    values: dict[str, str] = {}
    if not env_path.exists():
        return values
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def parse_segments(spec: str) -> list[tuple[int, int]]:
    segments: list[tuple[int, int]] = []
    for raw_part in spec.split(","):
        part = raw_part.strip()
        if not part:
            continue
        if "-" not in part:
            raise ValueError(f"分段格式错误：{part}，应类似 0-20")
        start_raw, end_raw = part.split("-", 1)
        start = int(start_raw.strip())
        end = int(end_raw.strip())
        if start < 0 or end <= start:
            raise ValueError(f"分段范围错误：{part}")
        segments.append((start, end))
    if not segments:
        raise ValueError("没有解析到任何分段")
    return segments


def build_segments(segment_seconds: int, max_segments: int, video_duration: int | float | None = None) -> list[tuple[int, int]]:
    if segment_seconds <= 0:
        raise ValueError("--segment-seconds 必须大于 0")
    if max_segments <= 0:
        raise ValueError("--max-segments 必须大于 0")

    segments: list[tuple[int, int]] = []
    start = 0
    for _ in range(max_segments):
        end = start + segment_seconds
        if video_duration is not None:
            if start >= video_duration:
                break
            end = min(end, int(video_duration))
        if end > start:
            segments.append((start, end))
        start += segment_seconds
    return segments


def make_segment_prompt(segment: tuple[int, int], extra_prompt: str | None = None) -> str:
    start, end = segment
    prompt = (
        f"请只分析这条完整视频中的 {fmt_time(start)}-{fmt_time(end)} 这一段。"
        "不要分析其他时间段。\n\n"
        "请用中文输出，控制篇幅，重点回答：\n"
        "1. 这一段实际出现了什么画面变化；\n"
        "2. 能识别到的字幕、屏幕文字或旁白信息；\n"
        "3. 镜头节奏、转场、包装动效有什么特点；\n"
        "4. 哪些地方不确定，需要人工复核。\n"
    )
    if extra_prompt:
        prompt += "\n补充要求：\n" + extra_prompt.strip() + "\n"
    return prompt


def content_with_video(prompt_text: str, video: VideoPayload) -> list[dict[str, Any]]:
    return [
        {"type": "text", "text": prompt_text},
        {"type": "video_url", "video_url": {"url": video.data_url}},
    ]


def build_messages(
    mode: str,
    video: VideoPayload,
    segment: tuple[int, int],
    prompt_text: str,
    history: list[TurnResult],
) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": (
                "你是视频拉片分析助手。用户会按时间段连续追问同一条视频。"
                "必须严格按用户指定时间段回答，不能把其他时间段混进来。"
            ),
        }
    ]

    if mode == "repeat-video":
        for item in history:
            messages.append({"role": "user", "content": item.prompt_text or f"分析 {fmt_time(item.segment[0])}-{fmt_time(item.segment[1])}"})
            messages.append({"role": "assistant", "content": item.content})
        messages.append({"role": "user", "content": content_with_video(prompt_text, video)})
        return messages

    if mode == "carry-first-video":
        if not history:
            messages.append({"role": "user", "content": content_with_video(prompt_text, video)})
            return messages

        first = history[0]
        first_prompt = first.prompt_text or f"分析 {fmt_time(first.segment[0])}-{fmt_time(first.segment[1])}"
        messages.append({"role": "user", "content": content_with_video(first_prompt, video)})
        messages.append({"role": "assistant", "content": first.content})
        for item in history[1:]:
            messages.append({"role": "user", "content": item.prompt_text or f"分析 {fmt_time(item.segment[0])}-{fmt_time(item.segment[1])}"})
            messages.append({"role": "assistant", "content": item.content})
        messages.append({"role": "user", "content": prompt_text})
        return messages

    if mode == "text-followup":
        for item in history:
            messages.append({"role": "user", "content": item.prompt_text or f"分析 {fmt_time(item.segment[0])}-{fmt_time(item.segment[1])}"})
            messages.append({"role": "assistant", "content": item.content})
        if history:
            messages.append({"role": "user", "content": prompt_text})
        else:
            messages.append({"role": "user", "content": content_with_video(prompt_text, video)})
        return messages

    raise ValueError(f"未知追问模式：{mode}")


def extract_cost_usd(generation_metadata: dict[str, Any] | None, stream_usage: dict[str, Any] | None) -> CostInfo:
    data = generation_metadata.get("data", {}) if isinstance(generation_metadata, dict) else {}
    total_cost = data.get("total_cost")
    if isinstance(total_cost, (int, float)):
        return CostInfo(float(total_cost), "generation.total_cost")

    usage_cost = data.get("usage")
    if isinstance(usage_cost, (int, float)):
        return CostInfo(float(usage_cost), "generation.usage")

    if isinstance(stream_usage, dict):
        stream_cost = stream_usage.get("cost")
        if isinstance(stream_cost, (int, float)):
            return CostInfo(float(stream_cost), "stream.usage.cost")

    return CostInfo(None, "unavailable")


def build_opener(proxy_url: str | None) -> request.OpenerDirector:
    if proxy_url:
        return request.build_opener(request.ProxyHandler({"http": proxy_url, "https": proxy_url}))
    return request.build_opener(request.ProxyHandler({}))


def read_json_url(
    opener: request.OpenerDirector,
    url: str,
    headers: dict[str, str] | None = None,
    timeout: int = 60,
) -> dict[str, Any]:
    req = request.Request(url, headers=headers or {}, method="GET")
    with opener.open(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
    return json.loads(raw)


def check_model(model: str, opener: request.OpenerDirector) -> dict[str, Any] | None:
    data = read_json_url(opener, OPENROUTER_MODELS_URL, timeout=60)
    for item in data.get("data", []):
        if item.get("id") == model:
            architecture = item.get("architecture", {})
            modalities = architecture.get("input_modalities", [])
            pricing = item.get("pricing", {})
            print(f"模型确认: {model}")
            print(f"输入模态: {modalities}")
            print(f"官方定价字段: {pricing}")
            if "video" not in modalities:
                print("警告: OpenRouter 模型列表未声明 video 输入，本次视频请求可能失败。")
            return item
    print(f"警告: OpenRouter 模型列表中未找到 {model}。")
    return None


def get_video_info(video_path: Path) -> dict[str, float]:
    import cv2

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"无法打开视频: {video_path}")
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    cap.release()
    duration = frames / fps if fps > 0 else 0
    return {"fps": fps, "width": width, "height": height, "frames": frames, "duration": duration}


def preprocess_full_video(video_path: Path, output_path: Path, max_dim: int, target_fps: int) -> Path:
    import cv2

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"无法打开视频: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if width > max_dim or height > max_dim:
        if width >= height:
            target_width = max_dim
            target_height = int(height * (max_dim / width))
        else:
            target_height = max_dim
            target_width = int(width * (max_dim / height))
    else:
        target_width, target_height = width, height

    frame_interval = max(1, round(fps / target_fps)) if fps > 0 else 1
    actual_fps = fps / frame_interval if fps > 0 else target_fps

    print(f"视频预处理: {width}x{height}@{fps:.2f}fps, {total_frames}帧")
    print(f"输出规格: {target_width}x{target_height}@{actual_fps:.2f}fps, max_dim={max_dim}")

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(output_path), fourcc, actual_fps, (target_width, target_height))
    if not writer.isOpened():
        cap.release()
        raise RuntimeError(f"无法创建临时视频: {output_path}")

    frame_idx = 0
    written = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if frame_idx % frame_interval == 0:
            if width != target_width or height != target_height:
                frame = cv2.resize(frame, (target_width, target_height), interpolation=cv2.INTER_AREA)
            writer.write(frame)
            written += 1
        frame_idx += 1
        if frame_idx and frame_idx % 600 == 0:
            print(f"  已处理 {frame_idx}/{total_frames} 帧，写入 {written} 帧")

    cap.release()
    writer.release()
    size_mb = output_path.stat().st_size / 1024 / 1024
    print(f"预处理完成: {written} 帧, {size_mb:.2f} MB")
    return output_path


def encode_video_payload(video_path: Path) -> VideoPayload:
    mime_type = mimetypes.guess_type(str(video_path))[0] or "video/mp4"
    raw = video_path.read_bytes()
    encoded = base64.b64encode(raw).decode("utf-8")
    data_url = f"data:{mime_type};base64,{encoded}"
    print(f"视频 payload: 原始 {len(raw) / 1024 / 1024:.2f} MB, base64 {len(encoded) / 1024 / 1024:.2f} MB")
    return VideoPayload(mime_type=mime_type, data_url=data_url, byte_size=len(raw), source_path=video_path)


def call_openrouter_stream(
    api_key: str,
    opener: request.OpenerDirector,
    payload: dict[str, Any],
    timeout: int,
    quiet: bool,
) -> tuple[str, dict[str, Any], float, str | None, str | None]:
    req = request.Request(
        OPENROUTER_CHAT_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "kepu-fullvideo-followup-probe/1.0",
            "HTTP-Referer": "https://openrouter.ai/",
            "X-Title": "kepu-fullvideo-followup-probe",
        },
        method="POST",
    )

    chunks: list[str] = []
    usage: dict[str, Any] = {}
    generation_id: str | None = None
    finish_reason: str | None = None
    start_time = time.time()

    with opener.open(req, timeout=timeout) as resp:
        for raw_line in resp:
            line = raw_line.decode("utf-8", errors="replace").strip()
            if not line.startswith("data: "):
                continue
            body = line[len("data: ") :].strip()
            if body == "[DONE]":
                break
            if not body:
                continue
            chunk = json.loads(body)
            generation_id = chunk.get("id") or generation_id
            if chunk.get("usage"):
                usage = chunk["usage"]
            if chunk.get("error"):
                print(f"\n[OpenRouter chunk error] {chunk['error']}")
            choices = chunk.get("choices") or []
            if choices:
                finish_reason = choices[0].get("finish_reason") or finish_reason
                delta = choices[0].get("delta") or {}
                text = delta.get("content")
                if text:
                    chunks.append(text)
                    if not quiet:
                        print(text, end="", flush=True)
    elapsed = time.time() - start_time
    if not quiet:
        print()
    return "".join(chunks), usage, elapsed, generation_id, finish_reason


def fetch_generation_metadata(
    api_key: str,
    opener: request.OpenerDirector,
    generation_id: str | None,
    timeout: int = 60,
) -> dict[str, Any] | None:
    if not generation_id:
        return None
    headers = {"Authorization": f"Bearer {api_key}", "User-Agent": "kepu-fullvideo-followup-probe/1.0"}
    query = parse.urlencode({"id": generation_id})
    url = f"{OPENROUTER_GENERATION_URL}?{query}"
    last_error: Exception | None = None
    for attempt in range(1, 4):
        try:
            return read_json_url(opener, url, headers=headers, timeout=timeout)
        except Exception as exc:
            last_error = exc
            if attempt < 3:
                time.sleep(2)
    print(f"警告: generation metadata 获取失败: {last_error}")
    return None


def build_request_payload(args: argparse.Namespace, messages: list[dict[str, Any]]) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": args.model,
        "messages": messages,
        "stream": True,
        "stream_options": {"include_usage": True},
        "max_tokens": args.max_tokens,
        "temperature": args.temperature,
    }
    if args.reasoning_effort != "none":
        payload["reasoning"] = {"effort": args.reasoning_effort}
    return payload


def write_turn_jsonl(path: Path, row: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_markdown_report(
    path: Path,
    args: argparse.Namespace,
    video_path: Path,
    processed_path: Path,
    segments: list[tuple[int, int]],
    results: list[TurnResult],
    exchange_rate: float,
) -> None:
    total_usd = sum(item.cost_usd or 0 for item in results)
    total_cny = total_usd * exchange_rate
    lines = [
        "# OpenRouter 完整视频连续追问测试",
        "",
        f"最后更新时间：{now_bj_display()}",
        "更新次数：1",
        "",
        f"- 模型：`{args.model}`",
        f"- 追问模式：`{args.mode}`",
        f"- 原视频：`{video_path}`",
        f"- 预处理视频：`{processed_path}`",
        f"- 分段：{', '.join(f'{fmt_time(s)}-{fmt_time(e)}' for s, e in segments)}",
        f"- 累计费用：${total_usd:.6f}，约 ¥{total_cny:.4f}",
        "",
        "## 每轮结果",
        "",
    ]
    for idx, item in enumerate(results, 1):
        usd = item.cost_usd
        cny = usd * exchange_rate if usd is not None else None
        cost_text = f"${usd:.6f}，约 ¥{cny:.4f}（{item.cost_source}）" if usd is not None else "未获取到"
        prompt_tokens = (item.usage or {}).get("prompt_tokens")
        completion_tokens = (item.usage or {}).get("completion_tokens")
        reasoning_tokens = ((item.usage or {}).get("completion_tokens_details") or {}).get("reasoning_tokens")
        lines.extend(
            [
                f"### 第 {idx} 轮：{fmt_time(item.segment[0])}-{fmt_time(item.segment[1])}",
                "",
                f"- Generation ID：`{item.generation_id or '未返回'}`",
                f"- 耗时：{item.elapsed_sec:.1f}s",
                f"- 结束原因：`{item.finish_reason or '未知'}`",
                f"- 费用：{cost_text}",
                f"- Token：prompt={prompt_tokens}, completion={completion_tokens}, reasoning={reasoning_tokens}",
                "",
                item.content.strip() or "（无内容）",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def run_probe(args: argparse.Namespace) -> int:
    env = load_env(Path(args.env)) if args.env else load_env()
    api_key = os.environ.get("OPENROUTER_API_KEY") or env.get("OPENROUTER_API_KEY")
    proxy_url = args.proxy or os.environ.get("GEMINI_PROXY") or env.get("GEMINI_PROXY")

    opener = build_opener(proxy_url)
    if not args.skip_model_check:
        check_model(args.model, opener)

    if args.check_model_only:
        return 0

    if not api_key:
        print("错误: 没有找到 OPENROUTER_API_KEY。请写入 Gemini本地私密配置.env 或环境变量。")
        return 2

    video_path = Path(args.video).expanduser().resolve()
    if not video_path.exists():
        print(f"错误: 找不到视频文件: {video_path}")
        return 2

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    info = get_video_info(video_path)
    duration = info.get("duration") or 0
    print(f"源视频: {video_path}")
    print(f"源视频时长: {duration:.1f}s, 尺寸: {int(info['width'])}x{int(info['height'])}, fps={info['fps']:.2f}")

    timestamp = now_bj_for_file()
    if args.no_preprocess:
        processed_path = video_path
    else:
        processed_path = output_dir / f"{timestamp}_preprocessed_fullvideo_{args.max_dim}px_{args.fps}fps.mp4"
        preprocess_full_video(video_path, processed_path, args.max_dim, args.fps)

    video = encode_video_payload(processed_path)

    if args.segments:
        segments = parse_segments(args.segments)
    else:
        segments = build_segments(args.segment_seconds, args.max_segments, duration)

    extra_prompt = Path(args.prompt_file).read_text(encoding="utf-8") if args.prompt_file else None
    jsonl_path = output_dir / f"{timestamp}_openrouter_fullvideo_followup_cost_log.jsonl"
    report_path = output_dir / f"{timestamp}_OpenRouter完整视频连续追问测试.md"

    history: list[TurnResult] = []
    print(f"开始测试: mode={args.mode}, model={args.model}, segments={segments}")
    print(f"成本日志: {jsonl_path}")

    for index, segment in enumerate(segments, 1):
        prompt_text = make_segment_prompt(segment, extra_prompt)
        messages = build_messages(args.mode, video, segment, prompt_text, history)
        payload = build_request_payload(args, messages)

        print("\n" + "=" * 72)
        print(f"第 {index}/{len(segments)} 轮: {fmt_time(segment[0])}-{fmt_time(segment[1])}")
        print(f"请求模式: {args.mode}; timeout={args.timeout}s; max_tokens={args.max_tokens}")

        try:
            content, usage, elapsed, generation_id, finish_reason = call_openrouter_stream(
                api_key=api_key,
                opener=opener,
                payload=payload,
                timeout=args.timeout,
                quiet=args.quiet,
            )
            metadata = fetch_generation_metadata(api_key, opener, generation_id)
            cost = extract_cost_usd(metadata, usage)
            cny = cost.usd * args.usd_cny if cost.usd is not None else None
            if cost.usd is not None:
                print(f"本轮费用: ${cost.usd:.6f}，约 ¥{cny:.4f}（来源: {cost.source}）")
            else:
                print("本轮费用: 未获取到，已记录 generation_id 供后续查询")
            print(f"本轮耗时: {elapsed:.1f}s; generation_id={generation_id}; finish_reason={finish_reason}")

            result = TurnResult(
                segment=segment,
                content=content,
                generation_id=generation_id,
                prompt_text=prompt_text,
                elapsed_sec=elapsed,
                finish_reason=finish_reason,
                cost_usd=cost.usd,
                cost_source=cost.source,
                usage=usage,
                generation_metadata=metadata,
            )
            history.append(result)

            total_usd = sum(item.cost_usd or 0 for item in history)
            print(f"累计费用: ${total_usd:.6f}，约 ¥{total_usd * args.usd_cny:.4f}")

            write_turn_jsonl(
                jsonl_path,
                {
                    "time_bj": now_bj_display(),
                    "round": index,
                    "model": args.model,
                    "mode": args.mode,
                    "segment": {"start": segment[0], "end": segment[1]},
                    "generation_id": generation_id,
                    "elapsed_sec": elapsed,
                    "finish_reason": finish_reason,
                    "cost_usd": cost.usd,
                    "cost_cny": cny,
                    "cost_source": cost.source,
                    "usage": usage,
                    "generation_metadata": metadata,
                    "content_chars": len(content),
                },
            )
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            print(f"HTTP {exc.code}: {body[:2000]}")
            return 1
        except Exception as exc:
            print(f"异常: {exc}")
            return 1

        if index < len(segments) and args.sleep > 0:
            time.sleep(args.sleep)

    write_markdown_report(report_path, args, video_path, processed_path, segments, history, args.usd_cny)
    print("\n" + "=" * 72)
    print(f"测试完成: {report_path}")
    print(f"成本日志: {jsonl_path}")

    if not args.keep_preprocessed and processed_path != video_path and processed_path.exists():
        processed_path.unlink()
        print("已清理预处理临时视频")

    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="OpenRouter 完整视频连续追问与成本探针")
    parser.add_argument("--video", help="完整视频路径")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="输出目录")
    parser.add_argument("--env", default=str(ENV_PATH), help="私密 env 文件路径")
    parser.add_argument("--proxy", help="代理地址；默认读取 GEMINI_PROXY")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="OpenRouter 模型 ID")
    parser.add_argument(
        "--mode",
        choices=["repeat-video", "carry-first-video", "text-followup"],
        default="repeat-video",
        help="repeat-video 最稳；carry-first-video 模拟完整消息历史；text-followup 验证不重传视频是否可行",
    )
    parser.add_argument("--segments", help="手动分段，例如 0-20,20-40,40-60")
    parser.add_argument("--segment-seconds", type=int, default=20, help="自动分段长度")
    parser.add_argument("--max-segments", type=int, default=3, help="自动分段数量")
    parser.add_argument("--prompt-file", help="追加到每轮问题后的补充提示词文件")
    parser.add_argument("--max-dim", type=int, default=640, help="预处理后视频最大边")
    parser.add_argument("--fps", type=int, default=5, help="预处理目标帧率")
    parser.add_argument("--no-preprocess", action="store_true", help="直接上传原视频")
    parser.add_argument("--keep-preprocessed", action="store_true", help="保留预处理视频")
    parser.add_argument("--timeout", type=int, default=600, help="单轮请求超时秒数")
    parser.add_argument("--max-tokens", type=int, default=1600, help="每轮最大输出 token，防止一次输出过长")
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--reasoning-effort", choices=["none", "low", "medium", "high"], default="high")
    parser.add_argument("--sleep", type=float, default=2.0, help="每轮之间等待秒数")
    parser.add_argument("--usd-cny", type=float, default=7.25, help="美元转人民币估算汇率")
    parser.add_argument("--skip-model-check", action="store_true", help="跳过 OpenRouter 模型列表检查")
    parser.add_argument("--check-model-only", action="store_true", help="只检查模型，不发起视频请求")
    parser.add_argument("--quiet", action="store_true", help="不实时打印模型输出")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    if not args.check_model_only and not args.video:
        parser.error("除 --check-model-only 外，必须提供 --video")
    return run_probe(args)


if __name__ == "__main__":
    raise SystemExit(main())
