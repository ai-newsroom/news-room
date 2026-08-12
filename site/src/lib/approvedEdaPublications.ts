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
    throw new Error(`EDA release path escapes repository: ${path}`);
  }
  return readFile(url);
}

function sha256(value: Uint8Array) {
  return createHash('sha256').update(value).digest('hex');
}

export async function getApprovedEdaPublications() {
  const articles = await getCollection('edaArticles');
  const releases = await getCollection('edaReleases');
  const articlesById = new Map(articles.map((article) => [publicationId(article.id), article]));
  const seen = new Set<string>();
  const approved = [];

  for (const release of releases) {
    if (release.data.release_status !== 'approved-for-publication') continue;

    const id = release.data.publication_id;
    if (publicationId(release.id) !== id || seen.has(id)) {
      throw new Error(`duplicate or mismatched EDA release id: ${id}`);
    }
    seen.add(id);

    const article = articlesById.get(id);
    if (!article || article.data.edition !== 'eda' || article.data.decision !== 'publish-candidate') {
      throw new Error(`approved EDA release has no publish-candidate article: ${id}`);
    }

    const articlePath = `content/eda/${id}/article.md`;
    const evidencePath = `decisions/eda/${id}/evidence.json`;
    const expectedRoutes = new Set(['/eda/', `/eda/${id}/`]);
    if (
      release.data.article_path !== articlePath
      || release.data.evidence_path !== evidencePath
      || release.data.routes.length !== expectedRoutes.size
      || release.data.routes.some((route) => !expectedRoutes.has(route))
    ) {
      throw new Error(`EDA release path or route scope mismatch: ${id}`);
    }

    const articleBytes = await readRepositoryFile(articlePath);
    const evidenceBytes = await readRepositoryFile(evidencePath);
    if (
      sha256(articleBytes) !== release.data.artifact_hashes.article_sha256
      || sha256(evidenceBytes) !== release.data.artifact_hashes.evidence_sha256
    ) {
      throw new Error(`EDA release artifact hash mismatch: ${id}`);
    }

    const evidence = JSON.parse(evidenceBytes.toString('utf8'));
    const humanAuthorized = (
      release.data.authorization.mode === 'human'
      && release.data.authorization.approved === true
      && evidence.release_gate?.human_approval_required === true
    );
    const automaticallyAuthorized = (
      release.data.authorization.mode === 'automatic'
      && evidence.release_gate?.human_approval_required === false
      && evidence.release_gate?.automatic_publish_allowed === true
      && evidence.release_gate?.quality_gate_passed === true
      && evidence.release_gate?.policy_id === release.data.authorization.policy_id
    );
    if (
      evidence.edition !== 'eda'
      || evidence.decision !== 'publish-candidate'
      || (!humanAuthorized && !automaticallyAuthorized)
    ) {
      throw new Error(`EDA release evidence gate mismatch: ${id}`);
    }

    approved.push({ id, article, release });
  }

  return approved.sort(
    (left, right) => right.article.data.date.valueOf() - left.article.data.date.valueOf(),
  );
}
