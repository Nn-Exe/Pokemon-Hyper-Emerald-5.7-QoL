-- Quest Log screens: open it from the Bag (Key Items, Use), then walk it - a detail, back, Up, chapters with L/R
-- and Left/Right, scrolling to the bottom of Post-game and Lost Artifacts, the closing row - screenshotting
-- each step (q_*.png), and B back to the field. Run next to game.gba/game.sav copies with DIR set.
NAME = "questlog_screens"
DIR = DIR or "./"
dofile(DIR .. "../dexnavchain/test_boot.lua")
local JOURNAL = 363
local plan, t0 = {}, nil
local function at(d, fn) plan[#plan + 1] = {d, fn} end
at(0, function()
  local base = emu:read32(0x02039DD8 + 4 * 8)
  local cap = emu:read8(0x02039DD8 + 4 * 8 + 4)
  for i = 0, cap - 1 do
    if emu:read16(base + i * 4) == JOURNAL then
      local a, b = emu:read16(base), emu:read16(base + 2)
      local qa, qb = emu:read16(base + i * 4), emu:read16(base + i * 4 + 2)
      emu:write16(base + i * 4, a); emu:write16(base + i * 4 + 2, b)
      emu:write16(base, qa); emu:write16(base + 2, qb)
      w("moved the Journal from slot " .. i)
    end
  end
end)
at(20, function() tap(K.START) end)
at(80, function() tap(K.DOWN) end)
at(100, function() tap(K.DOWN) end)
at(150, function() tap(K.A) end)
at(300, function() tap(K.LEFT) end)
at(390, function() tap(K.A) end)
at(450, function() tap(K.A) end)
at(650, function() shot("ql_1"); w(string.format("cb2 %08X", cb2())) end)
local t = 660
local seq = {
  {K.A, "d_badges1"}, {K.B, "back"},
  {K.UP, "up"}, {K.A, "d_sail"}, {K.B, "back2"},
  {K.L, "post"}, {K.DOWN, nil}, {K.DOWN, nil}, {K.DOWN, "post_dn3"},
}
for i = 1, 30 do seq[#seq + 1] = {K.DOWN, i == 30 and "post_bottom" or nil} end
for _, x in ipairs({{K.A, "d_post_last"}, {K.B, nil}, {K.L, "hoenn"}, {K.LEFT, "hoenn2"}, {K.RIGHT, nil}, {K.RIGHT, nil},
                    {K.R, "lost"}, {K.R, "lost_r"}}) do seq[#seq + 1] = x end
for i = 1, 20 do seq[#seq + 1] = {K.DOWN, i == 20 and "lost_bottom" or nil} end
seq[#seq + 1] = {K.A, "d_final"}
seq[#seq + 1] = {K.B, nil}
seq[#seq + 1] = {K.B, nil}
for i, x in ipairs(seq) do
  at(t, function() tap(x[1]) end)
  if x[2] then at(t + 30, function() shot("q_" .. x[2]) end) end
  t = t + 40
end
at(t + 200, function() shot("q_field"); w(string.format("after cb2 %08X lock %d", cb2(), lock())); done() end)
function TEST(f)
  t0 = t0 or f
  for _, p in ipairs(plan) do if f - t0 == p[1] then p[2]() end end
end
