# Party Editor + Rare Candy NPC — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a party-menu *Edit* screen that changes a Pokémon's nature, IVs and EVs, and add an NPC inside Petalburg's Poké Mart that hands out Rare Candy.

**Architecture:** Two standalone Thumb-1 binary patchers in the house style. `patches/candynpc/` relocates Mart map `8/6`'s object array with one extra entry and adds a `giveitem` script. `patches/partyedit/` relocates the party-menu action table with one extra entry, chains the existing builder trampoline, and adds a self-contained BG0+window screen that writes to `gPlayerParty` in place. No save-format change; no game routine rewritten.

**Tech Stack:** Python 3 + `keystone` (Thumb assembler) + `capstone` (verification), mGBA **dev** build driven by Lua for tests. No C source exists; everything is patched bytes.

**Spec:** `docs/superpowers/specs/2026-09-21-party-editor-and-candy-npc-design.md`

## Global Constraints

- Target ROM: `Hyper Emerald v5.7 EN+QoL.gba`, 33,554,432 bytes, header `BPEE` at `0xAC`. Rebuild it with `python3 tools/romdiff.py apply "Hyper EMR LA v5.7 bugfix 2.gba" release/hyper-emerald-en-qol.hpatch build/current.gba` (sha1 must be `e99406d7ce98d528a4968d7e43c8925285bf9454`).
- Every patcher: assert `BPEE`/32 MB → assert every touched site → assemble twice (once for length, once with real data addresses) through the `thumb()` Thumb-2 check → assert the target region is all `0xFF` → write → print chosen addresses. Copy the shape from `patches/dexnavchain/dexnavchain_patch.py`.
- Thumb-1 only. `ldr rX,[pc,#…]` reaches 1020 bytes (split pools every ~900 B); `ldrb/strb` immediates ≤ 31; conditional branches ±256 B.
- Trampolines: 8-byte (`ldr r3,[pc,#0]; bx r3; .word`) only at a 4-aligned site; 10-byte (`ldr r3,[pc,#4]; bx r3; nop; .word`) otherwise.
- A hook on a function's **first** instruction still has a live `lr` — preserve it. Tail hooks do not.
- Never write to the save. Editor scratch that must persist nothing uses `gPlayerParty` directly.
- Run mGBA as: `tools/mgba-dev/mGBA.app/Contents/MacOS/mGBA -C mute=1 -C fpsTarget=2000 -C audioSync=0 -C videoSync=0 --script <test>.lua <rom>.gba`, on copies inside `build/test/`. Write a `<name>_done.txt` at the end so the shell can wait.
- Do not commit or push unless asked.

## Verified facts (from recon, do not re-derive)

| Thing | Address |
|---|---|
| Party action table `sCursorOptions` (relocated) | `0x08FD9B8C`, 34 entries; its 3 literals `0x1B32F8/0x1B37C8/0x1B37F8` |
| Relearner `builder_hook` (append Moves then CANCEL) | `0x08FD9B00`; entered from the trampoline at `0x081B3518`; returns to `0x081B3529` |
| `AppendToList` | `0x080A0944`; `actions[]` at `sPartyMenuInternal(+0xF)`, `numActions` at `+0x17` |
| `sPartyMenuInternal` / `gPartyMenu` / `slotId` / `gSpecialVar_0x8004` | `0x0203CEC4` / `0x0203CEC8` / `+9` / `0x020375E0` |
| `gPlayerParty` | `0x020244EC`, 100-byte entries |
| Mon fields (unencrypted, unshuffled) | nature `+0x1F` bits 0–6; EVs `+0x38` (6 bytes HP,Atk,Def,Spe,SpA,SpD); IV word `+0x48` (5 bits each); species `+0x20`; level `+0x54` |
| `CalculateMonStats` / `PlaySE` / `Task_ClosePartyMenu` | `0x08068D0D` / `0x080A37A5` / `0x081B12C1` |
| `gMain` (newKeys `+0x2E`) | `0x030022C0` |
| Petalburg Mart map | group `8`, num `6`; events struct `0x0852F304` (nobj=4, objects `0x0852F294`, warps `0x0852F2F4`) |
| Script opcodes | lock `0x69`, faceplayer `0x5A`, giveitem `0x44` (item u16, amount u16), release `0x6B`, end `0x02` |
| Rare Candy item id | 68 |
| Free region (both patches) | file `0x08F53700` … `0x08F54AA0` (5024 B), all-`0xFF`, zero inbound pointers |

---

# Part B — Rare Candy NPC (do this first: it proves the harness)

### Task 1: Test harness + baseline

**Files:**
- Create: `patches/candynpc/test_boot.lua`
- Create: `build/test/` (scratch, gitignored via `*.gba`/`*.sav`)

**Interfaces:**
- Produces: a reusable `test_boot.lua` pattern (DIR constant, `emu:screenshot`, `*_done.txt`) that Tasks 2–6 reuse.

- [ ] **Step 1: Write the harness**

```lua
-- patches/candynpc/test_boot.lua
local DIR = "/Users/ribeiro/Downloads/Pokemon-Hyper-Emerald-5.7-QoL/build/test/"
local OUT = DIR .. "screens/"
local frames, done = 0, false
callbacks:add("frame", function()
  frames = frames + 1
  if frames == 240 then emu:screenshot(OUT .. "boot.png") end
  if frames >= 600 and not done then
    done = true
    local f = io.open(DIR .. "boot_done.txt", "w"); f:write("ok\n"); f:close()
    console:log("BOOT OK")
  end
end)
```

- [ ] **Step 2: Run it on the current build (control)**

```bash
mkdir -p build/test/screens
cp build/current.gba build/test/game.gba
tools/mgba-dev/mGBA.app/Contents/MacOS/mGBA -C mute=1 -C fpsTarget=2000 -C audioSync=0 -C videoSync=0 \
  --script patches/candynpc/test_boot.lua build/test/game.gba
```
Expected: process exits, `build/test/boot_done.txt` exists, `screens/boot.png` is a normal title/intro frame.

- [ ] **Step 3: Confirm the free region**

```bash
./.venv/bin/python - <<'PY'
rom=open("build/current.gba","rb").read()
assert rom[0xF53700:0xF54AA0]==b"\xff"*5024, "region not free"
print("free region OK")
PY
```
Expected: `free region OK`.

---

### Task 2: The candy NPC patch

**Files:**
- Create: `patches/candynpc/candynpc.s`
- Create: `patches/candynpc/candynpc_patch.py`
- Create: `patches/candynpc/test_candynpc.lua`

**Interfaces:**
- Consumes: Task 1's harness pattern and the free region.
- Produces: `build/candynpc.gba` (current build + NPC), used by later tasks as the base ROM.

- [ ] **Step 1: Write the script blob source**

The NPC's whole behaviour is one vanilla script; no Thumb needed.
`patches/candynpc/candynpc.s` documents it (kept as a comment file for parity with the other patches):

```
@ Rare Candy NPC in Petalburg Poké Mart (map 8/6). The "NPC" is a relocated copy of the map's
@ object array with one extra entry whose script is the 9 bytes below. No assembly: the script is
@ plain script bytecode written by candynpc_patch.py.
@   lock(69) faceplayer(5A) giveitem(44) 44 00 01 00 release(6B) end(02)
@ 44 00 = item 68 (Rare Candy); 01 00 = amount 1. giveitem shows the "obtained" message itself.
```

- [ ] **Step 2: Write the failing test**

```lua
-- patches/candynpc/test_candynpc.lua
local DIR = "/Users/ribeiro/Downloads/Pokemon-Hyper-Emerald-5.7-QoL/build/test/"
local frames, phase, done = 0, 0, false
-- 8/6 object array (original) and the new 5th entry we expect the patcher to add
local OBJ_ARRAY = 0x0852F294
local NEW_COUNT = 0x0852F304
callbacks:add("frame", function()
  frames = frames + 1
  if frames == 120 then
    -- the events struct's nobj must now be 5, and the 5th object's script must be our script
    console:log(string.format("nobj=%d", emu:read8(NEW_COUNT)))
    console:log(string.format("obj4_script=%08X", emu:read32(NEW_COUNT - 0x10 + 4*24 + 16)))
  end
  if frames >= 180 and not done then
    done = true
    local f = io.open(DIR .. "candynpc_done.txt", "w"); f:write("ok\n"); f:close()
  end
end)
```
Run it once on `build/current.gba` (control): expected `nobj=4` and `obj4_script` reading warp bytes, and **no** `candynpc_done.txt` until patched.

- [ ] **Step 3: Write the patcher**

```python
"""Rare Candy NPC in Petalburg Poke Mart (map 8/6). usage: python candynpc_patch.py <in.gba> <out.gba>"""
import struct, sys
FREE = 0x00F53700
OBJ_ARRAY = 0x052F294            # file offset of map 8/6's 4-object array
OBJ_COUNT = 0x052F304            # file offset of the MapEvents struct (byte 0 = nobj)
OBJ_PTR   = 0x052F308            # file offset of its objectEvents pointer word
COUNT = 4
RARE_CANDY = 68
SCRIPT = bytes((0x69, 0x5A, 0x44)) + struct.pack("<HH", RARE_CANDY, 1) + bytes((0x6B, 0x02))


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    assert rom[OBJ_COUNT] == COUNT, "map 8/6 object count unexpected"
    assert struct.unpack_from("<I", rom, OBJ_PTR)[0] == 0x08000000 + OBJ_ARRAY, "object array pointer unexpected"
    blob = bytes(rom[OBJ_ARRAY:OBJ_ARRAY + COUNT * 24])
    assert len(SCRIPT) == 9
    # new object: gfx id reused from obj1 (0x13), tile (4,6), flag 0, script -> our copy
    gfx = rom[OBJ_ARRAY + 24 + 1]
    newobj = bytearray(24)
    newobj[1] = gfx
    struct.pack_into("<h", newobj, 4, 4)      # x
    struct.pack_into("<h", newobj, 6, 6)      # y
    script_addr = 0x08000000 + FREE + COUNT * 24
    struct.pack_into("<I", newobj, 16, script_addr)
    end = FREE + (COUNT + 1) * 24 + len(SCRIPT)
    assert set(rom[FREE:end]) == {0xFF}, "target region not free"
    rom[FREE:FREE + COUNT * 24] = blob
    rom[FREE + COUNT * 24:FREE + (COUNT + 1) * 24] = bytes(newobj)
    rom[FREE + (COUNT + 1) * 24:end] = SCRIPT
    rom[OBJ_COUNT] = COUNT + 1
    struct.pack_into("<I", rom, OBJ_PTR, 0x08000000 + FREE)
    open(outp, "wb").write(rom)
    print("object array -> 0x%08X (5 entries), script @0x%08X" % (0x08000000 + FREE, script_addr))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
```

- [ ] **Step 4: Run it and re-run the test**

```bash
./.venv/bin/python patches/candynpc/candynpc_patch.py build/current.gba build/candynpc.gba
cp build/candynpc.gba build/test/game.gba
tools/mgba-dev/mGBA.app/Contents/MacOS/mGBA -C mute=1 -C fpsTarget=2000 -C audioSync=0 -C videoSync=0 \
  --script patches/candynpc/test_candynpc.lua build/test/game.gba
```
Expected: `nobj=5`, `obj4_script` = the patched script address, `candynpc_done.txt` written.

- [ ] **Step 5: Play-verify by hand (screenshot)**

Extend `test_candynpc.lua` to walk into the Mart and talk to the NPC (drive keys with `emu:addKey`), then
`emu:screenshot`. This is where a real save matters; if none is available, set the spawn warp with the
throwaway-ROM trick in `patches/mintskip/test_mintskip.lua`. Expected: the NPC shows the "obtained a Rare
Candy!" message and the bag gains one (check `gBagPockets`).

- [ ] **Step 6: Commit**

```bash
git add patches/candynpc/
git commit -F - <<'EOF'
Add Rare Candy NPC to Petalburg's Poké Mart

Co-authored-by: CommandCodeBot <noreply@commandcode.ai>
EOF
```

---

# Part A — Party editor

### Task 3: Menu entry — relocate the action table and chain the builder hook

**Files:**
- Create: `patches/partyedit/partyedit.s` (entry + cursor callback + cb2 only, this task)
- Create: `patches/partyedit/partyedit_patch.py`
- Create: `patches/partyedit/test_entry.lua`

**Interfaces:**
- Consumes: `build/candynpc.gba` as the base ROM; `patches/relearner/relearner_patch.py` and `patches/dexnav/dexnav_patch.py` as structural templates.
- Produces: `builder_hook`, `cursor_edit`, `cb2_edit` symbol addresses that Task 4 extends; a relocated 35-entry table.

- [ ] **Step 1: Write the failing test**

```lua
-- patches/partyedit/test_entry.lua
-- Synthesize a party member in RAM, open START > POKEMON, then the party menu, and screenshot the
-- action list. We assert the number of actions and that an "Edit" label row exists by pixel-diffing
-- against the unpatched build's screenshot (kept as entry_control.png).
local DIR = "/Users/ribeiro/Downloads/Pokemon-Hyper-Emerald-5.7-QoL/build/test/"
local frames, done = 0, false
local PARTY = 0x020244EC
callbacks:add("frame", function()
  frames = frames + 1
  if frames == 60 then
    -- one plausible mon: species 25 (Pikachu), level 5, 0 EVs, 31/31/31/0/0/31 IVs, nature 0
    emu:write8(PARTY + 0x1F, 0)
    emu:write16(PARTY + 0x20, 25)
    emu:write8(PARTY + 0x54, 5)
    emu:write32(PARTY + 0x48, 0x7C000000 | (31) | (31 << 5) | (31 << 10) | (31 << 25))
    emu:write8(0x02024498, 1)              -- gPlayerPartyCount
  end
  if frames == 300 then emu:screenshot(DIR .. "screens/entry_patched.png") end
  if frames >= 420 and not done then
    done = true
    local f = io.open(DIR .. "entry_done.txt", "w"); f:write("ok\n"); f:close()
  end
end)
```

- [ ] **Step 2: Run the control and record `entry_control.png`**

Run the same script (with only the screenshot name difference) on `build/candynpc.gba`; keep the shot. This is the "compare against a control" habit from `docs/NOTES.md`.

- [ ] **Step 3: Write the entry assembly**

`patches/partyedit/partyedit.s` — this task's part:

```asm
@ Party editor: menu entry. builder_hook is entered from the trampoline at 0x081B3518
@ (the CANCEL append in SetPartyMonFieldSelectionActions). It appends EDIT (34) when there is
@ room, then jumps to the relearner's builder_hook, which appends MOVES (33) and CANCEL and
@ returns to 0x081B3529. Tail hook: no live lr to preserve.
.thumb
builder_hook:
    ldr r0, lit_internal
    ldr r1, [r0]
    ldrb r2, [r1, #0x17]        @ numActions
    cmp r2, #6
    bhs bh_chain                @ no room for one more
    adds r0, r1, #0
    adds r0, #0xF               @ actions[]
    adds r1, #0x17              @ &numActions
    movs r2, #34                @ MENU_EDIT
    ldr r3, lit_append
    bl call3
bh_chain:
    ldr r3, lit_prev            @ relearner builder_hook 0x08FD9B00
    bx r3

cursor_edit:                    @ (u8 taskId) - mirrors CursorCb_Summary 0x081B37FC
    push {r4, lr}
    lsls r4, r0, #24
    lsrs r4, r4, #24
    movs r0, #5
    ldr r3, lit_playse
    bl call3                    @ PlaySE(SE_SELECT)
    ldr r0, lit_internal
    ldr r1, [r0]
    ldr r0, lit_cb2_edit
    str r0, [r1, #4]            @ sPartyMenuInternal->exitCallback = cb2_edit
    adds r0, r4, #0
    ldr r3, lit_close
    bl call3                    @ Task_ClosePartyMenu(taskId)
    pop {r4}
    pop {r0}
    bx r0

cb2_edit:                       @ main callback once the party menu has faded
    ldr r0, lit_party
    ldrb r0, [r0, #9]           @ gPartyMenu.slotId
    ldr r1, lit_var8004
    strh r0, [r1]               @ gSpecialVar_0x8004 = slot
    ldr r0, lit_cb2_screen
    bx r0                       @ our editor screen (Task 4)

call3:
    bx r3

.align 2
lit_internal:   .word 0x0203CEC4
lit_append:     .word 0x080A0945
lit_prev:       .word 0x08FD9B01
lit_playse:     .word 0x080A37A5
lit_cb2_edit:   .word CB2_EDIT_ADDR
lit_close:      .word 0x081B12C1
lit_party:      .word 0x0203CEC8
lit_var8004:    .word 0x020375E0
lit_cb2_screen: .word CB2_SCREEN_ADDR
```

- [ ] **Step 4: Write the patcher**

`patches/partyedit/partyedit_patch.py`, modelled on `patches/dexnavchain/dexnavchain_patch.py`:

```python
FREE = 0x00F53700            # same verified region; Task 2's blob is small, this patch owns from here
TABLE = 0x615C08 + 0        # current relocated table is at 0x08FD9B8C (34 entries)
HOOK  = 0x1B3518
LITS  = (0x1B32F8, 0x1B37C8, 0x1B37F8)
EDITS = 34
```
It must: assert `rom[HOOK:HOOK+4] == bytes.fromhex("004b1847")` and that the word at `HOOK+4` is
`0x08FD9B01`; assert each of the three literals reads `0x08FD9B8C`; read the 34-entry table
(`rom[0xFD9B8C:0xFD9B8C+34*8]`); assemble the source with `thumb()`; lay out `code | text("Edit") |
table(35)`; write at `FREE`; repoint the three literals to the new table; replace the hook with
`004b1847 || .word BASE|1 || 4x nop`. Print every address.

- [ ] **Step 5: Run test and compare with control**

```bash
./.venv/bin/python patches/partyedit/partyedit_patch.py build/candynpc.gba build/partyedit.gba
cp build/partyedit.gba build/test/game.gba
tools/mgba-dev/mGBA.app/Contents/MacOS/mGBA -C mute=1 -C fpsTarget=2000 -C audioSync=0 -C videoSync=0 \
  --script patches/partyedit/test_entry.lua build/test/game.gba
```
Expected: the patched screenshot shows an extra **Edit** row versus `entry_control.png`; *Moves* is still
present. Compare with `patches/dexnavchain/test_boot.lua`'s screenshot helper.

- [ ] **Step 6: Commit**

```bash
git add patches/partyedit/
git commit -F - <<'EOF'
Add an Edit action to the party menu

Co-authored-by: CommandCodeBot <noreply@commandcode.ai>
EOF
```

---

### Task 4: Editor screen skeleton

**Files:**
- Modify: `patches/partyedit/partyedit.s` (add screen functions)
- Modify: `patches/partyedit/partyedit_patch.py`
- Create: `patches/partyedit/test_screen.lua`

**Interfaces:**
- Consumes: `cb2_edit` from Task 3; the DexNav screen template (`patches/dexnav/dexnav.s`, `patches/dexnav/dexnav_patch.py`).
- Produces: `cb2_screen`, `vblank`, `task`, `draw`, `print`, `u8dec` symbols; the `CB2_SCREEN_ADDR` used in Task 3.

- [ ] **Step 1: Write the failing test** — assert `CB2_SCREEN_ADDR` no longer points at the current build's value and that a screenshot after selecting *Edit* is not the field.

```lua
-- patches/partyedit/test_screen.lua  (drives the same party synthesis as Task 3,
-- then navigates START > POKEMON > (mon) > Edit and screenshots)
```

- [ ] **Step 2: Add the screen to the assembly**

Follow the DexNav screen exactly for plumbing: one BG (CharBase/map from the DexNav's `BGTEMPLATE 0x31F0`),
a tilemap buffer from `AllocZeroed(0x800)`, windows on palette 15 loaded from our own 16-colour palette
(set index 0 background, never leave a used colour at 0), text via `AddTextPrinterParameterized4` speed 0.
Functions to add:

| Function | Responsibility |
|---|---|
| `cb2_screen` | init once (`init_screen`), then per-frame `RunTasks` + `draw` |
| `vblank` | `CopyWindowToVram` / palette flush, mirror of the DexNav vblank |
| `task` | `ReadKeys` → cursor move / value change / page / exit |
| `draw` | redraw header, 7 rows, values, cursor, hint |
| `print` | `AddTextPrinterParameterized4` wrapper |
| `u8dec` | 0–255 → up to 3 digits into a scratch string |

Window layout (24×16 at tile base `0x240`, the region the DexNav proved clear of the map and the field's
own windows): header row, then 7 value rows, then a 2-row hint. Row order on page 1: Nature, HP, Atk, Def,
SpA, SpD, Spe IVs. Page 2: the six EVs + `EV total n/510`.

- [ ] **Step 3: Run and screenshot**

Run `test_screen.lua`. Expected: the screen appears with the mon's name/level, nature, and six values; the
field is not visible through it. **Look at the picture** — tile corruption and transparency are invisible in
memory dumps.

- [ ] **Step 4: Commit** as in Task 3.

---

### Task 5: Editing writes

**Files:**
- Modify: `patches/partyedit/partyedit.s`
- Modify: `patches/partyedit/partyedit_patch.py`
- Create: `patches/partyedit/test_edit.lua`

**Interfaces:**
- Consumes: Task 4's row model.
- Produces: `apply_nature`, `apply_iv`, `apply_ev` routines; the mon byte layouts the test asserts.

- [ ] **Step 1: Write the failing test**

```lua
-- patches/partyedit/test_edit.lua
-- After the party is synthesized, drive: Edit, down x1 (to HP IV), right x3, B.
-- Then read the bytes back.
local PARTY = 0x020244EC
callbacks:add("frame", function()
  frames = frames + 1
  if frames == 500 then
    console:log("nature=" .. emu:read8(PARTY + 0x1F))
    console:log("ivs=" .. string.format("%08X", emu:read32(PARTY + 0x48)))
    console:log("ev_hp=" .. emu:read8(PARTY + 0x38))
  end
end)
```
Control (unpatched): IVs unchanged. Patched: HP IV field = initial+3, `isEgg`/ability bits untouched.

- [ ] **Step 2: Implement the writes**

- Nature (row 0): read/modify/write `mon+0x1F`, keeping bit 7: `ldrb r1,[r0,#0x1F]; and r1,#0x80; orr r1,r2; strb r1,[r0,#0x1F]`.
- IV row *i* (0=HP…5=Spe): build a mask/shift table (HP 0, Atk 5, Def 10, Spe 15, SpA 20, SpD 25), clear the
  5-bit field in `mon+0x48`, or in the new value. Preserve bits 30/31.
- EV row *i*: `strb` the value at `mon + 0x38 + i`. Clamp each to 255 and clamp the six-byte total to 510.
- After any change: `CalculateMonStats 0x08068D0D` (reused, not reimplemented).

- [ ] **Step 3: Run and read the bytes back** — expected values as above.

- [ ] **Step 4: Visual check with the in-game summary**

Open the mon's summary after editing (drive keys) and screenshot; the stats must match the new IV/EV/nature.

- [ ] **Step 5: Commit** as in Task 3.

---

### Task 6: Page switch, EV total, and the field-move edge case

**Files:**
- Modify: `patches/partyedit/partyedit.s`, `patches/partyedit/partyedit_patch.py`
- Create: `patches/partyedit/test_pages.lua`

- [ ] **Step 1: Test page switching (START) shows the six EVs and `EV total n/510`, and that the total updates.**
- [ ] **Step 2: Implement START → page toggle; recompute the total on each draw (`u8dec` ×2).**
- [ ] **Step 3: Test the degradation case:** teach the synthesized mon 4 field moves (write the move ids into `+0x2C` and set the field-move table match), reopen the party menu, and confirm *Edit* is hidden exactly as *Moves* is — no crash, no overrun of `actions[]`.
- [ ] **Step 4: Run, screenshot, commit.**

---

### Task 7: Docs, changelog, release chain

**Files:**
- Modify: `README.md` (Features table + *Rebuild from source* chain, after the `rbutton` line)
- Modify: `CHANGELOG.md` (new dated entry)
- Modify: `docs/NOTES.md` (new sections: addresses, gotchas, the stale free-run correction)
- Modify: `docs/features.html` (the Rare Candy row under declined/limitations)
- Modify: `release/`

- [ ] **Step 1: Add the two patchers to the README chain** after `rbutton`, with the correct in/out names.
- [ ] **Step 2: Run the whole chain end to end** from `Hyper EMR LA v5.7 bugfix 2.gba` and confirm it reaches a build whose diff against `build/partyedit.gba` is empty.
- [ ] **Step 3: Rebuild `release/hyper-emerald-en-qol.hpatch`** with `tools/romdiff.py create original.gba out.gba release/hyper-emerald-en-qol.hpatch` and update `release/CHECKSUMS.txt`. Ask before publishing anything.
- [ ] **Step 4: Write the NOTES sections** — the new addresses, every gotcha hit, and a note that the old `0x08FE5284`/`0x08FF2454` free-run claim is stale for this build.
- [ ] **Step 5: Commit** (docs only; do not push).

---

## Self-Review

**Spec coverage:** editor entry point → Task 3; screen → Task 4; nature/IV/EV writes + recalc → Task 5;
page/EV-total/field-move caveat → Task 6; candy NPC → Task 2; free-space correction, build chain, release
→ Tasks 1/7. All spec sections map to a task.

**Known gaps to close during execution (recorded, not hand-waved):**
1. The live nature-name table. Recon found a 25-entry pointer table at `0x0861CB50` whose entries decode to
   the nature names, but `docs/NOTES.md` claims a *dead* copy exists at `0x0861CAAC`. Task 4 step 1 must
   verify which is referenced by code before using it; if neither is live, read the names out of the
   multichoice list `0x7C`'s strings (proven live by `patches/mintskip/`).
2. The exact `giveitem` operand width. Disassembly of `0x080999A0` shows two halfword reads, so
   `item u16, amount u16`; Task 2 step 4 confirming the bag gained one item settles it.
3. `CB2_ReturnToField` address for the editor's exit (candidate `0x080860C8`, the Sinnoh map's exit).
   Confirm from `patches/sinnohmap/sinnohmap.s` before wiring.

**Type consistency:** `cb2_edit`/`cursor_edit`/`builder_hook` (Task 3) are the names reused in Tasks 4–6;
`CB2_SCREEN_ADDR`/`CB2_EDIT_ADDR` are the only cross-task placeholders, both substituted by the patcher.
