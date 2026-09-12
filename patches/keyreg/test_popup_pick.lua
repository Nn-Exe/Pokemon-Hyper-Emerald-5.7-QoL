local dir = "C:/Users/nonth/AppData/Local/Temp/claude/c--Users-nonth-Desktop-Works---Productivity-gba-trans/02742dae-7df3-4db2-93fc-cf708e28c0df/scratchpad/bagtest/"
local f = 0
local A, B, SELECT, START, RIGHT, LEFT, UP, DOWN = 0, 1, 2, 3, 4, 5, 6, 7
local seq = {}
local function add(fr, key) seq[#seq + 1] = {fr, key} end
local t = 2000
add(t, A); t = t + 700                 -- CONTINUE -> field
add(t, SELECT); t = t + 90
local s_popup = t                      -- popup visible
add(t, B); t = t + 60
local s_cancel = t
add(t, LEFT); t = t + 60               -- walk (controls unlocked?)
local s_walk = t
add(t, SELECT); t = t + 90
local s_popup2 = t
add(t, DOWN); t = t + 20               -- pick slot 2 (Old Rod)
local s_pick = t + 60
t = t + 150
add(t, A); t = t + 120                 -- dismiss message if any
local s_after = t
add(t, SELECT); t = t + 90
add(t, LEFT); t = t + 120              -- pick slot 3 (Mach Bike)
local s_bike = t
add(t, A); t = t + 120
local s_bike2 = t
local done = t + 60
local shots = {[s_popup]="m1popup", [s_cancel]="m2cancel", [s_walk]="m3walk", [s_popup2]="m4popup2", [s_pick]="m5pick",
               [s_after]="m6after", [s_bike]="m7bike", [s_bike2]="m8bike2"}
local function slots()
  local p = emu:read32(0x03005D8C)
  return string.format("%d %d %d %d", emu:read16(p + 0x496), emu:read16(p + 0x9C2), emu:read16(p + 0x9C4), emu:read16(p + 0x9C6))
end
local log = io.open(dir .. "reg3_log.txt", "w")
callbacks:add("frame", function()
  f = f + 1
  if f < 1900 and f % 90 == 0 then emu:addKey(START) end
  if f < 1900 and f % 90 == 5 then emu:clearKey(START) end
  for _, s in ipairs(seq) do
    if f == s[1] then emu:addKey(s[2]) end
    if f == s[1] + 4 then emu:clearKey(s[2]) end
  end
  if shots[f] then
    emu:screenshot(dir .. "m_" .. shots[f] .. ".png")
    log:write(shots[f] .. " f=" .. f .. " slots=" .. slots() .. "\n"); log:flush()
  end
  if f == done then local fh = io.open(dir .. "reg3_done.txt", "w"); fh:write("done"); fh:close() end
end)
