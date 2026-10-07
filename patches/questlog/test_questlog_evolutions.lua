-- Quest Log, Evolutions: open the log with R from the Start menu, move to the Evolutions card (the cursor starts
-- on the current chapter: GRID is the way from "Artifacts"), open it and walk down the list to the families in
-- ROWS, a screenshot of each (evo_<name>.png), then B back to the field.
-- Run next to game.gba/game.sav copies with DIR set, NOT under a temp folder (mGBA stops on a "Temporary file
-- loaded" dialog there). A family's list position: python patches/questlog/evolutions.py game.gba <name>.
-- To see the pages of families the save has not met, run a copy with evo_seen's "beq" (00 D0 before 01 20 00 BD,
-- just above the Quest Log's second 0x080C0665 literal) turned into C0 46.
NAME = "questlog_evolutions"
DIR = DIR or "./"
dofile(DIR .. "../dexnavchain/test_boot.lua")
local GRID = {"DOWN", "RIGHT", "RIGHT"}
local ROWS = {{0, "001_bulbasaur"}, {1, "004_charmander"}, {12, "037_vulpix"}, {18, "052_meowth"}, {55, "133_eevee"},
              {56, "133_eevee_2"}, {65, "150_mewtwo"}, {67, "155_cyndaquil"}, {74, "172_pichu"}, {161, "386_deoxys"},
              {194, "479_rotom"}, {200, "493_arceus"}, {201, "493_arceus_2"}, {223, "550_basculin"},
              {269, "656_froakie"}, {293, "718_zygarde"}, {324, "789_cosmog"}, {360, "888_zacian"}, {361, "889_zamazenta"}, {362, "891_kubfu"}, {364, "905_enamorus"}}
local plan, t0 = {}, nil
local function at(d, fn) plan[#plan + 1] = {d, fn} end
local t = 20
local function key(k, wait) at(t, function() tap(k) end); t = t + (wait or 40) end
local function snap(n) at(t, function() shot(n); w(string.format("%s cb2 %08X", n, cb2())) end); t = t + 4 end
key(K.START, 60)
key(K.R, 160)
snap("evo_grid")
for _, k in ipairs(GRID) do key(K[k], 30) end
key(K.A, 120)
local pos = 0
for _, row in ipairs(ROWS) do
  while row[1] - pos >= 9 do key(K.R, 24); pos = pos + 9 end      -- R: a list page down
  while pos < row[1] do key(K.DOWN, 24); pos = pos + 1 end
  t = t + 30
  snap("evo_" .. row[2])
end
key(K.B, 60)
key(K.B, 200)
snap("evo_field")
at(t + 20, function() done() end)
function TEST(f)
  t0 = t0 or f
  for _, p in ipairs(plan) do if f - t0 == p[1] then p[2]() end end
end
