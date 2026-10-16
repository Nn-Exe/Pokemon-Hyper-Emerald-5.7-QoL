-- Arven's sandwich last (the lab open, Nemona beaten, Koraidon well, the future's herb found): the talk that feeds
-- Miraidon goes straight on to "let's finish this", and he and Nemona leave for the door.
STEPS = {
  {"setup", fresh = true, set = {0x41D5, 0x43AC, 0x43AD, 0x43B1, 0x43B2, 0x43B3, 0x43B4, 0x43B5, 0x43B7,
                                 0x43B8, 0x43B9, 0x43BA, 0x43BB, 0x43BC}, stage = 2},   -- all but Miraidon (0x43B6)
  {"warp", 35, 91, 26, 31},
  {"expect", "not_sent", on = {0x43BE}, off = {0x43BD}},
  {"walk", 39, 43, "on", "to_miraidon"}, {"face", "UP"}, {"shot", "miraidon_weak"}, {"a"},
  {"mash", "miraidon_weak", 35091},
  {"walk", 37, 43, "act", "to_arven"}, {"face_to", 37, 43}, {"a"}, {"fight", "sandwich_go", 35091},
  {"expect", "sent", on = {0x43B6, 0x43BD}, off = {0x43BE}, gone = {19}},
  {"shot", "arven_gone"},
  {"walk", 39, 43, "on", "to_miraidon2"}, {"face", "UP"}, {"a"}, {"mash", "miraidon_up", 35091},
  {"walk", 44, 16, "on", "to_lab"}, {"shot", "guards"},
  {"expect", "guards", here = {22, 23}},
  {"finish"},
}
