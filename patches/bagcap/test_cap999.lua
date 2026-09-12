local dir = "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/_testrun/"
local f = 0
local A, B, SELECT, START, RIGHT, LEFT, UP, DOWN, R = 0, 1, 2, 3, 4, 5, 6, 7, 8
local log = io.open(dir .. "cap1_log.txt", "w")
local seq = {}
local t = 2700
local function tap(key, gap) seq[#seq+1] = {t, function() emu:addKey(key) end}; seq[#seq+1] = {t+4, function() emu:clearKey(key) end}; t = t + (gap or 40) end
local function shot(name) seq[#seq+1] = {t, function() emu:screenshot(dir .. "cap_" .. name .. ".png") end}; t = t + 2 end
-- inject quantities: items pocket slot 0 = 150, slot 1 = 999 (encrypted with SB2 key)
seq[#seq+1] = {t, function()
  local key = emu:read16(emu:read32(0x03005D90) + 0xAC)
  local slots = emu:read32(0x02039DD8)
  emu:write16(slots + 2, 150 ~ key)
  emu:write16(slots + 6, 999 ~ key)
  log:write(string.format("key=%04x item0=%d item1=%d\n", key, emu:read16(slots), emu:read16(slots + 4))); log:flush()
end}
t = t + 10
tap(START, 120); tap(DOWN, 40); tap(DOWN, 40); tap(A, 300); shot("bag")
tap(A, 90); shot("ctx")          -- context menu for slot 0
tap(DOWN, 40); tap(DOWN, 40); tap(A, 90); shot("toss")   -- Toss? (menu order Use/Give/Toss/Cancel) -> quantity picker
tap(B, 60); tap(B, 60); tap(B, 200); tap(B, 200)
seq[#seq+1] = {t, function() local fh = io.open(dir .. "cap1_done.txt", "w"); fh:write("done"); fh:close() end}
callbacks:add("frame", function()
  f = f + 1
  if f < 1900 and f % 90 == 0 then emu:addKey(START) end
  if f < 1900 and f % 90 == 5 then emu:clearKey(START) end
  if f == 2000 then emu:addKey(A) end
  if f == 2004 then emu:clearKey(A) end
  for _, s in ipairs(seq) do if f == s[1] then s[2]() end end
end)
