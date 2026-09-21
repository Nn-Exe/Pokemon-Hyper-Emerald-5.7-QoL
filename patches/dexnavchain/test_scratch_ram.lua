-- Fill a candidate scratch region with a pattern, then play hard and see if it survives.
local dir = "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/_testrun/"
local NL = string.char(10)
local log = io.open(dir .. "pat2_log.txt", "w")
local function w(s) log:write(s .. NL); log:flush() end
local CAND = {0x02038E00, 0x02039E40, 0x0203D600, 0x0203F100, 0x02031C00, 0x0203A660}
local LEN = 0x40
local A, B, SELECT, START, RIGHT, LEFT, UP, DOWN = 0, 1, 2, 3, 4, 5, 6, 7
local f, filled, broken = 0, false, false
local function fill()
  for _, LO in ipairs(CAND) do
    for a = LO, LO + LEN - 4, 4 do emu:write32(a, 0xA5A5A5A5) end
  end
  filled = true
  w("filled " .. #CAND .. " candidates, " .. LEN .. " bytes each")
end
local function check(tag)
  if not filled then return end
  local parts = {}
  for _, LO in ipairs(CAND) do
    local bad = 0
    for a = LO, LO + LEN - 4, 4 do if emu:read32(a) ~= 0xA5A5A5A5 then bad = bad + 4 end end
    parts[#parts + 1] = string.format("%08X:%s", LO, bad == 0 and "ok" or tostring(bad))
    if bad > 0 then broken = true end
  end
  w(string.format("%-22s frame %5d cb2 %08X  %s", tag, f, emu:read32(0x030022C4), table.concat(parts, "  ")))
end
callbacks:add("frame", function()
  f = f + 1
  if f < 1900 then
    if f % 90 == 0 then emu:addKey(START) end
    if f % 90 == 5 then emu:clearKey(START) end
    if f == 1800 then emu:addKey(A) end
    if f == 1804 then emu:clearKey(A) end
    return
  end
  if f == 1950 then fill(); return end
  if f == 2000 then check("overworld idle") end
  -- surf + fight wild battles by mashing A
  if f > 2050 and f < 7000 then
    local p = f % 100
    if p == 0 then emu:addKey(RIGHT) elseif p == 25 then emu:clearKey(RIGHT)
    elseif p == 50 then emu:addKey(LEFT) elseif p == 75 then emu:clearKey(LEFT) end
    if f % 12 == 0 then emu:addKey(A) end
    if f % 12 == 4 then emu:clearKey(A) end
  end
  if f == 3500 then check("during battles 1") end
  if f == 5000 then check("during battles 2") end
  if f == 7000 then emu:clearKey(RIGHT); emu:clearKey(LEFT); emu:clearKey(A); check("after battles") end
  -- start menu -> bag -> back
  if f == 7100 then emu:addKey(START) elseif f == 7106 then emu:clearKey(START) end
  if f == 7200 then check("start menu") end
  if f == 7260 then emu:addKey(DOWN) elseif f == 7266 then emu:clearKey(DOWN) end
  if f == 7300 then emu:addKey(DOWN) elseif f == 7306 then emu:clearKey(DOWN) end
  if f == 7340 then emu:addKey(A) elseif f == 7346 then emu:clearKey(A) end   -- BAG
  if f == 7500 then check("bag open") end
  if f == 7560 then emu:addKey(B) elseif f == 7566 then emu:clearKey(B) end
  if f == 7700 then emu:addKey(START) elseif f == 7706 then emu:clearKey(START) end
  -- DexNav (last-but-one entry) : press UP twice from top lands near the bottom of the list
  if f == 7800 then emu:addKey(UP) elseif f == 7806 then emu:clearKey(UP) end
  if f == 7840 then emu:addKey(UP) elseif f == 7846 then emu:clearKey(UP) end
  if f == 7880 then emu:addKey(A) elseif f == 7886 then emu:clearKey(A) end
  if f == 8100 then check("dexnav-ish screen") end
  if f == 8160 then emu:addKey(B) elseif f == 8166 then emu:clearKey(B) end
  -- save: START -> SAVE -> A A
  if f == 8300 then emu:addKey(START) elseif f == 8306 then emu:clearKey(START) end
  if f == 8400 then emu:addKey(DOWN) elseif f == 8406 then emu:clearKey(DOWN) end
  if f == 8440 then emu:addKey(DOWN) elseif f == 8446 then emu:clearKey(DOWN) end
  if f == 8480 then emu:addKey(DOWN) elseif f == 8486 then emu:clearKey(DOWN) end
  if f == 8520 then emu:addKey(A) elseif f == 8526 then emu:clearKey(A) end
  if f == 8600 then emu:addKey(A) elseif f == 8606 then emu:clearKey(A) end
  if f == 8700 then emu:addKey(A) elseif f == 8706 then emu:clearKey(A) end
  if f == 8900 then check("after save attempt") end
  if f == 9000 then emu:addKey(B) elseif f == 9006 then emu:clearKey(B) end
  if f == 9200 then
    check("final")
    emu:screenshot(dir .. "pat2_end.png")
    local fh = io.open(dir .. "pat2_done.txt", "w"); fh:write(broken and "BROKEN" or "SURVIVED"); fh:close()
  end
end)
