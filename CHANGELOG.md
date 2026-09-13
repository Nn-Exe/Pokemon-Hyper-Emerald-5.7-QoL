# Changelog

All changes are binary patches on top of `Hyper EMR LA v5.7 bugfix 2.gba`. Dates are when the work was verified in mGBA.

## 2026-09-13
- **Coloured stat names** in battle messages (Attack red, Defense orange, Speed light green, Sp. Atk pink, Sp. Def blue, Accuracy/Evasiveness yellow). `patches/statcolor/`
- **In-party move relearner**: new *Moves* option in the party menu opens the game's Move Relearner for that Pokémon, no Heart Scale. `patches/relearner/`
- **Second translation pass**: 1,944 more strings, including every remaining Pokédex description (Gen 4+ species), Battle Frontier / Battle Tower apprentice dialogue, Sinnoh trainer speeches, item, ability and move descriptions. `translation/patch_remaining.py`
- **L quick repel**: L in the overworld offers to use Max Repel → Super Repel → Repel. `patches/lrepel/`
- Repel "use another?" prompt confirmed native to the hack (no patch needed).
- Investigated and declined: Items pocket 250 / PC 126 (the hack's flag tables live in the old bag area of the save), Rare Candy shop (hack's shop code soft-resets), OHKO item (delivered as an emulator cheat instead).

## 2026-09-12
- **Bag stack cap 999** for every pocket. `patches/bagcap/`
- **Auto-run toggle** with R in the overworld (persistent). `patches/autorun/`
- **Quick ball throw**: tap R in a wild battle; hold R to pick the ball; on-screen widget. `patches/quickball/`
- **Register up to 4 key items**; SELECT opens a directional popup. `patches/keyreg/`
- **Bag sort** with START (type → name → amount). `patches/bagsort/`
- OHKO / max-stat cheat files for mGBA and RetroArch. `cheats/`
- Repository created; release patch and `romdiff.py` tool.

## 2026-07 (translation project)
- First translation pass: ~4,000 leftover Chinese strings (post-game, Volo/Arceus sidequest, Sinnoh story, trainer battle text, cutscenes) relocated into verified free space; freeze in the Volo/Arceus cutscene fixed; save compatibility with the original kept (game code byte-identical).
