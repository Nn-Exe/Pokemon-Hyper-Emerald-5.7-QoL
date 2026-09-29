-- The editor's value strings must stay in 0x0203F120..0x0203F13B: the Quest Log's Start-menu widget keeps its
-- magic and window id at 0x02039E40, and hypertrain keeps a byte at 0x0203F13C. Open the editor, edit on both
-- pages, and compare those bytes before and after.
local DIR = "/Users/ribeiro/Downloads/Pokemon-Hyper-Emerald-5.7-QoL/build/test/"
local A, B, START, DOWN, RIGHT = 0, 1, 3, 7, 4
local frames, done = 0, false
local log = io.open(DIR .. "scratch_log.txt", "w")
local function w(s) log:write(s .. string.char(10)); log:flush() end
local function hex(addr, n)
  local t = {}
  for i = 0, n - 1 do t[#t + 1] = string.format("%02X", emu:read8(addr + i)) end
  return table.concat(t)
end
local function tap(f, key)
  if frames == f then emu:addKey(key) end
  if frames == f + 4 then emu:clearKey(key) end
end
local qlog, ht

callbacks:add("frame", function()
  frames = frames + 1
  if frames < 1900 and frames % 90 == 0 then emu:addKey(START) end
  if frames < 1900 and frames % 90 == 5 then emu:clearKey(START) end
  if frames == 2000 then emu:addKey(A) end
  if frames == 2004 then emu:clearKey(A) end
  tap(2600, START); tap(2750, DOWN); tap(2900, A); tap(3200, A)
  tap(3400, DOWN); tap(3470, DOWN); tap(3600, A)
  if frames == 3900 then
    qlog, ht = hex(0x02039E40, 24), hex(0x0203F13C, 4)
    w(string.format("editor open: cb2=%08X qlog=%s ht=%s", emu:read32(0x030022C0 + 4), qlog, ht))
  end
  for k = 0, 7 do tap(4000 + k * 40, RIGHT) end     -- nature row: the longest strings
  tap(4400, START); tap(4600, DOWN)
  for k = 0, 3 do tap(4800 + k * 40, RIGHT) end     -- an EV and the total
  if frames == 5200 then
    local q2, h2 = hex(0x02039E40, 24), hex(0x0203F13C, 4)
    w(string.format("after edits: qlog=%s ht=%s scratch=%s", q2, h2, hex(0x0203F120, 28)))
    w(string.format("RESULT qlog %s, hypertrain %s", q2 == qlog and "untouched" or "CHANGED",
      h2 == ht and "untouched" or "CHANGED"))
  end
  tap(5300, B)
  if frames >= 5700 and not done then
    done = true
    w(string.format("back: cb2=%08X", emu:read32(0x030022C0 + 4)))
    local f = io.open(DIR .. "scratch_done.txt", "w"); f:write("ok\n"); f:close()
  end
end)
