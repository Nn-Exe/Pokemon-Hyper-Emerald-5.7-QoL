-- Run with Area Zero's harness: _testrun/paldea/run.ps1 -Rom <rom> -Steps "../consolequest/steps_ending.lua"
-- (the ROM's .sav beside it; a save with 0x41D5 set).
-- consolequest: the console's menu, then Rainbow R.'s ending entered at its patched line (0x09882B3F: the call before
-- "GAME CLEAR"), through the Hall of Fame and the credits to the title and Continue; its flag (0x43A4) must be set and
-- saved, the other three clear. Then the Quest Log's Side Content around the new rows (44-49), with A on two of them.
-- Run on build 47 too (the control: no flag, 55 rows).
local function key_ring()                 -- SELECT opens the Quest Log (test_questlog_side.lua's way)
  local sb1 = emu:read32(0x03005D8C)
  emu:write16(sb1 + 0x496, 363)
  emu:write16(sb1 + 0x9C2, 0); emu:write16(sb1 + 0x9C4, 0); emu:write16(sb1 + 0x9C6, 0)
end
STEPS = {
  {"boot"}, {"daynight_off"},
  {"setup", set = {0x42F3, 0x4302}},                       -- Elio's three cartridges, and the passerby's
  {"flags", 0x43A4, 0x43A8, 0x43A9, 0x416B},
  {"warp", 1, 1, 3, 2}, {"wait", 60}, {"shot", "room"},
  {"face", "UP"}, {"press", "A", 90}, {"shot", "gamecube"},
  {"press", "A", 90}, {"shot", "console_a2"},
  {"press", "A", 90}, {"shot", "console_games"},
  {"press", "A", 90}, {"shot", "console_menu"},
  {"press", "B", 120}, {"shot", "menu_b"},                  -- B: the menu's 127, past the four compares: release
  {"script", {0x05, 0x3F, 0x2B, 0x88, 0x09}, 1},            -- goto 0x09882B3F
  {"rec", "gameclear", 20}, {"wait", 400}, {"recstop"},     -- (no A: the GAME CLEAR box stays up)
  {"rec", "ending", 120},
  {"fight", "ending", 0},
  {"recstop"},
  {"shot", "back"},
  {"flags", 0x43A4, 0x43A8, 0x43A9, 0x416B, 0x42F3, 0x4302},
  {"call", key_ring},
  {"press", "SEL", 60}, {"press", "UP", 170}, {"shot", "grid"}, {"qlog", "grid"},
  {"qcard", 6}, {"press", "A", 90}, {"shot", "side_top"},
  {"qlog", "side"},
}
for k = 1, 43 do STEPS[#STEPS + 1] = {"press", "DOWN", 8} end
STEPS[#STEPS + 1] = {"wait", 30}
STEPS[#STEPS + 1] = {"shot", "row43"}
for k = 44, 50 do
  STEPS[#STEPS + 1] = {"press", "DOWN", 30}
  STEPS[#STEPS + 1] = {"shot", string.format("row%d", k)}
  if k == 46 or k == 49 then
    STEPS[#STEPS + 1] = {"press", "A", 60}
    STEPS[#STEPS + 1] = {"shot", string.format("row%d_a", k)}
    STEPS[#STEPS + 1] = {"press", "B", 60}
  end
end
STEPS[#STEPS + 1] = {"press", "B", 60}
STEPS[#STEPS + 1] = {"press", "B", 90}
STEPS[#STEPS + 1] = {"shot", "closed"}
STEPS[#STEPS + 1] = {"finish"}
