-- Continue from test_ground_make.lua's save on the build with the painted ground. A save holds the tiles round
-- you as they were (the map as you see it is saved with it); the build's stamp differs, so the map is read
-- again (story.FRESH) and the new boulder is there, beside you.
STEPS = {
  {"shot", "continued"},
  {"expect", "read_again", map = 35090, pos = {35, 41}, blocks = {{36, 40, 0x34E0}, {41, 8, 0x3001}}},
  {"walk", 37, 39, "on", "round_the_boulder"}, {"expect", "round", pos = {37, 39}},
  {"finish"},
}
