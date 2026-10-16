-- Continue from test_vault_ice_make.lua's save (on the ice of another build's vault). The stamp differs, so the
-- vault is read again: you are put back on the tile you stood on (story.FRESH: a warp to it), and from there the
-- game may slide you on the way you face. Wherever that leaves you, it is a place the puzzle can be played on
-- from: the way out is walked to (the walker slides) and taken.
STEPS = {
  {"shot", "continued"},
  {"expect", "read_again", map = 35101, stage = 4},
  {"walk", 9, 16, "on", "to_the_door"}, {"step", "DOWN", 1}, {"mash", "out", 35094},
  {"expect", "out", map = 35094},
  {"finish"},
}
