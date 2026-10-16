-- The crater, walked: down the wall into the past, the DexNav, round the valley and up the mesa and its dais to the
-- time crystal, into the future, a wild battle in each era, the north-east terrace's time crystal, then through
-- every door: the Zero Lab (its door is open: everything before the finale is done), Research Station No. 2 (the
-- cot, the note, the recording), the Crystal Cavern (its item), and back up to the wall.
STEPS = {
  {"setup", fresh = true, set = {0x41D5, 0x43AC, 0x43B5, 0x43B6, 0x43B7, 0x43BC}, stage = 2},
  {"warp", 35, 89, 14, 14},                                   -- the wall's top ledge
  {"walk", 18, 26, "on", "wall_down"},                        -- below the bottom ledge's cave mouth
  {"step", "UP", 1}, {"mash", "to_past", 35090},
  {"shot", "past"},
  {"press", "R", 150}, {"shot", "dexnav"}, {"press", "B", 150},
  {"walk", 26, 31, "on", "up_to_dais"}, {"shot", "dais"},     -- the shelf's steps, the valley, the mesa, the dais
  {"face", "UP"}, {"a"}, {"mash", "time_crystal", 35091},
  {"shot", "future"},
  {"repel", 0},
  {"walk", 7, 19, "on", "grass_f"}, {"wild", "wild_future"},
  {"repel", 250},
  {"walk", 26, 31, "on", "back_to_dais"}, {"face", "UP"}, {"a"}, {"mash", "time_back", 35090},
  {"shot", "past_again"},
  {"repel", 0},
  {"walk", 7, 19, "on", "grass_p"}, {"wild", "wild_past"},
  {"repel", 250},
  {"walk", 45, 21, "on", "ne_terrace"}, {"face", "UP"}, {"a"}, {"mash", "time_ne", 35091},
  {"shot", "future_ne"},
  {"repel", 250},
  {"walk", 44, 15, "on", "to_lab"}, {"step", "UP", 1}, {"mash", "into_lab", 35096},
  {"shot", "lab"},
  {"walk", 1, 6, "on", "lab_terminal"}, {"face", "DOWN"}, {"a"}, {"mash", "terminal", 35096},
  {"walk", 7, 14, "on", "lab_exit"}, {"step", "DOWN", 1}, {"mash", "out_of_lab", 35091},
  {"shot", "future_after_lab"},
  {"repel", 250},
  {"walk", 22, 21, "on", "to_station"}, {"step", "UP", 1}, {"mash", "into_station", 35093},
  {"shot", "station2"},
  {"walk", 10, 4, "on", "cot"}, {"face", "UP"}, {"a"}, {"mash", "rest", 35093},
  {"walk", 2, 5, "on", "table"}, {"face", "DOWN"}, {"a"}, {"mash", "note", 35093},
  {"walk", 1, 4, "on", "recorder"}, {"face", "UP"}, {"a"}, {"mash", "recording", 35093},
  {"walk", 5, 2, "on", "pc"}, {"face", "UP"}, {"a"}, {"press", "A", 120}, {"shot", "pc_menu"},  -- the game's own PC
  {"press", "B", 120}, {"press", "B", 120}, {"press", "B", 120}, {"press", "B", 120}, {"shot", "pc_closed"},
  {"walk", 9, 8, "on", "station_exit"}, {"step", "DOWN", 1}, {"mash", "out_of_station", 35091},
  {"shot", "future_after_station"},
  {"repel", 250},
  {"walk", 6, 15, "on", "to_cave"}, {"step", "UP", 1}, {"mash", "into_cavern", 35094},
  {"shot", "cavern"},
  {"walk", 8, 11, "on", "cavern_item"}, {"face", "LEFT"}, {"a"}, {"mash", "booster", 35094},
  {"shot", "cavern_end"},
  {"walk", 3, 2, "on", "cavern_exit"}, {"step", "UP", 1}, {"mash", "out_of_cavern", 35091},
  {"shot", "future_after_cavern"},
  {"repel", 250},                                             -- (the walk round has used up the last one)
  {"walk", 14, 13, "on", "to_mouth"}, {"step", "UP", 1}, {"mash", "to_wall", 35089},
  {"shot", "wall_again"},
  {"finish"},
}
