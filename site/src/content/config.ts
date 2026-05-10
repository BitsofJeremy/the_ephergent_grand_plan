// Astro Content Collection Schema for ephergent.com
import { z, defineCollection } from 'astro:content';

export const collections = {
  games: defineCollection({
    schema: z.object({
      slug: z.string(),
      title: z.string(),
      genre: z.string(),
      engine: z.string(),
      size: z.string(),
      embed_path: z.string(),
      story_context: z.string(),
    }),
  }),
  crew: defineCollection({
    schema: z.object({
      slug: z.string(),
      name: z.string(),
      role: z.string(),
      voice: z.string(),
      portrait: z.string(),
      lore_links: z.array(z.string()),
    }),
  }),
  lore: defineCollection({
    schema: z.object({
      slug: z.string(),
      title: z.string(),
      type: z.string(),
      summary: z.string(),
      links: z.array(z.string()),
    }),
  }),
  transmissions: defineCollection({
    schema: z.object({
      title: z.string(),
      author: z.string(),
      date: z.string(),
      tags: z.array(z.string()),
      excerpt: z.string(),
    }),
  }),
};
