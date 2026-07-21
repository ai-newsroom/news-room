import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { getCollection } from 'astro:content';

const repositoryRoot = fileURLToPath(new URL('../../../', import.meta.url));

function publicationId(id: string) {
  return id.split('/')[0];
}

async function readRepositoryFile(path: string) {
  const url = new URL(path, `file://${repositoryRoot}/`);
  if (!fileURLToPath(url).startsWith(`${repositoryRoot}/`)) {
    throw new Error(`AI release path escapes repository: ${path}`);
  }
  return readFile(url);
}

function sha256(value: Uint8Array) {
  return createHash('sha256').update(value).digest('hex');
}

export async function getApprovedAiPublications() {
  const articles = await getCollection('aiArticles');
  const releases = await getCollection('aiReleases');
  const articlesById = new Map(articles.map((article) => [publicationId(article.id), article]));
  const seen = new Set<string>();
  const approved = [];

  for (const release of releases) {
    if (
      release.data.release_status !== 'approved-for-publication'
      || release.data.human_approval.approved !== true
    ) continue;

    const id = release.data.publication_id;
    if (publicationId(release.id) !== id || seen.has(id)) {
      throw new Error(`duplicate or mismatched AI release id: ${id}`);
    }
    seen.add(id);

    const article = articlesById.get(id);
    if (!article || article.data.edition !== 'ai' || article.data.decision !== 'publish-candidate') {
      throw new Error(`approved AI release has no publish-candidate article: ${id}`);
    }

    const articlePath = `content/ai/${id}/article.md`;
    const evidencePath = `decisions/ai/${id}/evidence.json`;
    const expectedRoutes = new Set(['/ai/', `/ai/${id}/`]);
    if (
      release.data.article_path !== articlePath
      || release.data.evidence_path !== evidencePath
      || release.data.routes.length !== expectedRoutes.size
      || release.data.routes.some((route) => !expectedRoutes.has(route))
    ) {
      throw new Error(`AI release path or route scope mismatch: ${id}`);
    }

    const articleBytes = await readRepositoryFile(articlePath);
    const evidenceBytes = await readRepositoryFile(evidencePath);
    if (
      sha256(articleBytes) !== release.data.artifact_hashes.article_sha256
      || sha256(evidenceBytes) !== release.data.artifact_hashes.evidence_sha256
    ) {
      throw new Error(`AI release artifact hash mismatch: ${id}`);
    }

    const evidence = JSON.parse(evidenceBytes.toString('utf8'));
    if (
      evidence.edition !== 'ai'
      || evidence.decision !== 'publish-candidate'
      || evidence.release_gate?.human_approval_required !== true
    ) {
      throw new Error(`AI release evidence gate mismatch: ${id}`);
    }

    approved.push({ id, article, release });
  }

  return approved.sort(
    (left, right) => right.article.data.date.valueOf() - left.article.data.date.valueOf(),
  );
}
