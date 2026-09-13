-- In-party move relearner test 3 (fresh boot, START menu cursor at Pokedex): open Moves on the first mon,
-- learn Hammer Arm over move 1, then confirm overworld control and the START menu.
local dir = "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/tools/test-harness/"
local f = 0
local A, B, SELECT, START, RIGHT, LEFT, UP, DOWN, R, L = 0, 1, 2, 3, 4, 5, 6, 7, 8, 9
local log = io.open(dir .. "relearn3_log.txt", "w")
local function pos() return string.format("pos=%d,%d", emu:read16(0x02037350 + 0x10), emu:read16(0x02037350 + 0x12)) end
local function shot(name) emu:screenshot(dir .. "rl3_" .. name .. ".png"); log:write(name .. " f=" .. f .. " " .. pos() .. "\n"); log:flush() end
local seq = {}
local function at(fr, fn) seq[#seq + 1] = {fr, fn} end
local function tap(key, fr) at(fr, function() emu:addKey(key) end); at(fr + 4, function() emu:clearKey(key) end) end
local u = 2700
tap(START, u); tap(DOWN, u + 40); tap(A, u + 80); tap(A, u + 230); tap(UP, u + 310); tap(UP, u + 340); tap(A, u + 380)
at(u + 600, function() shot("relearner") end)
tap(A, u + 610); at(u + 760, function() shot("pick") end)            -- "can't learn more than four"
tap(A, u + 770); at(u + 900, function() shot("delete_q") end)        -- "Delete an older move?" Yes/No
tap(A, u + 910); at(u + 1250, function() shot("forget_screen") end)  -- summary screen (moves page)
tap(A, u + 1260); at(u + 1450, function() shot("after_choose") end)
tap(A, u + 1460); at(u + 1650, function() shot("msg1") end)
tap(A, u + 1660); at(u + 1850, function() shot("msg2") end)
tap(A, u + 1860); at(u + 2050, function() shot("msg3") end)
tap(A, u + 2060); at(u + 2300, function() shot("after") end)
tap(B, u + 2310); at(u + 2500, function() shot("after_b1") end)
tap(B, u + 2510); at(u + 2700, function() shot("after_b2") end)
tap(A, u + 2710); at(u + 2900, function() shot("after_a") end)
at(u + 2910, function() emu:addKey(RIGHT) end); at(u + 2980, function() emu:clearKey(RIGHT); shot("walked") end)
tap(START, u + 3000); at(u + 3070, function() shot("menu") end); tap(B, u + 3080)
at(u + 3120, function() local fh = io.open(dir .. "relearn3_done.txt", "w"); fh:write("done"); fh:close() end)
callbacks:add("frame", function()
  f = f + 1
  if f < 1900 and f % 90 == 0 then emu:addKey(START) end
  if f < 1900 and f % 90 == 5 then emu:clearKey(START) end
  if f == 2000 then emu:addKey(A) end
  if f == 2004 then emu:clearKey(A) end
  for _, s in ipairs(seq) do if f == s[1] then s[2]() end end
end)
