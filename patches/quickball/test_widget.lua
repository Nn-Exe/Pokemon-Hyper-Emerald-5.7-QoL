local dir = "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/_testrun/"
local f = 0
local A, B, SELECT, START, RIGHT, LEFT, UP, DOWN, R = 0, 1, 2, 3, 4, 5, 6, 7, 8
local log = io.open(dir .. "qb4_log.txt", "w")
local function shot(name) emu:screenshot(dir .. "q4_" .. name .. ".png"); log:write(name .. " f=" .. f .. "\n"); log:flush() end
local function menuReady() return emu:read32(0x03005D60) == 0x08057589 end
local function inBattle() return emu:read32(0x030022C4) == 0x08038421 end
local function finish(msg) local fh = io.open(dir .. "qb4_done.txt", "w"); fh:write(msg); fh:close() end
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
    if inBattle() then emu:clearKey(LEFT); emu:clearKey(RIGHT); battleStart = f; lastAction = f; phase = "wait1" end
    if f > 12000 then phase = "giveup"; finish("no battle") end
  elseif phase == "wait1" or phase == "wait2" or phase == "wait3" then
    if menuReady() and f > lastAction + 150 then
      emu:clearKey(A); m = f
      if phase == "wait1" then phase = "t1" elseif phase == "wait2" then phase = "t2" else phase = "t3" end
    elseif phase == "wait3" and not inBattle() and f > lastAction + 600 then
      shot("field_after"); finish("done field")
    else
      if phase ~= "wait2" and (f - lastAction) % 60 == 30 then emu:addKey(A) end
      if phase ~= "wait2" and (f - lastAction) % 60 == 34 then emu:clearKey(A) end
    end
    if f > lastAction + 5000 then phase = "giveup"; shot("timeout"); finish("timeout " .. phase) end
  elseif phase == "t1" then
    local d = f - m
    if d == 20 then shot("t1_widget") end
    if d == 30 then emu:addKey(R) end
    tap(RIGHT, d, 50)
    if d == 80 then shot("t1_cycled") end
    if d == 90 then emu:clearKey(R) end
    if d == 110 then shot("t1_released") end
    tap(RIGHT, d, 130)                       -- cursor to Bag
    if d == 150 then shot("t1_cursorbag") end
    tap(A, d, 160)
    if d == 330 then shot("t1_bag") end
    tap(B, d, 350)
    if d == 360 then lastAction = f; phase = "wait2" end
  elseif phase == "t2" then
    local d = f - m
    if d == 20 then shot("t2_back") end
    tap(R, d, 30)
    if d == 60 then shot("t2_throw") end
    if d == 200 then shot("t2_anim") end
    if d == 210 then lastAction = f; phase = "wait3" end
  elseif phase == "t3" then
    local d = f - m
    if d == 20 then shot("t3_menu"); finish("done menu") end
  end
end)
