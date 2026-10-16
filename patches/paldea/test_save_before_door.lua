-- Continue from make_save_before_door.lua's save (no setup) and play it to the end, as the user would: the door
-- is shut and says who is missing; Nemona's battle sends her and Arven to it and it opens; the finale; the ending
-- in Mossdeep City, after which the four of them are gone from the hole and live in the stations.
STEPS = {
  {"shot", "continued"},
  {"expect", "shut", map = 35091, pos = {44, 16}, stage = 2, on = {0x43BC}, off = {0x43B7, 0x43BD}, gone = {22, 23}},
  {"walk", 44, 15, "on", "to_door"}, {"shot", "door_shut"},
  {"step", "UP", 2},                                           -- the shutter does not let you in
  {"expect", "still_outside", map = 35091, off = {0x43BD}},
  {"face", "UP"}, {"a"}, {"mash", "door_waits", 35091},
  {"walk", 36, 28, "on", "to_nemona"}, {"face", "UP"}, {"shot", "nemona"}, {"a"}, {"fight", "nemona", 35091},
  {"expect", "sent", on = {0x43B7, 0x43BD}, off = {0x43BE}, gone = {24}},
  {"walk", 44, 16, "on", "to_lab"}, {"shot", "guards"},
  {"expect", "guards", here = {22, 23}},
  {"step", "UP", 2}, {"mash", "into_lab", 35096},
  {"walk", 6, 4, "on", "to_machine"}, {"face", "UP"}, {"a"}, {"fight", "finale", 6},
  {"expect", "ending", on = {0x43C1, 0x43BE, 0x43C0, 0x43C2, 0x43D4}, stage = 4,       -- (0x43D5, who is in the
   gone = {30, 32, 33, 34}, here = {31}},                                              -- stations, is worked out on
                                                                                      -- the way into each map)
  {"shot", "home"},
  -- (the user: "make sure that after the ending of the mission, those new npcs would not block the way out"):
  -- every tile of the strip is walked on, then the stairs up into the city
  {"walk", 66, 33, "on", "west_end"}, {"walk", 70, 33, "on", "east_end"}, {"walk", 70, 32, "on", "where_jacq_was"},
  {"walk", 69, 33, "on", "where_arven_was"}, {"walk", 67, 33, "on", "where_penny_was"},
  {"walk", 66, 31, "on", "up_the_stairs"}, {"shot", "the_way_out"},
  {"walk", 68, 33, "on", "to_hole"}, {"face", "UP"}, {"a"}, {"mash", "hole", 35089},
  {"walk", 18, 25, "on", "down"}, {"step", "DOWN", 1}, {"mash", "crater", 35090},
  {"walk", 22, 21, "on", "to_station2"}, {"step", "UP", 1}, {"mash", "station2", 35093},
  {"expect", "arven_home", here = {1}},
  {"walk", 8, 5, "on", "to_arven"}, {"face", "UP"}, {"shot", "arven"}, {"a"}, {"mash", "arven_home", 35093},
  {"finish"},
}
