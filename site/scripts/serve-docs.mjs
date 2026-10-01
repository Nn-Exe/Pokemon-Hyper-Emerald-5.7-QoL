// Serve ../docs exactly as GitHub Pages does: under the repository's path, with directory index pages
// and docs/404.html for anything missing.   node scripts/serve-docs.mjs [port]

import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const DOCS = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../docs');
const BASE = '/Pokemon-Hyper-Emerald-5.7-QoL';
const PORT = Number(process.argv[2]) || 4321;
const TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.xml': 'application/xml; charset=utf-8',
  '.txt': 'text/plain; charset=utf-8',
  '.md': 'text/markdown; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.gif': 'image/gif',
  '.webp': 'image/webp',
  '.mp4': 'video/mp4',
  '.woff2': 'font/woff2',
  '.webmanifest': 'application/manifest+json',
};

function send(req, res, file, status = 200) {
  const size = fs.statSync(file).size;
  const head = { 'Content-Type': TYPES[path.extname(file)] || 'application/octet-stream', 'Accept-Ranges': 'bytes' };
  const range = /^bytes=(\d*)-(\d*)$/.exec(req.headers.range || '');
  if (range && status === 200) {
    // video elements ask for byte ranges
    const start = range[1] ? Number(range[1]) : 0;
    const end = range[2] ? Math.min(Number(range[2]), size - 1) : size - 1;
    res.writeHead(206, { ...head, 'Content-Range': `bytes ${start}-${end}/${size}`, 'Content-Length': end - start + 1 });
    fs.createReadStream(file, { start, end }).pipe(res);
    return;
  }
  res.writeHead(status, { ...head, 'Content-Length': size });
  fs.createReadStream(file).pipe(res);
}

http
  .createServer((req, res) => {
    const pathname = decodeURIComponent(new URL(req.url, 'http://x').pathname);
    if (pathname === '/') {
      res.writeHead(302, { Location: BASE + '/' });
      return res.end();
    }
    if (!pathname.startsWith(BASE)) {
      res.writeHead(404);
      return res.end('outside the site base');
    }
    let file = path.join(DOCS, pathname.slice(BASE.length));
    if (!file.startsWith(DOCS)) {
      res.writeHead(403);
      return res.end();
    }
    if (fs.existsSync(file) && fs.statSync(file).isDirectory()) {
      if (!pathname.endsWith('/')) {
        res.writeHead(301, { Location: pathname + '/' });
        return res.end();
      }
      file = path.join(file, 'index.html');
    }
    if (fs.existsSync(file)) return send(req, res, file);
    send(req, res, path.join(DOCS, '404.html'), 404);
  })
  .listen(PORT, () => console.log(`docs/ served at http://localhost:${PORT}${BASE}/`));
