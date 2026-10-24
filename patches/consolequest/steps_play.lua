-- Run with a copy of Area Zero's harness whose "fight" waits 200,000 frames (test_paldea.lua with 60000 -> 200000,
-- beside walk.lua and ../dexnavchain/test_boot.lua): _testrun/paldea/run.ps1 -Rom <rom> -Here <that folder> -Steps <path to this from it>
-- consolequest: a whole cartridge played through the console's own menu (HP League: 7 battles), our side pinned by
-- the harness's "fight" (9999 stats), to GAME CLEAR, the Hall of Fame, the credits and Continue: 0x416B set and
-- saved, the other three clear; each battle's foe level logged (the cartridge says both teams are forced to Lv50).
STEPS = {
  {"boot"}, {"daynight_off"},
  {"setup", set = {0x42F3, 0x4302}},
  {"flags", 0x43A4, 0x43A8, 0x43A9, 0x416B},
  {"warp", 1, 1, 3, 2}, {"wait", 60},
  {"face", "UP"}, {"press", "A", 90}, {"press", "A", 90}, {"press", "A", 90}, {"shot", "games"},
  {"press", "A", 90}, {"shot", "menu"},                    -- (the fourth box: the menu)
  {"press", "DOWN", 20}, {"press", "DOWN", 20}, {"press", "DOWN", 30}, {"shot", "hp_league"},
  {"press", "A", 90}, {"shot", "inserted"},
  {"fight", "hpleague", 0},
  {"shot", "back"},
  {"flags", 0x43A4, 0x43A8, 0x43A9, 0x416B},
  {"expect", "flag", on = {0x416B}, off = {0x43A4, 0x43A8, 0x43A9}},
  {"finish"},
}
