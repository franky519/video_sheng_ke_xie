#!/usr/bin/env python3
"""
整条视频 Plan 模式多轮拆解测试

测试目标：
1. 输入一个完整视频（4.5min），预处理后调用 Gemini 3.5 Flash（high）
2. 使用 /plan 斜杠命令让 agent 自动拆解任务、分步执行
3. 在同一会话中支持追问，多轮协作完成完整分析
"""

import os
import cv2
import asyncio
from pathlib import Path
from google.antigravity import Agent, LocalAgentConfig, types
from google.antigravity.types import (
    GeminiConfig, ModelConfig, ModelEntry, GenerationConfig, ThinkingLevel
)

ENV_PATH = Path(__file__).resolve().parent.parent / "Gemini本地私密配置.env"
if ENV_PATH.exists():
    with open(ENV_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")

proxy_val = os.environ.get("GEMINI_PROXY") or "http://127.0.0.1:10808"
os.environ["HTTP_PROXY"] = proxy_val
os.environ["HTTPS_PROXY"] = proxy_val
os.environ["ALL_PROXY"] = proxy_val
os.environ["GOOGLE_CLOUD_DISABLE_DIRECT_PATH"] = "true"

SCRIPT_DIR = Path(__file__).resolve().parent
SRC_VIDEO = SCRIPT_DIR.parent / "02_别人视频的拆解分析" / "差评君" / "E_豆包是真人炼的_抖音" / "raw_video" / "03_7628935872846531892_2026年了，为什么会有人觉得豆包是真人炼的？ #豆包#AI#心理学#硬核玩家计划.mp4"
TEMP_CLIP = SCRIPT_DIR / "temp_test_full.mp4"

MODEL_NAME = "gemini-3.5-flash"
THINKING_LEVEL = ThinkingLevel.HIGH

OUTPUT_DIR = SCRIPT_DIR.parent / "02_别人视频的拆解分析"


def crop_video():
    print(f"读取源视频: {SRC_VIDEO}")
    if not SRC_VIDEO.exists():
        raise FileNotFoundError(f"找不到: {SRC_VIDEO}")

    cap = cv2.VideoCapture(str(SRC_VIDEO))
    if not cap.isOpened():
        raise RuntimeError("无法打开")

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    max_dim = 640
    if width > max_dim or height > max_dim:
        if width > height:
            w_new = max_dim
            h_new = int(height * (max_dim / width))
        else:
            h_new = max_dim
            w_new = int(width * (max_dim / height))
    else:
        w_new, h_new = width, height

    # 降帧到 10fps 减少体积
    target_fps = 10
    frame_skip = max(1, int(fps / target_fps))
    output_fps = fps / frame_skip

    print(f"原始: {width}x{height}, {fps}fps, {total_frames}帧, {total_frames/fps:.1f}s")
    print(f"输出: {w_new}x{h_new}, ~{output_fps:.1f}fps, 最大边{max_dim}px")

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(TEMP_CLIP), fourcc, output_fps, (w_new, h_new))

    frame_count = 0
    output_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_count % frame_skip == 0:
            if width != w_new or height != h_new:
                frame = cv2.resize(frame, (w_new, h_new), interpolation=cv2.INTER_AREA)
            out.write(frame)
            output_count += 1
        frame_count += 1

    cap.release()
    out.release()
    mb = TEMP_CLIP.stat().st_size / 1024 / 1024
    print(f"预处理完成: {output_count}帧, ~{output_count/output_fps:.1f}s, {mb:.1f}MB\n")


async def run_plan_test():
    print(f"初始化 Agent: {MODEL_NAME}, thinking_level={THINKING_LEVEL.value}")
    config = LocalAgentConfig(
        system_instructions="你是专业视频内容分析师。先用 plan 模式拆解任务，再分步执行，最终给出完整的视频分析报告。",
        gemini_config=GeminiConfig(
            models=ModelConfig(
                default=ModelEntry(
                    name=MODEL_NAME,
                    generation=GenerationConfig(thinking_level=THINKING_LEVEL)
                )
            )
        )
    )

    async with Agent(config) as agent:
        video = types.Video.from_file(str(TEMP_CLIP))

        # 第1轮：/plan 命令让 agent 自动规划分析策略
        print("=" * 70)
        print("第1轮: 发起 /plan 命令，让 agent 制定视频分析计划")
        print("=" * 70)
        plan_prompt = [
            types.SlashCommand(name=types.BuiltinSlashCommandName.PLAN),
            "这是一条知识科普类抖音短视频（约4.5分钟），请制定完整的视频拆解分析计划并执行，"
            "最终输出一份详细的分析报告。报告需包含：\n"
            "1. 视频整体结构与叙事框架\n"
            "2. 逐分镜的详细拆解（画面内容、旁白文字、视觉元素）\n"
            "3. 视频使用的修辞手法和叙事技巧\n"
            "4. 风格与美术设计分析\n"
            "5. 可以借鉴的创作要点和技巧总结",
            video
        ]
        response = await agent.chat(plan_prompt)
        plan_result = await response.text()
        print(plan_result)
        print()

        # 第2轮：让 agent 确认计划是否完整执行，如有遗漏补充
        print("=" * 70)
        print("第2轮: 确认分析完整度，补充遗漏")
        print("=" * 70)
        response2 = await agent.chat(
            "请检查上述分析是否覆盖了视频的全部内容。如有遗漏的分镜或关键片段，请补充完整。"
        )
        supplement = await response2.text()
        print(supplement)
        print()

        # 第3轮：生成最终格式化报告并保存
        print("=" * 70)
        print("第3轮: 生成最终格式化报告")
        print("=" * 70)
        response3 = await agent.chat(
            "请将上述全部分析内容整合成一份 Markdown 格式的完整报告。"
            "报告应包含清晰的章节划分（用 # 和 ## 标题），"
            "确保每个分镜都有时间戳标注。"
        )
        final_report = await response3.text()
        print(final_report)
        print()

        # 保存
        output_file = OUTPUT_DIR / "2026-06-15_11-30_plan模式_完整视频拆解报告_豆包_3.5Flash.md"
        output_file.write_text(
            f"# 整条视频 Plan 模式自动拆解分析报告\n\n"
            f"测试时间：2026-06-15 北京时间\n\n"
            f"模型：{MODEL_NAME}\n"
            f"推理等级：{THINKING_LEVEL.value}\n"
            f"视频：豆包灵异事件（约4.5分钟）\n\n"
            f"---\n\n"
            f"{final_report}\n",
            encoding="utf-8"
        )
        print(f"报告已保存: {output_file}")


def main():
    try:
        crop_video()
        asyncio.run(run_plan_test())
    finally:
        if TEMP_CLIP.exists():
            try:
                TEMP_CLIP.unlink()
                print("临时文件已清理")
            except Exception as e:
                print(f"清理失败: {e}")


if __name__ == "__main__":
    main()
