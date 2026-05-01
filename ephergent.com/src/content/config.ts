// Astro Content Collection Schema for ephergent.com
import { z, defineCollection } from 'astro:content';

export const collections = {
  games: defineCollection({
    schema: z.object({
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
      name: z.string(),
      role: z.string(),
      voice: z.string().optional(),
      portrait: z.string().optional(),
      lore_links: z.array(z.string()).optional(),
    }),
  }),
  lore: defineCollection({
    schema: z.object({
      title: z.string(),
      type: z.string(),
      summary: z.string(),
      links: z.array(z.string()).optional(),
    }),
  }),
  transmissions: defineCollection({
    schema: z.object({
      title: z.string(),
      author: z.string(),
      date: z.union([z.string(), z.date()]),
      tags: z.array(z.string()).optional(),
      excerpt: z.string().optional(),
    }),
  }),
};
