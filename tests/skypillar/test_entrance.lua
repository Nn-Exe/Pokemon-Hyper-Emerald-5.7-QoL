-- Sky Pillar entrance 24/79: the "a free slot?" prompt at (3,9) - No pushes you back, Yes turns the trigger off
-- (var 0x400F = 1) - and the door check at (10,2): without the 3rd Meteorite you are sent back.
NAME = "entrance"
DIR = DIR or "./"
HERE = HERE or DIR
dofile(HERE .. "../../patches/dexnavchain/test_boot.lua")
local SCRIPT = 0x0203F100
local function sb1() return emu:read32(0x03005D8C) end
local function sb2() return emu:read32(0x03005D90) end
local function flagbyte(f)
  if f < 0x4000 then return sb1() + 0x1270 + (f >> 3) end
  local i = (f - 0x4000) >> 3
  if i <= 0x33 then return sb1() + 0x988 + i end
  if i <= 0x67 then return sb1() + 0x3B24 + i - 0x34 end
  if i <= 0x9B then return sb2() + 0x5C + i - 0x68 end
  return sb2() + 0x28 + i - 0x9C
end
local function setflag(f, on)
  local a = flagbyte(f); local b = emu:read8(a)
  if on then b = b | (1 << (f & 7)) else b = b & ~(1 << (f & 7)) & 0xFF end
  emu:write8(a, b)
end
local function var(v) return emu:read16(sb1() + 0x139C + (v - 0x4000) * 2) end
local function setvar(v, x) emu:write16(sb1() + 0x139C + (v - 0x4000) * 2, x) end
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1); emu:write8(0x03000E38, 0)
end
local function pos() local pl = 0x02037350; return emu:read16(pl + 0x10) - 7, emu:read16(pl + 0x12) - 7 end
local t0
local plan = {}
local function at(d, fn) plan[#plan + 1] = {d, fn} end
at(1, function()
  setflag(0x1C0, false); setflag(0x50, false); setvar(0x400F, 0)
  run({0x39, 24, 79, 0xFF, 3, 0, 10, 0, 0x02})
end)
at(300, function() local x, y = pos(); w(string.format("at (%d,%d), var400F %d", x, y, var(0x400F))); tap(K.UP, 24) end)
at(360, function() shot("en_1") end)
at(420, function() tap(K.A) end)
at(480, function() shot("en_2") end)
at(540, function() tap(K.A) end)
at(600, function() shot("en_3_yesno") end)
at(620, function() tap(K.B) end)                  -- No
at(760, function() local x, y = pos(); w(string.format("after No: at (%d,%d), var400F %d, lock %d", x, y, var(0x400F), lock())); shot("en_4_after_no") end)
at(800, function() tap(K.UP, 24) end)
for k = 0, 9 do at(880 + k * 40, function() tap(K.A) end) end   -- through the text, then Yes
at(1400, function() local x, y = pos(); w(string.format("after Yes: at (%d,%d), var400F %d, lock %d", x, y, var(0x400F), lock())); shot("en_5_after_yes") end)
at(1420, function() shot("en_5a_before_again"); tap(K.DOWN, 24) end)
at(1480, function() tap(K.UP, 24) end)
at(1600, function() local x, y = pos(); w(string.format("stepped on it again: at (%d,%d), lock %d (0 = no prompt)", x, y, lock())); shot("en_5b_again") end)
-- the door check: no 3rd Meteorite in the Bag
at(1620, function()
  local base, cap = emu:read32(0x02039DD8), emu:read8(0x02039DD8 + 4)
  for s = 0, cap - 1 do if emu:read16(base + 4 * s) == 690 then emu:write32(base + 4 * s, 0) end end
  run({0x39, 24, 79, 0xFF, 10, 0, 3, 0, 0x02})
end)
at(1920, function() local x, y = pos(); w(string.format("below the door at (%d,%d)", x, y)); tap(K.UP, 24) end)
at(1980, function() shot("en_6_door") end)
at(2040, function() tap(K.A) end)
at(2200, function() local x, y = pos(); w(string.format("after the door message: at (%d,%d), lock %d", x, y, lock())); shot("en_7_door_after"); done() end)
function TEST(f) t0 = t0 or f; for _, p in ipairs(plan) do if f - t0 == p[1] then p[2]() end end end
