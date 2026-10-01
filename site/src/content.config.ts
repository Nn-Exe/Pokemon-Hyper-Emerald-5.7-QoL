import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

// One MDX file per guide in src/content/guides. The file name is the URL: /guides/<name>/.
const guides = defineCollection({
  loader: glob({ pattern: '*.mdx', base: './src/content/guides' }),
  schema: z.object({
    title: z.string(),
    /** the small label above the title and on cards */
    category: z.string(),
    description: z.string(),
    /** which shelf of the guides hub it sits on, and its place there */
    group: z.enum(['start', 'walkthrough', 'reference']),
    order: z.number(),
    /** a clip from src/data/clips.json: the hero plays it, cards show its poster frame */
    clip: z.string(),
    heroAlt: z.string(),
    updated: z.string().optional(),
    /** tables and team cards want the full column, prose wants a reading width */
    wide: z.boolean().default(false),
    /** slugs of three guides to offer at the end; defaults to its neighbours */
    related: z.array(z.string()).default([]),
  }),
});

export const collections = { guides };
