-- Exp. Share on/off. Set DIR (game.gba/game.sav and output) and HERE (this folder).
-- 1) share_check(182, 1) straight after boot (expect 1: on). 2) A wild Lv 2 Magikarp, won by pressing A; every
-- party member's EXP before and after. 3) The Exp. Share used from the Bag (moved to the first Key Items
-- slot): screenshot es_off.png, share_check again (expect 0). 4) The same battle again: only the Pokemon
-- that fought should gain. 5) Used again: es_on.png, share_check 1.
NAME = "expshare"
DIR = DIR or "./"
HERE = HERE or DIR
dofile(HERE .. "../dexnavchain/test_boot.lua")
local SCRIPT, STUB, OUT = 0x0203F100, 0x0203F300, 0x0203F400
local PARTY, COUNT = 0x020244EC, 0x020244E9
local STUBBYTES = {0x10,0xB5,0xB6,0x20,0x01,0x21,0x04,0x4B,0x00,0xF0,0x05,0xF8,0x03,0x49,0x08,0x60,
                   0x10,0xBC,0x01,0xBC,0x00,0x47,0x18,0x47,0x01,0x5B,0xFF,0x08,0x00,0xF4,0x03,0x02}
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1)
  emu:write8(0x03000E38, 0)
end
local function levels()
  local t = {}
  for i = 0, emu:read8(COUNT) - 1 do t[#t + 1] = tostring(emu:read8(PARTY + i * 100 + 0x54)) end
  return table.concat(t, ", ")
end
local function exps()
  local t = {}
  for i = 0, emu:read8(COUNT) - 1 do t[#t + 1] = emu:read32(PARTY + i * 100 + 0x24) end
  return t
end
local before
local function diff(tag)
  local now, s = exps(), {}
  for i, v in ipairs(now) do s[#s + 1] = string.format("%d", v - (before[i] or v)) end
  w(tag .. " EXP gained per party slot: " .. table.concat(s, ", "))
end
local function check(tag)
  run({0x23, 0x01, 0xF3, 0x03, 0x02, 0x02})
end
local plan, t0 = {}, nil
local function at(d, fn) plan[#plan + 1] = {d, fn} end
local function mash(from, to) for f = from, to, 30 do at(f, function() tap(K.A) end) end end
local function battle(t, tag)
  at(t, function() before = exps(); run({0xB6, 129, 0, 2, 0, 0, 0xB7, 0x02}) end)   -- setwildbattle Magikarp Lv2; dowildbattle
  mash(t + 200, t + 2200)
  at(t + 2300, function() diff(tag); w("  outcome " .. emu:read8(0x0202433A) .. ", cb2 " .. string.format("%08X", cb2())) end)
end
local function use_from_bag(t, shotname, pocket)
  at(t, function()
    local base = emu:read32(0x02039DD8 + 4 * 8)
    local cap = emu:read8(0x02039DD8 + 4 * 8 + 4)
    for i = 0, cap - 1 do
      if emu:read16(base + i * 4) == 182 then
        local a, b = emu:read16(base), emu:read16(base + 2)
        emu:write16(base + i * 4, a); emu:write16(base + i * 4 + 2, b)
        emu:write16(base, 182); emu:write16(base + 2, 1)
      end
    end
  end)
  at(t + 10, function() tap(K.START) end)
  if pocket then                                                   -- the Start menu keeps its cursor on Bag after that
    at(t + 40, function() tap(K.DOWN) end) at(t + 60, function() tap(K.DOWN) end)
  end
  at(t + 80, function() tap(K.A) end)
  if pocket then at(t + 210, function() tap(K.LEFT) end) end    -- the Bag remembers the pocket after that
  at(t + 250, function() shot(shotname .. "_desc") end)
  at(t + 260, function() tap(K.A) end)
  at(t + 320, function() tap(K.A) end)                                   -- Use
  at(t + 420, function() shot(shotname) end)
  at(t + 430, function() tap(K.A) end)
  for k = 0, 5 do at(t + 480 + k * 40, function() tap(K.B) end) end
end
at(30, function() for i, b in ipairs(STUBBYTES) do emu:write8(STUB + i - 1, b) end; check() end)
at(100, function() w("share_check at start: " .. emu:read32(OUT)); w("party levels: " .. levels()) end)
battle(120, "ON ")
use_from_bag(2500, "es_off", true)
at(3300, function() check() end)
at(3360, function() w("share_check after using it: " .. emu:read32(OUT)) end)
battle(3400, "OFF")
use_from_bag(5800, "es_on")
at(6600, function() check() end)
at(6660, function() w("share_check after using it again: " .. emu:read32(OUT)); done() end)
function TEST(f)
  t0 = t0 or f
  for _, p in ipairs(plan) do if f - t0 == p[1] then p[2]() end end
end
