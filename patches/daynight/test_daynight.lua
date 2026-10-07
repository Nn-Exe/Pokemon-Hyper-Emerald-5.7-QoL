-- Day/Night On / Off. On Route 102 with the game clock moved to 23:00 (the save's time offset is shifted):
--  1. On (the bit clear): the screen's palette differs from the game's finished palette (tinted), time of day 5.
--  2. the bit set by hand: the screen's palette equals the game's (no tint); time of day still 5.
--  3. the bit cleared: tinted again.
--  4. the Option menu: the 7th row reads Day/Night On Off; RIGHT on it sets the bit, A does nothing, B leaves;
--     back on the field: no tint. Again with LEFT: the bit clear, the tint back.
--  5. the clock at 12:00, On: no tint either way.
-- Log daynight_log.txt (PASS / FAIL lines), shots dn_*.png.
NAME = "daynight"
dofile((DIR or "./") .. "../dexnavchain/test_boot.lua")
local SCRIPT = 0x0203F100
local OPTION_CB2 = nil
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1); emu:write8(0x03000E38, 0)
end
local function sb2() return emu:read32(0x03005D90) end
local function hour() return emu:read8(0x03005CFA) end
local function sethour(h)
  local off = emu:read8(sb2() + 0x9A)
  if off >= 128 then off = off - 256 end
  emu:write8(sb2() + 0x9A, (off + hour() - h) % 24)
end
local function bit() return (emu:read8(sb2() + 0x15) >> 4) & 1 end
local function setbit(v)
  local b = emu:read8(sb2() + 0x15)
  emu:write8(sb2() + 0x15, v == 1 and (b | 0x10) or (b & 0xEF))
end
local function tinted()                              -- colours on screen that differ from the game's finished palette
  local n = 0
  for i = 0, 0x3FE, 2 do
    if emu:read16(0x05000000 + i) ~= emu:read16(0x02037B14 + i) then n = n + 1 end
  end
  return n
end
local fails = 0
local function check(name, ok, detail)
  if not ok then fails = fails + 1 end
  w(string.format("%s  %s  (%s)", ok and "PASS" or "FAIL", name, detail))
end
local function state(tag)
  return string.format("%s: hour %d, bit %d, tinted colours %d, time of day %d, cb2 %08X", tag, hour(), bit(), tinted(),
    emu:read8(0x0203C000), cb2())
end
local steps, at = {}, 0
local function step(wait, fn) at = at + wait; steps[#steps + 1] = {at, fn} end
local function keys(str)                             -- one key every 30 frames
  for i = 1, #str do
    local k = ({U = K.UP, D = K.DOWN, L = K.LEFT, R = K.RIGHT, A = K.A, B = K.B, S = K.START})[str:sub(i, i)]
    step(30, function() tap(k) end)
  end
end
step(5, function() sethour(23) end)
step(40, function() run({0x39, 0, 17, 0xFF, 10, 0, 7, 0, 0x02}) end)          -- Route 102
step(300, function() w(state("1 on, 23h")); shot("dn_1_on_23h")
  check("23:00, On: the screen is tinted", tinted() > 100 and emu:read8(0x0203C000) == 5, "tinted " .. tinted()) end)
step(5, function() setbit(1) end)
step(10, function() w(state("2 off by hand")); shot("dn_2_off_23h")
  check("the bit set: no tint, time of day unchanged", tinted() == 0 and emu:read8(0x0203C000) == 5, "tinted " .. tinted()) end)
step(5, function() setbit(0) end)
step(10, function() w(state("3 on again"))
  check("the bit cleared: tinted again", tinted() > 100, "tinted " .. tinted()) end)
keys("SDDDDDDA")                                                               -- START, Option
step(120, function() OPTION_CB2 = cb2(); w(state("4 option menu")); shot("dn_4_menu") end)
keys("DDDDDD")
step(30, function() shot("dn_5_row7") end)
keys("R")
step(30, function() w(state("5 right")); shot("dn_6_off")
  check("RIGHT on the 7th row sets the bit", bit() == 1, "bit " .. bit()) end)
keys("A")
step(60, function() check("A on the 7th row does not leave the menu", cb2() == OPTION_CB2, string.format("cb2 %08X", cb2())) end)
keys("U")
step(30, function() shot("dn_7_row6") end)
keys("B")
step(120, function() check("B leaves the menu", cb2() ~= OPTION_CB2, string.format("cb2 %08X", cb2())) end)
keys("B")
step(90, function() w(state("6 field, off")); shot("dn_8_field_off")
  check("after the menu: Off kept, no tint on the field", bit() == 1 and tinted() == 0 and cb2() == OVERWORLD, "tinted " .. tinted()) end)
keys("SA")                                                                     -- the start menu remembers Option
step(120, function() shot("dn_9_menu_off") end)
keys("DDDDDDL")
step(30, function() w(state("7 left")); shot("dn_10_on")
  check("LEFT sets it back to On", bit() == 0, "bit " .. bit()) end)
keys("B")
step(120, function() end)
keys("B")
step(90, function() w(state("8 field, on")); shot("dn_11_field_on")
  check("On again: the night tint is back at once", tinted() > 100 and cb2() == OVERWORLD, "tinted " .. tinted()) end)
step(5, function() sethour(12) end)
step(40, function() run({0x39, 0, 17, 0xFF, 10, 0, 7, 0, 0x02}) end)          -- the game reads the clock on a map load
step(300, function() w(state("9 noon")); shot("dn_12_noon")
  check("12:00, On: no tint", tinted() == 0 and emu:read8(0x0203C000) == 2, "tinted " .. tinted()) end)
step(10, function() w(fails == 0 and "ALL PASS" or (fails .. " FAILED")); done() end)
local t0, idx = nil, 1
function TEST(f)
  t0 = t0 or f
  local d = f - t0
  while idx <= #steps and d >= steps[idx][1] do steps[idx][2](); idx = idx + 1 end
end
