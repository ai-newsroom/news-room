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

export const collections = { articles, debates, guests };
