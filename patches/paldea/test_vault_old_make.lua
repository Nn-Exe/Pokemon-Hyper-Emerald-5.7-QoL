-- Run on a build from before the Sealed Vault (test 14): a save in the Crystal Cavern after the story, standing
-- below its second mouth, with Ting-Lu, Chi-Yu and Wo-Chien still in the cavern and a crystal on the tile in
-- front of the mouth. test_vault_old_load.lua continues from it on the build with the vault.
local DONE = {0x41D5, 0x43AC, 0x43AD, 0x43B1, 0x43B2, 0x43B3, 0x43B4, 0x43B5, 0x43B6, 0x43B7, 0x43B8, 0x43B9,
              0x43BA, 0x43BB, 0x43BC, 0x43BD, 0x43BE, 0x43C0, 0x43C1}
STEPS = {
  {"setup", fresh = true, set = DONE, stage = 4},
  {"warp", 35, 94, 15, 4},
  {"expect", "as_it_was", map = 35094, pos = {15, 4}},
  {"shot", "before_saving"},
  {"menutop"},
  {"press", "START", 90},
  {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15},
  {"press", "A", 60}, {"mash", "save", 35094},
  {"finish"},
}
