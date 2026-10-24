-- A real Poke Ball at Ogerpon (2026-10-17: the story tests wrote the battle's outcome as "caught"; this throws one):
-- Part 1 up to Ogerpon's four masks battled (F_MASKS), a Master Ball given (additem, on this copy only), Ogerpon
-- talked to at the plaza: the catch battle; in it BAG, the Poke Balls, the Master Ball, Use. Then F_OGERPON must be
-- set and an Ogerpon in the party or the PC (the Pokedex mark 1017). Pictures at every press.
local PART1 = {0x43E9, 0x43EB, 0x43ED, 0x43F2, 0x43F8, 0x43F9, 0x43FC, 0x43FE, 0x440B, 0x440C, 0x441B, 0x4337, 0x4346,
               0x4347, 0x434A}
local function p(key, wait, tag) return {{"press", key, wait or 40}, {"shot", tag}} end
local function add(list, more) for _, s in ipairs(more) do list[#list + 1] = s end return list end
STEPS = {
  {"setup", set = PART1, repel = false},
  {"dex9", clear = {1017}},
  {"warp", 35, 106, 35, 12}, {"wait", 90},
  {"script", {0x44, 0x01, 0x00, 0x01, 0x00, 0x02}, 60},                 -- additem Master Ball (item 1), 1
  {"expect", "ogerpon_waits", on = {0x434A}, off = {0x4352}, at = {{19, 35, 10}}},
  {"walk", 35, 10, "act", "to_ogerpon"}, {"face_to", 35, 10}, {"a"}, {"wait", 60}, {"shot", "talk"},
  {"wait", 120}, {"press", "A", 120}, {"shot", "talk2"}, {"press", "A", 120}, {"shot", "talk3"},
  {"press", "A", 120}, {"shot", "talk4"}, {"wait", 600}, {"shot", "battle_intro"}, {"press", "A", 300},
  {"shot", "battle_menu"},
}
add(STEPS, p("RIGHT", 30, "on_bag"))
add(STEPS, p("A", 120, "bag_open"))
add(STEPS, p("RIGHT", 60, "balls_pocket"))
add(STEPS, p("A", 60, "ball_picked"))
add(STEPS, p("A", 60, "use"))
add(STEPS, {{"wait", 900}, {"shot", "thrown"}})
add(STEPS, p("B", 120, "after1"))
add(STEPS, p("B", 120, "after2"))
add(STEPS, p("B", 120, "after3"))
add(STEPS, p("B", 120, "after4"))
add(STEPS, {{"mash", "after_catch", 35106}, {"shot", "field_after"},
            {"expect", "caught", on = {0x4352}}, {"finish"}})
local last = nil
callbacks:add("frame", function()            -- Ogerpon's Pokedex mark (1017) and the party, whenever they change
  if emu:read32(0x03005D8C) == 0 then return end
  local ext, k = 0x0203DA00, 1017 - 960
  local t = {}
  for i = 0, 5 do t[#t + 1] = tostring(emu:read16(0x020244EC + 100 * i + 0x20)) end
  local now = string.format("party %s; Pokedex 1017 caught %d", table.concat(t, " "),
    (emu:read8(ext + 36 + (k >> 3)) >> (k & 7)) & 1)
  if now ~= last then last = now; w("test: " .. now) end
end)
