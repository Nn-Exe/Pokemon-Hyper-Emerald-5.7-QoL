-- Effectiveness indicator test: wild battle -> Fight -> screenshot the move list on each of the four moves.
local dir = "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/_testrun/"
local f = 0
local A, B, SELECT, START, RIGHT, LEFT, UP, DOWN = 0, 1, 2, 3, 4, 5, 6, 7
local NL = string.char(10)
local log = io.open(dir .. "te_log.txt", "w")
local phase, battleStart, lastAction, t0 = "walk", nil, 0, nil
local function menuReady() return emu:read32(0x03005D60) == 0x08057589 end
local function str()                       -- gDisplayedStringBattle, decoded roughly
  local s, a = "", 0x02022E2C
  for i = 0, 40 do
    local c = emu:read8(a + i)
    if c == 0xFF then break end
    if c >= 0xBB and c <= 0xD4 then s = s .. string.char(65 + c - 0xBB)
    elseif c >= 0xD5 and c <= 0xEE then s = s .. string.char(97 + c - 0xD5)
    elseif c >= 0xA1 and c <= 0xAA then s = s .. string.char(48 + c - 0xA1)
    elseif c == 0xB9 then s = s .. "x" elseif c == 0xAD then s = s .. "."
    elseif c == 0xBA then s = s .. "/" elseif c == 0x00 then s = s .. " "
    else s = s .. string.format("{%02X}", c) end
  end
  return s
end
local function windows()
  for w = 5, 11 do
    local b = 0x02020004 + w * 12
    log:write(string.format("win %2d: bg=%d left=%d top=%d w=%d h=%d pal=%d base=%d", w, emu:read8(b), emu:read8(b+1),
      emu:read8(b+2), emu:read8(b+3), emu:read8(b+4), emu:read8(b+5), emu:read16(b+6)) .. NL)
  end
  log:flush()
end
local function pals()
  windows()
  for pal = 0, 15 do
    local t = string.format("bgpal %2d:", pal)
    for c = 0, 15 do t = t .. string.format(" %04x", emu:read16(0x05000000 + pal * 32 + c * 2)) end
    log:write(t .. NL)
  end
  log:flush()
end
local function shot(tag)
  emu:screenshot(dir .. "te_" .. tag .. ".png")
  if tag == "move1" then pals() end
  log:write(string.format("%s: cursor=%d str=%q  opp types %d/%d", tag, emu:read8(0x020244B0),
    str(), emu:read8(0x02024084 + 0x58 + 0x21), emu:read8(0x02024084 + 0x58 + 0x22)) .. NL); log:flush()
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
    end
    if f > 12000 then local fh = io.open(dir .. "te_done.txt", "w"); fh:write("no battle"); fh:close(); phase = "over" end
  elseif phase == "wait" then
    if menuReady() and f > lastAction + 150 then emu:clearKey(A); t0 = f; phase = "test"
    else
      if (f - battleStart) % 60 == 30 then emu:addKey(A) end
      if (f - battleStart) % 60 == 34 then emu:clearKey(A) end
      if f > lastAction + 4000 then local fh = io.open(dir .. "te_done.txt", "w"); fh:write("timeout"); fh:close(); phase = "over" end
    end
  elseif phase == "test" then
    local d = f - t0
    if d == 10 then emu:addKey(A) end                 -- Fight
    if d == 14 then emu:clearKey(A) end
    if d == 90 then shot("move1") end
    if d == 110 then emu:addKey(RIGHT) end
    if d == 114 then emu:clearKey(RIGHT) end
    if d == 160 then shot("move2") end
    if d == 180 then emu:addKey(DOWN) end
    if d == 184 then emu:clearKey(DOWN) end
    if d == 230 then shot("move4") end
    if d == 250 then emu:addKey(LEFT) end
    if d == 254 then emu:clearKey(LEFT) end
    if d == 300 then shot("move3") end
    if d == 320 then local fh = io.open(dir .. "te_done.txt", "w"); fh:write("done"); fh:close(); phase = "over" end
  end
end)
