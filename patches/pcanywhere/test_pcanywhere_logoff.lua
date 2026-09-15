-- PC anywhere test: hub room (no PC in front). Hold B + press SELECT -> PC menu -> storage -> back -> log off,
-- then check the player can walk and nothing was drawn in front; finally SELECT alone still opens the key popup.
local dir = "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/tools/test-harness/"
local f = 0
local A, B, SELECT, START, RIGHT, LEFT, UP, DOWN, R, L = 0, 1, 2, 3, 4, 5, 6, 7, 8, 9
local NL = string.char(10)
local log = io.open(dir .. "pc1_log.txt", "w")
local function px() return emu:read16(0x02037350 + 0x10) - 7 end
local function py() return emu:read16(0x02037350 + 0x12) - 7 end
local function shot(name)
  emu:screenshot(dir .. "pc1_" .. name .. ".png")
  log:write(string.format("%s f=%d pos=%d,%d cb2=%08x%s", name, f, px(), py(), emu:read32(0x030022C4), NL)); log:flush()
end
local plan = {}
local function at(fr, fn) plan[#plan + 1] = {fr, fn} end
local function tap(key, fr) at(fr, function() emu:addKey(key) end); at(fr + 4, function() emu:clearKey(key) end) end
local t = 2600
at(t, function() shot("before") end)
at(t + 10, function() emu:addKey(B) end)                 -- hold B
tap(SELECT, t + 20)                                      -- press SELECT while B is held
at(t + 40, function() emu:clearKey(B) end)
at(t + 120, function() shot("menu") end)                 -- "Which PC should be accessed?"
tap(A, t + 130); at(t + 220, function() shot("a1") end)
tap(A, t + 230); at(t + 320, function() shot("a2") end)
at(t + 420, function() shot("storage_menu") end)
tap(B, t + 430); at(t + 540, function() shot("b1") end)
tap(B, t + 550); at(t + 660, function() shot("b2") end)
tap(B, t + 670); at(t + 780, function() shot("b3") end)
tap(B, t + 790); at(t + 900, function() shot("b4") end)
at(t + 960, function() emu:addKey(DOWN) end); at(t + 1000, function() emu:clearKey(DOWN); shot("walked_down") end)
at(t + 1030, function() emu:addKey(UP) end); at(t + 1070, function() emu:clearKey(UP) end)
at(t + 1110, function() shot("walked_up") end)
tap(SELECT, t + 1130); at(t + 1190, function() shot("select_alone") end)
tap(B, t + 1200); at(t + 1260, function() shot("end") end)
at(t + 1270, function() local fh = io.open(dir .. "pc1_done.txt", "w"); fh:write("done"); fh:close() end)
callbacks:add("frame", function()
  f = f + 1
  if f < 1900 and f % 90 == 0 then emu:addKey(START) end
  if f < 1900 and f % 90 == 5 then emu:clearKey(START) end
  if f == 2000 then emu:addKey(A) end
  if f == 2004 then emu:clearKey(A) end
  for _, p in ipairs(plan) do if f == p[1] then p[2]() end end
end)
