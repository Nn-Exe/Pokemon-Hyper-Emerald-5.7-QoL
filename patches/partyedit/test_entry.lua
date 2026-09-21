-- Task 3 test: open START > POKEMON, select the mon, and read the party menu's action list.
-- sPartyMenuInternal (0x0203CEC4) -> actions[] at +0xF, numActions at +0x17. Entry 34 = our Edit.
local DIR = "/Users/ribeiro/Downloads/Pokemon-Hyper-Emerald-5.7-QoL/build/test/"
local OUT = DIR .. "screens/"
local A, START, DOWN = 0, 3, 7
local frames, done = 0, false
local log = io.open(DIR .. "entry_log.txt", "w")
local function w(s) log:write(s .. string.char(10)); log:flush() end

local function actions()
  local p = emu:read32(0x0203CEC4)
  if p < 0x02000000 or p >= 0x02040000 then return "no sPartyMenuInternal" end
  local n = emu:read8(p + 0x17)
  local out = {}
  for i = 0, n - 1 do out[#out + 1] = tostring(emu:read8(p + 0xF + i)) end
  return string.format("internal=%08X numActions=%d actions={%s}", p, n, table.concat(out, ","))
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
  -- into the start menu, down to POKEMON, open the party menu, then select the mon
  tap(2600, START); tap(2750, DOWN); tap(2900, A); tap(3200, A)
  if frames == 3400 then
    w(actions())
    emu:screenshot(OUT .. "entry_list.png")
  end
  if frames >= 3600 and not done then
    done = true; local f = io.open(DIR .. "entry_done.txt", "w"); f:write("ok\n"); f:close()
  end
end)
