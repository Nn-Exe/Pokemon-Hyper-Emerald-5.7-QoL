-- Quest Log Badges: clear the last three Sinnoh badge flags so both states show, open the grid, move to
-- the Badges card and open the badge case; move the frame, back to the grid with B. Screenshots badges_grid*.png, case_*.png. Run next to game.gba/game.sav with DIR set.
NAME = "questlog_badges"
DIR = DIR or "./"
dofile(DIR .. "../dexnavchain/test_boot.lua")
local SCRIPT = 0x0203F100
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1)
  emu:write8(0x03000E38, 0)
end
local plan, t0 = {}, nil
local function at(d, fn) plan[#plan + 1] = {d, fn} end
at(0, function()
  local sb1 = emu:read32(0x03005D8C)
  emu:write16(sb1 + 0x496, 363)
  emu:write16(sb1 + 0x9C2, 0); emu:write16(sb1 + 0x9C4, 0); emu:write16(sb1 + 0x9C6, 0)
  run({0x2A, 0xD2, 0x42, 0x2A, 0xD3, 0x42, 0x2A, 0xD4, 0x42, 0x02})   -- clearflag Mine, Icicle, Beacon
end)
local t = 60
local function key(k, wait) at(t, function() tap(k) end); t = t + (wait or 30) end
local function snap(n) at(t, function() shot(n); w(n .. string.format(" cb2 %08X", cb2())) end); t = t + 10 end
key(K.SEL, 50); key(K.UP, 170)
for i = 1, 7 do key(K.RIGHT, 20) end            -- the grid cursor stops on the last card: Badges
snap("badges_grid")
key(K.A, 60); snap("case_coal")                  -- the case, the frame on the Coal Badge
key(K.DOWN); snap("case_relic")
key(K.RIGHT); snap("case_mine")                  -- the Mine Badge: cleared, a silhouette
key(K.RIGHT); key(K.RIGHT); snap("case_beacon")
key(K.UP); snap("case_fen")
key(K.B, 60); snap("badges_grid2")
key(K.B, 200)
at(t, function() done() end)
function TEST(f)
  t0 = t0 or f
  for _, p in ipairs(plan) do if f - t0 == p[1] then p[2]() end end
end
