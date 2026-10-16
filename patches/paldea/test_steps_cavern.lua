-- The Crystal Cavern and the Underdepths under it, there and back, after the story. The user, on test 11: "the
-- crystal cavern right now it is loop cannot go out". Both rooms' ways out were the game's "dynamic" warp (back
-- to wherever you came in by), and the game keeps only one such place: going down the ladder made it the ladder,
-- so the cavern's mouth then led to the cavern's own ladder for ever. Walked in from each time, down, up and
-- out: you must come out in the crater you went in from.
local DONE = {0x41D5, 0x43AC, 0x43AD, 0x43B1, 0x43B2, 0x43B3, 0x43B4, 0x43B5, 0x43B6, 0x43B7, 0x43B8, 0x43B9,
              0x43BA, 0x43BB, 0x43BC, 0x43BD, 0x43BE, 0x43C0, 0x43C1}
local function there_and_back(era, tag)
  return {
    {"warp", 35, era, 6, 16},                                  -- below the cavern's mouth
    {"walk", 6, 15, "on", "to_mouth" .. tag}, {"step", "UP", 1}, {"mash", "into_cavern" .. tag, 35094},
    {"walk", 3, 3, "on", "in" .. tag},
    {"walk", 3, 2, "on", "to_mouth_first" .. tag}, {"step", "UP", 1}, {"mash", "straight_out" .. tag, 35000 + era},
    {"expect", "straight_out" .. tag, map = 35000 + era, pos = {6, 15}},
    {"step", "UP", 1}, {"mash", "in_again" .. tag, 35094},
    {"walk", 6, 10, "on", "to_ladder" .. tag}, {"step", "DOWN", 1}, {"mash", "down" .. tag, 35100},
    {"shot", "underdepths" .. tag},
    {"walk", 12, 20, "on", "to_way_up" .. tag}, {"step", "DOWN", 2}, {"mash", "up" .. tag, 35094},
    {"expect", "at_the_ladder" .. tag, map = 35094},
    {"shot", "back_in_the_cavern" .. tag},
    {"walk", 3, 2, "on", "to_mouth_out" .. tag}, {"step", "UP", 1}, {"mash", "out" .. tag, 0},
    {"expect", "out_where_you_came_in" .. tag, map = 35000 + era, pos = {6, 15}},
    {"shot", "outside" .. tag},
  }
end
STEPS = {{"setup", fresh = true, set = DONE, stage = 4}}
for _, s in ipairs(there_and_back(91, "_future")) do STEPS[#STEPS + 1] = s end
for _, s in ipairs(there_and_back(90, "_past")) do STEPS[#STEPS + 1] = s end
STEPS[#STEPS + 1] = {"finish"}
