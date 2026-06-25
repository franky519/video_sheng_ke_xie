export const FPS = 24;
export const WIDTH = 1280;
export const HEIGHT = 720;
export const DURATION_IN_FRAMES = FPS * 36; // 36 秒视频

export const secondsToFrames = (seconds: number) => Math.round(seconds * FPS);

export const ranges = {
  intro: {
    start: secondsToFrames(0),
    end: secondsToFrames(2),
  },
  plainAnswer: {
    start: secondsToFrames(2),
    end: secondsToFrames(12),
  },
  expertAnswer: {
    start: secondsToFrames(12),
    end: secondsToFrames(22),
  },
  promptQuestion: {
    start: secondsToFrames(22),
    end: secondsToFrames(36),
  },
} as const;

export const subtitles = [
  {
    start: 0,
    end: 2,
    text: '你有没有经历过这种诡异的事——',
  },
  {
    start: 2,
    end: 7,
    text: '同样是把一份厚厚的重疾险条款拍照发给豆包，问它“这保险有没有坑”。',
  },
  {
    start: 7,
    end: 12,
    text: '你的豆包回了一堆“本产品保障多少种疾病、等待期多少天”的背书废话，听完跟没听一样。',
  },
  {
    start: 12,
    end: 17,
    text: '但你朋友的豆包，却能逐条列出三个隐藏极深的免责陷阱，',
  },
  {
    start: 17,
    end: 22,
    text: '甚至连附录小字里的除外条款都给你标注得一清二楚。',
  },
  {
    start: 22,
    end: 26,
    text: '这时候你肯定会去搜“豆包提问技巧”、“怎么写好提示词”，觉得是自己的问法有问题。',
  },
  {
    start: 26,
    end: 32,
    text: '提问方式确实有影响，但它的上限是焊死的。把同一道分析题交给初中生和博士，题目写得再清晰，初中生也答不出博士的水平。',
  },
  {
    start: 32,
    end: 36,
    text: '模型的能力上限摆在那，再好的提问技巧也突破不了。',
  },
] as const;


