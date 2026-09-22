# Changelog

One line per change, newest first. The how and why of each change is in [docs/NOTES.md](docs/NOTES.md); each
patch folder has its own notes. Tags: **Added** new feature · **Fixed** bug fix · **Changed** · **Tool** for modders.

## 2026-09-22
- **Changed** Quest Log chapter grid redesigned as cards on a dark backdrop: rounded corners, a colour and a pixel-art icon per chapter, done/total at the top right (green once complete), and a flashing gold-orange border on the selected card. Moving the cursor no longer recounts every chapter, so it is instant. `patches/questlog/`
- **Changed** Quest Log opens on a chapter grid: seven tiles (Hoenn, Post-game, Sinnoh, Lost Artifacts, Legends, Key Items, Side Content) with done/total each, the current chapter selected. D-pad picks, A opens, B in a list goes back to the grid, B on the grid closes; L/R still flip chapters inside a list. `patches/questlog/`
- **Added** Quest Log "Side Content" chapter: 39 rows outside the story - the six Hisuian trades, the gift Pokémon (the Littleroot legendary choice, Meloetta, the Galar gift, Meltan, Kubfu/Rockruff, Poipole...), other regions' starters hidden as one-off battles, and side stories (Red and Blue's Buzzwole, the Shadow Triad, the Old Chateau...). Each ticked by its script's own flag. `patches/questlog/`
- **Added** Legends chapter now includes the Ultra Beasts (counted as mythical): 92 rows. `patches/questlog/`
- **Added** Quest Log "Key Items" chapter: the 55 key items the game hands out, in story order, ticked once you have got them (in the Bag, or the game's own "received" flag for ones that are used up or given away - the Devon Goods, the Letter, the Meteorite, the Dried Fish). Items you have not got yet are still named (dimmed), and A says where each one comes from. `patches/questlog/`
- **Added** Quest Log "Legends" chapter: all 82 legendary and mythical Pokémon in the game in National Dex order, ticked when caught (read from your Pokédex), named once seen, "???" before that. A gives a hint for unseen ones and the exact place and level once seen. The header counts caught/82. Each row shows a silhouette of the Pokémon, made from its own menu icon shrunk to 16x16 (dimmed until seen). `patches/questlog/`
- **Tool** Content audit: `tools/romdata/flag_audit.py` sorts every flag the scripts set (934, all maps) into battles, gifts, items, trainers and events, marks what the Journal follows, and `tools/build_audit_page.py` writes the local page `docs/content-audit.html` (with a hand-written list of the side content outside the Journal).
- **Fixed** Sinnoh Map: flying to the Sinnoh League now lands at the League building's door once you have come through Victory Road (the courier's own second League stop, flag 0x42EB); before that it is still the Pokémon Center by the Victory Road entrance. `patches/leaguefly/`
- **Added** Start menu shortcut to the Quest Log: a small "[R] Journal" box at the top left while the menu is open (where the Safari Zone shows its balls); **R** opens the Quest Log and B returns to the menu. `patches/questlog/`
- **Added** Quest Log: using the Journal now opens a checklist screen - every objective of a chapter (Hoenn, Post-game, Sinnoh, Lost Artifacts) with a tick when done, an arrow on the current one, a diamond on side objectives and "???" for what is ahead. L/R turn the chapter, A reads an objective in full, B closes. Built on the Journal's own table and routines; every objective has a short title in `steps.py`. `patches/questlog/`
- **Changed** Journal's closing message now also points to the six-battle trial at Cogita's retreat off Sootopolis (the Dream Sky Gauntlet sets no flag, so it cannot be an objective). The story's "final foe" thread is left open by the original hack. `patches/journal/`
- **Changed** Journal objectives no longer spoil what you will meet: they say where to go, not who waits there (e.g. "face the phantom of nightmares" instead of Darkrai; the Distortion World's ruler, the Plates' true owner, what waits beyond the sky). Names the player already knows, or needs as a requirement, stay. `patches/journal/`
- **Added** Journal: the Solaceon nightmare (the husband's story, Dawn's Lunar Wing, waking the woman, Darkrai in the Lost Tower), after Volo and before Enamorus, as "any order" steps (84 objectives now). Guide: the nightmare row corrected from the scripts - it leads to Darkrai, not Giratina. `patches/journal/`
- **Fixed** Enamorus's name was still in Chinese (爱娜莫洛斯); it now reads Enamorus everywhere. `patches/speciesnames/`
- **Added** Journal: the story after Volo - Rei and Cogita's report, Cogita and Enamorus, Kitty's Dried Fish and nameless stone, the God of Forms at the Moonbow Dome, and Cogita on Champion Island (80 objectives now). The Champion Island ticket objective now waits for Scott's own flag: Yanshan also sets the ferry flag but gives no ticket (tested). `patches/journal/`
- **Added** Guide: the God of Forms / Kitty questline (Lost Artifacts), and Kitty and Huang Banxian in Steven's Island's developer house - read from the ROM's scripts.
- **Fixed** Guide, Champion Island: reached by the Lilycove ferry with Scott's ticket (first Silver Symbol) - read from the ROM's scripts. The walkthrough said "off Route 105"; the items page said "after Rainbow Rocket". Yanshan in Steven's Island's developer house gives the Key Stone.
- **Fixed** Journal: the Champion Island objective said to surf there. It is now two objectives, as the game has it: earn a Silver Symbol at the Battle Frontier (e.g. Salon Maiden Anabel at the Battle Tower) and get the ferry ticket from Scott, then take the ferry from Lilycove City. `patches/journal/`
- **Fixed** Journal: the last page of its message closed by itself before you could read it; it now waits for a button like every other page. `patches/journal/`
- **Fixed** Berries pocket numbers: the hack's newer berries (Occa ... Maranga) showed as "No?2" because the number is item id - 132 printed in two digits. They now continue after Enigma (No43): Occa No44 ... Maranga No67. The bug is in the original hack too. `patches/berrynum/`

## 2026-09-21
- **Added** Journal key item: shows your next story objective across Hoenn, the post-game, Sinnoh and Lost Artifacts, with progress for the Sinnoh gyms, the Tapu trials and the Plates (the next Plate's hiding place, in Waji's order). Replaces the unused Fame Checker and is handed to you automatically. `patches/journal/`
- **Changed** Gold healthbox now also marks **your own** shiny Pokémon (both boxes in double battles), not only wild and trainers' ones. `patches/shinybox/`
- **Changed** Release v1.4 (everything below since v1.3.1): DexNav hunting, the Sinnoh Map with fly, R opening the DexNav with Auto Run moved into the Option menu, and the News Tracker fix. Rebuilt patch and checksums in `release/`.
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
