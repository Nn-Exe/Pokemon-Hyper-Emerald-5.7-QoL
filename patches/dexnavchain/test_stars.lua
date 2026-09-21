-- Hold the chain and the star rating high from outside, so the rare branches (perfect IVs, egg moves,
-- extra shiny rerolls) run on every encounter and can be checked.
local dir = "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/_testrun/"
local NL = string.char(10)
local log = io.open(dir .. "forced_log.txt", "w")
local function w(s) log:write(s .. NL); log:flush() end
local A, B, START, RIGHT, LEFT = 0, 1, 3, 4, 5
local ST = 0x0203A660
local OVERWORLD, BATTLE = 0x08085E5D, 0x08038421
local f, holdUntil, battles, phase, sampled = 0, 0, 0, "field", false
local function cb2() return emu:read32(0x030022C4) end
local function lock() return emu:read8(0x03000F2C) end
local function mon()
  local m = 0x02024744
  local iv = emu:read32(m + 0x48)
  local t, n31 = {}, 0
  for i = 0, 5 do local v = (iv >> (5*i)) & 31; t[#t+1] = tostring(v); if v == 31 then n31 = n31 + 1 end end
  local pid, ot = emu:read32(m), emu:read32(m + 4)
  return string.format("species %d lv %2d IVs %-17s %d perfect, ability %d, %s, moves %d/%d/%d/%d",
    emu:read16(m + 0x20), emu:read8(m + 0x54), table.concat(t, "/"), n31, (iv >> 31) & 1,
    ((pid ~ (pid >> 16) ~ ot ~ (ot >> 16)) & 0xFFFF) < 8 and "SHINY" or "not shiny",
    emu:read16(m+0x2C), emu:read16(m+0x2E), emu:read16(m+0x30), emu:read16(m+0x32))
end
local function tap(k) emu:addKey(k); holdUntil = f + 6 end
local steps = {
  {2020, function() tap(START) end}, {2080, function() tap(6) end}, {2120, function() tap(6) end},
  {2160, function() tap(A) end}, {2340, function() tap(7) end}, {2440, function() tap(A) end},
  {2560, function() tap(B) end},
  {2700, function() w("armed; forcing chain 30 / 3 stars from here on") end},
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
  -- keep the hunt at chain 30 with three stars promised, while we are out on the field
  if c == OVERWORLD and emu:read16(ST + 2) ~= 0 then
    emu:write16(ST + 4, 30)
    emu:write8(ST + 8, 3)
  end
  if c == BATTLE then
    if phase ~= "battle" then phase = "battle"; battles = battles + 1; sampled = false
      w(string.format("battle %d starts: %s", battles, mon())) end
    if not sampled and f % 4 == 0 and emu:read16(0x02024744 + 0x20) ~= 0 then
      -- sample again once the battle is properly up, in case the first read caught the transition
      if battles > 0 and emu:read8(0x02024744 + 0x54) > 0 then
        sampled = true
        w(string.format("   settled:        %s", mon()))
      end
    end
    if f % 12 == 0 then emu:addKey(A) end
    if f % 12 == 5 then emu:clearKey(A) end
    return
  end
  if phase == "battle" and c == OVERWORLD then phase = "field" end
  if lock() == 1 then
    if holdUntil == 0 and f % 26 == 0 then tap(A) end
    return
  end
  if holdUntil > 0 or c ~= OVERWORLD then return end
  local p = f % 96
  if p == 0 then emu:addKey(RIGHT) elseif p == 44 then emu:clearKey(RIGHT)
  elseif p == 48 then emu:addKey(LEFT) elseif p == 92 then emu:clearKey(LEFT) end
  if f == 20000 then
    w(string.format("done: %d battles", battles))
    local fh = io.open(dir .. "forced_done.txt", "w"); fh:write("done"); fh:close()
  end
end)
