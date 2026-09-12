local dir = "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/_testrun/"
local f = 0
local A, B, SELECT, START, RIGHT, LEFT, UP, DOWN, R = 0, 1, 2, 3, 4, 5, 6, 7, 8
local log = io.open(dir .. "auto1_log.txt", "w")
local function pos() return emu:read16(0x02037350 + 0x10), emu:read16(0x02037350 + 0x12) end
local function flag() return emu:read8(emu:read32(0x03005D8C) + 0x31) end
local function finish(msg) local fh = io.open(dir .. "auto1_done.txt", "w"); fh:write(msg); fh:close() end
-- steps: {frame offset, action}; hold = {key, frames}
local seq = {}
local t = 2700
local function hold(key, frames, extra)
  seq[#seq+1] = {t, function() emu:addKey(key); if extra then emu:addKey(extra) end end}
  seq[#seq+1] = {t + frames, function() emu:clearKey(key); if extra then emu:clearKey(extra) end end}
  t = t + frames + 30
end
local function tap(key) seq[#seq+1] = {t, function() emu:addKey(key) end}; seq[#seq+1] = {t+4, function() emu:clearKey(key) end}; t = t + 30 end
local function mark(name)
  seq[#seq+1] = {t, function() local x, y = pos(); log:write(string.format("%s f=%d pos=%d,%d autorun=%d\n", name, f, x, y, flag())); log:flush(); emu:screenshot(dir .. "a1_" .. name .. ".png") end}
  t = t + 2
end
mark("start")
hold(DOWN, 48); mark("walk_down"); hold(UP, 48); mark("walk_up")
hold(RIGHT, 48); mark("walk_right"); hold(LEFT, 48); mark("walk_left")
tap(R); mark("toggled_on")
hold(DOWN, 48); mark("auto_down"); hold(UP, 48); mark("auto_up")
hold(RIGHT, 48); mark("auto_right"); hold(LEFT, 48); mark("auto_left")
hold(DOWN, 48, B); mark("autoB_down"); hold(UP, 48, B); mark("autoB_up")
tap(R); mark("toggled_off")
hold(DOWN, 48); mark("off_down"); hold(UP, 48); mark("off_up")
hold(DOWN, 48, B); mark("offB_down"); hold(UP, 48, B); mark("offB_up")
seq[#seq+1] = {t, function() finish("done") end}
callbacks:add("frame", function()
  f = f + 1
  if f < 1900 and f % 90 == 0 then emu:addKey(START) end
  if f < 1900 and f % 90 == 5 then emu:clearKey(START) end
  if f == 2000 then emu:addKey(A) end
  if f == 2004 then emu:clearKey(A) end
  for _, s in ipairs(seq) do if f == s[1] then s[2]() end end
end)
