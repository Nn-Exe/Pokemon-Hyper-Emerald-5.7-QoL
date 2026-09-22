-- Quest Log chapter grid: open from SELECT (grid, current chapter selected), move to Legends and open it, B
-- back to the grid, open Side Content and a row, then B out to the field. Screenshots g*_*.png.
NAME = "questlog_grid"
DIR = DIR or "./"
dofile(DIR .. "../dexnavchain/test_boot.lua")
local plan, t0 = {}, nil
local function at(d, fn) plan[#plan + 1] = {d, fn} end
at(0, function()
  local sb1 = emu:read32(0x03005D8C)
  emu:write16(sb1 + 0x496, 363)
  emu:write16(sb1 + 0x9C2, 0); emu:write16(sb1 + 0x9C4, 0); emu:write16(sb1 + 0x9C6, 0)
end)
local seq = {
  {10, K.SEL}, {60, K.UP}, {220, nil, "g1_grid"},
  {230, K.DOWN}, {260, K.LEFT}, {290, nil, "g2_moved"}, {300, K.A}, {340, nil, "g3_legends"},
  {350, K.B}, {390, nil, "g4_back"}, {400, K.LEFT}, {430, K.DOWN}, {460, nil, "g5_side_sel"},
  {470, K.A}, {510, nil, "g6_side"}, {520, K.A}, {560, nil, "g7_detail"},
  {570, K.B}, {600, K.B}, {640, K.B}, {840, nil, "g8_field"},
}
for _, x in ipairs(seq) do
  at(x[1], function()
    if x[2] then tap(x[2]) end
    if x[3] then shot(x[3]); w(string.format("%s cb2 %08X lock %d", x[3], cb2(), lock())) end
  end)
end
at(850, function() done() end)
function TEST(f)
  t0 = t0 or f
  for _, p in ipairs(plan) do if f - t0 == p[1] then p[2]() end end
end
