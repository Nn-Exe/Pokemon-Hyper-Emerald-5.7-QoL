-- Continue from test_tiles_make.lua's save on tiles19's build (tiles taken from Koga's Village, Fortree City and
-- Lavaridge Town painted into the crater). The save holds the tiles round you as they were: the terrace's grass.
-- The build's stamp differs, so the map is read again (story.FRESH) and the taken tiles are there: the thatched
-- house's door right above you (26,27) and its roof (24,24). Then a walk along the terrace, a look at the corner
-- of Fortree and the hot spring in the north-west, and the same in the future, where the same tiles stand.
STEPS = {
  {"shot", "continued"},
  {"expect", "read_again", map = 35090, pos = {26, 28}, blocks = {{26, 27, 0x069B}, {24, 24, 0x0690}}},
  {"walk", 29, 28, "on", "along_the_terrace"}, {"expect", "walked", pos = {29, 28}},
  {"shot", "walked"},
  {"warp", 35, 90, 13, 8},
  {"expect", "north_west", map = 35090, blocks = {{16, 2, 0x32E1}, {12, 4, 0x02B1}, {10, 3, 0x16AC}}},
  {"warp", 35, 91, 26, 28},
  {"expect", "future", map = 35091, blocks = {{26, 27, 0x069B}, {16, 2, 0x32E1}, {12, 4, 0x02B1}}},
  {"shot", "future"},
  {"finish"},
}
