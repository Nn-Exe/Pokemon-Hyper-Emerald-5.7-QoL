-- Side Content: the Snivy row by its two flags, and the Burning Soul's portrait. STATE (env):
--   start  = 0x045D set, 0x41B0 clear (a new game: Snivy hidden)       -> Snivy "To do"
--   league = 0x045D clear, 0x41B0 set (after Ever Grande's guard)      -> Snivy "To do"
--   done   = both set (after the battle)                               -> Snivy "Done"
-- Screenshots snivy_<STATE>.png and burning_soul.png. Run next to game.gba/game.sav with DIR set.
NAME = "questlog_snivy"
DIR = DIR or "./"
dofile(DIR .. "../dexnavchain/test_boot.lua")
local STATE = os.getenv("STATE") or "start"
local SNIVY, BURNING = tonumber(os.getenv("SNIVY_ROW") or "18"), tonumber(os.getenv("BURNING_ROW") or "38")
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
local SET = {start = {0x29, 0x2A}, league = {0x2A, 0x29}, done = {0x29, 0x29}}   -- ops for 0x045D, 0x41B0
local plan, t0 = {}, nil
local function at(d, fn) plan[#plan + 1] = {d, fn} end
at(0, function()
  local sb1 = emu:read32(0x03005D8C)
  emu:write16(sb1 + 0x496, 363)
  emu:write16(sb1 + 0x9C2, 0); emu:write16(sb1 + 0x9C4, 0); emu:write16(sb1 + 0x9C6, 0)
  local op = SET[STATE]
  run({op[1], 0x5D, 0x04, op[2], 0xB0, 0x41, 0x02})
end)
-- the panel test's way in: SELECT, the grid, A opens the current chapter (Sinnoh on the test save), R x4 -> Side
local seq = {{60, K.SEL}, {110, K.UP}, {280, K.A}, {320, K.R}, {350, K.R}, {380, K.R}, {410, K.R}}
for _, x in ipairs(seq) do at(x[1], function() tap(x[2]) end) end
local t = 460
local function down(n) for i = 1, n do at(t, function() tap(K.DOWN) end); t = t + 25 end end
down(SNIVY)
at(t + 20, function() shot("snivy_" .. STATE) end); t = t + 30
down(BURNING - SNIVY)
at(t + 20, function() shot("burning_soul") end); t = t + 30
at(t + 10, function() done() end)
function TEST(f)
  t0 = t0 or f
  for _, p in ipairs(plan) do if f - t0 == p[1] then p[2]() end end
end
