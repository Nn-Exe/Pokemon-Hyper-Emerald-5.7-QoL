-- Quest Log, Key Items chapter: open from SELECT, R three times to Key Items, screenshot every screenful
-- (key_NN.png) down all 55 rows, then A on the first row. Run next to game.gba/game.sav with DIR set.
NAME = "questlog_keyitems"
DIR = DIR or "./"
dofile(DIR .. "../dexnavchain/test_boot.lua")
local plan, t0 = {}, nil
local function at(d, fn) plan[#plan + 1] = {d, fn} end
at(0, function()
  local sb1 = emu:read32(0x03005D8C)
  emu:write16(sb1 + 0x496, 363)
  emu:write16(sb1 + 0x9C2, 0); emu:write16(sb1 + 0x9C4, 0); emu:write16(sb1 + 0x9C6, 0)
end)
at(10, function() tap(K.SEL) end)
at(60, function() tap(K.UP) end)
at(220, function() w(string.format("cb2 %08X", cb2())); tap(K.R) end)
at(260, function() tap(K.R) end)
at(280, function() tap(K.R) end)
at(320, function() shot("key_00") end)
local t = 330
for s = 1, 7 do
  for i = 1, 8 do at(t, function() tap(K.DOWN) end); t = t + 12 end
  at(t + 10, function() shot(string.format("key_%02d", s)) end); t = t + 20
end
-- back to the top, open a row with A
for i = 1, 60 do at(t, function() tap(K.UP) end); t = t + 8 end
at(t + 10, function() tap(K.A) end)
at(t + 60, function() shot("key_detail_top") end)
at(t + 70, function() tap(K.B) end)
at(t + 110, function() done() end)
function TEST(f)
  t0 = t0 or f
  for _, p in ipairs(plan) do if f - t0 == p[1] then p[2]() end end
end
