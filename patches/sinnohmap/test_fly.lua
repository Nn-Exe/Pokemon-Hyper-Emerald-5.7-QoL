-- From Hearthome: open the map, hop to a town, press A, and see whether the courier script takes us there.
local dir = "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/_testrun/"
local NL = string.char(10)
local log = io.open(dir .. "fly_log.txt", "w")
local function w(s) log:write(s .. NL); log:flush() end
local f = 0
local A, B, SELECT, START, RIGHT, LEFT, UP, DOWN = 0, 1, 2, 3, 4, 5, 6, 7
local HOPS = os.getenv("FLY_HOPS") or "L,L,L"
local plan = {}
local function at(fr, fn) plan[#plan+1] = {fr, fn} end
local function tap(k, fr) at(fr, function() emu:addKey(k) end); at(fr + 4, function() emu:clearKey(k) end) end
local function where()
  local sb1 = emu:read32(0x03005D8C)
  return string.format("map %d/%d pos (%d,%d) cb2 %08X", emu:read8(sb1 + 4), emu:read8(sb1 + 5),
    emu:read16(sb1), emu:read16(sb1 + 2), emu:read32(0x030022C4))
end
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
  w("start: " .. where())
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
at(t + 520, function() w("map open: " .. boxtext()) end)
local d = 560
local keys = {L = LEFT, R = RIGHT, U = UP, D = DOWN}
for k in HOPS:gmatch("[LRUD]") do
  tap(keys[k], t + d)
  at(t + d + 18, function() w("hop " .. k .. " -> " .. boxtext()) end)
  d = d + 26
end
at(t + d, function() emu:screenshot(dir .. "fly_pick.png") end)
tap(A, t + d + 10)                               -- fly!
for i = 1, 8 do
  at(t + d + 10 + i * 60, function() w(string.format("+%ds: %s", i, where())) end)
end
at(t + d + 500, function() emu:screenshot(dir .. "fly_after.png") end)
at(t + d + 520, function() local fh = io.open(dir .. "fly_done.txt", "w"); fh:write("done"); fh:close() end)
callbacks:add("frame", function()
  f = f + 1
  if f < 1900 and f % 90 == 0 then emu:addKey(START) end
  if f < 1900 and f % 90 == 5 then emu:clearKey(START) end
  if f == 2000 then emu:addKey(A) end
  if f == 2004 then emu:clearKey(A) end
  for _, p in ipairs(plan) do if f == p[1] then p[2]() end end
end)
