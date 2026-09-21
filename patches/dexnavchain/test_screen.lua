local dir = "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/_testrun/"
local NL = string.char(10)
local log = io.open(dir .. "visual_log.txt", "w")
local function w(s) log:write(s .. NL); log:flush() end
local A, B, START, RIGHT, LEFT, UP, DOWN = 0, 1, 3, 4, 5, 6, 7
local ST = 0x0203A660
local OVERWORLD, BATTLE = 0x08085E5D, 0x08038421
local f, holdUntil, battles, phase, bstart = 0, 0, 0, "field", 0
local function cb2() return emu:read32(0x030022C4) end
local function lock() return emu:read8(0x03000F2C) end
local function st()
  return string.format("species %d chain %d lv %d stars %d flags %02X",
    emu:read16(ST+2), emu:read16(ST+4), emu:read8(ST+6), emu:read8(ST+8), emu:read8(ST+9))
end
local function tap(k) emu:addKey(k); holdUntil = f + 6 end
local plan = {
  {2020, function() tap(START) end}, {2080, function() tap(UP) end}, {2120, function() tap(UP) end},
  {2160, function() tap(A) end},
  {2320, function() emu:screenshot(dir .. "v_page1.png") end},
  {2360, function() tap(DOWN) end}, {2420, function() tap(DOWN) end},
  {2500, function() emu:screenshot(dir .. "v_cursor2.png") end},
  {2540, function() tap(RIGHT) end},
  {2640, function() emu:screenshot(dir .. "v_page2.png") end},
  {2680, function() tap(LEFT) end},
  {2780, function() emu:screenshot(dir .. "v_back1.png") end},
  {2820, function() tap(DOWN) end}, {2860, function() tap(DOWN) end}, {2900, function() tap(DOWN) end},
  {2940, function() tap(DOWN) end}, {2980, function() tap(DOWN) end}, {3020, function() tap(DOWN) end},
  {3060, function() tap(DOWN) end}, {3100, function() tap(DOWN) end},
  {3160, function() emu:screenshot(dir .. "v_clamp.png") end},
  {3200, function() tap(A) end},
  {3320, function() w("armed " .. st()); tap(B) end},
  {3460, function() emu:screenshot(dir .. "v_bar.png"); w("bar up " .. st()) end},
  {3500, function() emu:write16(ST + 4, 200); emu:write8(ST + 8, 2); emu:write8(ST + 14, 0xFF)
                    w("forced chain 200 (max shiny rerolls) and 2 stars") end},
  {3580, function() emu:screenshot(dir .. "v_bar200.png") end},
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
  if f < 3620 then return end
  local c = cb2()
  if c == OVERWORLD and emu:read16(ST + 2) ~= 0 then emu:write16(ST + 4, 200); emu:write8(ST + 8, 2) end
  if c == BATTLE then
    if phase ~= "battle" then phase = "battle"; battles = battles + 1; bstart = f
      w(string.format("battle %d starts at f%d", battles, f)) end
    if f - bstart == 300 then
      local m = 0x02024744
      local iv = emu:read32(m + 0x48)
      local t, n31 = {}, 0
      for i = 0, 5 do local v = (iv >> (5*i)) & 31; t[#t+1] = tostring(v); if v == 31 then n31 = n31 + 1 end end
      local pid, ot = emu:read32(m), emu:read32(m + 4)
      w(string.format("   foe species %d lv %d IVs %s (%d perfect) %s", emu:read16(m + 0x20), emu:read8(m + 0x54),
        table.concat(t, "/"), n31, ((pid ~ (pid >> 16) ~ ot ~ (ot >> 16)) & 0xFFFF) < 8 and "SHINY!" or "not shiny"))
    end
    if f % 12 == 0 then emu:addKey(A) end
    if f % 12 == 5 then emu:clearKey(A) end
    return
  end
  if phase == "battle" and c == OVERWORLD then phase = "field"; w("   battle over, " .. st()) end
  if lock() == 1 then
    if holdUntil == 0 and f % 26 == 0 then tap(A) end
    return
  end
  if holdUntil > 0 or c ~= OVERWORLD then return end
  local p = f % 96
  if p == 0 then emu:addKey(RIGHT) elseif p == 44 then emu:clearKey(RIGHT)
  elseif p == 48 then emu:addKey(LEFT) elseif p == 92 then emu:clearKey(LEFT) end
  if f == 20000 then
    w("done, " .. battles .. " battles at max chain, no hang")
    local fh = io.open(dir .. "visual_done.txt", "w"); fh:write("done"); fh:close()
  end
end)
