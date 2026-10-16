-- The story, part 3: the waterfall. Surf the pond, climb the falls (Waterfall) into the hanging valley, step off,
-- Station 4's log and note, then surf back down the falls and out of the pond.
STEPS = {
  {"setup", fresh = true, set = {0x41D5, 0x43AC, 0x43AD}, stage = 2},
  {"warp", 35, 90, 33, 20},                                    -- the pond's south shore
  {"face", "UP"}, {"a"}, {"mash", "surf", 35090},
  {"shot", "surfing"},
  {"step", "UP", 4}, {"shot", "at_the_falls"},                -- the splash
  {"face", "UP"}, {"a"}, {"mash", "waterfall", 35090},        -- up to the river at the top
  {"shot", "top"},
  {"step", "LEFT", 1}, {"step", "LEFT", 1}, {"mash", "ashore", 35090},
  {"shot", "valley"},
  {"walk", 27, 9, "on", "to_s4"}, {"step", "UP", 1}, {"mash", "into_s4", 35098},
  {"walk", 1, 4, "on", "recorder4"}, {"face", "UP"}, {"a"}, {"mash", "log4", 35098},
  {"walk", 2, 5, "on", "to_note4"}, {"face", "DOWN"}, {"a"}, {"mash", "note4", 35098},
  {"walk", 9, 8, "on", "s4_exit"}, {"step", "DOWN", 1}, {"mash", "s4_out", 35090},
  {"shot", "valley_again"},
  {"walk", 31, 9, "on", "to_river"}, {"face", "RIGHT"}, {"a"}, {"mash", "surf_top", 35090},
  {"step", "DOWN", 1}, {"step", "DOWN", 1}, {"mash", "down_the_falls", 35090},
  {"shot", "below"},
  {"step", "DOWN", 4}, {"step", "DOWN", 1}, {"mash", "ashore_below", 35090},
  {"shot", "out"},
  {"flags", 0x43BB},
  {"finish"},
}
