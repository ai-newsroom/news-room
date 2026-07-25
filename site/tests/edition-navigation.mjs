import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { readFile, readdir } from 'node:fs/promises';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const scriptDirectory = dirname(fileURLToPath(import.meta.url));
const repositoryRoot = resolve(scriptDirectory, '../..');
const siteRoot = join(repositoryRoot, 'site');
const distRoot = join(siteRoot, 'dist');

const build = spawnSync('npm', ['run', 'build'], {
  cwd: siteRoot,
  encoding: 'utf8',
  env: { ...process.env, ASTRO_TELEMETRY_DISABLED: '1', NO_UPDATE_NOTIFIER: '1' },
});
assert.equal(build.status, 0, build.stdout + build.stderr);

const pages = {
  current: await readFile(join(distRoot, 'index.html'), 'utf8'),
  currentArticle: await readFile(join(distRoot, 'news', '2026-07-21', 'index.html'), 'utf8'),
  newsroom: await readFile(join(distRoot, 'newsroom', 'index.html'), 'utf8'),
  ai: await readFile(join(distRoot, 'ai', 'index.html'), 'utf8'),
  aiArticle: await readFile(join(distRoot, 'ai', '2026-07-21', 'index.html'), 'utf8'),
};
const distEntries = await readdir(distRoot);
assert.equal(distEntries.includes('eda'), false, 'EDA must not have a public route');

const editionLinks = [
  'href="/news-room"',
  'href="/news-room/ai/"',
];

for (const [name, html] of Object.entries(pages)) {
  assert.ok(html.includes('aria-label="뉴스룸 판 선택"'), `${name}: edition switcher missing`);
  for (const href of editionLinks) {
    assert.ok(html.includes(href), `${name}: edition link missing: ${href}`);
  }
  assert.match(html, />\s*시사판\s*<\/a>/, `${name}: current-affairs label missing`);
  assert.match(html, />\s*AI판\s*<\/a>/, `${name}: AI label missing`);
  assert.equal(
    (html.match(/aria-current="page"/g) ?? []).length,
    1,
    `${name}: exactly one edition must be current`,
  );
}

assert.ok(pages.current.includes('<h1 id="edition-title">시사 뉴스</h1>'));
assert.ok(pages.current.includes('편집 강령과 제작 과정 보기'));
assert.match(pages.newsroom, /<h1[^>]*>시사판 편집국<\/h1>/);
assert.ok(pages.newsroom.includes('이 편집국 계약은 시사판에만 적용됩니다'));
assert.equal(pages.newsroom.includes('EDA판'), false);

assert.ok(pages.ai.includes('<h1 id="edition-title">AI 뉴스</h1>'));
assert.ok(pages.ai.includes('근거 수준 E2'));
assert.equal(pages.ai.includes('aria-label="AI News 이동"'), false);
assert.equal(pages.ai.includes('매일의 토론 전문'), false);
assert.ok(pages.aiArticle.includes('aria-label="기사 공개 및 검증 정보"'));

console.log(JSON.stringify({
  status: 'pass',
  editionRoutes: ['/', '/ai/'],
  sharedNavigationPages: Object.keys(pages).length,
  legacyArticleRoutePreserved: true,
  aiEditorialScopeIsolated: true,
}));
