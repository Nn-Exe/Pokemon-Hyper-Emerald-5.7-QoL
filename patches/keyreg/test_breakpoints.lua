local dir = "C:/Users/nonth/AppData/Local/Temp/claude/c--Users-nonth-Desktop-Works---Productivity-gba-trans/02742dae-7df3-4db2-93fc-cf708e28c0df/scratchpad/bagtest/"
local f = 0
local A, B, SELECT, START, RIGHT, LEFT, UP, DOWN = 0, 1, 2, 3, 4, 5, 6, 7
local log = io.open(dir .. "dbg_log.txt", "w")
local function slots()
  local p = emu:read32(0x03005D8C)
  return string.format("%d %d %d %d", emu:read16(p + 0x496), emu:read16(p + 0x9C2), emu:read16(p + 0x9C4), emu:read16(p + 0x9C6))
end
local function probe(tag)
  local t = {}
  for i = 0, 15 do
    local base = 0x03005E00 + i*40
    local fn = emu:read32(base); local act = emu:read8(base+4)
    if act ~= 0 then t[#t+1] = string.format("%d:%08x", i, fn) end
  end
  local sv = ""
  for i = 0, 7 do sv = sv .. string.format("%02x ", emu:read8(0x02021FC4 + i)) end
  log:write(tag .. " tasks=" .. table.concat(t, ",") .. " strvar4=" .. sv .. "\n"); log:flush()
end
local function bp(name, a)
  local ok, err = pcall(function()
    emu:setBreakpoint(function()
      log:write(string.format("f=%d BP %s r0=%08x r1=%08x lr=%08x\n", f, name, emu:readRegister("r0"), emu:readRegister("r1"), emu:readRegister("lr"))); log:flush()
    end, a)
  end)
  if not ok then log:write("setBreakpoint failed: " .. tostring(err) .. "\n"); log:flush() end
end
bp("hook1AD520", 0x081AD520)
bp("usereg", 0x08FD8E48)
bp("draw_popup", 0x08FD8F4A)
bp("popup_task", 0x08FD8FDC)
bp("use_item", 0x08FD8F1E)
log:write("script loaded\n"); log:flush()
callbacks:add("frame", function()
  f = f + 1
  if f < 1900 and f % 90 == 0 then emu:addKey(START) end
  if f < 1900 and f % 90 == 5 then emu:clearKey(START) end
  if f == 2000 then emu:addKey(A) end
  if f == 2004 then emu:clearKey(A) end
  if f == 2700 then emu:addKey(SELECT) end
  if f == 2704 then emu:clearKey(SELECT) end
  if f == 2690 or f == 2760 or f == 2900 then probe("f" .. f); emu:screenshot(dir .. "dbg_" .. f .. ".png"); log:write("f=" .. f .. " slots=" .. slots() .. "\n"); log:flush() end
  if f == 2950 then local fh = io.open(dir .. "dbg_done.txt", "w"); fh:write("done"); fh:close() end
end)
