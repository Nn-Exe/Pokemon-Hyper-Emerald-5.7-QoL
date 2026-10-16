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
   `0x08FDED20`, plus the Journal at `0x08FE5400..0x08FE91DC` (it grows with its text), berrynum at
   `0x08FEFE00..0x08FEFE74`, the Quest Log at `0x08FEA000..0x08FED3C8` (it grows), sheetonce at `0x08FEE100..0x08FEE130`, goldbox at `0x08FEE400..0x08FEE88C` (0x08FEEA00 kept for it), objpal at `0x08FEF600..0x08FEF684`, roamfix at `0x08FEF700..0x08FEF758`, sprframe at `0x08FEFA20..0x08FEFA5C`, leaguefly at `0x08FEFF00..0x08FEFF0E` and
   leaguetext's strings at `0x08FF2460..0x08FF24C0`; free unreferenced runs remain from `0x08FED3C8` to `0x08FEF600` and from `0x08FEF758` to `0x08FEFA20` and `0x08FEFA5C` to `0x08FEFE00` (words in graphics data read into both by chance: scan before use)
   and from `0x08FF5C36` to `0x08FFD5A0` (hisuimap `0x08FF3000..0x08FF54C0`, ovalcharm `0x08FF5600..0x08FF591A`,
   flyicons `0x08FF5A00..0x08FF5A18`, expshare `0x08FF5B00..0x08FF5C36`). The 0xFF run `0x09FBC380..0x09FD2A00` (89.6 KB) is free: reserved data sat there until 2026-10-07, so it is proven safe for data; the many words that seem to point into it are chance matches in code and text (zhtext's moved texts follow at `0x09FD2A00`). The run `0x08F53700..0x08F54AA0` holds candynpc (`..0x08F5382F`),
   naturefix (`0x08F54200..0x08F5423C`) and hypertrain (`0x08F54300..0x08F543CD`). Inside the second free run,
   `0x08FF6D00..0x08FF723C` is the key ring and repelfix and `0x08FF7240..0x08FF7316` daynight, `0x08FF7320..0x08FF7368`
   rngseed, `0x08FF7380..0x08FF75CC` namingkb's table, `0x08FF75D0..0x08FF7634` dexnavabil, `0x08FF7640..0x08FF76C4` shinyfade, `0x08FF7704..0x08FF7744` mistmsg
   (between the two chance words below); `0x08FF7744..0x08FF7785` is free, but graphics data elsewhere
   holds the words `0x08FF7703` and `0x08FF7785` by chance, so a pointer check stops a blob that reaches them. Dead vanilla bodies used for veneers: ButtonMode_ProcessInput 0x080BAFD4..E3
   (daynight), ButtonMode_DrawChoices 0x080BB030..37 (rngseed). In the hack's
   own tail, `0x09FD8000..0x09FDCB54` is the DexNav screen, the key ring and lmoveinfo, `0x09FDCC00..0x09FDCC80`
   zhtext's stub and names, `0x09FDCD00..0x09FDCE38` fusionfix (then Area Zero: `paldea`'s Journal block from `0x09FE1000` - JOURNAL_END
   `0x09FE8000` - `gen9journal` `0x09FE8000..0x09FEC0F4`, `paldea`'s sprites from `0x09FF1000`; check what is
   still blank there before taking it), and `0x09FD2A00..0x09FD5472` zhtext's moved texts (text only: up to `0x09FD6F00` no
   aligned word points in, but code bytes at odd addresses match by chance). Check inbound pointers
   before using a region, and remember a "pointer" found inside compressed graphics is usually a false hit.
   **Zero-filled space** is the other kind: the hack's upper 16 MB was padded with `0x00` between the author's
   blocks (megabytes of it, e.g. `0x099E5508..0x09D00000`). `speciesx` and `gen9` (in the working
   ROM since 2026-10-11) take `0x0968D000..0x096C4A00` and `0x09A10000..0x09AB810C`; treat both as taken. `paldea` (Area Zero,
   on top of gen9, in the working ROM since 2026-10-11 too) takes `0x09FBC400..` of the 0xFF run (63 KB today, growing) and
   `0x09FF1000..0x09FFC000` in the ROM's free tail (its sprites: 43.8 KB used, 164 bytes left), `0x09FE1000..0x09FF0000` just
   below that (its Journal rows, 13 KB, and the craters' own tileset once the user takes tiles from other maps:
   up to 40 KB together), the hack's
   sprites 125 (the hole), 126 (the pale time crystal of before 2026-10-12: no map has it now), 127, 212, 225, 227 and 240-253 (the table's filler end: seventeen
   Pokemon and a recorder) and 254-255 (the time rift, past and future: no spare entry is left), the field palette tags 0x1124-0x1137 in a longer copy of the field palette table (the
   three words at `0x0808E8BC`, `0x0808E950` and `0x0808E9A8` point at the copy), trainers 943, 947, 952, 958 and
   classes 71-72, the wild table's spare room at
   `0x08E19128` (now full), maps 35/89-100 and layout ids 846-857, flags
   `0x43AB-0x43BE` and `0x43C0-0x43D6` and vars `0x40A8` and `0x40F9`. To tell a real pointer
   from a look-alike, use `speciesx_patch.is_pointer`: a ROM-header word, or a literal that a `ldr rX,[pc,#n]`
   in front of it loads, inside the regions that hold code.
2. Repoint a pointer word rather than rewriting a routine. Many game functions are already trampolines into
   the hack's own code (`ldr rX,[pc,#0]; bx rX; .word target`) — repointing that word is the cheapest hook
   there is, and it is how `CreateWildMon` was taken over.
3. If a site is already hooked, **chain**: read the current target, write yours, jump to the old one when
   done. The overworld hook at `0x08085E5C` already has four patches chained through it (the Journal's stub is first).
4. Trampolines: 8 bytes (`ldr r3,[pc,#0]; bx r3; .word`) only at a 4-aligned site; 10 bytes
   (`ldr r3,[pc,#4]; bx r3; mov r8,r8; .word`, bytes `014b1847c046` + word) otherwise. At an unaligned site the pc rounds down and the ldr
   reads its own trampoline — an instant crash.
5. **A hook on a function's first instruction still has a live `lr`.** The prologue that saves it has not
   run, so any `bl` in your stub destroys the caller's return address. Keep `lr` in a register across the
   stub. Hooks at a function's tail do not have this problem.
6. Thumb-1 only: `ldr rX,[pc,…]` reaches 1020 bytes, so split literal pools every ~900 bytes of code;
   `ldrb/strb` immediates ≤ 31, `ldrh/strh` even and ≤ 62; conditional branches ±256 bytes.
7. **Never write `nop`.** Keystone assembles it as `00 BF`, a Thumb-2 hint that is undefined on the GBA and
   slips past the 4-byte check. Use `mov r8, r8` (`C0 46`).
8. Never write to the save. Scratch belongs in EWRAM you have **measured** as unused (see below).

## Finding EWRAM scratch

Do not reason about it, measure it. `patches/dexnavchain/test_scratch_ram.lua` fills candidate regions with
a pattern and plays through battles, menus, the bag, a save and a Pokénav call, then reports which survived.
`0x0203B700` looked perfect and turned out to be a save staging buffer. `0x0203A660` (32 bytes + 96 of
scratch) is in use by the DexNav chain; `0x02039E40`, `0x0203D600`, `0x0203F100` and `0x02031C00` also
survived the same test. Taken since: `0x02039E40` (the Quest Log's Start-menu widget); `0x02031C00` (64 bytes) is
the egg-move buffer since the eggmoves patch; `0x0203F13C` is hypertrain's byte; `0x0203F130..0x0203F137` is gen9's
battle state (test build); the rest of `0x0203F100..0x0203F12F` is free (the Lua tests put scripts at `0x0203F100`).

**`0x0203D600` is not scratch, though it survived that test.** It is inside the saved overflow stream
(`0x0203CF64..0x0203DE00`): the species of the Pokémon kept inside a fused Necrozma (slot `0x0203D5E0`; Calyrex's is
`0x0203D644`, Kyurem's `0x0203D800`). The test ran with those slots empty. hypertrain used the byte in v1.5 and
players could no longer fuse or split Necrozma (NOTES, *Fusion slots*). Before taking EWRAM, check it is outside
that stream, and measure with a fusion stored.

Guard every scratch block with a magic word and zero it when the magic is absent — EWRAM does not come up
zeroed on hardware.

## Verifying

Run mGBA **dev** (`mGBA.exe --script test.lua rom.gba`, with the ROM's folder as the working directory so
relative paths in the Lua resolve). Keep it off the user's screen: start it through
`gba-trans/_testrun/hidden.ps1` (`Start-Hidden`: a Windows desktop of its own), not with `Start-Process` -
a minimized start still shows mGBA's separate "Scripting" window, in front and with the keyboard.
`_testrun/gen9/run.ps1` is a runner built on it. The Lua drives the game with
`emu:addKey`/`clearKey` on a frame callback, reads memory with `emu:read8/16/32`, and takes
`emu:screenshot(path)`. Write a `*_done.txt` at the end so the shell can wait for it. Breakpoints and
watchpoints do call back in this build (`emu:setBreakpoint(fn, address)`, `emu:setRangeWatchpoint(fn, lo, hi,
C.WATCHPOINT_TYPE.READ)`; registers with `emu:readRegister("pc")`): measured 2026-10-11, `_testrun/tornadus/wp`.
mGBA's own log goes to a file with `-l 79 -C logToFile=1 -C logFile=<path without spaces>`: every access to memory
that is not there is a line in it, which is how the sprframe bug was found.

Two habits that caught real bugs:

- **Screenshot and look.** Tile corruption, a transparent background or a palette that is not what you
  assumed are invisible in memory dumps and obvious in a picture.
- **Compare against a control.** The same script on the unpatched ROM, or the same spot with the feature
  hidden, tells you whether what you are seeing is yours.

Sampling a value on the first frame a battle callback appears reads it *during the transition*, before the
Pokémon is made — sample a few hundred frames in as well before believing it.

**Text you write or re-break** must fit the field message box: 216 px a line (27 tiles), 208 px if a ▼ follows
it. The font is proportional (widths at `0x086542E4`), so count pixels, not letters; a wider line is not
clipped, it wraps round and draws over its own start. `python tools/text_overflow.py <rom>` measures every text
a script shows and must report none; `textfix_patch.py` (BREAKS) is where a too-wide page gets new breaks.

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
  `0x1BC` base stats (28 B; the ability bytes at +22/+23 are leftovers - a species' abilities are three u16 at
  `0x097A0000`, two regular then the hidden one), `0x1C0` ability names (13 B), `0x1C8` items (44 B).
  Egg moves `0x09D78128` (species + 20000 markers), moves `0x09D86419` (12 B, PP at +4).
- **Sprite palette slots in battle** (sSpritePaletteTags `0x03000CF0`, 16 tags, `0xFFFF` = free; slots 0-3 are the
  battlers' own, untagged). Since `ballfree` a battle leaves slots 9-15 free for move animations (before, each
  Pokemon sent out of one of the hack's own balls held two for the whole battle); many animations load three or
  four, a few seven or eight. Never paint into a slot without tagging it - the game hands out the lowest
  free slot and will load over yours (the gold healthbox did this for a month). Since `goldbox` the game's
  LoadSpritePalette / AllocSpritePalette are ours (`0x08FEE694` / `0x08FEE6D8`): when no slot is free, `make_room`
  takes one back from the type badges (tag 0x5E62), then from the gold healthbox (0x5E63). A new battle sprite of
  ours with a palette must be able to lose it the same way (hide, and come back when a slot is free) or go into
  that list. gMain.oamBuffer is gMain + 0x38 (`0x030022F8`); move animations' scripts run in callback1, before
  the OAM buffer is built. NOTES, *The gold healthbox kept its palette*.
- **Sprite tiles** are 1,024 for everything on screen, and LoadSpriteSheet does not look whether a tag is loaded
  already: loading the same sheet twice takes the tiles twice and FreeSpriteTilesByTag gives back one. A sprite
  made from a sheet that did not fit is drawn from tile 0 on (pieces of the first healthbox). The free tiles are
  the zero bits of sSpriteTileAllocBitmap (`0x02021B3C`, 128 bytes); the ranges by tag are sSpriteTileRangeTags
  (`0x030009F0`) / sSpriteTileRanges (`0x03000A70`). NOTES, *The move menu ate the sprite tiles*.
- The start menu **cannot take another entry**: `sCurrentStartMenuActions` is exactly 9 bytes at
  `0x02037610` and `AddStartMenuAction` has no bounds check. Use an item's field-use pointer instead.
- **Species tables** are 1,200 entries each, back to back from `0x08F186E0` (NOTES, *Species tables*, lists all 23).
  `speciesx` moves them to make room: take a table's address from the ROM header (`0x128`-`0x144`, `0x1BC`) or from
  `speciesx_patch.layout()`, not from a constant. The Pokédex holds 960 numbers (flags at SaveBlock1 `+0x560` /
  `+0x5D8`, entries `0x09250000`); cry ids from 388 up are unused.
- **The battle engine** is the hack's own (`0x09D38000..0x09D78000`). A battler's ability is 16-bit at
  `0x0203F000 + 2 * battler` (`gBattleMons[].ability` is only its low byte) and the engine switches on that: an id
  it does not list does nothing. It reads a species' ability at `0x09D00110` (the Pokémon coming in) and
  `0x09D73A9C`. Its command table is `0x09D7717C` (251 entries; entry 5 is the damage calculation `0x09D6046C`);
  the vanilla table at `0x0831BD10` is dead. `0x09D45B84` returns 1 unless Cloud Nine / Air Lock is out; field
  effects are `*(*(0x02024218) + 0xD4)` (Electric Terrain `& 0x1E000`). Type effectiveness is worked out inside
  command 5 (the engine's scripts have no `typecalc`): `gMoveResultFlags & 0x02` is "super effective" as soon as it
  returns. A second table of routines at `0x09D79EAC` (220 entries) is called from scripts by number; entry 24
  is the damage of the set-amount moves, which the engine picks **by the move's number**, as it can a move's
  type. The speed routine is `0x09D5E3F0` (battler in r0; r3 is free at its entry).
- **Moves**: 938 of them (0-937). The data (`0x09D86419`, 12 bytes) has blank rows up to id 1023 and the animation
  pointers (`0x09D0AB00`) up to 1029, so a new move's row and animation go in place; the names (`0x09D30258`),
  the description pointers (`0x09D2AD00`, indexed move - 1) and the Z-Move / Max Move power bytes (`0x09D8A838`,
  `0x09D86050`) end at the last move with other data behind them: `gen9` moves those four to 1,024 entries, so
  take their addresses from the ROM header (`0x148`) or from a literal, not from these constants. NOTES, *Gen 9*.

## Finishing a feature

Apply to the working ROM only after the Lua tests pass, and archive the previous ROM first. Then:
diff the new ROM against the archived one and confirm every changed region is one you intended; copy the
tests into the patch folder; add a row to `README.md`, an entry to `CHANGELOG.md`, and a section to
`docs/NOTES.md` recording the addresses and every gotcha you hit. Do not commit or push unless asked.
