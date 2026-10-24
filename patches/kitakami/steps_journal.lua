-- The Quest Log's Legends with Kitakami's five counted (kjournal.py, 2026-10-17): the grid (Legends x/124), the end of
-- the Legends list (rows 120-124: Okidogi, Munkidori, Fezandipiti, Ogerpon, Pecharunt, no longer Locked), Ogerpon's
-- and Pecharunt's details; then Pecharunt (1025) and Ogerpon (1017) marked caught: their rows and the count again.
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
local CLOSE = {{"press", "B", 30}, {"press", "B", 30}, {"press", "B", 60}}
local function tour(tag)
  return cat(OPEN,
    {{"press", "B", 40}, {"shot", tag .. "_grid"}, {"qlog", tag}},
    {{"qcard", 4}, {"press", "A", 60}},
    rep("DOWN", 118), {{"press", "DOWN", 30}, {"shot", tag .. "_legends_119"}},
    rep("DOWN", 3), {{"press", "DOWN", 30}, {"shot", tag .. "_legends_123"}},
    {{"press", "DOWN", 30}, {"shot", tag .. "_legends_124"}},
    {{"press", "A", 40}, {"shot", tag .. "_pecharunt_detail"}, {"press", "B", 30}},
    {{"press", "UP", 30}, {"press", "A", 40}, {"shot", tag .. "_ogerpon_detail"}, {"press", "B", 30}},
    CLOSE)
end
STEPS = cat({{"setup"}, {"warp", 35, 106, 23, 46}, {"wait", 60}},
            {{"dex9", clear = {1014, 1015, 1016, 1017, 1025}}},
            tour("before"),
            {{"dex9", caught = {1017, 1025}}},
            tour("caught"),
            {{"finish"}})
