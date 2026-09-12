local dir = "C:/Users/nonth/AppData/Local/Temp/claude/c--Users-nonth-Desktop-Works---Productivity-gba-trans/02742dae-7df3-4db2-93fc-cf708e28c0df/scratchpad/bagtest/"
local f = 0
local START, A, DOWN, B, SELECT, RIGHT = 3, 0, 7, 1, 2, 4
local function tap(key, at, len)
  if f == at then emu:addKey(key) end
  if f == at + (len or 4) then emu:clearKey(key) end
end
local function dump(name, pocket)
  local p = emu:read32(0x02039DD8 + pocket*8)
  local cap = emu:read8(0x02039DD8 + pocket*8 + 4)
  local s = "cap=" .. cap .. ": "
  for i = 0, cap-1 do s = s .. emu:read16(p + i*4) .. " " end
  local fh = io.open(dir .. name, "w"); fh:write(s .. "\n"); fh:close()
end
callbacks:add("frame", function()
  f = f + 1
  if f < 1900 and f % 90 == 0 then emu:addKey(START) end
  if f < 1900 and f % 90 == 5 then emu:clearKey(START) end
  tap(A, 2000); tap(START, 2600); tap(DOWN, 2760); tap(DOWN, 2820); tap(A, 2940)
  tap(RIGHT, 3300)   -- Poke Balls
  tap(START, 3500)
  tap(RIGHT, 3700)   -- TM/HM
  tap(START, 3900)   -- expect no-op
  tap(RIGHT, 4100)   -- Berries
  tap(RIGHT, 4300)   -- Key Items
  tap(START, 4500)
  tap(B, 4800)       -- close bag
  local shots = {[3450]=1,[3600]=1,[3850]=1,[4000]=1,[4450]=1,[4600]=1,[5000]=1}
  if shots[f] then emu:screenshot(dir .. "s4_" .. f .. ".png") end
  if f == 3450 then dump("p_balls_before.txt",1) end
  if f == 3650 then dump("p_balls_after.txt",1) end
  if f == 3850 then dump("p_tm_before.txt",2) end
  if f == 4050 then dump("p_tm_after.txt",2) end
  if f == 4450 then dump("p_key_before.txt",4) end
  if f == 4650 then dump("p_key_after.txt",4) end
  if f == 5100 then local fh = io.open(dir .. "done.txt", "w"); fh:write("done"); fh:close() end
end)

