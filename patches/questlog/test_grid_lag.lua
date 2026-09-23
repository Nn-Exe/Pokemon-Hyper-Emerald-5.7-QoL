-- Quest Log chapter grid: press a direction and screenshot every frame after it, to see how many frames pass
-- before the screen changes. Also logs the cursor byte (V+0) each frame. Run next to game.gba/game.sav.
NAME = "gridlag"
dofile((DIR or "./") .. "../dexnavchain/test_boot.lua")
local TASK = tonumber(os.getenv("TASK_FN") or "0x08FEA891")
local t0, plan, V = nil, {}, 0
local shooting, shotbase = 0, 0
local function at(d, fn) plan[#plan + 1] = {d, fn} end
local function findV()                      -- the task's data[0..1] holds the block; V = block + 0x800
  for i = 0, 15 do
    local t = 0x03005E00 + i * 40
    if emu:read32(t) == TASK then return emu:read32(t + 8) + 0x800 end
  end
  return 0
end
at(0, function()
  local sb1 = emu:read32(0x03005D8C)
  emu:write16(sb1 + 0x496, 363)
  emu:write16(sb1 + 0x9C2, 0); emu:write16(sb1 + 0x9C4, 0); emu:write16(sb1 + 0x9C6, 0)
end)
at(10, function() tap(K.SEL) end)
at(60, function() tap(K.UP) end)
at(230, function()
  V = findV()
  w(string.format("grid open, V %08X, cursor %d", V, V ~= 0 and emu:read8(V) or -1))
end)
at(250, function() tap(K.RIGHT); shooting = 20; shotbase = 0; w("RIGHT pressed") end)
at(320, function() tap(K.DOWN); shooting = 20; shotbase = 100; w("DOWN pressed") end)
at(400, function() done() end)
function TEST(f)
  t0 = t0 or f
  local d = f - t0
  for _, p in ipairs(plan) do if d == p[1] then p[2]() end end
  if shooting > 0 then
    local n = 20 - shooting
    shot(string.format("g%03d", shotbase + n))
    if V ~= 0 then w(string.format("  frame +%d cursor %d", n, emu:read8(V))) end
    shooting = shooting - 1
  end
end
