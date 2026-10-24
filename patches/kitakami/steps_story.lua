-- Kitakami's whole story (2026-10-16), played from the user's own save through test_paldea.lua's harness:
-- Briar's bus; chapter 1 Carmine's battle at the bus stop, Kieran, the caretaker's task; chapter 2 the three
-- signboards with Kieran, Loyalty Plaza, evening; chapter 3 the festival, Ogerpon drops the Teal Mask, a stall's
-- shop; chapter 4 Grandpa's true story; chapters 5-6 Kieran's battle and the Loyal Three waking; chapter 7 the hunt;
-- chapter 8 Kieran's second battle, Ogerpon's four masks and the catch; then a Loyal Three caught or knocked out after
-- the story, Grandpa changing an Ogerpon's mask, a save in Mossui and Continue.
--   ..\paldea\run.ps1 -Rom k7.gba -Steps ../../../_testrun/kitakami/steps_story.lua -Timeout 3000
-- Every walk is made twice: a PokeNav call can interrupt the first (it did, on the way to Carmine at the festival).
-- Two things the harness cannot do are done by a frame callback of this file, for the test only:
--  * the catch: the harness wins battles (our battlers pinned) but never throws a ball, so after Ogerpon's last
--    battle (the Teal form once F_MASKS is set) the battle's outcome is written as 7 (caught) once the battle is
--    over, before the script reads it. Ogerpon does not join the party.
--  * an Ogerpon to change: before Grandpa is asked after the story, the first party Pokemon is made an Ogerpon in
--    the Wellspring Mask (species 1229); the log says what it is after he changes it to Teal (1228).
local MD, MOSSUI, HALL, FAMILY = 6, 35106, 35107, 35108     -- (one-floor Hall since 2026-10-17: the maps renumbered)
local F = {carmine = 0x43EB, task = 0x43ED, b1 = 0x43F2, b2 = 0x43F8, b3 = 0x43F9, plaza = 0x43FC, mask = 0x43FE,
           truth = 0x440B, wake = 0x440C, oki = 0x441B, munki = 0x4337, fez = 0x4346, kieran3 = 0x4347,
           masks = 0x434A, ogerpon = 0x4352, gone_oki = 0x4356}
local function add(list, more) for _, s in ipairs(more) do list[#list + 1] = s end return list end
local function talk(list, label, x, y, map)
  return add(list, {{"walk", x, y, "act", label}, {"walk", x, y, "act", label .. "_again"}, {"face_to", x, y}, {"a"},
                    {"mash", label, map or MOSSUI},
                    {"shot", label .. "_after"}})
end
local function fight(list, label, x, y, map)
  return add(list, {{"walk", x, y, "act", label}, {"walk", x, y, "act", label .. "_again"}, {"face_to", x, y}, {"a"},
                    {"fight", label, map or MOSSUI},
                    {"shot", label .. "_after"}})
end
local function door(list, label, x, y, map)
  return add(list, {{"walk", x, y, "on", label}, {"wait", 150}, {"expect", label, map = map}, {"shot", label}})
end

-- the frame callback (see above)
local function sb2() return emu:read32(0x03005D90) end
local function sb1() return emu:read32(0x03005D8C) end
local function flagbyte(f)
  local i = (f - 0x4000) >> 3
  if i <= 0x33 then return sb1() + 0x988 + i end
  if i <= 0x67 then return sb1() + 0x3B24 + i - 0x34 end
  if i <= 0x9B then return sb2() + 0x5C + i - 0x68 end
  return sb2() + 0x28 + i - 0x9C
end
local function kflag(f) return (emu:read8(flagbyte(f)) >> (f & 7)) & 1 end
local catching, caught_frames, poked = false, 0, false
callbacks:add("frame", function()
  local cb = emu:read32(0x030022C4)
  if cb == 0x08038421 then
    if emu:read16(0x02024744 + 0x20) == 1228 and kflag(F.masks) == 1 and kflag(F.ogerpon) == 0 then catching = true end
  elseif catching then
    emu:write8(0x0202433A, 7); caught_frames = caught_frames + 1
    if caught_frames > 400 then catching = false end
  end
  local s = sb1()
  if not poked and kflag(F.ogerpon) == 1 and emu:read8(s + 4) == 35 and emu:read8(s + 5) == 108 then
    emu:write16(0x020244EC + 0x20, 1229); poked = true
    w(string.format("test: party 1 made species 1229 (Wellspring), max HP %d", emu:read16(0x020244EC + 0x58)))
  end
  if poked and not REPORTED and emu:read16(0x020244EC + 0x20) ~= 1229 then
    REPORTED = true
    w(string.format("kit_mask: party 1 is now species %d, max HP %d", emu:read16(0x020244EC + 0x20),
      emu:read16(0x020244EC + 0x58)))
  end
end)

STEPS = {
  {"setup"},
  {"expect", "area_zero_done", stage = 4},
  {"warp", 0, 6, 70, 33},
}
talk(STEPS, "briar_bus", 70, 32, MOSSUI)
add(STEPS, {{"expect", "arrived", map = MOSSUI, pos = {23, 46}}})
-- chapter 1: one step up from the bus stop Carmine sees you, and her battle begins (since 2026-10-20)
add(STEPS, {{"walk", 23, 45, "on", "carmine_spots"}, {"fight", "carmine_battle", MOSSUI}, {"shot", "carmine_battle_after"}})
add(STEPS, {{"expect", "ch1_carmine", on = {F.carmine}, gone = {2}}})
add(STEPS, {{"warp", 35, 106, 12, 16}})
door(STEPS, "hall_in", 12, 14, HALL)
add(STEPS, {{"walk", 7, 8, "on", "to_caretaker"}, {"face", "UP"}, {"a"}, {"mash", "caretaker_task", HALL},
            {"expect", "ch1_task", on = {F.task}}})
-- chapter 2
add(STEPS, {{"warp", 35, 106, 9, 38}, {"expect", "kieran_at_board1", at = {{3, 10, 36}}}})
talk(STEPS, "board1", 9, 37)
add(STEPS, {{"expect", "ch2_board1", on = {F.b1}}, {"warp", 35, 106, 38, 38},
            {"expect", "kieran_at_board2", at = {{3, 37, 36}}}})
talk(STEPS, "board2", 38, 37)
add(STEPS, {{"expect", "ch2_board2", on = {F.b2}}, {"warp", 35, 106, 24, 6},
            {"expect", "kieran_at_board3", at = {{3, 27, 5}}}})
talk(STEPS, "board3", 26, 6)
add(STEPS, {{"expect", "ch2_board3", on = {F.b3}}, {"warp", 35, 106, 36, 13},
            {"expect", "kieran_at_plaza", at = {{3, 36, 11}}}})
talk(STEPS, "kieran_plaza", 36, 11)
add(STEPS, {{"wait", 120}, {"expect", "ch2_evening", on = {F.plaza}, map = MOSSUI, pos = {23, 32}},
            {"shot", "evening_festival"}})
-- chapter 3
talk(STEPS, "carmine_festival", 25, 35)
add(STEPS, {{"expect", "ch3_mask", on = {F.mask}}})
-- the stall's greeting, A to Buy/Sell/Quit, B = Quit, then "Come again!" closed with B (mash's first A presses,
-- facing the vendor, would open the shop again and buy)
add(STEPS, {{"walk", 19, 40, "on", "to_apples"}, {"face", "UP"}, {"a"}, {"wait", 90}, {"press", "A", 90},
            {"shot", "apple_stall_shop"}, {"press", "B", 60}, {"shot", "apple_stall_quit"},
            {"press", "B", 60}, {"wait", 60}, {"shot", "apple_stall_left"}})
-- chapter 4
add(STEPS, {{"warp", 35, 106, 18, 31}})
door(STEPS, "family", 18, 29, FAMILY)
talk(STEPS, "grandpa_truth", 6, 2, FAMILY)
add(STEPS, {{"expect", "ch4_truth", on = {F.truth}}})
-- chapters 5 and 6
add(STEPS, {{"warp", 35, 106, 34, 13}, {"expect", "kieran_angry_at_plaza", at = {{3, 34, 11}}},
            {"shot", "plaza_morning"}})
fight(STEPS, "kieran_battle", 34, 11)
add(STEPS, {{"expect", "ch6_wake", on = {F.wake}, gone = {5, 6, 7}}})
-- chapter 7
add(STEPS, {{"warp", 35, 106, 41, 11}})
fight(STEPS, "hunt_okidogi", 42, 10)
add(STEPS, {{"expect", "ch7_okidogi", on = {F.oki}}, {"warp", 35, 106, 29, 11}})
fight(STEPS, "hunt_munkidori", 28, 10)
add(STEPS, {{"expect", "ch7_munkidori", on = {F.munki}}, {"warp", 35, 106, 12, 16}})
fight(STEPS, "hunt_fezandipiti", 17, 14)
add(STEPS, {{"expect", "ch7_all", on = {F.fez}}})
-- chapter 8
add(STEPS, {{"warp", 35, 106, 34, 12}, {"expect", "ogerpon_waits", at = {{19, 35, 10}}}, {"shot", "ogerpon_waits"}})
fight(STEPS, "ogerpon_final", 35, 10)
add(STEPS, {{"expect", "ch8_done", on = {F.kieran3, F.masks, F.ogerpon}}})
-- after the story
add(STEPS, {{"warp", 35, 106, 41, 11}})
fight(STEPS, "after_okidogi", 42, 10)
add(STEPS, {{"expect", "after_okidogi_gone", on = {F.gone_oki}}, {"warp", 35, 106, 18, 31}})
door(STEPS, "family_after", 18, 29, FAMILY)
talk(STEPS, "grandpa_masks", 6, 2, FAMILY)
add(STEPS, {{"warp", 35, 106, 23, 46},
  {"menutop"},
  {"press", "START", 90},
  {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15},
  {"press", "A", 60}, {"mash", "save", MOSSUI},
  {"reset"}, {"boot"},
  {"expect", "continued", map = MOSSUI, on = {F.ogerpon}},
  {"shot", "continued"},
  {"finish"},
})
