-- A research station's door opening, frame by frame, in the past and in the future: with tiles taken from other
-- maps the craters have a secondary tileset of their own (tiles.py), and the game draws an opening door into that
-- set's last 8 picture cells with the colours of its rows. Run on the build with taken tiles and on one without:
-- the pictures must be the same (tiles19.ps1 compares them). DOOR_AT = "x,y" of the tile below the door
-- (default: Station No. 2's).
local x, y = (os.getenv("DOOR_AT") or "22,21"):match("(%d+),(%d+)")
x, y = tonumber(x), tonumber(y)
STEPS = {{"setup", fresh = true, set = {0x41D5, 0x43AC, 0x43AD, 0x43B1}, stage = 2}}
for _, e in ipairs({{"past", 90}, {"future", 91}}) do
  STEPS[#STEPS + 1] = {"warp", 35, e[2], x, y}
  STEPS[#STEPS + 1] = {"face", "UP"}
  STEPS[#STEPS + 1] = {"shot", e[1] .. "_shut"}
  STEPS[#STEPS + 1] = {"press", "UP", 6}
  for k = 1, 7 do
    STEPS[#STEPS + 1] = {"shot", e[1] .. "_" .. k}
    STEPS[#STEPS + 1] = {"press", "B", 4}
  end
  STEPS[#STEPS + 1] = {"press", "B", 240}
  STEPS[#STEPS + 1] = {"shot", e[1] .. "_inside"}
end
STEPS[#STEPS + 1] = {"finish"}
