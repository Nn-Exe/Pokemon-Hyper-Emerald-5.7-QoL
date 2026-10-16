-- Past the crater's edges. The user, on test 13: "increase the border of the map, cuz right now it got cut off
-- when ran on the border". The screen shows 7 tiles either side of you and 5 above and below, and the crater's
-- ground comes within 4 tiles of its sides and 3 of its top. Up to test 13 the game drew the map's 2 x 2 border
-- block there, which cannot follow a cliff on one row and a wood on the next: the cliff stopped dead against
-- trees at both ends. Now each crater has four strips joined to it (world.beyond, maps.py: connections) that go
-- on with what the map ends in.
--   1. after a warp into each crater, the tiles the game holds past each edge are the strips' (PAST_EDGE: the
--      land above the crater 0x71 and the wall's face 0x79 run on to the west and east, the woods on every side
--      are in step with the map's own: 0x1D6 0x1D7 a tree's middle, 0x1D4 0x1D5 the row two trees share);
--   2. pictures from the places nearest each edge, and on the way there (walking draws the new row or column
--      from the same tiles);
--   3. the wall, whose border was right as it was.
-- Spots are given in the map's own coordinates (EDGE_SPOTS, the environment: "group,num,x,y;...").
local DONE = {0x41D5, 0x43AC, 0x43AD, 0x43B1, 0x43B2, 0x43B3, 0x43B4, 0x43B5, 0x43B6, 0x43B7, 0x43B8, 0x43B9,
              0x43BA, 0x43BB, 0x43BC, 0x43BD, 0x43BE, 0x43C0, 0x43C1}
PAST_EDGE = {
  {-3, 9, 0x3471}, {-2, 11, 0x3479}, {-1, 12, 0x3479}, {-3, 13, 0x35EF}, {-2, 14, 0x35D6},      -- west, the cliff
  {-2, 0, 0x35D4}, {-1, 1, 0x35D7}, {-2, 6, 0x35E4},                                            -- west, the rim
  {52, 9, 0x3471}, {53, 11, 0x3479}, {54, 12, 0x3479}, {54, 14, 0x35D6},                        -- east
  {26, 0, 0x35D4}, {27, 0, 0x35D5}, {26, -1, 0x35D6}, {27, -1, 0x35D7}, {26, -2, 0x35D4}, {27, -2, 0x35D5},
  {24, 51, 0x35D4}, {24, 52, 0x35D6}, {25, 52, 0x35D7}, {24, 53, 0x35D4},                       -- south
  {-1, -1, 0x35D7}, {-2, -2, 0x35D4}, {52, -1, 0x35D6}, {-1, 52, 0x35D7}, {53, 53, 0x35D5},     -- the corners
}
local spots = os.getenv("EDGE_SPOTS") or
  "35,90,4,34;35,90,4,42;35,90,47,24;35,90,47,38;35,90,24,47;35,91,4,34;35,89,7,26;35,89,19,26;35,89,13,14"
STEPS = {
  {"setup", fresh = true, set = DONE, stage = 4},
  {"warp", 35, 90, 12, 17}, {"expect", "past_edges", map = 35090, pos = {12, 17}, blocks = PAST_EDGE},
  {"walk", 4, 16, "on", "west"}, {"expect", "west", pos = {4, 16}, blocks = PAST_EDGE}, {"shot", "west_cliff"},
  {"warp", 35, 90, 40, 17}, {"walk", 47, 15, "on", "east"}, {"expect", "east", pos = {47, 15}}, {"shot", "east_cliff"},
  {"warp", 35, 90, 38, 8}, {"walk", 40, 3, "on", "north"}, {"expect", "north", pos = {40, 3}}, {"shot", "north_east"},
  {"walk", 24, 3, "on", "along_the_top"}, {"expect", "north_west", pos = {24, 3}}, {"shot", "north_west"},
  {"warp", 35, 90, 30, 45}, {"walk", 43, 47, "on", "south"}, {"expect", "south", pos = {43, 47}}, {"shot", "south_east"},
  {"walk", 8, 47, "on", "along_the_bottom"}, {"expect", "south_west", pos = {8, 47}}, {"shot", "south_west"},
  {"warp", 35, 91, 12, 17}, {"expect", "future_edges", map = 35091, pos = {12, 17}, blocks = PAST_EDGE},
  {"walk", 4, 16, "on", "west_future"}, {"shot", "west_cliff_future"},
}
local k = 0
for g, n, x, y in spots:gmatch("(%d+),(%d+),(%d+),(%d+)") do
  k = k + 1
  STEPS[#STEPS + 1] = {"warp", tonumber(g), tonumber(n), tonumber(x), tonumber(y)}
  STEPS[#STEPS + 1] = {"shot", string.format("edge%02d_%s_%s_%s_%s", k, g, n, x, y)}
end
STEPS[#STEPS + 1] = {"finish"}
