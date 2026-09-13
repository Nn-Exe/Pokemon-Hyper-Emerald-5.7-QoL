-- Showcase capture: bag 999 + START sort, SELECT key-item popup (4 registered), quick-ball widget (hold R in battle).
local dir = "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/tools/test-harness/"
local f = 0
local A, B, SELECT, START, RIGHT, LEFT, UP, DOWN, R, L = 0, 1, 2, 3, 4, 5, 6, 7, 8, 9
local NL = string.char(10)
local log = io.open(dir .. "showcase_log.txt", "w")
local function inBattle() return emu:read32(0x030022C4) == 0x08038421 end
local function shot(name) emu:screenshot(dir .. "sh_" .. name .. ".png"); log:write(name .. " f=" .. f .. NL); log:flush() end
local plan = {}
local function at(fr, fn) plan[#plan + 1] = {fr, fn} end
local function tap(key, fr) at(fr, function() emu:addKey(key) end); at(fr + 4, function() emu:clearKey(key) end) end
local t = 2600
at(t, function()
  local sb1 = emu:read32(0x03005D8C)
  emu:write16(sb1 + 0x496, 259)                       -- registered: Mach Bike
  emu:write16(sb1 + 0x9C2, 261); emu:write16(sb1 + 0x9C4, 262); emu:write16(sb1 + 0x9C6, 264)   -- Itemfinder, Old Rod, Acro Bike
  local slots = 0x0203D030
  emu:write16(slots + 2, 999)                         -- first Items slot x999
  emu:write16(slots + 6, 250)
end)
-- bag: START, DOWN, DOWN, A (fresh boot cursor is on Pokedex)
tap(START, t + 20); tap(DOWN, t + 60); tap(DOWN, t + 90); tap(A, t + 120)
at(t + 300, function() shot("bag_open") end)
tap(START, t + 310); at(t + 360, function() shot("bag_sort1") end)
at(t + 400, function() shot("bag_sort1b") end)
tap(START, t + 420); at(t + 470, function() shot("bag_sort2") end)
tap(START, t + 530); at(t + 580, function() shot("bag_sort3") end)
tap(B, t + 620); tap(B, t + 720)
-- SELECT popup
tap(SELECT, t + 820); at(t + 870, function() shot("keyreg_popup") end)
at(t + 900, function() shot("keyreg_popup2") end)
tap(B, t + 920)
at(t + 960, function() local fh = io.open(dir .. "showcase_done.txt", "w"); fh:write("done"); fh:close() end)
-- walk into battle, hold R
local phase = "idle"; local m = 0

callbacks:add("frame", function()
  f = f + 1
  if f < 1900 and f % 90 == 0 then emu:addKey(START) end
  if f < 1900 and f % 90 == 5 then emu:clearKey(START) end
  if f == 2000 then emu:addKey(A) end
  if f == 2004 then emu:clearKey(A) end
  for _, p in ipairs(plan) do if f == p[1] then p[2]() end end
  if phase == "walk" then
    local k = math.floor((f - m) / 40) % 2
    if k == 0 then emu:clearKey(RIGHT); emu:addKey(LEFT) else emu:clearKey(LEFT); emu:addKey(RIGHT) end
    if inBattle() then
      emu:clearKey(LEFT); emu:clearKey(RIGHT); phase = "battle"; m = f
      for _, d in ipairs({900, 1100, 1300, 1400}) do tap(B, m + d) end
      at(m + 1500, function() shot("battle_menu") end)
      at(m + 1510, function() emu:addKey(R) end)
      at(m + 1560, function() shot("quickball_hold") end)
      tap(RIGHT, m + 1580); at(m + 1640, function() shot("quickball_hold2") end)
      at(m + 1650, function() emu:clearKey(R) end)
      at(m + 1700, function() shot("quickball_thrown") end)
      at(m + 1800, function() shot("quickball_thrown2") end)
      at(m + 2000, function() local fh = io.open(dir .. "showcase_done.txt", "w"); fh:write("done"); fh:close() end)
    end
    if f - m > 6000 then local fh = io.open(dir .. "showcase_done.txt", "w"); fh:write("done"); fh:close(); phase = "done" end
  end
end)
