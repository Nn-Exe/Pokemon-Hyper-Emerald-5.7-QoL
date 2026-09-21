-- DexNav list search levels and the spot cry. Seed sector 30 of a scratch save first (every species a level:
-- 999/42/7), then: the list shows "SL n" right-aligned before "Lv.", the header keeps the place name clean with
-- the hint right-aligned, and PlayCry sets 0x020383EC to 2 when a spot appears.
NAME = "levels"
dofile((DIR or "./") .. "test_boot.lua")
local t0, cried = nil, false
function TEST(f)
  t0 = t0 or f
  local r = f - t0
  if emu:read8(0x020383EC) == 2 and not cried then cried = true; w("cry played at +" .. r) end
  if r == 20 then tap(K.R) end
  if r == 170 then shot("levels_p1") end
  if r == 180 then tap(K.RIGHT) end
  if r == 260 then shot("levels_p2") end
  if r == 270 then tap(K.DOWN) end
  if r == 300 then tap(K.A) end
  if r == 330 then tap(K.R) end
  if r == 480 then tap(K.RIGHT) end
  if r == 560 then tap(K.DOWN) end
  if r == 600 then shot("levels_unreg") end
  if r == 620 then w("cry seen: " .. tostring(cried)); done() end
end
