# Hyper Emerald v5.7 (Full English Modern) - ROM data-mining summary

ROM: `Pokemon Hyper Emerald v5.7 - Full English Modern.gba` (32 MB, code BPEE).
All scripts and outputs live in this folder (`romdata/`). Every script is re-runnable with plain Python 3
(`python <script>.py`; set `PYTHONIOENCODING=utf-8` on Windows). `romlib.py` holds the ROM path, the Gen 3
charmap decoder and helpers; the other scripts import it. Nothing in the workspace was modified.

## Verified table addresses (ROM addresses; 0x08xxxxxx = file offset 0x0xxxxxx)

| Table | Address | Layout / count | How verified |
|---|---|---|---|
| gSpeciesNames | **0x08F2B790** | 11 bytes/name; 1200 entries dumped. 0..989 are the 990 "real" species (incl. Egg #412, Unown forms 413-439); 994..1199 are form names (Rotom forms 958-959, Kyurem-W/B 995-996, Zacian/Zamazenta/Eternatus 1190-1195, Galarian Zigzagoon 1101, ...). 6 entries still Chinese (990-993, 1025). | Bulbasaur=1, Pikachu=25, Mew=151, Celebi=251, **Treecko=277, Rayquaza=406, Chimecho=411** - i.e. vanilla Emerald INTERNAL ids (252-276 are fillers named Charizard...Toxtricity in this hack). Referenced by code literals at 0x144, 0x1644C, 0x17BE4, 0x17F28, ... |
| gTrainerClassNames | **0x0830FCD4** | 13 bytes/name; 71 classes (0..70; 71+ junk) | Hiker=2, Expert=10, Elite Four=31, Leader=32, Youngster=37, Champion=38, Lass=54 = vanilla ids. 0x53/0x54 = PK/MN glyphs. New classes 65-70: TeamGalactic, Scientist, Team Rocket, Team Plasma, Team Flare, Lorekeeper; class 1 renamed "Team Rainbow". Referenced from 0x183B4, 0x6F0AC, 0x14F5B0, ... |
| gTrainers | **0x090019F8** | 40 bytes/entry; **1459 entries (0..1458)**. 38 slots are junk/unused (902-909, 911-918, 921, 931, 940, 943, 947, 957, 958, 1023, 1024, 1080, 1113, 1178, 1190, 1197, 1211, 1296-1301, 1455) and are flagged `invalid` in trainers.json. | Vanilla ids hold: Roxanne=265, Brawly=266, Norman=269, Sidney=261, Roxanne rematch=770 (= 261+509, exactly vanilla). Referenced from 0x3587C, 0x36320, 0x36480, ... (vanilla battle code). Struct is vanilla (`partyFlags, class, encMusic/gender, pic, name[12], u16 items[4], u8 double, pad, u32 aiFlags, u8 partySize, pad, ptr party`). Party entry = 8 bytes `{u16 iv, u16 lvl, u16 species, u16 item/pad}` or 16 bytes with `u16 moves[4]` when partyFlags bit0 is set; bit1 = held item (vanilla rules; 0 sanity failures across all 1421 valid trainers). Chinese-encoded trainer names are kept as `{CNxxxx}` tokens. |
| gItems | **0x08FC2C7C** | 44 bytes/entry (vanilla ItemStruct: name[14], u16 id, u16 price, ..., pocket at +26); 800 entries dumped. Real items are 0..768 (768 = "Sinnoh Pager"); 769-799 are "New Item" placeholders; 754-767 still have Chinese names; 32 entries are "??????" placeholders (glyph 0x3D, e.g. 72, 82, 114-117). The struct's `id` field is not reliable (513 Griseous Core has id 0), so the JSON key is the table index - which is what trainer/script data uses. | Master Ball=1, Potion=13, Rare Candy=68, Max Repel=84 (matches NOTES). TM/HM block ~378-500, memories/mega stones 600-700. Referenced from 0x1C8, 0xD7490, 0xD74B4, ... |
| gMoveNames | **0x09D30258** | 13 bytes/name; 937 entries (0..936; 937 is Chinese junk) | Pound=1, Tackle=33, Psycho Boost=354, Roost=355 (Gen 4+ ids), Max moves at the end. Referenced from 0x148, 0x59B14, ... |
| gRegionMapEntries | **0x085A147C** | 8 bytes `{x,y,w,h,ptr name}`; **213 entries** (0xD5, same count as vanilla) | Littleroot Town=0 ... Ever Grande=15, Route 101-134 = 16-49, Underwater=50. The vanilla dummy sections 51-212 were renamed to Sinnoh/extra areas (Route 209/210, Solaceon, Mt. Silver=66, Jubilife=91, Sinnoh League, Hisui Region, Distortion World, Spear Pillar, Lake Verity/Valor/Acuity, ...). Referenced from 0x123B44, 0x123D54, 0x12459C, 0x124654, 0x13D814. |
| gMapGroups | **0x08A54698** | 38 group pointers: 34 vanilla groups at 0x08485D60..0x08486574 plus 4 new ones - 34 @0x08B07CC8 (96 maps), 35 @0x08AFED4C (89), 36 @0x08B0C4E8 (97), 37 @0x08B0F1B4 (122). **922 maps total.** | Found by a structural scan (map header -> layout/events sanity, `scan_maps.py`) then a pointer search; referenced from code at 0x84AA4. Cross-check: map 13/20 (Lilycove Dept. Store 5F) object 4 script = 0x0822000A, exactly as in NOTES. Header layout is vanilla (`layout, events, scripts, connections, u16 music, u16 layoutId, u8 mapsec, u8 cave, u8 weather, u8 mapType, pad, u8 flags, u8 battleType`). 4 maps have a null events pointer. |
| gWildMonHeaders | **0x08E17D50** | 20 bytes `{group, num, pad, land, water, rock, fishing}`; **254 entries**, FF FF terminator at 0x08E19128. Slot arrays are vanilla `{u8 min, u8 max, u16 species}` with 12/5/5/10 slots; slot % from the vanilla rate tables. | Referenced from the vanilla wild_encounter code (0xB4D48, 0xB5438, 0xB54D8, 0xB5560, 0xB567C, 0xB56DC, 0xB5728, 0xB579C, 0xB57DC, 0xB5864, 0x13CC78, 0x13CCB4, 0x196C50). Route 101 land = Zigzagoon/Poochyena/Nidoran/Wurmple/Weedle/Caterpie/Bulbasaur/Lillipup... Lv 2-5. 4 slots in the ROM have min>max (Seafloor Cavern, Victory Road) - swapped and annotated. Altering Cave (24/106) has 9 headers = vanilla-style variants (tagged `variant`). Some rock-smash rates are >100 (155/170) - left as-is. A stale partial copy exists at 0x099C18EC (unreferenced), and a 7-entry Lv5 Bulbasaur-line placeholder table at 0x08553894 (referenced from 0xB5398/0xB5628; dumped as `wild_extra_0x08553894.json`). |

Species-id note for the website: ids <= 251 are national-dex ids; Hoenn species use vanilla internal ids
(Treecko 277 ... Chimecho 411, Egg 412, Unown forms 413-439); Gen 4+ species follow from ~440 in the hack's own
order (Riolu 500, Whimsicott 600, Keldeo 700, Mareanie 800, Thundurus 900, Basculin 989). Always map ids through
`species.json`.

## Deliverables (all in this folder)

| File | Content |
|---|---|
| `mapsections.json` | 213 region-map sections: id -> {name, x, y, w, h} |
| `maps.json` | 922 maps: group, num, header addr, mapsec id/name, mapType, weather, music id, layoutId, cave, flags, battleType, width/height, layout/events/scripts pointers |
| `wild.json` | 254 encounter headers (246 distinct maps; 218 land, 102 water, 9 rock-smash, 88 fishing tables): mapsec + group/num + land/water/rock/fishing `{species, species_id, minLevel, maxLevel, slot%, rod}` |
| `wild_by_species.json` | 714 species -> list of {location, method, levels, slot% (merged per location/method)} |
| `wild_extra_0x08553894.json` | the 7-entry placeholder city table (see above) |
| `trainers.json` | 1459 trainers: id, class, name, party_flags, items, double flag, AI flags, party (species/level/item/moves) |
| `trainer_classes.json` | 71 class names |
| `key_trainers.md` | 335 trainer entries under 180 names: all Hoenn Gym Leaders (Roxanne 265 + rematches ..., Tate & Liza), Elite Four (Sidney/Phoebe/Glacia/Drake), Wallace, May/Brendan/Wally, all 8 Sinnoh leaders (Roark 1123 ... Volkner), Sinnoh E4 (Aaron/Bertha/Flint/Lucian) + Cynthia (886 and 1135), Volo (1339: Lv100 Hoopa/Eternatus/Dialga/Palkia/Giratina/Regigigas), Steven, Red (857/901/952), Leon, Ash, Serena, Archie/Maxie/Matt/Shelly/Tabitha/Courtney, Frontier Brains, Zinnia, plus ~120 other franchise characters (Blue, Lance, Giovanni, Cyrus, N, Ghetsis, Lysandre, Diantha, Lusamine, Marnie, Bea, ...). Every duplicate name (rematches / hard mode) is listed with its own levels. Chinese-named PkMn Trainer-class trainers are in a separate last section. |
| `items.json` | 800 items: index -> {name, id_field, price, pocket} |
| `species.json` | 1200 species/form names |
| `moves.json` | 937 move names |
| `static_encounters.md` / `.json` | 179 `setwildbattle` (0xB6, confirmed: always followed by 0xB7 dowildbattle) hits = 172 unique map/species/level rows, from walking every map's object/coord/bg-event scripts and map-script tables (call/goto/trainerbattle sub-scripts followed). Examples: Zeraora Lv50 (Route 101), Cresselia Lv50 (Mt. Pyre), Genesect Lv50 (New Mauville), Jirachi Lv30 (Artisan Cave), Marshadow Lv30 (Altering Cave), Cosmog Lv15 (Meteor Falls), Spiritomb Lv50 (Abandoned Ship), Arceus Lv80, Dialga/Giratina Lv80. Second section: every `trainerbattle` found per map (1113 hits, 957 distinct trainers) - e.g. Roark @ Oreburgh City 37/82, Gardenia @ Eterna City 37/83, Norman @ 8/1, Wallace @ 16/4, Red @ Mt. Silver 34/56 + 34/60, Volo @ Hisui Region 37/108. |
| `trainer_battles_by_map.json` | raw trainerbattle hits (map, script, trainer id, levels) |
| `_mapscan.json` | intermediate structural-scan results |

Scripts: `romlib.py`, `dump_tables.py`, `dump_maps.py`, `dump_trainers.py`, `make_key_trainers.py`,
`scan_maps.py`, `scan_wild.py`, `scan_static.py`.

## What I could not do / caveats

- The static-encounter and trainer-by-map scans are heuristic: scripts reached through `special`/`callnative`,
  hack-specific opcodes (>= 0xCA stops the walk), or stored outside the map event/script tables are missed.
  ~360 trainers with parties (incl. Cynthia and Leon) are not attributed to a map; their party data is complete
  in `trainers.json`. A `setwildbattle` in a script shared by several maps is reported once per referencing map.
- 35 maps carry a mapsec id whose name is empty (e.g. id 87) - mostly the hack's added interiors; `mapsec` is "" there.
- Music ids and layout ids are raw numbers (no name table was mined).
- Region-map x/y/w/h for the renamed Sinnoh sections are 0/0/1/1 (they are not drawn on the Hoenn map).
- Still Chinese-encoded in this build: item names 754-767, species 990-993 and 1025, move 937, and ~60 trainer
  names (mostly Sinnoh route trainers) - reported as `{CNxxxx}` tokens.
- Trainer classes >= 71, items >= 769, species >= 1200 and trainers flagged `invalid` are not real data.
- Fishing slot% uses the vanilla 70/30 | 60/20/20 | 40/40/15/4/1 table; the hack's code may weight differently (not verified in code).
- The hack's party-entry format was checked against vanilla rules only via level/species sanity (0 failures), not by disassembly.

Confidence: high for species/move/item/class/map-section/trainer tables and gWildMonHeaders (all anchored by
code references and well-known ids); high for maps.json (vanilla group sizes match exactly and the NOTES
cross-check passed); medium for the script-derived files (static_encounters, trainer_battles_by_map).