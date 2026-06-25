import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate, spring } from "remotion";

const MODEL_NAME = "doubao-seed-2.0-pro";
const INITIAL_RANK = 8;
const FINAL_RANK = 35;
const FPS = 30;

const GOLD = "#F5A623";
const RED = "#E84040";
const DARK_BG = "#080C14";
const TEXT_PRIMARY = "#FFFFFF";
const TEXT_SECONDARY = "#8899AA";
const CARD_BG = "#111827";

const interp = (frame: number, inputRange: number[], outputRange: number[]) =>
  interpolate(frame, inputRange, outputRange, {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

export const RankingAnimation: React.FC = () => {
  const frame = useCurrentFrame();

  const titleFadeEnd = 20;
  const subtitleFadeEnd = 35;
  const rankDropStart = 50;
  const rankDropEnd = 190;
  const settleEnd = 220;

  const titleOpacity = interp(frame, [0, titleFadeEnd], [0, 1]);
  const subtitleOpacity = interp(frame, [titleFadeEnd, subtitleFadeEnd], [0, 1]);

  const badgeSpring = spring({
    frame: frame - 25,
    fps: FPS,
    config: { damping: 14, mass: 0.7 },
  });

  const currentRank = Math.round(interp(frame, [rankDropStart, rankDropEnd], [INITIAL_RANK, FINAL_RANK]));

  const dropProgress = interp(frame, [rankDropStart, rankDropEnd], [0, 1]);
  const isDropping = frame >= rankDropStart && frame <= rankDropEnd;

  const r = Math.round(interp(dropProgress, [0, 1], [245, 232]));
  const g = Math.round(interp(dropProgress, [0, 1], [166, 64]));
  const b = Math.round(interp(dropProgress, [0, 1], [35, 64]));
  const rankColor = `rgb(${r}, ${g}, ${b})`;
  const glowColor = `rgba(${r}, ${g}, ${b}, ${interp(dropProgress, [0, 1], [0.45, 0.25])})`;

  const badgeSlideY = interp(dropProgress, [0, 1], [0, 200]);
  const badgeScale = interp(dropProgress, [0, 1], [1, 0.82]);
  const shakeX = isDropping ? Math.sin(frame * 0.7) * interp(dropProgress, [0, 0.6, 1], [0, 5, 0]) : 0;

  const rankPulse = isDropping ? 1 + Math.sin(frame * 0.5) * 0.06 : 1;

  const yearLabel =
    currentRank <= 10 ? "2026 年 3-4 月 · 唯一挤进第一梯队的国产模型" : "2026 年 5-6 月 · 两月内跌出第一梯队";

  const contrastOpacity = interp(frame, [settleEnd, settleEnd + 20], [0, 1]);

  const titleScale = interp(frame, [0, 20], [1.15, 1]);

  return (
    <AbsoluteFill
      style={{
        backgroundColor: DARK_BG,
        fontFamily: '"PingFang SC", "Microsoft YaHei", "Noto Sans SC", sans-serif',
      }}
    >
      {/* 背景网格 */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px)",
          backgroundSize: "80px 80px",
          opacity: interp(frame, [0, 30], [0, 0.5]),
        }}
      />

      {/* 顶部微光 */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: "50%",
          transform: "translateX(-50%)",
          width: 800,
          height: 400,
          background: `radial-gradient(ellipse at center, ${glowColor} 0%, transparent 70%)`,
          opacity: 0.15,
        }}
      />

      {/* 标题区域 */}
      <div
        style={{
          position: "absolute",
          top: 90,
          width: "100%",
          textAlign: "center",
          opacity: titleOpacity,
          transform: `scale(${titleScale})`,
        }}
      >
        <div style={{ fontSize: 22, color: TEXT_SECONDARY, letterSpacing: 10, textTransform: "uppercase" }}>
          Chatbot Arena
        </div>
        <div style={{ fontSize: 38, color: TEXT_PRIMARY, fontWeight: 700, marginTop: 6, letterSpacing: 6 }}>
          全球盲选评测 · 文本榜排名
        </div>
      </div>

      {/* 排行榜左侧模糊排名列表 */}
      <div
        style={{
          position: "absolute",
          top: 280,
          left: 200,
          width: 240,
          opacity: interp(frame, [40, 60], [0, 0.5]),
        }}
      >
        {Array.from({ length: 8 }, (_, i) => {
          const rn = i + 1 + (isDropping ? Math.floor((frame - rankDropStart) / 6) : 0);
          return (
            <div
              key={i}
              style={{
                display: "flex",
                alignItems: "center",
                padding: "6px 0",
                fontSize: 14,
                color: TEXT_SECONDARY,
                opacity: 0.35,
                fontFamily: "monospace",
              }}
            >
              <span style={{ width: 36, textAlign: "right", marginRight: 12 }}>#{rn}</span>
              <span>{rn <= 12 ? "Gemini-2.5-Pro" : rn <= 20 ? "Claude-4-Opus" : "Qwen3-Max"}</span>
            </div>
          );
        })}
      </div>

      {/* 中央排名徽章 */}
      <div
        style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          opacity: badgeSpring,
          transform: `translate(-50%, -50%) translateY(${badgeSlideY}px) translateX(${shakeX}px) scale(${badgeScale})`,
        }}
      >
        {/* 光晕 */}
        <div
          style={{
            position: "absolute",
            width: 320,
            height: 320,
            borderRadius: "50%",
            background: `radial-gradient(circle, ${glowColor} 0%, transparent 70%)`,
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            opacity: 0.7,
          }}
        />

        {/* 卡片背景 */}
        <div
          style={{
            background: CARD_BG,
            borderRadius: 20,
            border: `1px solid ${rankColor}`,
            boxShadow: `0 0 40px ${glowColor}, inset 0 0 60px rgba(0,0,0,0.5)`,
            padding: "40px 80px 32px",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
          }}
        >
          {/* 排名数字 */}
          <div
            style={{
              fontSize: 160,
              fontWeight: 900,
              color: rankColor,
              lineHeight: 1,
              transform: `scale(${rankPulse})`,
              textShadow: `0 0 80px ${glowColor}, 0 0 20px ${glowColor}`,
              letterSpacing: -4,
            }}
          >
            #{currentRank}
          </div>

          {/* 模型名称 */}
          <div
            style={{
              fontSize: 30,
              color: TEXT_PRIMARY,
              fontWeight: 500,
              marginTop: 12,
              letterSpacing: 1,
            }}
          >
            {MODEL_NAME}
          </div>

          {/* 排名标签 */}
          <div
            style={{
              marginTop: 18,
              padding: "6px 28px",
              borderRadius: 20,
              border: `1px solid ${rankColor}`,
              fontSize: 18,
              color: rankColor,
              fontWeight: 600,
              letterSpacing: 1,
            }}
          >
            {currentRank <= 10 ? "全球第一梯队 TOP 10" : `第 ${currentRank} 位`}
          </div>
        </div>

        {/* 时间上下文 */}
        <div
          style={{
            marginTop: 28,
            fontSize: 17,
            color: TEXT_SECONDARY,
            letterSpacing: 2,
            opacity: subtitleOpacity,
            textAlign: "center",
            maxWidth: 520,
          }}
        >
          {yearLabel}
        </div>
      </div>

      {/* 底部进度条 */}
      <div
        style={{
          position: "absolute",
          bottom: 150,
          left: "50%",
          transform: "translateX(-50%)",
          width: 700,
          opacity: badgeSpring,
        }}
      >
        {/* 两端标签 */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            marginBottom: 14,
            fontSize: 15,
            letterSpacing: 2,
          }}
        >
          <span style={{ color: dropProgress < 0.5 ? GOLD : TEXT_SECONDARY, fontWeight: dropProgress < 0.5 ? 700 : 400 }}>
            #10 · 2026.3
          </span>
          <span style={{ color: dropProgress > 0.5 ? RED : TEXT_SECONDARY, fontWeight: dropProgress > 0.5 ? 700 : 400 }}>
            #35 · 2026.5
          </span>
        </div>

        {/* 进度轨道 */}
        <div
          style={{
            height: 4,
            background: "rgba(255,255,255,0.08)",
            borderRadius: 2,
            overflow: "hidden",
          }}
        >
          <div
            style={{
              height: "100%",
              width: `${(dropProgress * 100).toFixed(1)}%`,
              background: `linear-gradient(90deg, ${GOLD}, ${RED})`,
              borderRadius: 2,
            }}
          />
        </div>

        {/* 进度指示点 */}
        <div style={{ position: "relative", height: 0 }}>
          <div
            style={{
              position: "absolute",
              left: `${(dropProgress * 100).toFixed(1)}%`,
              top: -18,
              transform: "translateX(-50%)",
              width: 14,
              height: 14,
              borderRadius: "50%",
              background: rankColor,
              boxShadow: `0 0 16px ${glowColor}`,
            }}
          />
        </div>
      </div>

      {/* 底部结论文字 */}
      <div
        style={{
          position: "absolute",
          bottom: 60,
          width: "100%",
          textAlign: "center",
          opacity: contrastOpacity,
        }}
      >
        <span style={{ fontSize: 20, color: RED, letterSpacing: 3, fontWeight: 600 }}>
          AI 模型竞争：两个月从巅峰到平庸
        </span>
      </div>
    </AbsoluteFill>
  );
};
