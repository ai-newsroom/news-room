import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { readFile, readdir } from 'node:fs/promises';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const scriptDirectory = dirname(fileURLToPath(import.meta.url));
const repositoryRoot = resolve(scriptDirectory, '../..');
const siteRoot = join(repositoryRoot, 'site');
const distRoot = join(siteRoot, 'dist');
const decisionsRoot = join(repositoryRoot, 'decisions', 'ai');
const contentRoot = join(repositoryRoot, 'content', 'ai');

const releaseIds = (await readdir(decisionsRoot, { withFileTypes: true }))
  .filter((entry) => entry.isDirectory())
  .map((entry) => entry.name)
  .sort();
const approved = [];
function htmlText(value) {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function publicPath(id, kind) {
  if (kind === 'regular' || kind === undefined) return id;
  const [date, slug] = id.split('--', 2);
  assert.ok(date && slug, `invalid special id: ${id}`);
  return `${date}/${slug}`;
}

for (const id of releaseIds) {
  let release;
  try {
    release = JSON.parse(await readFile(join(decisionsRoot, id, 'release.json'), 'utf8'));
  } catch {
    continue;
  }
  if (release.release_status !== 'approved-for-publication') continue;
  assert.equal(release.publication_id, id);
  assert.ok(['human', 'automatic'].includes(release.authorization.mode));
  if (release.authorization.mode === 'automatic') {
    assert.equal(release.authorization.policy_id, 'ai-auto-publish-v1');
    assert.ok(release.authorization.checks.length >= 5);
    assert.equal(release.publication_kind ?? 'regular', 'regular');
  } else {
    assert.equal(release.authorization.approved, true);
    assert.ok(['regular', 'special'].includes(release.publication_kind ?? 'regular'));
  }
  const source = await readFile(join(contentRoot, id, 'article.md'), 'utf8');
  const titleLine = source.split('\n').find((line) => line.startsWith('title:'));
  assert.ok(titleLine, `missing title: ${id}`);
  approved.push({
    id,
    release,
    source,
    title: JSON.parse(titleLine.slice('title:'.length).trim()),
    publicPath: publicPath(id, release.publication_kind),
  });
}
assert.ok(approved.length >= 1);

const build = spawnSync('npm', ['run', 'build'], {
  cwd: siteRoot,
  encoding: 'utf8',
  env: { ...process.env, ASTRO_TELEMETRY_DISABLED: '1', NO_UPDATE_NOTIFIER: '1' },
});
assert.equal(build.status, 0, build.stdout + build.stderr);

const landing = await readFile(join(distRoot, 'ai', 'index.html'), 'utf8');
const legacyHome = await readFile(join(distRoot, 'index.html'), 'utf8');
for (const { id, publicPath: routePath, release, source, title } of approved) {
  const article = await readFile(join(distRoot, 'ai', routePath, 'index.html'), 'utf8');
  assert.ok(landing.includes(htmlText(title)));
  assert.ok(landing.includes(`href="/news-room/ai/${routePath}/"`));
  assert.ok(article.includes(htmlText(title)));
  for (const requiredAppendix of ['이해상충과 취재 조건', '근거 원장', '출처']) {
    assert.ok(article.includes(requiredAppendix), `missing ${requiredAppendix}: ${id}`);
  }
  assert.ok(article.includes(`발행 ID ${id}`));
  const label = release.authorization.mode === 'automatic'
    ? '자동 출고 검증 완료'
    : '사람 공개 승인 완료';
  assert.ok(article.includes(label));
  if (release.publication_kind === 'special') {
    assert.ok(article.includes('편집자 요청 특별판'));
    assert.ok(landing.includes('특별판'));
  }
  assert.equal(legacyHome.includes(title), false);
  assert.equal(source.includes('no-publish'), false);
}

const cosmos = approved.find(({ id }) => id === '2026-07-21');
assert.ok(cosmos);
const cosmosHtml = await readFile(join(distRoot, 'ai', cosmos.publicPath, 'index.html'), 'utf8');
for (const expected of [
  '0334b6f3da2b8519e9c832175c16fd46d32d6f2a',
  '앞선 토큰으로 다음 토큰을 예측하는 자동회귀 Reasoner',
  '확산(diffusion) Generator',
  '트랜스포머 혼합 구조(Mixture-of-Transformers, MoT)',
  'VANTAGE',
  '독립 재현',
]) assert.ok(cosmosHtml.includes(expected), `missing pinned Cosmos evidence: ${expected}`);

const contentIds = (await readdir(contentRoot, { withFileTypes: true }))
  .filter((entry) => entry.isDirectory())
  .map((entry) => entry.name);
const unapprovedTechnicalRoutes = contentIds.filter(
  (id) => !approved.some((publication) => publication.id === id),
).length;
assert.equal(unapprovedTechnicalRoutes, 0);

console.log(JSON.stringify({
  status: 'pass',
  approvedAiRoutes: ['/ai/', ...approved.map(({ id }) => `/ai/${id}/`)],
  authorizationModes: [...new Set(approved.map(({ release }) => release.authorization.mode))],
  unapprovedTechnicalRoutes,
  legacyHomeUnchangedByAiContent: true,
  sameDateLegacyRouteIsolated: true,
}));
