// Astro Content Collection Schema for ephergent.com
import { z, defineCollection } from 'astro:content';

export const collections = {
  games: defineCollection({
    schema: z.object({
      title: z.string(),
      genre: z.string().optional(),
      engine: z.string().optional(),
      size: z.string().optional(),
      size_mb: z.number().optional(),
      embed_path: z.string().optional(),
      story_context: z.string().optional(),
    }),
  }),
  crew: defineCollection({
    schema: z.object({
      name: z.string().optional(),
      role: z.string().optional(),
      voice: z.string().optional(),
      portrait: z.string().optional(),
      lore_links: z.array(z.string()).optional(),
    }),
  }),
  lore: defineCollection({
    schema: z.object({
      title: z.string().optional(),
      type: z.string().optional(),
      summary: z.string().optional(),
      links: z.array(z.string()).optional(),
    }),
  }),
  transmissions: defineCollection({
    schema: z.object({
      title: z.string().optional(),
      author: z.string().optional(),
      date: z.string().optional(),
      tags: z.array(z.string()).optional(),
      excerpt: z.string().optional(),
    }),
  }),
};
