-- Patch arrow: puts the patch left, right, above, below and diagonally from the player; the bar must show one
-- arrow in its top right corner - sideways first, then up/down once lined up. Check the screenshots.
NAME = "arrow2"
dofile((DIR or "./") .. "test_boot.lua")
local ST = 0x0203A660
local function pxy() local id = emu:read8(0x02037595); local o = 0x02037350 + id*0x24; return emu:read16(o+0x10), emu:read16(o+0x12) end
-- the patch is put where each arrow must show: left, right, up, down, then lined up sideways
local cases = {{-2, 0, "left"}, {3, 0, "right"}, {0, -3, "up"}, {0, 1, "down"}, {-1, -2, "left first"}, {2, 1, "right first"}}
local t0
function TEST(f)
  t0 = t0 or f
  local r = f - t0
  if r == 20 then tap(K.R) end
  if r == 170 then tap(K.A) end
  local i = (r - 400) // 30 + 1
  if r >= 400 and i <= #cases and (r - 400) % 30 == 0 then
    local x, y = pxy(); emu:write8(ST+28, x + cases[i][1]); emu:write8(ST+29, y + cases[i][2])
  end
  if r >= 400 and i <= #cases and (r - 400) % 30 == 20 then
    local g = emu:read8(0x02020004 + emu:read8(ST+14) * 12 + 8)
    shot(string.format("ar_%d", i)); w("case " .. i .. " expects " .. cases[i][3])
  end
  if r == 400 + 30 * #cases + 5 then done() end
end
