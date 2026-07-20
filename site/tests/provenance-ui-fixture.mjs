import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import {
  cp,
  lstat,
  mkdir,
  mkdtemp,
  readFile,
  readdir,
  readlink,
  rm,
  symlink,
  writeFile,
} from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { dirname, join, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const scriptDirectory = dirname(fileURLToPath(import.meta.url));
const repositoryRoot = resolve(scriptDirectory, '../..');
const productionSite = join(repositoryRoot, 'site');
const productionContent = join(repositoryRoot, 'content');
const productionNewsroom = join(repositoryRoot, 'newsroom');
const provenanceId = '2099-01-01-provenance-fixture';
const legacyId = '2099-01-02-legacy-fixture';

const sentinels = {
  draft: 'DRAFT_PROVENANCE_SENTINEL_7d9f',
  prompt: 'PROMPT_PROVENANCE_SENTINEL_8a3c',
  run: 'RUN_PROVENANCE_SENTINEL_4e2b',
};

const articleWithProvenance = `---
title: "provenance fixture article"
date: 2099-01-01
topic: "isolated provenance rendering fixture"
summary: "세 provenance artifact의 route 격리와 HTML escaping을 검증한다."
---

세 provenance 파일이 있는 격리 기사다.
`;

const articleWithoutProvenance = `---
title: "legacy fixture article"
date: 2099-01-02
topic: "legacy article without provenance"
summary: "provenance 파일이 없는 기존 기사 호환성을 검증한다."
---

provenance 파일이 없는 기존 형식 기사다.
`;

const artifacts = {
  'draft.md': `${sentinels.draft}
AT&T <draft-special>
<script data-provenance-fixture="draft">globalThis.DRAFT_FIXTURE_EXECUTED = true;</script>
`,
  'prompt.md': `${sentinels.prompt}
</pre><script data-provenance-fixture="prompt">globalThis.PROMPT_FIXTURE_EXECUTED = true;</script><pre>
<button onclick="globalThis.PROMPT_BUTTON_EXECUTED = true">do not execute</button>
`,
  'run.md': `${sentinels.run}
<img data-provenance-fixture="run" src=x onerror="globalThis.RUN_FIXTURE_EXECUTED = true">
<a href="javascript:globalThis.RUN_LINK_EXECUTED=true">do not execute</a>
`,
};

function sha256(value) {
  return createHash('sha256').update(value).digest('hex');
}

async function snapshotFiles(root) {
  const result = {};

  async function visit(directory) {
    const entries = await readdir(directory, { withFileTypes: true });
    entries.sort((left, right) => left.name.localeCompare(right.name));
    for (const entry of entries) {
      const path = join(directory, entry.name);
      const key = relative(root, path).split(sep).join('/');
      const metadata = await lstat(path);
      if (entry.isDirectory()) {
        result[key] = {
          kind: 'directory',
          mode: metadata.mode,
          size: metadata.size,
          mtimeMs: metadata.mtimeMs,
        };
        await visit(path);
      } else if (entry.isSymbolicLink()) {
        result[key] = {
          kind: 'symlink',
          targetHash: sha256(await readlink(path)),
          mode: metadata.mode,
          size: metadata.size,
          mtimeMs: metadata.mtimeMs,
        };
      } else {
        result[key] = {
          kind: 'file',
          sha256: sha256(await readFile(path)),
          mode: metadata.mode,
          size: metadata.size,
          mtimeMs: metadata.mtimeMs,
        };
      }
    }
  }

  await visit(root);
  return result;
}

async function copySite(source, destination) {
  const excluded = ['node_modules', 'dist', '.astro'].map((name) => join(source, name));
  await cp(source, destination, {
    recursive: true,
    filter(path) {
      return !excluded.some(
        (excludedPath) => path === excludedPath || path.startsWith(`${excludedPath}${sep}`),
      );
    },
  });
}

async function linkDependencies(source, destination) {
  await mkdir(destination, { recursive: true });
  const entries = await readdir(source, { withFileTypes: true });
  for (const entry of entries) {
    if (entry.name === '.vite' || entry.name === '.astro') continue;
    await symlink(
      join(source, entry.name),
      join(destination, entry.name),
      entry.isDirectory() ? 'dir' : 'file',
    );
  }
}

async function copyNewsroomInputs(destination) {
  await mkdir(destination, { recursive: true });
  for (const filename of ['charter.md', 'CLAUDE.md', 'sources.md']) {
    await cp(join(productionNewsroom, filename), join(destination, filename));
  }
  await cp(join(productionNewsroom, 'personas'), join(destination, 'personas'), {
    recursive: true,
  });
}

async function writeFixtureContent(contentRoot) {
  const provenanceDirectory = join(contentRoot, provenanceId);
  const legacyDirectory = join(contentRoot, legacyId);
  await mkdir(provenanceDirectory, { recursive: true });
  await mkdir(legacyDirectory, { recursive: true });
  await writeFile(join(provenanceDirectory, 'article.md'), articleWithProvenance, 'utf8');
  await writeFile(join(legacyDirectory, 'article.md'), articleWithoutProvenance, 'utf8');
  for (const [filename, content] of Object.entries(artifacts)) {
    await writeFile(join(provenanceDirectory, filename), content, 'utf8');
  }
}

function occurrences(haystack, needle) {
  return haystack.split(needle).length - 1;
}

function tagOccurrences(html, tagName) {
  return [...html.matchAll(new RegExp(`<${tagName}(?:\\s|>)`, 'g'))].length;
}

function assertNoExecutableFixtureMarkup(html) {
  const executableFragments = [
    '<script data-provenance-fixture=',
    '</pre><script data-provenance-fixture=',
    '<button onclick=',
    '<img data-provenance-fixture=',
    '<a href="javascript:',
  ];
  for (const fragment of executableFragments) {
    assert.equal(html.includes(fragment), false, `executable markup leaked: ${fragment}`);
  }
}

async function run() {
  const productionBefore = await snapshotFiles(productionContent);
  for (const id of [provenanceId, legacyId]) {
    assert.equal(
      Object.keys(productionBefore).some((path) => path.startsWith(`${id}/`)),
      false,
      `fixture id already exists in production content: ${id}`,
    );
  }

  const temporaryRoot = await mkdtemp(join(tmpdir(), 'news-room-provenance-ui-'));
  const isolatedRepository = join(temporaryRoot, 'news-room');
  const isolatedSite = join(isolatedRepository, 'site');
  const isolatedContent = join(isolatedRepository, 'content');

  try {
    await mkdir(isolatedRepository, { recursive: true });
    await copySite(productionSite, isolatedSite);
    await copyNewsroomInputs(join(isolatedRepository, 'newsroom'));
    await linkDependencies(
      join(productionSite, 'node_modules'),
      join(isolatedSite, 'node_modules'),
    );
    await writeFixtureContent(isolatedContent);

    const build = spawnSync('npm', ['run', 'build'], {
      cwd: isolatedSite,
      encoding: 'utf8',
      env: {
        ...process.env,
        ASTRO_TELEMETRY_DISABLED: '1',
        NO_UPDATE_NOTIFIER: '1',
      },
    });
    assert.equal(
      build.status,
      0,
      `isolated Astro build failed\nstdout:\n${build.stdout}\nstderr:\n${build.stderr}`,
    );

    const provenanceHtml = await readFile(
      join(isolatedSite, 'dist', 'news', provenanceId, 'index.html'),
      'utf8',
    );
    const legacyHtml = await readFile(
      join(isolatedSite, 'dist', 'news', legacyId, 'index.html'),
      'utf8',
    );
    const indexHtml = await readFile(join(isolatedSite, 'dist', 'index.html'), 'utf8');

    for (const label of [
      '기사 초고 보기',
      '발행 세션 프롬프트 보기',
      '사용 모델 및 실행 정보 보기',
    ]) {
      assert.equal(occurrences(provenanceHtml, label), 1, `missing provenance label: ${label}`);
      assert.equal(legacyHtml.includes(label), false, `empty legacy details rendered: ${label}`);
    }
    assert.equal(tagOccurrences(provenanceHtml, 'details'), 3);
    assert.equal(occurrences(provenanceHtml, 'class="artifact"'), 3);
    assert.equal(tagOccurrences(legacyHtml, 'details'), 0, 'legacy article rendered empty details');

    for (const sentinel of Object.values(sentinels)) {
      assert.equal(occurrences(provenanceHtml, sentinel), 1, `sentinel missing: ${sentinel}`);
      assert.equal(legacyHtml.includes(sentinel), false, `sentinel leaked to legacy route: ${sentinel}`);
      assert.equal(indexHtml.includes(sentinel), false, `sentinel leaked to index route: ${sentinel}`);
    }

    assertNoExecutableFixtureMarkup(provenanceHtml);
    assert.ok(provenanceHtml.includes('AT&amp;T &lt;draft-special&gt;'));
    assert.ok(provenanceHtml.includes('&lt;script data-provenance-fixture='));
    assert.ok(provenanceHtml.includes('&lt;/pre&gt;&lt;script data-provenance-fixture='));
    assert.ok(provenanceHtml.includes('&lt;button onclick='));
    assert.ok(provenanceHtml.includes('&lt;img data-provenance-fixture='));
    assert.match(provenanceHtml, /&lt;a href=(?:&quot;|")javascript:/);
  } finally {
    await rm(temporaryRoot, { recursive: true, force: true });
  }

  const productionAfter = await snapshotFiles(productionContent);
  assert.deepEqual(productionAfter, productionBefore, 'production content changed during fixture build');
  console.log(
    JSON.stringify({
      status: 'pass',
      fixtureArticles: 2,
      provenanceDetails: 3,
      isolatedSentinels: Object.keys(sentinels).length,
      productionContentUnchanged: true,
      temporaryFixtureRemoved: true,
    }),
  );
}

await run();
