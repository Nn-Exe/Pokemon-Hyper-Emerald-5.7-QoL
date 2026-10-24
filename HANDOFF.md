# Handoff

Everything here is binary patching of a single GBA ROM: **Pokémon Hyper Emerald: Lost Artifacts v5.7**, a
Chinese Emerald hack (BPEE, 32 MB), translated to English and then extended with quality-of-life features.
There is no C source and no build system for the game itself — each feature is Thumb assembly assembled at a
fixed address and written into free space, plus a handful of patched pointer words.

If you read one other file, make it [docs/NOTES.md](docs/NOTES.md): it is the running engineering record,
newest section last, and it holds the addresses and the gotchas that cost real time to find.

## What you need that is not in this repo

The `.gitignore` keeps ROMs, saves and emulator binaries out on purpose.

| Thing | Where it comes from |
| --- | --- |
| `Pokemon Hyper Emerald v5.7 - Full English Modern.gba` | the working ROM, 32 MB, `BPEE` at 0xAC. Every patcher takes it as input. |
| The pre-QoL translated ROM + the untouched original | needed only to rebuild the whole chain from scratch (`movefix` and `gfxfix` diff against the original). |
| Battery saves (`.sav`) | for the test harness. A late-game save on a route with wild encounters is what most tests assume. |
| mGBA **dev** build | `--script` Lua only exists in the dev builds, not 0.10.x releases. Get `mGBA-build-latest-win64` from `https://s3.amazonaws.com/mgba/`. |
| Python 3 with `keystone-engine` and `capstone` | assembling and verifying Thumb. |
| `Crest_v1.0.F.gba` (another ROM hack, sha1 e892062a...) | only for `patches/gen9/`: the new species' pictures, icons and cries are read from it. Third argument of `gen9_patch.py`. |

## Layout

```
patches/<feature>/<feature>.s          Thumb source, assembled at a fixed BASE
patches/<feature>/<feature>_patch.py   asserts the ROM matches, assembles, writes, repoints
patches/<feature>/test_*.lua           mGBA Lua that drives the game and checks the feature
tools/                                 ROM mining and asset conversion (region maps, encounter tables…)
tools/gif_editor.py                    GIFs out of docs/showcase with the mouse, a local page (`gba-trans/hyper-emerald/showcase/gif editor.bat`)
site/                                  the guide website's source (Astro); `npm run build` writes it into docs/
docs/NOTES.md                          engineering record: every feature, every gotcha, all addresses
docs/DEXNAV-PROGRESS.md                the newest feature in detail — start here if you are continuing it
cheats/                                mGBA / RetroArch cheat files
```

A patcher is always `python patches/x/x_patch.py in.gba out.gba`. It never edits in place, and it asserts
its way in: if the bytes it expects are not there it refuses rather than writing something wrong. The full
chain that builds the release from the translated ROM is in [README.md](README.md) under *Rebuilding*.

## The rules the patches follow

These are not style preferences; each one is a bug that already happened.

1. **Free space only.** Write into runs of `0xFF` that nothing points into. A run of `0xFF` is not free if
   the game holds pointers into it. The current blobs live between `0x08FD8C00` and `0x08FDED20`; there are
   larger unreferenced runs at `0x08FE5284` and `0x08FF2454` if you need room.
2. **Minimal hooks.** Prefer repointing one pointer word over rewriting a routine. When a hook is
   unavoidable, use an 8-byte trampoline (`ldr r3,[pc,#0]; bx r3; .word`) at 4-aligned sites and the 10-byte
   form elsewhere — at an unaligned site the pc rounds down and the ldr reads its own trampoline.
3. **Chain, never replace.** Several features hook the same site (the overworld hook at `0x08085E5C`).
   A new patch reads the current target, writes itself in, and jumps to what was there.
4. **Thumb-1 only.** The patchers assemble a twin with the literal pools replaced by nops and assert that
   Capstone finds no 4-byte instruction: a stray Thumb-2 encoding will not run on a GBA. Watch the reach
   limits — pc-relative `ldr` reaches 1020 bytes, so long functions need several literal pools.
5. **Never write to the save.** No feature so far stores anything in SaveBlock1/2. (One deliberate exception:
   `bagslots` moves the Items pocket within the hack's own saved "overflow stream", 0x0203CF64-0x0203DE00, with a
   one-time migration - NOTES, *Items pocket 100 -> 200 slots*. That stream is saved: never use it as scratch -
   v1.5's Hyper Training did, one byte, and players could no longer fuse Necrozma: NOTES, *Fusion slots*.)
   Scratch goes in EWRAM
   that has been *measured* to be unused (fill a candidate with a pattern, play through battles, menus, the
   bag, a save and a Pokénav call, then check what survived — `patches/dexnavchain/test_scratch_ram.lua`).
6. **Verify in the emulator, not by reading.** Every feature here has a Lua test that drives the game and
   reads memory back. Three of the last four bugs were invisible in the source and obvious in a screenshot.

## Release v2.0: the Windows PC, 2026-10-24

1. **v2.0 is released** (the user: "push to release repo"): the game is `rom/` = "(my placements 55)" =
   **fb949e02...**, which the whole chain from the v1.4 archive gives byte for byte. Build 55 is build 54 with
   Kieran's Appletun and Flapple no longer their Gigantamax slots (found while making the site's data; NOTES,
   *Kieran's Gigantamax apples*). `release/hyper-emerald-en-qol.hpatch`
   and `CHECKSUMS.txt` rebuilt; the public repo has one "Release v2.0" commit and a GitHub release `v2.0`; the guide
   site describes v2.0 (`RELEASED_VERSION` = `PATCH_VERSION` = '2.0'). NOTES, *Release v2.0*.

## Earlier handoff: the Windows PC, 2026-10-22 (evening) -> the Mac

1. **New step `hisuifly`** between `gen9anim` and `kitakami`: the Hisui map flies again (Mingyao's Braviary), each
   place needing flag 0x431E, Rei and Cogita's news at base camp after Volo (the user: "make sure it check if we
   already completed Hisui quest at finding Volo but before skitty Cat"). Data only, 11 bytes:
   `python -I patches/hisuifly/hisuifly_patch.py in.gba out.gba`. The three `rebuild_chain.py` copies and
   `paldea/rebuild.py`'s TAIL run it. `rom/` = the working ROM = "(my placements 39)" = **f5ce12ce...** (= 10203d90...
   + the patch); the whole chain from the v1.4 archive gives it byte for byte (96 s). NOTES, *The Hisui map flies again, after Volo*.
2. The guide site still says the Hisui map does not fly (`site/src/data/features.ts`, `guides/mechanics.mdx`):
   change it with the next release.
3. **New step `evgain`** after `hisuifly`, before `kitakami` (reported: "Total EV sometimes stuck at 509"): the
   engine's EV gain counted points due to a full stat (252) toward 510, so a Power item for a full stat, or a foe
   giving EVs in one, stopped it at 509. One byte (0x09D5A9A2): `python -I patches/evgain/evgain_patch.py in.gba
   out.gba`. `rom/` = the working ROM = "(my placements 40)" = **ebeae0f5...** (= f5ce12ce... + the patch); the whole chain from the
   v1.4 archive gives it byte for byte (98 s). NOTES,
   *EVs from battles stopped at 509*.
4. **New step `mintquirky`** after `evgain`, before `kitakami` (a player's report): Cheren's Mint list in the usual
   order with Quirky in None's place (the user's choice; no undo), names cut to fit the screen; the Mint byte 25 =
   Quirky (24 stays Hardy) read the same by the stats and the summary. Code at 0x09E3C000..0x09E3C10C (blank,
   proven: NOTES). `rom/` = the working ROM = "(my placements 41)" = **8cccc1f9...**; the whole chain from the v1.4 archive gives it byte for byte. NOTES, *Cheren's Mint list*.
   Two other reports needed no change (NOTES, *Two reports that needed no change*): the box between Jubilife and
   Route 204 was a PokeNav call in our films (screenshot asked for), and the Shiny Charm already counts for eggs
   (6 tries against 2, measured).
5. **New step `castlefence`** after `mintquirky`, before `kitakami` (a player's report): the Rainbow Castle's first
   floor (34/82) raised its trap fence on every load, so a player teleported out by the inner Kirlia came back on the
   wrong side of it; now only when you are north of it. A new on-load script at 0x09E3C200, 40 bytes.
   `rom/` = the working ROM = "(my placements 42)" = **c5a095b0...**, which the whole chain from the v1.4 archive gives byte for byte.
   NOTES, *Rainbow Castle: the fence*.
6. **New step `azpeople`** after `castlefence`, before `kitakami`: Area Zero's six people redrawn after references
   the user found (Pokemon Essentials art, recovered from screenshots): 32 x 32 walkers in that style for all six,
   new battle pictures 250-252 (Nemona, AI Sada, AI Turo). The pictures are `patches/azpeople/sprites/*.png`
   (`make.py` turns them into what the patch reads); how they were made is in `_testrun/paldea/people/redraw`
   (Windows PC only). 30.8 KB at 0x09E24000. `kitakami/ksprites.py` now accepts Nemona's entry at 32 x 32.
   `rom/` = the working ROM = "(my placements 43)" = **38fac465...**, which the whole chain from the v1.4 archive gives byte for byte. Open: the references' artist is not known -
   credit them at a release if found. NOTES, *Area Zero's people, after the references*.
7. **Checked after, no change:** the castle round trip on foot (out by the inner Kirlia, back in through the fence,
   up to the inner Kirlia again) and the EV items at the 510 cap (vitamins and EV berries all right). Found while
   testing, the original hack's own: HP Up revived a fainted Pokemon with a few HP, and a Pomeg Berry gave full HP to
   a fainted one or one at 1 HP - fixed (8).
8. **New step `hpcalc`** after `azpeople` (the user: "patch to current rom", "everything"): when a Pokemon's max HP
   changes, a fainted one keeps 0 HP and a living one never drops below 1 (the game's own rule, plus the floor), in
   the hack's stat routine (40 bytes at 0x09F03A5C). "(my placements 44)" = **34921763...**. NOTES, *A fainted
   Pokemon stays fainted*.
9. **New step `eshot`** after `hpcalc`, before `kitakami` (a player's report): Electro Shot fires in its first turn
   in the rain (not with a Utility Umbrella, Cloud Nine or Air Lock), with its own charge message; a new kind-2 script,
   a routine and a string, longer copies of gen9abil's two tables, 2.6 KB at 0x09E3B000 (proven: NOTES).
   "(my placements 45)" = **2cb96ba2...**. NOTES, *Electro Shot in the rain* (also: Supreme Overlord checked again,
   it works).
10. **New step `granitefall`** after `eshot`, before `kitakami` (a player's report): four cracked tiles of Granite Cave
   B1F that dropped you into B2F's rock (stuck) are plain floor. "(my placements 46)" = **f1fc3a60...**. NOTES,
   *Granite Cave: falls into the rock*.
11. **New step `startclock`** after `granitefall`, before `kitakami` (2026-10-23, asked): a clock box on the Start menu
   under the "R Journal" one ("Thu 4:24 PM (Day)"). `rom/` = the working ROM = "(my placements 47)" = **9d6d95bb...**.
   NOTES, *A clock on the Start menu*.
12. **New step `consolequest`** after `startclock`, before `kitakami` (2026-10-23, the user: "include in the side
   quest, 4 quests"): the console in your room's four cartridges (Rainbow R., Ultra A., Friends, HP League) are Side
   Content rows 45-48 in the Quest Log (55 -> 59), each ticked by a flag its GAME CLEAR now sets (0x43A4, 0x43A8,
   0x43A9, 0x416B; the Hall of Fame's save keeps it). Data and four 8-byte script stubs at 0x09E22000..0x09E22DC4
   (0x09E22000..0x09E24000 kept). "(my placements 48)" = **b5572a73...** (`rom/` until gmaxicon); the whole chain
   from the v1.4 archive gives it byte for byte. Tested by a jump into Rainbow R.'s ending and by HP League played
   through the console's menu (7 battles at Lv50, to the Hall of Fame and Continue). The guide site
   still says 55 side quests (`site/src/data/features.ts`): change it with the next release. NOTES, *The console's
   cartridges in the Quest Log*.
13. **New step `gmaxicon`** after `consolequest`, before `kitakami` (2026-10-23, asked): the Max Mushroom icon at the
   bottom right of the summary's picture for a Pokemon with the Gigantamax bit (mon +0x4E bit 7, the Max Soup's; Emerald's
   Country Ribbon bit, so the Ribbons count counts it). An 8-byte trampoline at 0x081C4A08 and 0x09E3AD00..0x09E3AF0B.
   The mark is the Max Mushroom's own item icon (item 87, read from the ROM), made 14 x 14 (the user: "use this
   attached img", then "smaller", "too big"), at the right end of the nickname's row - in the picture's corner for a
   nickname over 54 px, so it never covers a name. "(my placements 53)" = **e8810b63...** (on 52's clock).
   NOTES, *The Gigantamax mark on the summary*.
14. **`startclock` changed** (2026-10-23, the user, with a picture of the box under the Journal's: "remove the evening,
   whatever, and move into the same row as R Journey"): "Thu 5:08 PM", no time of day, on the Journal box's row at
   (11,1) 9 x 2 (frame tiles 10-20; the Start menu's frame starts at 21); at the top left without the Journal and still
   under the Safari / Pyramid window. `rom/` = the working ROM = "(my placements 52)" = **e3e56cec...**, 456 bytes from
   51, all in 0x09E3BC08..0x09E3BF1B; the whole chain from the v1.4 archive gives it byte for byte. NOTES, *The clock
   beside the Journal*.
15. **`gmaxicon` moved onto the name row** (2026-10-23, the user's mock-up: the mark right of the nickname, "make sure
   it would not affect any name"): at the nickname row's right end when the nickname is at most 54 px, else in the
   picture's corner (item 13). `rom/` = the working ROM = "(my placements 53)" = **e8810b63...**, 408 bytes from 52;
   the whole chain from the v1.4 archive gives it byte for byte. NOTES, *The Gigantamax mark on the summary*.
16. **The Zygarde Cube's Key Items row** (2026-10-23, reported: not on Route 110): "Lying in Terminus Cave." Route
   110's ball is boxed in by blocked tiles; both balls share flag 0x03EF. A main-chain change: new Gen 9 base in
   roms/test-gen9 (9f2e5b2b). `rom/` = roms/current = "(my placements 54)" = **9932ea5b...**, = the whole chain.
   NOTES, *The Zygarde Cube is in Terminus Cave*.

## Earlier handoff: the Windows PC, 2026-10-22 (later) -> the Mac

1. **The version number is 2.0** (`qolversion`: `QOL = "2.0"`; not a release: `release/`, the site's versions and
   the public repo still say 1.9). It sits mid-chain, so the whole chain was rebuilt and the Gen 9 base
   (`roms/test-gen9`) replaced with its `gen9` stage. `rom/` = "(my placements 38)" = **10203d90...** (8 bytes from
   84a2d8d7...: the digits of the four titles); the whole chain from the v1.4 archive gives it byte for byte. On
   the Mac: rebuild the chain, or take `rom/` as it is.
2. The showcase GIF for 2.0: `docs/showcase/showcase-v2.0.gif` (the README still shows 1.9's until a release);
   made by `_testrun/showcase20/montage.py` from clips filmed on build 38 (NOTES, *Version 2.0 and its showcase*).

## Last handoff: the Windows PC, 2026-10-22 -> the Mac

1. **New step `gen9anim`** between `gen9abil` and `kitakami`: the 48 Gen 9 moves play animations of their own
   (43 scripts in the game's animation language). Assembled once (`build.py`, xPack's arm-none-eabi-as); the patcher
   only reads `gen9anim.bin` and `gen9anim.sym`: `python -I patches/gen9anim/gen9anim_patch.py in.gba out.gba`. It
   takes 0x09E38000..0x09E3C000; gen9abil's claim is now 0x09E33000..0x09E38000 (its output unchanged). The three
   `rebuild_chain.py` copies and `paldea/rebuild.py`'s TAIL run it. `rom/` = the working ROM = "(my placements
   37)" = **84a2d8d7...** (= 3c9f52c1... + the patch); `roms/before-kitakami/` = **5da2d7f6...** (on the Mac: the
   patch on 3d32f3cf...). NOTES, *The Gen 9 moves' own animations*.
2. The whole chain from the v1.4 archive gives 84a2d8d7... byte for byte (100 s).

## Last handoff: the Windows PC, 2026-10-21 (late night) -> the Mac

1. **New step `gen9abil`** between `eggrelearn` and `kitakami`: the Gen 9 abilities work in battle (each its own
   id from 0x101, its own name and messages; 34 with their Scarlet/Violet effect, Zero to Hero without one - no
   Hero Form). C code, compiled once with xPack arm-none-eabi-gcc 12.2.1 (`build.py`; `ARMGCC=<its bin>` elsewhere);
   the patcher only reads `gen9abil.bin` and `gen9abil.sym`, so the Mac needs no compiler unless it changes the C:
   `python -I patches/gen9abil/gen9abil_patch.py in.gba out.gba`. It stands in front of 25 engine routines (`WRAP`):
   a later patch that hooks one of them chains through its wrapper. The three `rebuild_chain.py` copies and
   `paldea/rebuild.py`'s TAIL run it. `rom/` = the working ROM = "(my placements 36)" = **3c9f52c1...**
   (= 767e052c... + the patch); `roms/before-kitakami/` = **3d32f3cf...** (on the Mac: the patch on c2c97e5e...).
   NOTES, *The Gen 9 abilities work in battle*.
2. The whole chain from the v1.4 archive gives 3c9f52c1... byte for byte (135 s; main game alone still 265a0e93...).

## Last handoff: the Windows PC, 2026-10-21 (night) -> the Mac

1. **New step `eggrelearn`** between `iconnight` and `kitakami` (the user: "yeah in party relearner"): the Move
   Relearner (the party menu's Moves, and the Fallarbor tutor: one screen) lists egg moves after the level-up moves,
   up to 64 (the screen held 25). Code only, no Crest ROM needed: `python -I patches/eggrelearn/eggrelearn_patch.py
   in.gba out.gba`; no other step touches its bytes. The three `rebuild_chain.py` copies and `paldea/rebuild.py`'s TAIL
   run it. `rom/` = the working ROM = "(my placements 35)" = **767e052c...** (= 8dafe8d1... + the patch);
   `roms/before-kitakami/` = **c2c97e5e...** (on the Mac: the patch on 3e75e37b...). NOTES, *Egg moves in the Move
   Relearner*.
2. The whole chain from the v1.4 archive gives 767e052c... byte for byte (113 s; main game alone still 265a0e93...).

## Last handoff: the Windows PC, 2026-10-21 (evening) -> the Mac

1. **Area Zero's people in pictures of their own** (the user: "reusing npcs make the game look cheap"; the mock-up:
   "everything is great"): no new step - `paldea` (`cast.py`, `sprites/people*.py`) and `kitakami` (`ktrainers`,
   `ksprites`, `kchapters`, `editor`, `regions`) changed. Map sprites for Nemona, Arven, Penny, Jacq, AI Sada, AI Turo
   (the hack's sprite entries 174-178, 180; palette tags 0x1141-0x1144), battle pictures 250-252 (Nemona, the AIs);
   Kitakami's Carmine and Kieran are pictures 253, 254 now and its tables are found through the code words. Area
   Zero's sprite block runs to the ROM's end (0x09FFC000..0x0A000000 taken: proof in NOTES). `rom/` = the working ROM
   = "(my placements 33)" = **8dafe8d1...**; `roms/before-kitakami/` = **3e75e37b...**. NOTES, *Area Zero's people in
   pictures of their own*.
2. On the Mac: Kitakami now needs Area Zero's people in the game it goes on (`ksprites.check`: entry 174 must be Area
   Zero's Nemona), so it goes on `roms/before-kitakami`'s 3e75e37b..., not on an older one. The whole chain from the
   v1.4 archive gives 8dafe8d1... byte for byte.

## Last handoff: the Windows PC, 2026-10-21 -> the Mac

1. **Two new steps `contexit` and `iconnight`** between `paulgift` and `kitakami` (a player's report: stuck inside a
   tree in Petalburg Woods after Continue; the DexNav bar's Sunkern / Spearow in odd colours). Code only, no Crest ROM
   needed, and neither touches what another step touches: `python -I patches/contexit/contexit_patch.py in out`, then
   `python -I patches/iconnight/iconnight_patch.py in out`. On the Mac: both on top of `rom/`'s old 8aeca761... give
   the new `rom/` byte for byte. The three `rebuild_chain.py` copies and `paldea/rebuild.py`'s TAIL run them. `rom/` =
   the working ROM = "(my placements 32)" = **66d87291...**; `roms/before-kitakami/` = the `iconnight` stage,
   **daa23880...** (on the Mac: both patches on 0813e72e...). NOTES, *Continue walked you into a tree; the DexNav icon
   at night*.
2. The whole chain from the v1.4 archive with the two steps gives 66d87291... byte for byte (main game alone still
   265a0e93...).

## Last handoff: the Windows PC, 2026-10-20 -> the Mac

1. **New step `keytrainers`** between `wilditem` and `kitakami`: the key trainers' teams with Gen 9 Pokemon (by
   Luciano Fire - credit them; the user: "merge to my current rom"). Data only, no Crest ROM needed: `python -I
   patches/keytrainers/keytrainers_patch.py in.gba out.gba` applies `keytrainers.json` (42 trainers, 549 bytes, every
   old byte checked; `make_data.py` makes it from the coworker's ROM). The three `rebuild_chain.py` copies and `paldea/rebuild.py`'s TAIL run it. `rom/` = the working
   ROM = "(my placements 28)" = **1ecd960b...** (= 8dac47f0... + the coworker's bytes: the whole chain from the v1.4
   archive gives it byte for byte). NOTES, *The key trainers' Gen 9 teams*.
2. `roms/before-kitakami/` is now the chain's `keytrainers` stage, **bb39febc...**; on the Mac, make it by running the
   patch on the `wilditem` stage (1ea26019...), or rebuild. A Kitakami build from the old file lacks the teams.
3. **Kitakami** (2026-10-20, the user's reports): Carmine stops you one step up from the bus stop (a coord event:
   the first in Kitakami), and Mossui's weather is put back after a battle (the hack carries a battle's weather onto
   the map). Only `patches/kitakami/` changed: `rom/` = "(my placements 30)" = **6b167bfa...**. The Kitakami story
   tests meet Carmine by that step now (`steps_story.lua`). NOTES, *Kitakami: Carmine stops you*.
4. **New step `paulgift`** between `keytrainers` and `kitakami` (a report: Paul gave a second EV-IV Display in Fortree;
   the user: "paul doesn't need to give again"): a 5-byte goto over his gift line and giveitem. Also the Quest Log's
   Key Items row for it (`questlog/keyitems.py`, `portraits.LOC_OVERRIDE`): "Your PC", in the main chain, so
   `roms/test-gen9` changed too (**a9f9397b...**). `rom/` = "(my placements 31)" = **8aeca761...** (the whole chain
   gives it byte for byte); `roms/before-kitakami/` = the `paulgift` stage, **0813e72e...**. On the Mac (no `gen9`):
   take `rom/`; `paulgift` alone on bb39febc... gives Paul's fix without the new Quest Log text, and
   `questlog_on_top.py` was not tried for it (it predates `gen9journal`, whose rows point at the moved strings too).
   NOTES, *Paul's second EV-IV Display*.

## Last handoff: the Windows PC, 2026-10-18 -> the Mac

1. **New step `wilditem`** between `gen9journal` and `kitakami` (a report: the Abandoned Ship's Pikachu held an Oran
   Berry, not the Light Ball its script gives it). Code only, no Crest ROM needed: `python -I
   patches/wilditem/wilditem_patch.py in.gba out.gba`. The three `rebuild_chain.py` copies and `paldea/rebuild.py`'s
   TAIL run it. `rom/` = the working ROM = "(my placements 27)" = **8dac47f0...** (= 382cf97c... + this patch: the
   whole chain from the v1.4 archive gives it byte for byte). NOTES, *A wild Pokemon keeps the item it was given*.
2. `roms/before-kitakami/` (Kitakami's editor builds on it) is now the chain's `wilditem` stage, **1ea26019...**; on
   the Mac, make it by running the patch on the 8462fa6f... game (the `rom/` of before Kitakami), or rebuild.
3. Since the patch sits before `kitakami`, a Kitakami build made from the old before-kitakami file lacks the fix.

## Last handoff: the Windows PC, 2026-10-17 -> the Mac

1. **Kitakami is in the game** at the user's word ("try to merge with main rom, make sure to not touch something
   unrelated"): the chain is now ... `gen9journal` -> `kitakami` (with the user's Kitakami placements: on the PC
   `roms/test-kitakami/placements.txt`; `rom/kitakami-placements.txt` is the copy the game was built with). `rom/` =
   the working ROM = "(my placements 26)" = **382cf97c...**; the game before it 8462fa6f.... The three
   `rebuild_chain.py` copies on the PC and `patches/paldea/rebuild.py` run the new step. NOTES, *Kitakami*.
2. **Building Kitakami again on the Mac** (`patches/kitakami/krebuild.py`, its editor): Kitakami cannot go onto a
   game that has it, so they build on `roms/before-kitakami/Hyper Emerald - the game before Kitakami.gba` beside the
   repo (`krebuild.base_rom()`). On the PC `rebuild.py` keeps that file current; on the Mac make it once from git,
   the `rom/` of before this commit (8462fa6f...), or with the chain's `gen9journal` stage.
3. In Area Zero's placements Jacq must stay at 70,32 in Mossdeep: Kitakami's Briar takes his tile after the ending
   (the kitakami step stops and says so otherwise).
4. The guide site still lists Kitakami's five as not in this version: it describes the v1.9 release.

## Last handoff: the Windows PC, 2026-10-15 (evening) -> the Mac

1. **The whole of Gen 9 is in the game** at the user's word ("patch to my current rom, including every fix and whole
   gen9"): the chain is now ... `zhtext` -> `speciesx` -> `gen9` -> `paldea` -> `gen9rest` (Crest ROM) -> `gen9dex` ->
   `gen9egg` -> `gen9journal`. `rom/` = the working ROM = "(my placements 23)" = **65b5a7f6...** (2026-10-16: the
   Evolutions chapter with the Gen 9 families; ca71db7b... the evening before, without); the main game alone
   bf8a9d28.... The three `rebuild_chain.py` copies on the PC and `patches/paldea/rebuild.py` run the four new steps.
   A save opened in it has its Gen 9 marks moved once (`gen9dex`): it must not go back to 370503cf... or older.
2. **New**: `patches/gen9journal/` (the Quest Log's Legends: 20 Paradox, five Kitakami legends Locked, 119 to catch,
   three-digit counts; Side Content: ten Area Zero rows); the move-info tag is an L key and a magnifying glass
   (`patches/lmoveinfo/art.py`); Nemona's rematch sets 0x43E4 (`patches/paldea`). NOTES, *The Quest Log's Gen 9
   rows*. Tested on the PC (`patches/gen9journal/test_gen9journal.lua`).
3. **For the Kitakami work**: Okidogi, Munkidori, Fezandipiti, Ogerpon and Pecharunt are Locked rows at the end of
   the Legends (`gen9journal_patch.py`, `KITAKAMI`; a row's second halfword 1). When they can be met, make them
   ordinary rows inside the counted part (and the count, `legend_all`'s NLEG, the chapter's total, and row 0's
   texts follow from the patcher), with where-texts read from the game.
4. The Whole Gen 9 test builds (`rom/unreleased/whole-gen9-test/`) are superseded by the game itself.

## Last handoff: the Mac, 2026-10-15 -> the other PC

What the Mac did that day (all pushed; the details are in NOTES, *Side quests rechecked* and *Whole Gen 9 test 5*):

1. **Side quests fixed in the game.** `patches/sidefix/` (in the chain after `iconpalfix`, before `zhtext`): Blue's
   Galar gift can be reached (she stood inside the wall of the Lilycove Museum 1F), the demon soul's Magikarp in
   Steven's residence no longer shares Dawn's flag, two text slips. The Quest Log's Side Content and Key Items rows
   that were wrong are rewritten (`patches/questlog/sidecontent.py`, `keyitems.py`, `portraits.py`; the Contest
   Pass row is gone). `rom/` = the Mac's working ROM = **370503cf...**; the whole chain from the v1.4 archive with the
   Crest ROM gives it byte for byte.
2. **Whole Gen 9 test 4 and test 5** in `rom/unreleased/whole-gen9-test/` (test only, never the main game; each with
   its `.sav`, a copy of the user's save of 14 October; test 3 kept until the user says it can go):
   * test 4 = the game above + `gen9rest`: f71d606c..., "(DexNav open)" e6d75ed6...;
   * test 5 = test 4 + `gen9dex` (Gen 9 at its official Pokedex numbers 906-1025; a save's Gen 9 marks are moved to
     the new numbers once - ONE WAY, such a save must not go back to the main game; four-digit numbers on the
     Pokedex page) + `gen9egg` (egg moves for 41 more Gen 9 Pokemon): 33ee387f..., "(DexNav open)" 29fbf86d....
     The user: "for order of pokedex, reorder only gen9, don't touch the original rom since I don't wanna risk bugs".
3. **Tests.** The user's 8-point list on test 5 (Pokedex screens, TMs / Relearner / egg moves, the new moves' texts,
   forms, the 22 stand-in abilities, the DexNav for every new wild Pokemon, v1.8 saves, 32 hours of random play):
   all passed; the folder's READ ME says it in the user's terms, NOTES with the numbers. The Mac's harness is
   `tests/gen9mac/` (*Working on macOS* below); its Lua files run on the Windows mGBA dev too (they `dofile` the
   Windows `test_boot.lua` path, which `runner.py` rewrites on the Mac; set `GEN9_DIR` and the env each one lists).
4. **v1.8 rebuilt exactly** on a machine with no original ROM (sha1 ade383ba, the release's): NOTES, *Whole Gen 9 test
   5*, the v1.8 saves bullet. Useful whenever an old release has to be reproduced.
5. **The story played by hand from New Game** on test 5 (`tests/gen9mac/test_play.lua`, plans in
   `tests/gen9mac/play/`): Journal steps 1-2 and most of 3 (to Roxanne's gym), no fault of the game found; the
   user stopped it ("I think it is ready"). The user's plan: the release will be the whole Gen 9 + Area Zero.
   NOTES, *Playing the story by hand*.

What the other PC does next:

1. `git pull`. The game in `rom/` (370503cf...) is the new working ROM - copy it over the working ROM / start the
   next "(my placements N)" from it, or rebuild: add `sidefix` after `iconpalfix` in the three copies of
   `rebuild_chain.py`; the full game must come out 370503cf..., the main game alone 048790b4....
2. The Whole Gen 9 test, if it is rebuilt there: after `gen9rest`, `python -I patches/gen9dex/gen9dex_patch.py in out`,
   then `python -I patches/gen9egg/gen9egg_patch.py in out`, then `patches/gen9rest/dexnav_open_test.py` for the
   twin - 33ee387f... and 29fbf86d.... Both patchers refuse anything but the numbering and tables they expect.
3. Not in the push: the Kitakami / Ogerpon work that is in progress on the Mac (`patches/kitakami/`,
   `rom/unreleased/kitakami/` STORY.md and `kit/`) - not committed.
4. Still open, nothing decided: in battle messages a stand-in ability goes by the name of the one it copies
   ("Oinkologne's Mummy!"; the summary shows its own name); the game's Sand Force (and so Rocky Payload) boosts Rock
   moves without a sandstorm; Flatter stops the game in a double battle (below).

## Current state

Applied to the working ROM and verified in mGBA (on a real late-game save, Sinnoh post-game):

- everything in [CHANGELOG.md](CHANGELOG.md) up to and including **2026-09-23**;
- the working ROM's Option screen says **+QoL2.0** since 2026-10-22, and **v2.0 is released** (2026-10-24, the user:
  "push to release repo"): Kitakami and everything since v1.9 are public; v1.9 (2026-10-16) made the whole of Gen 9
  and Area Zero public (the user: "Yes, both public", then "Full v1.9 release");
- the last published release is **v2.0** (2026-10-24, game sha1 fb949e02...; v1.9 was 2026-10-16 with 65b5a7f6..., v1.8 2026-10-07; see CHANGELOG for v1.6 to v2.0); v1.5 (2026-09-23) added, on top of v1.4 (DexNav, Sinnoh map + fly,
  R button, News Tracker fix):
  * gold healthbox on your own shinies too (`patches/shinybox/`);
  * the **Journal** key item: next story objective from Prof. Birch to Cogita, 84 steps traced in the game's
    scripts (`patches/journal/`: `steps.py` is the table; `make_tests.py` + `test_journal.lua` +
    `check_journal.py` check all 94 scenarios byte for byte). Rules and every flag gotcha: NOTES, JOURNAL;
  * the **Quest Log**: the Journal opens a checklist screen, one chapter a page (`patches/questlog/`; it rebuilds
    and verifies the Journal blob, then calls its routines. `test_questlog.lua` + `check_questlog.py` run the
    same 94 scenarios through the screen; R in the Start menu opens it too; a fifth chapter, Legends, lists the legendaries from
    `patches/questlog/legends.py`, a sixth the key items from `keyitems.py`, a seventh
    side content from `sidecontent.py`; the log opens on a chapter grid; lists are Unbound-style with an info
    panel - portraits and locations in `portraits.py`). NOTES, QUEST LOG;
  * berry numbers in the Bag: "No?2" -> No44-71 (`patches/berrynum/`, four sites - the hack has two copies of
    its item-name routine);
- the guide's post-game and Lost Artifacts walkthroughs were rewritten from the scripts and are already live
  (public repo, 2026-09-21). `tools/romdata/scripts.py`, `prereq.py` and `savefile.py` are the tools that did it.

Order of the newest patches on top of v1.4: `shinybox` (both sides) -> `journal` -> `berrynum` -> `speciesnames` -> `questlog` -> `leaguefly` -> `leaguetext` -> `qolversion` -> `candynpc` -> `naturefix` -> `hypertrain` -> `hisuimap` -> `dexdesc` -> `ovalcharm` -> `flyicons` -> `eggmoves` -> `expshare` -> `bagslots` -> `itemdesc` -> `textfix` -> `hmfree` -> `instanttext` -> `fastsurf` -> `dexnavseen` -> `dexnavscan` -> `dexnavui` -> `keyring` -> `repelfix` -> `nocandynpc` -> `lmoveinfo` -> `daynight` -> `rngseed` -> `expgain` -> `namingkb` -> `fusionfix` -> `dexnavabil` -> `shinyfade` -> `evivpal` -> `mistmsg` -> `objpal` -> `roamfix` -> `sprframe` -> `summitfix` -> `goldbox` -> `ballfree` -> `sheetonce` -> `iconpalfix` -> `sidefix` -> `dexstats` -> `zhtext`, and for the working ROM then `speciesx` -> `gen9` -> `paldea` -> `gen9rest`
-> `gen9dex` -> `gen9egg` -> `gen9journal` (the last four since 2026-10-15: NOTES, *The Quest Log's Gen 9 rows*) -> `wilditem`
(2026-10-18) -> `keytrainers` (2026-10-20) -> `paulgift` (2026-10-20) -> `contexit` -> `iconnight` (2026-10-21) ->
`kitakami` (2026-10-17)
(`nocandynpc` takes `candynpc`'s NPC back out - NOTES, *Rare Candy NPC removed*; `fusionfix` chains on the ClearBag
trampoline `bagslots` made, so it comes after it - NOTES, *Fusion slots*; `dexnavabil` is the DexNav bar's ability,
in the working ROM since 2026-10-08 and in no release yet - NOTES, *DexNav bar: the ability it names*; `shinyfade`,
`evivpal` and `mistmsg` are the fixes for a player's report of 2026-10-09, in no release yet either - NOTES, *A player's
report: four things*; `textfix` and `eggmoves` grew on 2026-10-10 - 58 pages of text changed to fit the message
box, and Mr. Mime's and Mime Jr.'s egg move lists - in the working ROM, in no release yet: NOTES, *A second report*;
`objpal` (2026-10-10, after `mistmsg`, before `zhtext`) gives back an object palette that nothing on screen draws with -
the hack's allocator handed the seventh kind of thing on a map a spare slot that does not keep its colours; in the
working ROM, in no release yet: NOTES, *Objects' palettes given back*;
`roamfix` (2026-10-10, after `objpal`, before `zhtext`) keeps the roaming Tornadus and Thundurus in Sinnoh after
Continue - the hack tells a Sinnoh roamer by a byte that is not in the save; in the working ROM, in no release yet:
NOTES, *Tornadus and Thundurus roamed Hoenn after Continue*;
`sprframe` (2026-10-11, after `roamfix`, before `zhtext`) drops a sprite picture copy that cannot be a picture - some
of Hisui's wandering Pokemon have fewer pictures than their walking animation shows, and the game copied what
lies after their table over video memory (a player's report: a Hisui map in stripes until the next battle); in the
working ROM, in no release yet: NOTES, *A sprite's missing picture copied over video memory*;
`summitfix` (2026-10-12, after `sprframe`, before `zhtext`) keeps Kitty's nameless stone when an attempt at the summit
fails and lets her give it again to a save that already lost it - script bytes only, so it gives the same 440 bytes
in the chain or on top of the finished game; that is how `rom/` got it on the Mac, which cannot run `gen9`.
`rebuild_chain.py` on the Windows PC has the name after `sprframe` since 2026-10-12, and the full game came out there
as sha1 36c0f986..., the same file: NOTES, *The summit: a lost attempt ended the quest*;
`goldbox` (2026-10-13, after `summitfix`, before `zhtext`) gives a shiny Pokemon's gold healthbox a sprite palette
slot of its own (tag 0x5E63) and the status icons on it their real colours, and replaces the game's
LoadSpritePalette and AllocSpritePalette so that, when no slot is free, the type badges and then the gold give
theirs up - a report: "the shiny box sometimes still disappear" (in double battles a three-palette move
animation overwrote the gold). Like `summitfix` it gives the same bytes in the chain or on top of the finished
game (compared), so the Mac can apply it to `rom/`. In the working ROM, `rom/` and "(my placements 18)", sha1
8c155ddc..., in no release: NOTES, *The gold healthbox kept its palette*;
`ballfree` (2026-10-13, after `goldbox`, before `zhtext`; two bytes, the same in the chain or on top) lets the game
free the graphics of the hack's own Poke Balls (ids 12-26) after their animation, as it does for the first twelve:
they stayed loaded all battle, two palette slots a battler, which is what took the gold healthbox's slot whenever a
move healed. The working ROM, `rom/` and "(my placements 19)" are adcc2707...: NOTES, *The hack's own balls were
never let go of*;
`sheetonce` (2026-10-13, after `ballfree`, before `zhtext`; 48 bytes at 0x08FEE100 and one pool word of the hack's,
the same in the chain or on top) stops the hack loading the Mega Evolution icon's 32-tile sheet again at every
opening of the move menu - that ate every sprite tile in seven turns of a double battle, and move animations then
lost their pictures. The working ROM, `rom/` and "(my placements 20)" are 2db23aa2...: NOTES, *The move menu ate
the sprite tiles*;
`iconpalfix` (2026-10-15, after `sheetonce`, before `zhtext`; two bytes, the same in the chain or on top) gives the
DexNav search bar's icon its own palette: LoadMonIconPalette still sent every species above 412 to palette 1. The
working ROM, `rom/` and "(my placements 21)" are 40685de4...: NOTES, *The DexNav bar's icon in its own colours*.
`sidefix` (2026-10-15, after `iconpalfix`, before `zhtext`; 263 script, map and text bytes, most of them one line
moved up two bytes; the same in the chain or on top) puts Blue (Lilycove Museum 1F) on the floor where she can be talked to and moves Steven's Island's demon
soul off Dawn's flag 0x4118 onto his own trainer flag 0x4552. The same day the Quest Log's Side Content and Key
Items texts changed (`patches/questlog/sidecontent.py`, `keyitems.py`, `portraits.py`): that is `questlog`'s data,
early in the chain, so the Mac put it into the finished game with `patches/sidefix/questlog_on_top.py` (the two
main-chain builds' difference, plus `paldea`'s copies of the Journal's and the Legends' panel rows re-pointed, as
`paldea` itself does when the chain runs again). The Mac's game, `rom/` and the working ROM there are
370503cf...; the main game alone 048790b4.... The Mac has the Crest ROM since that day (`rom/Crest_v1.0.F.gba`,
git-ignored) and built the whole chain with `speciesx`, `gen9` and `paldea`: 370503cf... byte for byte (and
40685de4... without the fixes). **The Windows PC**: add `sidefix` after `iconpalfix` in the three copies of
`rebuild_chain.py`. NOTES, *Side quests rechecked*.
The **Whole Gen 9 test** (`rom/unreleased/whole-gen9-test/`, never the main game) is now test 5: the game +
`gen9rest` + `gen9dex` (Gen 9 at its official numbers; a save's marks are moved once) + `gen9egg` (Gen 9 egg moves),
and `gen9rest/dexnav_open_test.py` for the "(DexNav open)" twin. NOTES, *Whole Gen 9 test 5*.
Still OPEN: Flatter stops the game in a double battle (the game of before too);
`rom/unreleased/` (2026-10-12) holds design work that is not in the game: the trial kit and results for turning
Area Zero's time crystals into a rift (the user chose it; built into `patches/paldea` on the Windows PC the same
day - the craters' two time objects are that rift in the working ROM, `rom/` and "(my placements 16)", sha1
52db9719...: NOTES, *The time rift*; since the version number went to 1.9 later that day the three are
d7e673b3...; with `goldbox`, 2026-10-13, they were 8c155ddc... ("(my placements 18)"), adcc2707... with `ballfree` (19) 2db23aa2... with `sheetonce` ("(my placements 20)") and 40685de4... with `iconpalfix` ("(my placements 21)")), and the
mock-ups and story notes for a teal "Kitakami Hall" (an Ogerpon story). Its README says what was decided and what
is open. It is under `rom/` so that it stays out of the public repo;
`zhtext` is the leftover Chinese and
must stay last: it checks the Chinese bytes it replaces - NOTES, *Leftover Chinese*; its data files are made by
`translation/official/`, which needs a pret/pokeemerald checkout and is not needed to build).
After pulling a change to any patch that is not last, rebuild the whole chain from the v1.4 archive + the shinybox
edit - see NOTES, *Working ROM rebuilt*. `bagslots` changes the save: see NOTES, *Items pocket 100 -> 200 slots*.
`questlog_patch.py` needs numpy and the move and place names in `tools/romdata/out/` (git-ignored: run
`python tools/romdata/dump_tables.py` once with `HE_ROM` set to a build of the game). Tests: `make_tests.py` (94 cases); `test_journal.lua` on the chain's Journal-only
stage (after `journal`, before `questlog`) and `test_questlog.lua` on the end, with their check_*.py;
`test_hypertrain.lua`; `test_bagslots.lua` then `test_bagslots_reload.lua`, `test_bagslots_newgame.lua`,
`test_bagslots_saves.lua`, `test_bagslots_state.lua` (a pre-1.6 save state); `test_fusionfix.lua` (four scenarios,
`SCEN=`; with `OLD=1` it expects an unpatched build's answers) and `test_fusionfix_newgame.lua`.

(On a ROM that already has the old shinybox, "both sides" is the 2-byte edit at `0x08FDA136` in NOTES; the
patcher itself only builds from a clean BattleMainCB2.)

The chain is now: ... `sinnohmap` → `dexnavchain` → `rbutton` (see *Rebuild from source* in the README). While
iterating on the DexNav, build from a ROM that has everything up to `sinnohmap` (the working ROM before
`dexnavchain`), then apply `dexnavchain` and `rbutton` on top.

Release mechanics (patch file, checksums, GitHub release) are described in the README; the release patch is
generated against the translated ROM, never against a ROM you cannot reproduce.

## Working on macOS

- Python: a venv with `keystone-engine`, `capstone`, `pillow`. On Apple silicon the keystone wheel ships no
  library: `brew install keystone` and copy `libkeystone.dylib` into the venv's `site-packages/keystone/`;
  Python 3.12+ also needs `pip install setuptools` (keystone imports `distutils`).
- mGBA: the release app has no `--script`; use the dev build (`mGBA-build-latest-macos.dmg` from
  `https://s3.amazonaws.com/mgba/`). Run tests muted and fast:
  `mGBA.app/Contents/MacOS/mGBA -C mute=1 -C fpsTarget=2000 -C audioSync=0 -C videoSync=0 --script test.lua game.gba`
  on copies of the ROM and `.sav` in a scratch folder. `patches/dexnavchain/test_boot.lua` is the shared boot
  harness the newer tests use (set `DIR`).
- Many tests at once, no window: `tests/gen9mac/runner.py jobs.json outdir [workers]` with `MGBA_HEADLESS` pointing
  at an `mgba-headless` built from source (two lines added to `src/platform/headless-main.c`: a video buffer for
  screenshots and `mCoreAutoloadSave` for the `.sav`; cmake with `-DBUILD_HEADLESS=ON -DBUILD_QT=OFF -DBUILD_SDL=OFF`
  and Lua 5.4). It runs a game hour in about 70 seconds. It does not call Lua breakpoints: where a test needs one,
  the job's `patch` writes the needed bytes into that run's copy of the ROM. The `gen_jobs*.py` files make the
  job lists of NOTES' test passes.
- pret's `pokeemerald.sym` (the `symbols` branch) matches this ROM for most vanilla code; the menu code from about
  `0x08197000` is shifted (+0xC04 at `ClearStdWindowAndFrame`), so disassemble before trusting a symbol there.

## Where the unfinished edges are

- **Gen 9 legendaries, Paradox Pokémon, the Baxcalibur line (2026-10-08): in the working ROM since 2026-10-11, in no release.**
  `patches/speciesx/` grows the species tables from 1,200 to 1,280 slots; `patches/gen9/` fills 38 of them (official
  Scarlet/Violet data; pictures and cries from the Crest ROM) and makes their signature abilities work. A second
  pass the same day added seven signature moves (move ids 938-947: the move name, description and two power tables
  now have 1,024 entries), Booster Energy (item 769) and the Speed half of Protosynthesis / Quark Drive. They go
  LAST in the chain, after `zhtext`: `speciesx_patch.py in out`, then `python -I gen9_patch.py in out <Crest ROM>`,
  then `check_gen9.py before after`. The build is in `gba-trans/hyper-emerald/roms/test-gen9/`. What is open: nothing in the
  game hands these Pokémon or the item out yet (the user: "don't mind about the encounter yet"), six signature
  moves that Crest does not have either, and the guide / Quest Log tools, which still read 1,200 species at the
  old table addresses. Ogerpon's four masks stay four species (the user: "left Ogerpon as is"). NOTES, *Species
  tables* and *Gen 9*.

- **Area Zero, where the Gen 9 Pokémon are found (2026-10-08): in the working ROM since 2026-10-11 with the user's
  own placements and painting, in no release.** Since 2026-10-11 Jacq stands in Mossdeep from the start of the game
  and talks of his field trip (flag 0x43E2 once spoken to); the hole still comes with 0x41D5, and he knows you then
  (NOTES, *Jacq before the hole*). `patches/paldea/`
  goes after `gen9`: Jacq and a black hole in Mossdeep City after Team Rainbow Rocket (the Timeless Woods up to
  test 15; Mossdeep's own events are untouched and tested against the build without it), the wall (35/89), the
  crater in the past and in the future (35/90, 35/91; world.py: cut-corner terraces, a climbable waterfall), nine
  rooms (four research stations, the Crystal Cavern, the icy cave, the Zero Lab, the Underdepths, and the old
  Sealed Shrine kept empty) and the whole approved story: Penny and the four logs, Arven's sandwiches after the
  Titans, Nemona, the finale with AI Sada, AI Turo and the Protocol, the ending; after it the Gen 9 legends to
  catch and the four people living in the stations. The seventeen Gen 9 Pokémon that stand on the maps are
  overworld sprites from pokeemerald-expansion and the stations' recorder is drawn for the patch (mons.py,
  `sprites/`). The lab's door is shut until Arven and Nemona stand at it, which they do by themselves once
  everything before the finale is done, in any order. **Where everything stands and the ground itself are the user's
  to edit** (tests 11 and 12): `placements.txt` and `ground.txt` in `gba-trans/hyper-emerald/roms/test-paldea/`, with the
  mouse (`edit placements.bat`: editor.py, a local page that moves things and paints tiles as Hex Maniac Advance
  would, with "Tidy the edges": tidy.py works every terrace corner, path border and puddle rim out again from the
  painted shape) or by hand with `rebuild.bat`; check.py refuses what the game could not use. Their own build is
  the newest "(my placements N)" there, not a "test N". The terraces are drawn from the tileset's grass family
  since test 13 (the user found the rock family's sand-coloured corners and repainted them by hand). Since test
  14 the crater goes on past its edges (the user: "it got cut off when ran on the border"): four strips, maps
  35/102-105 that nobody enters, joined to both craters as connections (`world.beyond`, `maps.Map.connect`);
  nothing in the crater moved. Since test 15 Wo-Chien, Ting-Lu and Chi-Yu are in the Sealed Vault (35/101)
  behind the Crystal Cavern's second mouth: a sliding-floor puzzle, three stakes to pull (check.py plays it
  through), and there is a Booster Energy item ball in each crater. The user
  plays from emulator save states and seldom saves in the game: a new build needs an in-game save
  (`state_to_save.lua` makes one from a state), under the new ROM's name on the Desktop, where their mGBA keeps
  saves. Since test 17 the Journal has Area Zero as an optional quest (seven rows after "Steven is waiting";
  `patches/paldea/journal_az.py` replaces the Quest Log's compute so optional rows never take the current
  objective) and the Legends chapter its seven legendaries (99 in all: the count prints two digits).
  Since test 18 a legend caught or knocked out is gone for good. Since test 19 the editor can take tiles for
  the two craters from any map drawn with the General tileset ("Take from another map...": `patches/paldea/tiles.py`,
  the user's `tiles.txt`; the craters then get a secondary tileset of their own, with room for 433 picture cells
  and 75 colours); without tiles.txt the build is unchanged. Also since test 19 (`patches/paldea/objpal.py`) the
  hack's object palette allocator gives back a slot nothing on screen draws with; it used to hand the seventh
  kind of thing on a map slot 10, which shows another sprite's colours (the user: Walking Wake miscoloured).
  It is the hack's code for every map: `patches/objpal/`, in the working ROM since 2026-10-10.
  Builds and a map guide in `gba-trans/hyper-emerald/roms/test-paldea/` (test 18 = "(my placements 9)"). On 2026-10-11 the user asked for one ROM
  ("everything should be into one rom now? area zero plus everything fix, change?"): the working ROM is the main
  chain's result + `speciesx` + `gen9` + `paldea` with their `placements.txt` and `ground.txt`
  (`_testrun/rel18/rebuild_chain.py` builds all of it; `--main` stops at the main game), the Gen 9 base in
  `roms/test-gen9` is built from the main game of that day, and "(my placements N)" is the same ROM under a fresh
  name - the one to open for the user, whose emulator has an old save state under the working ROM's name. Ask
  before any of it goes into a release. NOTES, *Area Zero* and *One ROM*.
  The craters' two time crystals are a shimmering time rift since 2026-10-12 (sprite slots 254 / 255, a
  four-frame kind in `mons.py`; Area Zero's sprite block has 164 bytes left and the hack's sprite table no spare
  entry): NOTES, *The time rift*.
  **The built ROM is in this repo, `rom/`, since 2026-10-12** (the user: "include the rom itself so that I can work
  easily no need to patch left and right"), with the placements it was built with. Private dev repo only: `main`
  tracks `dev/main` now, `_testrun/rel18/mirror_public.py` leaves out `rom/` and every `.gba`, and this checkout's
  `.git/hooks/pre-push` refuses to send a commit with a `.gba` anywhere but to `dev`. When the working ROM
  changes, copy it to `rom/` and put its sha1 in `rom/README.md`; commit and push when the user asks.

- **Open freeze report (a player's, 2026-10-09, RetroArch mGBA core, fast-forward 5-6x)**: "one time I was selecting
  something in my journal, the emulator got frozen". Not reproduced: 1.25 million frames of random input in the
  Quest Log on two builds (`_testrun/report/fuzz_questlog.lua`; NOTES, *A player's report: four things*). Not tried:
  opening it from the Bag, a save with other rows revealed. Ask for the screen and a save if it comes back.
- **Egg moves, left open (2026-10-10)**: Duraludon (species 274) has no egg move list (Sword/Shield: Mirror Coat,
  Night Slash, Slash) - adding one makes the table longer, which `gen9_patch.py` also does. And a player asked for
  BDSP's egg moves where Sword/Shield made them TRs (Buneary's Cosmic Power): the hack follows Sword/Shield and has
  those on its tutor list; the union of both games would add 511 moves to 133 species. The user has not decided.
  NOTES, *A second report*. The guide's Pokédex (`tools/build_pokedex.py` -> `site/src/data/pokedex.json`) was
  not rebuilt: until it is, it shows the old egg moves for Goldeen, Bonsly, Mr. Mime and Mime Jr.
- **Text width**: a line of script text must not pass 216 px (208 before a ▼). `python tools/text_overflow.py <rom>`
  lists the pages that do; run it after any change to the translation. The current build gives none.
- **Open crash report (a player's, no save)**: Berries pocket, cursor from Occa onto Jaboca -> "Jumped to invalid
  address: E3A02004" (a function pointer read from address ~0). Not reproduced on any build with that exact
  pocket, boy or girl, or with every berry walked over. `patches/berrynum/test_berrynum_report.lua` rebuilds the
  reported pocket and dumps registers and the stack if it crashes - run it on the player's save if one turns up.

- **DexNav** — never played through: a water hunt while surfing, a Rock Smash hunt, a real trainer battle breaking
  the chain, Repel with the patch, Safari Zone catches. The arrow points sideways first and can point into a
  boulder; the patch is always a free tile at the player's height, but a maze-like cave can still wall it off.
  More in [docs/DEXNAV-PROGRESS.md](docs/DEXNAV-PROGRESS.md).
- **Shelved, root cause known**: in-party nature changer (`patches/naturemenu/`), PC item sort
  (`patches/pcsort/`). Both are written, neither is verified in game.
- **Translation**: roughly 365 strings could not be placed in safe space and are still Chinese. Reclaiming
  space or shortening translations is the way in; `translation/` holds the toolchain.
