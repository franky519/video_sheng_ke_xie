#!/usr/bin/env python3
import os
import cv2
import asyncio
from pathlib import Path
from google.antigravity import Agent, LocalAgentConfig
from google.antigravity import types
from google.antigravity.types import (
    GeminiConfig, ModelConfig, ModelEntry, GenerationConfig, ThinkingLevel
)

# 加载本地私密配置中的 API KEY 和代理设置
ENV_PATH = Path(__file__).resolve().parent.parent / "Gemini本地私密配置.env"
if ENV_PATH.exists():
    with open(ENV_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")

# 设置代理环境（优先使用配置中的代理）
proxy_val = os.environ.get("GEMINI_PROXY") or "http://127.0.0.1:10808"
os.environ["HTTP_PROXY"] = proxy_val
os.environ["HTTPS_PROXY"] = proxy_val
os.environ["ALL_PROXY"] = proxy_val
os.environ["GOOGLE_CLOUD_DISABLE_DIRECT_PATH"] = "true"

SCRIPT_DIR = Path(__file__).resolve().parent
# 差评君视频路径
SRC_VIDEO = SCRIPT_DIR.parent / "02_别人视频的拆解分析" / "差评君" / "E_豆包是真人炼的_抖音" / "raw_video" / "03_7628935872846531892_2026年了，为什么会有人觉得豆包是真人炼的？ #豆包#AI#心理学#硬核玩家计划.mp4"
TEMP_CLIP = SCRIPT_DIR / "temp_test_30s.mp4"

def crop_video_30s():
    print(f"正在读取源视频: {SRC_VIDEO}")
    if not SRC_VIDEO.exists():
        raise FileNotFoundError(f"找不到源视频: {SRC_VIDEO}")

    cap = cv2.VideoCapture(str(SRC_VIDEO))
    if not cap.isOpened():
        raise RuntimeError("无法打开源视频")

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # 缩放到 640px 最大边，减少体积加快上传
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

    print(f"原视频属性: FPS={fps:.2f}, 尺寸={width}x{height} -> 缩放尺寸: {w_new}x{h_new}")

    total_frames = int(fps * 30) # 30秒
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(TEMP_CLIP), fourcc, fps, (w_new, h_new))

    frame_count = 0
    while frame_count < total_frames:
        ret, frame = cap.read()
        if not ret:
            break
        if width != w_new or height != h_new:
            frame = cv2.resize(frame, (w_new, h_new), interpolation=cv2.INTER_AREA)
        out.write(frame)
        frame_count += 1

    cap.release()
    out.release()
    print(f"裁剪视频完成: {TEMP_CLIP} (共 {frame_count} 帧, 约 {TEMP_CLIP.stat().st_size / 1024 / 1024:.2f} MB)")

async def run_agent_test():
    print("正在初始化 Antigravity Agent...")
    # 这里会自动从系统 keychain/keyring 读取本地登录凭证
    config = LocalAgentConfig(
        system_instructions="你是一个视频分析助手，请详细梳理视频前30秒发生的画面变化和主要旁白文字。",
        gemini_config=GeminiConfig(
            models=ModelConfig(
                default=ModelEntry(
                    name="gemini-3.5-flash",
                    generation=GenerationConfig(thinking_level=ThinkingLevel.HIGH)
                )
            )
        )
    )

    async with Agent(config) as agent:
        print(f"正在加载视频文件...")
        video_spec = types.Video.from_file(str(TEMP_CLIP))

        print("向 Agent 发起多模态分析请求 (Gemini 3.5 Flash, thinking_level=high)...")
        response = await agent.chat([
            "请详细总结这个视频前30秒，包含了哪些分镜画面、文案旁白以及视觉元素？",
            video_spec
        ])
        content = await response.text()
        print("\n=== Agent 视频分析结果 ===")
        print(content)
        print("=========================\n")

        output_file = SCRIPT_DIR.parent / "02_别人视频的拆解分析" / "2026-06-15_10-25_AntigravitySDK_视频分析结果_豆包_30s.md"
        output_file.write_text(
            f"# Antigravity SDK 视频多模态分析结果\n\n"
            f"测试时间：2026-06-15 10:25 北京时间\n\n"
            f"{content}\n",
            encoding="utf-8"
        )
        print(f"分析结果已成功写入本地文件: {output_file}")

def main():
    try:
        crop_video_30s()
        asyncio.run(run_agent_test())
    finally:
        # 清理临时裁剪文件
        if TEMP_CLIP.exists():
            try:
                TEMP_CLIP.unlink()
                print("已自动清理本地临时裁剪视频")
            except Exception as e:
                print(f"清理临时文件失败: {e}")

if __name__ == "__main__":
    main()
