-- Both-bikes test: load the save, look at the Key Items pocket for the Mach Bike (259) and Acro Bike (272)
-- before and after the overworld runs, then open the bag to see them.
local dir = "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/_testrun/"
local f = 0
local A, B, SELECT, START, RIGHT, LEFT, UP, DOWN = 0, 1, 2, 3, 4, 5, 6, 7
local NL = string.char(10)
local log = io.open(dir .. "bb_log.txt", "w")
local function keyitems()                 -- gBagPockets @0x02039DD8: 5 x {itemSlot *slots, u8 capacity}
  local out, mach, acro = "", false, false
  for pocket = 0, 4 do
    local base = emu:read32(0x02039DD8 + pocket * 8)
    local cap = emu:read8(0x02039DD8 + pocket * 8 + 4)
    if base >= 0x02000000 and base < 0x03000000 and cap > 0 and cap < 100 then
      for i = 0, cap - 1 do
        local id = emu:read16(base + i * 4)
        if id == 259 then mach = true; out = out .. "[p" .. pocket .. " Mach] " end
        if id == 272 then acro = true; out = out .. "[p" .. pocket .. " Acro] " end
      end
    end
  end
  return out, mach, acro
end
local function report(tag)
  local ids, mach, acro = keyitems()
  log:write(string.format("%s: mach=%s acro=%s  key items: %s", tag, tostring(mach), tostring(acro), ids) .. NL)
  log:flush()
end
callbacks:add("frame", function()
  f = f + 1
  if f < 1900 and f % 90 == 0 then emu:addKey(START) end
  if f < 1900 and f % 90 == 5 then emu:clearKey(START) end
  if f == 1990 then report("before continue") end
  if f == 2000 then emu:addKey(A) end
  if f == 2004 then emu:clearKey(A) end
  if f == 2400 then report("in the overworld") end
  if f == 2500 then emu:screenshot(dir .. "bb_field.png"); emu:addKey(START) end
  if f == 2504 then emu:clearKey(START) end
  if f == 2560 then emu:addKey(DOWN) end          -- START menu -> Bag
  if f == 2564 then emu:clearKey(DOWN) end
  if f == 2580 then emu:addKey(DOWN) end
  if f == 2584 then emu:clearKey(DOWN) end
  if f == 2600 then emu:addKey(A) end
  if f == 2604 then emu:clearKey(A) end
  if f == 2760 then emu:screenshot(dir .. "bb_bag.png") end
  if f == 2800 then emu:addKey(RIGHT) end         -- across the pockets to Key Items
  if f == 2804 then emu:clearKey(RIGHT) end
  if f == 2830 then emu:addKey(RIGHT) end
  if f == 2834 then emu:clearKey(RIGHT) end
  if f == 2860 then emu:addKey(RIGHT) end
  if f == 2864 then emu:clearKey(RIGHT) end
  if f == 2920 then emu:screenshot(dir .. "bb_keyitems.png"); report("bag open") end
  if f == 2960 then local fh = io.open(dir .. "bb_done.txt", "w"); fh:write("done"); fh:close() end
end)
