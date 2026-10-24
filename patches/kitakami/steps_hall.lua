-- The new Mask Hall (khall.py, 2026-10-17): how it looks, a plaque read, the caretaker, the door out; then with
-- F_WAKE set (the cases smashed) and with F_OGERPON set (the plaques' last words).
local HALL, MOSSUI = 35107, 35106
local function add(list, more) for _, s in ipairs(more) do list[#list + 1] = s end return list end
local function read(list, label, x)
  return add(list, {{"walk", x, 7, "on", "to_" .. label}, {"face", "UP"}, {"a"}, {"wait", 40}, {"shot", label},
                    {"mash", label, HALL}})
end
STEPS = {
  {"setup", set = {0x43EB}},                          -- after Carmine's battle (the caretaker gives the task)
  {"warp", 35, 107, 6, 9}, {"wait", 60}, {"shot", "hall_stage"},
  {"warp", 35, 107, 6, 13}, {"wait", 60}, {"shot", "hall_door"},
}
read(STEPS, "plaque_wellspring", 3)
read(STEPS, "plaque_hearthflame", 6)
add(STEPS, {{"walk", 7, 8, "on", "to_caretaker"}, {"face", "UP"}, {"a"}, {"wait", 40}, {"shot", "caretaker"},
            {"mash", "caretaker", HALL}})
add(STEPS, {{"walk", 6, 14, "on", "to_mat"}, {"press", "DOWN", 120}, {"wait", 60},
            {"expect", "out_of_the_hall", map = MOSSUI}, {"shot", "outside"}})
add(STEPS, {{"setup", set = {0x43EB, 0x43ED, 0x43FC, 0x43FE, 0x440B, 0x440C}},     -- the Loyal Three awake
            {"warp", 35, 107, 6, 9}, {"wait", 60}, {"shot", "smashed"}})
read(STEPS, "plaque_smashed", 9)
add(STEPS, {{"setup", set = {0x4352}}, {"warp", 35, 107, 6, 9}, {"wait", 60}, {"shot", "after_story"}})
read(STEPS, "plaque_after", 3)
add(STEPS, {{"finish"}})
