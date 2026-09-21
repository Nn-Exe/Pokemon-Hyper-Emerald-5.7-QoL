# Party Pokémon editor + Rare Candy NPC — design

Date: 2026-09-21 · Build: `Hyper Emerald v5.7 EN+QoL.gba` (v1.4, sha1 `e99406d7…`)

Two independent features, delivered as two new patchers appended to the end of the build chain:
`patches/partyedit/` (architectural — a new screen) and `patches/candynpc/` (bounded — one NPC).
Both are binary patches in the house style: Thumb-1 into verified free space, pointer words repointed,
verified by driving mGBA with Lua.

## Feature A — Party Pokémon editor

### Goal

From the party menu, an **Edit** action opens a screen that lets you change the selected Pokémon's
**nature, IVs and EVs** with exact values, then recalculates its stats. No save-format change: it edits
`gPlayerParty` directly, so it works with existing saves in both directions.

### Entry point

The START menu is full (`sCurrentStartMenuActions` is 9 bytes at `0x02037610`, no bounds check), so the
editor hangs off the **party menu**, exactly like the relearner's *Moves*.

Recon (in the v1.4 build):

| Thing | Address |
|---|---|
| Party-menu action table `sCursorOptions` (relocated by the relearner) | `0x08FD9B8C`, 34 entries `{text*, cursor_cb*}` |
| Its three readers (literals) | `0x1B32F8`, `0x1B37C8`, `0x1B37F8` |
| Relearner's `builder_hook` | `0x08FD9B00` (entered via the trampoline at `0x081B3518`) |
| `SetPartyMonFieldSelectionActions` | `0x081B3414`; it appends SUMMARY, the field moves (`0x13+j`), SWITCH (1), ITEM (3)/MAIL (6), then falls into the hook at `0x081B3518` |
| `AppendToList` | `0x080A0944` (`actions[]` at `+0xF` of `sPartyMenuInternal`, `numActions` at `+0x17`; 8 slots) |
| `sPartyMenuInternal` | `0x0203CEC4` (pointer) · `gPartyMenu` `0x0203CEC8`, `slotId` `+9` |
| `gSpecialVar_0x8004` | `0x020375E0` |
| `gPlayerParty` | `0x020244EC` (100-byte entries) |

Approach: **relocate the party-menu action table again** (35 entries: the 34 we inherit + entry 34 =
`{"Edit", cursor_edit}`), repoint the three readers, and **chain the builder trampoline**: the word at
`0x081B3518` points at our `builder_hook`, which appends action 34 when `numActions < 6` and then jumps to
the relearner's `builder_hook` (which appends *Moves* when `numActions < 7`, then CANCEL, then returns to
`0x081B3529`). Calling, not replacing, so *Moves* keeps working.

Caveat, inherited from the relearner and accepted: `actions[]` holds only 8, so a Pokémon that knows enough
field moves shows fewer options. With the usual 0–2 field moves, both *Moves* and *Edit* appear.

`cursor_edit` mirrors `cursor_moves`: `PlaySE(SE_SELECT)`, set `sPartyMenuInternal->exitCallback (+4)` to
our `cb2_edit`, `Task_ClosePartyMenu`. `cb2_edit` reads `gPartyMenu.slotId`, stashes the slot, and
`SetMainCallback2` our screen.

### Screen

A self-contained BG0 + window screen in the style of the DexNav screen (`patches/dexnav/`): own VBlank
callback, own 16-colour palette, text via `AddTextPrinterParameterized4`, a mon icon sprite in the header.

```
+----------------------------------+
| Edit  <Nickname>            Lv n |   header window
| Nature   Jolly                   |
| HP  IV      31                   |   page 1: nature + 6 IVs
| Atk IV      31                   |
| Def IV       0                   |
| SpA IV       0                   |
| SpD IV       0                   |
| Spe IV      31                   |
|  > UD row   LR +/-   L/R x5      |   hint row
|    START page   B done           |
+----------------------------------+
```

Page 2 is the six EVs plus a running `EV total n/510`. Controls (adjustable at review):

| Input | Action |
|---|---|
| Up / Down | move the cursor between rows |
| Left / Right | value −1 / +1 (auto-repeats while held) |
| L / R | value −5 / +5 |
| START | switch page (nature+IVs ↔ EVs) |
| B | write `CalculateMonStats`, return to the field |

Changes are applied to the mon as they are made, so the summary is live; `B` recalculates stats once more
and exits. `CalculateMonStats 0x08068D0D` is the same routine the Mint NPC path uses.

### Data model (hack stores party mons unencrypted, unshuffled — see NOTES)

| Field | Where | Write rule |
|---|---|---|
| Nature | `mon + 0x1F`, bits 0–6 | preserve bit 7 |
| IVs | 5-bit fields of the word at `mon + 0x48` (HP 0–4, Atk 5–9, Def 10–14, Spe 15–19, SpA 20–24, SpD 25–29) | preserve bit 30 (`isEgg`) and bit 31 (ability slot) |
| EVs | 6 bytes at `mon + 0x38` (HP, Atk, Def, Spe, SpA, SpD) | each 0–255; the screen also clamps the total to 510 |

Species/level for the header: `+0x20`, `+0x54`. Eggs never reach the field-selection action list, so no
egg case to handle. Recalculation: `CalculateMonStats 0x08068D0D`.

### Free space

`0x08F53700` (file), 5,024 bytes — all-`0xFF` in both the original and the v1.4 build, zero aligned
pointers into it, and clean under the project's safe-space allocator (`translation/safespace.py`, margin
260). The old notes' "free" runs at `0x08FE5284`/`0x08FF2454` are **stale**: they now carry real Thumb
pointers, so neither is usable. The patcher asserts the whole region is `0xFF` and refuses otherwise.

## Feature B — Rare Candy NPC in Petalburg's Poké Mart

Recon: Petalburg City is map `0/0`; its Poké Mart is the interior **map `8/6`** (11×8), whose map script
`0x08207D68` holds the two `pokemart` lists `0x08207D8C` / `0x08207DB8`. Its event block is at
`0x0852F304`: 4 objects (array `0x0852F294`, immediately followed by the warp array `0x0852F2F4`), so there
is no spare object slot.

The hack soft-resets on any mart list it does not own (`BuyMenuTryMakePurchase 0x080E0EDC` → `0x096FFF00`),
which is why a candy *shop* was declined. The chosen mechanism is an NPC giver instead:

- Relocate map `8/6`'s 4-entry object array into free space with a **5th entry** — a standing NPC on a free
  tile inside the mart, reusing an existing `OBJ_EVENT_GFX` id — set `nobj = 5` and repoint the events
  struct's object pointer. (Same "copy the table with one extra entry" trick as the START menu and this
  spec's Feature A.)
- New script in free space: `lock` / `faceplayer` / `giveitem ITEM_RARE_CANDY(68), 1` / `msgbox` "Here,
  take a Rare Candy." / `release` / `end`, **repeatable** (no flag gate), to stand in for a shop.
- Item 68 is Rare Candy; the message and any string live in free space.

If adding the object proves unsafe in testing, the fallback is to give the candy from the mart clerk
instead of a new NPC (same script, repointed object). Buying it instead (append Rare Candy to the mart's
existing list `0x08207D8C`) remains a one-line alternative if a real shop is wanted later.

## Build & verify

Two new patchers appended to the chain in `README.md`, after `rbutton`:

```
python patches/partyedit/partyedit_patch.py current.gba out1.gba
python patches/candynpc/candynpc_patch.py   out1.gba out2.gba
```

Each follows the house template (`patches/dexnavchain/dexnavchain_patch.py`): assert `BPEE`/32 MB, assert
every touched site, assemble twice through the `thumb()` check (no Thumb-2), assert the target region is
`0xFF`, print chosen addresses. Lua tests drive mGBA dev (`tools/mgba-dev/mGBA.app`) on copies of the ROM
and a late-game `.sav`, read the mon bytes back with `emu:read8/16/32`, and screenshot the screen.

Verification checklist: open the party menu and confirm *Edit* appears and *Moves* still works; change
nature/IV/EV and confirm the mon's bytes and the summary stats change; confirm a cart with 4 field moves
degrades gracefully; enter the Petalburg Mart and confirm the NPC gives exactly one Rare Candy, repeatedly.

## Out of scope

Level, species, ability, moves, experience, shininess (the personality value), and any change to the save
format or the START menu.
