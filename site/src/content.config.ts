import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const articles = defineCollection({
  loader: glob({ pattern: '*/article.md', base: '../content' }),
  schema: z.object({
    title: z.string(),
    date: z.coerce.date(),
    topic: z.string().optional(),
    guest: z.string().optional(),
    summary: z.string().optional(),
    holiday: z.boolean().optional(),
    publication: z.enum(['published', 'experiment']).default('published'),
  }),
});

const debates = defineCollection({
  loader: glob({ pattern: '*/debate.md', base: '../content' }),
  schema: z.object({}).passthrough(),
});

const guests = defineCollection({
  loader: glob({ pattern: '*/guest.md', base: '../content' }),
  schema: z.object({}).passthrough(),
});

const aiArticles = defineCollection({
  loader: glob({ pattern: '*/article.md', base: '../content/ai' }),
  schema: z.object({
    edition: z.literal('ai'),
    decision: z.enum(['publish-candidate', 'no-publish']),
    title: z.string(),
    date: z.coerce.date(),
    subject: z.string(),
    summary: z.string(),
    evidence_ceiling: z.enum(['E1', 'E2', 'E3', 'E4']),
    reproducibility: z.enum(['R0', 'R1', 'R2', 'R3']),
    conflicts: z.array(z.string()).min(1),
  }).strict(),
});

const aiReleases = defineCollection({
  loader: glob({ pattern: '*/release.json', base: '../decisions/ai' }),
  schema: z.object({
    schema_version: z.literal(1),
    edition: z.literal('ai'),
    publication_id: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
    decision: z.literal('publish-candidate'),
    release_status: z.enum(['approved-for-publication', 'withdrawn']),
    article_path: z.string(),
    evidence_path: z.string(),
    artifact_hashes: z.object({
      article_sha256: z.string().regex(/^[0-9a-f]{64}$/),
      evidence_sha256: z.string().regex(/^[0-9a-f]{64}$/),
    }).strict(),
    routes: z.array(z.string()).min(2),
    authorization: z.discriminatedUnion('mode', [
      z.object({
        mode: z.literal('human'),
        approved: z.literal(true),
        approved_at: z.string(),
        approved_by: z.string(),
        approval_basis: z.string(),
        scope: z.array(z.string()).min(1),
      }).strict(),
      z.object({
        mode: z.literal('automatic'),
        policy_id: z.literal('ai-auto-publish-v1'),
        authorized_at: z.string(),
        executor: z.string(),
        checks: z.array(z.string()).min(5),
      }).strict(),
    ]),
  }).strict(),
});

const edaArticles = defineCollection({
  loader: glob({ pattern: '*/article.md', base: '../content/eda' }),
  schema: z.object({
    edition: z.literal('eda'),
    decision: z.enum(['publish-candidate', 'no-publish']),
    title: z.string(),
    date: z.coerce.date(),
    subject: z.string(),
    summary: z.string(),
    evidence_ceiling: z.enum(['E1', 'E2', 'E3', 'E4']),
    reproducibility: z.enum(['R0', 'R1', 'R2', 'R3']),
    conflicts: z.array(z.string()).min(1),
  }).strict(),
});

const edaReleases = defineCollection({
  loader: glob({ pattern: '*/release.json', base: '../decisions/eda' }),
  schema: z.object({
    schema_version: z.literal(1),
    edition: z.literal('eda'),
    publication_id: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
    decision: z.literal('publish-candidate'),
    release_status: z.enum(['approved-for-publication', 'withdrawn']),
    article_path: z.string(),
    evidence_path: z.string(),
    artifact_hashes: z.object({
      article_sha256: z.string().regex(/^[0-9a-f]{64}$/),
      evidence_sha256: z.string().regex(/^[0-9a-f]{64}$/),
    }).strict(),
    routes: z.array(z.string()).min(2),
    authorization: z.object({
      mode: z.literal('human'),
      approved: z.literal(true),
      approved_at: z.string(),
      approved_by: z.string(),
      approval_basis: z.string(),
      scope: z.array(z.string()).min(1),
    }).strict(),
  }).strict(),
});

export const collections = {
  articles,
  debates,
  guests,
  aiArticles,
  aiReleases,
  edaArticles,
  edaReleases,
};
