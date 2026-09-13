-- Stat colour test: inject X items into the Items pocket, walk into a wild battle, use X Attack / X Speed /
-- X Special / X Defense over four turns, screenshot the "rose!" messages and dump the BG palettes.
local dir = "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/tools/test-harness/"
local f = 0
local A, B, SELECT, START, RIGHT, LEFT, UP, DOWN, R, L = 0, 1, 2, 3, 4, 5, 6, 7, 8, 9
local log = io.open(dir .. "statcol1_log.txt", "w")
local function inBattle() return emu:read32(0x030022C4) == 0x08038421 end
local function shot(name) emu:screenshot(dir .. "sc_" .. name .. ".png"); log:write(name .. " f=" .. f .. "\n"); log:flush() end
local function dumpPal()
  for bank = 0, 15 do
    local s = {}
    for i = 0, 15 do s[#s + 1] = string.format("%04x", emu:read16(0x05000000 + bank * 32 + i * 2)) end
    log:write(string.format("bgpal%02d %s\n", bank, table.concat(s, " ")))
  end
  log:flush()
end
local phase = "boot"; local m = 0; local step = 0; local turn = 0; local plan = {}
local function tapAt(fr, key) plan[#plan + 1] = {fr, key, true}; plan[#plan + 1] = {fr + 4, key, false} end
local function useItemTurn(t0, turnNo)
  plan[#plan + 1] = {t0 - 10, "shot", "menu" .. turnNo}; tapAt(t0, RIGHT); tapAt(t0 + 20, A)                   -- BAG
  plan[#plan + 1] = {t0 + 100, "shot", "bag" .. turnNo}
  for d = 1, turnNo - 1 do tapAt(t0 + 60 + d * 12, DOWN) end   -- turn n uses item n
  tapAt(t0 + 120, A)                                    -- select item
  tapAt(t0 + 170, A)                                    -- Use
  plan[#plan + 1] = {t0 + 230, "shot", "t" .. turnNo .. "_a"}
  plan[#plan + 1] = {t0 + 290, "shot", "t" .. turnNo .. "_b"}
  plan[#plan + 1] = {t0 + 350, "shot", "t" .. turnNo .. "_c"}
  if turnNo == 1 then plan[#plan + 1] = {t0 + 290, "pal", ""} end
  for k = 1, 9 do tapAt(t0 + 400 + k * 70, B) end       -- advance through the rest of the turn (B never picks Fight)
end
callbacks:add("frame", function()
  f = f + 1
  if f < 1900 and f % 90 == 0 then emu:addKey(START) end
  if f < 1900 and f % 90 == 5 then emu:clearKey(START) end
  if f == 2000 then emu:addKey(A) end
  if f == 2004 then emu:clearKey(A) end
  if f == 2600 then
    local slots = 0x0203D030
    local items = {{75, 5}, {77, 5}, {79, 5}, {76, 5}}   -- X Attack, X Speed, X Special, X Defense
    for i, it in ipairs(items) do emu:write16(slots + (i - 1) * 4, it[1]); emu:write16(slots + (i - 1) * 4 + 2, it[2]) end
    phase = "walk"; m = f
  end
  if phase == "walk" then
    local k = math.floor((f - m) / 40) % 2
    if k == 0 then emu:clearKey(RIGHT); emu:addKey(LEFT) else emu:clearKey(LEFT); emu:addKey(RIGHT) end
    if inBattle() then
      emu:clearKey(LEFT); emu:clearKey(RIGHT); phase = "battle"; m = f
      log:write("battle at f=" .. f .. "\n"); log:flush()
      for _, d in ipairs({900, 1100, 1300, 1400}) do tapAt(m + d, B) end   -- dismiss intro texts
      local t0 = m + 1500                                -- action menu is up by now
      for turnNo = 1, 4 do useItemTurn(t0 + (turnNo - 1) * 1200, turnNo) end
      local t5 = t0 + 4 * 1200
      plan[#plan + 1] = {t5 - 10, "shot", "menu5"}
      tapAt(t5, A); tapAt(t5 + 40, A)                        -- Fight -> first move (Hammer Arm: user's Speed falls)
      for k = 1, 14 do plan[#plan + 1] = {t5 + 60 + k * 45, "shot", "fight_" .. k} end
      plan[#plan + 1] = {t5 + 400, "pal", ""}
      plan[#plan + 1] = {t5 + 800, "done", ""}
    end
    if f - m > 6000 then log:write("no battle\n"); log:flush(); local fh = io.open(dir .. "statcol1_done.txt", "w"); fh:write("done"); fh:close(); phase = "done" end
  elseif phase == "battle" then
    for _, p in ipairs(plan) do
      if f == p[1] then
        if p[2] == "shot" then shot(p[3])
        elseif p[2] == "pal" then dumpPal()
        elseif p[2] == "done" then local fh = io.open(dir .. "statcol1_done.txt", "w"); fh:write("done"); fh:close(); phase = "done"
        elseif p[3] then emu:addKey(p[2]) else emu:clearKey(p[2]) end
      end
    end
  end
end)
