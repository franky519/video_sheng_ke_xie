import type {ReactNode} from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';
import {AssetLedger} from '../components/AssetLedger';
import {
  ExpertAnswerCard,
  Magnifier,
  PlainAnswerCard,
  PromptCard,
  QuestionCard,
  QuestionMark,
} from '../components/Cards';
import {PhoneMock} from '../components/PhoneMock';
import {DebugTag, StageBackground, Subtitle, Timecode} from '../components/Stage';
import {linear, smooth, springScale} from '../lib/motion';
import {ranges, secondsToFrames} from '../lib/timeline';

type DoubaoScience30Props = {
  showDebugLabels?: boolean;
};

export const DoubaoScience30 = ({showDebugLabels = true}: DoubaoScience30Props) => {
  return (
    <StageBackground>
      <IntroScene showDebugLabels={showDebugLabels} />
      <PlainAnswerScene showDebugLabels={showDebugLabels} />
      <ExpertAnswerScene showDebugLabels={showDebugLabels} />
      <PromptQuestionScene showDebugLabels={showDebugLabels} />
      <Timecode />
      <Subtitle />
      <AssetLedger visible={showDebugLabels} />
    </StageBackground>
  );
};

const SceneTitle = ({children}: {children: ReactNode}) => {
  return <div className="scene-title">{children}</div>;
};

const IntroScene = ({showDebugLabels}: {showDebugLabels: boolean}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const sceneOpacity = linear(frame, ranges.intro.start, ranges.intro.end - secondsToFrames(0.2), 1, 1);
  const leftScale = springScale({
    frame,
    fps,
    start: secondsToFrames(0),
    from: 0,
    to: 1,
    damping: 15,
    mass: 0.6,
  });
  const rightScaleBase = springScale({
    frame,
    fps,
    start: secondsToFrames(1),
    from: 0,
    to: 1,
    damping: 15,
    mass: 0.6,
  });
  const leftOpacity = linear(frame, secondsToFrames(2.5), secondsToFrames(5), 1, 0.4);
  const rightZoom = linear(frame, secondsToFrames(3), secondsToFrames(5), 1, 1.05);

  if (frame >= ranges.intro.end) {
    return null;
  }

  return (
    <AbsoluteFill style={{opacity: sceneOpacity}}>
      <SceneTitle>同一个问题，两个答案为什么差这么多？</SceneTitle>
      <div className="intro-layout">
        <div
          className="phone-slot phone-slot-left"
          style={{
            opacity: leftOpacity,
            transform: `translateX(-20%) scale(${leftScale})`,
          }}
        >
          <PhoneMock variant="plain" />
          <div className="phone-caption muted">像复制粘贴</div>
        </div>
        <div
          className="phone-slot phone-slot-right"
          style={{
            transform: `translateX(20%) scale(${rightScaleBase * rightZoom})`,
          }}
        >
          <PhoneMock variant="expert" />
          <div className="phone-caption strong">像专家</div>
        </div>
      </div>
      {showDebugLabels ? (
        <DebugTag>00:00-00:05 / ASSET_01_01 + ASSET_01_02 + ASSET_01_03 / CSS fallback</DebugTag>
      ) : null}
    </AbsoluteFill>
  );
};

const PlainAnswerScene = ({showDebugLabels}: {showDebugLabels: boolean}) => {
  const frame = useCurrentFrame();
  if (frame < ranges.plainAnswer.start || frame >= ranges.plainAnswer.end) {
    return null;
  }

  const questionOpacity =
    linear(frame, secondsToFrames(5), secondsToFrames(5.8), 0, 1) *
    linear(frame, secondsToFrames(12), secondsToFrames(13.5), 1, 0);
  const questionY = smooth(frame, secondsToFrames(5), secondsToFrames(5.8), 385, 116);
  const answerOpacity =
    linear(frame, secondsToFrames(7), secondsToFrames(7.5), 0, 1) *
    linear(frame, secondsToFrames(13.5), secondsToFrames(15), 1, 0);
  const answerBlur = linear(frame, secondsToFrames(13.5), secondsToFrames(15), 0, 20);
  const scroll = linear(frame, secondsToFrames(8.5), secondsToFrames(13.5), 0, 80);

  return (
    <AbsoluteFill>
      <SceneTitle>普通模式：答案有内容，但没有判断</SceneTitle>
      <div
        className="question-wrap"
        style={{
          opacity: questionOpacity,
          transform: `translate(-50%, ${questionY}px)`,
        }}
      >
        <QuestionCard />
      </div>
      <div
        className="plain-answer-wrap"
        style={{
          opacity: answerOpacity,
          filter: `blur(${answerBlur}px)`,
        }}
      >
        <PlainAnswerCard scroll={scroll} />
      </div>
      {showDebugLabels ? (
        <DebugTag>00:05-00:15 / ASSET_02_01 + ASSET_02_02 / TranslateY + Blur + Opacity</DebugTag>
      ) : null}
    </AbsoluteFill>
  );
};

const ExpertAnswerScene = ({showDebugLabels}: {showDebugLabels: boolean}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  if (frame < ranges.expertAnswer.start || frame >= ranges.expertAnswer.end) {
    return null;
  }

  const cardScale = springScale({
    frame,
    fps,
    start: secondsToFrames(15),
    from: 0.9,
    to: 1,
    damping: 12,
    mass: 0.6,
  });
  const greenClip = smooth(frame, secondsToFrames(16.5), secondsToFrames(17.5), 0, 1);
  const orangeClip = smooth(frame, secondsToFrames(19), secondsToFrames(20), 0, 1);
  const magnifierScale = springScale({
    frame,
    fps,
    start: secondsToFrames(21.5),
    from: 0,
    to: 1,
    damping: 12,
    mass: 0.6,
  });
  const jitterX = Math.sin(frame * 0.82) * 2 * linear(frame, secondsToFrames(22.5), secondsToFrames(25), 0, 1);
  const jitterY = Math.cos(frame * 0.76) * 2 * linear(frame, secondsToFrames(22.5), secondsToFrames(25), 0, 1);

  return (
    <AbsoluteFill>
      <SceneTitle>专家模式：直接指出坑点</SceneTitle>
      <div
        className="expert-wrap"
        style={{
          transform: `translate(-50%, -50%) scale(${cardScale})`,
        }}
      >
        <ExpertAnswerCard greenClip={greenClip} orangeClip={orangeClip} />
      </div>
      <div
        className="magnifier-wrap"
        style={{
          opacity: magnifierScale,
          transform: `translate(${jitterX}px, ${jitterY}px) scale(${magnifierScale})`,
        }}
      >
        <Magnifier />
      </div>
      {showDebugLabels ? (
        <DebugTag>00:15-00:25 / ASSET_03_01 + ASSET_03_02 / ClipPath + local magnifier + Spring</DebugTag>
      ) : null}
    </AbsoluteFill>
  );
};

const PromptQuestionScene = ({showDebugLabels}: {showDebugLabels: boolean}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  if (frame < ranges.promptQuestion.start || frame >= ranges.promptQuestion.end) {
    return null;
  }

  const leftProgress = smooth(frame, secondsToFrames(25), secondsToFrames(25.8), 0, 1);
  const rightProgress = smooth(frame, secondsToFrames(25.2), secondsToFrames(26), 0, 1);
  const leftX = -520 + 905 * leftProgress;
  const rightX = 1280 + 520 - 905 * rightProgress;
  const questionScale =
    frame < secondsToFrames(27.5)
      ? springScale({
          frame,
          fps,
          start: secondsToFrames(27),
          from: 0,
          to: 1.2,
          damping: 10,
          mass: 0.5,
        })
      : 1 + Math.sin((frame - secondsToFrames(27.5)) * 0.55) * 0.015;
  const questionOpacity = linear(frame, secondsToFrames(27), secondsToFrames(27.35), 0, 1);
  const glow = linear(frame, secondsToFrames(27), secondsToFrames(27.5), 0, 1);

  return (
    <AbsoluteFill>
      <SceneTitle>观众的第一反应：是不是提示词问题？</SceneTitle>
      <div
        className="prompt-card-wrap"
        style={{
          transform: `translate(${leftX}px, 125px) rotate(${-8 * leftProgress}deg)`,
        }}
      >
        <PromptCard variant="guide" />
      </div>
      <div
        className="prompt-card-wrap"
        style={{
          transform: `translate(${rightX}px, 125px) rotate(${8 * rightProgress}deg)`,
        }}
      >
        <PromptCard variant="super" />
      </div>
      <div
        className="question-mark-wrap"
        style={{
          opacity: questionOpacity,
          transform: `translate(-50%, -50%) scale(${questionScale})`,
          filter: `drop-shadow(0 0 ${30 * glow}px rgba(255, 52, 52, ${0.75 * glow}))`,
        }}
      >
        <QuestionMark />
      </div>
      {showDebugLabels ? (
        <DebugTag>00:25-00:30 / ASSET_04_01 + ASSET_04_02 + ASSET_04_03 / Rotate + TranslateX + Glow</DebugTag>
      ) : null}
    </AbsoluteFill>
  );
};
