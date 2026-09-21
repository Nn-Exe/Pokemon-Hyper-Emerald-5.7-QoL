-- Arm a hunt, walk off the map, walk back: the hunt should park and resume with its chain intact.
local dir = "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/_testrun/"
local NL = string.char(10)
local log = io.open(dir .. "park_log.txt", "w")
local function w(s) log:write(s .. NL); log:flush() end
local A, B, START, RIGHT, LEFT, UP, DOWN = 0, 1, 3, 4, 5, 6, 7
local ST = 0x0203A660
local OVERWORLD, BATTLE = 0x08085E5D, 0x08038421
local f, holdUntil, phase, lastMap = 0, 0, "field", ""
local function cb2() return emu:read32(0x030022C4) end
local function sb1() return emu:read32(0x03005D8C) end
local function lock() return emu:read8(0x03000F2C) end
local function map() return string.format("%d/%d", emu:read8(sb1() + 4), emu:read8(sb1() + 5)) end
local function st()
  return string.format("species %d chain %d flags %02X win %02X hunt-map %d/%d here %s",
    emu:read16(ST+2), emu:read16(ST+4), emu:read8(ST+9), emu:read8(ST+14),
    emu:read8(ST+10), emu:read8(ST+11), map())
end
local function tap(k) emu:addKey(k); holdUntil = f + 6 end
local plan = {
  {2020, function() tap(START) end}, {2080, function() tap(UP) end}, {2120, function() tap(UP) end},
  {2160, function() tap(A) end}, {2340, function() tap(DOWN) end}, {2440, function() tap(A) end},
  {2560, function() tap(B) end},
  {2700, function() w("armed: " .. st()); emu:write16(ST + 4, 7) end},   -- pretend a chain of 7
  {2760, function() w("chain forced to 7: " .. st()) end},
  {3000, function() emu:write8(ST + 10, 99); emu:write8(ST + 11, 99)
                    w("pretending we walked off the hunting ground") end},
  {3060, function() w("  60 frames later: " .. st()) end},
  {3200, function() w("  400 frames later: " .. st()); emu:screenshot(dir .. "p_parked.png") end},
  {3400, function() emu:write8(ST + 10, emu:read8(sb1() + 4)); emu:write8(ST + 11, emu:read8(sb1() + 5))
                    w("back on the hunting ground") end},
  {3520, function() w("  after coming back: " .. st()); emu:screenshot(dir .. "p_resumed.png") end},
}
callbacks:add("frame", function()
  f = f + 1
  if holdUntil > 0 and f == holdUntil then for k = 0, 9 do emu:clearKey(k) end; holdUntil = 0 end
  if f < 1900 then
    if f % 90 == 0 then emu:addKey(START) end
    if f % 90 == 5 then emu:clearKey(START) end
    if f == 1800 then emu:addKey(A) end
    if f == 1804 then emu:clearKey(A) end
    return
  end
  for _, s in ipairs(plan) do if f == s[1] then s[2]() end end
  if f < 2800 then return end
  local c = cb2()
  if c == BATTLE then                                   -- get out of battles quickly, they are not the point
    if f % 12 == 0 then emu:addKey(A) end
    if f % 12 == 5 then emu:clearKey(A) end
    return
  end
  if lock() == 1 then
    if holdUntil == 0 and f % 26 == 0 then tap(A) end
    return
  end
  if c ~= OVERWORLD then return end
  local m = map()
  if m ~= lastMap then
    w(string.format("f%-6d map is now %s | %s", f, m, st()))
    lastMap = m
    emu:screenshot(dir .. "p_map_" .. m:gsub("/", "_") .. "_" .. f .. ".png")
  end
  if holdUntil > 0 then return end
  -- first walk one way to leave the map, then back again
  if f < 9000 then
    if f % 60 < 50 then emu:addKey(RIGHT) else emu:clearKey(RIGHT) end
  else
    emu:clearKey(RIGHT)
    if f % 60 < 50 then emu:addKey(LEFT) else emu:clearKey(LEFT) end
  end
  if f % 600 == 0 then w(string.format("  f%-6d %s", f, st())) end
  if f == 4200 then
    w("done: " .. st())
    local fh = io.open(dir .. "park_done.txt", "w"); fh:write("done"); fh:close()
  end
end)
