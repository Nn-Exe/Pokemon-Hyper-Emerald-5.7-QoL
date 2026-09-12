local base = "C:/Users/nonth/AppData/Local/Temp/claude/c--Users-nonth-Desktop-Works---Productivity-gba-trans/f184de21-699d-4c79-a35b-04f41a1fd6c9/scratchpad/shots_roam"
local frame = 0
local hb = io.open("C:/Users/nonth/AppData/Local/Temp/claude/c--Users-nonth-Desktop-Works---Productivity-gba-trans/f184de21-699d-4c79-a35b-04f41a1fd6c9/scratchpad/roam_hb.txt", "w")
local dirs = {6, 7, 5, 4}
callbacks:add("frame", function()
  frame = frame + 1
  emu:clearKeys(0x3FF)
  -- dismiss continue menu early, then roam+talk to trigger many NPCs/scripts
  if frame < 200 then
    if frame % 20 < 6 then emu:addKey(0) end
  else
    local c = frame % 80
    if c < 8 then emu:addKey(0)                                  -- talk / advance
    elseif c < 30 then emu:addKey(dirs[((frame // 80) % 4) + 1]) -- walk
    elseif c < 40 then emu:addKey(0)
    elseif c < 62 then emu:addKey(dirs[((frame // 40) % 4) + 1]) -- walk other dir
    elseif c < 70 then emu:addKey(0) end
  end
  if frame % 60 == 0 then hb:write(frame .. "\n"); hb:flush() end
  if frame % 60 == 0 and frame <= 30000 then
    emu:screenshot(base .. "/f" .. string.format("%06d", frame) .. ".png")
  end
end)
