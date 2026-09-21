-- End to end: arm a hunt and fight a run of encounters, checking what appears and how the chain counts.
local dir = "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/_testrun/"
local NL = string.char(10)
local log = io.open(dir .. "verify_log.txt", "w")
local function w(s) log:write(s .. NL); log:flush() end
local A, B, START, RIGHT, LEFT, UP, DOWN = 0, 1, 3, 4, 5, 6, 7
local ST = 0x0203A660
local OVERWORLD, BATTLE = 0x08085E5D, 0x08038421
local f, holdUntil, battles, phase, battleStart, reported = 0, 0, 0, "field", 0, false
local FLEE_AT = 0                                    -- see test_chain_break.lua for the break path
local function cb2() return emu:read32(0x030022C4) end
local function lock() return emu:read8(0x03000F2C) end
local function chain() return emu:read16(ST + 4) end
local function flags() return emu:read8(ST + 9) end
local function outcome() return emu:read8(0x0202433A) end
local function foe() return emu:read16(0x02024744 + 0x20), emu:read8(0x02024744 + 0x54) end
local function tap(k) emu:addKey(k); holdUntil = f + 6 end
local steps = {
  {2020, function() tap(START) end}, {2080, function() tap(UP) end}, {2120, function() tap(UP) end},
  {2160, function() tap(A) end}, {2340, function() tap(DOWN) end}, {2440, function() tap(A) end},
  {2560, function() tap(B) end},
  {2700, function() w(string.format("armed: species %d level %d chain %d", emu:read16(ST+2), emu:read8(ST+6), chain())) end},
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
    if phase ~= "battle" then
      phase = "battle"; battles = battles + 1; battleStart = f; reported = false
      w(string.format("battle %d starts: chain %d, flags %02X, next target lv %d",
        battles, chain(), flags(), emu:read8(ST + 6)))
    end
    if not reported and f - battleStart > 240 then
      reported = true
      local sp, lv = foe()
      w(string.format("   foe is species %d lv %d, flags %02X (bit1 set = we seeded it)", sp, lv, flags()))
    end
    if battles == FLEE_AT and f - battleStart > 260 then      -- RUN: down, right, A
      local q = (f - battleStart) % 90
      if q == 0 then tap(DOWN) elseif q == 20 then tap(RIGHT) elseif q == 40 then tap(A) end
      return
    end
    if f % 12 == 0 then emu:addKey(A) end
    if f % 12 == 5 then emu:clearKey(A) end
    return
  end
  if phase == "battle" and c == OVERWORLD then
    phase = "field"
    w(string.format("   battle %d ended, outcome %d", battles, outcome()))
  end
  if phase == "field" and battleStart > 0 and f > battleStart and f % 60 == 0 and f - battleStart < 100000 then
    if not reported then return end
  end
  if lock() == 1 then
    if holdUntil == 0 and f % 26 == 0 then tap(A) end
    return
  end
  if holdUntil > 0 or c ~= OVERWORLD then return end
  if battleStart > 0 and f == battleStart + 100000 then return end
  if f % 240 == 0 then
    w(string.format("  f%-6d field: chain %d flags %02X outcome %d next lv %d stars %d",
      f, chain(), flags(), outcome(), emu:read8(ST + 6), emu:read8(ST + 8)))
  end
  local p = f % 96
  if p == 0 then emu:addKey(RIGHT) elseif p == 44 then emu:clearKey(RIGHT)
  elseif p == 48 then emu:addKey(LEFT) elseif p == 92 then emu:clearKey(LEFT) end
  if f == 22000 then
    w(string.format("done: %d battles, chain %d", battles, chain()))
    local fh = io.open(dir .. "verify_done.txt", "w"); fh:write("done"); fh:close()
  end
end)
