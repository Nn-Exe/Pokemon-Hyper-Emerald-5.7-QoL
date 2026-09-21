-- Use the renamed item in Hoenn and watch the message with no further input at all.
local dir = "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/_testrun/"
local NL = string.char(10)
local log = io.open(dir .. "nm_log.txt", "w")
local function w(s) log:write(s .. NL); log:flush() end
local f = 0
local A, B, SELECT, START, RIGHT, LEFT, UP, DOWN = 0, 1, 2, 3, 4, 5, 6, 7
local plan = {}
local function at(fr, fn) plan[#plan+1] = {fr, fn} end
local function tap(k, fr) at(fr, function() emu:addKey(k) end); at(fr + 4, function() emu:clearKey(k) end) end
local function tasks(tag)
  local s = tag .. " cb2 " .. string.format("%08X", emu:read32(0x030022C4))
  for t = 0, 15 do
    local b = 0x03005E00 + t * 0x28
    if emu:read8(b + 4) == 1 then s = s .. string.format(" t%d=%08X", t, emu:read32(b)) end
  end
  w(s)
end
local t = 2400
at(t, function()
  local base = emu:read32(0x02039DD8 + 4 * 8)
  local cap = emu:read8(0x02039DD8 + 4 * 8 + 4)
  for i = 0, cap - 1 do
    if emu:read16(base + i * 4) == 361 then
      local a, b = emu:read16(base), emu:read16(base + 2)
      emu:write16(base + i * 4, a); emu:write16(base + i * 4 + 2, b)
      emu:write16(base, 361); emu:write16(base + 2, 1)
      w("moved the item to the top of Key Items")
    end
  end
end)
tap(START, t + 20)
for i = 0, 1 do tap(DOWN, t + 80 + i * 20) end
tap(A, t + 130)
tap(LEFT, t + 280)
tap(A, t + 360)
tap(A, t + 440)                       -- Use, then no input at all
for i = 0, 7 do
  local d = 480 + i * 40
  at(t + d, function() emu:screenshot(dir .. string.format("nm_%d.png", d)); tasks("t+" .. d) end)
end
tap(A, t + 820)                       -- now press A
at(t + 880, function() emu:screenshot(dir .. "nm_afterA.png"); tasks("after A") end)
at(t + 900, function() local fh = io.open(dir .. "nm_done.txt", "w"); fh:write("done"); fh:close() end)
callbacks:add("frame", function()
  f = f + 1
  if f < 1900 and f % 90 == 0 then emu:addKey(START) end
  if f < 1900 and f % 90 == 5 then emu:clearKey(START) end
  if f == 2000 then emu:addKey(A) end
  if f == 2004 then emu:clearKey(A) end
  for _, p in ipairs(plan) do if f == p[1] then p[2]() end end
end)
