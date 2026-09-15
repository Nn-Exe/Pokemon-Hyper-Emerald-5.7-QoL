-- PC anywhere test: hub room (no PC in front). Hold B + press SELECT -> PC menu -> storage -> back -> log off,
-- then check the player can walk and nothing was drawn in front; finally SELECT alone still opens the key popup.
local dir = "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/tools/test-harness/"
local f = 0
local A, B, SELECT, START, RIGHT, LEFT, UP, DOWN, R, L = 0, 1, 2, 3, 4, 5, 6, 7, 8, 9
local NL = string.char(10)
local log = io.open(dir .. "pc3_log.txt", "w")
local function px() return emu:read16(0x02037350 + 0x10) - 7 end
local function py() return emu:read16(0x02037350 + 0x12) - 7 end
local function shot(name)
  emu:screenshot(dir .. "pc3_" .. name .. ".png")
  log:write(string.format("%s f=%d pos=%d,%d cb2=%08x%s", name, f, px(), py(), emu:read32(0x030022C4), NL)); log:flush()
end
local plan = {}
local lastcb = 0
callbacks:add("frame", function() local c = emu:read32(0x030022C4); if c ~= lastcb then log:write(string.format("cb2 -> %08x at f=%d%s", c, f, NL)); log:flush(); lastcb = c end end)
local function at(fr, fn) plan[#plan + 1] = {fr, fn} end
local function tap(key, fr) at(fr, function() emu:addKey(key) end); at(fr + 4, function() emu:clearKey(key) end) end
local t = 2600
at(t, function() shot("before") end)
at(t + 10, function() emu:addKey(B) end)                 -- hold B
tap(SELECT, t + 20)                                      -- press SELECT while B is held
at(t + 40, function() emu:clearKey(B) end)
at(t + 120, function() shot("menu") end)                 -- "Which PC should be accessed?"
tap(A, t + 130)                                   -- Lanette's PC
tap(A, t + 260)                                   -- "Accessed Lanette's PC."
tap(A, t + 390)                                   -- "Pokemon Storage System opened."
at(t + 500, function() shot("submenu") end)
tap(DOWN, t + 505); tap(DOWN, t + 525)
tap(A, t + 545)                                   -- Move Pokemon
at(t + 900, function() shot("box_screen") end)
tap(B, t + 910); at(t + 1000, function() shot("box_b") end)
tap(A, t + 1010); at(t + 1250, function() shot("box_left") end)
tap(B, t + 1260); at(t + 1360, function() shot("sub_b") end)
tap(B, t + 1370); at(t + 1480, function() shot("main_b") end)
tap(B, t + 1490); at(t + 1600, function() shot("off") end)
at(t + 1620, function() emu:addKey(UP) end); at(t + 1660, function() emu:clearKey(UP) end)
at(t + 1700, function() shot("walked") end)
at(t + 1720, function() local fh = io.open(dir .. "pc3_done.txt", "w"); fh:write("done"); fh:close() end)
callbacks:add("frame", function()
  f = f + 1
  if f < 1900 and f % 90 == 0 then emu:addKey(START) end
  if f < 1900 and f % 90 == 5 then emu:clearKey(START) end
  if f == 2000 then emu:addKey(A) end
  if f == 2004 then emu:clearKey(A) end
  for _, p in ipairs(plan) do if f == p[1] then p[2]() end end
end)
