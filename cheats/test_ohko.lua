local dir = "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/_testrun/"
local f = 0
local A, B, SELECT, START, RIGHT, LEFT, UP, DOWN, R = 0, 1, 2, 3, 4, 5, 6, 7, 8
local log = io.open(dir .. "ohko1_log.txt", "w")
local function menuReady() return emu:read32(0x03005D60) == 0x08057589 end
local function inBattle() return emu:read32(0x030022C4) == 0x08038421 end
local function mons()
  local b0, b1 = 0x02024084, 0x02024084 + 0x58
  return string.format("me: sp=%d atk=%d spd=%d spa=%d hp=%d/%d | foe: sp=%d lv=%d hp=%d/%d",
    emu:read16(b0), emu:read16(b0+2), emu:read16(b0+6), emu:read16(b0+8), emu:read16(b0+0x28), emu:read16(b0+0x2C),
    emu:read16(b1), emu:read8(b1+0x2A), emu:read16(b1+0x28), emu:read16(b1+0x2C))
end
local function shot(name) emu:screenshot(dir .. "ok_" .. name .. ".png"); log:write(name .. " f=" .. f .. " " .. mons() .. "\n"); log:flush() end
local function finish(msg) local fh = io.open(dir .. "ohko1_done.txt", "w"); fh:write(msg); fh:close() end
local battleStart, phase, m, lastAction = nil, "walk", nil, 0
local function tap(key, d, at) if d == at then emu:addKey(key) end; if d == at + 4 then emu:clearKey(key) end end
callbacks:add("frame", function()
  f = f + 1
  if f < 1900 and f % 90 == 0 then emu:addKey(START) end
  if f < 1900 and f % 90 == 5 then emu:clearKey(START) end
  if f == 2000 then emu:addKey(A) end
  if f == 2004 then emu:clearKey(A) end
  if phase == "walk" and f > 2600 then
    local k = math.floor((f - 2600) / 40) % 2
    if k == 0 then emu:clearKey(RIGHT); emu:addKey(LEFT) else emu:clearKey(LEFT); emu:addKey(RIGHT) end
    if inBattle() then emu:clearKey(LEFT); emu:clearKey(RIGHT); battleStart = f; lastAction = f; phase = "wait" end
    if f > 12000 then phase = "giveup"; finish("no battle") end
  elseif phase == "wait" then
    if menuReady() and f > lastAction + 150 then emu:clearKey(A); m = f; phase = "fight"; shot("menu")
    else
      if (f - lastAction) % 60 == 30 then emu:addKey(A) end
      if (f - lastAction) % 60 == 34 then emu:clearKey(A) end
    end
    if f > lastAction + 5000 then phase = "giveup"; shot("timeout"); finish("timeout") end
  elseif phase == "fight" then
    local d = f - m
    tap(A, d, 10)                 -- Fight
    tap(A, d, 70)                 -- first move
    if d == 140 then shot("attack") end
    if d == 260 then shot("hit") end
    if d == 400 then shot("after") end
    if d == 600 then shot("later") end
    if d == 900 then shot("end"); finish("done") end
  end
end)
