// Check every internal link, image, video and anchor in the published site (../docs).
//   node scripts/check-links.mjs
// Exits 1 and lists the problems if a page links to a file or an #anchor that does not exist.

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const DOCS = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../docs');
const BASE = '/Pokemon-Hyper-Emerald-5.7-QoL';

function walk(dir, out = []) {
  for (const name of fs.readdirSync(dir)) {
    const full = path.join(dir, name);
    if (fs.statSync(full).isDirectory()) {
      if (name !== 'showcase') walk(full, out);
    } else if (name.endsWith('.html')) out.push(full);
  }
  return out;
}

const pages = walk(DOCS);
const idsOf = new Map();
function ids(file) {
  if (!idsOf.has(file)) {
    const html = fs.readFileSync(file, 'utf8');
    idsOf.set(file, new Set([...html.matchAll(/\sid="([^"]+)"/g)].map((m) => m[1])));
  }
  return idsOf.get(file);
}

/** URL path under the base -> file in docs, as GitHub Pages resolves it */
function resolve(urlPath) {
  let file = path.join(DOCS, decodeURIComponent(urlPath));
  if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
  return fs.existsSync(file) ? file : null;
}

const problems = [];
let checked = 0;
for (const page of pages) {
  const html = fs.readFileSync(page, 'utf8');
  const rel = path.relative(DOCS, page).replace(/\\/g, '/');
  const refs = [...html.matchAll(/\s(?:href|src|poster|data-src)="([^"]+)"/g)].map((m) => m[1].replace(/&amp;/g, '&'));
  for (const ref of new Set(refs)) {
    if (/^(https?:|mailto:|data:)/.test(ref)) continue;
    checked++;
    if (ref.startsWith('#')) {
      if (ref.length > 1 && !ids(page).has(decodeURIComponent(ref.slice(1)))) problems.push(`${rel}: no anchor ${ref}`);
      continue;
    }
    if (!ref.startsWith(BASE + '/')) {
      problems.push(`${rel}: link outside the site base: ${ref}`);
      continue;
    }
    const [pathPart, hash] = ref.slice(BASE.length).split('#');
    const file = resolve(pathPart.split('?')[0]);
    if (!file) problems.push(`${rel}: missing ${ref}`);
    else if (hash && file.endsWith('.html') && !ids(file).has(decodeURIComponent(hash)))
      problems.push(`${rel}: no anchor #${hash} in ${pathPart}`);
  }
}

// the search index links too
const search = JSON.parse(fs.readFileSync(path.join(DOCS, 'search.json'), 'utf8'));
for (const e of search) {
  checked++;
  const [pathPart, hash] = e.u.split('#');
  const file = resolve('/' + pathPart.split('?')[0]);
  if (!file) problems.push(`search.json: missing ${e.u} (${e.n})`);
  else if (hash && !ids(file).has(decodeURIComponent(hash))) problems.push(`search.json: no anchor in ${e.u} (${e.n})`);
}

if (problems.length) {
  console.error(problems.slice(0, 80).join('\n'));
  console.error(`\n${problems.length} problem(s) in ${pages.length} pages`);
  process.exit(1);
}
console.log(`${pages.length} pages, ${checked} internal links and ${search.length} search entries: all resolve`);
