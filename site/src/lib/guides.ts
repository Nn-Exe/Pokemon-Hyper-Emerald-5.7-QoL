import { getCollection, type CollectionEntry } from 'astro:content';

export type Guide = CollectionEntry<'guides'>;

export const GROUPS = [
  { key: 'walkthrough', title: 'Walkthrough', note: 'The whole story, in order' },
  { key: 'start', title: 'Getting started', note: 'Before you press New Game' },
  { key: 'reference', title: 'Reference guides', note: 'Where things are' },
] as const;

const groupOrder = { start: 0, walkthrough: 1, reference: 2 };

/** Every guide in reading order: getting started, the three walkthrough parts, then reference. */
export async function allGuides() {
  const guides = await getCollection('guides');
  return guides.sort(
    (a, b) => groupOrder[a.data.group] - groupOrder[b.data.group] || a.data.order - b.data.order,
  );
}

export const guideHref = (g: Guide) => `/guides/${g.id}/`;
export const guidePoster = (g: Guide) => `clips/${g.data.clip}.png`;
