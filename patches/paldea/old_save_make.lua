-- Run on test 10's ROM (not a test of this build): makes the saves an older build leaves behind, for
-- old_save_load.lua to continue from on the new one. STEPS_KIND (the environment) picks which:
--   woods   after test 10's ending, in the Timeless Woods, Jacq and the three students standing by the hole
--   shrine  inside the Sealed Shrine (35/99)
--   under   in the Underdepths (35/100)
local DONE = {0x41D5, 0x43AC, 0x43AD, 0x43B0, 0x43B1, 0x43B2, 0x43B3, 0x43B4, 0x43B5, 0x43B6, 0x43B7, 0x43B8,
              0x43B9, 0x43BA, 0x43BB, 0x43BC, 0x43BD, 0x43BE, 0x43C0, 0x43C1}
--   loop    (on test 11's ROM) in the Crystal Cavern after a trip down to the Underdepths and back, entered from
--           the future: the cavern's way out leads to its own ladder
local kind = os.getenv("STEPS_KIND") or "woods"
local at = {woods = {34, 67, 24, 13}, shrine = {35, 99, 8, 9}, under = {35, 100, 12, 18}, loop = {35, 91, 6, 16}}
STEPS = {
  {"setup", fresh = true, set = DONE, stage = 4},
  {"warp", at[kind][1], at[kind][2], at[kind][3], at[kind][4]},
}
if kind == "loop" then
  for _, s in ipairs({
    {"walk", 6, 15, "on", "to_mouth"}, {"step", "UP", 1}, {"mash", "into_cavern", 35094},
    {"walk", 6, 10, "on", "to_ladder"}, {"step", "DOWN", 1}, {"mash", "down", 35100},
    {"walk", 12, 20, "on", "to_way_up"}, {"step", "DOWN", 2}, {"mash", "up", 35094},
    {"walk", 6, 10, "on", "off_the_ladder"},
  }) do STEPS[#STEPS + 1] = s end
  at.loop = {35, 94}
end
for _, s in ipairs({
  {"shot", "before_saving"},
  {"press", "START", 90},
  {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15},
  {"shot", "menu_save"},
  {"press", "A", 60}, {"mash", "save", at[kind][1] * 1000 + at[kind][2]},
  {"finish"},
}) do STEPS[#STEPS + 1] = s end
