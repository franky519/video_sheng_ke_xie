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

export const WindowContainer = ({children, style}: {children: ReactNode, style?: React.CSSProperties}) => {
  return (
    <div
      style={{
        position: 'absolute',
        left: '50%',
        top: '50%',
        transform: 'translate(-50%, -50%)',
        width: '1000px',
        height: '560px',
        backgroundColor: '#ffffff',
        borderRadius: '16px',
        border: '4px solid #000000',
        overflow: 'hidden',
        boxShadow: '0 24px 60px rgba(0, 0, 0, 0.4)',
        display: 'flex',
        flexDirection: 'column',
        ...style
      }}
    >
      {/* Top Bar */}
      <div
        style={{
          height: '42px',
          borderBottom: '4px solid #000000',
          backgroundColor: '#ffffff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 16px',
          userSelect: 'none',
        }}
      >
        <div style={{fontFamily: 'monospace', fontWeight: 'bold', fontSize: '15px', color: '#000000'}}>
          DOUBAO WORKFLOW
        </div>
        <div style={{display: 'flex', gap: '8px'}}>
          <div style={{width: '12px', height: '12px', borderRadius: '50%', border: '2px solid #000000', backgroundColor: '#00CA4E'}} />
          <div style={{width: '12px', height: '12px', borderRadius: '50%', border: '2px solid #000000', backgroundColor: '#FFBD44'}} />
          <div style={{width: '12px', height: '12px', borderRadius: '50%', border: '2px solid #000000', backgroundColor: '#FF605C'}} />
        </div>
      </div>
      {/* Content Area */}
      <div style={{flex: 1, position: 'relative', overflow: 'hidden', backgroundColor: '#ffffff'}}>
        {children}
      </div>
    </div>
  );
};

