// The Pokédex, moves and abilities mined from the ROM (tools/build_pokedex.py).

import raw from '../data/pokedex.json';
import movesRaw from '../data/moves.json';
import abilitiesRaw from '../data/abilities.json';
import { slugify, url } from './url';
import { wildEntry, staticEncounters, speciesId, type Sighting } from './data';
import { LEGEND_GROUPS } from '../data/legendaries';

export type FormKind = 'Standard' | 'Mega' | 'Gigantamax' | 'Regional' | 'Form';
export type Evolution = { to: number; how: string; text: string };
export type Species = {
  sid: number;
  name: string;
  slug: string;
  dex: number;
  form: FormKind;
  types: string[];
  /** HP, Attack, Defense, Sp. Atk, Sp. Def, Speed */
  stats: number[];
  abilities: number[];
  hidden: number;
  catch: number;
  exp: number;
  ev: string[];
  gender: number;
  eggCycles: number;
  friendship: number;
  growth: string;
  eggGroups: string[];
  items: { id: number; name: string; rate: string }[];
  category?: string;
  height?: number;
  weight?: number;
  entry?: string;
  evo?: Evolution[];
  forms?: { to: number; how: string }[];
  /** [level, move]; level 0 is learned on evolving */
  levelUp: [number, number][];
  /** indexes into TMS */
  tm: number[];
  egg: number[];
};
export type Move = {
  id: number;
  name: string;
  type: string;
  cat: 'Physical' | 'Special' | 'Status';
  power: number;
  acc: number;
  pp: number;
  desc: string;
  tm?: string;
  slug: string;
};
export type Ability = { id: number; name: string; desc: string; slug: string };

export const STAT_LABELS = ['HP', 'Attack', 'Defense', 'Sp. Atk', 'Sp. Def', 'Speed'];
export const TYPE_LIST = [
  'Normal', 'Fire', 'Water', 'Electric', 'Grass', 'Ice', 'Fighting', 'Poison', 'Ground',
  'Flying', 'Psychic', 'Bug', 'Rock', 'Ghost', 'Dragon', 'Dark', 'Steel', 'Fairy',
];

const everything = (raw as any).species as Species[];
export const TMS = (raw as any).tm as { label: string; move: number }[];

// Two slots the game keeps twice over (Ultra Necrozma from either fusion, a second Enamorus) share one page,
// and so do Unown's letters.
const bySid = new Map<number, Species>();
const byIdentity = new Map<string, Species>();
export const species: Species[] = [];
for (const s of everything) {
  const key = `${s.dex}|${s.name}`;
  const first = byIdentity.get(key);
  if (first) bySid.set(s.sid, first);
  else {
    byIdentity.set(key, s);
    bySid.set(s.sid, s);
    species.push(s);
  }
}
const UNOWN = 201;
for (let sid = 413; sid <= 439; sid++) if (bySid.has(UNOWN)) bySid.set(sid, bySid.get(UNOWN)!);

export const speciesBySid = (sid: number) => bySid.get(sid);
export const pokedexHref = (s: Species) => `/wiki/pokedex/${s.slug}/`;
/** Link to a species' Pokédex page, or undefined for ids the Pokédex leaves out. */
export const pokedexUrl = (sid: number) => {
  const s = bySid.get(sid);
  return s ? url(pokedexHref(s)) : undefined;
};
export const frontSprite = (sid: number, shiny = false) => url(`/sprites/front/${sid}${shiny ? 's' : ''}.png`);
export const dexNo = (s: Species) => '#' + String(s.dex).padStart(3, '0');
export const bst = (s: Species) => s.stats.reduce((a, b) => a + b, 0);

// ---- moves and abilities ----
function withSlugs<T extends { name: string }>(list: T[]): (T & { slug: string })[] {
  const used = new Map<string, number>();
  return list.map((x) => {
    const base = slugify(x.name) || 'x';
    const n = (used.get(base) || 0) + 1;
    used.set(base, n);
    return { ...x, slug: n === 1 ? base : `${base}-${n}` };
  });
}
export const moves = withSlugs(movesRaw as Omit<Move, 'slug'>[]) as Move[];
export const abilities = withSlugs(abilitiesRaw as Omit<Ability, 'slug'>[]) as Ability[];
const moveById = new Map(moves.map((m) => [m.id, m]));
const abilityById = new Map(abilities.map((a) => [a.id, a]));
export const move = (id: number) => moveById.get(id);
export const ability = (id: number) => abilityById.get(id);
export const moveHref = (m: Move) => `/wiki/moves/#${m.slug}`;
export const abilityHref = (a: Ability) => `/wiki/abilities/#${a.slug}`;

/** Who has each ability: [regular holders, hidden-ability holders]. */
export const abilityHolders = new Map<number, { regular: Species[]; hidden: Species[] }>();
for (const s of species) {
  for (const a of s.abilities) {
    if (!abilityHolders.has(a)) abilityHolders.set(a, { regular: [], hidden: [] });
    abilityHolders.get(a)!.regular.push(s);
  }
  if (s.hidden) {
    if (!abilityHolders.has(s.hidden)) abilityHolders.set(s.hidden, { regular: [], hidden: [] });
    abilityHolders.get(s.hidden)!.hidden.push(s);
  }
}

// ---- evolution families ----
type FormLink = { to: number; how: string };
const parents = new Map<number, { from: number; how: string; text: string }>();
for (const s of species)
  for (const e of s.evo || []) {
    const to = bySid.get(e.to)?.sid;
    if (to && to !== s.sid && !parents.has(to)) parents.set(to, { from: s.sid, how: e.how, text: e.text });
  }

// Mega Evolutions, Primal Reversions and Gigantamax forms hang off their base species. The game links them itself
// (the Mega rows of its evolution table, and its battle-form table for Gigantamax); a form neither table names,
// Eternamax Eternatus, is matched by name, then by National Dex number.
const formLinks = new Map<number, FormLink[]>();
const baseOf = new Map<number, { from: number; how: string }>();
const link = (from: number, to: number, how: string) => {
  if (baseOf.has(to) || from === to) return;
  baseOf.set(to, { from, how });
  formLinks.set(from, [...(formLinks.get(from) || []), { to, how }]);
};
for (const s of species)
  for (const f of s.forms || []) {
    const to = bySid.get(f.to)?.sid;
    if (to) link(s.sid, to, f.how);
  }
for (const s of species) {
  if ((s.form !== 'Mega' && s.form !== 'Gigantamax') || baseOf.has(s.sid)) continue;
  const plain = s.name.replace(/^(Gigantamax|Eternamax|Mega|Primal) /, '');
  const base =
    species.find((o) => o.name === plain) ||
    species.find((o) => o.dex === s.dex && o.form === 'Standard') ||
    species.find((o) => o.dex === s.dex && o.form !== 'Mega' && o.form !== 'Gigantamax');
  if (base) link(base.sid, s.sid, s.form === 'Gigantamax' ? 'Gigantamax' : 'Mega Evolution');
}
export const formsOf = (s: Species) => formLinks.get(s.sid) || [];
/** The species a Mega or Gigantamax form comes from, and what triggers it. */
export const baseForm = (s: Species) => {
  const b = baseOf.get(s.sid);
  return b ? { species: bySid.get(b.from)!, how: b.how } : undefined;
};

/** The first stage of the line a species belongs to (a Mega or Gigantamax form belongs to its base's line). */
export function familyRoot(sid: number): number {
  const self = bySid.get(sid)?.sid ?? sid;
  let cur = baseOf.get(self)?.from ?? self;
  const seen = new Set<number>();
  while (parents.has(cur) && !seen.has(cur)) {
    seen.add(cur);
    cur = parents.get(cur)!.from;
  }
  return cur;
}

/** The steps from the first stage to this species: [{ from, to, how, text }], empty for a first stage. */
export function lineage(sid: number) {
  const steps: { from: Species; to: Species; how: string; text: string }[] = [];
  let cur = bySid.get(sid)?.sid ?? sid;
  const seen = new Set<number>();
  while (parents.has(cur) && !seen.has(cur)) {
    seen.add(cur);
    const p = parents.get(cur)!;
    steps.unshift({ from: bySid.get(p.from)!, to: bySid.get(cur)!, how: p.how, text: p.text });
    cur = p.from;
  }
  return steps;
}

export type FamilyNode = {
  species: Species;
  /** how its parent turns into it */
  how?: string;
  text?: string;
  kind: 'root' | 'evolution' | 'form';
  children: FamilyNode[];
};

export function family(sid: number): FamilyNode | undefined {
  const root = bySid.get(familyRoot(sid));
  if (!root) return undefined;
  const seen = new Set<number>();
  const build = (s: Species, kind: FamilyNode['kind'], how?: string, text?: string): FamilyNode => {
    seen.add(s.sid);
    const children: FamilyNode[] = [];
    // the same target reached two ways (Leafeon: a place or a stone) is one branch with both ways named
    const ways = new Map<number, Evolution[]>();
    for (const e of s.evo || []) {
      const to = bySid.get(e.to)?.sid;
      if (to) ways.set(to, [...(ways.get(to) || []), e]);
    }
    for (const [to, list] of ways) {
      const t = bySid.get(to);
      if (t && !seen.has(to))
        children.push(
          build(t, 'evolution', [...new Set(list.map((e) => e.how))].join(' or '), list.map((e) => e.text).join(' Or: ')),
        );
    }
    for (const f of formsOf(s)) {
      const t = bySid.get(f.to);
      if (t && !seen.has(t.sid)) children.push(build(t, 'form', f.how));
    }
    return { species: s, how, text, kind, children };
  };
  const tree = build(root, 'root');
  return tree.children.length ? tree : undefined;
}

export function familyMembers(node: FamilyNode | undefined, into = new Set<number>()) {
  if (node) {
    into.add(node.species.sid);
    for (const c of node.children) familyMembers(c, into);
  }
  return into;
}

/** Other entries that share a National Dex number: regional forms, Megas, alternate forms. */
export function otherForms(s: Species) {
  return species.filter((o) => o.dex === s.dex && o.sid !== s.sid);
}

// ---- where to get one ----
const sidsOf = new Map<number, number[]>();
for (const [sid, s] of bySid) sidsOf.set(s.sid, [...(sidsOf.get(s.sid) || []), sid]);
const idsOf = (s: Species) => sidsOf.get(s.sid) || [s.sid];

export function wildSightings(s: Species): Sighting[] {
  return idsOf(s)
    .flatMap((sid) => wildEntry(sid)?.sightings ?? [])
    .sort((a, b) => b.pct - a.pct);
}
export function scriptedBattles(s: Species) {
  const ids = new Set(idsOf(s));
  return staticEncounters.filter((e) => ids.has(e.sid));
}
/** The entries of the Legendary Locations guide that name this species. */
export function legendEntries(s: Species) {
  const ids = new Set(idsOf(s));
  return LEGEND_GROUPS.flatMap((g) => g.legends).filter((l) => l.mons.some((m) => ids.has(speciesId(m))));
}
/** Can it be met in the game: a wild encounter, a scripted battle or a legendary's own event. */
export const obtainableDirectly = (s: Species) =>
  wildSightings(s).length > 0 || scriptedBattles(s).length > 0 || legendEntries(s).length > 0;

export function genderText(ratio: number) {
  if (ratio === 255) return 'Genderless';
  if (ratio === 254) return 'Always female';
  if (ratio === 0) return 'Always male';
  const female = (Math.round((ratio / 254) * 8) / 8) * 100;
  return `${100 - female}% male, ${female}% female`;
}

const dexNumbers = new Set(species.map((s) => s.dex)).size;
export const dexStats = {
  /** every page in the Pokédex: species and their forms */
  total: species.length,
  /** National Dex numbers: Bulbasaur to Enamorus */
  species: dexNumbers,
  forms: species.length - dexNumbers,
  megas: species.filter((s) => s.form === 'Mega').length,
  gigantamax: species.filter((s) => s.form === 'Gigantamax').length,
  regional: species.filter((s) => s.form === 'Regional').length,
  hidden: species.filter((s) => s.hidden).length,
  moves: moves.length,
  abilities: abilities.length,
};

export const typeClass = (type: string) => 't-' + type.toLowerCase();
export const heightText = (dm: number) => `${(dm / 10).toFixed(1)} m`;
export const weightText = (hg: number) => `${(hg / 10).toFixed(1)} kg`;
