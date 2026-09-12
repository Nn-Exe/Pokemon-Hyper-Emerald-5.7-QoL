local dir = "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/tools/test-harness/"
local f = 0
local A, B, SELECT, START, RIGHT, LEFT, UP, DOWN, R, L = 0, 1, 2, 3, 4, 5, 6, 7, 8, 9
local log = io.open(dir .. "lrepel1_log.txt", "w")
local function state()
  local sb1 = emu:read32(0x03005D8C)
  local var = emu:read16(sb1 + 0x139C + (0x4021 - 0x4000) * 2)
  local slots = emu:read32(0x02039DD8); local qty = -1; local idx = -1
  for i = 0, 99 do if emu:read16(slots + i*4) == 84 then qty = emu:read16(slots + i*4 + 2); idx = i; break end end
  return string.format("var=%04x (item %d steps %d) maxrepel=%d@%d pos=%d,%d", var, var >> 8, var & 0xFF, qty, idx, emu:read16(0x02037350+0x10), emu:read16(0x02037350+0x12))
end
local function shot(name) emu:screenshot(dir .. "lr_" .. name .. ".png"); log:write(name .. " f=" .. f .. " " .. state() .. "\n"); log:flush() end
local seq = {}
local t = 2700
local function at(fr, fn) seq[#seq+1] = {fr, fn} end
local function tap(key, fr) at(fr, function() emu:addKey(key) end); at(fr + 4, function() emu:clearKey(key) end) end
at(t, function() shot("start") end)
tap(L, t + 10); at(t + 70, function() shot("popup") end)            -- popup should appear
tap(B, t + 80); at(t + 140, function() shot("declined") end)        -- No via B? (B = No)
tap(A, t + 150); at(t + 220, function() shot("after_close") end)
tap(L, t + 260); at(t + 320, function() shot("popup2") end)
tap(A, t + 330); at(t + 420, function() shot("used") end)           -- Yes
tap(A, t + 430); at(t + 520, function() shot("msg_closed") end)
tap(L, t + 540); at(t + 600, function() shot("active_L") end)       -- active repel: nothing should happen
at(t + 610, function() emu:addKey(LEFT) end); at(t + 650, function() emu:clearKey(LEFT); shot("walked") end)
-- remove all repels then press L: nothing should happen
at(t + 680, function()
  local slots = emu:read32(0x02039DD8)
  for i = 0, 99 do local id = emu:read16(slots + i*4); if id == 84 or id == 83 or id == 86 then emu:write16(slots + i*4 + 2, 0) end end
  local sb1 = emu:read32(0x03005D8C); emu:write16(sb1 + 0x139C + (0x4021 - 0x4000) * 2, 0)   -- clear active repel
end)
tap(L, t + 700); at(t + 760, function() shot("norepel_L") end)
at(t + 770, function() emu:addKey(RIGHT) end); at(t + 810, function() emu:clearKey(RIGHT); shot("walked2") end)
tap(R, t + 830); at(t + 870, function() shot("autorun_R") end)      -- chained auto-run hook still works
at(t + 900, function() local fh = io.open(dir .. "lrepel1_done.txt", "w"); fh:write("done"); fh:close() end)
callbacks:add("frame", function()
  f = f + 1
  if f < 1900 and f % 90 == 0 then emu:addKey(START) end
  if f < 1900 and f % 90 == 5 then emu:clearKey(START) end
  if f == 2000 then emu:addKey(A) end
  if f == 2004 then emu:clearKey(A) end
  for _, s in ipairs(seq) do if f == s[1] then s[2]() end end
end)
