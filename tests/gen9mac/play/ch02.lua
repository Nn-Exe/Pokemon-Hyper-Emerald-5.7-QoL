-- Chapter 2: the rival on Route 103, back to the lab for the Pokedex (0x0861)
return {
  {"walk", 6, 12, map = "1.4"}, {"press", "DOWN", 1, 20}, {"wait", 200},   -- out of the lab
  {"edge", "up"},                                                         -- Littleroot -> Route 101
  {"edge", "up"},                                                         -- Route 101 -> Oldale Town
  {"edge", "up"},                                                         -- Oldale -> Route 103
  {"walk", 18, 18}, {"grind", 11, 120000},                                -- train in Route 103's grass first
  {"heal"},                                                               -- (Oldale's Pokemon Center)
  {"talk", 2}, {"expectvar", 0x4084, 4, 6000},                            -- the rival: the battle
  {"settle"},
  {"edge", "down"}, {"edge", "down"}, {"edge", "down"},                   -- back to Littleroot
  {"walk", 6, 16, map = "0.9"}, {"wait", 300},                             -- the lab's door
  {"expect", 0x0861, 8000}, {"settle"}, {"shot", "pokedex"},
  {"save"},
}
