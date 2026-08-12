import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { readFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const siteRoot = join(dirname(fileURLToPath(import.meta.url)), '..');
const distRoot = join(siteRoot, 'dist');
const origin = 'https://ai-newsroom.github.io';
const basePath = '/news-room';

const build = spawnSync('npm', ['run', 'build'], {
  cwd: siteRoot,
  encoding: 'utf8',
});

assert.equal(build.status, 0, `site build failed:\n${build.stdout}\n${build.stderr}`);

const pages = [
  {
    name: 'current-affairs index',
    file: 'index.html',
    url: `${origin}${basePath}/`,
    type: 'website',
    image: 'current-affairs.png',
  },
  {
    name: 'current-affairs article',
    file: 'news/2026-07-21/index.html',
    url: `${origin}${basePath}/news/2026-07-21/`,
    type: 'article',
    image: 'current-affairs.png',
  },
  {
    name: 'AI index',
    file: 'ai/index.html',
    url: `${origin}${basePath}/ai/`,
    type: 'website',
    image: 'ai.png',
  },
  {
    name: 'AI article',
    file: 'ai/2026-07-21/index.html',
    url: `${origin}${basePath}/ai/2026-07-21/`,
    type: 'article',
    image: 'ai.png',
  },
  {
    name: 'EDA index',
    file: 'eda/index.html',
    url: `${origin}${basePath}/eda/`,
    type: 'website',
    image: 'eda.png',
  },
  {
    name: 'EDA article',
    file: 'eda/2026-08-13/index.html',
    url: `${origin}${basePath}/eda/2026-08-13/`,
    type: 'article',
    image: 'eda.png',
  },
];

for (const page of pages) {
  const html = await readFile(join(distRoot, page.file), 'utf8');
  const imageUrl = `${origin}${basePath}/social/${page.image}`;

  assert.match(html, /<meta name="description" content="[^"]+">/, `${page.name} needs a description`);
  assert.ok(html.includes(`<link rel="canonical" href="${page.url}">`), `${page.name} canonical URL is missing`);
  assert.ok(html.includes(`<meta property="og:type" content="${page.type}">`), `${page.name} OG type is incorrect`);
  assert.match(html, /<meta property="og:title" content="[^"]+">/, `${page.name} OG title is missing`);
  assert.match(html, /<meta property="og:description" content="[^"]+">/, `${page.name} OG description is missing`);
  assert.ok(html.includes(`<meta property="og:url" content="${page.url}">`), `${page.name} OG URL is missing`);
  assert.ok(html.includes(`<meta property="og:image" content="${imageUrl}">`), `${page.name} OG image is missing`);
  assert.ok(html.includes('<meta property="og:image:width" content="1200">'), `${page.name} OG image width is missing`);
  assert.ok(html.includes('<meta property="og:image:height" content="630">'), `${page.name} OG image height is missing`);
  assert.ok(html.includes('<meta name="twitter:card" content="summary_large_image">'), `${page.name} X card type is missing`);
  assert.ok(html.includes(`<meta name="twitter:image" content="${imageUrl}">`), `${page.name} X image is missing`);
}

for (const image of ['current-affairs.png', 'ai.png', 'eda.png']) {
  const png = await readFile(join(distRoot, 'social', image));
  assert.equal(png.toString('ascii', 1, 4), 'PNG', `${image} is not a PNG`);
  assert.equal(png.readUInt32BE(16), 1200, `${image} width must be 1200px`);
  assert.equal(png.readUInt32BE(20), 630, `${image} height must be 630px`);
}

console.log('social card metadata and images: ok');
