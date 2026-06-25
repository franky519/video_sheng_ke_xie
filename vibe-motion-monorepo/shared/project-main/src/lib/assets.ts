export type AssetStatus = 'AUTO' | 'DONE' | 'TODO: BROWSER' | 'TODO: STOCK' | 'TODO: AI_GEN' | 'TODO: HUMAN';

export type ProjectAsset = {
  id: string;
  description: string;
  category: 'GENERATE_BY_CODE' | 'AI_BROWSER_CAPTURE' | 'STOCK_LIBRARY' | 'AI_GENERATED' | 'HUMAN_CAPTURE';
  status: AssetStatus;
};

export const assets: ProjectAsset[] = [
  { id: 'ASSET_01_01', description: '豆包主页空闲态截图', category: 'AI_BROWSER_CAPTURE', status: 'DONE' },
  { id: 'ASSET_02_01', description: '豆包输入框打字状态截图', category: 'AI_BROWSER_CAPTURE', status: 'DONE' },
  { id: 'ASSET_02_02', description: '重疾险条文模拟页面截图', category: 'AI_BROWSER_CAPTURE', status: 'DONE' },
  { id: 'ASSET_02_03', description: '霓虹扫描线（代码渲染）', category: 'GENERATE_BY_CODE', status: 'AUTO' },
  { id: 'ASSET_03_01', description: '豆包快速模式对话气泡', category: 'GENERATE_BY_CODE', status: 'AUTO' },
  { id: 'ASSET_03_02', description: '红色"背书废话"图章', category: 'GENERATE_BY_CODE', status: 'AUTO' },
  { id: 'ASSET_04_01', description: '豆包专家模式设置页截图', category: 'AI_BROWSER_CAPTURE', status: 'DONE' },
  { id: 'ASSET_04_02', description: '绿色风险分析卡片（代码渲染）', category: 'GENERATE_BY_CODE', status: 'AUTO' },
  { id: 'ASSET_05_01', description: '条文放大框（代码渲染）', category: 'GENERATE_BY_CODE', status: 'AUTO' },
  { id: 'ASSET_05_02', description: '荧光笔高亮划线（代码渲染）', category: 'GENERATE_BY_CODE', status: 'AUTO' },
  { id: 'ASSET_05_03', description: '放大镜容器（代码渲染）', category: 'GENERATE_BY_CODE', status: 'AUTO' },
  { id: 'ASSET_06_01', description: '搜索结果页面截图', category: 'AI_BROWSER_CAPTURE', status: 'DONE' },
  { id: 'ASSET_06_02', description: '搜索框逐字打字（代码渲染）', category: 'GENERATE_BY_CODE', status: 'AUTO' },
  { id: 'ASSET_06_03', description: '发光问号图标（代码渲染）', category: 'GENERATE_BY_CODE', status: 'AUTO' },
  { id: 'ASSET_07_01', description: '初中生vs博士对比卡片（代码渲染）', category: 'GENERATE_BY_CODE', status: 'AUTO' },
  { id: 'ASSET_07_02', description: '铁栏闸门"上限焊死"（代码渲染）', category: 'GENERATE_BY_CODE', status: 'AUTO' },
  { id: 'ASSET_07_03', description: '电焊火花粒子（代码渲染）', category: 'GENERATE_BY_CODE', status: 'AUTO' },
  { id: 'ASSET_08_01', description: '挂锁图标（代码渲染）', category: 'GENERATE_BY_CODE', status: 'AUTO' },
  { id: 'ASSET_08_02', description: '红色覆层遮罩（代码渲染）', category: 'GENERATE_BY_CODE', status: 'AUTO' },
];

