#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import math
from pathlib import Path
from functools import lru_cache

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


OUT_DIR = Path(__file__).resolve().parent / "2026-06-03_09-46_豆包科普视频_0_30s程序化样片输出"
VIDEO_PATH = OUT_DIR / "2026-06-03_09-46_豆包科普视频_0_30s程序化样片.mp4"
FRAME_DIR = OUT_DIR / "关键帧预览"

W, H = 1280, 720
FPS = 24
DURATION = 30
TOTAL_FRAMES = FPS * DURATION

FONT_PATH = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
FONT_CACHE: dict[int, ImageFont.FreeTypeFont] = {}


def font(size: int) -> ImageFont.FreeTypeFont:
    if size not in FONT_CACHE:
        FONT_CACHE[size] = ImageFont.truetype(FONT_PATH, size)
    return FONT_CACHE[size]


def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def progress(t: float, start: float, end: float) -> float:
    if end <= start:
        return 1.0 if t >= end else 0.0
    return clamp((t - start) / (end - start))


def lerp(a: float, b: float, p: float) -> float:
    return a + (b - a) * p


def smoothstep(p: float) -> float:
    p = clamp(p)
    return p * p * (3 - 2 * p)


def spring01(p: float, damping: float = 12.0, mass: float = 0.6) -> float:
    p = clamp(p)
    if p <= 0:
        return 0.0
    if p >= 1:
        return 1.0
    decay = math.exp(-damping * p / (mass * 5.0))
    wobble = math.cos((2.2 + 0.8 / mass) * math.pi * p)
    return 1.0 - decay * wobble


def rgba(color: tuple[int, int, int], alpha: float = 1.0) -> tuple[int, int, int, int]:
    return (color[0], color[1], color[2], int(255 * clamp(alpha)))


def text_size(text: str, fnt: ImageFont.FreeTypeFont) -> tuple[int, int]:
    box = fnt.getbbox(text)
    return box[2] - box[0], box[3] - box[1]


def wrap_text(text: str, fnt: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for ch in text:
        test = current + ch
        if text_size(test, fnt)[0] <= max_width or not current:
            current = test
        else:
            lines.append(current)
            current = ch
    if current:
        lines.append(current)
    return lines


def draw_text_block(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    fnt: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int, int],
    max_width: int,
    line_gap: int = 10,
) -> int:
    x, y = xy
    for line in wrap_text(text, fnt, max_width):
        draw.text((x, y), line, font=fnt, fill=fill)
        y += text_size(line, fnt)[1] + line_gap
    return y


def rounded_rect_layer(
    size: tuple[int, int],
    radius: int,
    fill: tuple[int, int, int, int],
    outline: tuple[int, int, int, int] | None = None,
    width: int = 2,
    shadow: tuple[int, int, int, int] | None = None,
    shadow_offset: tuple[int, int] = (0, 12),
    shadow_blur: int = 22,
) -> Image.Image:
    w, h = size
    layer = Image.new("RGBA", (w + 80, h + 80), (0, 0, 0, 0))
    if shadow:
        shadow_layer = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow_layer)
        sx = 40 + shadow_offset[0]
        sy = 40 + shadow_offset[1]
        sd.rounded_rectangle((sx, sy, sx + w, sy + h), radius=radius, fill=shadow)
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(shadow_blur))
        layer.alpha_composite(shadow_layer)
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle((40, 40, 40 + w, 40 + h), radius=radius, fill=fill, outline=outline, width=width)
    return layer


def paste_center(base: Image.Image, layer: Image.Image, center: tuple[float, float], alpha: float = 1.0) -> None:
    if alpha <= 0:
        return
    if alpha < 1:
        layer = layer.copy()
        a = layer.getchannel("A")
        layer.putalpha(a.point(lambda px: int(px * alpha)))
    x = int(center[0] - layer.width / 2)
    y = int(center[1] - layer.height / 2)
    base.alpha_composite(layer, (x, y))


def scaled(layer: Image.Image, scale: float) -> Image.Image:
    scale = max(0.001, scale)
    return layer.resize((max(1, int(layer.width * scale)), max(1, int(layer.height * scale))), Image.Resampling.LANCZOS)


@lru_cache(maxsize=4)
def make_phone(kind: str) -> Image.Image:
    phone = Image.new("RGBA", (340, 590), (0, 0, 0, 0))
    d = ImageDraw.Draw(phone)
    d.rounded_rectangle((16, 12, 324, 578), radius=42, fill=(12, 13, 16, 255), outline=(74, 78, 86, 255), width=4)
    d.rounded_rectangle((40, 42, 300, 548), radius=30, fill=(246, 248, 250, 255))
    d.rounded_rectangle((136, 26, 204, 38), radius=7, fill=(38, 40, 45, 255))
    d.ellipse((62, 64, 90, 92), fill=(44, 159, 94, 255))
    d.text((104, 64), "豆包", font=font(22), fill=(32, 35, 40, 255))
    if kind == "plain":
        title = "普通回答"
        color = (126, 132, 142, 255)
        lines = [
            "本产品保障多种重大疾病，等待期为90天。",
            "赔付比例依据合同条款执行。",
            "建议您仔细阅读保险责任与免责条款。",
            "如有疑问请咨询官方客服。",
        ]
    else:
        title = "专家回答"
        color = (22, 136, 78, 255)
        lines = [
            "先看 3 个坑：",
            "1. 免责条款是否把既往症排除。",
            "2. 赔付条件看似相同，触发标准不同。",
            "3. 附录小字可能限制报销范围。",
        ]
    d.rounded_rectangle((62, 112, 278, 154), radius=16, fill=(235, 239, 244, 255))
    d.text((84, 121), title, font=font(22), fill=color)
    y = 182
    for idx, line in enumerate(lines):
        bg = (236, 239, 244, 255) if kind == "plain" else (230, 248, 238, 255) if idx in (1, 3) else (248, 241, 226, 255) if idx == 2 else (236, 239, 244, 255)
        d.rounded_rectangle((62, y, 278, y + 72), radius=14, fill=bg)
        draw_text_block(d, (78, y + 13), line, font(15), (45, 49, 55, 255), 186, 5)
        y += 88
    return phone


def subtitle(base: Image.Image, text: str) -> None:
    d = ImageDraw.Draw(base)
    fnt = font(25)
    lines = wrap_text(text, fnt, 1050)
    box_h = 34 * len(lines) + 22
    y0 = H - box_h - 28
    d.rounded_rectangle((125, y0, W - 125, H - 24), radius=18, fill=(10, 11, 13, 182))
    y = y0 + 13
    for line in lines:
        tw, _ = text_size(line, fnt)
        d.text(((W - tw) / 2, y), line, font=fnt, fill=(246, 248, 250, 255))
        y += 34


@lru_cache(maxsize=2)
def make_question_card() -> Image.Image:
    layer = rounded_rect_layer((920, 118), 22, (250, 251, 252, 255), shadow=(0, 0, 0, 120))
    d = ImageDraw.Draw(layer)
    d.text((76, 68), "帮我看看这份保险条款有哪些坑？", font=font(34), fill=(30, 33, 38, 255))
    d.text((76, 114), "用户输入", font=font(18), fill=(110, 118, 128, 255))
    return layer


def make_plain_answer(scroll_px: float = 0.0) -> Image.Image:
    card = rounded_rect_layer((940, 420), 18, (235, 237, 240, 255), shadow=(0, 0, 0, 120))
    d = ImageDraw.Draw(card)
    x0, y0 = 76, 65 - int(scroll_px)
    d.text((x0, y0), "普通回答", font=font(28), fill=(88, 94, 105, 255))
    y = y0 + 58
    blocks = [
        "本产品保障多种重大疾病，等待期为90天，赔付比例依据合同条款约定执行。",
        "保险期间内，如被保险人首次确诊合同约定疾病，保险公司将按照基本保险金额给付保险金。",
        "投保前请仔细阅读保险责任、责任免除、犹豫期、现金价值及相关服务说明。",
        "以上内容仅供参考，具体以保险合同和保险公司解释为准。",
    ]
    for block in blocks:
        d.rounded_rectangle((x0, y, x0 + 780, y + 68), radius=12, fill=(247, 248, 250, 255))
        draw_text_block(d, (x0 + 24, y + 15), block, font(20), (70, 75, 82, 255), 720, 6)
        y += 88
    return card


def make_expert_card(green_p: float, orange_p: float) -> Image.Image:
    card = rounded_rect_layer((1000, 500), 22, (37, 40, 46, 255), outline=(84, 91, 103, 255), width=2, shadow=(0, 0, 0, 150))
    d = ImageDraw.Draw(card)
    d.text((82, 68), "专家回答：这份保险先看三个风险点", font=font(33), fill=(250, 252, 255, 255))
    d.text((82, 118), "不是复述条款，而是直接指出容易漏看的地方。", font=font(22), fill=(180, 187, 198, 255))

    rows = [
        ("免责条款", "是否把既往症、职业风险、等待期内确诊排除在外。"),
        ("赔付条件", "看着都是“确诊即赔”，实际可能要求病理、手术或严重程度。"),
        ("附录小字", "部分保障范围、医院限制、报销比例会藏在附录几行字里。"),
    ]
    y = 180
    for idx, (head, body) in enumerate(rows):
        d.rounded_rectangle((82, y, 920, y + 82), radius=15, fill=(51, 55, 64, 255))
        if idx == 0 and green_p > 0:
            d.rounded_rectangle((202, y + 42, 202 + int(690 * green_p), y + 67), radius=8, fill=(56, 222, 132, 100))
        if idx == 1 and orange_p > 0:
            d.rounded_rectangle((202, y + 42, 202 + int(705 * orange_p), y + 67), radius=8, fill=(255, 166, 70, 110))
        d.text((108, y + 24), head, font=font(24), fill=(255, 255, 255, 255))
        draw_text_block(d, (202, y + 24), body, font(21), (228, 232, 239, 255), 700, 6)
        y += 98
    return card


def make_magnifier(jitter: tuple[float, float]) -> Image.Image:
    layer = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx = 150 + jitter[0]
    cy = 150 + jitter[1]
    d.ellipse((cx - 118, cy - 118, cx + 118, cy + 118), fill=(248, 252, 255, 244), outline=(255, 255, 255, 255), width=8)
    d.ellipse((cx - 104, cy - 104, cx + 104, cy + 104), outline=(80, 190, 255, 160), width=3)
    d.text((58 + jitter[0], 74 + jitter[1]), "附录小字", font=font(28), fill=(28, 32, 38, 255))
    fine = "免赔责任：既往症、等待期内症状、非指定医院记录可能影响赔付。"
    draw_text_block(d, (58 + int(jitter[0]), 122 + int(jitter[1])), fine, font(20), (38, 43, 52, 255), 190, 8)
    return layer


@lru_cache(maxsize=4)
def make_prompt_card(kind: str) -> Image.Image:
    card = Image.new("RGBA", (500, 700), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle((10, 10, 490, 690), radius=18, fill=(250, 251, 252, 255), outline=(220, 224, 230, 255), width=2)
    if kind == "a":
        title = "提问指南"
        body = [
            "角色：保险顾问",
            "任务：找出隐藏风险",
            "输出：按严重程度排序",
            "限制：不要只复述条款",
        ]
        accent = (38, 114, 236, 255)
    else:
        title = "超级 Prompt"
        body = [
            "请先识别免责条款",
            "再比较赔付触发条件",
            "最后检查附录与小字",
            "把不确定处单独标出",
        ]
        accent = (236, 93, 63, 255)
    d.text((42, 46), title, font=font(36), fill=(30, 34, 40, 255))
    d.rounded_rectangle((42, 104, 430, 114), radius=5, fill=accent)
    y = 158
    for line in body:
        d.rounded_rectangle((42, y, 430, y + 82), radius=14, fill=(238, 241, 245, 255))
        draw_text_block(d, (64, y + 22), line, font(25), (48, 54, 63, 255), 340, 7)
        y += 112
    d.text((42, 620), "看起来像提示词问题", font=font(23), fill=(112, 120, 132, 255))
    return card


def paste_rotated_card(base: Image.Image, card: Image.Image, center: tuple[float, float], angle: float, alpha: float) -> None:
    shadow = Image.new("RGBA", (card.width + 80, card.height + 80), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((55, 60, 55 + card.width, 60 + card.height), radius=22, fill=(0, 0, 0, 100))
    shadow = shadow.filter(ImageFilter.GaussianBlur(20))
    shadow.alpha_composite(card, (40, 40))
    rotated = shadow.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)
    paste_center(base, rotated, center, alpha)


def draw_question_mark(base: Image.Image, scale_val: float, glow: float) -> None:
    if scale_val <= 0:
        return
    size = int(220 * scale_val)
    mark = Image.new("RGBA", (360, 360), (0, 0, 0, 0))
    d = ImageDraw.Draw(mark)
    for radius, alpha in [(42, 80), (24, 120), (10, 160)]:
        glow_layer = Image.new("RGBA", mark.size, (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow_layer)
        gd.text((98, 35), "?", font=font(size), fill=(255, 50, 42, int(alpha * glow)))
        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius))
        mark.alpha_composite(glow_layer)
    for offset, fill in [((10, 12), (110, 12, 18, 255)), ((5, 6), (190, 24, 28, 255)), ((0, 0), (255, 64, 52, 255))]:
        d.text((98 + offset[0], 35 + offset[1]), "?", font=font(size), fill=fill)
    paste_center(base, mark, (W / 2, H / 2 + 8), 1)


def scene_intro(base: Image.Image, t: float) -> None:
    d = ImageDraw.Draw(base)
    d.text((70, 48), "同一个问题，两个答案为什么差这么多？", font=font(34), fill=(245, 247, 250, 255))
    d.text((72, 92), "0~30 秒程序化动效打样 / 占位 UI", font=font(20), fill=(142, 151, 164, 255))

    left_p = spring01(progress(t, 0.0, 1.0), 15, 0.6)
    right_p = spring01(progress(t, 1.0, 2.0), 15, 0.6)
    left_opacity = 1.0 - 0.6 * progress(t, 2.5, 5.0)
    right_zoom = 1.0 + 0.05 * progress(t, 3.0, 5.0)
    paste_center(base, scaled(make_phone("plain"), left_p), (420, 390), left_opacity)
    paste_center(base, scaled(make_phone("expert"), right_p * right_zoom), (850, 380), 1)
    d.text((305, 626), "像复制粘贴", font=font(24), fill=(148, 155, 166, int(255 * left_opacity)))
    d.text((770, 626), "像专家", font=font(24), fill=(76, 232, 144, 255))
    subtitle(base, "同样问豆包，为什么他的答案像专家，你的答案像复制粘贴？")


def scene_plain_answer(base: Image.Image, t: float) -> None:
    local = t - 5.0
    d = ImageDraw.Draw(base)
    d.text((70, 48), "普通模式：答案有内容，但没有判断", font=font(34), fill=(245, 247, 250, 255))
    q_opacity = 1.0 - progress(t, 12.0, 13.5)
    q_y = lerp(455, 175, smoothstep(progress(t, 5.0, 5.8)))
    paste_center(base, make_question_card(), (W / 2, q_y), q_opacity)

    answer_opacity = progress(t, 7.0, 7.5) * (1.0 - progress(t, 13.5, 15.0))
    scroll_px = 80 * progress(t, 8.5, 13.5)
    blur = int(20 * progress(t, 13.5, 15.0))
    answer = make_plain_answer(scroll_px)
    if blur > 0:
        answer = answer.filter(ImageFilter.GaussianBlur(blur))
    paste_center(base, answer, (W / 2, 448), answer_opacity)

    d.rounded_rectangle((86, 582, 438, 626), radius=22, fill=(255, 255, 255, 30))
    d.text((106, 590), "画面目标：让观众觉得“听完像没听”", font=font(20), fill=(180, 187, 198, 255))
    subtitle(base, "你的豆包说，本产品保障多少种重大疾病，等待期多少天，赔付比例是多少。听完像没听。")


def scene_expert_answer(base: Image.Image, t: float) -> None:
    d = ImageDraw.Draw(base)
    d.text((70, 48), "专家模式：直接指出坑点", font=font(34), fill=(245, 247, 250, 255))
    scale_val = lerp(0.9, 1.0, spring01(progress(t, 15.0, 15.8), 12, 0.6))
    green_p = smoothstep(progress(t, 16.5, 17.5))
    orange_p = smoothstep(progress(t, 19.0, 20.0))
    expert = make_expert_card(green_p, orange_p)
    paste_center(base, scaled(expert, scale_val), (W / 2, 365), 1)

    mag_p = spring01(progress(t, 21.5, 22.5), 12, 0.6)
    if mag_p > 0:
        jitter = (math.sin(t * 20) * 2 * progress(t, 22.5, 25.0), math.cos(t * 18) * 2 * progress(t, 22.5, 25.0))
        paste_center(base, scaled(make_magnifier(jitter), mag_p), (820, 455), 1)
        d.line((920, 535, 1030, 642), fill=(255, 255, 255, int(180 * mag_p)), width=12)
        d.line((920, 535, 1030, 642), fill=(76, 160, 220, int(140 * mag_p)), width=6)
    subtitle(base, "但你朋友的豆包会直接告诉你，哪条免责条款容易漏看，哪个赔付条件看着差不多其实完全不同。")


def scene_prompt_question(base: Image.Image, t: float) -> None:
    d = ImageDraw.Draw(base)
    d.text((70, 48), "观众的第一反应：是不是提示词问题？", font=font(34), fill=(245, 247, 250, 255))
    left_p = smoothstep(progress(t, 25.0, 25.8))
    right_p = smoothstep(progress(t, 25.2, 26.0))
    left_x = lerp(-230, 450, left_p)
    right_x = lerp(W + 230, 830, right_p)
    paste_rotated_card(base, scaled(make_prompt_card("a"), 0.78), (left_x, 405), -8 * left_p, left_p)
    paste_rotated_card(base, scaled(make_prompt_card("b"), 0.78), (right_x, 405), 8 * right_p, right_p)

    q_p = progress(t, 27.0, 27.5)
    if q_p > 0:
        s = lerp(0.0, 1.2, spring01(q_p, 10, 0.5))
        if t >= 27.5:
            s = 1.0 + math.sin((t - 27.5) * math.pi * 2) * 0.015
        draw_question_mark(base, s, progress(t, 27.0, 27.5))
    d.text((370, 590), "这只是入口问题，真正要继续追到“模式/模型/成本”", font=font(24), fill=(235, 238, 243, 220))
    subtitle(base, "这时候很多人第一反应是：是不是我不会提问？是不是他的提示词写得更好？")


def render_frame(frame: int) -> Image.Image:
    t = frame / FPS
    base = Image.new("RGBA", (W, H), (30, 32, 35, 255))
    d = ImageDraw.Draw(base)
    for i in range(0, W, 64):
        alpha = 24 if i % 128 == 0 else 14
        d.line((i, 0, i, H), fill=(255, 255, 255, alpha), width=1)
    for j in range(0, H, 64):
        alpha = 20 if j % 128 == 0 else 12
        d.line((0, j, W, j), fill=(255, 255, 255, alpha), width=1)

    if t < 5.0:
        scene_intro(base, t)
    elif t < 15.0:
        scene_plain_answer(base, t)
    elif t < 25.0:
        scene_expert_answer(base, t)
    else:
        scene_prompt_question(base, t)

    d = ImageDraw.Draw(base)
    bar_w = int(W * (frame + 1) / TOTAL_FRAMES)
    d.rectangle((0, H - 7, bar_w, H), fill=(76, 232, 144, 230))
    d.text((W - 106, 22), f"{t:04.1f}s", font=font(20), fill=(170, 178, 190, 255))
    return base


def write_video() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FRAME_DIR.mkdir(parents=True, exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(VIDEO_PATH), fourcc, FPS, (W, H))
    if not writer.isOpened():
        raise RuntimeError("OpenCV VideoWriter 无法打开 MP4 输出，请检查本机编码器。")

    key_seconds = {0, 2, 6, 9, 16, 18, 22, 26, 28, 30}
    for frame in range(TOTAL_FRAMES):
        img = render_frame(frame)
        if int(frame / FPS) in key_seconds and frame % FPS == 0:
            img.convert("RGB").save(FRAME_DIR / f"frame_{int(frame / FPS):02d}s.jpg", quality=92)
        arr = cv2.cvtColor(np.array(img.convert("RGB")), cv2.COLOR_RGB2BGR)
        writer.write(arr)
        if frame % (FPS * 5) == 0:
            print(f"rendered {frame}/{TOTAL_FRAMES}")
    writer.release()
    print(f"video={VIDEO_PATH}")
    print(f"frames={FRAME_DIR}")


if __name__ == "__main__":
    write_video()
