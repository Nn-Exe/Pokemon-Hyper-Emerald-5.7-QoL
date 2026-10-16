-- Pictures of the crater's terraces in the game, after the story, from spots that show their corners: the mesa
-- from inside and from below, the west slope, the knoll, the pond under the falls, the lake's corner. Test 13
-- changed every terrace piece (the grass family instead of the rock one: no sand-coloured corners any more).
local DONE = {0x41D5, 0x43AC, 0x43AD, 0x43B1, 0x43B2, 0x43B3, 0x43B4, 0x43B5, 0x43B6, 0x43B7, 0x43B8, 0x43B9,
              0x43BA, 0x43BB, 0x43BC, 0x43BD, 0x43BE, 0x43C0, 0x43C1}
STEPS = {
  {"setup", fresh = true, set = DONE, stage = 4},
  {"warp", 35, 90, 26, 31}, {"shot", "mesa_inside"},
  {"warp", 35, 90, 26, 35}, {"shot", "mesa_below"},
  {"warp", 35, 90, 23, 27}, {"shot", "mesa_corner"},
  {"warp", 35, 90, 11, 35}, {"shot", "west_slope"},
  {"warp", 35, 90, 14, 21}, {"shot", "path_through_the_edge"},
  {"warp", 35, 90, 42, 38}, {"shot", "knoll_below"},
  {"warp", 35, 90, 42, 24}, {"shot", "east_terraces"},
  {"warp", 35, 90, 36, 21}, {"shot", "pond_and_path"},
  {"warp", 35, 90, 36, 46}, {"shot", "picnic"},
  {"warp", 35, 91, 26, 35}, {"shot", "mesa_below_future"},
  {"walk", 26, 34, "on", "to_the_steps"}, {"walk", 26, 31, "on", "up_the_steps"},
  {"expect", "on_the_mesa", pos = {26, 31}},
  {"finish"},
}
