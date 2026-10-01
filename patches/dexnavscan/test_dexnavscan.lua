-- DexNav lists what the game uses on the map. Warps to each stop, opens the DexNav with R, shoots page 1 and
-- (RIGHT) page 2, closes it. Expected (from the tables, see NOTES): Lilycove - Water Staryu, Tentacool, Wingull,
-- Fish Magikarp, Wailmer, Tentacool, Staryu, Starmie, and no Land (the Pyramid's Charmeleon line was listed
-- before); Mauville - nothing; Mossdeep - 4 Water + 6 Fish, no Land; Petalburg - unchanged (4 Water + 7 Fish);
-- Altering Cave with VAR 0x403E = 0 (the form list) and = 3 (Houndour), as GetCurrentMapWildMonHeaderId picks.
-- Screenshots dexnavscan_<stop>_p1/p2.png; the log dexnavscan_log.txt.
NAME = "dexnavscan"
dofile((DIR or "./") .. "../dexnavchain/test_boot.lua")
local SCRIPT = 0x0203F100
local function sb1() return emu:read32(0x03005D8C) end
local function setvar(v, x) emu:write16(sb1() + 0x139C + (v - 0x4000) * 2, x) end
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1)
  emu:write8(0x03000E38, 0)
end
local STOPS = {
  {"lilycove", 0, 5, 40, 20}, {"mauville", 0, 2, 20, 10}, {"mossdeep", 0, 6, 40, 20}, {"petalburg", 0, 0, 15, 15},
  {"altering0", 24, 106, 16, 12, 0}, {"altering3", 24, 106, 16, 12, 3},
}
local t0, plan = nil, {}
local function at(d, fn) plan[#plan + 1] = {d, fn} end
for i, s in ipairs(STOPS) do
  local t = 10 + (i - 1) * 1000
  at(t, function()
    if s[6] then setvar(0x403E, s[6]) end
    run({0x39, s[2], s[3], 0xFF, s[4], 0, s[5], 0, 0x02})
  end)
  at(t + 350, function()
    w(string.format("%-10s map %d/%d  cb2 %08X lock %d  var403E %d", s[1], emu:read8(sb1() + 4), emu:read8(sb1() + 5),
      cb2(), lock(), emu:read16(sb1() + 0x139C + 0x3E * 2)))
    tap(K.R)
  end)
  at(t + 600, function() shot("dexnavscan_" .. s[1] .. "_p1"); w("  dexnav cb2 " .. string.format("%08X", cb2())); tap(K.RIGHT) end)
  at(t + 680, function() shot("dexnavscan_" .. s[1] .. "_p2"); tap(K.B) end)
  at(t + 880, function() tap(K.B) end)
end
at(10 + #STOPS * 1000, function() w(string.format("end cb2 %08X lock %d", cb2(), lock())); done() end)

function TEST(f)
  t0 = t0 or f
  local d = f - t0
  for _, p in ipairs(plan) do if d == p[1] then p[2]() end end
end
