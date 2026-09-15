# Changelog

One line per change, newest first. The how and why of each change is in [docs/NOTES.md](docs/NOTES.md); each
patch folder has its own notes. Tags: **Added** new feature · **Fixed** bug fix · **Changed** · **Tool** for modders.

## 2026-09-16
- **Added** PC anywhere: hold B and press SELECT in the overworld to open the PC (box storage, your PC, Hall of Fame). `patches/pcanywhere/`

## 2026-09-15
- **Added** Trainer hiding: the release hides 3 Team Flare grunts on Allearth Forest that no script refers to. `patches/trainerhide/`
- **Tool** `trainers.py` lists a map's trainers as SAFE / CHECK / RISKY; `strict_select.py` finds script-free grunts.
- **Added** Mint nature changer without the quiz: the teacher in the Rustboro Trainer's School now offers Mints straight away. `patches/mintskip/`
- **Fixed** Garbled graphics in Rustboro and 57 other maps (text passes had overwritten compressed tiles). `patches/gfxfix/`
- **Tool** `audit_gfx.py` checks every compressed graphic against the original ROM.
- **Checked** Desert Ruins Garchomp guardian crash: not reproducible on this build, the original, or older builds.

## 2026-09-14
- **Fixed** New-game crash in the Mountain Top cutscene, plus 8 other scenes (text passes had overwritten movement scripts). `patches/movefix/`
- **Added** Player's guide website (GitHub Pages) and credits for the earlier translation team.

## 2026-09-13
- **Added** Coloured stat names in battle messages. `patches/statcolor/`
- **Added** In-party move relearner (party menu → Moves). `patches/relearner/`
- **Added** Second translation pass: 1,944 strings incl. all 960 Pokédex entries and Battle Frontier dialogue.
- **Added** L quick repel (Max → Super → Repel). `patches/lrepel/`
- **Changed** Repository published on GitHub (MIT license, showcase images, release v1.0).
- **Declined** Bigger Items pocket / PC storage (save format conflict), 1-yen Rare Candy shop (hack soft-resets).

## 2026-09-12
- **Added** Bag stack cap 999. `patches/bagcap/`
- **Added** Auto-run toggle with R. `patches/autorun/`
- **Added** Quick ball throw with R in wild battles, with on-screen widget. `patches/quickball/`
- **Added** Register up to 4 key items, SELECT popup. `patches/keyreg/`
- **Added** Bag sort with START. `patches/bagsort/`
- **Added** OHKO / max-stat cheat files for mGBA and RetroArch. `cheats/`

## 2026-07
- **Added** First translation pass: ~4,000 Chinese strings (post-game, Lost Artifacts story, Sinnoh, battle text).
- **Fixed** Freeze in the Volo/Arceus cutscene.

## Shelved (not in the release)
- In-party nature changer: root cause found (6-byte grid command), not re-tested. `patches/naturemenu/`
- PC item storage sort: not verified in-game. `patches/pcsort/`
