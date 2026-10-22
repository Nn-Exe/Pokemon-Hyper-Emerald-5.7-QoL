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

## A second host (InfinityFree)

```
npm run package:infinityfree                                   # a mirror: canonical links name the GitHub site
node scripts/package-infinityfree.mjs https://your.address     # a site of its own: own canonical links, sitemap, robots.txt
```

Builds the same site for a domain root (`HOST_ROOT=1`, see `astro.config.mjs`) into `../infinityfree/`, which is
git-ignored: `htdocs/` is what goes into the account's `htdocs` folder by FTP, `zips/` the same in archives the
host accepts, `HOW-TO-UPLOAD.txt` the steps. The script takes only the `docs/showcase` files the pages link, writes
the `.htaccess`, and refuses to finish if the result breaks the free plan's limits (HTML and JS files 1 MB, other
files 10 MB, 30,000 files and folders). Two more limits shape the pages themselves: every request counts toward
50,000 a day, so the Pokédex index draws its cards from sheets, and no page may be heavier than 1 MB of HTML, so
the Wild Encounters rows are bare cells (`.enc` in `global.css`). Check a copy with
`node scripts/check-links.mjs ../infinityfree/htdocs ""` and look at it with
`node scripts/serve-docs.mjs 4322 ../infinityfree/htdocs ""`.

## Where things are

| Path | What it is |
| --- | --- |
| `src/content/guides/*.mdx` | One file per guide. The file name is the URL (`/guides/<name>/`). |
| `src/pages/` | The other pages: home, the guides and wiki hubs, the wiki indexes, the Pokédex (`wiki/pokedex/[slug].astro` makes one page a species), features, FAQ, changelog, gallery, about. |
| `src/data/*.json` | Generated from the ROM. Do not edit; see below. |
| `src/data/*.ts` | Hand-written: features, releases, FAQ, legendaries, gallery captions. |
| `src/components/` | Building blocks. The ones guides use are listed below. |
| `src/styles/global.css` | The whole design system, in numbered sections. Colours are tokens at the top, light and dark. |
| `src/consts.ts` | Site name, navigation, the patch version and "last updated" date. **Bump these with each release.** |
| `public/` | Icons, the social card, the sprite sheets and the Pokédex front pictures (`sprites/front/`). |
| `scripts/publish.mjs` | Copies `dist/` into `../docs`. Keeps `NOTES.md`, `DEXNAV-PROGRESS.md` and `showcase/`; writes redirects for the old `.html` page names. |

Screenshots and clips are **not** in this folder: they live in `../docs/showcase/`, which the README uses too.
`npm run dev` serves that folder at `/showcase/`, and a publish never touches it.

## Writing a guide

Guides are Markdown with a few components, available without importing anything:

```mdx
<Team id={265} />                         a boss team from the ROM (the trainer's id)
<Mon name="Rayquaza" />                   a Pokémon with its icon, linked to its Pokédex page
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
python tools/build_pokedex.py          # pokedex.json, moves.json, abilities.json (run before build_sprites.py)
python tools/build_sprites.py          # public/sprites/{mon,trainer,item}.png, front/<species>.png, front-<n>.webp
python tools/build_tm_locations.py     # tms.json: where each TM and HM is found (after build_pokedex.py)
python tools/build_mega_stones.py      # megastones.json: where each Mega Stone is found
python tools/build_guide_items.py      # guide-items.json: the Z-Crystals with their Totems, and the Plates
python tools/build_berries.py          # berries.json: every Berry, its trees, gifts, daily givers, shops, wild holders
python tools/build_spot_maps.py        # public/spots/*.webp, spots.json: a picture of each spot (after the four above)
python tools/build_site_content.py     # journal.json (patches/journal/steps.py, Area Zero's rows from patches/paldea), side-content.json
python tools/build_site_images.py      # favicon, touch icon and the social card
FFMPEG=<path> python tools/build_clips.py   # docs/showcase/clips from the README montage GIFs and the GIF editor's v1.9 one
                                            # (--only v1.9: that montage alone, the other clips left as they are)
```

Every tool finds the game's tables through `tools/romdata/tables.py`: up to v1.8 they sit at fixed addresses; v1.9
(the whole of Gen 9) moved the species tables to 1,408 slots elsewhere, and the move descriptions, egg moves and
Pokédex entries too. It reads each address from the words the game itself uses and checks it, so the same tools
read v1.8 and v1.9, and a build that moves them again stops instead of giving the site wrong data.

The names the site prints for alternate forms (Alolan, Hisuian, Mega, Gigantamax…) and for names the ROM cuts
short are in `tools/romdata/species_display.py` and `display_names.py`; how each form comes about (Mega Stones, Max
Soup, held items, moves, abilities, Bag items) is read by `tools/romdata/forms.py`, which `build_pokedex.py` uses.

The tools read the ROM of the version the site describes: v1.9 since 2026-10-16 (the working ROM of that day,
sha1 65b5a7f6..., snapshotted in `gba-trans/_testrun/site19/hyper19.gba`), before that v1.8's release ROM. Run them
with `HE_ROMDATA_OUT` pointing at a scratch folder. `item_sources.py` gives the
tile of whatever lies on the ground, `build_spot_maps.py` draws the map around it with the object on it, and the
pages show the picture (`<Spot>`; the guide's lists are `<MegaStoneList />`, `<TotemList />` and
`<ItemPlaceList />`). Two things about this hack that the scan has to know: it draws its own objects through a
second sprite table (graphics 0x4E; a Mega Stone and a TM are two of them, and through the vanilla table they look
like nothing at all), and it keeps a good many objects parked where nobody can walk, scripts and all.

`build_tm_locations.py` finds the TMs and HMs itself (item balls, gifts, Game Corner prizes, shop lists) but not
what a gift asks of the player: that is one line a gift in its `NOTES`, written from the script's dialogue, and
the tool stops, quoting the dialogue, when a ROM has a gift without one. Its place names are pret's for the
maps vanilla Emerald has (`tools/romdata/map_names.json`) and the map section's for the hack's own; `PLACES`
overrides either.

## Scope

The site documents the public game: since 2026-10-16 v1.9, with Gen 9 and Area Zero (the user: "Yes, both
public"), ahead of its patch file (`RELEASED_VERSION` in `src/consts.ts` names the version the repository's patch
file builds; while it is behind `PATCH_VERSION` the home, Features, Changelog and Install pages say so).
`tools/build_site_data.py` keeps trainer slots 943, 947 and 952 only when they hold Area Zero's trainers
(`AREA_ZERO_SLOTS`); keep unreleased content out of the guides, the gallery and the changelog.
