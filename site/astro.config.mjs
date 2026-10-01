import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';
import { unified } from '@astrojs/markdown-remark';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

// GitHub Pages serves the repository's docs/ folder under this path.
const SITE = 'https://nn-exe.github.io';
const BASE = '/Pokemon-Hyper-Emerald-5.7-QoL';

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
  base: BASE,
  trailingSlash: 'always',
  outDir: './dist',
  build: { format: 'directory', inlineStylesheets: 'never' },
  integrations: [mdx(), sitemap()],
  // the remark/rehype pipeline, so the rehype plugin above runs on the MDX guides
  markdown: { processor: unified({ rehypePlugins: [rehypeSite] }) },
  vite: { plugins: [showcaseDev()] },
  devToolbar: { enabled: false },
});
