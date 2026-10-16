-- Continue from test_refresh_make.lua's save. STEPS_KIND (the environment):
--   moved  on a build whose placements moved Arven and Koraidon, took one crystal away and added two: the save
--          holds the map as it was, so the map is read again (story.FRESH) and everything stands where the new
--          placements put it, you where you saved; Arven still answers
--   same   on the build the save was made on: nothing is read again, everything where it was
local kind = os.getenv("STEPS_KIND") or "moved"
if kind == "moved" then
  STEPS = {
    {"shot", "continued"},
    {"expect", "read_again", map = 35090, pos = {36, 41}, stage = 2,
     at = {{20, 38, 44}, {21, 41, 42}, {13, 46, 38}}, nowhere = {{36, 39}, {37, 43}, {39, 42}}},
    {"walk", 38, 44, "act", "to_arven"}, {"face_to", 38, 44}, {"a"}, {"mash", "arven", 35090},
    {"shot", "after_arven"},
    {"walk", 41, 42, "act", "to_koraidon"}, {"face_to", 41, 42}, {"a"}, {"mash", "koraidon", 35090},
    {"expect", "still_there", at = {{20, 38, 44}, {21, 41, 42}}},
    {"finish"},
  }
else
  STEPS = {
    {"shot", "continued"},
    {"expect", "as_saved", map = 35090, pos = {36, 41}, stage = 2,
     at = {{19, 37, 43}, {20, 39, 42}, {13, 36, 39}, {14, 46, 38}}},
    {"walk", 37, 43, "act", "to_arven"}, {"face_to", 37, 43}, {"a"}, {"mash", "arven", 35090},
    {"finish"},
  }
end
