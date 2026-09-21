-- naturefix test: the mon's personality nature is Impish (8). Set the override to Jolly (13) in the editor,
-- exit, and open the summary. Before the fix it printed Impish; it should now print Jolly.
local DIR = "/Users/ribeiro/Downloads/Pokemon-Hyper-Emerald-5.7-QoL/build/test/"
local A, B, START, DOWN, RIGHT, R = 0, 1, 3, 7, 4, 8
local frames, done = 0, false
local log = io.open(DIR .. "nf_log.txt", "w")
local function w(s) log:write(s .. string.char(10)); log:flush() end
local PARTY = 0x020244EC
local function snap(tag)
  w(string.format("%s: override=%d personality_mod25=%d cb2=%08X", tag,
    emu:read8(PARTY + 0x1F), emu:read32(PARTY) % 25, emu:read32(0x030022C0 + 4)))
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
  if frames == 2400 then snap("start") end
  -- editor
  tap(2600, START); tap(2750, DOWN); tap(2900, A); tap(3200, A)
  tap(3400, DOWN); tap(3470, DOWN); tap(3600, A)
  -- Nature row: R,R = +10, then RIGHT x3 = 13 (Jolly)
  tap(4000, R); tap(4090, R); tap(4180, RIGHT); tap(4270, RIGHT); tap(4360, RIGHT)
  if frames == 4600 then snap("after edit (want 13)") end
  tap(4800, B)
  if frames == 5300 then snap("back in field") end
  -- summary again
  tap(5600, START); tap(5800, A)
  tap(6100, A)
  tap(6400, A)
  if frames == 6900 then emu:screenshot(DIR .. "screens/nf_summary.png"); snap("summary page1") end
  if frames >= 7200 and not done then
    done = true; local f = io.open(DIR .. "nf_done.txt", "w"); f:write("ok\n"); f:close()
  end
end)
