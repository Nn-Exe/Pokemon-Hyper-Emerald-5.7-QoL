-- Saves made on a build before this one hold the old copy of the map you saved on. KIND (the environment):
--   make_md   on the game without Kitakami (rom/): warp to Mossdeep beside the hole, save there
--   load_md   on the Kitakami build, from that save: Continue in Mossdeep, then Briar must be there (object 35)
--   load_bus  on the Kitakami build, from Kitakami test 4's save (made at Mossui's bus stop, nobody in the town):
--             Continue, then Briar and Carmine must be there
local kind = os.getenv("KIND") or "load_md"
local SAVE = {
  {"menutop"},
  {"press", "START", 90},
  {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15},
  {"press", "A", 60}, {"mash", "save", 0},
}
if kind == "make_md" then
  STEPS = {{"warp", 0, 6, 70, 33}, {"shot", "before_save"}}
  for _, s in ipairs(SAVE) do STEPS[#STEPS + 1] = s end
  STEPS[#STEPS + 1] = {"finish"}
elseif kind == "load_md" then
  STEPS = {{"wait", 120}, {"shot", "continued"}, {"expect", "briar_after_continue", map = 6, at = {{35, 70, 32}}},
           {"finish"}}
else
  STEPS = {{"wait", 120}, {"shot", "continued"},
           {"expect", "people_after_continue", map = 35106, at = {{1, 22, 46}, {2, 24, 45}}}, {"finish"}}
end
