# The guide site

Source of the player's guide at **https://nn-exe.github.io/Pokemon-Hyper-Emerald-5.7-QoL/**.
It is an [Astro](https://astro.build) project that builds to plain static files. GitHub Pages serves the
repository's `docs/` folder, so a build ends by copying the result there.

```
npm install        # once (Node 22.12 or newer)
npm run dev        # work on it at http://localhost:4321/Pokemon-Hyper-Emerald-5.7-QoL/
npm run build      # build, then copy into ../docs (what gets published)
npm run preview    # serve ../docs exactly as GitHub Pages does
npm run check      # every internal link, image, anchor and search entry resolves
```

Commit `docs/` together with the source: the published site is whatever is in `docs/` on the default branch.

## Where things are

| Path | What it is |
| --- | --- |
| `src/content/guides/*.mdx` | One file per guide. The file name is the URL (`/guides/<name>/`). |
| `src/pages/` | The other pages: home, the guides and wiki hubs, the wiki indexes, features, FAQ, changelog, gallery, about. |
| `src/data/*.json` | Generated from the ROM. Do not edit; see below. |
| `src/data/*.ts` | Hand-written: features, releases, FAQ, legendaries, gallery captions. |
| `src/components/` | Building blocks. The ones guides use are listed below. |
| `src/styles/global.css` | The whole design system, in numbered sections. Colours are tokens at the top, light and dark. |
| `src/consts.ts` | Site name, navigation, the patch version and "last updated" date. **Bump these with each release.** |
| `public/` | Icons, the social card and the sprite sheets. |
| `scripts/publish.mjs` | Copies `dist/` into `../docs`. Keeps `NOTES.md`, `DEXNAV-PROGRESS.md` and `showcase/`; writes redirects for the old `.html` page names. |

Screenshots and clips are **not** in this folder: they live in `../docs/showcase/`, which the README uses too.
`npm run dev` serves that folder at `/showcase/`, and a publish never touches it.

## Writing a guide

Guides are Markdown with a few components, available without importing anything:

```mdx
<Team id={265} />                         a boss team from the ROM (the trainer's id)
<Mon name="Rayquaza" />                   a Pokémon with its icon; links to the finder if it is found in the wild
<Item name="Mega Bracelet" />             an item with its Bag icon; label="…" changes the text
<Key>R</Key>                              a GBA button
<Callout type="warn" title="…">…</Callout>   tip (default) · warn · info · danger · plain
<Clip slug="dexnav-screen" />             a gameplay clip from src/data/clips.json
<Shot src="journal.png" alt="…" caption="…" />   a screenshot from docs/showcase, opens in the viewer
<Tag type="warn">community</Tag>          a small label
<Stage>Badge 1 · cap Lv 18</Stage>        the line under a walkthrough stage heading
```

A wrong Pokémon, item, trainer or clip name stops the build with a message that says which one. Write internal
links root-relative (`/wiki/encounters/`); the site's base path is added for you.

## Regenerating the data

The tables and sprites come from the patched ROM. From the repository root, with `HE_ROM` set to the ROM:

```
python tools/romdata/dump_tables.py && python tools/romdata/dump_maps.py && python tools/romdata/dump_trainers.py
python tools/romdata/scan_wild.py && python tools/romdata/scan_static.py && python tools/romdata/make_key_trainers.py
python tools/build_site_data.py        # wild.json, trainers.json, static.json, species.json, items.json
python tools/build_sprites.py          # public/sprites/{mon,trainer,item}.png
python tools/build_site_content.py     # journal.json (from patches/journal/steps.py), side-content.json
python tools/build_site_images.py      # favicon, touch icon and the social card
FFMPEG=<path> python tools/build_clips.py   # docs/showcase/clips from the six README montage GIFs
```

The names the site prints for alternate forms (Alolan, Hisuian, Mega, Gigantamax…) and for names the ROM cuts
short are in `tools/romdata/species_display.py` and `display_names.py`.

## Scope

The site documents the public release. `tools/build_site_data.py` leaves out the trainer slots the release does
not use (`UNRELEASED_TRAINERS`); keep unreleased content out of the guides, the gallery and the changelog too.
