-- The crater with tiles taken from other maps (tiles.py), in the game itself: warp beside each spot (LOOK_AT =
-- "x,y" or several, "x,y/x,y/..."), a picture in the past and in the future of each. The pictures are to be
-- looked at: a wrong colour or a wrong picture cell shows there and nowhere else.
STEPS = {{"setup", fresh = true, set = {0x41D5, 0x43AC, 0x43AD, 0x43B1}, stage = 2}}
local k = 0
for x, y in (os.getenv("LOOK_AT") or "26,29"):gmatch("(%d+),(%d+)") do
  k = k + 1
  STEPS[#STEPS + 1] = {"warp", 35, 90, tonumber(x), tonumber(y)}
  STEPS[#STEPS + 1] = {"shot", "past" .. k}
  STEPS[#STEPS + 1] = {"warp", 35, 91, tonumber(x), tonumber(y)}
  STEPS[#STEPS + 1] = {"shot", "future" .. k}
end
STEPS[#STEPS + 1] = {"finish"}
