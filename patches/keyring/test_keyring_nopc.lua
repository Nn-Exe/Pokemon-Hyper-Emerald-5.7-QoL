-- The key-item ring has no PC in Rainbow Castle, Allearth Forest, Giant Chasm, Spear Pillar, the Distortion World
-- and Mt. Silver. Registers up to four key items, then on Route 102 (control) and on one map of each area (warped to
-- its warp 0): SELECT (shot: the centre crossed out or not), A, wait (shot), B, and logs the map section, whether the
-- ring was still up after A (sprites in use), and that the palettes and lock came back. On Route 102 A must open the
-- PC (logged off with B). Screenshots nopc_*.png; the log keyring_nopc_log.txt.
NAME = "keyring_nopc"
dofile((DIR or "./") .. "../dexnavchain/test_boot.lua")
local SCRIPT = 0x0203F100
local function sb1() return emu:read32(0x03005D8C) end
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1); emu:write8(0x03000E38, 0)
end
local function palstate()
  local t = {}
  for i = 0, 15 do t[#t + 1] = emu:read16(0x03000CF0 + 2 * i) end
  for i = 0, 255 do t[#t + 1] = emu:read16(0x02037914 + 2 * i); t[#t + 1] = emu:read16(0x02037D14 + 2 * i) end
  return table.concat(t, ",")
end
local function sprites_in_use()
  local n = 0
  for i = 0, 63 do if emu:read8(0x02020630 + 0x44 * i + 0x3E) & 1 == 1 then n = n + 1 end end
  return n
end
local function state(tag)
  local s = sb1()
  w(string.format("%-24s map %d/%d mapsec %d cb2 %08X lock %d sprites %d", tag, emu:read8(s + 4), emu:read8(s + 5),
    emu:read8(0x02037318 + 0x14), cb2(), lock(), sprites_in_use()))
end
local t0, plan, d = nil, {}, 10
local function step(gap, fn) d = d + gap; plan[#plan + 1] = {d, fn} end
local before, spr0, spr_open

step(0, function()
  local key = emu:read32(0x02039DD8 + 4 * 8)
  local cap = emu:read8(0x02039DD8 + 4 * 8 + 4)
  local want = {[259] = 1, [272] = 1, [262] = 1, [263] = 1, [264] = 1, [261] = 1, [363] = 1, [260] = 1, [360] = 1}
  local items, offs = {}, {0x496, 0x9C2, 0x9C4, 0x9C6}
  for i = 0, cap - 1 do
    local it = emu:read16(key + 4 * i)
    if want[it] and #items < 4 then items[#items + 1] = it end
  end
  for i = 1, 4 do emu:write16(sb1() + offs[i], items[i] or 0) end
  w("registered " .. table.concat(items, ", "))
end)
local places = {{"route102", 0, 17, 0xFF, 10, 7, false}, {"rainbow_castle", 34, 82, 0}, {"allearth_forest", 34, 35, 0},
  {"giant_chasm", 34, 9, 0}, {"spear_pillar", 35, 11, 0}, {"distortion_world", 34, 13, 0}, {"mt_silver", 34, 53, 0}}
for _, p in ipairs(places) do
  local name = p[1]
  step(20, function() run({0x39, p[2], p[3], p[4], p[5] or 0, 0, p[6] or 0, 0, 0x02}) end)
  step(420, function() state(name .. " arrived") end)
  step(10, function() before = palstate(); spr0 = sprites_in_use(); tap(K.SEL) end)
  step(40, function() spr_open = sprites_in_use(); state(name .. " ring"); shot("nopc_" .. name) end)
  step(10, function() tap(K.A) end)
  step(90, function()
    state(name .. " after A")
    w(string.format("  ring still up after A: %s", tostring(sprites_in_use() == spr_open and spr_open > spr0)))
    shot("nopc_" .. name .. "_a")
  end)
  for k = 1, 6 do step(40, function() tap(K.B) end) end         -- closes the ring, or logs off the PC
  step(120, function()
    state(name .. " closed")
    w(string.format("  palettes restored: %s, sprites back: %s, lock %d", tostring(palstate() == before),
      tostring(sprites_in_use() == spr0), lock()))
  end)
end
step(30, function() done() end)

function TEST(f)
  t0 = t0 or f
  for _, p in ipairs(plan) do if f - t0 == p[1] then p[2]() end end
end
