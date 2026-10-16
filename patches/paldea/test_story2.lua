-- The story, part 2: the future. Nemona (a battle), the Titan Iron Treads, Arven's sandwich for Miraidon, Station
-- 3's log on the knoll. Starts where part 1 ends (its flags set).
STEPS = {
  {"setup", fresh = true, set = {0x41D5, 0x43AC, 0x43AD, 0x43B1, 0x43B2, 0x43B3, 0x43B5, 0x43B8, 0x43B9}, stage = 2},
  {"warp", 35, 91, 26, 31},                                    -- in front of the dais's time crystal
  {"shot", "future_arrive"},
  {"walk", 36, 28, "on", "to_nemona"}, {"face", "UP"}, {"shot", "nemona"}, {"a"}, {"fight", "nemona", 35091},
  {"flags", 0x43B7},
  {"walk", 8, 35, "on", "to_titan"}, {"face", "UP"}, {"shot", "titan"}, {"a"}, {"fight", "titan_future", 35091},
  {"flags", 0x43B4, 0x43D3},
  {"walk", 37, 43, "act", "to_arven"}, {"face_to", 37, 43}, {"a"}, {"fight", "sandwich", 35091},
  {"flags", 0x43B6},
  {"shot", "miraidon_up"},
  {"walk", 42, 36, "on", "to_s3"}, {"step", "UP", 1}, {"mash", "into_s3", 35097},
  {"walk", 1, 4, "on", "recorder3"}, {"face", "UP"}, {"a"}, {"mash", "log3", 35097},
  {"walk", 9, 8, "on", "s3_exit"}, {"step", "DOWN", 1}, {"mash", "s3_out", 35091},
  {"flags", 0x43BA},
  {"finish"},
}
