-- Find the hack's type-effectiveness code: in a wild battle, watch reads of the opponent's type bytes
-- (gBattleMons[1] + 0x21/0x22) while a move resolves, and log the PC of every reader.
local dir = "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/_testrun/"
local f = 0
local A, B, SELECT, START, RIGHT, LEFT, UP, DOWN = 0, 1, 2, 3, 4, 5, 6, 7
local NL = string.char(10)
local log = io.open(dir .. "tc_log.txt", "w")
local phase, battleStart, lastAction, t0 = "walk", nil, 0, nil
local function menuReady() return emu:read32(0x03005D60) == 0x08057589 end
local TYPE1 = 0x02024084 + 0x58 + 0x21
local hits, order = {}, {}
local armed = false

local function arm()
  local function cb()
    local pc = 0
    pcall(function() pc = emu:readRegister("pc") end)
    local k = string.format("%08x", pc)
    if not hits[k] then hits[k] = 0; order[#order + 1] = k end
    hits[k] = hits[k] + 1
  end
  local forms = {
    function() return emu:setWatchpoint(cb, TYPE1, 2) end,
    function() return emu:setWatchpoint(cb, TYPE1) end,
    function() return emu:setWatchpoint(TYPE1, 2, cb) end,
  }
  for i, fn in ipairs(forms) do
    local ok, err = pcall(fn)
    log:write(string.format("watchpoint form %d: ok=%s err=%s", i, tostring(ok), tostring(err)) .. NL); log:flush()
    if ok then armed = true; return true end
  end
  return false
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
    if f > 12000 then local fh = io.open(dir .. "tc_done.txt", "w"); fh:write("no battle"); fh:close(); phase = "over" end
  elseif phase == "wait" then
    if menuReady() and f > lastAction + 150 then
      emu:clearKey(A); t0 = f; phase = "test"
      log:write(string.format("battle menu at f=%d; opponent types %d/%d", f, emu:read8(TYPE1), emu:read8(TYPE1 + 1)) .. NL)
      arm()
    else
      if (f - battleStart) % 60 == 30 then emu:addKey(A) end
      if (f - battleStart) % 60 == 34 then emu:clearKey(A) end
      if f > lastAction + 4000 then local fh = io.open(dir .. "tc_done.txt", "w"); fh:write("timeout"); fh:close(); phase = "over" end
    end
  elseif phase == "test" then
    local d = f - t0
    if d == 10 then emu:addKey(A) end
    if d == 14 then emu:clearKey(A) end
    if d == 60 then emu:addKey(A) end
    if d == 64 then emu:clearKey(A) end
    if d == 500 then
      log:write("armed=" .. tostring(armed) .. " distinct readers: " .. #order .. NL)
      for _, k in ipairs(order) do log:write(string.format("  pc %s  x%d", k, hits[k]) .. NL) end
      log:flush()
      emu:screenshot(dir .. "tc_after.png")
      local fh = io.open(dir .. "tc_done.txt", "w"); fh:write("done"); fh:close(); phase = "over"
    end
  end
end)
