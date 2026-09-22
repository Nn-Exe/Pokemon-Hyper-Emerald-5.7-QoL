-- Quest Log, the Legends' first row "Gotta catch 'em all!": with ALL=1 every legend is first marked caught in the
-- Pokedex (both of the hack's flag arrays, SaveBlock1 +0x560 and +0x5D8, byte dex/8, bit dex%8); without it the
-- save is left as it is. Opens the grid (ac_grid), Legends (ac_top), A on row 0 (ac_detail), then scrolls to
-- the last legend (ac_last) and back to the grid (ac_grid_after).
-- Screenshots are prefixed with the mode. Run next to game.gba/game.sav with DIR set.
local ALL = os.getenv("ALL") == "1"
NAME = "questlog_allcaught_" .. (ALL and "all" or "save")
DIR = DIR or "./"
dofile(DIR .. "../dexnavchain/test_boot.lua")
local DEX = {144,145,146,150,151,243,244,245,249,250,251,377,378,379,380,381,382,383,384,385,386,480,481,482,
  483,484,485,486,487,488,489,490,491,492,493,494,638,639,640,641,642,643,644,645,646,647,648,649,716,717,718,
  719,720,721,772,773,785,786,787,788,789,790,791,792,793,794,795,796,797,798,799,800,801,802,803,804,805,807,
  808,809,888,889,890,891,892,893,894,895,896,897,898,905}
local P = ALL and "all_" or "save_"
local plan, t0 = {}, nil
local function at(d, fn) plan[#plan + 1] = {d, fn} end
at(0, function()
  local sb1 = emu:read32(0x03005D8C)
  emu:write16(sb1 + 0x496, 363)
  emu:write16(sb1 + 0x9C2, 0); emu:write16(sb1 + 0x9C4, 0); emu:write16(sb1 + 0x9C6, 0)
  if ALL then
    for _, n in ipairs(DEX) do
      for _, base in ipairs({0x560, 0x5D8}) do
        local a = sb1 + base + (n >> 3)
        emu:write8(a, emu:read8(a) | (1 << (n & 7)))
      end
    end
    w("marked " .. #DEX .. " legends caught")
  end
end)
local seq = {{10, K.SEL}, {60, K.UP}, {230, K.DOWN}, {260, K.LEFT}, {290, nil, "ac_grid"}, {300, K.A},
             {340, nil, "ac_top"}}
for _, x in ipairs(seq) do
  at(x[1], function()
    if x[2] then tap(x[2]) end
    if x[3] then shot(P .. x[3]); w(string.format("%s cb2 %08X", x[3], cb2())) end
  end)
end
at(350, function() tap(K.A) end)                                  -- row 0, selected on opening
at(400, function() shot(P .. "ac_detail") end)
at(410, function() tap(K.B) end)
local t = 450
for i = 1, 95 do at(t, function() tap(K.DOWN) end); t = t + 8 end
at(t + 20, function() shot(P .. "ac_last") end)
at(t + 30, function() tap(K.B) end)
at(t + 70, function() shot(P .. "ac_grid_after") end)
at(t + 80, function() done() end)
function TEST(f)
  t0 = t0 or f
  for _, p in ipairs(plan) do if f - t0 == p[1] then p[2]() end end
end
