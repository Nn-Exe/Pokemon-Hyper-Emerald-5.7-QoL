-- Pictures of the two things test 11 drew wrongly: you below the Zero Lab's shut door (your head was behind the
-- shutter), and a station's recorder (its reels were behind the counter's top), also with you below it.
STEPS = {
  {"setup", fresh = true, set = {0x41D5, 0x43AC, 0x43AD, 0x43B1, 0x43B2, 0x43B3, 0x43B4, 0x43B5, 0x43B6,
                                 0x43B8, 0x43B9, 0x43BA, 0x43BB, 0x43BC}, stage = 2},          -- all but Nemona
  {"warp", 35, 90, 44, 16},
  {"walk", 44, 15, "on", "to_door"}, {"face", "UP"}, {"shot", "below_the_shut_door"},
  {"warp", 35, 91, 44, 16},
  {"walk", 44, 15, "on", "to_door_future"}, {"face", "UP"}, {"shot", "below_the_shut_door_future"},
  {"warp", 35, 92, 8, 6},
  {"walk", 3, 4, "on", "beside"}, {"shot", "recorder"},
  {"walk", 1, 4, "on", "below"}, {"face", "UP"}, {"shot", "below_the_recorder"},
  {"a"}, {"mash", "log", 35092},
  {"warp", 35, 97, 8, 6},
  {"walk", 3, 4, "on", "beside3"}, {"shot", "recorder_station3"},
  {"finish"},
}
