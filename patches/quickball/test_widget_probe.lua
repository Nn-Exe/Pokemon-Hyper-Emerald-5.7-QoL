local dir = "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/_testrun/"
local f = 0
local A, B, SELECT, START, RIGHT, LEFT, UP, DOWN, R = 0, 1, 2, 3, 4, 5, 6, 7, 8
local log = io.open(dir .. "qb5_log.txt", "w")
local MYCB = 0x08FD947D
local function shot(name) emu:screenshot(dir .. "q5_" .. name .. ".png"); log:write(name .. " f=" .. f .. "\n"); log:flush() end
local function dumpSprites(tag)
  for i = 0, 63 do
    local s = 0x02020630 + i*0x44
    local fl = emu:read8(s + 0x3E)
    if fl % 2 == 1 and emu:read32(s + 0x1C) == MYCB then
      log:write(string.format("%s sprite %d oam=%04x %04x %04x x=%d y=%d\n", tag, i, emu:read16(s), emu:read16(s+2), emu:read16(s+4), emu:read16(s+0x20), emu:read16(s+0x22)))
    end
  end
  log:flush()
end
local function dumpVram()
  local v = ""
  for i = 0, 63 do v = v .. string.format("%02x", emu:read8(0x06010000 + 0x141*32 + i)) end
  local v2 = ""
  for i = 0, 31 do v2 = v2 .. string.format("%02x", emu:read8(0x06010000 + 0x151*32 + i)) end
  local p = ""
  for i = 0, 15 do p = p .. string.format("%04x ", emu:read16(0x05000200 + 10*32 + i*2)) end
  local q = ""
  for i = 0, 15 do q = q .. string.format("%04x ", emu:read16(0x05000200 + 11*32 + i*2)) end
  log:write("tile141=" .. v .. "\n"); log:write("tile151=" .. v2 .. "\n")
  log:write("pal10=" .. p .. "\n"); log:write("pal11=" .. q .. "\n"); log:flush()
end
local function menuReady() return emu:read32(0x03005D60) == 0x08057589 end
local function inBattle() return emu:read32(0x030022C4) == 0x08038421 end
local function finish(msg) local fh = io.open(dir .. "qb5_done.txt", "w"); fh:write(msg); fh:close() end
local battleStart, phase, m, lastAction = nil, "walk", nil, 0
callbacks:add("frame", function()
  f = f + 1
  if f < 1900 and f % 90 == 0 then emu:addKey(START) end
  if f < 1900 and f % 90 == 5 then emu:clearKey(START) end
  if f == 2000 then emu:addKey(A) end
  if f == 2004 then emu:clearKey(A) end
  if phase == "walk" and f > 2600 then
    local k = math.floor((f - 2600) / 40) % 2
    if k == 0 then emu:clearKey(RIGHT); emu:addKey(LEFT) else emu:clearKey(LEFT); emu:addKey(RIGHT) end
    if inBattle() then emu:clearKey(LEFT); emu:clearKey(RIGHT); battleStart = f; lastAction = f; phase = "wait1" end
    if f > 12000 then phase = "giveup"; finish("no battle") end
  elseif phase == "wait1" then
    if menuReady() and f > lastAction + 150 then emu:clearKey(A); m = f; phase = "t1"
    else
      if (f - lastAction) % 60 == 30 then emu:addKey(A) end
      if (f - lastAction) % 60 == 34 then emu:clearKey(A) end
    end
    if f > lastAction + 5000 then phase = "giveup"; shot("timeout"); finish("timeout") end
  elseif phase == "t1" then
    local d = f - m
    if d == 20 then shot("t1_widget"); dumpSprites("menu"); dumpVram(); finish("done") end
  end
end)
