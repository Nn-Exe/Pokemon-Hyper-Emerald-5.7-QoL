-- DexNav test 2: walk from Route 127 into Mossdeep City (group 0 / map 6, which is in the hack's extra
-- city encounter table), open DexNav there, screenshot both pages, leave, and walk again.
local dir = "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/_testrun/"
local f = 0
local A, B, SELECT, START, RIGHT, LEFT, UP, DOWN = 0, 1, 2, 3, 4, 5, 6, 7
local NL = string.char(10)
local log = io.open(dir .. "dnc_log.txt", "w")
local function px() return emu:read16(0x02037350 + 0x10) - 7 end
local function py() return emu:read16(0x02037350 + 0x12) - 7 end
local function shot(name)
  local sb1 = emu:read32(0x03005D8C)
  emu:screenshot(dir .. "dnc_" .. name .. ".png")
  log:write(string.format("%s f=%d pos=%d,%d map=%d/%d cb2=%08x menucount=%d%s", name, f, px(), py(),
    emu:read8(sb1 + 4), emu:read8(sb1 + 5), emu:read32(0x030022C4), emu:read8(0x0203760F), NL)); log:flush()
end
local plan = {}
local function at(fr, fn) plan[#plan + 1] = {fr, fn} end
local function tap(key, fr) at(fr, function() emu:addKey(key) end); at(fr + 4, function() emu:clearKey(key) end) end
local t = 2600
at(t, function() emu:addKey(UP) end); at(t + 40, function() emu:clearKey(UP) end)
at(t + 120, function() shot("mossdeep") end)
tap(START, t + 130); at(t + 180, function() shot("startmenu") end)
for i = 0, 6 do tap(DOWN, t + 200 + i * 12) end
tap(A, t + 300); at(t + 410, function() shot("dexnav_p1") end)
tap(RIGHT, t + 430); at(t + 470, function() shot("dexnav_p2") end)
tap(RIGHT, t + 490); at(t + 530, function() shot("dexnav_p3") end)
tap(B, t + 550); at(t + 670, function() shot("startmenu_again") end)
tap(B, t + 690); at(t + 750, function() shot("field_again") end)
at(t + 770, function() emu:addKey(DOWN) end); at(t + 810, function() emu:clearKey(DOWN) end)
at(t + 850, function() shot("walked") end)
at(t + 870, function() local fh = io.open(dir .. "dnc_done.txt", "w"); fh:write("done"); fh:close() end)
callbacks:add("frame", function()
  f = f + 1
  if f < 1900 and f % 90 == 0 then emu:addKey(START) end
  if f < 1900 and f % 90 == 5 then emu:clearKey(START) end
  if f == 2000 then emu:addKey(A) end
  if f == 2004 then emu:clearKey(A) end
  for _, p in ipairs(plan) do if f == p[1] then p[2]() end end
end)
