local base = "C:/Users/nonth/AppData/Local/Temp/claude/c--Users-nonth-Desktop-Works---Productivity-gba-trans/f184de21-699d-4c79-a35b-04f41a1fd6c9/scratchpad"
local outdir = base .. "/shots_long"
local frame = 0
local log = io.open(base .. "/longplay_heartbeat.txt", "w")

-- key ids: A=0 B=1 SEL=2 START=3 R=4 L=5 U=6 D=7 RB=8 LB=9
local dirs = {6, 7, 5, 4}   -- up down left right

callbacks:add("frame", function()
  frame = frame + 1
  emu:clearKeys(0x3FF)
  if frame < 300 then
    -- title: press start/A
    if frame % 30 < 6 then emu:addKey(3) end
    if frame % 30 >= 15 and frame % 30 < 21 then emu:addKey(0) end
  else
    -- dialogue advance + wander to trigger events
    local c = frame % 90
    if c < 10 then emu:addKey(0)            -- A (advance text / interact)
    elseif c < 40 then emu:addKey(dirs[((frame // 90) % 4) + 1])  -- walk a direction
    elseif c < 50 then emu:addKey(0)        -- A again
    elseif c < 70 then emu:addKey(dirs[((frame // 45) % 4) + 1])  -- walk another dir
    elseif c < 76 then emu:addKey(6)        -- up (for clock event etc.)
    end
  end
  if frame % 60 == 0 then
    log:write(frame .. "\n"); log:flush()
  end
  if frame % 120 == 0 and frame <= 40000 then
    emu:screenshot(outdir .. "/f" .. string.format("%06d", frame) .. ".png")
  end
end)
