-- Open the Fly map (CB2_OpenFlyMap 0x08124691, what the party menu's Fly calls) from the field and take a
-- screenshot fly_map.png. Run once on the ROM before the patch as a control. Set DIR and HERE.
NAME = "flyicons"
DIR = DIR or "./"
HERE = HERE or DIR
dofile(HERE .. "../dexnavchain/test_boot.lua")
local plan, t0 = {}, nil
local function at(d, fn) plan[#plan + 1] = {d, fn} end
at(30, function() emu:write32(0x030022C4, 0x08124691) end)
at(200, function() shot("fly_map") end)
at(210, function() tap(K.B) end)
at(400, function() w("after B: cb2 " .. string.format("%08X", cb2())); done() end)
function TEST(f)
  t0 = t0 or f
  for _, p in ipairs(plan) do if f - t0 == p[1] then p[2]() end end
end
