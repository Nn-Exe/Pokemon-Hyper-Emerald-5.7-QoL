-- Probe 2: in a wild battle, dump gSprites entries (candidate bases), OAM, and search IWRAM for palette tags.
local dir = "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/_testrun/"
local f = 0
local A, B, SELECT, START, RIGHT, LEFT, UP, DOWN, R = 0, 1, 2, 3, 4, 5, 6, 7, 8
local NL = string.char(10)
local log = io.open(dir .. "shiny2_log.txt", "w")
local phase, battleStart, lastAction = "walk", nil, 0
local function menuReady() return emu:read32(0x03005D60) == 0x08057589 end

local function dumpOAM()
  log:write("== OAM entries with palette 4 or 5 ==" .. NL)
  for i = 0, 127 do
    local a0 = emu:read16(0x07000000 + i * 8)
    local a1 = emu:read16(0x07000000 + i * 8 + 2)
    local a2 = emu:read16(0x07000000 + i * 8 + 4)
    local pal = math.floor(a2 / 4096)
    if pal == 4 or pal == 5 then
      log:write(string.format("oam %3d y=%3d x=%3d tile=%4d pal=%2d  a0=%04x a1=%04x a2=%04x", i,
        a0 % 256, a1 % 512, a2 % 1024, pal, a0, a1, a2) .. NL)
    end
  end
end

local function dumpSprites(base)
  log:write(string.format("== gSprites candidate %08x ==", base) .. NL)
  for i = 0, 63 do
    local s = base + i * 0x44
    local a0 = emu:read16(s)
    local a1 = emu:read16(s + 2)
    local a2 = emu:read16(s + 4)
    local cb = emu:read32(s + 0x1C)
    local pal = math.floor(a2 / 4096)
    local inuse = emu:read8(s + 0x3E)
    if cb >= 0x08000000 and cb < 0x0A000000 then
      local d = ""
      for k = 0, 7 do d = d .. string.format(" %04x", emu:read16(s + 0x2E + k * 2)) end
      log:write(string.format("spr %2d y=%3d x=%3d pal=%2d tile=%4d cb=%08x flags=%02x data:%s", i,
        a0 % 256, a1 % 512, pal, a2 % 1024, cb, inuse, d) .. NL)
    end
  end
end

local function dump()
  dumpOAM()
  dumpSprites(0x02020630)
  log:write("== IWRAM search for D6FF / D704 ==" .. NL)
  local a = 0x03000000
  while a < 0x03008000 do
    local v = emu:read16(a)
    if v == 0xD6FF or v == 0xD704 then
      local s = string.format("%08x = %04x  neighbours:", a, v)
      for i = -16, 16 do s = s .. string.format(" %04x", emu:read16(a + i * 2)) end
      log:write(s .. NL)
    end
    a = a + 2
  end
  log:write("== enemy mon @02024744: pid/otid ==" .. NL)
  log:write(string.format("pid=%08x otid=%08x", emu:read32(0x02024744), emu:read32(0x02024744 + 4)) .. NL)
  log:write("== done ==" .. NL)
  log:flush()
end

callbacks:add("frame", function()
  f = f + 1
  if f < 1900 and f % 90 == 0 then emu:addKey(START) end
  if f < 1900 and f % 90 == 5 then emu:clearKey(START) end
  if f == 2000 then emu:addKey(A) end
  if f == 2004 then emu:clearKey(A) end
  if phase == "walk" and f > 2600 then
    local k = math.floor((f - 2600) / 40) % 2
    if k == 0 then emu:clearKey(RIGHT); emu:addKey(LEFT) else emu:clearKey(LEFT); emu:addKey(RIGHT) end
    if emu:read32(0x030022C4) == 0x08038421 then
      emu:clearKey(LEFT); emu:clearKey(RIGHT); battleStart = f; lastAction = f; phase = "wait"
      log:write("battle at f=" .. f .. NL); log:flush()
    end
    if f > 12000 then
      local fh = io.open(dir .. "shiny2_done.txt", "w"); fh:write("no battle"); fh:close(); phase = "over"
    end
  elseif phase == "wait" then
    if menuReady() and f > lastAction + 150 then
      emu:clearKey(A)
      emu:screenshot(dir .. "shiny2_battle.png")
      dump()
      local fh = io.open(dir .. "shiny2_done.txt", "w"); fh:write("done"); fh:close()
      phase = "over"
    else
      if (f - battleStart) % 60 == 30 then emu:addKey(A) end
      if (f - battleStart) % 60 == 34 then emu:clearKey(A) end
      if f > lastAction + 4000 then
        local fh = io.open(dir .. "shiny2_done.txt", "w"); fh:write("timeout"); fh:close(); phase = "over"
      end
    end
  end
end)
