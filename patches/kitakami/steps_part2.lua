-- Kitakami Part 2, Mochi Mayhem (2026-10-17), on a build with the built-in places, from the user's own save with
-- Part 1 marked done: Briar's letter in Mossdeep and her bus; Kieran in the market (Nemona goes off); the farmer
-- (Shige) and the mother (Aya); the grandparents before Kitakami Hall; Arven and Penny in the market (Pecharunt shows
-- itself and flies off) - all woken by talking since 2026-10-17 (only Nemona and Pecharunt are battles); Nemona at Loyalty Plaza, then Pecharunt (won: it is yours); the morning after; Grandpa's
-- masks still there; a save and Continue.
--   ..\paldea\run.ps1 -Rom k12.gba -Steps ../../../_testrun/kitakami/steps_part2.lua -Timeout 3000
local MD, MOSSUI, FAMILY = 6, 35106, 35108
local F = {start = 0x437D, kieran = 0x4381, shige = 0x4382, aya = 0x4385, elders = 0x4386, arven = 0x438B,
           penny = 0x438D, nemona = 0x438E, pecharunt = 0x4390}
local PART1 = {0x43EB, 0x43ED, 0x43F2, 0x43F8, 0x43F9, 0x43FC, 0x43FE, 0x440B, 0x440C, 0x441B, 0x4337, 0x4346,
               0x4347, 0x434A, 0x4352}
local function add(list, more) for _, s in ipairs(more) do list[#list + 1] = s end return list end
local function talk(list, label, x, y, map)
  return add(list, {{"walk", x, y, "act", label}, {"walk", x, y, "act", label .. "_again"}, {"face_to", x, y}, {"a"},
                    {"mash", label, map or MOSSUI}, {"shot", label .. "_after"}})
end
local function fight(list, label, x, y, map)
  return add(list, {{"walk", x, y, "act", label}, {"walk", x, y, "act", label .. "_again"}, {"face_to", x, y}, {"a"},
                    {"fight", label, map or MOSSUI}, {"shot", label .. "_after"}})
end

-- once Pecharunt is caught: where it went, and the Pokedex's mark for 1025 (gen9rest's block: caught bit 1 of byte 8)
local function sb1() return emu:read32(0x03005D8C) end
local function sb2() return emu:read32(0x03005D90) end
local function flagbyte(f)
  local i = (f - 0x4000) >> 3
  if i <= 0x33 then return sb1() + 0x988 + i end
  if i <= 0x67 then return sb1() + 0x3B24 + i - 0x34 end
  if i <= 0x9B then return sb2() + 0x5C + i - 0x68 end
  return sb2() + 0x28 + i - 0x9C
end
local told = false
callbacks:add("frame", function()
  if told or (emu:read8(flagbyte(F.pecharunt)) >> (F.pecharunt & 7)) & 1 == 0 then return end
  told = true
  local where = "not in the party"
  for k = 0, 5 do
    if emu:read16(0x020244EC + 100 * k + 0x20) == 1237 then
      where = string.format("party slot %d, level %d", k + 1, emu:read8(0x020244EC + 100 * k + 0x54))
    end
  end
  local ext = 0x0203DA00
  w(string.format("test: Pecharunt caught - %s; Pokedex 1025 seen %d caught %d (marker %08X)", where,
    (emu:read8(ext + 4 + 8) >> 1) & 1, (emu:read8(ext + 36 + 8) >> 1) & 1, emu:read32(ext)))
end)

STEPS = {
  {"setup", set = PART1},
  {"expect", "part1_done", on = {0x4352}, off = {F.start}},
  {"warp", 0, 6, 70, 33},
}
talk(STEPS, "briar_letter", 70, 32, MOSSUI)
add(STEPS, {{"wait", 60}, {"expect", "p12_arrived", map = MOSSUI, on = {F.start}, at = {{3, 26, 41}, {29, 20, 41}}},
            {"shot", "p12_night_market"}})
talk(STEPS, "kieran_meet", 26, 41)
add(STEPS, {{"expect", "p13", on = {F.kieran}, gone = {29}}})
talk(STEPS, "shige", 14, 35)
add(STEPS, {{"expect", "shige_beaten", on = {F.shige}}})
talk(STEPS, "aya", 33, 33)
add(STEPS, {{"expect", "p14", on = {F.aya}}, {"warp", 35, 106, 12, 18}, {"wait", 60},
            {"expect", "grandparents_at_the_hall", at = {{31, 10, 16}, {32, 14, 16}, {3, 14, 19}}},
            {"shot", "p14_hall"}})
talk(STEPS, "grandparents", 10, 16)
add(STEPS, {{"expect", "p15", on = {F.elders}, gone = {31, 32}}, {"warp", 35, 106, 23, 42}, {"wait", 60},
            {"expect", "friends_dancing", at = {{27, 21, 40}, {28, 26, 40}}}, {"shot", "p15_market"}})
talk(STEPS, "arven", 21, 40)
talk(STEPS, "penny", 26, 40)
add(STEPS, {{"expect", "p16", on = {F.arven, F.penny}}, {"warp", 35, 106, 36, 13}, {"wait", 60},
            {"expect", "nemona_and_pecharunt", at = {{29, 36, 11}, {30, 36, 10}}}, {"shot", "p16_plaza"}})
fight(STEPS, "nemona_pecharunt", 36, 11)
add(STEPS, {{"expect", "p17_pecharunt_caught", on = {F.nemona, F.pecharunt}}, {"shot", "p17_plaza"},
            {"warp", 35, 106, 25, 47}, {"wait", 60}, {"shot", "p17_morning"}})
talk(STEPS, "kieran_after", 25, 45)
add(STEPS, {{"warp", 35, 106, 18, 31}, {"walk", 18, 29, "on", "family"}, {"wait", 150}, {"expect", "family", map = FAMILY},
            {"walk", 6, 3, "act", "to_grandpa"}, {"face_to", 6, 2}, {"a"}, {"wait", 60}, {"shot", "grandpa_after"},
            {"press", "B", 60}, {"press", "B", 60}, {"mash", "grandpa_after", FAMILY},
            {"warp", 35, 106, 23, 46},
            {"menutop"},
            {"press", "START", 90},
            {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15},
            {"press", "DOWN", 15},
            {"press", "A", 60}, {"mash", "save", MOSSUI},
            {"reset"}, {"boot"},
            {"expect", "continued", map = MOSSUI, on = {F.pecharunt}},
            {"shot", "continued"},
            {"finish"}})
