-- Nature row shows names: step it and check the displayed name matches the stored value.
local DIR = "/Users/ribeiro/Downloads/Pokemon-Hyper-Emerald-5.7-QoL/build/test/"
local A, B, START, DOWN, RIGHT = 0, 1, 3, 7, 4
local frames, done = 0, false
local log = io.open(DIR .. "nature_log.txt", "w")
local function w(s) log:write(s .. string.char(10)); log:flush() end
local PARTY = 0x020244EC
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
  if frames == 3900 then w("nature at open = " .. emu:read8(PARTY + 0x1F)) end
  -- eight RIGHTs on the Nature row: 0 (Hardy) -> 8 (Impish)
  for k = 0, 7 do tap(4000 + k * 90, RIGHT) end
  if frames == 4900 then
    w("after 8 RIGHT: nature byte = " .. emu:read8(PARTY + 0x1F))
    emu:screenshot(DIR .. "screens/nature_impish.png")
  end
  -- five more: 8 -> 13 (Jolly)
  for k = 0, 4 do tap(5100 + k * 90, RIGHT) end
  if frames == 5800 then
    w("after 13 RIGHT: nature byte = " .. emu:read8(PARTY + 0x1F))
    emu:screenshot(DIR .. "screens/nature_jolly.png")
  end
  if frames >= 6100 and not done then
    done = true; local f = io.open(DIR .. "nature_done.txt", "w"); f:write("ok\n"); f:close()
  end
end)
