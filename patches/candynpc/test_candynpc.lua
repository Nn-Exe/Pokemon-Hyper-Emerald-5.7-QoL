-- Task 2 in-game test. The pinned spawn map (Route 102) has been repointed at the Petalburg Mart's layout
-- and events in a throwaway ROM, so the player lands inside the Mart and can walk to the new NPC.
local DIR = "/Users/ribeiro/Downloads/Pokemon-Hyper-Emerald-5.7-QoL/build/test/"
local A, START, UP, RIGHT = 0, 3, 6, 4
local frames, done = 0, false
local log = io.open(DIR .. "npc_log.txt", "w")
local function w(s) log:write(s .. string.char(10)); log:flush() end

local function candy()
  local total = 0
  for pocket = 0, 4 do
    local base = emu:read32(0x02039DD8 + pocket * 8)
    local cap = emu:read8(0x02039DD8 + pocket * 8 + 4)
    if base >= 0x02000000 and base < 0x03000000 and cap > 0 and cap < 200 then
      for i = 0, cap - 1 do
        if emu:read16(base + i * 4) == 68 then total = total + emu:read8(base + i * 4 + 2) end
      end
    end
  end
  return total
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
  if frames == 2600 then
    local sb1 = emu:read32(0x03005D8C)
    w(string.format("field: map=%d/%d pos=(%d,%d) candy=%d", emu:read8(sb1 + 4), emu:read8(sb1 + 5),
      emu:read16(sb1), emu:read16(sb1 + 2), candy()))
    emu:screenshot(DIR .. "screens/npc_mart.png")
  end
  -- walk right to (7,6), face up at the NPC, talk
  tap(2800, RIGHT); tap(2860, RIGHT); tap(2920, RIGHT)
  tap(3050, UP)
  if frames == 3150 then emu:screenshot(DIR .. "screens/npc_face.png") end
  tap(3250, A)
  if frames == 3500 then
    w("after talking: candy=" .. candy())
    emu:screenshot(DIR .. "screens/npc_talk.png")
  end
  tap(3700, A); tap(3820, A); tap(3940, A)
  if frames == 4200 then
    w("after A spam: candy=" .. candy())
    emu:screenshot(DIR .. "screens/npc_after.png")
  end
  if frames >= 4400 and not done then
    done = true; local f = io.open(DIR .. "npc_done.txt", "w"); f:write("ok\n"); f:close()
  end
end)
