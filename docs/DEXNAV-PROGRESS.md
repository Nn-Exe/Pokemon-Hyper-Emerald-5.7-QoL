# DexNav search & chain — state of play

Status: **working, applied to the working ROM, verified in mGBA, not yet released.**
Code: [`patches/dexnavchain/`](../patches/dexnavchain/). Engineering detail and the addresses behind every
claim here: the *DEXNAV SEARCH AND CHAIN* section of [NOTES.md](NOTES.md).

## What it does

The DexNav screen (added earlier, `patches/dexnav/`) listed the current map's wild Pokémon and nothing more.
It now has a cursor, and **A** starts tracking the species under it.

Back on the field a bar across the **bottom** shows what you are hunting: the species icon, a **0–3 star**
rating, its name, the **level** and **ability** it will have, **No.** (how many of that species you have
caught or defeated in a row) and **SL**, its Search Level.

The rules follow [Pokémon Unbound's DexNav](https://pokemonunbound.miraheze.org/wiki/DexNav), with the
Search Level raised by DexNav encounters only (the user's choice):

| | Rule |
| --- | --- |
| Search Level | per species, +1 each time you meet the tracked species (any outcome), cap 999 as in ORAS, kept in flash, never reset |
| Odds row | SL 0–4 / 5–9 / 10–24 / 25–49 / 50–99 / 100+ |
| Egg move | 0 / 21 / 46 / 58 / 63 / 83 %, replaces the first move |
| Held item | 0 / 0 / 1 / 7 / 6 / 12 %, the species' common item (rare one 1 time in 5) |
| Perfect IVs (stars) | Unbound's table (0-3: 100/0/0/0, 86/13/1/0, 74/16/9/1, 61/16/16/7, 63/14/17/6, 57/7/24/12 %) rolled out of 200 instead of 100, so every star chance is halved; then capped by the chain: at most 1 star under No.10, 2 under No.20 (user's call: a 3-star at SL 10, No.0 felt too strong). Stars = guaranteed 31s. On top, a flat 1-in-500 roll (any SL, any chain, past the cap) sets stars to 4: all six IVs 31, drawn as three gold stars (palette 15 entry 12) |
| Shiny | `1 + (6·min(SL,100) + 2·clamp(SL-100,0,100) + max(SL-200,0)) / 32` CreateWildMon rolls (27 at SL 255: with this hack's vanilla 1/8192 per try, ≈ 0.33%, 0.61% at SL 999), +5 on the chain's 50th encounter, +10 on the 100th; the Shiny Charm still works inside each roll, as 5 tries per roll, so it multiplies everything by 5 |
| Level | `+ (chain mod 100) / 5` |
| Hidden ability | none: this hack's base stats carry only two ability slots |

The chain grows on a catch or a win. As in ORAS it ends, and tracking stops, when you run, lose, the Pokémon
flees, you **leave the map**, you get into **any other battle** (a trainer, a scripted Pokémon), or you pick a
different species. Closing the game loses it (RAM only), as in ORAS. The Search Level is untouched by all of
these. A different battle is detected through `gBattleResults.lastOpponentSpecies` (`0x03005D30`): we zero it
after every battle we score and when a hunt starts, so a non-zero value on the field with no battle of ours
pending means someone else's battle came and went. Not copied from ORAS: the hidden Pokémon in the grass you
sneak up on (it would be a whole overworld-sprite feature), and ORAS's own odds tables (Unbound's are used).

## The shaking patch

Land and Water hunts no longer turn every encounter into the hunted species. A patch appears 2–5 tiles from the
player, 3 rows up to 1 down (the bar covers the rows below), on a tile of the right kind
(`MetatileBehavior_IsLandWildEncounter` / `IsWaterWildEncounter`), and plays a field effect every 40 frames:

| Tile | Effect | Why this one |
| --- | --- | --- |
| tall grass | 4, the walking rustle | the leftover shaking grass (19) is tinted wrong here and never ends |
| long grass | 17, its long-grass rustle | same, 20 |
| water | 5, the puddle ripple | water surfacing (22) draws a pale blue box here and never ends |
| sand, cave floor, anything else | 10, jump-landing dust | the sand hole (21) has the same problem as 22 |

Every candidate tile also goes through `tile_ok`: inside the map proper (`gBackupMapLayout` 0x03005DC0 counts 7
border tiles each side, 8 on the right; beyond is the border or a connection), collision 0
(`MapGridGetCollisionAt` 0x080881B0), the player's elevation or a 0/15 tile (`MapGridGetElevationAt` 0x08088144 -
this also keeps water patches for when you are surfing), no object on it (`GetObjectEventIdByXY` 0x0808D574
returns 16 for none - boulders and Rock Smash rocks are objects), and not a forced-movement tile such as ice
(`MetatileBehavior_IsForcedMovementTile` 0x0808904C). Cave floors pass the encounter test nearly everywhere, which
is how patches ended up on rocks and off the map before. `test_tiles.lua` checks thousands of spawns against the
map data; on a map with no encounter tiles, repoint the IsLandWildEncounter literal in a scratch copy to a
`movs r0,#1; bx lr` gadget (0x080879F8) so every tile is a candidate.

The rustles are the effects the game plays under a walker and they watch that walker, so `fx_args` names the
player, who is never on the patch: each plays once and removes itself. The ripple takes screen pixels, so its
coordinates go through `SetSpritePosToOffsetMapCoords` (`0x080930E0`) first. It runs on a timer rather than
`FieldEffectActiveListContains`, because standing in tall grass keeps the player's own rustle (the same id) in
that list the whole time.

Stepping onto the patch is caught by `step_hook`, in front of the per-step encounter check (the hack's own,
through the trampoline word `0x0809CBEC`): it makes the hunted Pokémon through the CreateWildMon trampoline with
bit2 up (so `wild_hook` dresses it) and calls `BattleSetup_StartWildBattle` (`0x080B0698`), past Repel as the
DexNav does officially. Anywhere else the check runs as ever with bit6 up. `wild_hook` then substitutes only:
the patch's encounter (bit2); for a fishing hunt, calls returning into `GenerateFishingWildMon` (lr
`0x080B504F`) - no longer reached: arm_search now turns a fishing species into a water hunt (a ripple you surf
onto), at the user's request; for a Rock Smash hunt, calls returning into `TryGenerateWildMon` (lr `0x080B501B`) with bit6
down, i.e. not a step in the grass. Sweet Scent also takes that path.

A normal wild battle is not ours, so it resets the chain (ORAS) and a new patch appears where you stand. Walking
away from the patch (more than 7 columns or 5 rows) ends the search like leaving the map: the patch never follows
you to new grass; you register again.

**Not played through**: a real water or cave hunt (the ripple and dust were checked on land tiles, and the tile
choice uses the game's own tests), a Rock Smash or fishing hunt, and Repel. Worth a look when you are next near
water or in a cave.

`hud_arrow` prints one arrow toward the patch in the bar's top right corner (x 212, line 1), from the font (0x79 up,
0x7A down, 0x7B left, 0x7C right): left or right while the player is not in the patch's column, then up or down.
No distance (the user's call). Gotcha: `movs rX, #imm` sets N and Z, so a sign test after loading the
arrow character must `cmp` again - the first build always pointed right. It is redrawn every 4 frames from the overworld tick (a black fill, then the
text, then a tiles-only copy), and left blank when there is no patch.

## The DexNav screen

The header shows "A: Register" where the page draw put "DexNav" (`draw_hint`, over a fill in the header colour).
The selected row gets a 2-pixel red frame (`border`: four `FillWindowPixelRect` calls, `0x08003B64`) in entry 9 of
the list palette, which the screen leaves unused; the red is loaded with `LoadPalette` each draw, so the DexNav
blob itself stays byte-identical. Moving the cursor erases the old frame and draws the new one; the page, with
its icon sprites, is only drawn when the page changes (it used to be redrawn on every press). After A, the
original task still fades out and sets `CB2_ReturnToFieldWithOpenMenu`; on the frame it destroys itself,
`dn_task` swaps that for `cb2_return`, which is the same thing with `FieldCB_ReturnToFieldNoScript`
(`0x080AF6D4`) in `gFieldCallback` (`0x03005DAC`) instead of the start menu.

`draw_levels` writes each row's Search Level ("SL n", small font, red - entry 9, the frame's - blank at 0) after every page draw,
right-aligned to end at x 133, just before "Lv."; the flash sector is read once per page. `draw_hint` repaints
the header band (all but the page number), reprints the place name from gStringVar1 (0x02021CC4, left there by
the page draw) and right-aligns the hint to end at x 190 (`GetStringRightAlignXOffset` 0x081DB368). A new spot
plays the species' cry (`PlayCry_Normal` 0x080A3274, centred), which also ducks the music as the game does.

## How it is built

Three pointer words change in the whole ROM. Nothing the game does is rewritten.

| Site | Was | Now |
| --- | --- | --- |
| `0x080B4E6C` | the hack's own `CreateWildMon` (`0x09F05F19`) | our stub, which substitutes species/level and calls that same routine |
| `0x08085E60` | the overworld hook the earlier patches installed | our stub, which chains to it |
| `0x08FDA520` | the DexNav screen's task pointer, inside our own dexnav blob | our task, which calls the original and adds the cursor and A |

Everything else is new code and data at `0x08FDE4A0` (about 2 KB). State is 32 bytes of EWRAM at
`0x0203A660` plus 96 bytes of text scratch, so the chain itself does not survive a reload. Search levels do:
see *Search levels in flash* below.

The one thing worth understanding before changing anything: the hack's `CreateWildMon` already contains the
machinery a chain needs. It checks the bag for a Shiny Charm and passes a **reroll count** to a personality
generator that keeps rolling until one comes out shiny. Our stub does not reimplement any of that — it asks
the same routine for our species and level, calls it again while the chain has rerolls left, and then writes
the IVs, ability slot and egg move straight into the mon (data in this hack is unencrypted and unshuffled).

## Search levels in flash

Flash sector 30 is vanilla's Trainer Hill e-Reader sector. Only an e-Reader card writes it (`0x081D3AB0`,
called only from the e-Reader code), so on a long real save it was still blank (all `0xFF`). The hack
disabled the main save's checksums and fills its sectors to `0xFEE`, so there is no safe slack there.

We use the game's own `TryReadSpecialSaveSector` (`0x081535DC`) and `TryWriteSpecialSaveSector`
(`0x08153634`), which accept only sectors 30 and 31, stage through `gSaveDataBuffer` (`0x0203ABBC`) and write
the `0xB39D` sentinel. Passing `gSaveDataBuffer + 4` as the buffer makes their copy an in-place no-op, so no
extra RAM is needed. Layout from that `+4`: byte 0 is kept 0, `+4` the tag `DXSL`, `+8` 1000 entries of
`{u16 species, u16 level}` (it was `u8 level, u8 0` before the 999 cap; old entries read the same).

Byte 0 is the Trainer Hill's trainer count; its validator (`0x081D396C`) rejects anything outside 1–8, so the
hill can never mistake our data for its own. If the sector has the sentinel but not our tag (a real e-Reader
hill), it is left alone and search levels stay 0. The main save sectors are never written. Search levels are
written the moment they change, so they persist even if you do not save the game.

## What has been verified, and how

Each of these is a Lua test in the patch folder; all of them were run against the applied ROM.

- **Chain arithmetic** (`test_chain.lua`) — nine consecutive encounters, each the tracked species at exactly
  the pre-rolled level, chain rising by one per win.
- **Only the hunt counts** (`test_chain.lua`) — a Pokémon that is not the tracked species (a Pokénav rematch
  trainer, in practice) neither raises nor breaks the chain.
- **Breaking** (`test_chain_break.lua`) — a "ran away" outcome drops the chain to 0 and stops the tracking
  within four frames; wild encounters go back to normal afterwards.
- **Stars → IVs** (`test_stars.lua`) — forcing three stars gave four perfect IVs on every encounter, two
  stars gave three, in different stat positions each time.
- **Pokénav calls** (`test_pokenav_call.lua`) — a call with the bar up renders cleanly and completes; the bar
  takes itself down while the call owns the screen and comes back after.
- **DexNav screen** (`test_screen2.lua`) — hint and red frame drawn; three cursor moves redraw only the frame
  (icon animations carry on); A lands on the field with controls free and the bar up; walking away ends the search.
- **Shaking patch** (`test_patch.lua`, written before walking away ended the search: its "away" stage now sees
  tracking stop rather than a new patch) — the patch spawns and shakes; stepping onto it forces the hunted battle;
  the win gives chain 1 / SL 1 and a new patch; moving it off screen resets the chain; normal encounters in other
  grass are not substituted and reset the chain. Effects were checked frame by frame, and never pile up.
- **ORAS breaks** (`test_official.lua`) — idle and menus never break; SL 300→301 lands in flash; a battle we
  did not seed breaks the chain and keeps SL; re-arming reads SL 301 back from flash; leaving the map breaks.
- **Parking** (`test_park.lua`, obsolete: leaving the map now breaks the chain) — off the hunting map the bar disappears and the chain survives; back on it,
  the bar returns with the chain intact.
- **Screen and stress** (`test_screen.lua`) — cursor, paging, clamping at the last row, and a run of
  encounters at chain 200 (rerolls at full stretch) with no hang.
- **Unbound rules** (`test_unbound.lua`, `test_unbound_hi.lua`, run on a real late-game save) — arming through
  START → DexNav; a catch raises the chain (it did not before); a run breaks it; SL rises 0→4 across catch,
  win, win, run and lands in flash sector 30 (sentinel, byte 0 = 0, tag, one entry); a new session loads SL 4
  back; with SL 150 the egg move replaced move 1 with the right PP, two stars gave exactly two 31s, the rolled
  held item appeared, chain 49 gave +9 levels, and the 50th encounter (27 rolls) ran without a stall.
  `test_stars.lua` predates this: it expects stars+1 perfect IVs.
- **Scratch RAM** (`test_scratch_ram.lua`) — how the EWRAM region was chosen. Worth rerunning if you move it.

## Four bugs found here, so they are not rediscovered

1. **A battle could be counted twice.** The overworld callback keeps running during a battle's transition, so
   it read the *previous* battle's result — still standing in `gBattleOutcome` — and scored it against the new
   encounter. The stub now zeroes that byte when it seeds an encounter, and the tick ignores an outcome of 0.
2. **Unrelated battles counted.** Scoring now also checks that the Pokémon left in the enemy party is the
   species being hunted.
3. **Catches never counted.** The game empties `gEnemyParty` on a catch before the field comes back, so
   the species check failed and the battle was ignored. Scoring now reads
   `gBattleResults.lastOpponentSpecies` (`0x03005D30`), which is cleared per battle and survives the catch.
4. **The bar ate the map.** On the field BG0's tiles start at VRAM `0x06008000` while the map's own tilemaps
   sit at `0x0600E000` — tile index `0x300`. A window whose baseBlock reaches that far writes over the map
   and the screen turns to garbage. The bar sits at `0x240..0x2B0`, clear of the game's message window
   (`0x194`), location popup (`0x107`) and frame tiles (`0x214`). **If you resize the bar, check this first.**

## Loose ends

Nothing here is a known defect; these are decisions someone may want to revisit.

- **Encounter type is not distinguished.** The DexNav lists Land, Water, Rock and Fishing species; tracking a
  fishing-only species and then walking in grass will still produce it. Gating would mean checking which of
  the four `CreateWildMon` call sites (`0x080B5016`, `0x080B504A`, `0x080B509C`, `0x080B5758`) the call came
  from, via `lr`, and comparing it with the section the entry came from.
- **No explicit "stop hunting".** Pick another species, or run from one encounter. A toggle on A would
  conflict with re-picking the same species to keep the chain.
- **Hidden abilities do not exist in this hack** — base stats are the vanilla 28-byte struct with two ability
  slots — so the chain grants the second ability at best. The egg move is granted silently; the bar does not
  show it (deliberately, to match the requested layout: no direction arrow, no MOVE line).
- **Safari Zone** catches were not tested; the Safari battle outcome may not be the value the scoring expects.
- **The chain is RAM only.** Search levels are in flash; the chain could join them in the same sector.
- **Wild double battles**: none in the normal encounter path (CreateWildMon only fills enemy slot 0). Trainer
  battles never touch the chain.
- **The bar's black and the stars' red and gold** come from writing into the three spare slots of the field
  text palette (entries 10, 11 and 12 - three identical whites) on every draw, because a new map reloads the
  palettes. If a screen ever shows black, red or gold where it should be white, these slots are the place to look. If a screen ever
  shows black text where it should be white, that slot is the place to look.
