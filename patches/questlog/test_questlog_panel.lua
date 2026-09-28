-- Quest Log info panel (Unbound-style list): open from SELECT, visit every chapter type - Sinnoh, Hoenn scrolled,
-- Lost Artifacts (hidden steps), Legends (Gotta catch row, unseen, seen, caught), Key Items, Side Content - and a
-- detail, then back to the field. Screenshots pNN_*.png. Run next to game.gba/game.sav with DIR set.
NAME = "questlog_panel"
DIR = DIR or "./"
dofile(DIR .. "../dexnavchain/test_boot.lua")
local plan, t0 = {}, nil
local function at(d, fn) plan[#plan + 1] = {d, fn} end
at(0, function()
  local sb1 = emu:read32(0x03005D8C)
  emu:write16(sb1 + 0x496, 363)
  emu:write16(sb1 + 0x9C2, 0); emu:write16(sb1 + 0x9C4, 0); emu:write16(sb1 + 0x9C6, 0)
end)
local t = 10
local function key(k, wait) at(t, function() tap(k) end); t = t + (wait or 30) end
local function snap(n) at(t, function() shot(n); w(n .. string.format(" cb2 %08X", cb2())) end); t = t + 10 end
key(K.SEL, 50); key(K.UP, 170)
key(K.A, 40); snap("p01_sinnoh")                     -- Sinnoh, the current chapter
key(K.L); key(K.L); snap("p02_hoenn")                -- Hoenn (from the list: L twice)
key(K.DOWN); key(K.DOWN); key(K.DOWN); key(K.DOWN); snap("p03_hoenn_scrolled")
key(K.R); key(K.R); key(K.R); snap("p04_lost")        -- Lost Artifacts
key(K.R); snap("p05_legends_top")                     -- Legends: the Gotta catch row
key(K.DOWN); snap("p06_legend_unseen")                -- row 1
key(K.DOWN); snap("p07_legend_seen")                  -- row 2 (Zapdos: seen on this save)
key(K.DOWN); key(K.DOWN); snap("p08_legend_caught")   -- row 4 (Mewtwo)
key(K.R); snap("p09_keys")
key(K.DOWN); key(K.DOWN); snap("p10_keys_letter")
key(K.R); snap("p11_side")
key(K.A, 50); snap("p12_detail")
key(K.B); key(K.B, 60); snap("p13_grid")
key(K.B, 200); snap("p14_field")
at(t, function() done() end)
function TEST(f)
  t0 = t0 or f
  for _, p in ipairs(plan) do if f - t0 == p[1] then p[2]() end end
end
