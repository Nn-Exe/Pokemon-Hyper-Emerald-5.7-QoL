-- Multi-slot test: does Edit write to the mon you actually selected, or always to party[0]?
-- Synthesize a second mon (a copy of the first, with a distinctive IV word), select it, edit, read back.
local DIR = "/Users/ribeiro/Downloads/Pokemon-Hyper-Emerald-5.7-QoL/build/test/"
local A, B, START, DOWN, RIGHT = 0, 1, 3, 7, 4
local frames, done = 0, false
local log = io.open(DIR .. "slots_log.txt", "w")
local function w(s) log:write(s .. string.char(10)); log:flush() end
local PARTY = 0x020244EC
local function tap(f, key)
  if frames == f then emu:addKey(key) end
  if frames == f + 4 then emu:clearKey(key) end
end
local function snap(tag)
  w(string.format("%s: p0 ivs=%08X nature=%d | p1 ivs=%08X nature=%d | count=%d", tag,
    emu:read32(PARTY + 0x48), emu:read8(PARTY + 0x1F),
    emu:read32(PARTY + 100 + 0x48), emu:read8(PARTY + 100 + 0x1F), emu:read8(0x020244E9)))
end

callbacks:add("frame", function()
  frames = frames + 1
  if frames < 1900 and frames % 90 == 0 then emu:addKey(START) end
  if frames < 1900 and frames % 90 == 5 then emu:clearKey(START) end
  if frames == 2000 then emu:addKey(A) end
  if frames == 2004 then emu:clearKey(A) end
  if frames == 2400 then
    for i = 0, 99 do emu:write8(PARTY + 100 + i, emu:read8(PARTY + i)) end   -- clone mon 0 -> mon 1
    emu:write32(PARTY + 100 + 0x48, 0x11111111)                              -- distinctive IV word
    emu:write8(PARTY + 100 + 0x1F, 0)                                        -- nature 0
    emu:write8(0x020244E9, 2)                                                -- party count = 2
    snap("setup")
  end
  -- START -> Party -> (RIGHT selects the second mon) -> action list -> Edit
  tap(2600, START); tap(2750, DOWN); tap(2900, A)
  tap(3150, RIGHT)
  if frames == 3350 then snap("after RIGHT in party menu") end
  tap(3400, A)
  -- with two mons the list is {Summary, Switch, Item, Edit, Moves, Cancel}: Edit is the 4th row
  tap(3600, DOWN); tap(3670, DOWN); tap(3740, DOWN); tap(3850, A)
  if frames == 4100 then snap("editor open"); w("cb2=" .. string.format("%08X", emu:read32(0x030022C0 + 4))) end
  -- eight RIGHTs on the Nature row: the SELECTED mon's nature should go 0 -> 8
  for k = 0, 7 do tap(4200 + k * 60, RIGHT) end
  if frames == 4800 then snap("after 8 RIGHT (selected mon)") end
  if frames >= 5100 and not done then
    done = true; local f = io.open(DIR .. "slots_done.txt", "w"); f:write("ok\n"); f:close()
  end
end)
