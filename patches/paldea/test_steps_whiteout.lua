-- A white-out halfway through the finale leaves the cast's hide flag cleared (the flags below: everything done, the
-- cast's flag 0x43C0 clear). Coming back into the lab hides them again, so nobody stands there before the machine
-- is used, and the finale plays from the top.
STEPS = {
  {"setup", fresh = true, set = {0x41D5, 0x43AC, 0x43AD, 0x43B0, 0x43B1, 0x43B2, 0x43B3, 0x43B4, 0x43B5, 0x43B6,
                                 0x43B7, 0x43B8, 0x43B9, 0x43BA, 0x43BB, 0x43BC, 0x43BD, 0x43C2, 0x43C5}, stage = 2},
  {"warp", 35, 96, 7, 13},
  {"expect", "cast_hidden", on = {0x43C0}, gone = {1, 2, 3, 4}},
  {"shot", "lab_empty"},
  {"walk", 6, 4, "on", "to_machine"}, {"face", "UP"}, {"a"}, {"fight", "finale", 6},
  {"expect", "ending", on = {0x43C1, 0x43BE, 0x43C0, 0x43C2, 0x43D4}, off = {0x43C5}, stage = 4,
   gone = {30, 32, 33, 34}, here = {31}},
  {"finish"},
}
