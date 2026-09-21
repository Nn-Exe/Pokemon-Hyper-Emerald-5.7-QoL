-- Task 5 test: change an IV and an EV in the editor and read the mon's bytes back.
local DIR = "/Users/ribeiro/Downloads/Pokemon-Hyper-Emerald-5.7-QoL/build/test/"
local A, B, START, DOWN, UP, RIGHT, LEFT, R = 0, 1, 3, 7, 6, 4, 5, 8
local frames, done = 0, false
local log = io.open(DIR .. "edit_log.txt", "w")
local function w(s) log:write(s .. string.char(10)); log:flush() end
local PARTY = 0x020244EC

local function snap(tag)
  w(string.format("%s: ivs=%08X  evs=%d,%d,%d,%d,%d,%d  nature=%d  cb2=%08X", tag,
    emu:read32(PARTY + 0x48), emu:read8(PARTY + 0x38), emu:read8(PARTY + 0x39),
    emu:read8(PARTY + 0x3A), emu:read8(PARTY + 0x3B), emu:read8(PARTY + 0x3C), emu:read8(PARTY + 0x3D),
    emu:read8(PARTY + 0x1F), emu:read32(0x030022C0 + 4)))
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
  tap(2600, START); tap(2750, DOWN); tap(2900, A); tap(3200, A)
  tap(3400, DOWN); tap(3470, DOWN); tap(3600, A)
  if frames == 3950 then snap("in the editor") end
  -- IV page, row 1 = HP IV: three RIGHTs -> 28 becomes 31
  tap(4000, DOWN)
  tap(4150, RIGHT); tap(4230, RIGHT); tap(4310, RIGHT)
  if frames == 4500 then snap("after 3x RIGHT on HP IV") end
  -- switch to the EV page and bump HP EV by 2
  tap(4700, START)
  tap(4900, RIGHT); tap(4980, RIGHT)
  if frames == 5150 then snap("after 2x RIGHT on HP EV"); emu:screenshot(DIR .. "screens/editor_evpage.png") end
  -- back to the IV page: check it survived, and that the cursor highlight moved
  tap(5300, START)
  if frames == 5500 then emu:screenshot(DIR .. "screens/editor_ev.png") end
  tap(5600, B)
  if frames == 6000 then snap("after B (should be back in the field)") end
  if frames == 6400 then emu:screenshot(DIR .. "screens/editor_exit.png") end
  if frames >= 6600 and not done then
    done = true; local f = io.open(DIR .. "edit_done.txt", "w"); f:write("ok\n"); f:close()
  end
end)
