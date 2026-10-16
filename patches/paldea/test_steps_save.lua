-- Saving inside a new map (the crater in the past), then Continue from the title screen.
STEPS = {
  {"setup", set = {0x41D5, 0x43AC}, stage = 2},
  {"warp", 35, 90, 45, 21},
  {"press", "START", 90},
  {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15},
  {"shot", "menu_save"},
  {"press", "A", 60}, {"mash", "save", 35090},
  {"reset"}, {"boot"},
  {"shot", "continued"},
  {"walk", 45, 21, "on", "stand"}, {"face", "UP"}, {"a"}, {"mash", "ripple_after_load", 35091},
  {"finish"},
}
