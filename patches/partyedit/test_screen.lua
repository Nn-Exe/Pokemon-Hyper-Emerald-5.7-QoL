-- Task 4 test: open the party menu, choose Edit, and screenshot the editor screen.
local DIR = "/Users/ribeiro/Downloads/Pokemon-Hyper-Emerald-5.7-QoL/build/test/"
local OUT = DIR .. "screens/"
local A, START, DOWN, UP = 0, 3, 7, 6
local frames, done = 0, false
local log = io.open(DIR .. "screen_log.txt", "w")
local function w(s) log:write(s .. string.char(10)); log:flush() end
local cb2_init, cb2_edit

callbacks:add("frame", function()
  frames = frames + 1
  if frames < 1900 and frames % 90 == 0 then emu:addKey(START) end
  if frames < 1900 and frames % 90 == 5 then emu:clearKey(START) end
  if frames == 2000 then emu:addKey(A) end
  if frames == 2004 then emu:clearKey(A) end
  if frames == 2600 then emu:addKey(START) end
  if frames == 2604 then emu:clearKey(START) end
  if frames == 2750 then emu:addKey(DOWN) end
  if frames == 2754 then emu:clearKey(DOWN) end
  if frames == 2900 then emu:addKey(A) end
  if frames == 2904 then emu:clearKey(A) end
  if frames == 3200 then emu:addKey(A) end
  if frames == 3204 then emu:clearKey(A) end
  -- action list is {Summary, Item, Edit, Moves, Cancel}: the cursor starts at the top, so two DOWNs
  -- reach Edit. (UP wraps here, so do not press it.)
  for _, f in ipairs({3400, 3470}) do
    if frames == f then emu:addKey(DOWN) end
    if frames == f + 4 then emu:clearKey(DOWN) end
  end
  if frames == 3750 then emu:addKey(A) end
  if frames == 3754 then emu:clearKey(A) end
  if frames == 4100 then
    w(string.format("cb2 = %08X (expect 08F5398D)", emu:read32(0x030022C0 + 4)))
    emu:screenshot(OUT .. "editor.png")
  end
  if frames == 4300 then
    w(string.format("cb2 = %08X", emu:read32(0x030022C0 + 4)))
    emu:screenshot(OUT .. "editor2.png")
  end
  if frames >= 4500 and not done then
    done = true; local f = io.open(DIR .. "screen_done.txt", "w"); f:write("ok\n"); f:close()
  end
end)
