-- Shared boot harness for the candynpc/partyedit tests (Hyper Emerald v5.7).
-- Copy this file and change SHOT/EXIT frame counts per test. Writes <name>_done.txt so the shell can
-- wait for the run instead of polling the emulator.
local DIR = "/Users/ribeiro/Downloads/Pokemon-Hyper-Emerald-5.7-QoL/build/test/"
local OUT = DIR .. "screens/"
local SHOT_AT = 240
local DONE_AT = 600
local frames, done = 0, false

callbacks:add("frame", function()
  frames = frames + 1
  if frames == 1 then console:log("boot: first frame") end
  if frames == SHOT_AT then
    emu:screenshot(OUT .. "boot.png")
    console:log("boot: screenshot at frame " .. frames)
  end
  if frames == DONE_AT and not done then
    done = true
    local f = io.open(DIR .. "boot_done.txt", "w")
    f:write("ok " .. frames .. "\n")
    f:close()
    console:log("BOOT OK - reached frame " .. frames)
  end
end)
