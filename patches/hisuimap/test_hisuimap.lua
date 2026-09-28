-- Hisui on the Sinnoh Map: warp into Hisui with a script from EWRAM, open the map screen, hop the marker
-- around the six places, press A on one and check we land on that map, then show Mingyao's menu. Screenshots hm_*.png, log
-- hisuimap_log.txt. Set DIR (where game.gba/game.sav and the output go) and HERE (this folder).
--   WARP  = start map number (default 106, Coronet Highlands); GROUP=36 WARP=3 is Oreburgh, in Sinnoh
--   HOPS  = D-pad letters to press on the map (default "U,U,L,D,R,R" = Temple, Snowfall, Deertrack,
--           Prelude, Coronet, Firespit)
--   CB2   = the screen's cb2_init, as hisuimap_patch.py prints it; the map is opened by setting it directly
--   BAG=1 = open it the real way instead: START, Bag, Key Items, Sinnoh Map, Use
--   FLY=0 = press B at the end instead of A
--   GROUP = the start map's group (default 37)
NAME = "hisuimap"
DIR = DIR or "./"
HERE = HERE or DIR
dofile(HERE .. "../dexnavchain/test_boot.lua")
local SCRIPT = 0x0203F100
local GROUP = tonumber(os.getenv("GROUP") or "37")
local WARP = tonumber(os.getenv("WARP") or "106")
local HOPS = os.getenv("HOPS") or "U,U,L,D,R,R"
local CB2 = tonumber(os.getenv("CB2") or "0x08FF3141")
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1)
  emu:write8(0x03000E38, 0)
end
local function where()
  local sb1 = emu:read32(0x03005D8C)
  return string.format("map %d/%d pos (%d,%d) cb2 %08X", emu:read8(sb1 + 4), emu:read8(sb1 + 5),
    emu:read16(sb1), emu:read16(sb1 + 2), cb2())
end
local plan, t0 = {}, nil
local function at(d, fn) plan[#plan + 1] = {d, fn} end
at(30, function() w("start: " .. where()); run({0x39, GROUP, WARP, 1, 0, 0, 0, 0, 0x02}) end)
at(400, function() w("warped: " .. where()); shot("hm_field") end)
if os.getenv("BAG") == "1" then
  -- the real way in: START, Bag, the Sinnoh Map moved to the first Key Items slot, Use
  at(405, function()
    local base = emu:read32(0x02039DD8 + 4 * 8)
    local cap = emu:read8(0x02039DD8 + 4 * 8 + 4)
    for i = 0, cap - 1 do
      if emu:read16(base + i * 4) == 361 then
        local a, b = emu:read16(base), emu:read16(base + 2)
        emu:write16(base + i * 4, a); emu:write16(base + i * 4 + 2, b)
        emu:write16(base, 361); emu:write16(base + 2, 1)
      end
    end
  end)
  at(410, function() tap(K.START) end)
  at(440, function() shot("hm_menu") end)
  at(445, function() tap(K.DOWN) end) at(465, function() tap(K.DOWN) end)
  at(485, function() tap(K.A) end)
  at(600, function() tap(K.LEFT) end)
  at(650, function() shot("hm_bag") end)
  at(660, function() tap(K.A) end)
  at(720, function() tap(K.A) end)             -- Use
else
  at(420, function()
    emu:write32(0x03005DAC, 0x080AF6D5)        -- gFieldCallback, as the item sets it
    emu:write32(0x030022C4, CB2)
  end)
end
local O = os.getenv("BAG") == "1" and 400 or 0
at(500 + O, function() w("open: " .. where()); shot("hm_open") end)
local d = 520 + O
local n = 0
for k in HOPS:gmatch("[LRUD]") do
  local key = ({L = K.LEFT, R = K.RIGHT, U = K.UP, D = K.DOWN})[k]
  n = n + 1
  local tag = n
  at(d, function() tap(key) end)
  at(d + 40, function() shot("hm_hop" .. tag .. "_" .. k) end)
  d = d + 50
end
local FLY = os.getenv("FLY") ~= "0"
if FLY then
  at(d, function() tap(K.A) end)
  for i = 1, 10 do at(d + i * 60, function() w(string.format("+%ds: %s", i, where())) end) end
  at(d + 150, function() shot("hm_flying") end)
  at(d + 160, function() tap(K.A) end)             -- Mingyao's block waits for a button on her Braviary
  at(d + 700, function() w("end: " .. where() .. " script lock " .. lock()); shot("hm_after") end)
  at(d + 710, function() run({0x6F, 0, 0, 137, 0, 0x02}) end)   -- Mingyao's own menu, multichoice 137
  at(d + 780, function() shot("hm_mingyao"); tap(K.B) end)
  at(d + 900, function() done() end)
else
  at(d, function() tap(K.B) end)
  at(d + 200, function() w("after B: " .. where()); shot("hm_back"); done() end)
end
function TEST(f)
  t0 = t0 or f
  for _, p in ipairs(plan) do if f - t0 == p[1] then p[2]() end end
end
