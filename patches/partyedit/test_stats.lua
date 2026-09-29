-- Does an edit reach the SUMMARY, not just the mon's raw bytes?
-- Change Attack IV (already 12 -> 31 needs +19, and R is +5) at level 12, so the stat moves by ~2.
local DIR = "/Users/ribeiro/Downloads/Pokemon-Hyper-Emerald-5.7-QoL/build/test/"
local A, B, START, DOWN, R, RIGHT = 0, 1, 3, 7, 8, 4
local frames, done = 0, false
local log = io.open(DIR .. "stats_log.txt", "w")
local function w(s) log:write(s .. string.char(10)); log:flush() end
local PARTY = 0x020244EC

local function snap(tag)
  w(string.format("%s: ivs=%08X | stats hp=%d maxhp=%d atk=%d def=%d spe=%d spa=%d spd=%d",
    tag, emu:read32(PARTY + 0x48),
    emu:read16(PARTY + 0x56), emu:read16(PARTY + 0x58), emu:read16(PARTY + 0x5A),
    emu:read16(PARTY + 0x5C), emu:read16(PARTY + 0x5E), emu:read16(PARTY + 0x60), emu:read16(PARTY + 0x62)))
end

local function tap(f, key)
  if frames == f then emu:addKey(key) end
  if frames == f + 4 then emu:clearKey(key) end
end

callbacks:add("frame", function()
  frames = frames + 1
  if frames < 1900 and frames % 90 == 0 then emu:addKey(START) end
  if frames < 1900 and frames % 90 == 5 then emu:clearKey(START) end
  if frames == 2000 then emu:addKey(A) end
  if frames == 2004 then emu:clearKey(A) end
  if frames == 2400 then snap("field, before") end
  -- party menu -> action list -> Edit
  tap(2600, START); tap(2750, DOWN); tap(2900, A); tap(3200, A)
  tap(3400, DOWN); tap(3470, DOWN); tap(3600, A)
  if frames == 3950 then snap("editor open") end
  -- down to Atk IV (row 2), then R x4 for +20 (12 -> 31)
  tap(4050, DOWN); tap(4150, DOWN)
  tap(4300, R); tap(4390, R); tap(4480, R); tap(4570, R)
  if frames == 4750 then snap("after 4x R on Atk IV") end
  tap(4900, B)
  if frames == 5200 then snap("back in the field") end
  -- reopen the party menu and look at the summary
  tap(5400, START); tap(5550, DOWN); tap(5700, A)
  if frames == 5900 then emu:screenshot(DIR .. "screens/summary_list.png") end
  tap(6000, A)                       -- Summary
  if frames == 6300 then emu:screenshot(DIR .. "screens/summary_stats.png") end
  tap(6500, RIGHT)                   -- summary pages
  if frames == 6700 then emu:screenshot(DIR .. "screens/summary_p2.png") end
  if frames >= 7000 and not done then
    done = true; local f = io.open(DIR .. "stats_done.txt", "w"); f:write("ok\n"); f:close()
  end
end)
