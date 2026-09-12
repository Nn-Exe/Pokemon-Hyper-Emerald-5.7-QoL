local dir = "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/tools/test-harness/"
local f = 0
local A, B, SELECT, START, RIGHT, LEFT, UP, DOWN, R, L = 0, 1, 2, 3, 4, 5, 6, 7, 8, 9
local log = io.open(dir .. "lrepel2_log.txt", "w")
local function inBattle() return emu:read32(0x030022C4) == 0x08038421 end
local function state()
  local sb1 = emu:read32(0x03005D8C)
  local var = emu:read16(sb1 + 0x139C + (0x4021 - 0x4000) * 2)
  return string.format("var=%04x steps=%d pos=%d,%d battle=%s", var, var & 0xFF, emu:read16(0x02037350+0x10), emu:read16(0x02037350+0x12), tostring(inBattle()))
end
local phase = "boot"; local m = 0; local battles = 0; local wasBattle = false; local startSteps = 0
callbacks:add("frame", function()
  f = f + 1
  if f < 1900 and f % 90 == 0 then emu:addKey(START) end
  if f < 1900 and f % 90 == 5 then emu:clearKey(START) end
  if f == 2000 then emu:addKey(A) end
  if f == 2004 then emu:clearKey(A) end
  if f == 2700 then emu:addKey(L) end
  if f == 2704 then emu:clearKey(L) end
  if f == 2800 then emu:addKey(A) end      -- Yes
  if f == 2804 then emu:clearKey(A) end
  if f == 2900 then emu:addKey(A) end      -- close "used" message
  if f == 2904 then emu:clearKey(A) end
  if f == 2960 then log:write("activated: " .. state() .. "\n"); log:flush(); phase = "walk"; m = f end
  if phase == "walk" then
    local k = math.floor((f - m) / 40) % 2
    if k == 0 then emu:clearKey(RIGHT); emu:addKey(LEFT) else emu:clearKey(LEFT); emu:addKey(RIGHT) end
    local b = inBattle()
    if b and not wasBattle then battles = battles + 1; log:write(string.format("BATTLE started at f=%d %s\n", f, state())); log:flush() end
    wasBattle = b
    if (f - m) % 600 == 0 then log:write(string.format("f=%d %s battles=%d\n", f, state(), battles)); log:flush() end
    if f - m >= 4800 then
      emu:clearKey(LEFT); emu:clearKey(RIGHT)
      log:write(string.format("END f=%d %s battles=%d\n", f, state(), battles)); log:flush()
      local fh = io.open(dir .. "lrepel2_done.txt", "w"); fh:write("done"); fh:close(); phase = "done"
    end
  end
end)
