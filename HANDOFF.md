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

## Layout

```
patches/<feature>/<feature>.s          Thumb source, assembled at a fixed BASE
patches/<feature>/<feature>_patch.py   asserts the ROM matches, assembles, writes, repoints
patches/<feature>/test_*.lua           mGBA Lua that drives the game and checks the feature
tools/                                 ROM mining and asset conversion (region maps, encounter tables…)
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
5. **Never write to the save.** No feature so far stores anything in SaveBlock1/2. Scratch goes in EWRAM
   that has been *measured* to be unused (fill a candidate with a pattern, play through battles, menus, the
   bag, a save and a Pokénav call, then check what survived — `patches/dexnavchain/test_scratch_ram.lua`).
6. **Verify in the emulator, not by reading.** Every feature here has a Lua test that drives the game and
   reads memory back. Three of the last four bugs were invisible in the source and obvious in a screenshot.

## Current state

Applied to the working ROM and verified in mGBA (on a real late-game save, Sinnoh post-game):

- everything in [CHANGELOG.md](CHANGELOG.md) up to and including **2026-09-22**;
- the last published release is **v1.4** (DexNav, Sinnoh map + fly, R button, News Tracker fix). **Not yet
  released**, all applied and tested:
  * gold healthbox on your own shinies too (`patches/shinybox/`);
  * the **Journal** key item: next story objective from Prof. Birch to Volo, 74 steps traced in the game's
    scripts (`patches/journal/`: `steps.py` is the table; `make_tests.py` + `test_journal.lua` +
    `check_journal.py` check all 84 scenarios byte for byte). Rules and every flag gotcha: NOTES, JOURNAL;
  * berry numbers in the Bag: "No?2" -> No44-71 (`patches/berrynum/`, four sites - the hack has two copies of
    its item-name routine);
- the guide's post-game and Lost Artifacts walkthroughs were rewritten from the scripts and are already live
  (public repo, 2026-09-21). `tools/romdata/scripts.py`, `prereq.py` and `savefile.py` are the tools that did it.

Order of the newest patches on top of v1.4: `shinybox` (both sides) -> `journal` -> `berrynum`.

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
- pret's `pokeemerald.sym` (the `symbols` branch) matches this ROM for most vanilla code; the menu code from about
  `0x08197000` is shifted (+0xC04 at `ClearStdWindowAndFrame`), so disassemble before trusting a symbol there.

## Where the unfinished edges are

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
