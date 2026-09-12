local dir = "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/tools/test-harness/"
local f = 0
local A, B, SELECT, START, RIGHT, LEFT, UP, DOWN, R = 0, 1, 2, 3, 4, 5, 6, 7, 8
local log = io.open(dir .. "repel1_log.txt", "w")
local function state()
  local sb1 = emu:read32(0x03005D8C)
  local var = emu:read16(sb1 + 0x139C + (0x4021 - 0x4000) * 2)
  local slots = emu:read32(0x02039DD8); local qty = -1
  for i = 0, 60 do if emu:read16(slots + i*4) == 84 then qty = emu:read16(slots + i*4 + 2); break end end
  return string.format("var4021=%04x (item %d, steps %d) maxrepel_qty=%d itemvar=%d pos=%d,%d", var, var >> 8, var & 0xFF, qty, emu:read16(0x0203CE7C), emu:read16(0x02037350+0x10), emu:read16(0x02037350+0x12))
end
local function shot(name) emu:screenshot(dir .. "rp_" .. name .. ".png"); log:write(name .. " f=" .. f .. " " .. state() .. "\n"); log:flush() end
local seq = {}
local t = 2700
local function at(fr, fn) seq[#seq+1] = {fr, fn} end
at(t, function() shot("start") end)
at(t + 10, function() emu:addKey(LEFT) end)
at(t + 90, function() emu:clearKey(LEFT); shot("after_walk") end)
at(t + 150, function() shot("prompt1") end)
at(t + 160, function() emu:addKey(A) end); at(t + 164, function() emu:clearKey(A) end)   -- advance / answer
at(t + 220, function() shot("prompt2") end)
at(t + 230, function() emu:addKey(A) end); at(t + 234, function() emu:clearKey(A) end)
at(t + 300, function() shot("after_yes") end)
at(t + 310, function() emu:addKey(A) end); at(t + 314, function() emu:clearKey(A) end)
at(t + 400, function() shot("after_msg") end)
at(t + 410, function() emu:addKey(A) end); at(t + 414, function() emu:clearKey(A) end)
at(t + 500, function() shot("final") end)
at(t + 510, function() emu:addKey(RIGHT) end); at(t + 560, function() emu:clearKey(RIGHT); shot("walk_after") end)
at(t + 600, function() local fh = io.open(dir .. "repel1_done.txt", "w"); fh:write("done"); fh:close() end)
callbacks:add("frame", function()
  f = f + 1
  if f < 1900 and f % 90 == 0 then emu:addKey(START) end
  if f < 1900 and f % 90 == 5 then emu:clearKey(START) end
  if f == 2000 then emu:addKey(A) end
  if f == 2004 then emu:clearKey(A) end
  for _, s in ipairs(seq) do if f == s[1] then s[2]() end end
end)
