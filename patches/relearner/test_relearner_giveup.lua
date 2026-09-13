-- In-party move relearner test 2: (a) open Moves, give up with B -> Yes, confirm overworld control;
-- (b) open again, learn Hammer Arm over move 1, confirm overworld control and the new move in the party data.
local dir = "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/tools/test-harness/"
local f = 0
local A, B, SELECT, START, RIGHT, LEFT, UP, DOWN, R, L = 0, 1, 2, 3, 4, 5, 6, 7, 8, 9
local log = io.open(dir .. "relearn2_log.txt", "w")
local function mon1moves()
  local p = 0x020244EC
  return string.format("moves=%d,%d,%d,%d", emu:read16(p + 0x2C), emu:read16(p + 0x2E), emu:read16(p + 0x30), emu:read16(p + 0x32))
end
local function pos() return string.format("pos=%d,%d", emu:read16(0x02037350 + 0x10), emu:read16(0x02037350 + 0x12)) end
local function shot(name) emu:screenshot(dir .. "rl2_" .. name .. ".png"); log:write(name .. " f=" .. f .. " " .. pos() .. " " .. mon1moves() .. "\n"); log:flush() end
local seq = {}
local function at(fr, fn) seq[#seq + 1] = {fr, fn} end
local function tap(key, fr) at(fr, function() emu:addKey(key) end); at(fr + 4, function() emu:clearKey(key) end) end
local function openMoves(t)
  tap(START, t); tap(DOWN, t + 40); tap(A, t + 80); tap(A, t + 230); tap(UP, t + 310); tap(UP, t + 340); tap(A, t + 380)
end
local t = 2700
at(t - 10, function() shot("start") end)
openMoves(t); at(t + 600, function() shot("relearner_a") end)
tap(B, t + 610); at(t + 700, function() shot("giveup_prompt") end)
tap(A, t + 710); at(t + 950, function() shot("back_a") end)
at(t + 960, function() emu:addKey(LEFT) end); at(t + 1030, function() emu:clearKey(LEFT); shot("walked_a") end)
tap(START, t + 1050); at(t + 1120, function() shot("menu_a") end); tap(B, t + 1130)
-- (b) full learn
local u = t + 1300
openMoves(u); at(u + 600, function() shot("relearner_b") end)
tap(A, u + 610); at(u + 760, function() shot("b_pick") end)          -- "can't learn more than four"
tap(A, u + 770); at(u + 900, function() shot("b_delete_q") end)      -- "Delete an older move?" Yes/No
tap(A, u + 910); at(u + 1250, function() shot("b_forget_screen") end) -- summary screen
tap(A, u + 1260); at(u + 1450, function() shot("b_after_choose") end)
tap(A, u + 1460); at(u + 1650, function() shot("b_msg1") end)
tap(A, u + 1660); at(u + 1850, function() shot("b_msg2") end)
tap(A, u + 1860); at(u + 2050, function() shot("b_msg3") end)
tap(A, u + 2060); at(u + 2300, function() shot("b_after") end)
tap(B, u + 2310); tap(B, u + 2400); at(u + 2600, function() shot("back_b") end)
at(u + 2610, function() emu:addKey(RIGHT) end); at(u + 2680, function() emu:clearKey(RIGHT); shot("walked_b") end)
tap(START, u + 2700); at(u + 2770, function() shot("menu_b") end); tap(B, u + 2780)
at(u + 2820, function() local fh = io.open(dir .. "relearn2_done.txt", "w"); fh:write("done"); fh:close() end)
callbacks:add("frame", function()
  f = f + 1
  if f < 1900 and f % 90 == 0 then emu:addKey(START) end
  if f < 1900 and f % 90 == 5 then emu:clearKey(START) end
  if f == 2000 then emu:addKey(A) end
  if f == 2004 then emu:clearKey(A) end
  for _, s in ipairs(seq) do if f == s[1] then s[2]() end end
end)
