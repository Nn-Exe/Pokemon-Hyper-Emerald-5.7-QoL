-- Nemona last. Penny unlocks the lab and says who is still missing; nobody is at the door, the door stays shut
-- and says the same; Nemona, beaten, goes to the door with Arven there and then and it is open; the finale.
STEPS = {
  {"setup", fresh = true, set = {0x41D5, 0x43AC, 0x43AD, 0x43B1, 0x43B2, 0x43B3, 0x43B4, 0x43B5, 0x43B6,
                                 0x43B8, 0x43B9, 0x43BA, 0x43BB}, stage = 2},          -- all but Nemona (0x43B7)
  {"warp", 35, 92, 8, 6},
  {"walk", 8, 5, "on", "to_penny"}, {"face", "UP"}, {"a"}, {"mash", "penny_not_yet", 35092},
  {"expect", "lab_open", on = {0x43BC}, off = {0x43BD}},
  {"face", "UP"}, {"a"}, {"mash", "penny_again", 35092},
  {"warp", 35, 91, 26, 31},
  {"expect", "not_sent", on = {0x43BE}, off = {0x43BD}},
  {"walk", 44, 15, "on", "to_door"}, {"shot", "door_shut"},
  {"expect", "no_guards", gone = {22, 23}},
  {"step", "UP", 2},                                           -- the shutter does not let you in
  {"expect", "still_outside", map = 35091, off = {0x43BD}},
  {"face", "UP"}, {"a"}, {"mash", "door_waits", 35091},
  {"expect", "still_outside2", map = 35091, off = {0x43BD, 0x43C1}},
  {"walk", 36, 28, "on", "to_nemona"}, {"face", "UP"}, {"shot", "nemona"}, {"a"}, {"fight", "nemona", 35091},
  {"expect", "sent", on = {0x43B7, 0x43BD}, off = {0x43BE}, gone = {24}},
  {"shot", "nemona_gone"},
  {"walk", 44, 16, "on", "to_lab2"}, {"shot", "guards"},
  {"expect", "guards", here = {22, 23}},
  {"step", "UP", 2}, {"mash", "into_lab", 35096},
  {"walk", 6, 4, "on", "to_machine"}, {"face", "UP"}, {"a"}, {"fight", "finale", 6},
  {"expect", "ending", on = {0x43C1, 0x43BE, 0x43C0, 0x43C2, 0x43D4}, off = {0x43C5}, stage = 4,
   gone = {30, 32, 33, 34}, here = {31}},
  {"finish"},
}
