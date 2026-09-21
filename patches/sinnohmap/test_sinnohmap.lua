-- Open the Sinnoh map from the bag: find the Town Map in Key Items, use it, look, then B out.
local dir = "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/_testrun/"
local NL = string.char(10)
local log = io.open(dir .. "sm_log.txt", "w")
local function w(s) log:write(s .. NL); log:flush() end
local f = 0
local A, B, SELECT, START, RIGHT, LEFT, UP, DOWN = 0, 1, 2, 3, 4, 5, 6, 7
local plan = {}
local function at(fr, fn) plan[#plan+1] = {fr, fn} end
local function tap(k, fr) at(fr, function() emu:addKey(k) end); at(fr + 4, function() emu:clearKey(k) end) end
local t = 2400
at(t, function()
  local sb1 = emu:read32(0x03005D8C)
  local base = emu:read32(0x02039DD8 + 4 * 8)
  local cap = emu:read8(0x02039DD8 + 4 * 8 + 4)
  local slot = nil
  for i = 0, cap - 1 do if emu:read16(base + i * 4) == 361 then slot = i end end
  w(string.format("map group %d num %d; Town Map in key-item slot %s", emu:read8(sb1 + 4), emu:read8(sb1 + 5), tostring(slot)))
  if slot then                              -- move it to the top so the cursor lands on it
    local first = emu:read16(base)
    local firstq = emu:read16(base + 2)
    emu:write16(base + slot * 4, first); emu:write16(base + slot * 4 + 2, firstq)
    emu:write16(base, 361); emu:write16(base + 2, 1)
  end
end)
tap(START, t + 20)
for i = 0, 1 do tap(DOWN, t + 80 + i * 20) end
tap(A, t + 130)                              -- Bag
tap(LEFT, t + 280)                           -- -> Key Items
at(t + 340, function() emu:screenshot(dir .. "sm_bag.png") end)
tap(A, t + 360)                              -- pick the Town Map
at(t + 420, function() emu:screenshot(dir .. "sm_menu.png") end)
tap(A, t + 440)                              -- Use
for i = 0, 6 do
  local d = 470 + i * 25
  at(t + d, function() emu:screenshot(dir .. string.format("sm_u%d.png", d)) end)
end
at(t + 520, function() emu:screenshot(dir .. "sm_open.png")
  w(string.format("after Use: cb2 %08X", emu:read32(0x030022C4))) end)
at(t + 620, function() emu:screenshot(dir .. "sm_map1.png")
  w(string.format("on the map: cb2 %08X", emu:read32(0x030022C4))) end)
at(t + 640, function() emu:screenshot(dir .. "sm_map2.png") end)
tap(B, t + 700)
at(t + 800, function() emu:screenshot(dir .. "sm_back.png")
  w(string.format("after B: cb2 %08X", emu:read32(0x030022C4))) end)
at(t + 820, function() local fh = io.open(dir .. "sm_done.txt", "w"); fh:write("done"); fh:close() end)
callbacks:add("frame", function()
  f = f + 1
  if f < 1900 and f % 90 == 0 then emu:addKey(START) end
  if f < 1900 and f % 90 == 5 then emu:clearKey(START) end
  if f == 2000 then emu:addKey(A) end
  if f == 2004 then emu:clearKey(A) end
  for _, p in ipairs(plan) do if f == p[1] then p[2]() end end
end)
