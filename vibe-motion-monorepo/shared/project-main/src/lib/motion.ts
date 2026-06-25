import {interpolate, spring} from 'remotion';

export const clamp = (value: number, min = 0, max = 1) => Math.max(min, Math.min(max, value));

export const linear = (frame: number, start: number, end: number, from = 0, to = 1) => {
  return interpolate(frame, [start, end], [from, to], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
};

export const smooth = (frame: number, start: number, end: number, from = 0, to = 1) => {
  const value = linear(frame, start, end, 0, 1);
  const eased = value * value * (3 - 2 * value);
  return from + (to - from) * eased;
};

export const springScale = ({
  frame,
  fps,
  start,
  from,
  to,
  damping,
  mass,
}: {
  frame: number;
  fps: number;
  start: number;
  from: number;
  to: number;
  damping: number;
  mass: number;
}) => {
  const value = spring({
    frame: frame - start,
    fps,
    config: {
      damping,
      mass,
    },
  });

  return from + (to - from) * value;
};

export const opacityOut = (frame: number, start: number, end: number) => linear(frame, start, end, 1, 0);

