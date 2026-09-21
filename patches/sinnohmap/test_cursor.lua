-- Hearthome save: open the Sinnoh Map, then walk the marker around and watch the name box.
local dir = "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/_testrun/"
local NL = string.char(10)
local log = io.open(dir .. "cu_log.txt", "w")
local function w(s) log:write(s .. NL); log:flush() end
local f = 0
local A, B, SELECT, START, RIGHT, LEFT, UP, DOWN = 0, 1, 2, 3, 4, 5, 6, 7
local plan = {}
local function at(fr, fn) plan[#plan+1] = {fr, fn} end
local function tap(k, fr) at(fr, function() emu:addKey(k) end); at(fr + 4, function() emu:clearKey(k) end) end
local function boxtext()
  local s, a = "", 0x02021CC4
  for i = 0, 24 do
    local c = emu:read8(a + i)
    if c == 0xFF then break end
    if c >= 0xBB and c <= 0xD4 then s = s .. string.char(65 + c - 0xBB)
    elseif c >= 0xD5 and c <= 0xEE then s = s .. string.char(97 + c - 0xD5)
    elseif c >= 0xA1 and c <= 0xAA then s = s .. string.char(48 + c - 0xA1)
    elseif c == 0 then s = s .. " " else s = s .. "." end
  end
  return s
end
local t = 2400
at(t, function()
  local sb1 = emu:read32(0x03005D8C)
  w(string.format("start: map %d/%d", emu:read8(sb1 + 4), emu:read8(sb1 + 5)))
  local base = emu:read32(0x02039DD8 + 4 * 8)
  local cap = emu:read8(0x02039DD8 + 4 * 8 + 4)
  for i = 0, cap - 1 do
    if emu:read16(base + i * 4) == 361 then
      local a, b = emu:read16(base), emu:read16(base + 2)
      emu:write16(base + i * 4, a); emu:write16(base + i * 4 + 2, b)
      emu:write16(base, 361); emu:write16(base + 2, 1)
    end
  end
end)
tap(START, t + 20)
for i = 0, 1 do tap(DOWN, t + 80 + i * 20) end
tap(A, t + 130)
tap(LEFT, t + 280)
tap(A, t + 340)
tap(A, t + 420)                                  -- Use
at(t + 520, function() emu:screenshot(dir .. "cu_open.png"); w("opened: " .. boxtext()) end)
for k = 0, 5 do at(t + 522 + k * 6, function() emu:screenshot(dir .. string.format("cu_b%d.png", k)) end) end
local d = 560
for i, step in ipairs({LEFT, LEFT, LEFT, UP, UP, RIGHT, RIGHT, DOWN, DOWN, DOWN}) do
  tap(step, t + d)
  at(t + d + 18, function() w(string.format("step %2d -> %s", i, boxtext())) end)
  d = d + 26
end
at(t + d + 20, function() emu:screenshot(dir .. "cu_moved.png") end)
at(t + d + 60, function() local fh = io.open(dir .. "cu_done.txt", "w"); fh:write("done"); fh:close() end)
callbacks:add("frame", function()
  f = f + 1
  if f < 1900 and f % 90 == 0 then emu:addKey(START) end
  if f < 1900 and f % 90 == 5 then emu:clearKey(START) end
  if f == 2000 then emu:addKey(A) end
  if f == 2004 then emu:clearKey(A) end
  for _, p in ipairs(plan) do if f == p[1] then p[2]() end end
end)
