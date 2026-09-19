-- Type badge test: wild battle -> screenshot at the action menu, then after a move (switch of turn), and
-- dump sprites so the two badges (16x16, data[7] = 0/1) can be seen in the log.
local dir = "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/_testrun/"
local f = 0
local A, B, SELECT, START, RIGHT, LEFT, UP, DOWN = 0, 1, 2, 3, 4, 5, 6, 7
local NL = string.char(10)
local log = io.open(dir .. "ti_log.txt", "w")
local phase, battleStart, lastAction, t0 = "walk", nil, 0, nil
local function menuReady() return emu:read32(0x03005D60) == 0x08057589 end
local function dump(tag)
  emu:screenshot(dir .. "ti_" .. tag .. ".png")
  local n = 0
  for i = 0, 63 do
    local s = 0x02020630 + i * 0x44
    if emu:read16(s + 0x3E) % 2 == 1 then
      n = n + 1
      local a0, a1, a2 = emu:read16(s), emu:read16(s + 2), emu:read16(s + 4)
      log:write(string.format("%s spr %2d y=%3d x=%3d pal=%2d tile=%4d flags=%04x data0=%d d6=%d d7=%d cb=%08x", tag, i,
        a0 % 256, a1 % 512, math.floor(a2 / 4096), a2 % 1024, emu:read16(s + 0x3E), emu:read16(s + 0x2E),
        emu:read16(s + 0x3A), emu:read16(s + 0x3C), emu:read32(s + 0x1C)) .. NL)
    end
  end
  local t = tag .. " paltags:"
  for i = 0, 15 do t = t .. string.format(" %d:%04x", i, emu:read16(0x03000CF0 + i * 2)) end
  log:write(string.format("%s sprites=%d mon1 types=%d/%d", tag, n, emu:read8(0x02024084 + 0x58 + 0x21),
    emu:read8(0x02024084 + 0x58 + 0x22)) .. NL .. t .. NL); log:flush()
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
    if f > 12000 then local fh = io.open(dir .. "ti_done.txt", "w"); fh:write("no battle"); fh:close(); phase = "over" end
  elseif phase == "wait" then
    if battleStart and f == battleStart + 90 then emu:screenshot(dir .. "ti_intro.png") end
    if menuReady() and f > lastAction + 150 then
      emu:clearKey(A); t0 = f; phase = "test"; dump("menu")
    else
      if (f - battleStart) % 60 == 30 then emu:addKey(A) end
      if (f - battleStart) % 60 == 34 then emu:clearKey(A) end
      if f > lastAction + 4000 then local fh = io.open(dir .. "ti_done.txt", "w"); fh:write("timeout"); fh:close(); phase = "over" end
    end
  elseif phase == "test" then
    local d = f - t0
    if d == 10 then emu:addKey(A) end                       -- Fight
    if d == 14 then emu:clearKey(A) end
    if d == 60 then emu:addKey(A) end                       -- first move
    if d == 64 then emu:clearKey(A) end
    if d == 400 then dump("after_turn") end
    if d == 420 then local fh = io.open(dir .. "ti_done.txt", "w"); fh:write("done"); fh:close(); phase = "over" end
  end
end)
