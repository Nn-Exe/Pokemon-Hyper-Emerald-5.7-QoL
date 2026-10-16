-- The lab's door and the machine, for saves older builds could leave behind:
--  1. everything is done but nobody has been sent to the door (flags as test 9 left them when it was stuck), and
--     you are already standing in the crater: reading the shut door opens it;
--  2. you are inside the lab with something still missing (test 10 let you in): the machine says what, and the
--     story does not start.
STEPS = {
  {"setup", fresh = true, set = {0x41D5, 0x43AC, 0x43AD, 0x43B1, 0x43B2, 0x43B3, 0x43B4, 0x43B5, 0x43B6,
                                 0x43B8, 0x43B9, 0x43BA, 0x43BB, 0x43BC}, stage = 2},          -- all but Nemona
  {"warp", 35, 90, 44, 16},
  {"expect", "shut", off = {0x43BD}, gone = {22, 23}},
  {"shot", "door_shut"},
  {"setup", set = {0x43B7}},                                   -- ...and now Nemona too, with no map change
  {"walk", 44, 15, "on", "to_door"}, {"face", "UP"}, {"a"}, {"mash", "door_opens", 35090},
  {"expect", "opened", on = {0x43BD}, off = {0x43BE}, map = 35090},
  {"shot", "door_open"},
  {"step", "UP", 1}, {"mash", "into_lab", 35096},
  {"setup", fresh = true, set = {0x41D5, 0x43AC, 0x43AD, 0x43B1, 0x43B2, 0x43B3, 0x43B5, 0x43B7,
                                 0x43B8, 0x43B9, 0x43BA, 0x43BB, 0x43BC}, stage = 2},          -- Miraidon still weak
  {"warp", 35, 96, 7, 13},
  {"walk", 6, 4, "on", "to_machine"}, {"face", "UP"}, {"a"}, {"mash", "machine_not_ready", 35096},
  {"expect", "not_started", off = {0x43C1, 0x43BD}, map = 35096},
  {"finish"},
}
