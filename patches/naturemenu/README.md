# In-party nature changer (WORK IN PROGRESS - not applied, not in the release)

Goal: a **Nature** option in the party menu, beside the relearner's **Moves**, that changes the selected
Pokémon's nature - the same thing the Mint NPC in the Rustboro Trainer's School does after his quiz.

## What was found (all verified by reading the ROM)

| Thing | Where |
|---|---|
| Nature override byte | `mon + 0x1F`, bits 0-6 (bit 7 belongs to something else). It is in BoxPokemon's unused u16 at +30, outside the checksum, so no encryption or PID edit is involved. |
| Apply routine | `0x08FF0E00`: `mon = gPlayerParty[VAR_0x8004]; mon[0x1F] = VAR_0x8005 | (mon[0x1F] & 0x80);` then calls `0x08068D0D` (recalculates stats). |
| Nature menu | script `multichoice` list id `0x7C` - 25 entries, drawn as a 5x5 grid. |
| The Mint NPC's script | `0x0984A66B`: message -> multichoice 0x7C -> `copyvar VAR_0x8005, VAR_RESULT` -> call the "who do I use it on" subroutine (`special 0xA2` = ChoosePartyMon) -> `callnative 0x08FF0E01`. |

## What works in this patch

- The **Nature** entry is appended to the party menu's action list and draws correctly (screenshot-verified).
- Choosing it stores the slot, closes the menu, and the chained field-input hook starts the script.
- The script's message and the game's 25-nature grid appear, the cursor moves, and a choice can be made.
- Nothing crashes: the player returns to normal field control afterwards.

## What does not work yet

The chosen nature is never applied. A debug marker proved that the script's `callnative` **does not call our
routine** - the script continues to the next command (the confirmation message still prints) as though the
command were skipped, and our function never runs. The Mint NPC's own script uses the identical
`23 <ptr>` encoding, so the encoding is right; something about calling a *new* address from a script started by
`ScriptContext1_SetupScript` out of the field-input hook differs. Note the engine also puts the multichoice
result in the variable at `0x020375F0`, not at `VAR_RESULT`'s usual `0x020375F2`.

Next things to try: run the hack's own script fragment at `0x0984A66B` from the hook instead of a new script
(it asks which Pokémon again, but it is proven to work), or set the nature from the party-menu handler in code
and drop the script entirely, using a fixed nature list drawn by our own code.

## Root cause found later (2026-09-15)

The nature grid is `multichoicegrid` (opcode 0x71), which takes **6** bytes: x, y, list id, columns, ignoreBPress.
The script here wrote only 5, so the engine read the following `callnative` opcode (0x23) as the ignoreBPress byte
and skipped the call. The Mint NPC's script has the sixth byte (`71 00 00 7C 05 01`). Adding that byte should make
this patch work; it has not been re-tested.
