-- Garchomp guardian crash test (test-only ROM: hub door -> Desert Ruins 34/45 warp 2 at (29,2)).
-- Walk to (30,11), face the guardian at (30,12), talk, and record whether the game keeps running.
local dir = "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/tools/test-harness/"
local TAG = TAG or "x"
local f = 0
local A, B, SELECT, START, RIGHT, LEFT, UP, DOWN, R, L = 0, 1, 2, 3, 4, 5, 6, 7, 8, 9
local NL = string.char(10)
local log = io.open(dir .. "hide_" .. TAG .. "_log.txt", "w")
local function px() return emu:read16(0x02037350 + 0x10) - 7 end
local function py() return emu:read16(0x02037350 + 0x12) - 7 end
local function info()
  local sb1 = emu:read32(0x03005D8C)
  return string.format("map=%d/%d pos=%d,%d cb2=%08x", emu:read8(sb1 + 4), emu:read8(sb1 + 5), px(), py(), emu:read32(0x030022C4))
end
local function shot(name) emu:screenshot(dir .. "hide_" .. TAG .. "_" .. name .. ".png"); log:write(name .. " f=" .. f .. " " .. info() .. NL); log:flush() end
local steps = {
  {"wait", 200}, {"shot", "start"},
  {"walk", 10, 3}, {"walk", 16, 3}, {"walk", 16, 1}, {"key", UP, 30}, {"wait", 260}, {"shot", "inside"},
  {"wait", 30}, {"shot", "view"}, {"wait", 90}, {"shot", "view2"},
  {"done"},
}
local si, timer, held, walkT = 1, 0, nil, 0
callbacks:add("frame", function()
  f = f + 1
  if f < 1900 and f % 90 == 0 then emu:addKey(START) end
  if f < 1900 and f % 90 == 5 then emu:clearKey(START) end
  if f == 2000 then emu:addKey(A) end
  if f == 2004 then emu:clearKey(A) end
  if f < 2400 then return end
  local st = steps[si]
  if not st then return end
  local kind = st[1]
  if kind == "shot" then shot(st[2]); si = si + 1
  elseif kind == "done" then shot("end"); local fh = io.open(dir .. "hide_" .. TAG .. "_done.txt", "w"); fh:write("done"); fh:close(); si = si + 1
  elseif kind == "wait" then timer = timer + 1; if timer >= st[2] then timer = 0; si = si + 1 end
  elseif kind == "trace" then
    -- after talking: press A every 40 frames to advance text, log and screenshot periodically
    timer = timer + 1
    if timer % 40 == 1 then emu:addKey(A) elseif timer % 40 == 5 then emu:clearKey(A) end
    if timer % 60 == 0 then shot("t" .. timer) end
    if timer >= st[2] then timer = 0; si = si + 1 end
  elseif kind == "key" then
    if timer == 0 then emu:addKey(st[2]) end
    timer = timer + 1
    if timer > st[3] then emu:clearKey(st[2]); timer = 0; si = si + 1 end
  elseif kind == "walk" then
    local tx, ty, x, y = st[2], st[3], px(), py()
    local d = nil
    if x < tx then d = RIGHT elseif x > tx then d = LEFT elseif y < ty then d = DOWN elseif y > ty then d = UP end
    if d == nil then
      if held then emu:clearKey(held); held = nil end
      timer = timer + 1
      if timer >= 12 then timer = 0; walkT = 0; si = si + 1 end
    else
      if held ~= d then if held then emu:clearKey(held) end; held = d end
      if walkT % 24 >= 21 then emu:clearKey(d) else emu:addKey(d) end
      walkT = walkT + 1
      if walkT > 700 then log:write("walk timeout step " .. si .. " " .. info() .. NL); log:flush(); emu:clearKey(d); held = nil; walkT = 0; si = si + 1 end
    end
  end
end)
