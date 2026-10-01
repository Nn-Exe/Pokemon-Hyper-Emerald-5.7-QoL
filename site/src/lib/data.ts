// The ROM-mined tables (tools/build_site_data.py), shaped for the pages that print them.

import wildRaw from '../data/wild.json';
import trainersRaw from '../data/trainers.json';
import staticRaw from '../data/static.json';
import speciesIds from '../data/species.json';
import itemIds from '../data/items.json';
import sprites from '../data/sprites.json';
import formIds from '../data/forms.json';
import { slugify } from './url';

export type Region = 'hoenn' | 'sinnoh' | 'hisui' | 'other';
export const REGIONS: Record<Region, string> = {
  hoenn: 'Hoenn',
  sinnoh: 'Sinnoh',
  hisui: 'Hisui',
  other: 'Other areas',
};

export type Slot = { sid: number; species: string; min: number; max: number; pct: number };
export type Method = 'land' | 'water' | 'rock' | 'old' | 'good' | 'super';
export const METHODS: Record<Method, string> = {
  land: 'Grass / cave',
  water: 'Surfing',
  rock: 'Rock Smash',
  old: 'Old Rod',
  good: 'Good Rod',
  super: 'Super Rod',
};
export const METHOD_SHORT: Record<Method, string> = {
  land: 'Land',
  water: 'Surf',
  rock: 'Rock Smash',
  old: 'Old Rod',
  good: 'Good Rod',
  super: 'Super Rod',
};

export type Row = Slot & { method: Method };
export type Area = {
  id: string;
  map: string;
  region: Region;
  note: string;
  rows: Row[];
  methods: Method[];
};

/** One row per species and method: the game's twelve grass slots often repeat a species. */
function merge(slots: Slot[] | undefined, method: Method): Row[] {
  const by = new Map<number, Row>();
  for (const s of slots || []) {
    const row = by.get(s.sid);
    if (row) {
      row.min = Math.min(row.min, s.min);
      row.max = Math.max(row.max, s.max);
      row.pct += s.pct;
    } else by.set(s.sid, { ...s, method });
  }
  return [...by.values()].sort((a, b) => b.pct - a.pct);
}

const usedIds = new Map<string, number>();
export const areas: Area[] = (wildRaw as any[]).map((m) => {
  const base = slugify(m.map) || 'area';
  const n = (usedIds.get(base) || 0) + 1;
  usedIds.set(base, n);
  const rows = [
    ...merge(m.land?.slots, 'land'),
    ...merge(m.water?.slots, 'water'),
    ...merge(m.rock?.slots, 'rock'),
    ...merge(m.fish?.old?.slots, 'old'),
    ...merge(m.fish?.good?.slots, 'good'),
    ...merge(m.fish?.super?.slots, 'super'),
  ];
  return {
    id: n === 1 ? base : `${base}-${n}`,
    map: m.map,
    region: m.region,
    note: m.note,
    rows,
    methods: [...new Set(rows.map((r) => r.method))],
  };
});

export type Sighting = { area: Area; method: Method; min: number; max: number; pct: number };
export type Species = { sid: number; name: string; id: string; sightings: Sighting[] };

const bySid = new Map<number, Species>();
for (const area of areas)
  for (const row of area.rows) {
    if (!row.sid) continue;
    let sp = bySid.get(row.sid);
    if (!sp) bySid.set(row.sid, (sp = { sid: row.sid, name: row.species, id: '', sightings: [] }));
    sp.sightings.push({ area, method: row.method, min: row.min, max: row.max, pct: row.pct });
  }
const usedSpecies = new Map<string, number>();
/** Every species with a wild encounter, alphabetical, each with the places it appears. */
export const wildSpecies: Species[] = [...bySid.values()]
  .sort((a, b) => a.name.localeCompare(b.name) || a.sid - b.sid)
  .map((sp) => {
    const base = slugify(sp.name);
    const n = (usedSpecies.get(base) || 0) + 1;
    usedSpecies.set(base, n);
    sp.id = n === 1 ? base : `${base}-${n}`;
    return sp;
  });
const wildBySid = new Map(wildSpecies.map((s) => [s.sid, s]));
export const wildEntry = (sid: number) => wildBySid.get(sid);

// ---- trainers ----
export type PartyMon = { sid: number; species: string; level: number; item?: string; itemId?: number; moves?: string[] };
export type Trainer = {
  id: number;
  cls: string;
  name: string;
  pic: number;
  lv?: [number, number] | null;
  double: boolean;
  where: string;
  party: PartyMon[];
  tip?: string;
};
export type TrainerGroup = { key: string; title: string; intro: string; trainers: Trainer[] };

const CLASS_NAMES: Record<string, string> = {
  'PkMn Trainer': 'Pokémon Trainer',
  'PkMn Tamer': 'Pokémon Tamer',
  'PkMn Ranger': 'Pokémon Ranger',
  'PkMn Breeder♀': 'Pokémon Breeder',
  'PkMn Breeder♂': 'Pokémon Breeder',
  TeamGalactic: 'Team Galactic',
  'Team Rainbow': 'Team Rainbow Rocket',
};
export const className = (cls: string) => CLASS_NAMES[cls] || cls;
export const trainerTitle = (t: { cls: string; name: string }) => `${className(t.cls)} ${t.name}`.trim();

export const trainerGroups = (trainersRaw as any).groups as TrainerGroup[];
export const allTrainers = (trainersRaw as any).all as Trainer[];
const trainerById = new Map<number, Trainer>();
for (const g of trainerGroups) for (const t of g.trainers) trainerById.set(t.id, t);
export const bossTrainer = (id: number) => trainerById.get(id);
export const bossCount = trainerGroups.reduce((n, g) => n + g.trainers.length, 0);

// ---- scripted encounters ----
export type StaticEncounter = {
  map: string;
  region: Region;
  sid: number;
  species: string;
  level: number;
  item?: string;
  itemId?: number;
};
export const staticEncounters = staticRaw as StaticEncounter[];

// ---- name lookups for hand-written pages ----
const norm = (s: string) => s.toLowerCase().replace(/[’']/g, "'").trim();
const speciesByName = new Map(Object.entries(speciesIds as Record<string, number>).map(([k, v]) => [norm(k), v]));
const itemByName = new Map(Object.entries(itemIds as Record<string, number>).map(([k, v]) => [norm(k), v]));

export function speciesId(name: string) {
  const id = speciesByName.get(norm(name));
  if (!id) throw new Error(`Unknown Pokémon "${name}" (see src/data/species.json)`);
  return id;
}
export function itemId(name: string) {
  const id = itemByName.get(norm(name));
  if (!id) throw new Error(`Unknown item "${name}" (see src/data/items.json)`);
  return id;
}

// ---- sprite atlases (tools/build_sprites.py) ----
export function spritePos(kind: 'mon' | 'trainer' | 'item', id: number) {
  const s = (sprites as any)[kind];
  const cell = id > 0 && id < s.count ? id : 0;
  return `--x:${cell % s.cols};--y:${Math.floor(cell / s.cols)}`;
}

export const levelRange = (min: number, max: number) => (min === max ? String(min) : `${min}–${max}`);

const formSet = new Set(formIds as number[]);
const wildForms = wildSpecies.filter((s) => formSet.has(s.sid)).length;

export const stats = {
  areas: areas.length,
  /** everything with a wild encounter: species plus regional and other alternate forms, counted separately */
  species: wildSpecies.length,
  wildBase: wildSpecies.length - wildForms,
  wildForms,
  bosses: bossCount,
  trainers: allTrainers.length,
  scripted: staticEncounters.length,
};
