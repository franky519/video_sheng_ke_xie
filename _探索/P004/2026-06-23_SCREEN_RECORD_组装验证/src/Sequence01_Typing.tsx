import { useCurrentFrame, useVideoConfig, interpolate, OffthreadVideo, staticFile } from "remotion";

export const Sequence01Typing: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  const durationInFrames = fps * 8;

  const containerScale = interpolate(
    frame,
    [0, durationInFrames],
    [1.0, 1.15],
    { extrapolateRight: "clamp" }
  );

  const greenBoxOpacity = interpolate(
    frame,
    [fps * 4.5, fps * 5.2],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const greenBoxClip = interpolate(
    frame,
    [fps * 5.2, fps * 5.8],
    [100, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <div
      style={{
        width,
        height,
        backgroundColor: "#1A1A1A",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Layer 0: Grid background */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage:
            "linear-gradient(#333333 1px, transparent 1px), linear-gradient(90deg, #333333 1px, transparent 1px)",
          backgroundSize: "40px 40px",
          opacity: 0.15,
        }}
      />

      {/* Layer 1: Video container with Slow Push-in */}
      <div
        style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          width: width * 0.85,
          height: height * 0.85,
          transform: `translate(-50%, -50%) scale(${containerScale})`,
          transformOrigin: "center center",
          borderRadius: 16,
          overflow: "hidden",
          boxShadow: "0 0 60px rgba(0,0,0,0.5)",
        }}
      >
        <OffthreadVideo
          src={staticFile("doubao_typing.webm")}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "contain",
          }}
        />
      </div>

      {/* Layer 2: Green scan box — frames "免费额度" area */}
      <div
        style={{
          position: "absolute",
          top: height * 0.48,
          left: width * 0.28,
          width: width * 0.15,
          height: height * 0.045,
          border: "3px solid #00FF66",
          borderRadius: 4,
          opacity: greenBoxOpacity,
          boxShadow: "0 0 12px rgba(0, 255, 102, 0.5)",
          clipPath: `inset(0% 0% 0% ${greenBoxClip}%)`,
          pointerEvents: "none",
        }}
      />

      {/* Green scan line effect */}
      <div
        style={{
          position: "absolute",
          top: height * 0.48,
          left: width * 0.28,
          width: width * 0.15,
          height: 2,
          background: "linear-gradient(90deg, transparent, #00FF66, transparent)",
          opacity: greenBoxOpacity * 0.7,
          pointerEvents: "none",
        }}
      />
    </div>
  );
};
