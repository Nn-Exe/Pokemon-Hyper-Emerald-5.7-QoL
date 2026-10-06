import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';
import { unified } from '@astrojs/markdown-remark';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

// GitHub Pages serves the repository's docs/ folder under this path.
const GITHUB = { site: 'https://nn-exe.github.io', base: '/Pokemon-Hyper-Emerald-5.7-QoL' };

// A second host (scripts/package-infinityfree.mjs) builds the same site for a domain's root: HOST_ROOT=1 and,
// once the copy has an address of its own, HOST_SITE=https://that.address. Without HOST_SITE the copy is a
// mirror: its pages name the GitHub address as the canonical one and it gets no sitemap.
const onHost = process.env.HOST_ROOT === '1';
const BASE = onHost ? '' : GITHUB.base;
const SITE = (process.env.HOST_SITE || GITHUB.site).replace(/\/+$/, '');
const OWN_ADDRESS = !onHost || Boolean(process.env.HOST_SITE);
const CANONICAL_ROOT = OWN_ADDRESS ? SITE + BASE : GITHUB.site + GITHUB.base;

// The screenshots and clips live in ../docs/showcase (the README uses them too) and are never copied:
// scripts/publish.mjs leaves that folder alone, and in `astro dev` this middleware serves it.
const showcaseDir = fileURLToPath(new URL('../docs/showcase/', import.meta.url));
const TYPES = { '.png': 'image/png', '.gif': 'image/gif', '.mp4': 'video/mp4', '.webp': 'image/webp' };
function showcaseDev() {
  return {
    name: 'showcase-dev',
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        // the dev server may or may not have stripped the base path by the time this runs
        const url = decodeURIComponent((req.originalUrl || req.url || '').split('?')[0]);
        const prefix = [BASE + '/showcase/', '/showcase/'].find((p) => url.startsWith(p));
        if (!prefix) return next();
        const file = path.join(showcaseDir, url.slice(prefix.length));
        if (!file.startsWith(showcaseDir) || !fs.existsSync(file)) return next();
        res.setHeader('Content-Type', TYPES[path.extname(file)] || 'application/octet-stream');
        fs.createReadStream(file).pipe(res);
      });
    },
  };
}

// Guides are written with root-relative links (/wiki/encounters/); the site lives under BASE.
// Also wraps every table so a wide one scrolls inside its own box instead of the page.
function rehypeSite() {
  const walk = (node, parent, index) => {
    if (node.type === 'element') {
      const p = node.properties || (node.properties = {});
      if (node.tagName === 'a' && typeof p.href === 'string') {
        if (p.href.startsWith('/') && !p.href.startsWith('//')) p.href = BASE + p.href;
        else if (/^https?:/.test(p.href)) {
          p.target = '_blank';
          p.rel = 'noopener noreferrer';
        }
      }
      if (node.tagName === 'table' && parent && !(parent.properties?.className || []).includes('table-shell')) {
        parent.children[index] = {
          type: 'element',
          tagName: 'div',
          properties: { className: ['table-shell'], tabIndex: 0, role: 'region', ariaLabel: 'Table' },
          children: [node],
        };
      }
    }
    (node.children || []).forEach((child, i) => walk(child, node, i));
  };
  return (tree) => walk(tree, null, 0);
}

export default defineConfig({
  site: SITE,
  base: BASE || '/',
  trailingSlash: 'always',
  outDir: './dist',
  build: { format: 'directory', inlineStylesheets: 'never' },
  integrations: [mdx(), ...(OWN_ADDRESS ? [sitemap()] : [])],
  // the remark/rehype pipeline, so the rehype plugin above runs on the MDX guides
  markdown: { processor: unified({ rehypePlugins: [rehypeSite] }) },
  vite: {
    plugins: [showcaseDev()],
    // src/lib/url.ts reads these: where canonical links point, and whether this build has a sitemap
    define: {
      'import.meta.env.CANONICAL_ROOT': JSON.stringify(CANONICAL_ROOT),
      'import.meta.env.HAS_SITEMAP': JSON.stringify(OWN_ADDRESS),
    },
  },
  devToolbar: { enabled: false },
});
