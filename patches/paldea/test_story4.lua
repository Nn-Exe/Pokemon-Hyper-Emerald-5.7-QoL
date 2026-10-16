-- The story, part 4: Penny unlocks the lab; Arven and Nemona are at its door by themselves (everything else was
-- done already) and the door is open; the finale (AI Sada, AI Turo, the Protocol's Koraidon and Miraidon), home
-- through the hole, the ending in Mossdeep City, after which the four of them are gone from it.
STEPS = {
  {"setup", fresh = true, set = {0x41D5, 0x43AC, 0x43AD, 0x43B1, 0x43B2, 0x43B3, 0x43B4, 0x43B5, 0x43B6, 0x43B7,
                                 0x43B8, 0x43B9, 0x43BA, 0x43BB}, stage = 2},
  {"warp", 35, 92, 8, 6},
  {"walk", 8, 5, "on", "to_penny"}, {"face", "UP"}, {"a"}, {"mash", "penny_open", 35092},
  {"expect", "lab_open", on = {0x43BC}, off = {0x43BD}},
  {"face", "UP"}, {"a"}, {"mash", "penny_again", 35092},
  {"warp", 35, 90, 26, 31},
  {"expect", "sent", on = {0x43BD}, off = {0x43BE}},
  {"walk", 37, 43, "act", "picnic"}, {"shot", "picnic_without_arven"},
  {"expect", "arven_left", gone = {19}},
  {"walk", 44, 16, "on", "to_lab"}, {"shot", "guards"},
  {"expect", "guards", here = {22, 23}},
  {"walk", 43, 15, "act", "to_guard"}, {"face_to", 43, 15}, {"a"}, {"mash", "guard_arven", 35090},
  {"walk", 44, 16, "on", "to_lab2"}, {"step", "UP", 2}, {"mash", "into_lab", 35096},
  {"walk", 6, 4, "on", "to_machine"}, {"face", "UP"}, {"shot", "machine"}, {"a"}, {"fight", "finale", 6},
  {"shot", "home"},
  {"expect", "ending", on = {0x43C1, 0x43BE, 0x43C0, 0x43C2, 0x43D4}, off = {0x43C5, 0x43CD}, stage = 4,
   gone = {30, 32, 33, 34}, here = {31}},
  {"shot", "after_ending"},
  -- nobody of the ending is left in the way: every tile of the strip, then the stairs up into the city
  {"walk", 66, 33, "on", "west_end"}, {"walk", 70, 33, "on", "east_end"}, {"walk", 70, 32, "on", "where_jacq_was"},
  {"walk", 69, 33, "on", "where_arven_was"}, {"walk", 67, 33, "on", "where_penny_was"},
  {"walk", 66, 31, "on", "up_the_stairs"}, {"shot", "the_way_is_free"},
  {"finish"},
}
