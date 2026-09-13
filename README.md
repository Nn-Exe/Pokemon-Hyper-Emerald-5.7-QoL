# Hyper Emerald v5.7 (Lost Artifacts) — English translation + quality-of-life patches

Binary patches for the Chinese Pokémon Emerald ROM hack **Hyper Emerald: Lost Artifacts v5.7** (32 MB, game code `BPEE`).
Everything here was done without source: reverse engineering with Capstone, hand-written THUMB assembled with Keystone,
and automated testing in mGBA through Lua scripts. No ROMs or saves are included; you apply the patch to your own copy
of `Hyper EMR LA v5.7 bugfix 2.gba`.

## Features

| Feature | What it does | Folder |
|---|---|---|
| English translation | ~6,500 leftover Chinese strings (post-game, Volo/Arceus sidequest, Sinnoh story, Pokédex, moves, items, Battle Frontier) translated and relocated into free space with a safe-space allocator. Game code left byte-identical, so saves stay compatible. A second pass (`translation/patch_remaining.py`) adds ~1,940 more strings: every remaining Pokédex description (Gen 4+), Battle Frontier/Tower apprentice dialogue, Sinnoh trainer speeches, item/ability/move descriptions. | `translation/` |
| Bag sort | **START** in the bag sorts the current pocket. Repeated presses cycle **type → name → amount** (detected from the current order, no extra RAM). Message shown in the description box. Move item (SELECT) untouched. | `patches/bagsort/` |
| Multi-register key items | Register up to **4** key items. In the field, **SELECT** opens a popup listing them on ↑ → ↓ ←; press the direction to use. One registered item is used directly, as in vanilla. Slots stored in unused save bytes. | `patches/keyreg/` |
| Quick ball throw | In wild battles, **tap R** at the action menu to throw the first ball in your Poké Balls pocket without opening the bag. **Hold R** shows the ball and count; **LEFT/RIGHT** while holding changes the default. A ball icon with an "R" badge sits at the left of the screen while the menu is up. | `patches/quickball/` |
| Auto-run toggle | **R** in the overworld toggles auto-run (persistent in the save). B then walks instead. Respects Running Shoes and map rules. | `patches/autorun/` |
| L quick repel | **L** in the overworld asks "Use the Max Repel?" (falls back to Super Repel, then Repel) and uses it via the hack's own repel routine. Silent when a repel is active or you have none. | `patches/lrepel/` |
| In-party move relearner | **Moves** option in the party menu's action list (below Item). Opens the game's own Move Relearner for that Pokémon, using the hack's expanded move lists, no Heart Scale needed. Returns to the overworld when done. | `patches/relearner/` |
| Bag stack cap 999 | Every pocket holds up to 999 per item (was 99, berries already 999). Bag list shows 3 digits. Shops still sell 99 per purchase. | `patches/bagcap/` |
| OHKO cheat | Optional emulator cheat (no ROM change): pins your active Pokémon's Atk/Sp.Atk/Speed to 9999 in battle. Files for mGBA (`.cheats`) and RetroArch (`.cht`). | `cheats/` |

Also included: the reusable **line checker** `translation/check_line.py` to verify a Chinese line seen in game is
translated, and `patches/candyshop/` (an attempted 1-yen Rare Candy shop; reverted because this hack's custom shop code
soft-resets on purchases from a new item list — see `docs/NOTES.md`).

## Apply the patch

1. Obtain the original ROM `Hyper EMR LA v5.7 bugfix 2.gba` (33,554,432 bytes, sha1 in `release/`).
2. Run:
   ```
   python tools/romdiff.py apply "Hyper EMR LA v5.7 bugfix 2.gba" release/hyper-emerald-en-qol.hpatch "Hyper Emerald v5.7 EN+QoL.gba"
   ```
   The tool refuses to run on the wrong original.
3. Your existing `.sav` works unchanged (mGBA/RetroArch match saves by ROM file name, so name the ROM the same as before or rename the save).

## Rebuild from the individual patch scripts

Each feature is a standalone Python patcher that asserts the bytes it expects before touching anything, so they must be
applied in this order on top of the translated ROM:

```
pip install keystone-engine capstone
python patches/bagsort/bagsort_patch.py       in.gba out1.gba
python patches/keyreg/keyreg_patch.py         out1.gba out2.gba
python patches/quickball/quickball_patch.py   out2.gba out3.gba
python patches/autorun/autorun_patch.py       out3.gba out4.gba
python patches/bagcap/bagcap_patch.py         out4.gba out5.gba
python patches/lrepel/lrepel_patch.py         out5.gba out6.gba
python translation/patch_remaining.py         out6.gba out7.gba   # second text pass (needs translation/plan_remaining.json)
python patches/relearner/relearner_patch.py   out7.gba out8.gba
```

## How it was built (for other ROM hackers)

- The hack keeps vanilla Emerald layout for most engine code but wraps many functions with trampolines into its own
  code in the expansion area (0x09Dxxxxx). New features chain in front of those trampolines instead of patching the
  original bodies. `docs/NOTES.md` records every address, hook and gotcha.
- New code lives in verified-unreferenced free space around `0xFD8C00` (checked with a full pointer scan, not just
  runs of 0xFF — the hack holds live pointers into some "empty" regions).
- Persistent state uses only bytes proven unused: SaveBlock1 `unused_9C2[6]` for register slots and the padding byte
  at `0x31` for auto-run.
- Every build is disassembled after assembly and rejected if the assembler emitted a 32-bit Thumb-2 instruction
  (the GBA CPU can't execute them; Keystone emits them silently for out-of-range immediates).
- Testing: mGBA's Lua scripting drives the game (button sequences, memory reads, breakpoints, screenshots). Each
  feature folder has its `test_*.lua`.

## Layout

```
release/      hyper-emerald-en-qol.hpatch + CHECKSUMS.txt   (apply with tools/romdiff.py)
tools/        romdiff.py                                     (create/apply compact ROM diffs)
patches/      one folder per feature: *_patch.py, *.s source, test_*.lua
cheats/       OHKO cheat for mGBA (.cheats) and RetroArch (.cht)
translation/  extraction/insertion pipeline, translations JSON, check_line.py, RESUME.md
docs/         NOTES.md — the complete engineering log (addresses, hooks, pitfalls)
```

The `test_*.lua` scripts contain absolute paths from the development machine (`_testrun/` folder next to the ROM);
edit the `dir` line at the top before running them with `mGBA.exe --script test.lua rom.gba`.

## Requirements

Python 3.11, `keystone-engine`, `capstone`, optionally Pillow for screenshot checks. mGBA (with scripting) for the tests.

## Credits / legal

Original hack by its Chinese authors (DesvoL and team, per the in-game credits). Pokémon is © Nintendo / Game Freak.
This repository contains only patches, scripts and documentation — no game data.
