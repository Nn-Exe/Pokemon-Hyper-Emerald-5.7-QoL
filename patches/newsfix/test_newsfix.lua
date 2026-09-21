-- Reproduce the News Tracker freeze: put the item in the first Key Items slot, use it from the bag,
-- then log what the game is stuck in (callbacks, live tasks, the built strings).
local dir = "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/_testrun/"
local NL = string.char(10)
local log = io.open(dir .. "nt_log.txt", "w")
local f, phase, t0 = 0, "boot", 0
local A, B, SELECT, START, RIGHT, LEFT, UP, DOWN = 0, 1, 2, 3, 4, 5, 6, 7
local ITEM = 695
local function w(s) log:write(s .. NL); log:flush() end
local function text(a, n)
  local s = ""
  for i = 0, (n or 60) - 1 do
    local c = emu:read8(a + i)
    if c == 0xFF then break end
    if c >= 0xBB and c <= 0xD4 then s = s .. string.char(65 + c - 0xBB)
    elseif c >= 0xD5 and c <= 0xEE then s = s .. string.char(97 + c - 0xD5)
    elseif c >= 0xA1 and c <= 0xAA then s = s .. string.char(48 + c - 0xA1)
    elseif c == 0x00 then s = s .. " "
    elseif c == 0xFE then s = s .. "|"
    elseif c == 0xAD then s = s .. "."
    else s = s .. string.format("<%02X>", c) end
  end
  return s
end
local function state(tag)
  w("== " .. tag .. " (frame " .. f .. ") ==")
  w(string.format("   callback1 %08X  callback2 %08X  paletteFade %02X",
    emu:read32(0x030022C0), emu:read32(0x030022C4), emu:read8(0x02037FDB)))
  for t = 0, 15 do
    local base = 0x03005E00 + t * 0x28
    if emu:read8(base + 4) == 1 then                     -- isActive
      local d = {}
      for k = 0, 5 do d[#d+1] = emu:read16(base + 8 + k * 2) end
      w(string.format("   task %2d func %08X prev %d next %d data %s",
        t, emu:read32(base), emu:read8(base + 5), emu:read8(base + 6), table.concat(d, ",")))
    end
  end
  w("   var1 '" .. text(0x02021CC4) .. "'  var2 '" .. text(0x02021DC4) .. "'")
  w("   var3 '" .. text(0x02021EC4) .. "'")
  w("   var4 '" .. text(0x02021FC4, 120) .. "'")
end
callbacks:add("frame", function()
  f = f + 1
  if f < 1900 and f % 90 == 0 then emu:addKey(START) end
  if f < 1900 and f % 90 == 5 then emu:clearKey(START) end
  if f == 2000 then emu:addKey(A) end
  if f == 2004 then emu:clearKey(A) end
  if f == 2400 then
    local sb1 = emu:read32(0x03005D8C)
    local roam = sb1 + 0x31DC
    local bytes = ""
    for i = 0, 23 do bytes = bytes .. string.format("%02x", emu:read8(roam + i)) end
    w("roamer struct @" .. string.format("%08X", roam) .. ": " .. bytes)
    w(string.format("   active=%d species=%d   sRoamerLocation 0203BC86 = group %d map %d",
      emu:read8(roam + 0x13), emu:read16(roam + 8), emu:read8(0x0203BC86), emu:read8(0x0203BC87)))
    -- put the News Tracker in the first Key Items slot so the bag cursor lands on it
    local base = emu:read32(0x02039DD8 + 4 * 8)
    w(string.format("   key items pocket @%08X, slot0 was item %d", base, emu:read16(base)))
    emu:write16(base, ITEM); emu:write16(base + 2, 1)
    phase = "bag"; t0 = f
  end
  if phase == "bag" then
    local d = f - t0
    if d == 20 then emu:addKey(START) elseif d == 24 then emu:clearKey(START)
    elseif d == 80 then emu:addKey(DOWN) elseif d == 84 then emu:clearKey(DOWN)
    elseif d == 100 then emu:addKey(DOWN) elseif d == 104 then emu:clearKey(DOWN)
    elseif d == 120 then emu:addKey(A) elseif d == 124 then emu:clearKey(A)       -- open Bag
    elseif d == 280 then emu:addKey(LEFT) elseif d == 284 then emu:clearKey(LEFT) -- -> Key Items
    elseif d == 340 then state("bag open on Key Items"); emu:screenshot(dir .. "nt_bag.png")
    elseif d == 360 then emu:addKey(A) elseif d == 364 then emu:clearKey(A)       -- pick the item
    elseif d == 420 then emu:screenshot(dir .. "nt_menu.png"); state("item context menu")
    elseif d == 440 then emu:addKey(A) elseif d == 444 then emu:clearKey(A)       -- Use
    elseif d == 520 then state("just after Use"); emu:screenshot(dir .. "nt_used.png")
    elseif d == 700 then state("180 frames later"); emu:screenshot(dir .. "nt_frozen1.png")
    elseif d == 900 then state("400 frames later"); emu:screenshot(dir .. "nt_frozen2.png")
    elseif d == 920 then emu:addKey(A) elseif d == 924 then emu:clearKey(A)       -- does A dismiss it?
    elseif d == 1000 then state("after pressing A"); emu:screenshot(dir .. "nt_afterA.png")
      local fh = io.open(dir .. "nt_done.txt", "w"); fh:write("done"); fh:close(); phase = "over"
    end
  end
end)
