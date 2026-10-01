// Site-wide facts. Bump PATCH_VERSION and UPDATED with each release; everything else reads from here.

export const SITE_NAME = 'Hyper Emerald Guide';
export const GAME = 'Pokémon Hyper Emerald: Lost Artifacts';
export const GAME_VERSION = 'v5.7';
export const PATCH_VERSION = '1.7';
export const UPDATED = '2026-10-02';
export const TAGLINE =
  'The complete player’s guide to Pokémon Hyper Emerald: Lost Artifacts v5.7 and its English + quality-of-life patch.';

export const REPO = 'https://github.com/Nn-Exe/Pokemon-Hyper-Emerald-5.7-QoL';
export const ISSUES = REPO + '/issues';

export const NAV = [
  { href: '/', label: 'Home' },
  { href: '/guides/', label: 'Guides' },
  { href: '/wiki/', label: 'Wiki' },
  { href: '/features/', label: 'Features' },
  { href: '/faq/', label: 'FAQ' },
];

export const NAV_MORE = [
  { href: '/changelog/', label: 'Changelog' },
  { href: '/gallery/', label: 'Gallery' },
  { href: '/about/', label: 'About & credits' },
];

export const FOOTER = [
  {
    title: 'Play',
    links: [
      { href: '/guides/install/', label: 'Install & play' },
      { href: '/features/', label: 'Features' },
      { href: '/guides/controls/', label: 'Controls' },
      { href: '/changelog/', label: 'Changelog' },
    ],
  },
  {
    title: 'Guides',
    links: [
      { href: '/guides/walkthrough-hoenn/', label: 'Hoenn walkthrough' },
      { href: '/guides/walkthrough-postgame/', label: 'Post-game & Sinnoh' },
      { href: '/guides/lost-artifacts/', label: 'Lost Artifacts' },
      { href: '/guides/legendaries/', label: 'Legendary locations' },
      { href: '/guides/', label: 'All guides' },
    ],
  },
  {
    title: 'Reference',
    links: [
      { href: '/wiki/', label: 'Wiki' },
      { href: '/wiki/pokedex/', label: 'Pokédex' },
      { href: '/wiki/encounters/', label: 'Wild encounters' },
      { href: '/wiki/pokemon/', label: 'Pokémon finder' },
      { href: '/wiki/trainers/', label: 'Trainer battles' },
      { href: '/faq/', label: 'FAQ' },
      { href: '/gallery/', label: 'Gallery' },
    ],
  },
  {
    title: 'Project',
    links: [
      { href: '/about/', label: 'About & credits' },
      { href: REPO, label: 'GitHub repository', external: true },
      { href: ISSUES, label: 'Report a problem', external: true },
    ],
  },
];

export function formatDate(iso: string) {
  return new Date(iso + 'T00:00:00Z').toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    timeZone: 'UTC',
  });
}
