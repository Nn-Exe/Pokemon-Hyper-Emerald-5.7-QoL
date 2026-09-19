-- DexNav test: open START, move to DexNav (DOWN x7), open it, screenshot, page RIGHT twice, page LEFT,
-- B back to the start menu, B to the field, then walk to prove the overworld is alive.
local dir = "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/_testrun/"
local f = 0
local A, B, SELECT, START, RIGHT, LEFT, UP, DOWN, R, L = 0, 1, 2, 3, 4, 5, 6, 7, 8, 9
local NL = string.char(10)
local log = io.open(dir .. "dn_log.txt", "w")
local function px() return emu:read16(0x02037350 + 0x10) - 7 end
local function py() return emu:read16(0x02037350 + 0x12) - 7 end
local function shot(name)
  emu:screenshot(dir .. "dn_" .. name .. ".png")
  log:write(string.format("%s f=%d pos=%d,%d cb2=%08x menucount=%d%s", name, f, px(), py(),
    emu:read32(0x030022C4), emu:read8(0x0203760F), NL)); log:flush()
end
local plan = {}
local function at(fr, fn) plan[#plan + 1] = {fr, fn} end
local function tap(key, fr) at(fr, function() emu:addKey(key) end); at(fr + 4, function() emu:clearKey(key) end) end
local t = 2600
at(t, function() shot("field") end)
tap(START, t + 10); at(t + 60, function() shot("startmenu") end)
for i = 0, 6 do tap(DOWN, t + 80 + i * 12) end
at(t + 180, function() shot("cursor_dexnav") end)
tap(A, t + 190); at(t + 300, function() shot("dexnav_p1") end)
tap(RIGHT, t + 320); at(t + 360, function() shot("dexnav_p2") end)
tap(RIGHT, t + 380); at(t + 420, function() shot("dexnav_p3") end)
tap(LEFT, t + 440); at(t + 480, function() shot("dexnav_back_p2") end)
tap(B, t + 500); at(t + 620, function() shot("startmenu_again") end)
tap(B, t + 640); at(t + 700, function() shot("field_again") end)
at(t + 720, function() emu:addKey(UP) end); at(t + 760, function() emu:clearKey(UP) end)
at(t + 800, function() shot("walked") end)
at(t + 820, function() local fh = io.open(dir .. "dn_done.txt", "w"); fh:write("done"); fh:close() end)
callbacks:add("frame", function()
  f = f + 1
  if f < 1900 and f % 90 == 0 then emu:addKey(START) end
  if f < 1900 and f % 90 == 5 then emu:clearKey(START) end
  if f == 2000 then emu:addKey(A) end
  if f == 2004 then emu:clearKey(A) end
  for _, p in ipairs(plan) do if f == p[1] then p[2]() end end
end)
