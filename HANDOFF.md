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
tools/gif_editor.py                    GIFs out of docs/showcase with the mouse, a local page (`gba-trans/showcase/gif editor.bat`)
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
- the working ROM's Option screen says **+QoL1.9** since 2026-10-12, and **v1.9 is released** (2026-10-16): the
  whole of Gen 9 and Area Zero are public (the user: "Yes, both public", then "Full v1.9 release");
- the last published release is **v1.9** (2026-10-16, game sha1 65b5a7f6...; v1.8 was 2026-10-07; see CHANGELOG for v1.6 to v1.9); v1.5 (2026-09-23) added, on top of v1.4 (DexNav, Sinnoh map + fly,
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

Order of the newest patches on top of v1.4: `shinybox` (both sides) -> `journal` -> `berrynum` -> `speciesnames` -> `questlog` -> `leaguefly` -> `leaguetext` -> `qolversion` -> `candynpc` -> `naturefix` -> `hypertrain` -> `hisuimap` -> `dexdesc` -> `ovalcharm` -> `flyicons` -> `eggmoves` -> `expshare` -> `bagslots` -> `itemdesc` -> `textfix` -> `hmfree` -> `instanttext` -> `fastsurf` -> `dexnavseen` -> `dexnavscan` -> `dexnavui` -> `keyring` -> `repelfix` -> `nocandynpc` -> `lmoveinfo` -> `daynight` -> `rngseed` -> `expgain` -> `namingkb` -> `fusionfix` -> `dexnavabil` -> `shinyfade` -> `evivpal` -> `mistmsg` -> `objpal` -> `roamfix` -> `sprframe` -> `summitfix` -> `goldbox` -> `ballfree` -> `sheetonce` -> `iconpalfix` -> `sidefix` -> `zhtext`, and for the working ROM then `speciesx` -> `gen9` -> `paldea` -> `gen9rest`
-> `gen9dex` -> `gen9egg` -> `gen9journal` (the last four since 2026-10-15: NOTES, *The Quest Log's Gen 9 rows*)
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
  then `check_gen9.py before after`. The build is in `gba-trans/roms/test-gen9/`. What is open: nothing in the
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
  to edit** (tests 11 and 12): `placements.txt` and `ground.txt` in `gba-trans/roms/test-paldea/`, with the
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
  Builds and a map guide in `gba-trans/roms/test-paldea/` (test 18 = "(my placements 9)"). On 2026-10-11 the user asked for one ROM
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
