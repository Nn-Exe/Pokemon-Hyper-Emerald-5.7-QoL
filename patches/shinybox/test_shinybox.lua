-- shinybox test: start a wild battle, screenshot the normal box, force the opponent's battle copy to be
-- shiny (otId = personality -> shiny value 0), screenshot again, and log the healthbox sprite palettes.
local dir = "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/_testrun/"
local f = 0
local A, B, SELECT, START, RIGHT, LEFT, UP, DOWN, R = 0, 1, 2, 3, 4, 5, 6, 7, 8
local NL = string.char(10)
local log = io.open(dir .. "sb_log.txt", "w")
local phase, battleStart, lastAction, t0 = "walk", nil, 0, nil
local function menuReady() return emu:read32(0x03005D60) == 0x08057589 end

local function boxes(tag)
  for i = 0, 63 do
    local s = 0x02020630 + i * 0x44
    local flags = emu:read16(s + 0x3E)
    local cb = emu:read32(s + 0x1C)
    if flags % 2 == 1 and cb == 0x08007429 then
      local a2 = emu:read16(s + 4)
      log:write(string.format("%s spr %2d pal=%2d battler=%d right=%d", tag, i, math.floor(a2 / 4096),
        emu:read16(s + 0x3A), emu:read16(s + 0x38)) .. NL)
    end
  end
  local t = tag .. " tags:"
  for i = 8, 15 do t = t .. string.format(" %d:%04x", i, emu:read16(0x03000CF0 + i * 2)) end
  log:write(t .. NL)
  for p = 10, 15 do
    local s = string.format("%s objpal %2d:", tag, p)
    for c = 0, 15 do s = s .. string.format(" %04x", emu:read16(0x05000200 + p * 32 + c * 2)) end
    log:write(s .. NL)
  end
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
      local fh = io.open(dir .. "sb_done.txt", "w"); fh:write("no battle"); fh:close(); phase = "over"
    end
  elseif phase == "wait" then
    if menuReady() and f > lastAction + 150 then
      emu:clearKey(A); t0 = f; phase = "test"
      emu:screenshot(dir .. "sb_normal.png")
      boxes("normal")
    else
      if (f - battleStart) % 60 == 30 then emu:addKey(A) end
      if (f - battleStart) % 60 == 34 then emu:clearKey(A) end
      if f > lastAction + 4000 then
        local fh = io.open(dir .. "sb_done.txt", "w"); fh:write("timeout"); fh:close(); phase = "over"
      end
    end
  elseif phase == "test" then
    local d = f - t0
    if d == 10 then
      local mon = 0x02024084 + 0x58
      local pid = emu:read32(mon + 0x48)
      emu:write32(mon + 0x54, pid)                       -- otId = personality -> shiny
      log:write(string.format("forced shiny: pid=%08x otid=%08x", pid, emu:read32(mon + 0x54)) .. NL)
    elseif d == 40 then
      emu:screenshot(dir .. "sb_shiny.png"); boxes("shiny")
    elseif d == 100 then
      emu:screenshot(dir .. "sb_shiny2.png"); boxes("shiny2")
      local fh = io.open(dir .. "sb_done.txt", "w"); fh:write("done"); fh:close(); phase = "over"
    end
  end
end)
