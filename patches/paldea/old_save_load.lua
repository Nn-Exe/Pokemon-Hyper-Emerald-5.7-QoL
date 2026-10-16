-- Continue, on this build, from a save old_save_make.lua made on test 10 (STEPS_KIND as there).
--   woods   the save's copy of the woods held Jacq, the hole and the students: the woods are read again and
--           are the game's own (since test 16 the way in is in Mossdeep City)
--   shrine  the old Sealed Shrine still loads, empty; its way out leads to the wall
--   under   the Underdepths still load (35/100), Terapagos there
--   loop    (a save from test 11) the Crystal Cavern lets you out again
local kind = os.getenv("STEPS_KIND") or "woods"
if kind == "woods" then
  STEPS = {
    {"shot", "continued"},
    {"expect", "nothing_of_ours", map = 34067, on = {0x43C2}, gone = {9, 10, 11, 12, 13}},
    {"walk", 20, 13, "on", "west"}, {"shot", "west_of_the_hole"},
    {"walk", 28, 13, "on", "east"}, {"shot", "east_of_the_hole"},
    {"expect", "still_nothing", gone = {9, 10, 11, 12, 13}},
    {"finish"},
  }
elseif kind == "shrine" then
  STEPS = {
    {"shot", "continued"},
    {"expect", "in_the_shrine", map = 35099},
    {"walk", 8, 6, "on", "to_plaque"}, {"face", "UP"}, {"a"}, {"mash", "plaque", 35099},
    {"walk", 8, 12, "on", "to_exit"}, {"step", "DOWN", 1}, {"mash", "out", 35089},
    {"shot", "on_the_wall"},
    {"walk", 14, 14, "on", "up_the_wall"},
    {"finish"},
  }
elseif kind == "loop" then
  -- the save's way out of the cavern leads to the cavern's ladder; this build's cavern says where it leads again
  -- (the past: a save from test 11 does not know which crater it came from)
  STEPS = {
    {"shot", "continued"},
    {"expect", "in_the_cavern", map = 35094},
    {"walk", 3, 2, "on", "to_mouth"}, {"step", "UP", 1}, {"mash", "out", 0},
    {"expect", "out_in_the_crater", map = 35090, pos = {6, 15}},
    {"shot", "outside"},
    {"step", "UP", 1}, {"mash", "in_again", 35094},
    {"walk", 3, 2, "on", "to_mouth2"}, {"step", "UP", 1}, {"mash", "out2", 0},
    {"expect", "out_again", map = 35090, pos = {6, 15}},
    {"finish"},
  }
else
  STEPS = {
    {"shot", "continued"},
    {"expect", "in_the_underdepths", map = 35100, here = {1}},
    {"walk", 12, 16, "on", "to_terapagos"}, {"face", "UP"}, {"shot", "terapagos"},
    {"walk", 12, 20, "on", "to_exit"},
    {"finish"},
  }
end
