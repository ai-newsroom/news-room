import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { readFile, readdir } from 'node:fs/promises';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const scriptDirectory = dirname(fileURLToPath(import.meta.url));
const repositoryRoot = resolve(scriptDirectory, '../..');
const siteRoot = join(repositoryRoot, 'site');
const distRoot = join(siteRoot, 'dist');
const decisionsRoot = join(repositoryRoot, 'decisions', 'eda');
const contentRoot = join(repositoryRoot, 'content', 'eda');

const releaseIds = (await readdir(decisionsRoot, { withFileTypes: true }))
  .filter((entry) => entry.isDirectory())
  .map((entry) => entry.name)
  .sort();
const approved = [];
for (const id of releaseIds) {
  let release;
  try {
    release = JSON.parse(await readFile(join(decisionsRoot, id, 'release.json'), 'utf8'));
  } catch {
    continue;
  }
  if (release.release_status !== 'approved-for-publication') continue;
  assert.equal(release.publication_id, id);
  assert.equal(release.authorization.mode, 'human');
  assert.equal(release.authorization.approved, true);
  assert.ok(release.authorization.scope.length >= 1);
  const source = await readFile(join(contentRoot, id, 'article.md'), 'utf8');
  const titleLine = source.split('\n').find((line) => line.startsWith('title:'));
  assert.ok(titleLine, `missing title: ${id}`);
  approved.push({
    id,
    source,
    title: JSON.parse(titleLine.slice('title:'.length).trim()),
  });
}
assert.ok(approved.length >= 1);

const build = spawnSync('npm', ['run', 'build'], {
  cwd: siteRoot,
  encoding: 'utf8',
  env: { ...process.env, ASTRO_TELEMETRY_DISABLED: '1', NO_UPDATE_NOTIFIER: '1' },
});
assert.equal(build.status, 0, build.stdout + build.stderr);

const edaRootEntries = (await readdir(join(distRoot, 'eda'), { withFileTypes: true }))
  .map((entry) => entry.name)
  .sort();
assert.deepEqual(edaRootEntries, [...approved.map(({ id }) => id), 'index.html'].sort());

const landing = await readFile(join(distRoot, 'eda', 'index.html'), 'utf8');
const legacyHome = await readFile(join(distRoot, 'index.html'), 'utf8');
for (const { id, source, title } of approved) {
  const article = await readFile(join(distRoot, 'eda', id, 'index.html'), 'utf8');
  assert.ok(landing.includes(title));
  assert.ok(landing.includes(`href="/news-room/eda/${id}/"`));
  assert.ok(article.includes(title));
  assert.ok(article.includes('EDA 엔지니어를 위한 판단'));
  assert.ok(article.includes('확인된 것과 확인되지 않은 것'));
  assert.ok(article.includes('이 공개의 의의와 편집 판단'));
  assert.ok(article.includes('편집 판단:'));
  assert.ok(article.includes('이해상충과 취재 조건'));
  assert.ok(article.includes(`발행 ID ${id}`));
  assert.ok(article.includes('사람 공개 승인 완료'));
  assert.equal(legacyHome.includes(title), false);
  assert.equal(source.includes('no-publish'), false);
}

const contentIds = (await readdir(contentRoot, { withFileTypes: true }))
  .filter((entry) => entry.isDirectory())
  .map((entry) => entry.name);
const unapprovedTechnicalRoutes = contentIds.filter(
  (id) => !approved.some((publication) => publication.id === id),
).length;
assert.equal(unapprovedTechnicalRoutes, 0);

console.log(JSON.stringify({
  status: 'pass',
  approvedEdaRoutes: ['/eda/', ...approved.map(({ id }) => `/eda/${id}/`)],
  authorizationModes: ['human'],
  unapprovedTechnicalRoutes,
  legacyHomeUnchangedByEdaContent: true,
}));
