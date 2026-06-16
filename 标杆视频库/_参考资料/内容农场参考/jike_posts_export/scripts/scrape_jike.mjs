#!/usr/bin/env node

import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';

const USERNAME = '42951551-0D56-461E-B2F0-F5DDC1EABC1D';
const SCREEN_NAME = 'Danielw';
const PROFILE_URL = `https://web.okjike.com/u/${USERNAME}`;
const CDP_PORT = Number(process.env.CDP_PORT || 9223);
const OUT_DIR = path.resolve('jike_posts_export');
const IMAGES_DIR = path.join(OUT_DIR, 'images');
const RAW_DIR = path.join(OUT_DIR, 'raw');
const CUTOFF = new Date('2025-11-30T16:00:00.000Z'); // 2025-12-01 00:00 Asia/Shanghai
const API = 'https://api.ruguoapp.com/1.0/personalUpdate/single';
const REFRESH_API = 'https://api.ruguoapp.com/app_auth_tokens.refresh';

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function main() {
  await fs.mkdir(IMAGES_DIR, { recursive: true });
  await fs.mkdir(RAW_DIR, { recursive: true });

  const { token, pageWsUrl } = await getTokensFromBrowser();
  if (!token) throw new Error(`No JK_ACCESS_TOKEN found in Edge on CDP port ${CDP_PORT}`);

  const scrape = await fetchAllPosts({ pageWsUrl });
  const normalized = normalizePosts(scrape.posts);
  await fs.writeFile(path.join(RAW_DIR, 'posts_raw.json'), JSON.stringify(scrape.posts, null, 2));
  await fs.writeFile(path.join(RAW_DIR, 'posts_normalized.pre_images.json'), JSON.stringify(normalized, null, 2));

  await downloadImages(normalized);
  await fs.writeFile(path.join(RAW_DIR, 'posts_normalized.json'), JSON.stringify(normalized, null, 2));

  const postsMarkdown = renderPostsMarkdown(normalized, scrape);
  const judgmentsMarkdown = renderJudgmentsMarkdown(normalized, scrape);
  await fs.writeFile(path.join(OUT_DIR, 'posts_with_images.md'), postsMarkdown);
  await fs.writeFile(path.join(OUT_DIR, 'content_judgments.md'), judgmentsMarkdown);

  const stats = {
    generatedAt: new Date().toISOString(),
    profileUrl: PROFILE_URL,
    cutoff: CUTOFF.toISOString(),
    fetchedPages: scrape.pages,
    rawFetchedCount: scrape.rawFetchedCount,
    includedCount: normalized.length,
    earliestIncluded: normalized.at(-1)?.timeIso || null,
    latestIncluded: normalized[0]?.timeIso || null,
    imageCount: normalized.reduce((sum, post) => sum + post.images.length + post.targetImages.length, 0),
  };
  await fs.writeFile(path.join(OUT_DIR, 'scrape_stats.json'), JSON.stringify(stats, null, 2));
  console.log(JSON.stringify(stats, null, 2));
}

async function getTokensFromBrowser() {
  const targets = await fetch(`http://127.0.0.1:${CDP_PORT}/json/list`).then((r) => r.json());
  const page = targets.find((target) => target.type === 'page' && target.url.includes('web.okjike.com/u/'))
    || targets.find((target) => target.type === 'page' && target.url.includes('web.okjike.com'))
    || targets.find((target) => target.type === 'page');
  if (!page) throw new Error(`No page target found on CDP port ${CDP_PORT}`);

  const result = await cdpEvaluate(page.webSocketDebuggerUrl, `(() => ({
    token: localStorage.getItem('JK_ACCESS_TOKEN'),
    title: document.title,
    url: location.href
  }))()`);

  return { ...result, pageWsUrl: page.webSocketDebuggerUrl };
}

async function cdpEvaluate(wsUrl, expression) {
  const ws = new WebSocket(wsUrl);
  let id = 0;
  const pending = new Map();
  ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    if (message.id && pending.has(message.id)) {
      pending.get(message.id)(message);
      pending.delete(message.id);
    }
  };
  await new Promise((resolve, reject) => {
    ws.onopen = resolve;
    ws.onerror = reject;
  });
  const send = (method, params = {}) => {
    const messageId = ++id;
    ws.send(JSON.stringify({ id: messageId, method, params }));
    return new Promise((resolve) => pending.set(messageId, resolve));
  };
  await send('Runtime.enable');
  const response = await send('Runtime.evaluate', {
    expression,
    awaitPromise: true,
    returnByValue: true,
    timeout: 30_000,
  });
  ws.close();
  if (response.error) throw new Error(response.error.message);
  if (response.result?.exceptionDetails) {
    throw new Error(response.result.exceptionDetails.text || 'CDP evaluation failed');
  }
  return response.result.result.value;
}

async function fetchAllPosts(auth) {
  const posts = [];
  let loadMoreKey;
  let oldPages = 0;
  let pages = 0;
  let rawFetchedCount = 0;

  while (pages < 200) {
    const body = { limit: 20, username: USERNAME };
    if (loadMoreKey) body.loadMoreKey = loadMoreKey;

    const data = await browserPostJson(auth.pageWsUrl, API, body);

    if (!Array.isArray(data.data)) {
      throw new Error(`Unexpected API response: ${JSON.stringify(data).slice(0, 1000)}`);
    }

    pages += 1;
    rawFetchedCount += data.data.length;
    const included = data.data.filter((post) => postTime(post) >= CUTOFF);
    posts.push(...included);

    const pageMaxTime = data.data.reduce((max, post) => Math.max(max, postTime(post).getTime()), 0);
    if (pageMaxTime < CUTOFF.getTime()) oldPages += 1;
    else oldPages = 0;

    console.log(`page ${pages}: fetched=${data.data.length} included=${included.length} total=${posts.length} next=${JSON.stringify(data.loadMoreKey || null)}`);

    loadMoreKey = data.loadMoreKey;
    if (!loadMoreKey || data.data.length === 0) break;
    if (oldPages >= 2 && posts.length > 0) break;
    await sleep(350);
  }

  const unique = [];
  const seen = new Set();
  for (const post of posts) {
    if (seen.has(post.id)) continue;
    seen.add(post.id);
    unique.push(post);
  }
  unique.sort((a, b) => postTime(b) - postTime(a));
  return { posts: unique, pages, rawFetchedCount };
}

async function browserPostJson(wsUrl, url, body) {
  const expression = `fetch(${JSON.stringify(url)}, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'content-type': 'application/json',
      'x-jike-access-token': localStorage.getItem('JK_ACCESS_TOKEN')
    },
    body: ${JSON.stringify(JSON.stringify(body))}
  }).then(async (response) => ({ status: response.status, text: await response.text() }))`;
  const result = await cdpEvaluate(wsUrl, expression);
  let data;
  try {
    data = JSON.parse(result.text);
  } catch {
    throw new Error(`Non-JSON API response ${result.status}: ${String(result.text).slice(0, 1000)}`);
  }
  if ((data.code === 'E101' || result.status === 401) && localStorageRefreshPossible(data)) {
    throw new Error(`Access token expired and automatic refresh was not attempted: ${JSON.stringify(data).slice(0, 1000)}`);
  }
  return data;
}

function localStorageRefreshPossible() {
  return true;
}

function postTime(post) {
  return new Date(post.actionTime || post.createdAt || post.updatedAt || 0);
}

function normalizePosts(posts) {
  return posts.map((post, index) => {
    const target = post.target || null;
    const typeSlug = post.type === 'REPOST' ? 'repost' : 'post';
    const topic = post.topic?.content || target?.topic?.content || '';
    const images = extractPictureUrls(post.pictures);
    const targetImages = extractPictureUrls(target?.pictures);
    const text = post.rawContent || post.content || '';
    const targetText = target?.rawContent || target?.content || '';
    const time = postTime(post);
    return {
      index: index + 1,
      id: post.id,
      type: post.type,
      typeLabel: post.type === 'REPOST' ? '转发' : '原创',
      timeIso: time.toISOString(),
      timeLocal: formatChinaTime(time),
      link: `https://web.okjike.com/u/${USERNAME}/${typeSlug}/${post.id}`,
      topic,
      text,
      target: target ? {
        id: target.id,
        type: target.type,
        author: target.user?.screenName || '',
        username: target.user?.username || '',
        text: targetText,
        topic: target.topic?.content || '',
        link: target.user?.username ? `https://web.okjike.com/u/${target.user.username}/${target.type === 'REPOST' ? 'repost' : 'post'}/${target.id}` : '',
      } : null,
      counts: {
        like: post.likeCount ?? 0,
        comment: post.commentCount ?? 0,
        repost: post.repostCount ?? 0,
        share: post.shareCount ?? 0,
      },
      images,
      targetImages,
      urlsInText: post.urlsInText || [],
      raw: post,
    };
  });
}

function extractPictureUrls(pictures) {
  if (!Array.isArray(pictures)) return [];
  return pictures.map((picture, idx) => ({
    index: idx + 1,
    key: picture.key || '',
    url: picture.middlePicUrl || picture.picUrl || picture.smallPicUrl || picture.thumbnailUrl || '',
    sourceUrl: picture.picUrl || picture.middlePicUrl || picture.smallPicUrl || picture.thumbnailUrl || '',
    format: picture.format || inferExt(picture.key || picture.picUrl || picture.middlePicUrl || '') || 'jpg',
    width: picture.width || null,
    height: picture.height || null,
  })).filter((picture) => picture.url);
}

async function downloadImages(posts) {
  const jobs = [];
  for (const post of posts) {
    for (const image of post.images) {
      jobs.push({ post, image, scope: 'own' });
    }
    for (const image of post.targetImages) {
      jobs.push({ post, image, scope: 'target' });
    }
  }

  let done = 0;
  for (const job of jobs) {
    const ext = normalizeExt(job.image.format || inferExt(job.image.url));
    const filename = `${String(job.post.index).padStart(3, '0')}_${job.post.id}_${job.scope}_${job.image.index}.${ext}`;
    const filepath = path.join(IMAGES_DIR, filename);
    const rel = `images/${filename}`;
    job.image.localPath = rel;
    try {
      await downloadOne(job.image.url, filepath);
      done += 1;
      if (done % 20 === 0) console.log(`images: ${done}/${jobs.length}`);
    } catch (error) {
      job.image.downloadError = error.message;
      console.warn(`image failed: ${job.image.url} ${error.message}`);
    }
    await sleep(80);
  }
}

async function downloadOne(url, filepath) {
  try {
    await fs.access(filepath);
    return;
  } catch {}
  const response = await fetch(url, {
    headers: {
      'referer': 'https://web.okjike.com/',
      'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0',
    },
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const arrayBuffer = await response.arrayBuffer();
  await fs.writeFile(filepath, Buffer.from(arrayBuffer));
}

function renderPostsMarkdown(posts, scrape) {
  const lines = [];
  lines.push(`# ${SCREEN_NAME} 即刻动态图文汇编`);
  lines.push('');
  lines.push(`- 主页：${PROFILE_URL}`);
  lines.push(`- 范围：2025-12-01 至 2026-05-19（包含 12 月）`);
  lines.push(`- 生成时间：${formatChinaTime(new Date())}`);
  lines.push(`- 收录动态：${posts.length} 条`);
  lines.push(`- 图片：${posts.reduce((sum, post) => sum + post.images.length + post.targetImages.length, 0)} 张`);
  lines.push(`- 抓取页数：${scrape.pages} 页`);
  lines.push('');
  lines.push('## 目录');
  lines.push('');
  let currentMonth = '';
  for (const post of posts) {
    const month = post.timeLocal.slice(0, 7);
    if (month !== currentMonth) {
      currentMonth = month;
      lines.push(`### ${month}`);
    }
    const snippet = compact(post.text || post.target?.text || '', 42) || '(无正文)';
    lines.push(`- [${String(post.index).padStart(3, '0')}. ${post.timeLocal} · ${post.typeLabel} · ${escapeMd(snippet)}](#post-${post.index})`);
  }
  lines.push('');

  for (const post of posts) {
    lines.push(`## <a id="post-${post.index}"></a>${String(post.index).padStart(3, '0')}. ${post.timeLocal} · ${post.typeLabel}`);
    lines.push('');
    lines.push(`- 链接：${post.link}`);
    if (post.topic) lines.push(`- 圈子：${post.topic}`);
    lines.push(`- 互动：${post.counts.like} 赞 / ${post.counts.comment} 评论 / ${post.counts.repost} 转发 / ${post.counts.share} 分享`);
    lines.push('');
    if (post.type === 'REPOST') {
      lines.push('**转发评论**');
      lines.push('');
      lines.push(post.text ? blockText(post.text) : '_无转发评论_');
      lines.push('');
      if (post.images.length > 0) {
        lines.push('**转发附图**');
        lines.push('');
        appendImages(lines, post.images);
      }
      if (post.target) {
        lines.push('**被转发内容**');
        lines.push('');
        lines.push(`- 作者：${post.target.author || '未知'}`);
        if (post.target.topic) lines.push(`- 圈子：${post.target.topic}`);
        if (post.target.link) lines.push(`- 链接：${post.target.link}`);
        lines.push('');
        lines.push(post.target.text ? blockText(post.target.text) : '_无正文_');
        lines.push('');
        if (post.targetImages.length > 0) {
          lines.push('**被转发内容图片**');
          lines.push('');
          appendImages(lines, post.targetImages);
        }
      }
    } else {
      lines.push('**正文**');
      lines.push('');
      lines.push(post.text ? blockText(post.text) : '_无正文_');
      lines.push('');
      if (post.images.length > 0) {
        lines.push('**图片**');
        lines.push('');
        appendImages(lines, post.images);
      }
    }
    if (post.urlsInText.length > 0) {
      lines.push('**正文链接**');
      lines.push('');
      for (const url of post.urlsInText) lines.push(`- ${typeof url === 'string' ? url : url.url || JSON.stringify(url)}`);
      lines.push('');
    }
    lines.push('---');
    lines.push('');
  }
  return lines.join('\n');
}

function renderJudgmentsMarkdown(posts, scrape) {
  const candidates = contentFarmCandidates(posts);
  const lines = [];
  lines.push(`# ${SCREEN_NAME} 内容农场相关原文摘录`);
  lines.push('');
  lines.push(`- 来源：${PROFILE_URL}`);
  lines.push(`- 范围：2025-12-01 至 2026-05-19`);
  lines.push(`- 收录：${candidates.length} 条相关动态`);
  lines.push(`- 口径：只展示 Danielw 本人的正文或转发评论；不展示圈子、互动数据、被转发原文。`);
  lines.push('');
  lines.push('## 目录');
  lines.push('');
  let currentMonth = '';
  for (const post of candidates) {
    const month = post.timeLocal.slice(0, 7);
    if (month !== currentMonth) {
      currentMonth = month;
      lines.push(`### ${month}`);
    }
    const snippet = compact(post.text, 42) || '(无正文)';
    lines.push(`- [${String(post.index).padStart(3, '0')}. ${post.timeLocal} · ${post.typeLabel} · ${escapeMd(snippet)}](#post-${post.index})`);
  }
  lines.push('');

  for (const post of candidates) {
    lines.push(`## <a id="post-${post.index}"></a>${String(post.index).padStart(3, '0')}. ${post.timeLocal} · ${post.typeLabel}`);
    lines.push('');
    lines.push(`- 链接：${post.link}`);
    lines.push('');
    lines.push(blockText(post.text || '_无正文_'));
    lines.push('');
    if (post.images.length > 0) {
      appendImages(lines, post.images);
    }
    lines.push('---');
    lines.push('');
  }

  return lines.join('\n');
}

function contentFarmCandidates(posts) {
  const keyword = /(内容农场|农场内容|内容行业|内容领域|内容形式|视频agent|视频 agent|AI生成视频|AI采访|AI新闻|AI内容|素材生成|素材嗅探|真人素材|钩子变体|视频素材|分镜|画布|模板|流量|曝光量|默认给的曝光量|投流|广告流量|平台|推荐算法|算法驱动|包装|缩略图|标题|RPCH|真人秀|短视频|15秒视频|博主视频|视频播客|KOL|AI KOL|达人|IP|社交货币|谷贱伤农|布伦屋|院线|网剧|剪映|anygen|Manus)/i;
  return posts.filter((post) => post.text && keyword.test(post.text));
}

function appendImages(lines, images) {
  for (const image of images) {
    if (image.localPath && !image.downloadError) {
      lines.push(`![图片 ${image.index}](${image.localPath})`);
      lines.push('');
    } else {
      lines.push(`- 图片 ${image.index} 下载失败：${image.url}`);
    }
  }
}

function blockText(text) {
  return String(text).trim().replace(/\n{3,}/g, '\n\n');
}

function compact(text, length) {
  const normalized = String(text || '').replace(/\s+/g, ' ').trim();
  return normalized.length > length ? `${normalized.slice(0, length - 1)}...` : normalized;
}

function quoteInline(text) {
  return `“${String(text).replace(/\s+/g, ' ').trim()}”`;
}

function escapeMd(text) {
  return String(text).replace(/([\\[\\]])/g, '\\$1');
}

function formatChinaTime(date) {
  const parts = new Intl.DateTimeFormat('sv-SE', {
    timeZone: 'Asia/Shanghai',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).formatToParts(date).reduce((acc, part) => {
    acc[part.type] = part.value;
    return acc;
  }, {});
  return `${parts.year}-${parts.month}-${parts.day} ${parts.hour}:${parts.minute}`;
}

function inferExt(value) {
  const match = String(value || '').match(/\\.([a-zA-Z0-9]{2,5})(?:\\?|$)/);
  return match?.[1]?.toLowerCase() || '';
}

function normalizeExt(ext) {
  const clean = String(ext || 'jpg').toLowerCase().replace(/[^a-z0-9]/g, '');
  if (clean === 'jpeg') return 'jpg';
  if (['jpg', 'png', 'webp', 'gif', 'heic'].includes(clean)) return clean;
  return 'jpg';
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
