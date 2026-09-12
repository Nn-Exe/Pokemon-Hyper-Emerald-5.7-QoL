local dir = "C:/Users/nonth/AppData/Local/Temp/claude/c--Users-nonth-Desktop-Works---Productivity-gba-trans/02742dae-7df3-4db2-93fc-cf708e28c0df/scratchpad/bagtest/"
local f = 0
local A, B, SELECT, START, RIGHT, LEFT, UP, DOWN = 0, 1, 2, 3, 4, 5, 6, 7
local seq = {}
local function add(fr, key, len) seq[#seq + 1] = {fr, key, len or 4} end
local t = 2000
add(t, A); t = t + 700                 -- CONTINUE -> field
local s_pos0 = t
add(t, SELECT); t = t + 90
add(t, B); t = t + 60                  -- cancel popup
add(t, LEFT, 40); t = t + 80           -- hold LEFT: should walk
local s_walk = t
add(t, RIGHT, 40); t = t + 80          -- walk back
-- bag: deselect Itemfinder (key items idx 2)
add(t, START); t = t + 120
add(t, DOWN); t = t + 40; add(t, DOWN); t = t + 40
add(t, A); t = t + 300
for i = 1, 4 do add(t, RIGHT); t = t + 50 end
add(t, DOWN); t = t + 30; add(t, DOWN); t = t + 30
add(t, A); t = t + 60
local s_ctx = t                        -- expect "Deselect"
add(t, RIGHT); t = t + 40; add(t, A); t = t + 90
local s_desel = t
add(t, B); t = t + 200; add(t, B); t = t + 200
add(t, SELECT); t = t + 90
local s_popup3 = t                     -- slot 2 should now read ------
add(t, B); t = t + 60
local done = t + 30
local shots = {[s_pos0]="n0", [s_walk]="n1walk", [s_ctx]="n2ctx", [s_desel]="n3desel", [s_popup3]="n4popup3"}
local function slots()
  local p = emu:read32(0x03005D8C)
  return string.format("%d %d %d %d", emu:read16(p + 0x496), emu:read16(p + 0x9C2), emu:read16(p + 0x9C4), emu:read16(p + 0x9C6))
end
local function pos() return string.format("pos=%d,%d", emu:read16(0x02037350 + 0x10), emu:read16(0x02037350 + 0x12)) end
local log = io.open(dir .. "reg4_log.txt", "w")
callbacks:add("frame", function()
  f = f + 1
  if f < 1900 and f % 90 == 0 then emu:addKey(START) end
  if f < 1900 and f % 90 == 5 then emu:clearKey(START) end
  for _, s in ipairs(seq) do
    if f == s[1] then emu:addKey(s[2]) end
    if f == s[1] + s[3] then emu:clearKey(s[2]) end
  end
  if shots[f] then
    emu:screenshot(dir .. "n_" .. shots[f] .. ".png")
    log:write(shots[f] .. " f=" .. f .. " slots=" .. slots() .. " " .. pos() .. "\n"); log:flush()
  end
  if f == done then local fh = io.open(dir .. "reg4_done.txt", "w"); fh:write("done"); fh:close() end
end)
