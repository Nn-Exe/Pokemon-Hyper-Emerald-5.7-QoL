-- Not a test: a second save for the user's look at test 11, made from their own (run on a COPY of it). Their own
-- save has the story finished, and what test 11 changed about the lab's door and the ending can only be seen
-- before that. Here everything before the finale is done but Nemona, and Penny has unlocked the lab: you stand
-- below the Zero Lab's shut door in the future. Beat Nemona (in the tall grass south of the waterfall's pond) and
-- she and Arven go to the door, which opens; then the finale and the ending. The Repel counter is left alone.
-- The story's flags are set fresh, so whatever was caught after the story on the user's save is there again.
local BEFORE = {0x41D5, 0x43AC, 0x43AD, 0x43B1, 0x43B2, 0x43B3, 0x43B4, 0x43B5, 0x43B6, 0x43B8, 0x43B9, 0x43BA,
                0x43BB, 0x43BC, 0x43D2, 0x43D3}              -- all but Nemona (0x43B7); nobody sent to the door
STEPS = {
  {"setup", fresh = true, repel = false, set = BEFORE, stage = 2},
  {"warp", 35, 91, 44, 16},
  {"expect", "shut", map = 35091, pos = {44, 16}, on = {0x43BC}, off = {0x43B7, 0x43BD}, gone = {22, 23}},
  {"shot", "at_the_door"},
  {"menutop"},
  {"press", "START", 90},
  {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15},
  {"shot", "menu_save"},
  {"press", "A", 60}, {"mash", "save", 35091},
  {"reset"}, {"boot"},
  {"shot", "continued"},
  {"expect", "after_continue", map = 35091, pos = {44, 16}, stage = 2, on = {0x43BC}, off = {0x43B7, 0x43BD},
   gone = {22, 23}},
  {"finish"},
}
