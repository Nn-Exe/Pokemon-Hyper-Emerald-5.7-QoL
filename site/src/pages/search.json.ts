// The index behind the search dialog: one small JSON file, fetched the first time search opens.
// t type · n name · s sub-line · u URL under the site base · i sprite cell · k extra keywords

import type { APIRoute } from 'astro';
import { render } from 'astro:content';
import { allGuides } from '../lib/guides';
import {
  areas,
  trainerGroups,
  staticEncounters,
  trainerTitle,
  levelRange,
  speciesId,
  REGIONS,
  METHOD_SHORT,
} from '../lib/data';
import { slugify } from '../lib/url';
import {
  species,
  moves,
  abilities,
  machines,
  megaStones,
  wildSightings,
  dexNo,
  pokedexHref,
  moveHref,
  abilityHref,
  machineHref,
  megaStoneHref,
} from '../lib/pokedex';
import { LEGEND_GROUPS } from '../data/legendaries';
import { FEATURES } from '../data/features';
import { FAQ_GROUPS } from '../data/faq';
import journal from '../data/journal.json';
import guideItems from '../data/guide-items.json';
import berryData from '../data/berries.json';

type Entry = { t: string; n: string; s: string; u: string; i?: number; k?: string };

const PAGES: Entry[] = [
  { t: 'Page', n: 'Guides', s: 'Walkthrough, getting started and reference guides', u: 'guides/' },
  { t: 'Page', n: 'Wiki', s: 'Pokédex, moves, TM locations, abilities, encounters, trainers and scripted battles', u: 'wiki/' },
  { t: 'Page', n: 'Pokédex', s: 'Every Pokémon: stats, abilities, evolutions, locations and moves', u: 'wiki/pokedex/', k: 'pokedex dex species' },
  { t: 'Page', n: 'Moves', s: 'Every move: type, power, accuracy, PP and effect', u: 'wiki/moves/', k: 'attacks tm hm' },
  { t: 'Page', n: 'TMs & HMs', s: 'Where to find every TM and HM', u: 'wiki/tms/', k: 'tm hm technical hidden machine locations' },
  { t: 'Page', n: 'Berries', s: 'Where to get every Berry: trees, gifts, shops and wild Pokémon', u: 'wiki/berries/', k: 'berry berries tree plant' },
  { t: 'Page', n: 'Abilities', s: 'Every ability and the Pokémon that have it', u: 'wiki/abilities/', k: 'hidden ability' },
  { t: 'Page', n: 'Wild Encounters', s: 'Every encounter table by location', u: 'wiki/encounters/' },
  { t: 'Page', n: 'Pokémon Finder', s: 'Where to find each wild Pokémon', u: 'wiki/pokemon/' },
  { t: 'Page', n: 'Trainer Battles', s: 'Boss teams with levels, items and moves', u: 'wiki/trainers/', k: 'gym leaders elite four champion' },
  { t: 'Page', n: 'Every Trainer', s: 'The complete trainer table', u: 'wiki/trainers/all/' },
  { t: 'Page', n: 'Scripted Encounters', s: 'Every fixed wild battle', u: 'wiki/scripted-encounters/', k: 'static legendary totem' },
  { t: 'Page', n: 'Features', s: 'What the English + QoL patch adds', u: 'features/', k: 'qol quality of life patch' },
  { t: 'Page', n: 'FAQ', s: 'Patching, saves, controls and known issues', u: 'faq/', k: 'help problems questions' },
  { t: 'Page', n: 'Changelog', s: 'Every release of the patch', u: 'changelog/', k: 'version history update' },
  { t: 'Page', n: 'Gallery', s: 'Gameplay clips and screenshots', u: 'gallery/', k: 'screenshots videos' },
  { t: 'Page', n: 'About & Credits', s: 'Who made the hack, the patch and this guide', u: 'about/', k: 'credits sources' },
];

const clean = (text: string) =>
  text
    .replace(/<[^>]+>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
const clipText = (text: string, max = 110) => (text.length > max ? text.slice(0, max - 1).trimEnd() + '…' : text);

export const GET: APIRoute = async () => {
  const entries: Entry[] = [...PAGES];

  for (const g of await allGuides()) {
    entries.push({ t: 'Guide', n: g.data.title, s: g.data.description, u: `guides/${g.id}/`, k: g.data.category });
    const { headings } = await render(g);
    for (const h of headings.filter((x) => x.depth <= 3))
      entries.push({ t: 'Guide', n: h.text, s: g.data.title, u: `guides/${g.id}/#${h.slug}` });
  }

  for (const sp of species) {
    const places = wildSightings(sp).length;
    entries.push({
      t: 'Pokémon',
      n: sp.name,
      s: [dexNo(sp), sp.types.join(' / '), places ? `found in ${places} ${places === 1 ? 'place' : 'places'}` : '']
        .filter(Boolean)
        .join(' · '),
      u: pokedexHref(sp).slice(1),
      i: sp.sid,
    });
  }

  for (const m of moves)
    entries.push({
      t: 'Move',
      n: m.name,
      s: [m.type, m.cat, m.power > 1 ? `Power ${m.power}` : '', m.tm ?? ''].filter(Boolean).join(' · '),
      u: moveHref(m).slice(1),
      k: m.desc,
    });

  // a machine: found first where it is free, the shops last
  for (const t of machines)
    entries.push({
      t: 'TM',
      n: `${t.label} ${t.move.name}`,
      s: clipText([...new Set(t.sources.map((x) => x.place))].join(', ')),
      u: machineHref(t.label).slice(1),
      k: `${t.label.slice(0, 2)} ${Number(t.label.slice(2))} ${t.move.type}`,
    });

  for (const b of berryData.berries)
    entries.push({
      t: 'Berry',
      n: b.name,
      s: clipText([...new Set(b.sources.filter((x: any) => x.place).map((x: any) => x.place))].join(', ')),
      u: `wiki/berries/#${slugify(b.name)}`,
      i: b.item,
      k: `berry no ${b.no} ${b.desc}`,
    });

  for (const st of megaStones)
    entries.push({
      t: 'Mega Stone',
      n: st.name,
      s: clipText([...new Set(st.sources.map((x) => x.place))].join(', ')),
      u: megaStoneHref(st).slice(1),
      k: 'mega stone location where',
    });

  for (const t of guideItems.totems)
    entries.push({
      t: 'Z-Crystal',
      n: t.name,
      s: clipText(`Totem · ${[...new Set(t.entrances.map((e) => e.place))].join(', ')}`),
      u: `guides/mega-stones-key-items/#${slugify(t.name)}`,
      k: 'z crystal totem location where',
    });
  for (const [type, list] of [['Z-Crystal', guideItems.crystals], ['Plate', guideItems.plates]] as const)
    for (const r of list)
      entries.push({
        t: type,
        n: r.name,
        s: clipText([...new Set(r.sources.map((x) => x.place))].join(', ')),
        u: `guides/mega-stones-key-items/#${slugify(r.name)}`,
        k: 'location where',
      });

  for (const a of abilities) entries.push({ t: 'Ability', n: a.name, s: a.desc, u: abilityHref(a).slice(1) });

  for (const a of areas)
    entries.push({
      t: 'Location',
      n: a.note ? `${a.map} (${a.note.toLowerCase()})` : a.map,
      s: `${REGIONS[a.region]} · ${a.methods.map((m) => METHOD_SHORT[m]).join(', ')}`,
      u: `wiki/encounters/#${a.id}`,
    });

  for (const g of trainerGroups)
    for (const t of g.trainers)
      entries.push({
        t: 'Trainer',
        n: trainerTitle(t),
        s: [t.where, t.lv ? `Lv ${levelRange(t.lv[0], t.lv[1])}` : '', g.title].filter(Boolean).join(' · '),
        u: `wiki/trainers/#t-${t.id}`,
        i: t.pic,
      });

  for (const g of LEGEND_GROUPS)
    for (const l of g.legends)
      entries.push({
        t: 'Legendary',
        n: l.name,
        s: clipText(l.where),
        u: `guides/legendaries/#${slugify(l.name)}`,
        i: speciesId(l.mons[0]),
        k: l.mons.join(' '),
      });

  const seen = new Set<string>();
  for (const s of staticEncounters) {
    const key = `${s.sid}|${s.map}`;
    if (seen.has(key)) continue;
    seen.add(key);
    entries.push({
      t: 'Encounter',
      n: s.species,
      s: `Scripted battle · ${s.map} · Lv ${s.level}`,
      u: `wiki/scripted-encounters/?q=${encodeURIComponent(s.species)}`,
      i: s.sid,
    });
  }

  for (const c of journal.chapters)
    for (const s of c.steps)
      entries.push({
        t: 'Journal',
        n: s.title,
        s: `Objective ${s.n} · ${c.title}`,
        u: `guides/journal/#step-${s.n}`,
        k: clipText(s.text, 160),
      });

  for (const s of FEATURES)
    for (const c of s.cards)
      entries.push({ t: 'Feature', n: c.title, s: clipText(c.text), u: `features/#${s.id}`, k: s.nav });

  for (const g of FAQ_GROUPS)
    for (const i of g.items)
      entries.push({ t: 'FAQ', n: i.q, s: clipText(clean(i.a)), u: `faq/#${slugify(i.q)}` });

  return new Response(JSON.stringify(entries), { headers: { 'Content-Type': 'application/json; charset=utf-8' } });
};
