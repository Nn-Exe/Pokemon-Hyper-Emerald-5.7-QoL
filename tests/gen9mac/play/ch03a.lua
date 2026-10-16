-- Chapter 3: Petalburg (Norman, Wally), Route 104, Petalburg Woods, Rustboro and Roxanne (0x0867)
return {
  {"walk", 6, 12, map = "1.4"}, {"press", "DOWN", 1, 20}, {"wait", 200},   -- out of the lab
  {"edge", "up"}, {"edge", "up"},                                         -- Route 101, Oldale
  {"edge", "left"},                                                       -- Route 102
  {"walk", 24, 2, map = "0.17"},                                          -- a Cut tree blocks the way west: the
  {"walk", 6, 20, map = "34.67"},                                         --  Timeless Woods go round it
  {"edge", "left"},                                                       -- Petalburg City
  {"settle"}, {"shot", "petalburg"},
  {"walk", 15, 8, map = "0.0"}, {"settle"},                               -- the gym: Dad
  {"talk", 1}, {"expectvar", 0x4057, 2, 8000}, {"wait", 3000}, {"settle"}, {"shot", "wally1"},
  {"expectvar", 0x4057, 3, 20000}, {"settle"},                             -- Wally's catch, back to the gym
  {"talk", 1}, {"wait", 600}, {"settle"}, {"show", 0x4057, 0x4085},
  {"walk", 4, 111, map = "8.1"}, {"press", "DOWN", 1, 20}, {"wait", 300}, {"settle"},
  {"edge", "left"},                                                       -- Route 104 (Scott stops you)
  {"settle"}, {"walk", 10, 38, map = "0.19"},                             -- Petalburg Woods, south door
  {"walk", 36, 20, map = "24.11"}, {"settle"},                            -- the Devon researcher and the Aqua grunt
  {"walk", 8, 4, map = "24.11"},                                          -- through the woods to the north door
  {"save"},
}
