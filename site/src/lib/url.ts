// The site is served under a sub-path on GitHub Pages (and at the root of a second host): every internal URL
// goes through here.

const BASE = import.meta.env.BASE_URL.replace(/\/$/, '');
/** Where search engines are pointed: this build's own address, or GitHub's for a mirror (astro.config.mjs). */
const CANONICAL_ROOT: string = import.meta.env.CANONICAL_ROOT;
/** A mirror without an address of its own has no sitemap. */
export const HAS_SITEMAP: boolean = import.meta.env.HAS_SITEMAP;

/** Root-relative path -> path under the site's base ("/guides/" -> "/Pokemon-…/guides/"). */
export function url(path = '/') {
  if (/^(https?:|mailto:|#)/.test(path)) return path;
  return BASE + (path.startsWith('/') ? path : '/' + path);
}

/** A file in docs/showcase (screenshots and clips). */
export function showcase(file: string) {
  return url('/showcase/' + file);
}

/** Absolute URL of a root-relative path ("/guides/"), for canonical links, Open Graph and structured data. */
export function absolute(path = '/') {
  return CANONICAL_ROOT + (path.startsWith('/') ? path : '/' + path);
}

/** The canonical URL of the page being built, from its Astro.url.pathname (which carries the base). */
export function canonicalOf(pathname: string) {
  return absolute(pathname.startsWith(BASE + '/') ? pathname.slice(BASE.length) : pathname);
}

export function slugify(text: string) {
  return text
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/♀/g, '-f')
    .replace(/♂/g, '-m')
    .replace(/['’.:%]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}
