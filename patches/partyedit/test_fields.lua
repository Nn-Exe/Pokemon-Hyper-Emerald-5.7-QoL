-- Task 6 edge case: a mon that knows four field moves must hide Edit exactly as it hides Moves -
-- the action list holds only 8, so nothing may overflow.
local DIR = "/Users/ribeiro/Downloads/Pokemon-Hyper-Emerald-5.7-QoL/build/test/"
local A, START, DOWN = 0, 3, 7
local frames, done = 0, false
local log = io.open(DIR .. "fields_log.txt", "w")
local function w(s) log:write(s .. string.char(10)); log:flush() end
local PARTY = 0x020244EC

local function actions()
  local p = emu:read32(0x0203CEC4)
  if p < 0x02000000 or p >= 0x02040000 then return "no sPartyMenuInternal" end
  local n = emu:read8(p + 0x17)
  local out = {}
  for i = 0, n - 1 do out[#out + 1] = tostring(emu:read8(p + 0xF + i)) end
  return string.format("numActions=%d actions={%s}", n, table.concat(out, ","))
end

callbacks:add("frame", function()
  frames = frames + 1
  if frames < 1900 and frames % 90 == 0 then emu:addKey(START) end
  if frames < 1900 and frames % 90 == 5 then emu:clearKey(START) end
  if frames == 2000 then emu:addKey(A) end
  if frames == 2004 then emu:clearKey(A) end
  if frames == 2500 then
    -- four field moves: Cut 15, Fly 19, Surf 57, Strength 70
    local mv = {15, 19, 57, 70}
    for i, m in ipairs(mv) do
      emu:write16(PARTY + 0x2C + (i - 1) * 2, m)
      emu:write8(PARTY + 0x34 + (i - 1), 20)      -- PP, so the menu does not show ---
    end
    w("moves written: 15,19,57,70")
  end
  if frames == 2600 then emu:addKey(START) end
  if frames == 2604 then emu:clearKey(START) end
  if frames == 2750 then emu:addKey(DOWN) end
  if frames == 2754 then emu:clearKey(DOWN) end
  if frames == 2900 then emu:addKey(A) end
  if frames == 2904 then emu:clearKey(A) end
  if frames == 3200 then emu:addKey(A) end
  if frames == 3204 then emu:clearKey(A) end
  if frames == 3450 then
    w("4 field moves: " .. actions())
    emu:screenshot(DIR .. "screens/editor_fields.png")
  end
  if frames >= 3700 and not done then
    done = true; local f = io.open(DIR .. "fields_done.txt", "w"); f:write("ok\n"); f:close()
  end
end)
