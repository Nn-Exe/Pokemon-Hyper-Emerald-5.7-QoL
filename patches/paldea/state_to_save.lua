-- Not a test: turns an emulator save state into a save file. The user plays from save states and seldom saves in
-- the game, and a save state only works on the ROM it was made on (every script has moved in the next build).
-- Run on that ROM, with any save that boots; STATE_FILE (the environment) is a COPY of the state.
--   run.ps1 -Rom <the state's rom> -Steps state_to_save.lua -Extra "STATE_FILE=C:/.../copy.ss0"
-- It loads the state, saves from the Start menu, resets and continues from the new save to show that it took.
-- The .sav next to the ROM is then the state's game. The state must be at a place where Start opens the menu.
local state = os.getenv("STATE_FILE")
STEPS = {
  {"loadstate", state},
  {"shot", "state_loaded"},
  {"menutop"},
  {"press", "START", 90},
  {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15},
  {"shot", "menu_save"},
  {"press", "A", 60}, {"mash", "save", 0},
  {"shot", "saved"},
  {"reset"}, {"boot"},
  {"shot", "continued"},
  {"finish"},
}
