-- Mint quiz-skip test (test-only ROM whose hub door leads to the Trainer's School, map 11/4).
-- Walk in, reach the teacher at (6,3) from (7,3), talk, and check the nature actually changes.
local dir = "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/tools/test-harness/"
local f = 0
local A, B, SELECT, START, RIGHT, LEFT, UP, DOWN, R, L = 0, 1, 2, 3, 4, 5, 6, 7, 8, 9
local NL = string.char(10)
local log = io.open(dir .. "mint2_log.txt", "w")
local PARTY = 0x020244EC
local function px() return emu:read16(0x02037350 + 0x10) - 7 end
local function py() return emu:read16(0x02037350 + 0x12) - 7 end
local function nat() return emu:read8(PARTY + 0x1F) end
local function shot(name)
  emu:screenshot(dir .. "mint2_" .. name .. ".png")
  local sb1 = emu:read32(0x03005D8C)
  log:write(string.format("%s f=%d map=%d/%d pos=%d,%d nature=%d atk=%d spa=%d%s", name, f,
    emu:read8(sb1 + 4), emu:read8(sb1 + 5), px(), py(), nat() & 0x7F,
    emu:read16(PARTY + 0x5A), emu:read16(PARTY + 0x60), NL))
  log:flush()
end
-- steps: {"walk",x,y} {"key",k,frames} {"wait",n} {"shot",name} {"done"}
local steps = {
  {"wait", 200}, {"shot", "start"},
  {"walk", 10, 3}, {"walk", 16, 3}, {"walk", 16, 1}, {"key", UP, 30}, {"wait", 240}, {"shot", "inside"},
  {"walk", 5, 5}, {"walk", 7, 5}, {"walk", 7, 3}, {"key", LEFT, 4}, {"wait", 30}, {"shot", "facing"},
  {"key", A, 4}, {"wait", 130}, {"shot", "talked"},
  {"key", A, 4}, {"wait", 110}, {"shot", "yes"},
  {"wait", 60}, {"shot", "list"},
  {"key", RIGHT, 4}, {"wait", 16}, {"key", RIGHT, 4}, {"wait", 16}, {"key", RIGHT, 4}, {"wait", 40}, {"shot", "cursor"},
  {"key", A, 4}, {"wait", 120}, {"shot", "chosen"},
  {"key", A, 4}, {"wait", 150}, {"shot", "party"},
  {"key", A, 4}, {"wait", 150}, {"shot", "picked_mon"},
  {"key", A, 4}, {"wait", 120}, {"shot", "applied"},
  {"key", A, 4}, {"wait", 120}, {"shot", "after"},
  {"key", B, 4}, {"wait", 120}, {"shot", "done"},
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
  elseif kind == "done" then local fh = io.open(dir .. "mint2_done.txt", "w"); fh:write("done"); fh:close(); si = si + 1
  elseif kind == "wait" then timer = timer + 1; if timer >= st[2] then timer = 0; si = si + 1 end
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
      if walkT > 600 then log:write("walk timeout step " .. si .. NL); log:flush(); emu:clearKey(d); held = nil; walkT = 0; si = si + 1 end
    end
  end
end)
