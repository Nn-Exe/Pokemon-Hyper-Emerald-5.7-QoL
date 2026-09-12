local base = "C:/Users/nonth/AppData/Local/Temp/claude/c--Users-nonth-Desktop-Works---Productivity-gba-trans/f184de21-699d-4c79-a35b-04f41a1fd6c9/scratchpad/shots_vlong"
local frame = 0
local hb = io.open("C:/Users/nonth/AppData/Local/Temp/claude/c--Users-nonth-Desktop-Works---Productivity-gba-trans/f184de21-699d-4c79-a35b-04f41a1fd6c9/scratchpad/vlong_hb.txt", "w")
local dirs = {6, 7, 5, 4}
callbacks:add("frame", function()
  frame = frame + 1
  emu:clearKeys(0x3FF)
  if frame < 300 then
    if frame % 30 < 6 then emu:addKey(3) end
    if frame % 30 >= 15 and frame % 30 < 21 then emu:addKey(0) end
  else
    local c = frame % 90
    if c < 10 then emu:addKey(0)
    elseif c < 40 then emu:addKey(dirs[((frame // 90) % 4) + 1])
    elseif c < 50 then emu:addKey(0)
    elseif c < 70 then emu:addKey(dirs[((frame // 45) % 4) + 1])
    elseif c < 76 then emu:addKey(6) end
  end
  if frame % 60 == 0 then hb:write(frame .. "\n"); hb:flush() end
  if frame >= 1200 and frame % 60 == 0 and frame <= 40000 then
    emu:screenshot(base .. "/f" .. string.format("%06d", frame) .. ".png")
  end
end)
