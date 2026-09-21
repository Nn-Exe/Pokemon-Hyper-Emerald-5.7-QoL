# DexNav search & chain — state of play

Status: **working, applied to the working ROM, verified in mGBA, not yet released.**
Code: [`patches/dexnavchain/`](../patches/dexnavchain/). Engineering detail and the addresses behind every
claim here: the *DEXNAV SEARCH AND CHAIN* section of [NOTES.md](NOTES.md).

## What it does

The DexNav screen (added earlier, `patches/dexnav/`) listed the current map's wild Pokémon and nothing more.
It now has a cursor, and **A** starts tracking the species under it.

Back on the field a bar appears across the top showing what you are hunting: the species icon, a **0–3 star**
rating, its name, the **level** and **ability** it will have, and **No.** — how many of that species you have
caught or defeated in a row.

The next wild Pokémon on that map is that species, at exactly the level and ability the bar promised. Each
link in the chain improves the next encounter:

| Chain effect | Rule |
| --- | --- |
| Shiny | `1 + chain/4` extra rerolls, capped at 12, stacking with the Shiny Charm's own 5 |
| Perfect IVs | 3 stars = at least four 31s, 2 stars = three, 1 star = two. Chance of three stars is `1 + chain/2` per cent (cap 15), of two stars three times that, of one star six times that |
| Level | `+chain/8`, capped at +5, never past 100 |
| Egg move | `chain*3` per cent, capped at 60; taken from the species' own egg-move list |

The chain ends when you run, lose, or pick a different species. Leaving the map only **parks** the hunt —
step into a Pokémon Centre and back and the chain is still there. Encounters are only substituted on the map
the hunt was started on.

## How it is built

Three pointer words change in the whole ROM. Nothing the game does is rewritten.

| Site | Was | Now |
| --- | --- | --- |
| `0x080B4E6C` | the hack's own `CreateWildMon` (`0x09F05F19`) | our stub, which substitutes species/level and calls that same routine |
| `0x08085E60` | the overworld hook the earlier patches installed | our stub, which chains to it |
| `0x08FDA520` | the DexNav screen's task pointer, inside our own dexnav blob | our task, which calls the original and adds the cursor and A |

Everything else is new code and data at `0x08FDE4A0` (about 2 KB). State is 32 bytes of EWRAM at
`0x0203A660` plus 96 bytes of text scratch — **RAM only**, so a chain does not survive a reload, and nothing
is written to the save.

The one thing worth understanding before changing anything: the hack's `CreateWildMon` already contains the
machinery a chain needs. It checks the bag for a Shiny Charm and passes a **reroll count** to a personality
generator that keeps rolling until one comes out shiny. Our stub does not reimplement any of that — it asks
the same routine for our species and level, calls it again while the chain has rerolls left, and then writes
the IVs, ability slot and egg move straight into the mon (data in this hack is unencrypted and unshuffled).

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
- **Parking** (`test_park.lua`) — off the hunting map the bar disappears and the chain survives; back on it,
  the bar returns with the chain intact.
- **Screen and stress** (`test_screen.lua`) — cursor, paging, clamping at the last row, and a run of
  encounters at chain 200 (rerolls at full stretch) with no hang.
- **Scratch RAM** (`test_scratch_ram.lua`) — how the EWRAM region was chosen. Worth rerunning if you move it.

## Three bugs found here, so they are not rediscovered

1. **A battle could be counted twice.** The overworld callback keeps running during a battle's transition, so
   it read the *previous* battle's result — still standing in `gBattleOutcome` — and scored it against the new
   encounter. The stub now zeroes that byte when it seeds an encounter, and the tick ignores an outcome of 0.
2. **Unrelated battles counted.** Scoring now also checks that the Pokémon left in the enemy party is the
   species being hunted.
3. **The bar ate the map.** On the field BG0's tiles start at VRAM `0x06008000` while the map's own tilemaps
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
- **The chain is RAM only.** Surviving a reload would mean save-block space, which the project has so far
  avoided on purpose.
- **The bar's black** comes from writing one colour into a spare slot of the field text palette (entries
  10–12 are three identical whites) on every draw, because a new map reloads the palettes. If a screen ever
  shows black text where it should be white, that slot is the place to look.
