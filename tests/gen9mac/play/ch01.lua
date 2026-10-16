return {
  {"walk", 3, 2}, {"expectvar", 0x4092, 1, 3000},
  {"walk", 4, 2}, {"wait", 40}, {"press", "RIGHT", 1, 24},   -- out of the truck (an arrow warp: push toward it)
  {"wait", 1800},                                             -- Mom walks you into the house
  {"walk", 8, 2}, {"wait", 300},                              -- the stairs
  {"walk", 5, 2}, {"face", "up"}, {"press", "A", 1},          -- the wall clock (and the difficulty)
  {"expect", 0x0051, 6000}, {"wait", 600}, {"shot", "clockdone"},
  {"walk", 7, 1, map = "1.1"}, {"wait", 600},                 -- downstairs: Dad on TV
  {"expectvar", 0x4092, 7, 3000}, {"wait", 600}, {"shot", "tv"},
  {"walk", 8, 8, map = "1.0"}, {"press", "DOWN", 1, 20}, {"wait", 300}, {"shot", "outside"},
  {"walk", 14, 8}, {"wait", 600}, {"shot", "neighbour"},
  {"wait", 600},
  {"walk", 2, 2, map = "1.2"}, {"wait", 300},
  {"talk", 16}, {"wait", 1500}, {"shot", "rival"},          -- the Poke Ball on her floor: the rival comes in
  {"walk", 1, 1, map = "1.3"}, {"wait", 200},                -- downstairs
  {"walk", 2, 8, map = "1.2"}, {"press", "DOWN", 1, 20}, {"wait", 300},   -- out
  {"walk", 11, 1, map = "0.9"}, {"wait", 600}, {"shot", "north"},
  {"press", "UP", 1, 40}, {"wait", 400}, {"shot", "route101"},
  {"expectvar", 0x4060, 2, 3000},
  {"talk", 3}, {"expect", 0x0860, 12000}, {"wait", 600}, {"shot", "starter"},  -- Birch's bag: a starter, the battle
  {"wait", 3000}, {"shot", "after"},
  {"settle"}, {"save"},
}
