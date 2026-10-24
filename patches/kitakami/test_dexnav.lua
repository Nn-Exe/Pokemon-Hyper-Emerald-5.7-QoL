-- The DexNav in Kitakami: warp to Mossui Town; R opens the DexNav; a
-- screenshot of its screen (dexnav_<place>.png), B closes it. It reads the wild table this patch moved.
NAME = "dexnav"
dofile((HERE or DIR or "./") .. "../dexnavchain/test_boot.lua")
local SCRIPT = 0x0203F100
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1); emu:write8(0x03000E38, 0)
end
local PLACES = {{"mossui", 35, 106, 22, 34}}
local t0, k, base = nil, 1, 10
function TEST(f)
  t0 = t0 or f
  local d = f - t0
  local p = PLACES[k]
  if not p then if not ENDED then ENDED = true; w("finished"); done() end; return end
  local e = d - base
  if e == 0 then run({0x39, p[2], p[3], 0xFF, p[4], 0, p[5], 0, 0x02}) end
  if e == 240 then tap(K.R) end
  if e == 420 then shot("dexnav_" .. p[1]); w(string.format("%-8s cb2 %08X lock %d", p[1], cb2(), lock())) end
  if e == 440 then tap(K.B) end
  if e == 520 then tap(K.B) end
  if e == 600 then w(string.format("%-8s closed: cb2 %08X lock %d", p[1], cb2(), lock())); k = k + 1; base = d + 10 end
end
