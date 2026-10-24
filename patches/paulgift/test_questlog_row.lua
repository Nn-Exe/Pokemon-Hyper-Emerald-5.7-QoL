-- The Quest Log's Key Items row of the EV-IV Display (row 41 of 54): the list round it and its detail (A). A steps
-- file of patches/paldea/test_paldea.lua (its run.ps1: -Steps ..\paulgift\test_questlog_row.lua).
-- Expect: location "Your PC", "In your PC from the start: Item Storage, then Withdraw Item." (before: Fortree City,
-- "From Paul after your rematch in Fortree City.").
local function cat(...)
  local out = {}
  for _, l in ipairs({...}) do for _, s in ipairs(l) do out[#out + 1] = s end end
  return out
end
local function rep(key, n, wait)
  local out = {}
  for _ = 1, n do out[#out + 1] = {"press", key, wait or 14} end
  return out
end
local OPEN = {{"journal"}, {"press", "SEL", 30}, {"press", "UP", 90}, {"press", "A", 240}}
STEPS = cat(
  {{"boot"}}, OPEN,
  {{"press", "B", 40}, {"shot", "grid"}, {"qcard", 5}, {"press", "A", 60}, {"shot", "keys_top"}},
  rep("DOWN", 40), {{"press", "DOWN", 30}, {"shot", "keys_41"}},
  {{"press", "A", 40}, {"shot", "eviv_detail"}, {"press", "B", 30}},
  {{"press", "B", 30}, {"press", "B", 30}, {"press", "B", 60}},
  {{"finish"}})
