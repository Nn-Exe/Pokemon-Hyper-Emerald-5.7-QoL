# Changelog

One line per change, newest first. The how and why of each change is in [docs/NOTES.md](docs/NOTES.md); each
patch folder has its own notes. Tags: **Added** new feature · **Fixed** bug fix · **Changed** · **Tool** for modders.

## 2026-09-20
- **Changed** Release v1.3.1: type badges and the effectiveness multiplier show for every opponent again. The caught-only rule from v1.3 hid them on trainers' Pokémon you had only seen, and a "seen" rule is no rule at all (the game marks a Pokémon seen the moment it appears).
- **Changed** Release v1.3 published (everything below since v1.2).
- **Changed** Type badges now use SoulGold's 8×12 badge art (smaller, no overlap in double battles). `patches/typeicons/`

## 2026-09-19
- **Added** Leftover Chinese NPC names in English: 90 Battle Tent trainers, 2 Battle Frontier trainers, 6 story trainers, 6 partner-name words, all rewritten in place. `patches/npcnames/`
- **Changed** Type badges and the effectiveness multiplier now only show for Pokémon you've caught.
- **Added** Both bikes held at once — no more swapping at Rydel's. `patches/bothbikes/`
- **Added** Move effectiveness multiplier on the PP line of the battle move list. `patches/typeeff/`
- **Added** Type badges beside the opponent's healthbox in battle. `patches/typeicons/`

## 2026-09-18
- **Added** DexNav screen: START menu → DexNav lists the map's wild Pokémon with icons, level ranges and colour-coded habitat; also on the Safari Zone menu. `patches/dexnav/`
- **Added** Gold healthbox for a shiny opponent, matching the game's own shiny check. `patches/shinybox/`
- **Fixed** Options screen and Hall of Fame banner said version 5.5; they now say 5.7. `patches/version/`

## 2026-09-16
- **Changed** Release v1.2 published (everything below since v1.1).
- **Changed** PC button in the SELECT popup is now A; B or SELECT closes the popup.
- **Changed** PC anywhere moved into the SELECT popup: SELECT, then B opens the PC; SELECT closes the popup, which now always opens.
- **Added** PC anywhere: open the PC from anywhere (box storage, your PC, Hall of Fame). `patches/pcanywhere/`

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
