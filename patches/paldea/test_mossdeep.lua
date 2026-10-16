-- Mossdeep City as the game has it (test 16): the way into Area Zero is there now, and the user asked "make sure
-- everything in Mosdeep will work exactly the same since it has various event". Run on the build and on the Gen 9
-- test build without Area Zero (the control), from the same save; mossdeep16.ps1 compares the two logs, with
-- our objects (30-34) left out. STEPS_KIND (the environment):
--   space    the Space Center's people shown (0x1AD set: Mossdeep's ON_TRANSITION clears their hide flag 0x411F)
--   nospace  0x1AD clear (they are hidden, object 19 taken off)
--   before   Team Rainbow Rocket not beaten yet (no Jacq, no hole: nothing of ours)
--   save     a save made standing in Mossdeep, Continue; a save made surfing off its north shore, Continue
-- At every stop: who of Mossdeep's own is on the map and where, and the flags its scripts use.
local kind = os.getenv("STEPS_KIND") or "space"
local FL = {0x64, 0x65, 0x66, 0x67, 0x88A, 0x1AD, 0x314, 0x337, 0x4016, 0x4067, 0x40B4, 0x411E, 0x411F, 0x42B6}
local SAVE = {
  {"menutop"},
  {"press", "START", 90},
  {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15},
  {"press", "A", 60}, {"mash", "save", 6},
  {"reset"}, {"boot"},
}
local function add(list, more)
  for _, s in ipairs(more) do list[#list + 1] = s end
  return list
end
local function visit(list, label, x, y)
  return add(list, {{"warp", 0, 6, x, y}, {"flags", table.unpack(FL)}, {"shot", label}, {"avatar", label}})
end
local function tour(list)
  visit(list, "by_the_center", 28, 17)                       -- the Pokemon Center's door (warp 2)
  visit(list, "space_center", 64, 19)                         -- below the Space Center's door (warp 8)
  visit(list, "the_strip", 66, 31)                            -- the top of the stairs down to Jacq and the hole
  add(list, {{"walk", 68, 33, "on", "down_the_stairs"}, {"shot", "on_the_strip"}, {"avatar", "on_the_strip"},
             {"walk", 66, 31, "on", "back_up"}, {"flags", table.unpack(FL)}})
  visit(list, "the_gym_side", 36, 25)                         -- by warp 9
  return list
end

if kind == "before" then
  STEPS = tour({{"setup", clear = {0x41D5}, stage = 0}})
elseif kind == "nospace" then
  STEPS = tour({{"setup", set = {0x41D5}, clear = {0x1AD}, stage = 0}})
elseif kind == "save" then
  STEPS = {{"setup", set = {0x41D5, 0x1AD}, stage = 0}}
  visit(STEPS, "before_saving", 66, 31)
  add(STEPS, {{"face", "LEFT"}})
  add(STEPS, SAVE)
  add(STEPS, {{"flags", table.unpack(FL)}, {"shot", "continued"}, {"avatar", "continued"},
              {"walk", 68, 33, "on", "after_continue"}, {"shot", "on_the_strip"}})
  -- surfing: onto the water off the north shore, a save there, Continue
  add(STEPS, {{"warp", 0, 6, 20, 4}, {"face", "UP"}, {"a"}, {"mash", "surf", 6}, {"avatar", "surfing"}})
  add(STEPS, SAVE)
  add(STEPS, {{"avatar", "continued_surfing"}, {"flags", table.unpack(FL)}, {"shot", "continued_surfing"},
              {"step", "DOWN", 1}, {"avatar", "back_on_land"}})
else
  STEPS = tour({{"setup", set = {0x41D5, 0x1AD}, stage = 0}})
end
add(STEPS, {{"finish"}})
