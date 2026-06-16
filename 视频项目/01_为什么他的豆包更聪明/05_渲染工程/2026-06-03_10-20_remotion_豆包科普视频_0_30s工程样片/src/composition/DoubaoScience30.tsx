import type {ReactNode} from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig, spring, staticFile} from 'remotion';
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
import {DebugTag, StageBackground, Subtitle, Timecode, WindowContainer} from '../components/Stage';
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
  if (frame >= ranges.intro.end) return null;

  const windowScale = spring({
    frame,
    fps,
    config: {damping: 14, mass: 0.8},
  });

  const questionMarkScale = spring({
    frame: frame - 12, // starts at 0.5s (12 frames)
    fps,
    config: {damping: 10, mass: 0.5},
  });

  const questionMarkRotate = frame >= 24 ? Math.sin((frame - 24) * 0.4) * 12 : 0;

  return (
    <AbsoluteFill>
      <SceneTitle>你有没有经历过这种诡异的事——</SceneTitle>
      <WindowContainer style={{transform: `translate(-50%, -50%) scale(${windowScale})`}}>
        {/* Background: Empty Doubao screen */}
        <img
          src={staticFile('assets/ASSET_01_01.png')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
          alt="ASSET_01_01"
        />
        {/* Giant Question Mark */}
        {frame >= 12 && (
          <div
            style={{
              position: 'absolute',
              left: '50%',
              top: '50%',
              transform: `translate(-50%, -50%) scale(${questionMarkScale}) rotate(${questionMarkRotate}deg)`,
              fontSize: '140px',
              fontWeight: 'bold',
              color: '#ff3b35',
              fontFamily: 'monospace',
              textShadow: '0 0 35px rgba(255, 59, 53, 0.7), 4px 4px 0px #000000, -4px -4px 0px #000000, 4px -4px 0px #000000, -4px 4px 0px #000000',
              zIndex: 20,
            }}
          >
            ?
          </div>
        )}
      </WindowContainer>
      {showDebugLabels && (
        <DebugTag>00:00-00:02 / ASSET_01_01 / Spring scale + question mark wiggle</DebugTag>
      )}
    </AbsoluteFill>
  );
};

const PlainAnswerScene = ({showDebugLabels}: {showDebugLabels: boolean}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  if (frame < ranges.plainAnswer.start || frame >= ranges.plainAnswer.end) return null;

  // Contract slide up starting at frame 48 (2.0s)
  const contractSlide = spring({
    frame: frame - 48,
    fps,
    config: {damping: 15, mass: 0.7},
  });
  const contractY = (1 - contractSlide) * 120; // percent

  // Laser scanning line: active from frame 84 (3.5s) to 132 (5.5s)
  const scanProgress = Math.min(Math.max((frame - 84) / 48, 0), 1);
  const scanY = scanProgress * 100; // percent
  const scanOpacity = frame >= 84 && frame <= 132 ? 1 : 0;

  // Blur and dim contract after frame 168 (7s)
  const contractBlur = frame >= 168 ? Math.min((frame - 168) * 0.8, 10) : 0;
  const contractOpacity = frame >= 168 ? Math.max(1 - (frame - 168) * 0.05, 0.25) : 1;

  // Typing user question: starts at frame 60 (2.5s)
  const typeStart = 60;
  const typeDuration = 28;
  const fullQuery = '帮我看看这份重疾险条款有没有坑';
  const typedText = fullQuery.substring(0, Math.floor(Math.max(0, (frame - typeStart) / (typeDuration / fullQuery.length))));
  const cursorVisible = frame >= typeStart && frame < typeStart + typeDuration ? (Math.floor(frame / 6) % 2 === 0 ? '|' : '') : '';

  // Plain answer card slide up at frame 168 (7.0s)
  const answerSlide = spring({
    frame: frame - 168,
    fps,
    config: {damping: 14},
  });
  const answerY = (1 - answerSlide) * 100; // pixels
  const answerOpacity = linear(frame, 168, 178, 0, 1);

  // Red Stamp at frame 228 (9.5s)
  const stampProgress = spring({
    frame: frame - 228,
    fps,
    config: {damping: 8, mass: 0.5},
  });
  const stampScale = 3 - (stampProgress * 2);
  const stampOpacity = frame >= 228 ? 1 : 0;

  // Screen Shake
  const isShaking = frame >= 228 && frame < 233;
  const shakeX = isShaking ? (Math.random() - 0.5) * 12 : 0;
  const shakeY = isShaking ? (Math.random() - 0.5) * 12 : 0;

  return (
    <AbsoluteFill style={{transform: `translate(${shakeX}px, ${shakeY}px)`}}>
      <SceneTitle>普通模式：答复充满专业名词的背书废话</SceneTitle>
      <WindowContainer>
        <div style={{display: 'flex', width: '100%', height: '100%'}}>
          {/* Left Half: Contract Document */}
          <div
            style={{
              width: '42%',
              height: '100%',
              borderRight: '3px solid #000000',
              backgroundColor: '#f3f4f6',
              position: 'relative',
              overflow: 'hidden',
              transform: `translateY(${contractY}%)`,
              filter: `blur(${contractBlur}px)`,
              opacity: contractOpacity,
            }}
          >
            <img
              src={staticFile('assets/ASSET_02_02.png')}
              style={{width: '100%', height: '100%', objectFit: 'cover'}}
              alt="contract"
            />
            {/* Laser Scanning Line */}
            {scanOpacity > 0 && (
              <div
                style={{
                  position: 'absolute',
                  left: 0,
                  right: 0,
                  top: `${scanY}%`,
                  height: '8px',
                  background: 'linear-gradient(180deg, transparent, #00FF88, transparent)',
                  boxShadow: '0 0 15px #00FF88',
                  opacity: scanOpacity,
                }}
              />
            )}
          </div>

          {/* Right Half: Doubao Interface */}
          <div
            style={{
              width: '58%',
              height: '100%',
              backgroundColor: '#f9fafb',
              padding: '24px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
            }}
          >
            {/* Dialog area */}
            <div style={{flex: 1, display: 'flex', flexDirection: 'column', gap: '16px', overflow: 'hidden'}}>
              {/* User message */}
              <div style={{display: 'flex', justifyContent: 'flex-end'}}>
                <div
                  style={{
                    backgroundColor: '#1f2937',
                    color: '#ffffff',
                    padding: '14px 18px',
                    borderRadius: '16px 16px 4px 16px',
                    fontSize: '20px',
                    fontWeight: 'bold',
                    maxWidth: '85%',
                    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
                  }}
                >
                  {typedText}
                  {cursorVisible}
                </div>
              </div>

              {/* AI plain answer bubble */}
              {frame >= 168 && (
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'flex-start',
                    transform: `translateY(${answerY}px)`,
                    opacity: answerOpacity,
                    position: 'relative',
                  }}
                >
                  <div
                    style={{
                      backgroundColor: '#ffffff',
                      border: '2px solid #e5e7eb',
                      color: '#374151',
                      padding: '20px',
                      borderRadius: '16px 16px 16px 4px',
                      fontSize: '18px',
                      lineHeight: '1.5',
                      maxWidth: '90%',
                      boxShadow: '0 6px 16px rgba(0, 0, 0, 0.05)',
                    }}
                  >
                    <div style={{fontWeight: 'bold', fontSize: '20px', color: '#111827', marginBottom: '8px'}}>普通模式回复：</div>
                    <div style={{marginBottom: '6px'}}>• 本产品保障120种重大疾病，等待期为90天。</div>
                    <div style={{marginBottom: '6px'}}>• 赔付比例按合同规定基本保额给付。</div>
                    <div>• 投保前请仔细阅读责任免除及犹豫期。</div>
                  </div>

                  {/* Giant Stamp */}
                  {frame >= 228 && (
                    <div
                      style={{
                        position: 'absolute',
                        left: '45%',
                        top: '35%',
                        transform: `translate(-50%, -50%) scale(${stampScale}) rotate(-12deg)`,
                        opacity: stampOpacity,
                        border: '6px solid #ff3b35',
                        borderRadius: '8px',
                        padding: '8px 16px',
                        color: '#ff3b35',
                        fontSize: '32px',
                        fontWeight: 'bold',
                        fontFamily: 'monospace',
                        backgroundColor: 'rgba(255, 255, 255, 0.95)',
                        textShadow: '0px 0px 10px rgba(255, 59, 53, 0.2)',
                        boxShadow: '0 10px 25px rgba(255, 59, 53, 0.3)',
                        zIndex: 15,
                      }}
                    >
                      背书废话
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </WindowContainer>
      {showDebugLabels && (
        <DebugTag>00:02-00:12 / ASSET_02_02 + ASSET_03_01 / Contract scan + Stamp shake</DebugTag>
      )}
    </AbsoluteFill>
  );
};

const ExpertAnswerScene = ({showDebugLabels}: {showDebugLabels: boolean}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  if (frame < ranges.expertAnswer.start || frame >= ranges.expertAnswer.end) return null;

  // Left window animation (frame 288 to 312, 1s duration)
  const slideLeft = spring({
    frame: frame - 288,
    fps,
    config: {damping: 14, mass: 0.8},
  });
  const leftWinX = slideLeft * -280; // pixels
  const leftWinScale = 1 - slideLeft * 0.22;
  const leftWinOpacity = 1 - slideLeft * 0.65;
  const leftWinBlur = slideLeft * 6;

  // Right window animation (frame 293 to 317)
  const slideRight = spring({
    frame: frame - 293,
    fps,
    config: {damping: 14, mass: 0.8},
  });
  const rightWinX = 550 - slideRight * 550; // pixels from right

  // Card popups
  const card1Scale = spring({
    frame: frame - 324, // 13.5s
    fps,
    config: {damping: 12},
  });
  const card2Scale = spring({
    frame: frame - 340, // 14.2s
    fps,
    config: {damping: 12},
  });
  const card3Scale = spring({
    frame: frame - 356, // 14.8s
    fps,
    config: {damping: 12},
  });

  // 17s - 22s Zoom-in detail
  const zoomProgress = spring({
    frame: frame - 408, // 17.0s
    fps,
    config: {damping: 13, mass: 0.75},
  });
  const zoomOpacity = linear(frame, 408, 418, 0, 1);

  // Magnifier
  const magnifierScale = spring({
    frame: frame - 427, // 17.8s
    fps,
    config: {damping: 12, mass: 0.6},
  });
  const magnifierProgress = Math.min(Math.max((frame - 444) / 48, 0), 1); // 2s duration
  const magnifierX = -120 + magnifierProgress * 240; // slide X

  // Green Marker Line width
  const markerProgress = Math.min(Math.max((frame - 451) / 48, 0), 1);
  const markerWidth = markerProgress * 280; // pixels

  return (
    <AbsoluteFill>
      <SceneTitle>专家模式：直接指出容易忽略的隐藏坑点</SceneTitle>
      {/* Left Window: Shrunk Plain Dialog */}
      <div
        style={{
          position: 'absolute',
          left: '50%',
          top: '50%',
          transform: `translate(calc(-50% + ${leftWinX}px), -50%) scale(${leftWinScale})`,
          opacity: leftWinOpacity,
          filter: `blur(${leftWinBlur}px)`,
          pointerEvents: 'none',
        }}
      >
        <WindowContainer style={{boxShadow: 'none'}}>
          <div style={{display: 'flex', width: '100%', height: '100%'}}>
            <div style={{width: '42%', height: '100%', borderRight: '3px solid #000000', opacity: 0.3}}>
              <img src={staticFile('assets/ASSET_02_02.png')} style={{width: '100%', height: '100%', objectFit: 'cover'}} alt="c" />
            </div>
            <div style={{width: '58%', height: '100%', backgroundColor: '#f9fafb', padding: '24px'}}>
              <div style={{backgroundColor: '#ffffff', border: '2px solid #e5e7eb', padding: '20px', borderRadius: '16px'}}>
                <div style={{fontWeight: 'bold', fontSize: '20px', color: '#111827', marginBottom: '8px'}}>普通模式回复：</div>
                <div>• 本产品保障120种重大疾病，等待期为90天。</div>
              </div>
            </div>
          </div>
        </WindowContainer>
      </div>

      {/* Right Window: Expert Dialog sliding in */}
      <div
        style={{
          position: 'absolute',
          left: '50%',
          top: '50%',
          transform: `translate(calc(-50% + ${rightWinX}px), -50%)`,
          zIndex: 10,
        }}
      >
        <WindowContainer style={{borderColor: '#15814c', boxShadow: '0 24px 60px rgba(21, 129, 76, 0.25)'}}>
          {/* Expert Answer layout */}
          <div
            style={{
              width: '100%',
              height: '100%',
              backgroundColor: '#f3faf6',
              padding: '28px',
              display: 'flex',
              flexDirection: 'column',
              gap: '16px',
            }}
          >
            <div style={{fontSize: '22px', fontWeight: 'bold', color: '#15814c', display: 'flex', alignItems: 'center', gap: '8px'}}>
              <div style={{width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#15814c'}} />
              豆包专家模式回答：已诊断出3处免责条款隐蔽风险
            </div>

            {/* List of cards */}
            <div style={{display: 'flex', flexDirection: 'column', gap: '12px', flex: 1}}>
              {frame >= 324 && (
                <div
                  style={{
                    transform: `scale(${card1Scale})`,
                    backgroundColor: '#ffffff',
                    border: '2px solid #15814c',
                    borderRadius: '12px',
                    padding: '14px 18px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '14px',
                    boxShadow: '0 4px 12px rgba(21, 129, 76, 0.08)',
                  }}
                >
                  <div style={{backgroundColor: '#e3f7ed', color: '#15814c', padding: '6px 12px', borderRadius: '6px', fontWeight: 'bold', fontSize: '18px'}}>风险一</div>
                  <div style={{fontSize: '18px', fontWeight: 'bold', color: '#111827'}}>“轻度脑中风后遗症”理赔标准过苛（需等待180天诊断）</div>
                </div>
              )}

              {frame >= 340 && (
                <div
                  style={{
                    transform: `scale(${card2Scale})`,
                    backgroundColor: '#ffffff',
                    border: '2px solid #15814c',
                    borderRadius: '12px',
                    padding: '14px 18px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '14px',
                    boxShadow: '0 4px 12px rgba(21, 129, 76, 0.08)',
                  }}
                >
                  <div style={{backgroundColor: '#e3f7ed', color: '#15814c', padding: '6px 12px', borderRadius: '6px', fontWeight: 'bold', fontSize: '18px'}}>风险二</div>
                  <div style={{fontSize: '18px', fontWeight: 'bold', color: '#111827'}}>原位癌除外责任中，未包含浸润癌早期诊断豁免</div>
                </div>
              )}

              {frame >= 356 && (
                <div
                  style={{
                    transform: `scale(${card3Scale})`,
                    backgroundColor: '#ffffff',
                    border: '2px solid #15814c',
                    borderRadius: '12px',
                    padding: '14px 18px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '14px',
                    boxShadow: '0 4px 12px rgba(21, 129, 76, 0.08)',
                  }}
                >
                  <div style={{backgroundColor: '#e3f7ed', color: '#15814c', padding: '6px 12px', borderRadius: '6px', fontWeight: 'bold', fontSize: '18px'}}>风险三</div>
                  <div style={{fontSize: '18px', fontWeight: 'bold', color: '#111827'}}>附录小字排除“先天性遗传疾病引发的重疾责任”</div>
                </div>
              )}
            </div>
          </div>
        </WindowContainer>
      </div>

      {/* 17s - 22s: Zoom-in card overlays on top */}
      {frame >= 408 && (
        <div
          style={{
            position: 'absolute',
            left: '50%',
            top: '55%',
            transform: `translate(-50%, -50%) scale(${zoomProgress})`,
            opacity: zoomOpacity,
            width: '750px',
            height: '420px',
            backgroundColor: '#ffffff',
            border: '4px solid #000000',
            borderRadius: '16px',
            boxShadow: '0 30px 80px rgba(0, 0, 0, 0.5)',
            zIndex: 30,
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <div style={{height: '36px', borderBottom: '3px solid #000000', backgroundColor: '#eaeaea', display: 'flex', alignItems: 'center', padding: '0 12px', fontWeight: 'bold', fontSize: '14px'}}>
            附录小字区域特写 - 既往症除外条款
          </div>
          <div style={{flex: 1, backgroundColor: '#faf9f6', padding: '40px', position: 'relative', fontFamily: 'serif', color: '#333333'}}>
            <div style={{fontSize: '22px', lineHeight: '2', marginBottom: '20px'}}>
              第十八条 免责责任限制与既往疾病：
            </div>
            <div style={{fontSize: '19px', lineHeight: '2', position: 'relative'}}>
              因遗传性疾病、先天性畸形或
              <span style={{position: 'relative', fontWeight: 'bold'}}>
                【先天性遗传疾病】
                {frame >= 451 && (
                  <span
                    style={{
                      position: 'absolute',
                      left: 0,
                      bottom: '1px',
                      height: '22px',
                      width: `${markerWidth}px`,
                      backgroundColor: 'rgba(0, 255, 136, 0.45)',
                      borderRadius: '4px',
                      zIndex: -1,
                    }}
                  />
                )}
              </span>
              导致的保险责任，本公司不予承担赔付责任。
            </div>

            {/* Hover Magnifier Glass */}
            {frame >= 427 && (
              <div
                style={{
                  position: 'absolute',
                  left: `calc(50% + ${magnifierX}px)`,
                  top: '40%',
                  transform: `translate(-50%, -50%) scale(${magnifierScale})`,
                  width: '180px',
                  height: '180px',
                  border: '6px solid #00ff88',
                  borderRadius: '50%',
                  backgroundColor: 'rgba(255, 255, 255, 0.98)',
                  boxShadow: '0 10px 30px rgba(0, 0, 0, 0.25)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  overflow: 'hidden',
                  zIndex: 35,
                }}
              >
                <div style={{textAlign: 'center', padding: '10px'}}>
                  <div style={{fontSize: '12px', color: '#15814c', fontWeight: 'bold', marginBottom: '4px'}}>除外责任</div>
                  <div style={{fontSize: '16px', fontWeight: 'bold', color: '#ff3b35'}}>拒赔风险！</div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {showDebugLabels && (
        <DebugTag>00:12-00:22 / ASSET_04_01 + ASSET_05_03 / Split windows + Appendix zoom + Highlighter</DebugTag>
      )}
    </AbsoluteFill>
  );
};

const PromptQuestionScene = ({showDebugLabels}: {showDebugLabels: boolean}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  if (frame < ranges.promptQuestion.start || frame >= ranges.promptQuestion.end) {
    return null;
  }

  const startF = ranges.promptQuestion.start;
  const leftProgress = smooth(frame, startF, startF + secondsToFrames(0.8), 0, 1);
  const rightProgress = smooth(frame, startF + secondsToFrames(0.2), startF + secondsToFrames(1), 0, 1);
  const leftX = -520 + 905 * leftProgress;
  const rightX = 1280 + 520 - 905 * rightProgress;

  const questionScale =
    frame < startF + secondsToFrames(2.5)
      ? springScale({
          frame,
          fps,
          start: startF + secondsToFrames(2),
          from: 0,
          to: 1.2,
          damping: 10,
          mass: 0.5,
        })
      : 1 + Math.sin((frame - (startF + secondsToFrames(2.5))) * 0.55) * 0.015;
  const questionOpacity = linear(frame, startF + secondsToFrames(2), startF + secondsToFrames(2.35), 0, 1);
  const glow = linear(frame, startF + secondsToFrames(2), startF + secondsToFrames(2.5), 0, 1);

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
        <DebugTag>00:22-00:36 / ASSET_06_01 + ASSET_06_02 / Prompt Search + Handshake</DebugTag>
      ) : null}
    </AbsoluteFill>
  );
};
