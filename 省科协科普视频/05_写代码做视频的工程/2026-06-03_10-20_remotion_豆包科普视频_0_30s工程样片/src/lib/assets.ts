export type AssetStatus = 'AUTO' | 'TODO: HUMAN' | 'TODO: STOCK';

export type ProjectAsset = {
  id: string;
  description: string;
  status: AssetStatus;
  fallback: string;
};

export const assets: ProjectAsset[] = [
  {
    id: 'ASSET_01_01',
    description: '扁平化 iPhone 手机边框外壳',
    status: 'TODO: STOCK',
    fallback: 'CSS phone shell',
  },
  {
    id: 'ASSET_01_02',
    description: '豆包聊天窗口截图：普通长文本长句',
    status: 'TODO: HUMAN',
    fallback: 'CSS plain chat',
  },
  {
    id: 'ASSET_01_03',
    description: '豆包聊天窗口截图：专家式高质量回复',
    status: 'TODO: HUMAN',
    fallback: 'CSS expert chat',
  },
  {
    id: 'ASSET_04_03',
    description: '3D 红色发光立体问号图标',
    status: 'TODO: STOCK',
    fallback: 'CSS 3D question mark',
  },
];

