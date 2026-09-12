local base = "C:/Users/nonth/AppData/Local/Temp/claude/c--Users-nonth-Desktop-Works---Productivity-gba-trans/f184de21-699d-4c79-a35b-04f41a1fd6c9/scratchpad/shots_npc"
local frame = 0
callbacks:add("frame", function()
  frame = frame + 1
  emu:clearKeys(0x3FF)
  if frame % 30 < 5 then emu:addKey(0) end
  if frame >= 200 and frame % 20 == 0 and frame <= 1600 then
    emu:screenshot(base .. "/f" .. string.format("%05d", frame) .. ".png")
  end
end)
