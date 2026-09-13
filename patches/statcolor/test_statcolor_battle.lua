-- Battle textbox colour probe: dismiss the intro, Fight -> Hammer Arm (user's Speed falls), screenshot the message.
local dir = "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/tools/test-harness/"
local f = 0
local A, B, SELECT, START, RIGHT, LEFT, UP, DOWN, R, L = 0, 1, 2, 3, 4, 5, 6, 7, 8, 9
local NL = string.char(10)
local log = io.open(dir .. "statcol2_log.txt", "w")
local function inBattle() return emu:read32(0x030022C4) == 0x08038421 end
local function shot(name) emu:screenshot(dir .. "sc2_" .. name .. ".png"); log:write(name .. " f=" .. f .. NL); log:flush() end
local function dumpPal(tag)
  local s = {}
  for i = 0, 15 do s[#s + 1] = string.format("%04x", emu:read16(0x05000000 + i * 2)) end
  log:write("bgpal00@" .. tag .. " " .. table.concat(s, " ") .. NL); log:flush()
end
local phase = "boot"; local m = 0; local plan = {}
local function tapAt(fr, key) plan[#plan + 1] = {fr, key, true}; plan[#plan + 1] = {fr + 4, key, false} end
callbacks:add("frame", function()
  f = f + 1
  if f < 1900 and f % 90 == 0 then emu:addKey(START) end
  if f < 1900 and f % 90 == 5 then emu:clearKey(START) end
  if f == 2000 then emu:addKey(A) end
  if f == 2004 then emu:clearKey(A) end
  if f == 2600 then phase = "walk"; m = f end
  if phase == "walk" then
    local k = math.floor((f - m) / 40) % 2
    if k == 0 then emu:clearKey(RIGHT); emu:addKey(LEFT) else emu:clearKey(LEFT); emu:addKey(RIGHT) end
    if inBattle() then
      emu:clearKey(LEFT); emu:clearKey(RIGHT); phase = "battle"; m = f
      log:write("battle at f=" .. f .. NL); log:flush()
      for _, d in ipairs({900, 1100, 1300, 1400}) do tapAt(m + d, B) end
      plan[#plan + 1] = {m + 800, "moves", ""}; plan[#plan + 1] = {m + 1450, "moves", ""}
      local t0 = m + 1500
      plan[#plan + 1] = {t0 - 10, "shot", "menu"}
      tapAt(t0, LEFT); tapAt(t0 + 20, UP); tapAt(t0 + 40, A); tapAt(t0 + 100, A)   -- Fight, move 1 (Swords Dance)
      for k = 1, 12 do plan[#plan + 1] = {t0 + 120 + k * 45, "shot", "sd_" .. k} end
      plan[#plan + 1] = {t0 + 400, "pal", "a"}
      for k = 1, 6 do tapAt(t0 + 700 + k * 60, B) end
      local t1 = t0 + 1200
      plan[#plan + 1] = {t1 - 10, "shot", "menu2"}
      tapAt(t1, A); tapAt(t1 + 40, RIGHT); tapAt(t1 + 80, A)                       -- Fight, move 2 (Tail Whip)
      for k = 1, 22 do plan[#plan + 1] = {t1 + 100 + k * 45, "shot", "tw_" .. k} end
      plan[#plan + 1] = {t1 + 1150, "done", ""}
    end
    if f - m > 6000 then local fh = io.open(dir .. "statcol2_done.txt", "w"); fh:write("done"); fh:close(); phase = "done" end
  elseif phase == "battle" then
    for _, p in ipairs(plan) do
      if f == p[1] then
        if p[2] == "shot" then shot(p[3])
        elseif p[2] == "pal" then dumpPal(p[3])
        elseif p[2] == "moves" then
          local bm = 0x02024084
          emu:write16(bm + 0x0C, 14); emu:write16(bm + 0x0E, 39)   -- Swords Dance, Tail Whip
          emu:write8(bm + 0x24, 20); emu:write8(bm + 0x25, 20)
        elseif p[2] == "done" then local fh = io.open(dir .. "statcol2_done.txt", "w"); fh:write("done"); fh:close(); phase = "done"
        elseif p[3] then emu:addKey(p[2]) else emu:clearKey(p[2]) end
      end
    end
  end
end)
