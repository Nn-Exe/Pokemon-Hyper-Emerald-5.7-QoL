// Screenshots and clips live in ../docs/showcase and are served from <base>/showcase/.
// This reads their pixel size at build time so every <img> reserves its space.

import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import clipsRaw from '../data/clips.json';

const SHOWCASE = path.resolve(process.cwd(), '../docs/showcase');
const PUBLIC = path.resolve(process.cwd(), 'public');

const sizes = new Map<string, { width: number; height: number }>();

export function imageSize(file: string) {
  let size = sizes.get(file);
  if (size) return size;
  const full = path.join(SHOWCASE, file);
  if (!fs.existsSync(full)) throw new Error(`Missing showcase image: ${file}`);
  const head = Buffer.alloc(24);
  const fd = fs.openSync(full, 'r');
  fs.readSync(fd, head, 0, 24, 0);
  fs.closeSync(fd);
  if (head.toString('latin1', 1, 4) === 'PNG') size = { width: head.readUInt32BE(16), height: head.readUInt32BE(20) };
  else if (head.toString('latin1', 0, 3) === 'GIF') size = { width: head.readUInt16LE(6), height: head.readUInt16LE(8) };
  else throw new Error(`Unsupported image type: ${file}`);
  sizes.set(file, size);
  return size;
}

export type Clip = { slug: string; caption: string; group: string; width: number; height: number };
export const clips = clipsRaw as Clip[];
const clipBySlug = new Map(clips.map((c) => [c.slug, c]));

export function clip(slug: string) {
  const c = clipBySlug.get(slug);
  if (!c) throw new Error(`Unknown clip "${slug}" (see src/data/clips.json)`);
  return c;
}

export const clipGroups = [...new Set(clips.map((c) => c.group))];

/** Short content hash of a file in public/, so a changed sprite sheet is not served from cache. */
export function publicHash(file: string) {
  return crypto.createHash('sha1').update(fs.readFileSync(path.join(PUBLIC, file))).digest('hex').slice(0, 8);
}
