---
name: hyper-emerald-patch
description: Add or change a feature in the Hyper Emerald v5.7 GBA ROM hack (BPEE) by binary patching - Thumb assembly into free space plus repointed pointer words, verified by driving mGBA with Lua. Use for any "add X to the game", "fix X in the ROM", "hook X" task in this project, and before touching patches/*/ or docs/NOTES.md.
---

# Patching Hyper Emerald v5.7

There is no C source. A feature is Thumb assembly assembled at a fixed address, written into free ROM, and
reached by repointing as few pointer words as possible. Read the *DEXNAV SEARCH AND CHAIN* and *SINNOH MAP
SCREEN* sections of `docs/NOTES.md` for worked examples before starting a new one.

## The shape of a patch

```
patches/<name>/<name>.s          Thumb source. Placeholders like FOO_ADDR are substituted by the patcher.
patches/<name>/<name>_patch.py   python <name>_patch.py in.gba out.gba
patches/<name>/test_*.lua        mGBA Lua that drives the game and reads memory back
```

The patcher always: asserts the ROM is `BPEE` and 32 MB → asserts every site it is about to touch still
looks the way it expects → assembles twice (once to learn the code length, once with the real data
addresses) → asserts the target region is all `0xFF` → writes → prints the addresses it chose. Copy the
structure from `patches/dexnavchain/dexnavchain_patch.py`; it is the most complete one.

Two checks in that template matter more than they look:

- **`thumb()`** assembles a twin with every `.word` line replaced by two nops and asserts Capstone finds no
  4-byte instruction. A pool word like `0xFFFF` stops a linear sweep dead, and a leaked Thumb-2 encoding
  will not run on a GBA.
- **counting `push`** to locate functions. Each function must start with a `push`, and the patcher asserts
  the count. If you add a function, update the `order` tuple.

## Rules that are not negotiable

1. Free space is a run of `0xFF` **with no pointers into it**. Current blobs run from `0x08FD8C00` to
   `0x08FDED20`; bigger unreferenced runs sit at `0x08FE5284` and `0x08FF2454`. Check inbound pointers
   before using a region, and remember a "pointer" found inside compressed graphics is usually a false hit.
2. Repoint a pointer word rather than rewriting a routine. Many game functions are already trampolines into
   the hack's own code (`ldr rX,[pc,#0]; bx rX; .word target`) — repointing that word is the cheapest hook
   there is, and it is how `CreateWildMon` was taken over.
3. If a site is already hooked, **chain**: read the current target, write yours, jump to the old one when
   done. The overworld hook at `0x08085E5C` already has three patches chained through it.
4. Trampolines: 8 bytes (`ldr r3,[pc,#0]; bx r3; .word`) only at a 4-aligned site; 10 bytes
   (`ldr r3,[pc,#4]; bx r3; nop; .word`) otherwise. At an unaligned site the pc rounds down and the ldr
   reads its own trampoline — an instant crash.
5. **A hook on a function's first instruction still has a live `lr`.** The prologue that saves it has not
   run, so any `bl` in your stub destroys the caller's return address. Keep `lr` in a register across the
   stub. Hooks at a function's tail do not have this problem.
6. Thumb-1 only: `ldr rX,[pc,…]` reaches 1020 bytes, so split literal pools every ~900 bytes of code;
   `ldrb/strb` immediates ≤ 31, `ldrh/strh` even and ≤ 62; conditional branches ±256 bytes.
7. Never write to the save. Scratch belongs in EWRAM you have **measured** as unused (see below).

## Finding EWRAM scratch

Do not reason about it, measure it. `patches/dexnavchain/test_scratch_ram.lua` fills candidate regions with
a pattern and plays through battles, menus, the bag, a save and a Pokénav call, then reports which survived.
`0x0203B700` looked perfect and turned out to be a save staging buffer. `0x0203A660` (32 bytes + 96 of
scratch) is in use by the DexNav chain; `0x02039E40`, `0x0203D600`, `0x0203F100` and `0x02031C00` also
survived the same test and are free.

Guard every scratch block with a magic word and zero it when the magic is absent — EWRAM does not come up
zeroed on hardware.

## Verifying

Run mGBA **dev** (`mGBA.exe --script test.lua rom.gba`, launched with PowerShell `Start-Process` and
`-WorkingDirectory` so relative paths in the Lua resolve). The Lua drives the game with
`emu:addKey`/`clearKey` on a frame callback, reads memory with `emu:read8/16/32`, and takes
`emu:screenshot(path)`. Write a `*_done.txt` at the end so the shell can wait for it. Breakpoints via
`emu:setBreakpoint` did not fire in this build — log from the frame callback instead.

Two habits that caught real bugs:

- **Screenshot and look.** Tile corruption, a transparent background or a palette that is not what you
  assumed are invisible in memory dumps and obvious in a picture.
- **Compare against a control.** The same script on the unpatched ROM, or the same spot with the feature
  hidden, tells you whether what you are seeing is yours.

Sampling a value on the first frame a battle callback appears reads it *during the transition*, before the
Pokémon is made — sample a few hundred frames in as well before believing it.

## Facts worth having in front of you

- `GetMonData 0x0806A519`, `SetMonData 0x0806ACAD`, `CalculateMonStats 0x08068D0D`, `Random16 0x0806F5CD`,
  `__umodsi3 0x082E7BE1`, `IsShinyOtIdPersonality 0x0806EBD1`, `PlaySE 0x080A37A5`.
- Mon data is **unencrypted and unshuffled**: species `+0x20`, moves `+0x2C`, PP `+0x34`, IV word `+0x48`
  (5 bits per stat, bit 30 isEgg, bit 31 second ability), level `+0x54`. `gEnemyParty 0x02024744`,
  `gPlayerParty 0x020244EC`.
- `gBattleOutcome 0x0202433A` (1 won, 4 ran, 6 the wild one fled, 7 caught, 0 while a battle is starting).
- `LockPlayerFieldControls`' byte is `0x03000F2C`: non-zero whenever a menu, message, script or Pokénav call
  owns the screen. Anything you draw on the field should stand down while it is set.
- Windows: `AddWindow 0x08003381`, `RemoveWindow 0x08003575`, `FillWindowPixelBuffer 0x08003C49`,
  `PutWindowTilemap 0x0800378D`, `CopyWindowToVram 0x08003659`,
  `AddTextPrinterParameterized4 0x08199EED`, `LoadPalette 0x080A1939`.
- **Field BG0 tiles start at VRAM `0x06008000` and the map's tilemaps at `0x0600E000`** — a window baseBlock
  at or above tile `0x300` overwrites the map. The game keeps its message window at `0x194`, the location
  popup at `0x107` and the standard frame at `0x214`.
- Colour index 0 is transparent on a background. Tiles you blit by hand need a real colour, not 0, or the
  map shows through. The field text palette (15) has no black; entries 10–12 are spare duplicate whites.
- `LZ77UnCompVram` cannot use back-references of distance 1 — the BIOS writes VRAM a halfword at a time, so
  the byte just produced reads back as 0. Minimum distance 2.
- Table pointers live in the ROM header: `0x144` species names (11 B), `0x14C` move names (13 B),
  `0x1BC` base stats (28 B, abilities at +22/+23), `0x1C0` ability names (13 B), `0x1C8` items (44 B).
  Egg moves `0x09D78128` (species + 20000 markers), moves `0x09D86419` (12 B, PP at +4).
- The start menu **cannot take another entry**: `sCurrentStartMenuActions` is exactly 9 bytes at
  `0x02037610` and `AddStartMenuAction` has no bounds check. Use an item's field-use pointer instead.

## Finishing a feature

Apply to the working ROM only after the Lua tests pass, and archive the previous ROM first. Then:
diff the new ROM against the archived one and confirm every changed region is one you intended; copy the
tests into the patch folder; add a row to `README.md`, an entry to `CHANGELOG.md`, and a section to
`docs/NOTES.md` recording the addresses and every gotcha you hit. Do not commit or push unless asked.
