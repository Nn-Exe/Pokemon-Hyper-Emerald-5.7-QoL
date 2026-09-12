local dir = "C:/Users/nonth/AppData/Local/Temp/claude/c--Users-nonth-Desktop-Works---Productivity-gba-trans/02742dae-7df3-4db2-93fc-cf708e28c0df/scratchpad/bagtest/"
local f = 0
local START, A, DOWN, B, SELECT, R = 3, 0, 7, 1, 2, 8
local function tap(key, at, len)
  if f == at then emu:addKey(key) end
  if f == at + (len or 4) then emu:clearKey(key) end
end
local function dump(name, pocket)
  local p = emu:read32(0x02039DD8 + pocket*8)
  local s = ""
  for i = 0, 39 do s = s .. emu:read16(p + i*4) .. " " end
  local fh = io.open(dir .. name, "w"); fh:write(s .. "\n"); fh:close()
end
callbacks:add("frame", function()
  f = f + 1
  if f < 1900 and f % 90 == 0 then emu:addKey(START) end
  if f < 1900 and f % 90 == 5 then emu:clearKey(START) end
  tap(A, 2000); tap(START, 2600); tap(DOWN, 2760); tap(DOWN, 2820); tap(A, 2940)
  tap(START, 3300); tap(START, 3500); tap(START, 3700); tap(START, 3900)  -- type, name, amount, type
  tap(R, 4100)        -- Poke Balls pocket
  tap(START, 4300)    -- sort balls
  tap(SELECT, 4500)   -- move mode still works?
  tap(B, 4700)        -- cancel move
  tap(R, 4900); tap(R, 5000)  -- TM pocket? (skip berries) 
  tap(START, 5200)    -- should do nothing in TM/berry pocket
  tap(B, 5400)        -- close bag
  local shots = {[3400]=1,[3600]=1,[3800]=1,[4000]=1,[4250]=1,[4400]=1,[4600]=1,[4800]=1,[5100]=1,[5300]=1,[5600]=1}
  if shots[f] then emu:screenshot(dir .. "s3_" .. f .. ".png") end
  if f == 3250 then dump("items_before.txt",0) end
  if f == 3450 then dump("items_after1.txt",0) end
  if f == 3650 then dump("items_after2.txt",0) end
  if f == 3850 then dump("items_after3.txt",0) end
  if f == 4050 then dump("items_after4.txt",0) end
  if f == 4250 then dump("balls_before.txt",1) end
  if f == 4450 then dump("balls_after.txt",1) end
end)
