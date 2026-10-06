// Build the guide for a second host and lay it out ready to upload: InfinityFree's free plan, an Apache server
// where the site sits at the domain's root (the account's htdocs folder).
//
//   node scripts/package-infinityfree.mjs                        a mirror: canonical links name the GitHub site
//   node scripts/package-infinityfree.mjs https://your.address   a site of its own: its own canonical links,
//                                                                sitemap and robots.txt
//
// Writes ../infinityfree/ (git-ignored):
//   htdocs/              everything to upload: its contents go into the server's htdocs folder
//   zips/                the same in archives the host accepts (under 10 MB each), for its online file manager
//   HOW-TO-UPLOAD.txt    the steps
// and refuses to finish if the result breaks one of the plan's limits (LIMITS below; from InfinityFree's
// knowledge base, "Why are my files deleted after uploading them", read 2026-10-04).

import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const SITE_DIR = path.resolve(here, '..');
const BUILD = path.join(SITE_DIR, 'dist-host');
const SHOWCASE = path.resolve(SITE_DIR, '../docs/showcase');
const OUT = path.resolve(SITE_DIR, '../infinityfree');
const HTDOCS = path.join(OUT, 'htdocs');
const ZIPS = path.join(OUT, 'zips');

const LIMITS = {
  code: 1_000_000, // "HTML, PHP and JS files are limited to 1 MB"
  htaccess: 10_000, // ".htaccess files are limited to 10 kB"
  file: 10_000_000, // "All other files are limited to 10 MB" (an archive over that is deleted too)
  inodes: 30_000, // files and folders in the account
  blocked: ['.exe', '.apk'],
};
const ZIP_MAX = 9_000_000;

const address = (process.argv[2] || '').replace(/\/+$/, '');
if (address && !/^https?:\/\/[^/\s]+$/.test(address)) {
  console.error(`"${process.argv[2]}" is not an address like https://example.com`);
  process.exit(1);
}

// ---- 1. build for a domain root ----
const env = { ...process.env, HOST_ROOT: '1' };
if (address) env.HOST_SITE = address;
else delete env.HOST_SITE;
fs.rmSync(BUILD, { recursive: true, force: true, maxRetries: 20, retryDelay: 250 });
const astro = path.join(SITE_DIR, 'node_modules/astro/bin/astro.mjs');
const built = spawnSync(process.execPath, [astro, 'build', '--outDir', 'dist-host'], { cwd: SITE_DIR, env, stdio: 'inherit' });
if (built.status !== 0 || !fs.existsSync(path.join(BUILD, 'index.html'))) {
  console.error('the Astro build failed');
  process.exit(1);
}

// ---- 2. htdocs: the build, and the screenshots and clips its pages use ----
function walk(dir, out = []) {
  for (const name of fs.readdirSync(dir).sort()) {
    const full = path.join(dir, name);
    if (fs.statSync(full).isDirectory()) walk(full, out);
    else out.push(full);
  }
  return out;
}
fs.rmSync(OUT, { recursive: true, force: true, maxRetries: 20, retryDelay: 250 });
fs.mkdirSync(HTDOCS, { recursive: true });
fs.cpSync(BUILD, HTDOCS, { recursive: true });

// docs/showcase also holds what only the README shows (the montage GIFs, older screenshots): take what is linked
const used = new Set();
for (const file of walk(HTDOCS)) {
  if (!/\.(html|json|js|css|xml|webmanifest)$/.test(file)) continue;
  for (const m of fs.readFileSync(file, 'utf8').matchAll(/\/showcase\/([A-Za-z0-9_./-]+)/g)) used.add(m[1]);
}
for (const rel of [...used].sort()) {
  const from = path.join(SHOWCASE, rel);
  if (!fs.existsSync(from) || !fs.statSync(from).isFile()) {
    console.error(`a page links showcase/${rel}, which is not in docs/showcase`);
    process.exit(1);
  }
  const to = path.join(HTDOCS, 'showcase', rel);
  fs.mkdirSync(path.dirname(to), { recursive: true });
  fs.copyFileSync(from, to);
}

// ---- 3. what an Apache server needs told ----
fs.writeFileSync(
  path.join(HTDOCS, '.htaccess'),
  `# Hyper Emerald Guide: settings for the Apache server (written by site/scripts/package-infinityfree.mjs).

# a missing page shows the site's own "not found" page, not the host's
ErrorDocument 404 /404.html

AddDefaultCharset UTF-8
<IfModule mod_mime.c>
  AddType font/woff2 .woff2
  AddType video/mp4 .mp4
  AddType application/manifest+json .webmanifest
</IfModule>

# Let browsers keep what does not change, so a returning visitor asks the server for less (the free plan
# counts every request). Files under /_astro/ carry a hash in their name: a new build gives them new names.
<IfModule mod_expires.c>
  ExpiresActive On
  ExpiresDefault "access plus 1 hour"
  ExpiresByType text/html "access plus 10 minutes"
  ExpiresByType application/json "access plus 1 hour"
  ExpiresByType text/css "access plus 1 year"
  ExpiresByType text/javascript "access plus 1 year"
  ExpiresByType application/javascript "access plus 1 year"
  ExpiresByType font/woff2 "access plus 1 year"
  ExpiresByType image/png "access plus 7 days"
  ExpiresByType image/svg+xml "access plus 7 days"
  ExpiresByType video/mp4 "access plus 7 days"
</IfModule>
`,
);
if (address)
  fs.writeFileSync(path.join(HTDOCS, 'robots.txt'), `User-agent: *\nAllow: /\n\nSitemap: ${address}/sitemap-index.xml\n`);

// ---- 4. the plan's limits ----
const files = walk(HTDOCS);
const rel = (file) => path.relative(HTDOCS, file).replace(/\\/g, '/');
const folders = new Set();
for (const file of files) for (let d = path.dirname(rel(file)); d !== '.'; d = path.dirname(d)) folders.add(d);
const problems = [];
let biggestCode = { size: 0, name: '' };
for (const file of files) {
  const size = fs.statSync(file).size;
  const name = rel(file);
  const ext = path.extname(name).toLowerCase();
  const isCode = ['.html', '.htm', '.php', '.js'].includes(ext);
  const limit = path.basename(name) === '.htaccess' ? LIMITS.htaccess : isCode ? LIMITS.code : LIMITS.file;
  if (size > limit) problems.push(`${name} is ${size.toLocaleString('en-US')} bytes: over the ${limit.toLocaleString('en-US')} allowed`);
  if (LIMITS.blocked.includes(ext)) problems.push(`${name}: the host deletes ${ext} files`);
  if (isCode && size > biggestCode.size) biggestCode = { size, name };
}
const inodes = files.length + folders.size;
if (inodes > LIMITS.inodes) problems.push(`${inodes} files and folders: over the ${LIMITS.inodes} allowed`);
if (problems.length) {
  console.error(problems.join('\n'));
  process.exit(1);
}
const links = spawnSync(process.execPath, [path.join(here, 'check-links.mjs'), HTDOCS, ''], { stdio: 'inherit' });
if (links.status !== 0) process.exit(1);

// ---- 5. the same as archives under the host's 10 MB, for its file manager ----
// (a zip is: per entry a local header, the name and the data; then a directory of the entries; then a trailer)
const dos = (d) => ({
  time: (d.getHours() << 11) | (d.getMinutes() << 5) | (d.getSeconds() >> 1),
  date: ((d.getFullYear() - 1980) << 9) | ((d.getMonth() + 1) << 5) | d.getDate(),
});
const now = dos(new Date());
function entry(name, raw) {
  const isDir = name.endsWith('/');
  const packed = isDir ? raw : zlib.deflateRawSync(raw, { level: 9 });
  const store = isDir || packed.length >= raw.length;
  const nameBytes = Buffer.from(name, 'utf8');
  const body = store ? raw : packed;
  return { nameBytes, body, store, isDir, crc: isDir ? 0 : zlib.crc32(raw), size: raw.length, bytes: 76 + 2 * nameBytes.length + body.length };
}
function writeZip(file, entries) {
  const parts = [];
  const directory = [];
  let offset = 0;
  for (const e of entries) {
    const local = Buffer.alloc(30);
    local.writeUInt32LE(0x04034b50, 0);
    local.writeUInt16LE(20, 4);
    local.writeUInt16LE(0x0800, 6); // names are UTF-8
    local.writeUInt16LE(e.store ? 0 : 8, 8);
    local.writeUInt16LE(now.time, 10);
    local.writeUInt16LE(now.date, 12);
    local.writeUInt32LE(e.crc, 14);
    local.writeUInt32LE(e.body.length, 18);
    local.writeUInt32LE(e.size, 22);
    local.writeUInt16LE(e.nameBytes.length, 26);
    parts.push(local, e.nameBytes, e.body);
    const central = Buffer.alloc(46);
    central.writeUInt32LE(0x02014b50, 0);
    central.writeUInt16LE(0x0314, 4); // made on Unix: the mode below is used
    central.writeUInt16LE(20, 6);
    central.writeUInt16LE(0x0800, 8);
    central.writeUInt16LE(e.store ? 0 : 8, 10);
    central.writeUInt16LE(now.time, 12);
    central.writeUInt16LE(now.date, 14);
    central.writeUInt32LE(e.crc, 16);
    central.writeUInt32LE(e.body.length, 20);
    central.writeUInt32LE(e.size, 24);
    central.writeUInt16LE(e.nameBytes.length, 28);
    central.writeUInt32LE(e.isDir ? ((0o40755 << 16) | 0x10) >>> 0 : (0o100644 << 16) >>> 0, 38);
    central.writeUInt32LE(offset, 42);
    directory.push(central, e.nameBytes);
    offset += 30 + e.nameBytes.length + e.body.length;
  }
  const dir = Buffer.concat(directory);
  const end = Buffer.alloc(22);
  end.writeUInt32LE(0x06054b50, 0);
  end.writeUInt16LE(entries.length, 8);
  end.writeUInt16LE(entries.length, 10);
  end.writeUInt32LE(dir.length, 12);
  end.writeUInt32LE(offset, 16);
  fs.writeFileSync(file, Buffer.concat([...parts, dir, end]));
}
// in path order, so a folder stays in one archive where it fits; each archive names the folders it needs
const volumes = [];
let current = null;
for (const file of files) {
  const name = rel(file);
  const e = entry(name, fs.readFileSync(file));
  const dirs = [];
  for (let d = path.posix.dirname(name); d !== '.'; d = path.posix.dirname(d)) dirs.unshift(d + '/');
  const fresh = (v) => dirs.filter((d) => !v.dirs.has(d)).map((d) => entry(d, Buffer.alloc(0)));
  let add = current ? fresh(current) : [];
  if (!current || current.bytes + e.bytes + add.reduce((n, x) => n + x.bytes, 0) + 22 > ZIP_MAX) {
    current = { entries: [], dirs: new Set(), bytes: 0 };
    volumes.push(current);
    add = fresh(current);
  }
  for (const d of add) current.dirs.add(d.nameBytes.toString());
  current.entries.push(...add, e);
  current.bytes += e.bytes + add.reduce((n, x) => n + x.bytes, 0);
}
fs.mkdirSync(ZIPS, { recursive: true });
const zipNames = volumes.map((v, i) => `site-part-${i + 1}-of-${volumes.length}.zip`);
volumes.forEach((v, i) => writeZip(path.join(ZIPS, zipNames[i]), v.entries));
for (const name of zipNames) {
  const size = fs.statSync(path.join(ZIPS, name)).size;
  if (size > LIMITS.file) {
    console.error(`${name} came out at ${size} bytes: over the host's 10 MB`);
    process.exit(1);
  }
}

// ---- 6. the steps, for whoever uploads it ----
const total = files.reduce((n, f) => n + fs.statSync(f).size, 0);
const mb = (n) => (n / 1e6).toFixed(1) + ' MB';
fs.writeFileSync(
  path.join(OUT, 'HOW-TO-UPLOAD.txt'),
  `HYPER EMERALD GUIDE - UPLOADING TO INFINITYFREE
================================================

What is here
  htdocs\\   the whole website: ${files.length.toLocaleString('en-US')} files, ${mb(total)}. Everything INSIDE it goes into
            the "htdocs" folder of your hosting account.
  zips\\     the same website cut into ${zipNames.length} zip files (plan B, below).

InfinityFree has no "import one file" for a site this size: it deletes any file over 10 MB, zip files
included. The one-step way is an FTP program: you drag one folder and it copies everything.

THE WAY THAT WORKS: FileZilla (free)
  1. In the InfinityFree client area open your hosting account and find "FTP Details". You need three
     things from it: the FTP hostname, the FTP username and the FTP password.
  2. Install FileZilla Client from https://filezilla-project.org and open it.
  3. At the top fill in Host, Username and Password from step 1, leave Port empty, press Quickconnect.
  4. Right side (the server): open the folder "htdocs". If you added your own domain to the account, use the
     "htdocs" inside the folder named after that domain instead.
     Delete what InfinityFree put there (index2.html and the like).
  5. Left side (your PC): go to this folder, then into "htdocs".
     In FileZilla's menu turn on Server > "Force showing hidden files", so you can see ".htaccess" arrive.
  6. Click one file on the left, press Ctrl+A to select everything, and drag it onto the right side.
  7. Wait. It is about ${(Math.round(files.length / 100) * 100).toLocaleString('en-US')} small files, so it takes a while.
     When the list at the bottom is empty, look at the "Failed transfers" tab. If anything is listed there:
     right-click it > "Reset and requeue all", then right-click the queue > "Process queue".
  8. Open your website address. Done.

  Updating later: do the same again and answer "Overwrite" / "Always use this action".

PLAN B: the online File Manager (no program to install)
  In the client area open "File Manager", go into htdocs, and for each of the ${zipNames.length} files in zips\\, in order
  (part 1 first): Upload > the zip option that extracts it > pick the file > wait until it finishes.
  Each zip is under the 10 MB limit. This is slower and the file manager sometimes stops halfway on big
  archives; if a part fails, upload that part again, or use FileZilla.

Good to know (free plan)
  - Every file a visitor's browser asks for counts toward 50,000 requests a day for the whole account. Over
    that, InfinityFree switches the site off for 24 hours. Most pages here cost 5 to 35 requests on a first
    visit (measured 2026-10-04); the Gallery about 150.
  - Every visit first goes through InfinityFree's browser check. The crawlers that make link previews
    (Discord, WhatsApp, Facebook) cannot pass it, so links to this copy show without a preview card.
${
  address
    ? `  - This copy was built for ${address}: its pages, sitemap and robots.txt name that address.\n`
    : `  - This copy is a mirror: its pages tell search engines that the GitHub site
    (https://nn-exe.github.io/Pokemon-Hyper-Emerald-5.7-QoL/) is the original, so Google keeps listing that one.
    To make this copy the one Google lists, rebuild it with its address:
        cd site
        node scripts/package-infinityfree.mjs https://your-address
`
}
Rebuilding this folder after the site changes:   cd site   then   npm run package:infinityfree
`.replace(/\n/g, '\r\n'),
);

console.log(
  `\ninfinityfree/htdocs: ${files.length} files in ${folders.size} folders (${inodes} of ${LIMITS.inodes} allowed), ${mb(total)}` +
    `\n  largest HTML/JS file: ${biggestCode.name}, ${biggestCode.size.toLocaleString('en-US')} bytes (limit ${LIMITS.code.toLocaleString('en-US')})` +
    `\n  screenshots and clips taken from docs/showcase: ${used.size}` +
    `\n  ${address ? 'built for ' + address : 'a mirror: canonical links name the GitHub site'}` +
    `\ninfinityfree/zips: ${zipNames.map((n) => `${n} ${mb(fs.statSync(path.join(ZIPS, n)).size)}`).join(', ')}`,
);
