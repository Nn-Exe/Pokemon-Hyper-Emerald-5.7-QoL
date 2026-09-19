-- DexNav Safari test: switch FLAG_SYS_SAFARI_MODE (0x88C) on in the save block so START builds the Safari
-- menu (Retire, Dex, Party, Bag, Player, Option, DexNav, Exit), open DexNav from it, page, leave, clear the
-- flag, and walk.
local dir = "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/_testrun/"
local f = 0
local A, B, SELECT, START, RIGHT, LEFT, UP, DOWN = 0, 1, 2, 3, 4, 5, 6, 7
local NL = string.char(10)
local log = io.open(dir .. "dns_log.txt", "w")
local function flagAddr() return emu:read32(0x03005D8C) + 0x1270 + 0x111 end   -- flag 0x88C -> bit 4
local function setSafari(on)
  local a = flagAddr(); local v = emu:read8(a)
  if on then v = v | 0x10 else v = v & 0xEF end
  emu:write8(a, v)
  log:write(string.format("safari flag byte @%08x = %02x", a, emu:read8(a)) .. NL); log:flush()
end
local function px() return emu:read16(0x02037350 + 0x10) - 7 end
local function py() return emu:read16(0x02037350 + 0x12) - 7 end
local function shot(name)
  emu:screenshot(dir .. "dns_" .. name .. ".png")
  log:write(string.format("%s f=%d pos=%d,%d cb2=%08x menucount=%d%s", name, f, px(), py(),
    emu:read32(0x030022C4), emu:read8(0x0203760F), NL)); log:flush()
end
local plan = {}
local function at(fr, fn) plan[#plan + 1] = {fr, fn} end
local function tap(key, fr) at(fr, function() emu:addKey(key) end); at(fr + 4, function() emu:clearKey(key) end) end
local t = 2600
at(t, function() setSafari(true) end)
at(t + 4, function() shot("flagset") end)
tap(START, t + 10); at(t + 30, function() shot("after_start") end); at(t + 70, function() shot("safarimenu") end)
for i = 0, 5 do tap(DOWN, t + 90 + i * 12) end
at(t + 180, function() shot("cursor") end)
tap(A, t + 190); at(t + 300, function() shot("dexnav_p1") end)
tap(RIGHT, t + 320); at(t + 360, function() shot("dexnav_p2") end)
tap(B, t + 380); at(t + 500, function() shot("safarimenu_again") end)
tap(B, t + 520); at(t + 580, function() shot("field") end)
at(t + 590, function() setSafari(false) end)
at(t + 600, function() emu:addKey(UP) end); at(t + 640, function() emu:clearKey(UP) end)
at(t + 700, function() shot("walked") end)
at(t + 720, function() local fh = io.open(dir .. "dns_done.txt", "w"); fh:write("done"); fh:close() end)
callbacks:add("frame", function()
  f = f + 1
  if f < 1900 and f % 90 == 0 then emu:addKey(START) end
  if f < 1900 and f % 90 == 5 then emu:clearKey(START) end
  if f == 2000 then emu:addKey(A) end
  if f == 2004 then emu:clearKey(A) end
  for _, p in ipairs(plan) do if f == p[1] then p[2]() end end
end)
