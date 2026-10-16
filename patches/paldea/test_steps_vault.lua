-- The Sealed Vault (test 15). The user: "for the tinglu, chiyu, wochien, can we new room for them and have a puzzle
-- to solve to obtain them at around 15,1 ? cave entrace?" The Crystal Cavern's second mouth (15,1) leads into a
-- vault whose floor is slid on; Wo-Chien, Ting-Lu and Chi-Yu stand in niches behind crystals, and a crystal
-- bursts when its stake, out on the floor, is pulled. The way out (9,16) is in the bottom wall beside the middle
-- column (8), which is clear from the strip along the bottom (y 15) up to the floor below the niches (y 5).
-- STEPS_KIND (the environment):
--   shut    before the story is done a crystal stands in the mouth: nobody gets in, and it says why
--   open    after the story: in by the mouth, the tablet, the Sword's slat and a crystal read; down the middle
--           column holding Down all the while: you stay in the room (the first build had the way out at the
--           column's foot, and you left by it); the three stakes pulled in whatever order they can be reached
--           (the walker slides: walk.lua), each crystal gone with its stake; Wo-Chien walked up to and battled
--           (knocked out: gone for good since test 18); out by the door into the cavern, in again, a save inside the vault and
--           Continue from it
--   caught  the same on a save in which Ting-Lu was caught where it stood before (its flag is set): its niche is
--           empty, its stake and crystal still stand and still go
--   ice     a save made standing on the ice against a boulder: Continue leaves you there, and you slide on from it
local kind = os.getenv("STEPS_KIND") or "open"
local MID = {0x41D5, 0x43AC, 0x43AD, 0x43B1, 0x43B2}
local DONE = {0x41D5, 0x43AC, 0x43AD, 0x43B1, 0x43B2, 0x43B3, 0x43B4, 0x43B5, 0x43B6, 0x43B7, 0x43B8, 0x43B9,
              0x43BA, 0x43BB, 0x43BC, 0x43BD, 0x43BE, 0x43C0, 0x43C1}
local SEALS = {0x43D8, 0x43D9, 0x43DA}                      -- Wo-Chien's, Ting-Lu's, Chi-Yu's
local VAULT, CAVERN = 35101, 35094
local SAVE = {
  {"menutop"},
  {"press", "START", 90},
  {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15},
  {"press", "A", 60}, {"mash", "save", VAULT},
  {"reset"}, {"boot"},
}
local function with(list, more)
  local out = {}
  for _, s in ipairs(list) do out[#out + 1] = s end
  for _, s in ipairs(more) do out[#out + 1] = s end
  return out
end
local IN = {                                                -- in by the cavern's second mouth, up to the niches
  {"warp", 35, 94, 15, 3},
  {"step", "UP", 2}, {"mash", "into_the_vault", VAULT},
  {"expect", "at_the_door", map = VAULT, pos = {9, 16}},
  {"slide", "UP", 9, 15}, {"slide", "LEFT", 8, 15}, {"slide", "UP", 8, 5},
}
if kind == "shut" then
  STEPS = {
    {"setup", fresh = true, set = MID, stage = 2},
    {"warp", 35, 94, 15, 3}, {"shot", "the_mouth_shut"},
    {"expect", "a_crystal_in_it", map = CAVERN, here = {8}},
    {"step", "UP", 3},
    {"expect", "no_way_in", map = CAVERN, pos = {15, 2}},
    {"face", "UP"}, {"a"}, {"mash", "the_crystal", CAVERN}, {"shot", "the_crystal_read"},
    {"expect", "still_outside", map = CAVERN, pos = {15, 2}, off = SEALS},
    {"finish"},
  }
elseif kind == "ice" then
  STEPS = with({{"setup", fresh = true, set = DONE, stage = 4}}, IN)
  STEPS = with(STEPS, {
    {"walk", 2, 5, "on", "to_the_left"},
    {"slide", "DOWN", 2, 8}, {"slide", "DOWN", 2, 12},     -- onto the patch of snow, then against the boulder
    {"shot", "on_the_ice"},
  })
  STEPS = with(STEPS, SAVE)
  STEPS = with(STEPS, {
    {"expect", "still_on_the_ice", map = VAULT, pos = {2, 12}},
    {"shot", "continued_on_the_ice"},
    {"slide", "DOWN", 2, 12},                               -- the boulder: you only face it
    {"slide", "RIGHT", 9, 12},                              -- along the row to the patch in the middle
    {"finish"},
  })
else
  local set = {table.unpack(DONE)}
  if kind == "caught" then set[#set + 1] = 0x43CF end       -- Ting-Lu caught on an older build
  STEPS = {
    {"setup", fresh = true, set = set, stage = 4},
    {"warp", 35, 94, 15, 3}, {"shot", "the_mouth_open"},
    {"expect", "no_crystal_in_it", map = CAVERN, gone = {8}},
    {"step", "UP", 2}, {"mash", "into_the_vault", VAULT},
    {"expect", "at_the_door", map = VAULT, pos = {9, 16}, off = SEALS, here = {3, 5, 7}},
    {"shot", "at_the_door"},
    {"slide", "UP", 9, 15}, {"slide", "LEFT", 8, 15}, {"slide", "UP", 8, 5}, {"shot", "on_the_dais"},
    {"expect", "sealed", here = kind == "caught" and {1, 2, 4, 6, 8, 9, 11} or {1, 2, 4, 6, 8, 9, 10, 11},
     gone = kind == "caught" and {10} or {}},
    {"hold", "DOWN", 150},                                  -- all the way down, Down held: still in the room
    {"expect", "not_carried_out", map = VAULT, pos = {8, 15}},
    {"slide", "UP", 8, 5},
    {"walk", 8, 3, "on", "to_the_tablet"}, {"face", "UP"}, {"a"}, {"mash", "tablet", VAULT},
    {"walk", 5, 3, "on", "to_the_sword"}, {"face", "UP"}, {"a"}, {"mash", "sword", VAULT},
    {"walk", 2, 5, "on", "to_a_crystal"}, {"face", "UP"}, {"a"}, {"mash", "crystal", VAULT}, {"shot", "a_crystal_read"},
    {"expect", "nothing_done_yet", off = SEALS, pos = {2, 5}},
    {"pull", {3, 5, 7}, "stakes", VAULT},
    {"expect", "every_seal_gone", map = VAULT, on = SEALS, gone = {3, 4, 5, 6, 7, 8}},
    {"shot", "all_pulled"},
    {"walk", 2, 3, "on", "to_wo_chien"}, {"face", "UP"}, {"shot", "wo_chien"}, {"a"}, {"fight", "wo_chien", VAULT},
    {"expect", "wo_chien_gone", gone = {9}, on = {0x43CD}, pos = {2, 3}},
    {"walk", 14, 3, "on", "to_chi_yu"}, {"face", "UP"}, {"shot", "chi_yu"},
    {"walk", 11, 3, "on", "to_ting_lu"}, {"face", "UP"}, {"shot", "ting_lu"},
    {"walk", 9, 16, "on", "to_the_door"}, {"step", "DOWN", 1}, {"mash", "out", CAVERN},
    {"expect", "in_the_cavern", map = CAVERN}, {"shot", "back_in_the_cavern"},
    {"walk", 15, 2, "on", "to_the_mouth"}, {"step", "UP", 1}, {"mash", "in_again", VAULT},
    {"expect", "in_again", map = VAULT, pos = {9, 16}, on = SEALS},
    {"slide", "UP", 9, 15}, {"slide", "LEFT", 8, 15}, {"slide", "UP", 8, 5},
  }
  STEPS = with(STEPS, SAVE)
  STEPS = with(STEPS, {
    {"expect", "continued_in_the_vault", map = VAULT, pos = {8, 5}, on = SEALS, gone = {3, 4, 5, 6, 7, 8}},
    {"shot", "continued"},
    {"slide", "DOWN", 8, 15}, {"slide", "RIGHT", 9, 15}, {"step", "DOWN", 2}, {"mash", "out_again", CAVERN},
    {"expect", "out_again", map = CAVERN},
    {"finish"},
  })
end
