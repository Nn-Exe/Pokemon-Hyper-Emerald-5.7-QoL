-- Kitakami, the people milestone (2026-10-16), played from the user's own save through test_paldea.lua's harness:
-- Briar in Mossdeep by the hole, her bus to Mossui's bus stop, everyone in the town talked to (vendors across their
-- counters, the statues read), the seven signs read, the caretaker in Kitakami Hall (one floor since 2026-10-17: no
-- bed), Grandpa, the old woman, the old couple, Briar's bus back, then a save in Mossdeep and Continue (Briar still there).
--   ..\paldea\run.ps1 -Rom k6.gba -Steps ../../../_testrun/kitakami/steps_people.lua -Timeout 900
local MD, MOSSUI = 6, 35106
local function add(list, more) for _, s in ipairs(more) do list[#list + 1] = s end return list end
local function talk(list, label, x, y, map)
  return add(list, {{"walk", x, y, "act", label}, {"face_to", x, y}, {"a"}, {"mash", label, map or MOSSUI},
                    {"shot", label .. "_after"}})
end
local function across(list, label, x, y)            -- a vendor in their stall: stand below, face up, A
  return add(list, {{"walk", x, y + 1, "on", label}, {"face", "UP"}, {"a"}, {"mash", label, MOSSUI},
                    {"shot", label .. "_after"}})
end
local function door(list, label, x, y, map)
  return add(list, {{"walk", x, y, "on", label}, {"wait", 150}, {"expect", label, map = map}, {"shot", label}})
end

STEPS = {
  {"setup"},
  {"expect", "area_zero_done", stage = 4},
  -- Mossdeep: Briar on Jacq's tile, Jacq gone
  {"warp", 0, 6, 66, 31},
  {"expect", "briar_in_mossdeep", map = MD, at = {{35, 70, 32}}, gone = {30}, off = {0x43E8}},
  {"shot", "mossdeep_briar"},
}
talk(STEPS, "briar_mossdeep", 70, 32, MOSSUI)        -- her intro, Yes: the bus to Mossui
add(STEPS, {
  {"expect", "arrived", map = MOSSUI, pos = {23, 46}, on = {0x43E9},
   here = {1, 2, 11, 12}},                          -- (9, 10 are off the screen: not loaded yet)
  {"shot", "bus_stop"},
})
talk(STEPS, "carmine", 24, 45)
across(STEPS, "vendor_mochi", 19, 44)
across(STEPS, "vendor_rice", 28, 44)
across(STEPS, "vendor_apples", 19, 39)
across(STEPS, "vendor_masks", 28, 39)
talk(STEPS, "organiser", 22, 35)
talk(STEPS, "legend_1", 9, 37)
talk(STEPS, "farmer", 14, 35)
talk(STEPS, "legend_2", 38, 37)
talk(STEPS, "mother", 33, 33)
talk(STEPS, "child", 34, 33)
talk(STEPS, "carver", 10, 32)
talk(STEPS, "kieran", 20, 30)
talk(STEPS, "sign_hall", 16, 24)
talk(STEPS, "sign_shrine", 31, 24)
talk(STEPS, "elder", 35, 11)
talk(STEPS, "statue_okidogi", 33, 9)
talk(STEPS, "statue_munkidori", 35, 9)
talk(STEPS, "statue_fezandipiti", 37, 9)
talk(STEPS, "sign_pond", 28, 13)
talk(STEPS, "lanterns", 21, 7)
talk(STEPS, "hiker", 19, 7)
talk(STEPS, "legend_3", 26, 6)
-- Kitakami Hall (the Mask Hall): the caretaker before the stage
add(STEPS, {{"warp", 35, 106, 12, 16}})
door(STEPS, "hall", 12, 14, 35107)
add(STEPS, {{"walk", 7, 8, "on", "to_caretaker"}, {"face", "UP"}, {"a"}, {"mash", "caretaker", 35107}})
-- the family house, the two homes
add(STEPS, {{"warp", 35, 106, 18, 31}})
door(STEPS, "family", 18, 29, 35108)
talk(STEPS, "grandpa", 6, 2, 35108)
add(STEPS, {{"warp", 35, 106, 7, 31}})
door(STEPS, "home1", 7, 29, 35110)
talk(STEPS, "old_woman", 6, 3, 35110)
add(STEPS, {{"warp", 35, 106, 40, 31}})
door(STEPS, "home2", 40, 29, 35111)
talk(STEPS, "old_man", 2, 3, 35111)
talk(STEPS, "old_woman2", 6, 3, 35111)
-- Briar's bus back to Mossdeep
add(STEPS, {{"warp", 35, 106, 23, 46}})
talk(STEPS, "briar_back", 22, 46, MD)
add(STEPS, {
  {"expect", "back_in_mossdeep", map = MD, pos = {70, 33}, at = {{35, 70, 32}}},
  {"shot", "mossdeep_back"},
  -- a save in Mossdeep, Continue: Briar is still there
  {"menutop"},
  {"press", "START", 90},
  {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15},
  {"press", "A", 60}, {"mash", "save", MD},
  {"reset"}, {"boot"},
  {"expect", "continued", map = MD, at = {{35, 70, 32}}},
  {"shot", "continued"},
  {"finish"},
})
