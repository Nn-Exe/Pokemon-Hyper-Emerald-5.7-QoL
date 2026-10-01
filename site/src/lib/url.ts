// The site is served under a sub-path on GitHub Pages; every internal URL goes through here.

const BASE = import.meta.env.BASE_URL.replace(/\/$/, '');

/** Root-relative path -> path under the site's base ("/guides/" -> "/Pokemon-…/guides/"). */
export function url(path = '/') {
  if (/^(https?:|mailto:|#)/.test(path)) return path;
  return BASE + (path.startsWith('/') ? path : '/' + path);
}

/** A file in docs/showcase (screenshots and clips). */
export function showcase(file: string) {
  return url('/showcase/' + file);
}

/** Absolute URL, for canonical links, Open Graph and structured data. */
export function absolute(path = '/') {
  return new URL(url(path), import.meta.env.SITE).href;
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
