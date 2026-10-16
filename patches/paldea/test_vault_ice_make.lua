-- Run on a build of the vault other than the one to be tested (test 15's first, p15a: its way out was at 8,15):
-- a save made standing on the ice against a boulder (2,12). test_vault_ice_load.lua continues from it.
local DONE = {0x41D5, 0x43AC, 0x43AD, 0x43B1, 0x43B2, 0x43B3, 0x43B4, 0x43B5, 0x43B6, 0x43B7, 0x43B8, 0x43B9,
              0x43BA, 0x43BB, 0x43BC, 0x43BD, 0x43BE, 0x43C0, 0x43C1}
STEPS = {
  {"setup", fresh = true, set = DONE, stage = 4},
  {"warp", 35, 101, 8, 15},
  {"slide", "UP", 8, 5}, {"walk", 2, 5, "on", "to_the_left"},
  {"slide", "DOWN", 2, 8}, {"slide", "DOWN", 2, 12},
  {"shot", "before_saving"},
  {"menutop"},
  {"press", "START", 90},
  {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15},
  {"press", "A", 60}, {"mash", "save", 35101},
  {"finish"},
}
