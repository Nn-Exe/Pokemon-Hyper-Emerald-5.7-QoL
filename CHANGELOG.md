# Changelog

All changes are binary patches on top of `Hyper EMR LA v5.7 bugfix 2.gba`. Dates are when the work was verified in mGBA.

## 2026-09-15
- **Trainer hiding tool** (`patches/trainerhide/`): `trainers.py` lists a map's trainers with SAFE / CHECK / RISKY
  verdicts, `strict_select.py` finds grunts no script refers to, and `trainerhide_patch.py` hides the ones in
  `hidden.json` by moving the object off the map (object numbering and saves unchanged, reversible). The release
  hides 3 Team Flare grunts on Allearth Forest 34/41, 70% of the 4 grunts on Giant Chasm, Rainbow Castle and
  Allearth Forest that passed the strict check. Verified in mGBA.
- **Nature changer without the quiz**: the Unova Gym Leader in the Rustboro Trainer's School gives out Galar Mints
  that set a Pokémon's nature, but only after a run of random true/false questions. `patches/mintskip/` replaces
  the quiz gate in his script (11 bytes: a `compare VAR_4001, 15` + `goto_if` becomes an unconditional `goto`) so
  talking to him always opens "Do you need a Mint?" -> pick a nature -> pick a Pokémon. Repeatable, and the quiz
  branch is simply never reached. Verified in mGBA: Swampert went Hardy -> Adamant, Attack 274 -> 301 and
  Sp. Atk 199 -> 179.
- **Fix: corrupted town graphics** (reported in Rustboro City, where most of the town's tiles were garbled). The text
  passes repointed every 4-byte occurrence of a Chinese string's pointer, and 23 of those occurrences were chance
  byte sequences inside LZ77-compressed graphics. LZ77 is a stream, so one altered byte garbles everything decoded
  after it: the secondary tileset shared by Rustboro and 22 other maps lost 80% of its tiles, a second tileset used by
  35 maps lost 18%, and 19 more blobs (sprites, portraits, menu graphics) were damaged. `patches/gfxfix/` restores all
  92 bytes from the original ROM. Verified: every one of the 8,283 compressed blobs in the build now matches the
  original byte-for-byte (`patches/gfxfix/audit_gfx.py`).
- Translation pipeline: `translation/patch_remaining.py` now refuses to rewrite a pointer occurrence that lies inside
  an LZ77 blob.

## 2026-09-14
- **Fix: crash in the new-game intro** (Mountain Top cutscene, mGBA "Jumped to invalid address 101C0CB4") and in eight
  other scenes (Slateport Contest Hall reception, Hearthome contest, Mossdeep meteor scene, Steven's Island, Oreburgh,
  Hisui). The text passes had mistaken `applymovement 0x000F, ptr` (bytes `4F 0F 00 <ptr>`) for a `loadword` text load
  and replaced nine movement-script pointers / three movement scripts with English text. `patches/movefix/` restores
  them byte-for-byte from the original ROM and relocates two dialogue lines that had been truncated by the same mistake.
  Audited against the original: all 4,234 `applymovement` references now match. Verified in mGBA (new game to Littleroot).
- Translation pipeline (`translation/build_corpus.py`, `patch_conv.py`, `patch_story.py`) no longer treats `4F/50 0F 00`
  as a text pointer.

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
