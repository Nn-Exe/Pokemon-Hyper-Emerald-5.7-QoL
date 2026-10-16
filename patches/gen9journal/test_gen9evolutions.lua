-- The Quest Log's Evolutions chapter built again with Gen 9 (gen9journal), on the whole build, from a copy of the
-- user's newest save. A steps file of patches/paldea/test_paldea.lua (its run.ps1:
-- -Steps ..\gen9journal\test_gen9evolutions.lua). Pictures of the families that changed or came new, first with
-- the save's own Pokedex marks (unseen ones are shadows), then with every Gen 9 number seen; the list's last row.
local function cat(...)
  local out = {}
  for _, l in ipairs({...}) do for _, s in ipairs(l) do out[#out + 1] = s end end
  return out
end
local OPEN = {{"journal"}, {"press", "SEL", 30}, {"press", "UP", 90}, {"press", "A", 240}}
local CLOSE = {{"press", "B", 40}, {"press", "B", 40}, {"press", "B", 60}}
-- list rows (gen9journal's order): Mankey, Tauros, Wooper, Girafarig, Dunsparce, Pawniard, Applin, Duraludon,
-- Sprigatito, Charcadet, Greavard, Frigibax, Poltchageist, Ogerpon (the last)
local ROWS = {{20, "mankey"}, {53, "tauros"}, {85, "wooper"}, {88, "girafarig"}, {90, "dunsparce"},
              {257, "pawniard"}, {345, "applin"}, {361, "duraludon"}, {368, "sprigatito"}, {379, "charcadet"},
              {394, "greavard"}, {396, "frigibax"}, {398, "poltchageist"}, {399, "ogerpon"}}
local function tour(tag, rows)
  local s = cat(OPEN, {{"press", "B", 40}, {"qcard", 8}, {"press", "A", 120}, {"shot", tag .. "_top"}})
  for _, r in ipairs(rows) do
    s = cat(s, {{"evosel", r[1]}, {"press", "DOWN", 60}, {"shot", string.format("%s_%03d_%s", tag, r[1], r[2])}})
  end
  -- the last row, and Down there does nothing
  s = cat(s, {{"evosel", 399}, {"press", "DOWN", 60}, {"press", "DOWN", 60}, {"shot", tag .. "_end"}})
  return cat(s, CLOSE)
end
local GEN9 = {}
for d = 906, 1025 do GEN9[#GEN9 + 1] = d end
STEPS = cat(
  {{"boot"}},
  OPEN, {{"qlog", "first"}}, CLOSE,                    -- (the first opening moves the save's marks: gen9dex)
  tour("save", ROWS),
  {{"dex9", seen = cat(GEN9, {56, 57, 128, 194, 195, 203, 206, 624, 625, 840, 841, 842, 884})}},
  tour("seen", {{20, "mankey"}, {85, "wooper"}, {257, "pawniard"}, {345, "applin"}, {368, "sprigatito"},
                {379, "charcadet"}, {399, "ogerpon"}}),
  {{"finish"}})
