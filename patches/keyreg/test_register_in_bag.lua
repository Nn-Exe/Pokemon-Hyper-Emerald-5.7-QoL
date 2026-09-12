local dir = "C:/Users/nonth/AppData/Local/Temp/claude/c--Users-nonth-Desktop-Works---Productivity-gba-trans/02742dae-7df3-4db2-93fc-cf708e28c0df/scratchpad/bagtest/"
local f = 0
local A, B, SELECT, START, RIGHT, LEFT, UP, DOWN = 0, 1, 2, 3, 4, 5, 6, 7
-- sequence: {frame, key}
local seq = {}
local function add(fr, key) seq[#seq + 1] = {fr, key} end
local t = 2000
add(t, A); t = t + 600                 -- CONTINUE
add(t, START); t = t + 120             -- start menu
add(t, DOWN); t = t + 40; add(t, DOWN); t = t + 40
add(t, A); t = t + 300                 -- bag
for i = 1, 4 do add(t, RIGHT); t = t + 50 end   -- key items pocket
local shot1 = t
-- register item idx 2
add(t, DOWN); t = t + 30; add(t, DOWN); t = t + 30
add(t, A); t = t + 60
local shotctx = t
add(t, RIGHT); t = t + 40; add(t, A); t = t + 90
local shot2 = t
-- register item idx 4
add(t, DOWN); t = t + 30; add(t, DOWN); t = t + 30
add(t, A); t = t + 60; add(t, RIGHT); t = t + 40; add(t, A); t = t + 90
-- register item idx 7
add(t, DOWN); t = t + 30; add(t, DOWN); t = t + 30; add(t, DOWN); t = t + 30
add(t, A); t = t + 60; add(t, RIGHT); t = t + 40; add(t, A); t = t + 90
local shot3 = t
add(t, B); t = t + 200; add(t, B); t = t + 200   -- close bag, close start menu
local shot4 = t
add(t, SELECT); t = t + 90
local shot5 = t                        -- popup visible
add(t, B); t = t + 60                  -- cancel
local shot6 = t
add(t, LEFT); t = t + 60               -- can walk?
local shot7 = t
add(t, SELECT); t = t + 90
add(t, LEFT); t = t + 120              -- pick slot 3 (Mach Bike)
local shot8 = t
add(t, A); t = t + 120                 -- dismiss possible message
local shot9 = t
local done = t + 60
local shots = {[shot1]="k1", [shotctx]="k2ctx", [shot2]="k3", [shot3]="k4", [shot4]="k5field", [shot5]="k6popup",
               [shot6]="k7cancel", [shot7]="k8walk", [shot8]="k9pick", [shot9]="k10after"}
local function slots()
  local p = emu:read32(0x03005D8C)
  return string.format("%d %d %d %d", emu:read16(p + 0x496), emu:read16(p + 0x9C2), emu:read16(p + 0x9C4), emu:read16(p + 0x9C6))
end
local log = io.open(dir .. "reg1_log.txt", "w")
callbacks:add("frame", function()
  f = f + 1
  if f < 1900 and f % 90 == 0 then emu:addKey(START) end
  if f < 1900 and f % 90 == 5 then emu:clearKey(START) end
  for _, s in ipairs(seq) do
    if f == s[1] then emu:addKey(s[2]) end
    if f == s[1] + 4 then emu:clearKey(s[2]) end
  end
  if shots[f] then
    emu:screenshot(dir .. "r_" .. shots[f] .. ".png")
    log:write(shots[f] .. " f=" .. f .. " slots=" .. slots() .. "\n"); log:flush()
  end
  if f == done then local fh = io.open(dir .. "done.txt", "w"); fh:write("done"); fh:close() end
end)
