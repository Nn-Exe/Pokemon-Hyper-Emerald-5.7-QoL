# Changelog

One line per change, newest first. The how and why of each change is in [docs/NOTES.md](docs/NOTES.md); each
patch folder has its own notes. Tags: **Added** new feature · **Fixed** bug fix · **Changed** · **Tool** for modders.

## 2026-09-21
- **Added** DexNav: each species' Search Level shows in the list in red ("SL n", blank at 0), and a new shaking spot announces itself with the hunted Pokémon's cry. The header hint is right-aligned so long place names no longer run into it. `patches/dexnavchain/`
- **Added** DexNav jackpot: one hunted encounter in 500 (0.2%), at any Search Level or chain, has all six IVs perfect — shown as three gold stars on the bar. `patches/dexnavchain/`
- **Added** DexNav bar shows an arrow toward the shaking patch — left/right until you are lined up with it, then up/down — so you can find it when it is hard to see or behind the bar. `patches/dexnavchain/`
- **Changed** DexNav: a fishing species is now hunted like a water one — a ripple on the water you surf onto — instead of turning your next bite into it. Fishing is normal again. `patches/dexnavchain/`
- **Fixed** README shiny figures: this hack uses 1/8192 per try, so SL 255 is ≈0.33% (not 0.66%); the Shiny Charm multiplies the DexNav's rolls by 5.
- **Changed** DexNav bar: earned stars are red (they were white and hard to see); unearned stay grey. `patches/dexnavchain/`
- **Fixed** DexNav shaking patch could land where you can't step — off the map's edge, on rocks, walls or boulders, on a ledge above you, or on ice (mostly in caves). It now needs a walkable tile inside the map, at your height, with nothing on it and no sliding. Water patches appear while surfing. `patches/dexnavchain/`
- **Changed** DexNav stars (perfect IVs) are rarer: half of Unbound's odds, and the chain caps them — at most 1 star under No.10, 2 under No.20. The row frame starts at the name, clear of the icons. `patches/dexnavchain/`
- **Changed** **R** in the field now opens the DexNav (B or a registration comes straight back to the field). Auto Run moved to the Option menu, replacing Button Mode (its LR / L=A modes are gone); turn it on there once. `patches/rbutton/`
- **Added** Unregister: **A** on the registered species in the DexNav (the header says "A: Unregister") ends the hunt. `patches/dexnavchain/`
- **Changed** DexNav screen: the header says "A: Register", the selected row gets a red border (the blue arrow was hard to see), moving the cursor no longer redraws the whole list, and registering goes straight back to the field with the bar up. Walking away from the shaking patch now ends the search (register again) instead of the patch following you. `patches/dexnavchain/`
- **Added** DexNav shaking patch: while hunting a Land or Water species, a patch near you rustles (grass), ripples (water) or kicks up dust (caves, sand). Step on it for the hunted Pokémon — even with a Repel on; other tiles give the map's normal Pokémon, which resets the chain, as does leaving the patch off screen. Rock Smash and fishing hunts keep substituting their own encounters. `patches/dexnavchain/`
- **Changed** DexNav chain breaks the way it does in Omega Ruby / Alpha Sapphire: leaving the area or getting into any other battle (a trainer, a scripted Pokémon) now ends it too. Search Level now goes to 999 (was 255) and never resets. `patches/dexnavchain/`
- **Fixed** DexNav chain: catching the tracked Pokémon now counts (the game empties the enemy slot on a catch, so it was scored as "not the hunt"). `patches/dexnavchain/`
- **Changed** DexNav chain now follows Pokémon Unbound's DexNav: a per-species **Search Level** (shown as "SL" on the bar, kept in flash sector 30, never in the main save) sets the odds of an egg move, a held item and 0–3 perfect IVs, and adds shiny rolls; +1 level per 5 links (reset every 100); extra shiny rolls on the 50th and 100th encounter; the egg move replaces the first move. The bar moved to the bottom of the screen, framed with the menus' bold white border. `patches/dexnavchain/`
- **Added** DexNav search and chain: pick a species on the DexNav screen and **A** tracks it, a bar on the field shows the icon, star rating, level, ability and how many you have taken in a row, and each link improves the next one's shiny odds, IVs and egg-move chance. `patches/dexnavchain/`
- **Added** Fly from the Sinnoh map: **A** on a town you have already reached takes you there, by running that town's own courier script. `patches/sinnohmap/`

## 2026-09-20
- **Added** Sinnoh map on the **Sinnoh Map** key item (the hack's unused Town Map, renamed in place): its own screen, marker on your current area, name box, D-pad hops between places, A flies to any town whose courier you've used (it runs the courier's own script, same visited-flag rule; unvisited towns are greyed); the Hoenn map and Fly untouched. `patches/sinnohmap/`
- **Fixed** News Tracker key item froze the game (a stray byte swallowed the message's terminator); its region name is English now too. `patches/newsfix/`
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
