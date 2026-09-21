-- Gold stars: forces the one-in-500 all-perfect result (stars = 4), checks the bar draws three gold stars and the
-- start menu still looks right, then steps onto the patch and reads all six IVs as 31.
NAME = "gold2"
dofile((DIR or "./") .. "test_boot.lua")
local ST = 0x0203A660
local function pxy() local id = emu:read8(0x02037595); local o = 0x02037350 + id*0x24; return emu:read16(o+0x10), emu:read16(o+0x12) end
local t0, phase, bstart = nil, "field", 0
function TEST(f)
  t0 = t0 or f
  local r = f - t0
  if cb2() == BATTLE then
    if phase ~= "battle" then phase = "battle"; bstart = f end
    if f - bstart == 420 then
      local b = 0x02024744; local iv = emu:read32(b + 0x48); local t = {}
      for i = 0, 5 do t[#t+1] = tostring((iv >> (i*5)) & 31) end
      w(string.format("foe species %d, IVs %s", emu:read16(b + 0x20), table.concat(t, "/"))); done()
    end
    return
  end
  if r == 20 then tap(K.R) end
  if r == 170 then tap(K.A) end
  if r == 400 then emu:write8(ST+8, 4) end
  if r == 410 then tap(K.START) end
  if r == 470 then shot("gold_menu") end
  if r == 480 then tap(K.B) end
  if r == 600 then shot("gold_bar") end
  if r == 610 then local x, y = pxy(); emu:write8(ST+28, x + 1); emu:write8(ST+29, y); w(string.format("patch set right of the player (%d,%d)", x, y)) end
  if r == 640 then tap(K.RIGHT, 24) end
  if r == 3000 then w("no battle"); done() end
end
