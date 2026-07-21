import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { readFile, readdir } from 'node:fs/promises';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const scriptDirectory = dirname(fileURLToPath(import.meta.url));
const repositoryRoot = resolve(scriptDirectory, '../..');
const siteRoot = join(repositoryRoot, 'site');
const distRoot = join(siteRoot, 'dist');
const publicationId = '2026-07-21';
const articleTitle = 'NVIDIA Cosmos 3 Edge 4B 공개: 엣지 실행은 확인됐지만 성능 우월성은 아직 벤더 측정이다';

const build = spawnSync('npm', ['run', 'build'], {
  cwd: siteRoot,
  encoding: 'utf8',
  env: { ...process.env, ASTRO_TELEMETRY_DISABLED: '1', NO_UPDATE_NOTIFIER: '1' },
});
assert.equal(build.status, 0, build.stdout + build.stderr);

const aiRootEntries = (await readdir(join(distRoot, 'ai'), { withFileTypes: true }))
  .map((entry) => entry.name)
  .sort();
assert.deepEqual(aiRootEntries, [publicationId, 'index.html']);

const landing = await readFile(join(distRoot, 'ai', 'index.html'), 'utf8');
const article = await readFile(join(distRoot, 'ai', publicationId, 'index.html'), 'utf8');
const legacyHome = await readFile(join(distRoot, 'index.html'), 'utf8');
const legacySameDate = await readFile(join(distRoot, 'news', publicationId, 'index.html'), 'utf8');

assert.ok(landing.includes(articleTitle));
assert.ok(landing.includes(`href="/news-room/ai/${publicationId}/"`));
assert.equal((landing.match(new RegExp(articleTitle, 'g')) ?? []).length, 1);

for (const expected of [
  articleTitle,
  '0334b6f3da2b8519e9c832175c16fd46d32d6f2a',
  'VANTAGE',
  '독립 재현',
  '이해상충과 취재 조건',
  'NVIDIA는 모델·GPU·runtime을 공급하면서',
  '공개 승인 완료',
]) assert.ok(article.includes(expected), `missing AI article evidence: ${expected}`);

assert.equal(legacyHome.includes(articleTitle), false);
assert.equal(legacyHome.includes(`/ai/${publicationId}/`), false);
assert.equal(legacySameDate.includes(articleTitle), false);
assert.equal(article.includes('/news/2026-07-21/'), false);
assert.equal(article.includes('no-publish'), false);

console.log(JSON.stringify({
  status: 'pass',
  approvedAiRoutes: ['/ai/', `/ai/${publicationId}/`],
  unapprovedTechnicalRoutes: 0,
  legacyHomeUnchangedByAiContent: true,
  sameDateLegacyRouteIsolated: true,
}));
