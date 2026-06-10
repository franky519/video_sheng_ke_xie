export const FPS = 24;
export const WIDTH = 1280;
export const HEIGHT = 720;
export const DURATION_IN_FRAMES = FPS * 30;

export const secondsToFrames = (seconds: number) => Math.round(seconds * FPS);

export const ranges = {
  intro: {
    start: secondsToFrames(0),
    end: secondsToFrames(5),
  },
  plainAnswer: {
    start: secondsToFrames(5),
    end: secondsToFrames(15),
  },
  expertAnswer: {
    start: secondsToFrames(15),
    end: secondsToFrames(25),
  },
  promptQuestion: {
    start: secondsToFrames(25),
    end: secondsToFrames(30),
  },
} as const;

export const subtitles = [
  {
    start: 0,
    end: 5,
    text: '同样问豆包，为什么他的答案像专家，你的答案像复制粘贴？',
  },
  {
    start: 5,
    end: 15,
    text: '比如你们同时问：“帮我看看这份保险条款有哪些坑。”你的豆包说，本产品保障多少种重大疾病，等待期多少天，赔付比例是多少。听完像没听。',
  },
  {
    start: 15,
    end: 25,
    text: '但你朋友的豆包会直接告诉你，哪条免责条款容易漏看，哪个赔付条件看着差不多其实完全不同，甚至能提醒你去看附录里的那几行小字。',
  },
  {
    start: 25,
    end: 30,
    text: '这时候很多人第一反应是：是不是我不会提问？是不是他的提示词写得更好？',
  },
] as const;

