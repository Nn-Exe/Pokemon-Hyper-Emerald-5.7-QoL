-- Arm a hunt, then watch closely what a Pokenav call looks like while the bar is up, and chain some battles.
local dir = "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/_testrun/"
local NL = string.char(10)
local log = io.open(dir .. "call2_log.txt", "w")
local function w(s) log:write(s .. NL); log:flush() end
local A, B, SELECT, START, RIGHT, LEFT, UP, DOWN = 0, 1, 2, 3, 4, 5, 6, 7
local ST = 0x0203A660
local OVERWORLD, BATTLE = 0x08085E5D, 0x08038421
local f, holdUntil, lastLock, shots, callShots, battles, phase = 0, 0, 0, 0, 0, 0, "field"
local function cb2() return emu:read32(0x030022C4) end
local function sb1() return emu:read32(0x03005D8C) end
local function lock() return emu:read8(0x03000F2C) end
local function st()
  return string.format("species %d chain %d lv %d stars %d flags %02X win %02X",
    emu:read16(ST+2), emu:read16(ST+4), emu:read8(ST+6), emu:read8(ST+8), emu:read8(ST+9), emu:read8(ST+14))
end
local function enemy()
  local m = 0x02024744
  local iv = emu:read32(m + 0x48)
  local t, n31 = {}, 0
  for i = 0, 5 do local v = (iv >> (5*i)) & 31; t[#t+1] = tostring(v); if v == 31 then n31 = n31 + 1 end end
  local pid, ot = emu:read32(m), emu:read32(m + 4)
  return string.format("species %d lv %d IVs %s (%d perfect) ab %d %s move4 %d",
    emu:read16(m + 0x20), emu:read8(m + 0x54), table.concat(t, "/"), n31, (iv >> 31) & 1,
    ((pid ~ (pid >> 16) ~ ot ~ (ot >> 16)) & 0xFFFF) < 8 and "SHINY" or "-", emu:read16(m + 0x32))
end
local function tap(k) emu:addKey(k); holdUntil = f + 6 end
local steps = {
  {2020, function() tap(START) end}, {2080, function() tap(UP) end}, {2120, function() tap(UP) end},
  {2160, function() tap(A) end}, {2340, function() tap(DOWN) end}, {2440, function() tap(A) end},
  {2560, function() tap(B) end},
  {2700, function() w("armed " .. st()); emu:screenshot(dir .. "k_bar.png") end},
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
  local L, c = lock(), cb2()
  if L ~= lastLock then
    w(string.format("f%-6d lock %d->%d cb2 %08X %s", f, lastLock, L, c, st()))
    lastLock = L
  end
  if c == BATTLE then
    if phase ~= "battle" then
      phase = "battle"; battles = battles + 1
      w(string.format("BATTLE %d: %s", battles, enemy()))
      w("   " .. st())
      if battles <= 3 then emu:screenshot(dir .. string.format("k_battle%d.png", battles)) end
    end
    if f % 12 == 0 then emu:addKey(A) end
    if f % 12 == 5 then emu:clearKey(A) end
    return
  end
  if phase == "battle" and c == OVERWORLD then
    phase = "field"
    w(string.format("   after battle %d: %s", battles, st()))
    emu:screenshot(dir .. string.format("k_after%d.png", battles))
  end
  if L == 1 and c == OVERWORLD then                      -- a call or a message, with our bar up
    if callShots < 8 and f % 45 == 0 then
      callShots = callShots + 1
      emu:screenshot(dir .. string.format("k_call%d.png", callShots))
      w(string.format("   call shot %d at f%d, %s", callShots, f, st()))
    end
    if holdUntil == 0 and f % 26 == 0 then tap(A) end
    return
  end
  if holdUntil > 0 or c ~= OVERWORLD then return end
  local p = f % 96                                        -- left and right only: stay on this map
  if p == 0 then emu:addKey(RIGHT) elseif p == 44 then emu:clearKey(RIGHT)
  elseif p == 48 then emu:addKey(LEFT) elseif p == 92 then emu:clearKey(LEFT) end
  if f % 3000 == 0 then w(string.format("  f%-6d walking %s (battles %d)", f, st(), battles)) end
  if f == 30000 then
    w(string.format("done: %d battles, final %s", battles, st()))
    local fh = io.open(dir .. "call2_done.txt", "w"); fh:write("done"); fh:close()
  end
end)
