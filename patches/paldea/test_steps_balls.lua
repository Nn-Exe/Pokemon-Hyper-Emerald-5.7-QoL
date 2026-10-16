-- The crater's two item balls (test 15: "have more item ball booster energy in the crater as well like 1-2
-- location"): a Booster Energy in the past (the nook on the west terrace) and one in the future (the hanging
-- valley above the waterfall). Each is picked up, is gone, and its flag is set; the other time's is not touched.
local DONE = {0x41D5, 0x43AC, 0x43AD, 0x43B1, 0x43B2, 0x43B3, 0x43B4, 0x43B5, 0x43B6, 0x43B7, 0x43B8, 0x43B9,
              0x43BA, 0x43BB, 0x43BC, 0x43BD, 0x43BE, 0x43C0, 0x43C1}
STEPS = {
  {"setup", fresh = true, set = DONE, stage = 4},
  {"warp", 35, 90, 8, 29}, {"shot", "past_ball_from_afar"},
  {"expect", "both_there", off = {0x43DC, 0x43DD}},
  {"walk", 4, 28, "act", "to_the_past_ball"}, {"face_to", 4, 28}, {"shot", "past_ball"}, {"a"}, {"mash", "past_ball", 35090},
  {"expect", "past_taken", on = {0x43DC}, off = {0x43DD}, nowhere = {{4, 28}}},
  {"warp", 35, 91, 38, 4}, {"shot", "future_ball_from_afar"},
  {"walk", 41, 5, "act", "to_the_future_ball"}, {"face_to", 41, 5}, {"shot", "future_ball"}, {"a"}, {"mash", "future_ball", 35091},
  {"expect", "future_taken", on = {0x43DC, 0x43DD}, nowhere = {{41, 5}}},
  {"warp", 35, 90, 8, 29},
  {"expect", "past_still_gone", nowhere = {{4, 28}}},
  {"finish"},
}
