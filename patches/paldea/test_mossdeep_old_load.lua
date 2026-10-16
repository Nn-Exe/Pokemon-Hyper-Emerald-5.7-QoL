-- Continue on test 16 from test_mossdeep_old_make.lua's save (made in Mossdeep on test 15). The save's copy of
-- Mossdeep has its own 29 objects and nothing of ours; its stamp (story.FRESH) is another build's, so Mossdeep is
-- read again where you stand: Jacq and the hole are there, and the way in works.
STEPS = {
  {"shot", "continued"},
  {"avatar", "continued"},
  {"expect", "jacq_and_the_hole_now", map = 6, pos = {66, 31}, here = {30, 31}, gone = {32, 33, 34}},
  {"walk", 68, 33, "on", "to_hole"}, {"face", "UP"}, {"a"}, {"mash", "hole_first", 6},
  {"walk", 70, 32, "act", "to_jacq"}, {"face_to", 70, 32}, {"a"}, {"mash", "jacq", 6},
  {"walk", 68, 33, "on", "to_hole2"}, {"face", "UP"}, {"a"}, {"mash", "hole", 35089},
  {"expect", "on_the_wall", map = 35089},
  {"finish"},
}
