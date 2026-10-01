// Copy the built site (site/dist) into ../docs, the folder GitHub Pages serves.
//
// docs/ also holds things that are not the site: the engineering notes and the screenshots the README uses.
// Those are kept; everything else in docs/ is replaced by the new build. The old guide's page names
// (getting-started.html, trainers.html ...) are written as small redirect pages so existing links keep working.

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const DIST = path.resolve(here, '../dist');
const DOCS = path.resolve(here, '../../docs');
const BASE = '/Pokemon-Hyper-Emerald-5.7-QoL';
const ORIGIN = 'https://nn-exe.github.io';

// never touched by a publish
const KEEP = new Set(['NOTES.md', 'DEXNAV-PROGRESS.md', 'showcase', '.nojekyll']);

// old page -> new path (under the site base)
const REDIRECTS = {
  'getting-started.html': '/guides/install/',
  'features.html': '/features/',
  'mechanics.html': '/guides/mechanics/',
  'walkthrough-hoenn.html': '/guides/walkthrough-hoenn/',
  'walkthrough-postgame.html': '/guides/walkthrough-postgame/',
  'walkthrough-lost-artifacts.html': '/guides/lost-artifacts/',
  'trainers.html': '/wiki/trainers/',
  'pokemon-locations.html': '/wiki/encounters/',
  'legendaries.html': '/guides/legendaries/',
  'items.html': '/guides/mega-stones-key-items/',
  'faq.html': '/faq/',
  'credits.html': '/about/',
  'journal.html': '/guides/journal/',
  'content-audit.html': '/guides/side-content/',
};

if (!fs.existsSync(path.join(DIST, 'index.html'))) {
  console.error('site/dist has no index.html: run the Astro build first');
  process.exit(1);
}
if (!fs.existsSync(path.join(DOCS, 'showcase'))) {
  console.error(`${DOCS} has no showcase/ folder: refusing to publish into the wrong place`);
  process.exit(1);
}

let removed = 0;
for (const name of fs.readdirSync(DOCS)) {
  if (KEEP.has(name)) continue;
  // with a thousand pages, an indexer or virus scanner often still holds one: wait for it rather than fail
  fs.rmSync(path.join(DOCS, name), { recursive: true, force: true, maxRetries: 20, retryDelay: 250 });
  removed++;
}

let copied = 0;
function copy(from, to) {
  const stat = fs.statSync(from);
  if (stat.isDirectory()) {
    fs.mkdirSync(to, { recursive: true });
    for (const name of fs.readdirSync(from)) copy(path.join(from, name), path.join(to, name));
  } else {
    fs.copyFileSync(from, to);
    copied++;
  }
}
for (const name of fs.readdirSync(DIST)) {
  if (KEEP.has(name)) {
    console.error(`the build produced "${name}", which docs/ keeps for itself`);
    process.exit(1);
  }
  copy(path.join(DIST, name), path.join(DOCS, name));
}

for (const [file, target] of Object.entries(REDIRECTS)) {
  const to = BASE + target;
  const page = path.join(DOCS, target.replace(/^\//, ''), 'index.html');
  if (!fs.existsSync(page)) {
    console.error(`redirect ${file} points to ${target}, which the build did not produce`);
    process.exit(1);
  }
  fs.writeFileSync(
    path.join(DOCS, file),
    `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>This page has moved</title>
<link rel="canonical" href="${ORIGIN}${to}">
<meta name="robots" content="noindex">
<meta http-equiv="refresh" content="0; url=${to}">
<script>location.replace(${JSON.stringify(to)} + location.hash)</script>
</head>
<body>
<p>This page has moved to <a href="${to}">${ORIGIN}${to}</a>.</p>
</body>
</html>
`,
  );
}

console.log(
  `published to docs/: ${copied} files copied, ${removed} old entries replaced, ${Object.keys(REDIRECTS).length} redirects written`,
);
