local dir = "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/_testrun/"
local f = 0
local A, B, SELECT, START, RIGHT, LEFT, UP, DOWN, R = 0, 1, 2, 3, 4, 5, 6, 7, 8
local log = io.open(dir .. "qb3_log.txt", "w")
local function balls()
  local p = emu:read32(0x02039DD8 + 8)
  local s = ""
  for i = 0, 5 do s = s .. emu:read16(p + i*4) .. " " end
  return "balls=" .. s .. " itemvar=" .. string.format("%04x", emu:read16(0x0203CE7C))
end
local function shot(name) emu:screenshot(dir .. "q3_" .. name .. ".png"); log:write(name .. " f=" .. f .. " " .. balls() .. "\n"); log:flush() end
local function menuReady() return emu:read32(0x03005D60) == 0x08057589 end
local function inBattle() return emu:read32(0x030022C4) == 0x08038421 end
local function finish(msg) local fh = io.open(dir .. "qb3_done.txt", "w"); fh:write(msg); fh:close() end
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
    if inBattle() then emu:clearKey(LEFT); emu:clearKey(RIGHT); battleStart = f; lastAction = f; phase = "wait1"; log:write("battle at f=" .. f .. "\n"); log:flush() end
    if f > 12000 then phase = "giveup"; finish("no battle") end
  elseif phase == "wait1" or phase == "wait2" or phase == "wait3" then
    if menuReady() and f > lastAction + 150 then
      emu:clearKey(A); m = f
      if phase == "wait1" then phase = "t1" elseif phase == "wait2" then phase = "t2" else phase = "t3" end
      shot(phase .. "_menu")
    elseif phase == "wait3" and not inBattle() and f > lastAction + 600 then
      m = f; phase = "field"; shot("field_after")
    else
      if phase == "wait1" and (f - battleStart) % 60 == 30 then emu:addKey(A) end
      if phase == "wait1" and (f - battleStart) % 60 == 34 then emu:clearKey(A) end
      if phase == "wait3" and (f - lastAction) % 60 == 30 then emu:addKey(A) end
      if phase == "wait3" and (f - lastAction) % 60 == 34 then emu:clearKey(A) end
    end
    if f > lastAction + 5000 then phase = "giveup"; shot("timeout"); finish("timeout " .. phase) end
  elseif phase == "t1" then
    local d = f - m
    if d == 10 then emu:addKey(R) end
    if d == 50 then shot("t1_peek") end
    if d == 70 then emu:clearKey(R) end
    tap(RIGHT, d, 100)                       -- cursor to Bag
    tap(A, d, 130)                           -- open bag
    if d == 300 then shot("t1_bag") end
    tap(B, d, 320)                           -- close bag
    if d == 330 then lastAction = f; phase = "wait2" end
  elseif phase == "t2" then
    local d = f - m
    tap(R, d, 10)                            -- tap = throw
    if d == 70 then shot("t2_throw") end
    if d == 80 then lastAction = f; phase = "wait3" end
  elseif phase == "t3" then
    local d = f - m
    if d == 10 then emu:addKey(R) end
    if d == 50 then shot("t3_peek"); finish("done menu") end
    if d == 70 then emu:clearKey(R) end
  elseif phase == "field" then
    local d = f - m
    tap(START, d, 30); tap(DOWN, d, 120); tap(DOWN, d, 160); tap(A, d, 200); tap(RIGHT, d, 480)
    if d == 560 then shot("field_bag_balls"); finish("done field") end
  end
end)
