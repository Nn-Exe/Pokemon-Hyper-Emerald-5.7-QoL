-- Chapter 3b: train on Route 104, Rustboro, Roxanne (0x0867)
return {
  {"settle"}, {"grind", 24, 800000},  -- train in Route 104 grass
  {"edge", "up"},                                                         -- Rustboro City
  {"heal"}, {"walk", 25, 19, map = "0.3"}, {"settle"},                    -- the gym
  {"talk", 1}, {"expect", 0x0867, 20000}, {"settle"}, {"shot", "roxanne"},
  {"save"},
}
