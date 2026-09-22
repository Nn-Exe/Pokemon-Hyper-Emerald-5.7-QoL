-- Quest Log, Side Content chapter: open from SELECT (the grid), go to Side Content, screenshot every screenful
-- (side_NN.png) down all 44 rows - the always-shiny rows carry a red star after the name - then put the
-- selection bar on Snivy (a starred row) and one row with no star. Run next to game.gba/game.sav with DIR set.
NAME = "questlog_side"
DIR = DIR or "./"
dofile(DIR .. "../dexnavchain/test_boot.lua")
local plan, t0 = {}, nil
local function at(d, fn) plan[#plan + 1] = {d, fn} end
at(0, function()
  local sb1 = emu:read32(0x03005D8C)
  emu:write16(sb1 + 0x496, 363)
  emu:write16(sb1 + 0x9C2, 0); emu:write16(sb1 + 0x9C4, 0); emu:write16(sb1 + 0x9C6, 0)
end)
local seq = {{10, K.SEL}, {60, K.UP}, {230, K.DOWN}, {260, K.LEFT}, {290, K.LEFT}, {320, K.DOWN}, {350, K.A},
             {390, nil, "side_00"}}
for _, x in ipairs(seq) do
  at(x[1], function()
    if x[2] then tap(x[2]) end
    if x[3] then shot(x[3]); w(string.format("%s cb2 %08X lock %d", x[3], cb2(), lock())) end
  end)
end
local t = 400
for s = 1, 5 do
  for i = 1, 8 do at(t, function() tap(K.DOWN) end); t = t + 12 end
  at(t + 10, function() shot(string.format("side_%02d", s)) end); t = t + 20
end
for i = 1, 50 do at(t, function() tap(K.UP) end); t = t + 8 end
for i = 1, 19 do at(t, function() tap(K.DOWN) end); t = t + 12 end        -- row 19: Snivy
at(t + 10, function() shot("side_snivy_sel") end)
at(t + 20, function() tap(K.DOWN) end)                                       -- row 20: Oshawott, no star
at(t + 40, function() shot("side_oshawott_sel") end)
at(t + 50, function() tap(K.B) end)
at(t + 90, function() tap(K.B) end)
at(t + 300, function() w(string.format("after cb2 %08X lock %d", cb2(), lock())); done() end)
function TEST(f)
  t0 = t0 or f
  for _, p in ipairs(plan) do if f - t0 == p[1] then p[2]() end end
end
