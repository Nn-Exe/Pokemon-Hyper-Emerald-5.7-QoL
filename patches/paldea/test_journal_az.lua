-- Area Zero in the Journal / Quest Log (test 17, journal_az.py). The user: "update the journey game log as optional
-- quest, so player knows what to do next", and "update the legendary checkbox as well". Run on the build and on the
-- Gen 9 build without Area Zero (journal17.ps1 compares the logs): stage by stage through Area Zero's story, the
-- Quest Log opened from the field (SELECT, then UP), the current objective and every Journal row's status logged
-- (qlog). The rows of the main story must read as on the build without Area Zero; Area Zero's rows (61-67 on the
-- build, after "Steven is waiting") are "???" (4) until their step opens, Active (2) while open, Done (1). STEPS_KIND "shots": pictures of
-- the Post-game list round Area Zero's rows and of a group row's detail, and of the Legends chapter's end.
local kind = os.getenv("STEPS_KIND") or "stages"
local AZ = {0x43AC, 0x43AD, 0x43B1, 0x43B2, 0x43B3, 0x43B4, 0x43B5, 0x43B6, 0x43B7, 0x43B8, 0x43B9, 0x43BA,
            0x43BB, 0x43BC, 0x43BD, 0x43C1, 0x43C3, 0x43C4, 0x43C5, 0x43C6, 0x43C7, 0x43C8, 0x43C9, 0x43CA, 0x43CB,
            0x43CC, 0x43CD, 0x43CE, 0x43CF, 0x43D0, 0x43D1}
local CAUGHT = {0x43C3, 0x43C4, 0x43C5, 0x43C6, 0x43C7, 0x43C8, 0x43C9, 0x43CA, 0x43CB, 0x43CC, 0x43CD, 0x43CE,
                0x43CF, 0x43D0, 0x43D1}
local GEN9_DEX = {921, 922, 923, 924, 925, 926, 927, 928, 929, 930, 935, 936, 937, 938, 939}   -- Area Zero's 15
local function with(list, more)
  local out = {}
  for _, s in ipairs(list) do out[#out + 1] = s end
  for _, s in ipairs(more) do out[#out + 1] = s end
  return out
end
local OPEN = {{"journal"}, {"press", "SEL", 30}, {"press", "UP", 90}, {"press", "A", 240}}
local CLOSE = {{"press", "B", 30}, {"press", "B", 30}, {"press", "B", 60}}
local function stage(name, set, rr, dex)
  -- every Area Zero flag cleared, then this stage's set; Team Rainbow Rocket beaten or not; the fifteen's Dex bits
  -- (setup sets before it clears: two steps)
  local s = {{"setup", clear = with(AZ, rr and {} or {0x41D5}), stage = 0},
             {"setup", set = with(set, rr and {0x41D5} or {})},
             {"dex", clear = GEN9_DEX}, {"dex", caught = dex or {}}}
  s = with(s, OPEN)
  s = with(s, {{"qlog", name}})
  return with(s, CLOSE)
end
local MID = {0x43AC, 0x43B1, 0x43B2, 0x43B3, 0x43B5, 0x43B7, 0x43B8, 0x43B9}
local DOOR = {0x43AC, 0x43B1, 0x43B2, 0x43B3, 0x43B4, 0x43B5, 0x43B6, 0x43B7, 0x43B8, 0x43B9, 0x43BA, 0x43BB,
              0x43BC, 0x43BD}
local DONE = with(DOOR, {0x43C1})
-- every flag of the Journal's steps after "Storm the castle" (steps.py, steps 60 on): cleared, the story stands
-- just after Team Rainbow Rocket, and its current objective is "Return to Steven's Island", which Area Zero must
-- not take from it
local LATER = {0x005C, 0x08E0, 0x4060, 0x4081, 0x40F0, 0x40FE, 0x40FF, 0x4100, 0x4101, 0x4102, 0x4103, 0x4104,
               0x4105, 0x4106, 0x4107, 0x4108, 0x4109, 0x410B, 0x410C, 0x410E, 0x4117, 0x412D, 0x42AC, 0x42CD,
               0x42CE, 0x42CF, 0x42D0, 0x42D1, 0x42D2, 0x42D3, 0x42D4, 0x42D5, 0x42D8, 0x42F1, 0x42FB, 0x4313,
               0x4315, 0x4316, 0x4318, 0x4319, 0x431A, 0x431B, 0x431E, 0x4322, 0x4323, 0x4325}
local function press(key, n, wait)
  local out = {}
  for _ = 1, n do out[#out + 1] = {"press", key, wait or 12} end
  return out
end
if kind == "user" then
  -- the save as it is (the user's own): the Quest Log opened once, every row logged, a picture of where it opens
  STEPS = with(with(OPEN, {{"qlog", "user"}, {"shot", "user_list"}}), CLOSE)
  STEPS = with(STEPS, {{"finish"}})
  return
end
if kind == "midgame" then
  local function mid(name, set, extra)
    local s = {{"setup", clear = LATER}}
    s = with(s, stage(name, set, true))
    if extra then
      table.remove(s, #s); table.remove(s, #s); table.remove(s, #s)      -- (CLOSE comes after the pictures)
      s = with(s, extra)
      s = with(s, CLOSE)
    end
    return s
  end
  STEPS = {}
  STEPS = with(STEPS, mid("mid_rr", {}, {{"shot", "rr_list"}}))
  -- the list opens on the current objective (Steven, the row before Area Zero's seven): down to the sandwiches
  STEPS = with(STEPS, mid("mid_penny", {0x43AC, 0x43B1, 0x43B2, 0x43B3}, with(with(
    {{"shot", "penny_list"}}, press("DOWN", 3)),
    {{"press", "A", 10}, {"shot", "penny_sandwiches_panel"}, {"press", "A", 40}, {"shot", "penny_sandwiches_detail"},
     {"press", "B", 30}})))
  STEPS = with(STEPS, mid("mid_finale", DONE, with(with(
    {{"shot", "finale_list"}}, press("DOWN", 7)),
    {{"press", "A", 40}, {"shot", "finale_legends_detail"}, {"press", "B", 30}})))
  -- the Legends chapter: B to the grid, down to the Legends card, in, to the end of the list
  STEPS = with(STEPS, {{"setup", clear = LATER}})
  STEPS = with(STEPS, stage("mid_legends", with(DONE, {0x43C3, 0x43C4, 0x43CD}), true, {927, 928, 921}))
  table.remove(STEPS, #STEPS); table.remove(STEPS, #STEPS); table.remove(STEPS, #STEPS)
  STEPS = with(STEPS, {{"press", "B", 40}, {"press", "DOWN", 30}, {"press", "A", 60}, {"shot", "legends_top"}})
  STEPS = with(STEPS, press("DOWN", 110, 8))
  STEPS = with(STEPS, {{"shot", "legends_end"}, {"press", "A", 40},
                       {"shot", "legends_end_detail"}, {"press", "B", 30}})
  STEPS = with(STEPS, CLOSE)
  STEPS = with(STEPS, {{"finish"}})
  return
end
STEPS = {}
STEPS = with(STEPS, stage("before", {}, false))
STEPS = with(STEPS, stage("rr", {}, true))
STEPS = with(STEPS, stage("jacq", {0x43AC}, true))
STEPS = with(STEPS, stage("penny", {0x43AC, 0x43B1}, true))
STEPS = with(STEPS, stage("middle", MID, true))
STEPS = with(STEPS, stage("door", DOOR, true))
STEPS = with(STEPS, stage("finale", DONE, true))
STEPS = with(STEPS, stage("some_caught", with(DONE, {0x43C3, 0x43C4, 0x43CD}), true, {927, 928, 921}))
STEPS = with(STEPS, stage("all_caught", with(DONE, CAUGHT), true, GEN9_DEX))
STEPS = with(STEPS, {{"finish"}})
