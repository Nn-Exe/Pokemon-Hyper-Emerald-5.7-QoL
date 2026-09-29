-- Does the SUMMARY reflect the mon's bytes? Set WRITE = true to poke the nature override and max the IVs
-- before opening the summary. No editor involved, so nothing else can confuse the result.
local DIR = "/Users/ribeiro/Downloads/Pokemon-Hyper-Emerald-5.7-QoL/build/test/"
local WRITE = io.open(DIR .. "write.flag", "r") ~= nil
local A, B, START, DOWN, RIGHT = 0, 1, 3, 7, 4
local frames, done = 0, false
local log = io.open(DIR .. "disp_log.txt", "w")
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
  if frames == 2400 then
    if WRITE then
      emu:write8(PARTY + 0x1F, 5)          -- nature override = 5 (Bold)
      emu:write16(PARTY + 0x58, 77)        -- max HP 35 -> 77
      emu:write16(PARTY + 0x5A, 99)        -- Attack 20 -> 99
      emu:write16(PARTY + 0x5E, 88)        -- Speed 22 -> 88
    end
    w(string.format("setup WRITE=%s ivs=%08X nature_byte=%d atk_stat=%d",
      tostring(WRITE), emu:read32(PARTY + 0x48), emu:read8(PARTY + 0x1F), emu:read16(PARTY + 0x5A)))
  end
  -- START menu (cursor starts on Pokedex) -> Party -> party menu -> action list -> Summary
  tap(2600, START); tap(2750, DOWN); tap(2900, A); tap(3100, A); tap(3300, A)
  if frames == 3600 then
    emu:screenshot(DIR .. "screens/dp_page1.png")
    w(string.format("page1: nature_byte now=%d  personality%%25=%d  ivs=%08X",
      emu:read8(PARTY + 0x1F), emu:read32(PARTY + 0x00) % 25, emu:read32(PARTY + 0x48)))
  end
  tap(3800, RIGHT)
  if frames == 4100 then emu:screenshot(DIR .. "screens/dp_page2.png"); w("page2 shot") end
  tap(4400, RIGHT)
  if frames == 4700 then emu:screenshot(DIR .. "screens/dp_page3.png"); w("page3 shot") end
  if frames >= 5000 and not done then
    done = true; local f = io.open(DIR .. "disp_done.txt", "w"); f:write("ok\n"); f:close()
  end
end)
