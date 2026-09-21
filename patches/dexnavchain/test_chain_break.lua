-- Chain a couple of wins, then make the next battle end as "ran away" and check the chain breaks.
local dir = "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/_testrun/"
local NL = string.char(10)
local log = io.open(dir .. "break_log.txt", "w")
local function w(s) log:write(s .. NL); log:flush() end
local A, B, START, RIGHT, LEFT, UP, DOWN = 0, 1, 3, 4, 5, 6, 7
local ST, OUTCOME = 0x0203A660, 0x0202433A
local OVERWORLD, BATTLE = 0x08085E5D, 0x08038421
local f, holdUntil, battles, phase, injected, watch = 0, 0, 0, "field", false, 0
local function cb2() return emu:read32(0x030022C4) end
local function lock() return emu:read8(0x03000F2C) end
local function st()
  return string.format("chain %d flags %02X win %02X icon %02X outcome %d",
    emu:read16(ST+4), emu:read8(ST+9), emu:read8(ST+14), emu:read8(ST+18), emu:read8(OUTCOME))
end
local function tap(k) emu:addKey(k); holdUntil = f + 6 end
local steps = {
  {2020, function() tap(START) end}, {2080, function() tap(UP) end}, {2120, function() tap(UP) end},
  {2160, function() tap(A) end}, {2340, function() tap(DOWN) end}, {2440, function() tap(A) end},
  {2560, function() tap(B) end}, {2700, function() w("armed: " .. st()) end},
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
  for _, s in ipairs(steps) do if f == s[1] then s[2]() end end
  if f < 2750 then return end
  local c = cb2()
  if c == BATTLE then
    if phase ~= "battle" then phase = "battle"; battles = battles + 1
      w(string.format("battle %d starts: %s", battles, st())) end
    if f % 12 == 0 then emu:addKey(A) end
    if f % 12 == 5 then emu:clearKey(A) end
    return
  end
  if phase == "battle" and c == OVERWORLD then
    phase = "field"
    if battles >= 3 and not injected then                 -- pretend the player ran from this one
      injected = true
      emu:write8(OUTCOME, 4)
      w(string.format("battle %d ended; injected outcome 4 (ran away). before: %s", battles, st()))
      watch = f + 1
    else
      w(string.format("battle %d ended: %s", battles, st()))
    end
  end
  if watch > 0 and f >= watch and f <= watch + 240 and f % 20 == 0 then
    w(string.format("   +%3d frames: %s", f - watch, st()))
    if f == watch + 240 then
      emu:screenshot(dir .. "b_afterflee.png")
      w("done")
      local fh = io.open(dir .. "break_done.txt", "w"); fh:write("done"); fh:close()
    end
  end
  if lock() == 1 then
    if holdUntil == 0 and f % 26 == 0 then tap(A) end
    return
  end
  if holdUntil > 0 or c ~= OVERWORLD then return end
  local p = f % 96
  if p == 0 then emu:addKey(RIGHT) elseif p == 44 then emu:clearKey(RIGHT)
  elseif p == 48 then emu:addKey(LEFT) elseif p == 92 then emu:clearKey(LEFT) end
  if f == 20000 and watch == 0 then
    w("gave up waiting for 3 battles")
    local fh = io.open(dir .. "break_done.txt", "w"); fh:write("done"); fh:close()
  end
end)
