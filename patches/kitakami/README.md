# Kitakami (in the game since 2026-10-17)

The Ogerpon story's area - Mossui Town alone since 2026-10-16 (town revision 7, below; no Dreaded Den either) -
built on top of the
finished game (`rom/`), the way `summitfix` is: nothing here needs the Crest ROM, so it builds on any machine.

    python patches/kitakami/kitakami_patch.py "rom/Pokemon Hyper Emerald v5.7 - Full English Modern.gba" out.gba

The story, the decisions the user made and the mock-ups are in `rom/unreleased/kitakami/` (`STORY.md` first).

## Milestone 1 (2026-10-14): the three outdoor maps

- `tileset.py` - Kitakami's own secondary tileset: the hack's Lavaridge set (0x083DF794, which Bellchime Trail,
  the Bell Tower's roof and Lavaridge share) copied, with rows 9 / 10 / 11 recoloured (teal halls, grey rock, green
  maples; green no longer: revision 6), the homes' longhouse pieces again from 953 on in a slate-grey row (6), Slateport's market pieces made
  red-and-white (their colours packed into rows 7 and 8 and the spare slots of 11 and 12), two lantern pieces
  (new art). 58 pieces of ours (953-1010); 336 picture cells left (for the pagoda's real roof).
- `kworld.py` - the maps: Mossui Town (48x40, laid out like Ecruteak City), the Kitakami Road (40x30, north of it),
  Oni Mountain (32x30, east of the road), painted by `patches/paldea/world.py` and stamped with the buildings.
- `kitakami_patch.py` - writes it all into 0x09B40000..0x09C00000 (zero-filled, claimed by nothing; no code or
  header points into 0x09B00000..0x09D00000), adds maps 35/106-108 after Area Zero's with `patches/paldea/maps.py`
  (pointed at the tables the ROM has now: 862 layouts), joins them by connections, names map sections 187-190
  (Mossui Town, Kitakami Road, Oni Mountain, Dreaded Den). 28 bytes change outside its space: the three layout
  table references, group 35's table pointer, four name pointers.
- `preview.py <rom> <out.png>` - the maps drawn from the built tileset, as the game reads it.
- `test_walk.lua` - warps to the bus stop and walks the market's aisle, through its gate, the north path onto the
  road, east onto Oni Mountain, up its three terraces and into the den's mouth; presses B through an Egg hatching or
  a phone call. Passes on the build of 2026-10-14.

## Milestone 2 (2026-10-14): the doors and the insides

- `kinteriors.py` - fifteen rooms, cropped from rooms of the game's own and wired both ways: Kitakami Hall 1F
  (the hotel lobby of 34/61), 2F (34/63's floor), your room (34/61), 3F the Mask Hall (37/102's pillared hall with
  a gold stage) - their blues turned teal in copies of their tilesets; the family house (37/102's tatami room);
  the festival hall (Bellchime Trail's wooden hall, 35/75); seven homes (a Lavaridge house, 4/3); the Pokemon
  Center (Petalburg's, 8/4, its nurse with the game's own script 0x082079FC); the Dreaded Den (a cave of Seafloor
  Cavern's, 24/35). Maps 35/109-123 (group 35 now has 124; a warp's map number tops out at 126).
- `test_doors.lua` - from the Hall's door: the lobby, up to 2F, up to the Mask Hall, down, your room, out; a home;
  the Pokemon Center and its nurse; the den. Passes.
- Not yet: the centre sets no respawn point (healing there keeps the last one); the den's inner mouth leads nowhere.

## Town revision 5 (2026-10-15)

After playing it the user found too many houses and the festival hall's inside of no use, and asked for a town
more organised and useful. Mossui now has what the story or the player uses and nothing else (44x37): the market
street down the middle; Kitakami Hall raised in the north-west, Loyalty Plaza in its grove in the north-east, the
pond between; Carmine and Kieran's house and the old woman's on the west, the Pokemon Center and the old couple's
on the east; rice paddies in the bottom corners; the bus stop south. No festival hall (its organiser stands at the
market gate); two homes instead of seven (the other villagers stand out of doors). Maps: Mossui 106, road 107,
Oni 108, hall1-3 109/110/112, your room 111, family 113, Pokemon Center 114, den 115, homes 116-117. Oni
Mountain's second patch of tall grass moved off the way up to the summit's steps. Both tests pass again.

## Wild Pokemon (2026-10-15)

- `kwild.py` - the wild table (gWildMonHeaders, 0x08E17D50) had no room left: Area Zero's three headers took the
  68 spare bytes after its terminator. It is copied into Kitakami's space with four more headers (the Kitakami
  Road: grass, ponds, fishing; Oni Mountain: grass, added to its first two rises; the Dreaded Den: its floor;
  Mossui Town: the pond and the paddies, fishing) and its 15 references are pointed at the copy (13 literals of the
  game's wild code, the DexNav search's, one in the DexNav chain's data; nothing points into its middle). Kitakami's
  species (The Teal Mask's, as far as this game has them), Lv 50-64.
- The patch asserts the table still has 257 headers and the 15 references still point at it: if Area Zero (or
  anything before this patch) adds a header, this patch stops instead of dropping it.
- `test_wild.lua` (AREA=road / oni / den / r101) - walks in the grass until battles start and logs the Pokemon:
  the road gave Seedot, Ekans, Sentret; Oni Mountain Teddiursa, Nosepass; the den Noibat, all at their levels;
  Route 101 on this build and on the game before it both gave Route 101's own Pokemon (the table, moved, still
  serves every other map). `test_dexnav.lua` - the DexNav on the road, in the den and in Mossui lists Kitakami's
  Pokemon (`rom/unreleased/kitakami/kitakami-ingame-dexnav.png`).

## Town revision 6 (2026-10-15): the valley of red maples

The user asked for Mossui to be "outstanding ... fantasy", then, of the first try at it (a mock-up with trees put
together wrong), for every tree whole, the border all red and orange, and every tile placed with care. Mossui is now
48x50, ringed by a wood of red maples two trees deep (its border, beyond the map's edges, the same wood):

- The trees are the Lavaridge set's red maples and conifers, put together as the game's own maps put them (read
  off Bellchime Trail 35/74, the orchard of 36/57 and Route 112 0/27; `kworld.py` has the table): a maple's crown
  (688 696 on open ground, 658 659 in front of the tree above), its body (704 705; 715 705 after a neighbour) with
  its sides on the grass beside it (838 839), its bottom (656 657); a conifer's tip (538; 521 in front of the one
  above) and bottom (537). `wood()` grows a wood from a set of trees on the even grid; `maple()` and `conifers()`
  stand trees alone. The set's other tree pieces stand on rock (grey or pink on Kitakami's grass) and are not used.
- Row 11 keeps its reds and oranges (it was turned green). The hall's lower right corner (719) had a scrap of
  Bellchime's maple under it; Kitakami's copy has grass there, as its other corner does.
- `kart.py` - new art: a torii (5x4 tiles), a stone lantern (1x2) and a red bridge (2 wide), in the paper lanterns'
  colours where they can be. Each tile becomes a metatile over the ground it stands on (the ground's picture in the
  bottom layer, the art in the top one; the bridge is drawn whole), numbered with base metatiles no map uses (ours
  from 953 are nearly all taken): 22 of them; 359 numbers, 269 cells and 9 colours left. You pass under a torii's
  beams (they draw over you, as a tree's crown does), behind a lantern's top; a lantern's foot and the torii's pillars
  stop you; the bridge is walked on over the pond.
- The town: the road north leaves through a gap in the wood; the avenue runs from it over the pond on the bridge,
  across the street, under the market's gate and down the market to the bus stop (a clearing in the wood). Kitakami
  Hall on its hill in the north-west, with a forecourt, two stone lanterns and steps; Loyalty Plaza in a grove of red
  conifers in the north-east; below each, a torii in a court paved as the market is. On the street: the old woman's
  house and Carmine and Kieran's (larger) on the west, the Pokemon Center and the old couple's on the east, every
  door onto it. Rice paddies either side of the market.
- Also fixed: the homes reuse the longhouse's picture cells and its row-12 colours, and nothing kept those for them
  (the pagoda happened to); `build()` now does.
- Every walkable tile can be reached from the bus stop (the painter's `reach()`). `test_walk.lua` (bus stop, market,
  gate, avenue, bridge, north road, onto the road at its path, Oni Mountain to the den) and `test_doors.lua` (the
  hall and its floors, out under the torii, Carmine and Kieran's house, both homes, the Pokemon Center and its
  nurse, the den's door both ways: its floor's wild Pokemon are test_wild's, a battle this test cannot fight) pass; DexNav opens in Mossui, on the road and in the den; Oni Mountain's grass gives Nosepass and
  Geodude at Lv 61-63. The Kitakami Road and Oni Mountain still have the General set's green trees: next.

## Town revision 7 (2026-10-16, the Windows PC): the town alone, and a new home in the ROM

- **The Kitakami Road and Oni Mountain are gone** (the user, shown the three maps with the story's places on
  them: "short version, no need to have oni mountain or road whatever, just kitakami village", then "remove road
  and remove oni mountain, keep only town"). `road()` and `oni()` are out of `kworld.py`, and so are their
  connections, their wild grass (`kwild.py`: the den's floor and Mossui's water are left) and their names (map
  sections: Mossui Town 187, Dreaded Den 188; 189-190 are untouched now).
- **What was on them is in the town** (`kworld.py`, `mossui()`): the Dreaded Den's grey rock (`DEN_ROCK`, at
  `DEN_AT` 21,0) fills the gap in the wood where the road left, its mouth (23,3) at the top of the avenue between
  the two stone lanterns, a warp to the den's room (Mossui's warp 5; `kinteriors.wire`); the wood's gap is
  x 20-27 now. The legend's signboards (`LEGEND_SIGNS`): 1 amid the west rice fields (9,37), 2 amid the east
  ones (38,37), 3 at the foot of the den's path (25,5). Marks for the people milestone: Munkidori by the pond
  (28,10), Okidogi behind the shrine's grove (42,10), Fezandipiti on the hall's hill (17,14).
- **Maps** (group 35): Mossui 106, hall1 107, hall2 108, your room 109, hall3 110, family 111, Pokemon Center 112,
  den 113, home1 114, home2 115.
- **Space.** The Mac's 0x09B40000..0x09C00000 is not free any more: gen9rest claims 0x09B00000..0x09D00000 and
  filled that stretch when the whole of Gen 9 went into the game (2026-10-15), so the patch refused to apply ("not
  empty"). It is at **0x09E40000..0x09E80000** now (`FREE`), checked with `_testrun/space/kitakami_space.py`
  against `rom/` (8462fa6f...) and the hack's own ROM: all zeros in both, inside the zero run 0x09E10044..0x09F00000
  that both have (after the hack's forms table, before its code at 0x09F00000): 191 KB of zeros before the range,
  512 KB after; no ROM header word or code literal points into the run (speciesx's `is_pointer`); of the 811 words
  that read as an address in the range (182 on a 4-byte boundary, 45 after a byte that could be a script command)
  none is a real pointer, and the ones looked at lie in pictures and tunes (0x0839..., 0x086B...-0x0871...); no
  patch, tool or note in the repo names an address in the run. Read watchpoints on the whole run, on `rom/`
  without Kitakami (`_testrun/space/kitakami_watch.ps1` -> `kitakami_watch.txt`, 2026-10-16): 0 reads in 14 runs
  (the menus, Prelude Beach with R/SELECT/START/L, Surf and wild battles, the researcher with three saves and
  resets, walks on twelve maps); the control stretch of the first tileset's animation frames, in the same runs,
  2,749 to 1.9 million reads a run, so the watchpoints were seeing reads. The build writes 31.9 KB there (0x09E40000..0x09E4960F) and 80 bytes outside: the three layout-table
  references, group 35's table pointer, two map-section name pointers, the wild table's 15 references.
- On `rom/` (8462fa6f...) the build is f62687607d4627b239adb12b7d2bec35f102da3e.
- Tests, on that build, run on the PC with `_testrun/kitakami/run.ps1 -Rom <build> -Test walk|doors|wild|dexnav`
  (hidden, muted; the save is `_testrun/t28/nc_expgain`'s): `test_walk.lua` (bus stop, market, gate, avenue,
  bridge, the den's path, into the den) and `test_doors.lua` (every door both ways, the den's from the town) pass;
  `test_wild.lua` AREA=den meets Kitakami's den Pokemon at their levels (a Bronzor, Lv 61); `test_dexnav.lua` lists
  the den's floor and Mossui's water. GOTCHA: with that save `test_wild.lua` cannot run from the battle ("stuck in
  battle" after the first one, on Route 101 too), so it logs one battle a run.

### The Dreaded Den went too (2026-10-16)

The user, of the build above: "the den is unneccesary, make a playable". Gone: the den's rock and mouth in the town,
its room (Seafloor Cavern's cave, `kinteriors.py`), its map section name (only 187, Mossui Town, is written now),
its wild Pokemon (`kwild.py`: `LAND` is empty, Mossui's water and fishing are all of Kitakami's Pokemon). The wood
is closed at the top of the town again (`kworld.py`), the avenue ends at it (y 5) between the stone lanterns,
signboard 3 beside its end (25,5). Maps: Mossui 106, hall1 107, hall2 108, your room 109, hall3 110, family 111,
Pokemon Center 112, home1 113, home2 114. 37,832 bytes at 0x09E40000 (inside the range checked above). On `rom/`
(8462fa6f...) the build is be2442559ce2eed0ddff3401432574b8cd619bb1. Tests on it: `test_walk.lua` (to the
avenue's end; the wood stops you there: its last step logs STUCK at y 5, as it should), `test_doors.lua` (every
door), `test_dexnav.lua` (Mossui's water), `test_wild.lua` AREA=r101 (the moved table still serves the rest of the
game) pass.

**Kitakami test 4** (playable, on the PC): `roms/test-kitakami/Hyper Emerald - Kitakami test 4.gba` (that build)
with a save beside it (only there: the user wants no saves on the Desktop): the user's save of "(my placements
25)" (their newest; no save state
newer), warped to Mossui's bus stop (23,46) and saved from the Start menu by `_testrun/kitakami/make_save.lua`
(through `_testrun/paldea/run.ps1`), then reset and continued there to show it took. There is no way in or out
yet but Fly.

## The people and the way in (2026-10-16, the Windows PC)

The user, asked whether to start with the people and the way in: "do it". `kstory.py` (what they say, flags, who
wears which sprite), `ksprites.py` (the new sprites), `kpeople.py` (everything else); the wording is mine.

- **Who stands where** (`kpeople.TOWN`, `ROOM_PEOPLE`): in Mossui Briar and Carmine at the bus stop, Kieran outside
  the family house, the elder at Loyalty Plaza before the Loyal Three's three stone statues, the festival's
  organiser at the market gate, a vendor in each of the four stalls, six villagers (an apple farmer, a mother and
  her child, the lantern maker, a hiker, a mask carver). Inside: the caretaker behind Kitakami Hall's front desk
  (its row 11 is a counter), Grandpa in the family house, the old woman, the old couple (where Lavaridge's own
  couple stand in 4/3). The bed in your room (10,2-3) heals, with the healing fanfare, as Area Zero's cots. The
  seven signs (four town signs, the legend's three boards) say what they are. Everyone says their arrival lines
  (STORY.md, "Mossui's people", arrival); the chapters are the next milestones.
- **The vendors** stand in a gap of floor in the middle of their stall's goods row, under the awning, as
  Slateport's market has them (0/1: 5,43 and 11,43). First built standing a row higher behind the goods (with the
  goods made a counter): the awning hid them. `kworld.market()` returns the gaps; `kpeople` checks the vendors
  stand in them.
- **Sprites** (`ksprites.py`, pictures `sprites/`, made by `sprites/convert.py`): Carmine, Kieran, Briar - the
  approved repaints (`rom/unreleased/kitakami/kit/chars/ow.py`), nine frames, walking like any person; the statues
  - pokeemerald-expansion's walking sprites of Okidogi, Munkidori, Fezandipiti, front frame only, every colour a
  grey by its brightness, one shared palette; inanimate. They take the hack's sprite entries 236, 237, 239 and 228,
  229, 235: no object of the game's 939 maps uses them (`sprite_slots.py`), 236/237/239 are inanimate copies of
  228/229/235. Palette tags 0x1138-0x113B in a longer copy of the field palette table (Area Zero's copy, at
  0x09FFBD94, ended at row 56 with 0x11FF): the three code words point at ours.
- **Briar's way in** (`kpeople.make`): in Mossdeep she stands on Jacq's tile (70,32) once Area Zero's stage var
  0x40A8 is 4 (the ending is over: Jacq has gone back in), facing the hole; her intro the first time, then "Would
  you like to come along to Kitakami?" Yes -> the bus (a warp) to Mossui's bus stop (23,46). In Mossui she asks
  "Shall we take the bus back to Mossdeep?" -> (70,33), below her. Mossdeep's people and map scripts are Area
  Zero's copies: ours are copies of those with her added (object 35), our ON_TRANSITION / ON_RESUME work out her
  hide flag then go on to Area Zero's (which go on to Mossdeep's own); its ON_FRAME table is Area Zero's.
- **Flags**: 0x43E8 Briar's hide flag in Mossdeep (worked out on every way in and on resume), 0x43E9 met Briar.
  Checked free with `_testrun/kitakami/flagcheck_k.py` (the Area Zero check, with the user's newest saves added);
  0x43E5-0x43E7 and 0x43EA have chance matches and are skipped; 0x43EB, 0x43ED are free for the chapters.
- **Saves made on an older build** hold the old copy of a map's people. Area Zero's answer is a stamp in var 0x40F9
  (ON_TRANSITION writes it, ON_RESUME compares, ON_FRAME on 0 warps you onto your own tile, reading the map
  again). Every Kitakami map does the same with Kitakami's stamp (`kpeople.stamp_of`: Area Zero's and what this
  patch places), and Area Zero's stamp (0x4B00 in the game of 2026-10-16) is rewritten to ours in the 30 places
  its scripts write or compare it (24 setvar, 6 compare, all in Area Zero's blob 0x09FBC400..0x09FD2A00), so that
  a save made in Mossdeep before Briar existed reads Mossdeep again and has her.
- **Checks at build time** (`kpeople.layout_report`): every tile reachable from the bus stop without the people is
  reachable with them (but their own); everyone can be talked to and every sign read; nobody stands in or before a
  doorway or on a sign; at most six palettes on one screen (4 at the most, measured). `tools/text_overflow.py`
  on the build: the 54 new texts fit (the one text it flags, 0x08670057, is flagged on `rom/` too).
- On `rom/` (8462fa6f...) the build is 101b52ede0c42beb435468772db38e5d55b0c8c4, 54,972 bytes at 0x09E40000.
- **Tests** (through Area Zero's harness, `_testrun/paldea/run.ps1 -Rom <rom in that folder> -Steps
  ../../../_testrun/kitakami/<file>`; copies here): `steps_people.lua` from the user's save of "(my placements 25)":
  Briar in Mossdeep, her bus, all 18 people of the town (vendors in their stalls), the seven signs, the caretaker,
  the bed, Grandpa, the three in the homes, her bus back, a save in Mossdeep and Continue - passes;
  `steps_oldsave.lua`: a save made in Mossdeep on `rom/` has Briar after Continue on this build, and Kitakami test
  4's save (made at the bus stop, nobody in the town) has the people after Continue - both pass.
  `_testrun/kitakami/mossdeep_k.ps1`: Area Zero's `test_mossdeep.lua` (the Space Center's people shown, hidden,
  before Team Rainbow Rocket, a save in Mossdeep) on this build and on `rom/`, logs compared without Area Zero's
  objects and Briar (30-35): "same as the game" in all four. `test_walk`, `test_doors`, `test_dexnav`, `test_wild`
  (r101) pass on it too.
- **Kitakami test 5** (playable): `roms/test-kitakami/Hyper Emerald - Kitakami test 5.gba` (this build), its save
  the user's "(my placements 25)" save as it is (they stand in the Timeless Woods; Briar is in Mossdeep). No save
  on the Desktop (the user, 2026-10-16: none there any more).

## The story, all eight chapters (2026-10-16, the Windows PC)

The user, after playing the people milestone ("what I can test here? talk and nothing happened?"), chose "All 8
chapters" and battles at "Lv 70-75". STORY.md's scenes in the town alone, the den's at Loyalty Plaza. Files:
`kchapters.py` (the scripts and the stages), `kstory.py` (every line, the flags), `ktrainers.py`, `kasm.py`,
`ksprites.py` (four more sprites), `kpeople.py` (the wiring and the checks). The wording and the teams are mine.

- **Stages** are worked out from the story's flags on every way into Mossui and the family house and on resume
  (`kchapters.state_mossui`, `state_family`): Carmine and Kieran moved with `setobjectxyperm` (0x63) and
  `setobjectmovementtype` (0x65) to where the stage wants them (`kchapters.POS`), the statues, Ogerpon, the Loyal Three
  shown or hidden by "hide" flags. Within a visit a scene changes them with removeobject / addobject and calls the
  same state script. kchapters' docstring lists the stages (s0 arrival ... s11 after the story).
- **The state is flags only**: a var no script names can still be set by the hack's code (0x406A and 0x407C looked
  free; the Journal reads them). 26 flags from 0x43E8 to 0x437C, chosen from the 87 that `freecheck.py` finds free in
  the whole extended range (no flag command bytes, no aligned word, no object hides by it, clear in the saves):
  `kstory.py` lists them.
- **Battles**: Carmine (trainer row 1358: Ninetales, Ariados, Mabosstiff, Lv 70-71), Kieran at the plaza (1359:
  Appletun, Flapple, Lv 72-73), Kieran for Ogerpon (1360: Appletun, Incineroar, Flapple, Lv 74-75); class 33 "School
  Kid"; the approved battle pictures as pictures 250 and 251 (`ktrainers.py`: the picture, palette, animation and
  coordinate tables, 250 entries each, copied longer and repointed - the first build copied two of the four and the
  battle hung on a black screen). The Loyal Three in the hunt and Ogerpon in her four masks are wild battles at
  Lv 75 with the Totem flags (0x272 no Poke Balls, 0x273 no white-out); the catch is a wild battle with 0x273 only.
  Every story battle is fought with 0x273 on: a loss heals you and you can try again (Kitakami has no place to come
  round in). The outcome is read with special 183, as Area Zero does. The finale is six battles in a row (Kieran,
  the four masks, the catch): the party is healed before each mask and before the catch ("Your team caught its
  breath.", `kstory.REST`) - the first full story run ran out of PP in the fifth.
- **The festival's night** (`kasm.py`): the hack's tint routine reads the hour at 0x08CFE3EA; that read is a `bl`
  to kit_hour (0x08FEF580, the top of a free unreferenced run), which gives 22:00 (night blue) while F_PLAZA is set
  and F_TRUTH clear and you are in Mossui, the real hour otherwise. (It gave 18:00, an orange evening, until
  2026-10-17: the user, "for night, don't use tint orange it is kinda not sure night or not".)
- **Grandpa's masks** after the story: `kasm.mask_code` (callnative; in the blob) gives the first Ogerpon in the
  party the species of the chosen mask (1228 Teal, 1229 Wellspring, 1230 Hearthflame, 1231 Cornerstone, by their
  types in the ROM) with SetMonData and recalculates its stats.
- **The stalls** are shops from the festival on: candy apples (Sweet Apple, Tart Apple), festival mochi (the six
  vitamins), rice balls (Hyper Potion, Max Potion, Full Heal, Revive); the mask stall talks. **The hack's shop
  guard** (0x096FFF00, NOTES under gen9rest's test 2) resets the game when a shop's list holds an item outside its
  bitmap of the items a shop may sell (byte 0x09E0FE5F - (item >> 3), bit item & 7): Sweet Apple (88) and Tart Apple
  (89) were not in it, and the first story run reset the game on buying a Sweet Apple. `kitakami_patch.allow_shop_items`
  gives them their bits (byte 0x09E0FE54 |= 0x03) and asserts every stall item is allowed. Testing a shop: through
  the vendor (`_testrun/kitakami/steps_shop.lua`); a bare `pokemart` run by the harness trips the guard's other check
  (totalCost, read before the list buffer) even on the untouched ROM.
- **Sprites**: Ogerpon and the Loyal Three alive (pokeemerald-expansion's walking sprites) in the hack's entries 230,
  238, 205, 206, palette tags 0x113C-0x113F.
- **Checks at build time**: the layout report now runs for every stage and for the wake and festival scenes (from
  where you stand in them): reachability, nobody in a doorway, everyone talkable, at most six palettes a screen (6
  at most, in the wake scene); `tools/text_overflow.py`: the 211 new texts fit.
- **Tested** (`_testrun/kitakami/steps_story.lua` through `_testrun/paldea/run.ps1`, from the user's "(my placements
  25)" save): every chapter in order, each battle won, the stall's shop bought from and left, the forced catch, an
  after-story Okidogi gone once beaten, Grandpa's mask change (a Wellspring Ogerpon, 293 max HP, became Teal, 276), a
  save in Mossui and Continue. The harness (`patches/paldea/test_paldea.lua`) now presses B through a PokeNav call
  that holds the screen before a walk (one waited 30 minutes) and refills the pinned move's PP.
- **Kitakami test 6** (playable): `roms/test-kitakami/Hyper Emerald - Kitakami test 6.gba` (sha1 f3071d87...), its
  save the user's "(my placements 25)" one beside it.
- **Not done**: the Quest Log (the five Kitakami legends stay Locked rows in `gen9journal`; making them counted rows
  is a change to that patch, NOTES *The Quest Log's Gen 9 rows*), Pecharunt (Part 2), the masks shown on the Mask
  Hall's stage, the pagoda's roof.

## Placements, the editor, the one-floor Hall (2026-10-17, the Windows PC)

The user, on test 6: "1. the npc to heal in pokemon center has a werid dialog mixed chinese and spacebar 2. can the
signboard be something unique from normal signboard, its hard to tell 3. I want to edit placement myself", and "at
the tower, I think we need only one floor which is the current 3rd floor, hotel style is not needed anymore".

- **The nurse.** Every Pokemon Center's ON_RESUME is CableClub_OnResume (0x08277C30: `special 0x01A4`,
  InitUnionRoom), which empties the Union Room name buffer (0x02022C20). Kitakami's Center had the room but not
  that script. After healing the nurse asks special 0x01A5 (BufferUnionRoomPlayerName): the buffer was not 0xFF, so
  it was copied into STR_VAR_1 with no end and she said "It appears as if <junk> is playing right now" - Chinese
  glyphs and spaces in the user's emulator, a crash and reset in mGBA dev (the test had stopped one page short).
  The Center's ON_RESUME does `special 0x01A4` now (`kpeople.py`). `_testrun/kitakami/steps_nurse.lua` (PLACE=
  petalburg for the control: Petalburg's nurse never went that way).
- **Kitakami Hall is one floor**: the Mask Hall (37/102's pillared hall, teal), its mat (6,14) the door from the
  town. The hotel's lobby, 2F and your room (and its bed) are gone; the caretaker stands before the stage (7,7); his
  lines, the Hall's sign and "confetti in the lobby" reworded. Maps renumbered: hall 35/107, family 35/108, pc
  35/109, home1 35/110, home2 35/111 (a save made inside an old Kitakami room would land elsewhere: none existed).
- **The legend's signboards** are a drawn piece of their own (`kart.legend_board`: a notice board under a red shingle
  roof, a sheet of paper with writing and a red seal, on two posts; 1 x 2 tiles like the stone lantern: the board
  stops you, its roof on the tile above is walked behind). The town's four signs keep the General notice board.
  Signboard 3 moved from 25,5 to 26,6 (its roof would have been in the wood's maples) and Kieran's place there to
  27,5. A board needs plain ground under it and its roof (`tileset.can_hold`: a General metatile with nothing
  standing on it, or the market's paving); elsewhere the build says so.
- **Placements** (`kplaces.py`): every position of Kitakami - 16 townsfolk and statues, the bus stop, 7 signs, 21
  places of the story (Carmine's and Kieran's place at every stage, the scenes' starting tiles: Kieran and Carmine
  running in, Ogerpon at the festival, where evening finds you; Ogerpon at the plaza, the Loyal Three's hiding
  places), the five people inside - is read from `placements.txt` (`name = x, y[, facing]`), the built-in
  positions for what it leaves out. `kplaces.apply` hands them to kworld / kpeople / kchapters before the build. The
  Loyal Three wake where their statues stand.
- **The checks** (`kpeople.layout_report`, what "Check" says): everything on the map; everyone on ground you can walk
  to (a vendor in a stall's gap), nobody on another's tile, out of a doorway, off a sign, talkable, at every stage
  and in the two scenes; the three walks over open ground nobody stands on; the bus stop and the evening's tile
  walkable; no sign before a door, no signboard's roof on one; at most six palettes a screen; in the rooms everyone
  on a floor tile off the mat, reachable. A thing wrong at many moments is one line ("... (at: from arrival to
  chapter 5)").
- **The editor** (`editor.py`, "edit placements.bat" in roms/test-kitakami; port 8766-8775): the five maps drawn from
  the built game (the town without its signs; the signs, the signboards and every person as sprites, in their
  facing), drag or arrow keys, R turns a person, "Show who is there at" a moment of the story, Check, Save and
  rebuild (`krebuild.py`: "Hyper Emerald - Kitakami (my placements N).gba" from rom/, the user's newest save beside
  it - the most play time, never test 4's side save -, the last two kept), Play it (tools/pc_mgba). `?selftest`
  runs the page against itself (read with Edge headless `--dump-dom`); `_testrun/kitakami/editor_test.py` the server.
- **Tested**: the nurse heals and says goodbye (Kitakami's Center; Petalburg's as the control); the whole story
  (`steps_story.lua`) on the first editor build, which equals `_testrun/kitakami/kitakami8.gba` (4ef6a13d); the
  editor's server (good and bad moves; Save and rebuild in a throwaway folder) and its page (14 self-tests).

## The Mask Hall, drawn for Kitakami (2026-10-17, the Windows PC)

The user, after "what is the use of kitakami hall?" (it held one step of the story: the caretaker's task): "can u
redesign the interior hall to match the theme? or maybe something unique for this theme kitakami". No room of the
game is Japanese (the hack's 189 indoor maps of groups 34-37 looked through: its "wooden" rooms are a cave's tiles or
Sinnoh's houses), so the Hall is new art, `khall.py`, as the town's torii, lanterns and bridge are:

- **The room** (13 x 15): a dark wooden beam and pillars, shoji paper between them, a teal-bordered scroll with the
  Loyal Three's crests; a tatami stage the width of the hall with the three masks (Wellspring, Hearthflame,
  Cornerstone) in glass cases on red pedestals and a paper lantern at each end; the stage's wooden front with a gold
  plaque under each case; a plank floor, a red carpet from the door to the stage, teal zabuton in two rows a side; a
  standing paper lamp each side of the door (its head drawn over you); the mat (behaviour 0x65) at the bottom.
- **Its tileset** is made from the picture (`khall.build`): 8 x 8 cells, the same cell flipped kept once, colours
  packed into palette rows 6-12 (5 used), one metatile per kind of tile (58), 111 cells; the General set first;
  its own black tile for what is past the walls (the old Hall's border was 37/102's metatile 1, which is grass in
  General: the first build showed green round the room).
- **The masks' story**: the plaques are read from the floor (`kchapters.plaque`): the mask before the Loyal Three
  wake, "The glass is smashed. The case is empty." from then on, "Returned to Ogerpon, its true owner" after the
  story. The cases themselves are smashed from F_WAKE on: the Hall's ON_LOAD swaps the six case tiles
  (`setmetatile`, `kpeople`). The caretaker's lines already said the masks were shown on the stage and the case
  smashed: now the room shows it.
- The caretaker stays at 7,7 (beside the carpet, before the stage). The checks read the plaques too (one must be
  readable from the floor).
- **Tested** (`_testrun/kitakami/steps_hall.lua`): the room before the story, a plaque, the caretaker, out through
  the mat to Mossui's hall door; the smashed cases and their plaque with F_WAKE; the last plaque with F_OGERPON; the
  whole story (`steps_story.lua`) on a build with the built-in places. The user's build: "(my placements 6)".

## Part 2: Mochi Mayhem, Pecharunt (2026-10-17, the Windows PC)

The user, after asking what the last Pokedex entry is (#1025 Pecharunt, the ROM's species 1237) and where it comes
from: "do it". The epilogue of Scarlet / Violet's DLC as Serebii's Mochi Mayhem page has it (read 2026-10-17), in
Mossui alone, at night, with Area Zero's friends from Paldea:

- **The way in**: after the story (F_OGERPON), Briar has Kieran's letter - in Mossdeep (then her bus) or in Mossui
  (then the friends are in the market already); the mochi stall's vendor points you to her ("a little peach-shaped
  plush ... Ms. Briar was looking for you"). F_P2_START; Mossui is night-blue until Pecharunt is caught (kit_hour now
  takes windows: the festival's night and Part 2's, both 22; keystone's 00 BF padding avoided).
- **Stages p12-p17** (`kchapters.P2POS`, worked out on every way in as Part 1's are): p12 Kieran, Arven, Nemona and
  Penny in the market, Carmine dancing; p13 Nemona has gone for mochi, the apple farmer (Shige) and the mother (Aya)
  are woken from the mochi's spell by talking; p14 Kieran's grandparents before Kitakami Hall (woken), Grandpa away
  from home meanwhile (H_P2_HOME); p15 Arven and Penny in the market (woken), then Pecharunt shows itself over it and
  flies off;
  p16 Nemona and Pecharunt at Loyalty Plaza: her battle, then Pecharunt's (Lv 82, no Poke Balls, no white-out; won,
  `givemon`: the official catch is certain; full party: the PC; no room at all: it waits); p17 the morning after,
  Kieran and Carmine at the bus stop. The townsfolk babble about mochi all night (phase M), the after-story's lines
  once it is over. The Loyal Three keep away for the night (six palettes at the plaza) and are back the morning after.
- **Battles**: Nemona's and Pecharunt's only (the user, after the first build had seven: "remove unncessary battle",
  then "Nemona + Pecharunt"). The others are woken by talking: their mochi babble, "You called out, again and again...
  At last they blinked, as if waking from a dream.", what they say awake (the defeat lines of the first build).
  Nemona: trainer row 1378 (its flag 0x462B free), her picture 194 and class Champion as in Area Zero, Lycanroc,
  Goodra, Kommo-o, Pawmot, Meowscarada at Lv 80-82 (official 86-87); Pecharunt Lv 82 (official 88).
- **Sprites**: Pecharunt from pokeemerald-expansion (graphics/pokemon/pecharunt/overworld.png and _normal.pal, fetched
  2026-10-17) in the hack's unused sprite entry 204, palette tag 0x1140; Arven 67 and Penny 70 of the main table
  (Area Zero's 37 and 58 have palettes of their own: the market showed seven), Nemona 20, the grandparents 29, 22.
  Since 2026-10-21 Nemona wears Area Zero's own sprite (entry 174, `ksprites.AZ_PEOPLE`) and battle picture (row
  952's: 250); Arven's and Penny's own sprites (one palette between them) made seven palettes in the market at
  stages 12 and 15, so they keep 67 and 70. Carmine's and Kieran's battle pictures are 253 and 254 now (after Area
  Zero's 250-252), the picture tables found through the code words (`ktrainers.REF_AT`).
- **Flags**: 0x437D-0x439F (the free run by freecheck.py on the Kitakami build), `kstory.py`.
- **Placements**: Part 2's 18 places are a section of their own ("Mossui Town: Part 2 (Mochi Mayhem)"), the editor's
  moments p12-p17; the checks run every Part 2 stage and the moment Pecharunt shows over the market.
- **Tested** (`_testrun/kitakami/steps_part2.lua`, from the user's save with Part 1 marked done): the letter and the
  bus, everyone woken, Nemona's battle, Pecharunt won and given (party full: to the PC; the Pokedex marks 1025 seen
  and caught in gen9rest's block), the morning after, Grandpa's masks still there, a save and Continue; Part 1's
  whole story again on the same build; the texts fit.
- **The "Part 2 start" save** (the user: "give me the part 2 save" -> "Part 1 done, at Briar"): beside the build as
  "Hyper Emerald - Kitakami (my placements N) (Part 2 start).gba / .sav": the user's own game with Part 1's flags set
  as its ending leaves them, Ogerpon (Teal Mask, Lv 75) given (`givemon`: the PC when the party is full), saved at
  Mossui's bus stop beside Briar (`_testrun/kitakami/steps_p2save.lua`). krebuild never takes it for the user's game
  (SIDE).
- **Not done** (then): the Quest Log still showed Pecharunt (and the Loyal Three, Ogerpon) as Locked rows (done since: below).
- **Night over the market too** (the user, with a picture of Part 2's market: "when at night, the floor is too
  bright"): the hack's tint leaves BG palettes 12-15 alone (mask 0xFFFF0FFF at 0x08CFE474, NOTES *Day/night*) and
  Kitakami's tileset keeps market colours in row 12. `kasm.kit_bgmask` (0x08FEF540..0x08FEF580, in the free run from
  0x08FEE88C: all 0xFF, no word points in) is reached by a bl over `mov r8, r7; ldr r7, =mask` (0x08CFE472; the next
  instruction is a branch target and stays): in Mossui (35/106) the mask is 0xFFFF1FFF, elsewhere the game's.
  `_testrun/kitakami/steps_night.lua`: the festival's night and Part 2's, the market dark with the rest.
- **Trying Part 2's places**: krebuild makes a "(Part 2 start)" copy of every build with the newest Part 2 start save;
  the editor's "Play from Part 2 start" opens it.

## Ready for the game (2026-10-17, the Windows PC)

The user: "do everything needed before merging". Everything up to the merge itself (the merge changes `rom/`, the
working ROM and the chain, and waits for the user's word):

- **The Quest Log** (`kjournal.py`): gen9journal lists Okidogi, Munkidori, Fezandipiti, Ogerpon and Pecharunt as
  Locked rows after the 119 it counts. Now they are counted rows: lock 0, a hint and a where of their own (the levels
  from `kstory`), no forced silhouette, their panels; legend_all's compare (`0x08FEB220`) and the chapter's count
  (`0x08FEC60E`) 119 -> 124, row 0's "all ... of them" texts again with 124. The texts go into the blob; the rows
  stay where gen9journal put them, changed in place, and `check()` asserts they are as it left them first.
  `_testrun/kitakami/steps_journal.lua`: Legends x/124, rows 120-124 no longer Locked, Ogerpon's and Pecharunt's
  details; with 1017 and 1025 marked caught, their rows and the count follow.
- **A real catch** (`steps_ball.lua`): the story tests set the catch's outcome; this one throws a ball (a Quick Ball,
  the first in the Poké Balls pocket) at Ogerpon after its four masks: F_OGERPON set, Ogerpon in the party, the
  Pokédex's 1017 caught.
- **Space** of the night code (0x08FEF540..0x08FEF600): all 0xFF in `rom/` and in the hack's own ROM, no real pointer
  (a word in graphics data at 0x086D65B0 reads 0x08FEF5F9 by chance), only this patch names it; read watchpoints on
  it on `rom/` (`_testrun/space/kitakami_watch_night.ps1`): 0 reads in 14 runs, the control range read in all.
- **Every changed byte** (`_testrun/kitakami/regions.py <rom/> <build>`): the blob, the code, the two hooks, the
  pointer words of the tables copied (trainer pictures 6, palettes 18, animations 3, coordinates 8; wild 15; layouts
  3; field palettes 3), group 35's table, Mossdeep's header, map section 187, four trainer rows, eleven sprite
  entries, one shop byte, the Journal's rows and counts, Area Zero's stamp in 30 places: 71,750 bytes, none left over.
- **The chain** (`_testrun/kitakami/chain_kitakami.py`, made from `_testrun/rel18/rebuild_chain.py` by
  `make_chain.py`: `kitakami` after `gen9journal` with `roms/test-kitakami/placements.txt`): from the v1.4 archive,
  382cf97c..., byte for byte the user's "(my placements 12)"; its stage before Kitakami is `rom/` (8462fa6f...).
- **The user's build**: "Hyper Emerald - Kitakami (my placements 12).gba" (382cf97c...) and its "(Part 2 start)" copy
  in `roms/test-kitakami`. Every test of the day ran on that file (as `_testrun/kitakami/kitakami15.gba`).

## In the game (2026-10-17, the Windows PC)

The user: "try to merge with main rom, make sure to not touch something unrelated, I don't want to have new bugs".

- The working ROM archived first (`archive/... (before Kitakami 2026-10-17).gba`, 8462fa6f...); the same game copied
  to `roms/before-kitakami/Hyper Emerald - the game before Kitakami.gba`.
- `kitakami` added as the last step (after `gen9journal`, with `roms/test-kitakami/placements.txt`) of the three
  `rebuild_chain.py` copies (`_testrun/rel18`, `full`, `objpal`; still identical) and of `patches/paldea/rebuild.py`'s
  TAIL. Nothing else in the chain changed.
- The chain from the v1.4 archive: 382cf97c..., the bytes every test of the day ran on; its stage before Kitakami is
  the old game (8462fa6f...). Installed as the working ROM and `rom/` (with `rom/kitakami-placements.txt`).
  `rebuild.py` then made "(my placements 26)": the same 382cf97c..., its save a copy of "(my placements 25)"'s.
- Kitakami cannot be built on a game that has it (its space must be empty), so `krebuild.py` and the editor build on
  `krebuild.base_rom()`: `rom/` while Kitakami is not in it, `roms/before-kitakami/...` now. `rebuild.py` refreshes
  that file with every Area Zero build of the user's (the stage before `kitakami`), so a Kitakami build has the newest
  Area Zero places. Checked: `krebuild.py` on it gives 382cf97c... too.
- Briar takes Jacq's tile in Mossdeep (70,32): moving Jacq in Area Zero's placements stops the kitakami step, with a
  line that says so (`kpeople.check`).

Not built: the pagoda's roof.

## Carmine stops you; no sun left on the town (2026-10-20)

- One step up from where Briar's bus leaves you, Carmine sees you ("!", she turns to you) and her battle begins: a
  coord event on that tile (`kchapters.carmine_spots`, var 0x4009 kept by `k_state_mossui`); talking to her still
  works (`k_carmine` -> `k_carmine_fight`). The editor's Check says so if she is moved off that tile's side or a way
  past it is opened.
- The hack sets a map's weather from a battle's as the battle ends (its own code, 0x09D494AC): Mossui's ON_RESUME
  puts its weather (none) back - resetweather, then ResumePausedWeather (0x080AEE84), never doweather, which left the
  town black after the battle - so Carmine's Ninetales' Drought no longer leaves the town in harsh sunlight.
- `docs/NOTES.md`, *Kitakami: Carmine stops you*.
