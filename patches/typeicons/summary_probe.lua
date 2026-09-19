-- Open START -> Party -> first Pokemon -> Summary, screenshot, dump sprites and OBJ palette tags
-- (to trace the type icon graphics used by the summary screen).
local dir = "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/_testrun/"
local f = 0
local A, B, SELECT, START, RIGHT, LEFT, UP, DOWN = 0, 1, 2, 3, 4, 5, 6, 7
local NL = string.char(10)
local log = io.open(dir .. "sum_log.txt", "w")
local function dump(tag)
  emu:screenshot(dir .. "sum_" .. tag .. ".png")
  log:write(string.format("== %s cb2=%08x ==", tag, emu:read32(0x030022C4)) .. NL)
  for i = 0, 63 do
    local s = 0x02020630 + i * 0x44
    if emu:read16(s + 0x3E) % 2 == 1 then
      local a0, a1, a2 = emu:read16(s), emu:read16(s + 2), emu:read16(s + 4)
      local tmpl = emu:read32(s + 0x14)
      local tileTag, palTag = 0, 0
      if tmpl >= 0x08000000 and tmpl < 0x0A000000 then tileTag = emu:read16(tmpl); palTag = emu:read16(tmpl + 2) end
      log:write(string.format("spr %2d y=%3d x=%3d shape=%d size=%d pal=%2d tile=%4d tmpl=%08x tileTag=%04x palTag=%04x cb=%08x", i,
        a0 % 256, a1 % 512, math.floor(a0 / 16384), math.floor(a1 / 16384), math.floor(a2 / 4096), a2 % 1024, tmpl, tileTag, palTag, emu:read32(s + 0x1C)) .. NL)
    end
  end
  local t = "paltags:"
  for i = 0, 15 do t = t .. string.format(" %d:%04x", i, emu:read16(0x03000CF0 + i * 2)) end
  log:write(t .. NL); log:flush()
end
local plan = {}
local function at(fr, fn) plan[#plan + 1] = {fr, fn} end
local function tap(key, fr) at(fr, function() emu:addKey(key) end); at(fr + 4, function() emu:clearKey(key) end) end
local t = 2600
tap(START, t + 10)
tap(DOWN, t + 60)
tap(A, t + 90); at(t + 200, function() dump("party") end)
tap(A, t + 220); at(t + 300, function() dump("partymenu") end)
tap(A, t + 320); at(t + 500, function() dump("summary") end)
tap(RIGHT, t + 520); at(t + 600, function() dump("summary2") end)
at(t + 620, function() local fh = io.open(dir .. "sum_done.txt", "w"); fh:write("done"); fh:close() end)
callbacks:add("frame", function()
  f = f + 1
  if f < 1900 and f % 90 == 0 then emu:addKey(START) end
  if f < 1900 and f % 90 == 5 then emu:clearKey(START) end
  if f == 2000 then emu:addKey(A) end
  if f == 2004 then emu:clearKey(A) end
  for _, p in ipairs(plan) do if f == p[1] then p[2]() end end
end)
