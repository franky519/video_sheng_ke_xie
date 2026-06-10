import type {ReactNode} from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {subtitles} from '../lib/timeline';

export const StageBackground = ({children}: {children: ReactNode}) => {
  return (
    <AbsoluteFill className="stage">
      <div className="stage-grid" />
      {children}
    </AbsoluteFill>
  );
};

export const Timecode = () => {
  const frame = useCurrentFrame();
  const seconds = frame / 24;
  return <div className="timecode">{seconds.toFixed(1)}s</div>;
};

export const Subtitle = () => {
  const frame = useCurrentFrame();
  const seconds = frame / 24;
  const item = subtitles.find((subtitle) => seconds >= subtitle.start && seconds < subtitle.end);

  if (!item) {
    return null;
  }

  return (
    <div className="subtitle">
      <span>{item.text}</span>
    </div>
  );
};

export const DebugTag = ({children}: {children: ReactNode}) => {
  return <div className="debug-tag">{children}</div>;
};
