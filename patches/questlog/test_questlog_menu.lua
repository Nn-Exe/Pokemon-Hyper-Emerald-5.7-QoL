-- Quest Log from the Start menu: the "[R] Journal" box shows with the menu, R opens the Quest Log, B comes back
-- to the menu, the box goes when the menu closes and returns after the Pokedex. Logs the box's scratch word
-- (magic + window id) at each step and screenshots m*_*.png. Run next to game.gba/game.sav with DIR set.
NAME = "questlog_menu"
DIR = DIR or "./"
dofile(DIR .. "../dexnavchain/test_boot.lua")
local plan, t0 = {}, nil
local function at(d, fn) plan[#plan + 1] = {d, fn} end
local function st(n) shot(n); w(string.format("%s cb2 %08X lock %d magic %08X id %d", n, cb2(), lock(), emu:read32(0x02039E40), emu:read8(0x02039E44))) end
at(0, function() st("m0_field") end)
at(10, function() tap(K.START) end)
at(80, function() st("m1_menu") end)
at(90, function() tap(K.R) end)
at(250, function() st("m2_questlog") end)
at(260, function() tap(K.B) end)
at(450, function() st("m3_back_menu") end)
at(460, function() tap(K.B) end)
at(520, function() st("m4_closed") end)
at(530, function() tap(K.START) end)
at(590, function() tap(K.A) end)          -- first entry
at(800, function() st("m5_entry") end)
at(810, function() tap(K.B) end)
at(1000, function() st("m6_back") end)
at(1010, function() tap(K.START) end)
at(1060, function() st("m7_closed") end)
at(1070, function() tap(K.START) end)
at(1130, function() tap(K.R) end)
at(1300, function() tap(K.B) end)
at(1500, function() tap(K.R) end)          -- again from the reopened menu
at(1680, function() st("m8_again") end)
at(1690, function() tap(K.B) end)
at(1880, function() tap(K.B) end)
at(1950, function() st("m9_end"); done() end)
function TEST(f)
  t0 = t0 or f
  for _, p in ipairs(plan) do if f - t0 == p[1] then p[2]() end end
end
