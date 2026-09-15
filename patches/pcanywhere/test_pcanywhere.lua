-- SELECT popup PC test: SELECT -> popup (5 lines) -> B -> PC menu -> log off -> walk;
-- SELECT -> SELECT cancels -> walk; SELECT -> RIGHT uses the registered Mach Bike.
local dir = "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/tools/test-harness/"
local f = 0
local A, B, SELECT, START, RIGHT, LEFT, UP, DOWN, R, L = 0, 1, 2, 3, 4, 5, 6, 7, 8, 9
local NL = string.char(10)
local log = io.open(dir .. "pc5_log.txt", "w")
local function px() return emu:read16(0x02037350 + 0x10) - 7 end
local function py() return emu:read16(0x02037350 + 0x12) - 7 end
local function shot(name)
  emu:screenshot(dir .. "pc5_" .. name .. ".png")
  log:write(string.format("%s f=%d pos=%d,%d cb2=%08x avatar=%02x%s", name, f, px(), py(), emu:read32(0x030022C4), emu:read8(0x02037590), NL)); log:flush()
end
local plan = {}
local function at(fr, fn) plan[#plan + 1] = {fr, fn} end
local function tap(key, fr) at(fr, function() emu:addKey(key) end); at(fr + 4, function() emu:clearKey(key) end) end
local t = 2600
at(t, function() shot("before") end)
tap(SELECT, t + 10); at(t + 70, function() shot("popup") end)
tap(A, t + 90); at(t + 200, function() shot("pc_menu") end)
tap(B, t + 210); at(t + 290, function() shot("pc_b") end)
at(t + 400, function() shot("pc_off") end)
at(t + 420, function() emu:addKey(UP) end); at(t + 460, function() emu:clearKey(UP) end)
at(t + 500, function() shot("walk1") end)
tap(SELECT, t + 520); at(t + 580, function() shot("popup2") end)
tap(B, t + 600); at(t + 660, function() shot("cancelled") end)
at(t + 680, function() emu:addKey(DOWN) end); at(t + 720, function() emu:clearKey(DOWN) end)
at(t + 760, function() shot("walk2") end)
tap(SELECT, t + 780); at(t + 840, function() shot("popup3") end)
tap(RIGHT, t + 860); at(t + 1000, function() shot("item_used") end)
at(t + 1020, function() local fh = io.open(dir .. "pc5_done.txt", "w"); fh:write("done"); fh:close() end)
callbacks:add("frame", function()
  f = f + 1
  if f < 1900 and f % 90 == 0 then emu:addKey(START) end
  if f < 1900 and f % 90 == 5 then emu:clearKey(START) end
  if f == 2000 then emu:addKey(A) end
  if f == 2004 then emu:clearKey(A) end
  for _, p in ipairs(plan) do if f == p[1] then p[2]() end end
end)
