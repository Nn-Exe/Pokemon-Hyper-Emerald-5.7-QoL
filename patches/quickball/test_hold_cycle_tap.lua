local dir = "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/_testrun/"
local f = 0
local A, B, SELECT, START, RIGHT, LEFT, UP, DOWN, R = 0, 1, 2, 3, 4, 5, 6, 7, 8
local log = io.open(dir .. "qb2_log.txt", "w")
local function balls()
  local p = emu:read32(0x02039DD8 + 8)
  local s = ""
  for i = 0, 5 do s = s .. emu:read16(p + i*4) .. " " end
  return "balls=" .. s .. " itemvar=" .. string.format("%04x", emu:read16(0x0203CE7C))
end
local function shot(name) emu:screenshot(dir .. "q2_" .. name .. ".png"); log:write(name .. " f=" .. f .. " " .. balls() .. "\n"); log:flush() end
local function menuReady() return emu:read32(0x03005D60) == 0x08057589 end
local battleStart, phase, m, step = nil, "walk", nil, 1
-- each step: list of {offset, fn}
local steps = {
  { {10, function() emu:addKey(R) end},          -- long hold (60 frames) -> peek only
    {40, function() shot("s1_peek") end},
    {70, function() emu:clearKey(R) end},
    {90, function() shot("s1_nothrow") end},
    {110, function() emu:addKey(R) end},         -- hold + RIGHT -> cycle, no throw
    {130, function() emu:addKey(RIGHT) end}, {134, function() emu:clearKey(RIGHT) end},
    {150, function() shot("s1_cycled") end},
    {170, function() emu:clearKey(R) end},
    {190, function() shot("s1_restored") end},
    {210, function() emu:addKey(R) end}, {214, function() emu:clearKey(R) end},  -- tap -> throw
    {260, function() shot("s1_throw") end},
    {261, function() step = 2; phase = "wait" end} },
  { {10, function() emu:addKey(R) end},          -- peek: count should be one less
    {40, function() shot("s2_peek") end},
    {70, function() emu:clearKey(R) end},
    {100, function() emu:addKey(RIGHT) end}, {104, function() emu:clearKey(RIGHT) end}, -- cursor -> Bag
    {120, function() emu:addKey(A) end}, {124, function() emu:clearKey(A) end},
    {260, function() shot("s2_bag") end},
    {280, function() emu:addKey(B) end}, {284, function() emu:clearKey(B) end},
    {480, function() shot("s2_back") end},
    {481, function() local fh = io.open(dir .. "qb2_done.txt", "w"); fh:write("done"); fh:close() end} },
}
local lastAction = 0
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
      log:write("battle at f=" .. f .. "\n"); log:flush()
    end
    if f > 12000 then phase = "giveup"; local fh = io.open(dir .. "qb2_done.txt", "w"); fh:write("no battle"); fh:close() end
  elseif phase == "wait" then
    if menuReady() and f > lastAction + 150 then
      emu:clearKey(A); m = f; phase = "test"; shot("menu" .. step)
    else
      if (f - battleStart) % 60 == 30 then emu:addKey(A) end
      if (f - battleStart) % 60 == 34 then emu:clearKey(A) end
    end
    if f > lastAction + 4000 then phase = "giveup"; shot("timeout"); local fh = io.open(dir .. "qb2_done.txt", "w"); fh:write("timeout"); fh:close() end
  elseif phase == "test" then
    local d = f - m
    for _, s in ipairs(steps[step]) do
      if d == s[1] then s[2](); lastAction = f end
    end
  end
end)
