-- Items pocket 200 slots: a save STATE from before the patch. Such a state brings back the old memory - the pocket
-- table pointing at the old 100 slots, no MARKER - without the boot-time load that migrates. The game re-runs the
-- pocket setup (SetSaveBlocksPointers) after a battle and on some map loads, and the Bag must then still hold the
-- items. Simulated here on a normal boot: put the old layout back in memory, then warp, then a wild battle.
NAME = "bagslots_state"
DIR = DIR or "./"
HERE = HERE or DIR
dofile(HERE .. "../dexnavchain/test_boot.lua")
local POCKETS, OLD, NEW, MARKER = 0x02039DD8, 0x0203D030, 0x0203DAE0, 0x0203DADC
local SCRIPT = 0x0203F100
local fails = 0
local function ok(c, m) w((c and "  ok   " or "  FAIL ") .. m); if not c then fails = fails + 1 end end
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1); emu:write8(0x03000E38, 0)
end
local function count(base, n) local c = 0; for i = 0, n - 1 do if emu:read16(base + 4 * i) ~= 0 then c = c + 1 end end; return c end
local function items() return count(emu:read32(POCKETS), emu:read8(POCKETS + 4)) end
local function report(tag)
  w(string.format("%-22s Items pocket %08X x%d: %d items, marker %08X", tag, emu:read32(POCKETS), emu:read8(POCKETS + 4),
    items(), emu:read32(MARKER)))
end
local t0, want, phase = nil, nil, 0
function TEST(f)
  t0 = t0 or f
  local d = f - t0
  if d == 1 then
    report("after boot")
    want = count(OLD, 100)
    -- the memory of a pre-patch save state: old pointer, no marker, nothing in the new area
    emu:write32(POCKETS, OLD); emu:write8(POCKETS + 4, 100); emu:write32(MARKER, 0)
    for i = 0, 199 do emu:write32(NEW + 4 * i, 0) end
    report("as a v1.5 state")
    local sb1 = emu:read32(0x03005D8C)
    local g, n, x, y = emu:read8(sb1 + 4), emu:read8(sb1 + 5), emu:read16(sb1), emu:read16(sb1 + 2)
    run({0x39, g, n, 0xFF, x & 0xFF, x >> 8, y & 0xFF, y >> 8, 0x02})   -- warp to where we stand: a map load
  end
  if d == 400 then
    report("after a warp")
    run({0xB6, 129, 0, 2, 0, 0, 0xB7, 0x02})                           -- a wild Magikarp Lv 2
    phase = 1
  end
  if phase == 1 and d > 420 then
    if cb2() == OVERWORLD and lock() == 0 and d > 900 then
      report("after a battle")
      ok(items() == want, string.format("the Bag still holds the %d items", want))
      ok(emu:read32(POCKETS) == NEW and emu:read8(POCKETS + 4) == 200, "and it is the 200-slot pocket")
      w(fails == 0 and "ALL PASSED" or (fails .. " FAILED"))
      phase = 2; done(); return
    end
    if d % 20 == 0 then tap(K.A) end
    if d > 6000 then w("  FAIL the battle never ended"); phase = 2; done() end
  end
end
