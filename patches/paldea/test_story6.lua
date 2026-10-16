-- The order the user played test 9 in, which left the lab's machine refusing them: Arven is talked to when only the
-- logs are missing. He must not be needed again. The door is still shut; Station 2's log (the recorder, walked);
-- up the wall to Penny, who unlocks the lab; back down, and Arven and Nemona are at the door, which is open; the
-- finale starts.
STEPS = {
  {"setup", fresh = true, set = {0x41D5, 0x43AC, 0x43AD, 0x43B1, 0x43B2, 0x43B3, 0x43B4, 0x43B5, 0x43B6, 0x43B7,
                                 0x43B8, 0x43BA, 0x43BB}, stage = 2},          -- all but Station 2's log (0x43B9)
  {"warp", 35, 90, 26, 31},
  {"walk", 37, 43, "act", "to_arven"}, {"face_to", 37, 43}, {"shot", "arven"}, {"a"},
  {"mash", "arven_before_logs", 35090},
  {"expect", "not_yet", on = {0x43BE}, off = {0x43BC, 0x43BD}, here = {19}},
  {"walk", 44, 15, "on", "to_door"}, {"face", "UP"}, {"a"}, {"mash", "door_shut", 35090},
  {"walk", 22, 21, "on", "to_s2"}, {"step", "UP", 1}, {"mash", "into_s2", 35093},
  {"shot", "station2"},
  {"walk", 1, 4, "on", "recorder2"}, {"face", "UP"}, {"shot", "at_recorder"}, {"a"}, {"mash", "log2", 35093},
  {"expect", "log2", on = {0x43B9}},
  {"walk", 9, 8, "on", "s2_exit"}, {"step", "DOWN", 1}, {"mash", "s2_out", 35090},
  {"expect", "door_not_open_yet", off = {0x43BD}},
  {"walk", 14, 13, "on", "to_mouth"}, {"step", "UP", 1}, {"mash", "to_wall", 35089},
  {"walk", 11, 20, "on", "to_s1"}, {"step", "UP", 1}, {"mash", "into_s1", 35092},
  {"walk", 8, 5, "on", "to_penny"}, {"face", "UP"}, {"a"}, {"mash", "penny_open", 35092},
  {"expect", "lab_open", on = {0x43BC}, off = {0x43BD}},
  {"walk", 9, 8, "on", "s1_exit"}, {"step", "DOWN", 1}, {"mash", "s1_out", 35089},
  {"walk", 18, 26, "on", "wall_down"}, {"step", "UP", 1}, {"mash", "to_past", 35090},
  {"expect", "sent", on = {0x43BD}, off = {0x43BE}},
  {"walk", 44, 16, "on", "to_lab"}, {"shot", "guards"},
  {"expect", "guards", here = {22, 23}},
  {"step", "UP", 2}, {"mash", "into_lab", 35096},
  {"walk", 6, 4, "on", "to_machine"}, {"face", "UP"}, {"a"}, {"fight", "finale", 6},
  {"expect", "ending", on = {0x43C1, 0x43BE, 0x43C0, 0x43C2, 0x43D4}, off = {0x43C5}, stage = 4,
   gone = {30, 32, 33, 34}, here = {31}},
  {"finish"},
}
