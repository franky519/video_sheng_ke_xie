import { useCurrentFrame, interpolate, spring, AbsoluteFill } from "remotion";

type ModelEntry = {
  name: string;
  initialRank: number;
  isDoubao: boolean;
  appearFrame: number;
};

const MODELS: ModelEntry[] = [
  { name: "GPT-5.5 Pro", initialRank: 1, isDoubao: false, appearFrame: 0 },
  { name: "Claude 4.5 Opus", initialRank: 2, isDoubao: false, appearFrame: 0 },
  { name: "Gemini 3.0 Ultra", initialRank: 3, isDoubao: false, appearFrame: 0 },
  { name: "Grok 4", initialRank: 4, isDoubao: false, appearFrame: 0 },
  { name: "Llama 4 405B", initialRank: 5, isDoubao: false, appearFrame: 0 },
  { name: "Mistral Large 3", initialRank: 6, isDoubao: false, appearFrame: 0 },
  { name: "Qwen 3 Max", initialRank: 7, isDoubao: false, appearFrame: 0 },
  { name: "豆包 Pro", initialRank: 8, isDoubao: true, appearFrame: 0 },
  { name: "DeepSeek V4", initialRank: 9, isDoubao: false, appearFrame: 0 },
  { name: "Yi Lightning 2", initialRank: 10, isDoubao: false, appearFrame: 0 },
  { name: "Gemma 3 27B", initialRank: 11, isDoubao: false, appearFrame: 0 },
  { name: "Command R4+", initialRank: 12, isDoubao: false, appearFrame: 0 },
  { name: "Phi-4 14B", initialRank: 13, isDoubao: false, appearFrame: 0 },
  { name: "Reka Core 2", initialRank: 14, isDoubao: false, appearFrame: 0 },
  { name: "Nemotron 5", initialRank: 15, isDoubao: false, appearFrame: 0 },
  { name: "MiniMax 01", initialRank: 16, isDoubao: false, appearFrame: 0 },
  { name: "GLM-5 Plus", initialRank: 17, isDoubao: false, appearFrame: 0 },
  { name: "Ernie 5.0", initialRank: 18, isDoubao: false, appearFrame: 0 },
  { name: "AWS Nova Pro 2", initialRank: 19, isDoubao: false, appearFrame: 0 },
  { name: "HyperCLOVA X3", initialRank: 20, isDoubao: false, appearFrame: 0 },
  { name: "Falcon 4 180B", initialRank: 21, isDoubao: false, appearFrame: 0 },
  { name: "Jamba 2 Large", initialRank: 22, isDoubao: false, appearFrame: 0 },
  { name: "InternLM3 Pro", initialRank: 23, isDoubao: false, appearFrame: 0 },
  { name: "Pythia-X 32B", initialRank: 24, isDoubao: false, appearFrame: 0 },
  { name: "Aya Vision 3", initialRank: 25, isDoubao: false, appearFrame: 0 },
  { name: "Sky-T1 72B", initialRank: 26, isDoubao: false, appearFrame: 0 },
  { name: "DarkSamurai 2", initialRank: 27, isDoubao: false, appearFrame: 0 },
  { name: "LLaMAX-3 120B", initialRank: 28, isDoubao: false, appearFrame: 0 },
  { name: "Pangea-ML 65B", initialRank: 29, isDoubao: false, appearFrame: 0 },
  { name: "OpenCUA 2 34B", initialRank: 30, isDoubao: false, appearFrame: 0 },
  { name: "Solar-X 48B", initialRank: 31, isDoubao: false, appearFrame: 0 },
  { name: "Granite 4 Code", initialRank: 32, isDoubao: false, appearFrame: 0 },
  { name: "Saul-4 42B", initialRank: 33, isDoubao: false, appearFrame: 0 },
  { name: "OLMo 3 70B", initialRank: 34, isDoubao: false, appearFrame: 0 },
  { name: "StarCoder 3", initialRank: 35, isDoubao: false, appearFrame: 0 },
  { name: "Vicuna-X 50B", initialRank: 36, isDoubao: false, appearFrame: 0 },
  { name: "Bagel-4 28B", initialRank: 37, isDoubao: false, appearFrame: 0 },
  { name: "Tulu 4 37B", initialRank: 38, isDoubao: false, appearFrame: 0 },
];

const TITLE = "Chatbot Arena 文本榜";
const SUBTITLE = "排名变化 · 2026 年 3 月 → 5 月";
const ROW_HEIGHT = 26;
const VISIBLE_ROWS = 20;
const TOP_OFFSET = 180;
const LEFT_MARGIN = 200;
const COL_WIDTH = 700;
const RANK_WIDTH = 100;

const formatRank = (r: number) => `#${r}`;

export const RankingAnimation: React.FC = () => {
  const frame = useCurrentFrame();

  const doubaoEntry = MODELS.find((m) => m.isDoubao)!;
  const doubaoIndex = MODELS.indexOf(doubaoEntry);
  const modelsBeforeDoubao = MODELS.slice(0, doubaoIndex + 1);
  const modelsAboveDoubao = modelsBeforeDoubao.filter((m) => !m.isDoubao).length;

  const visibleStart = Math.max(
    0,
    Math.min(modelsAboveDoubao - (doubaoIndex > VISIBLE_ROWS - 3 ? doubaoIndex - (VISIBLE_ROWS - 3) : 0), MODELS.length - VISIBLE_ROWS)
  );

  const scrollOffset = interpolate(frame, [0, 180], [0, Math.max(0, doubaoIndex - 3) * ROW_HEIGHT], {
    extrapolateRight: "clamp",
    extrapolateLeft: "clamp",
  });

  const animatedDoubaoRank = interpolate(frame, [0, 150], [8, 35], {
    extrapolateRight: "clamp",
    extrapolateLeft: "clamp",
  });

  const isFinalFrame = frame > 210;

  return (
    <AbsoluteFill style={{ backgroundColor: "#0d0d0d" }}>
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: "100%",
          height: "100%",
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px)",
          backgroundSize: "32px 32px",
        }}
      />

      <div
        style={{
          position: "absolute",
          top: 60,
          left: LEFT_MARGIN,
          fontSize: 36,
          fontWeight: 700,
          color: "#ffffff",
          letterSpacing: 2,
        }}
      >
        {TITLE}
      </div>
      <div
        style={{
          position: "absolute",
          top: 108,
          left: LEFT_MARGIN,
          fontSize: 18,
          color: "#888888",
          letterSpacing: 1,
        }}
      >
        {SUBTITLE}
      </div>

      <div
        style={{
          position: "absolute",
          top: TOP_OFFSET - 30,
          left: LEFT_MARGIN,
          width: COL_WIDTH + RANK_WIDTH + 20,
          display: "flex",
          justifyContent: "space-between",
          fontSize: 13,
          color: "#555",
          letterSpacing: 1,
          borderBottom: "1px solid #222",
          paddingBottom: 8,
        }}
      >
        <span>模型</span>
        <span>排名</span>
      </div>

      <div
        style={{
          position: "absolute",
          top: TOP_OFFSET,
          left: 0,
          right: 0,
          height: VISIBLE_ROWS * ROW_HEIGHT,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            position: "absolute",
            top: -scrollOffset,
            left: LEFT_MARGIN,
            width: COL_WIDTH + RANK_WIDTH + 20,
          }}
        >
          {MODELS.map((model, idx) => {
            const rowTop = idx * ROW_HEIGHT;
            const isDoubao = model.isDoubao;

            const baseOpacity = Math.max(
              0.3,
              1 - Math.abs(rowTop - scrollOffset - (VISIBLE_ROWS * ROW_HEIGHT) / 2) / 500
            );

            const displayRank = isDoubao
              ? Math.round(animatedDoubaoRank)
              : isFinalFrame && model.initialRank < 8
                ? model.initialRank
                : isFinalFrame && model.initialRank > 8
                  ? model.initialRank + 27
                  : model.initialRank;

            const springScale = spring({
              frame: frame - idx * 2,
              fps: 30,
              config: { damping: 12, mass: 0.5 },
            });

            return (
              <div
                key={model.name}
                style={{
                  position: "absolute",
                  top: rowTop,
                  height: ROW_HEIGHT,
                  width: "100%",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  fontSize: 15,
                  color: isDoubao ? "#00ff66" : `rgba(255,255,255,${isFinalFrame ? 0.7 : baseOpacity})`,
                  fontWeight: isDoubao ? 700 : 400,
                  backgroundColor: isDoubao ? "rgba(0,255,102,0.08)" : "transparent",
                  borderRadius: 4,
                  paddingLeft: 8,
                  paddingRight: 8,
                  transform: isDoubao ? `scale(${springScale})` : undefined,
                  borderLeft: isDoubao ? "3px solid #00ff66" : "3px solid transparent",
                  transition: "color 0.5s",
                }}
              >
                <span>{isDoubao ? "✦ " : ""}{model.name}</span>
                <span style={{ fontVariantNumeric: "tabular-nums", width: RANK_WIDTH, textAlign: "right" }}>
                  {formatRank(displayRank)}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {isFinalFrame && (
        <div
          style={{
            position: "absolute",
            bottom: 100,
            left: LEFT_MARGIN,
            fontSize: 20,
            color: "#ff4444",
            fontWeight: 600,
            letterSpacing: 1,
            opacity: interpolate(frame, [210, 230], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
          }}
        >
          从唯一国产 TOP 10 → 两月后跌至 #35
        </div>
      )}
    </AbsoluteFill>
  );
};
