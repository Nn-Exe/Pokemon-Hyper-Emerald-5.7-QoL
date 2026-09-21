-- Journal from the Bag: move it to the top of Key Items, open the Bag from the start menu, Use it, and
-- screenshot the Bag entry (name, description, icon), the message over the Bag and the Bag after closing.
NAME = "journalbag"
dofile((DIR or "./") .. "../dexnavchain/test_boot.lua")

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
      w("moved the Journal from slot " .. i .. " to the top of Key Items")
    end
  end
end)
at(20, function() tap(K.START) end)
at(80, function() tap(K.DOWN) end)
at(100, function() tap(K.DOWN) end)
at(150, function() tap(K.A) end)                 -- Bag
at(300, function() tap(K.LEFT) end)              -- Items -> Key Items
at(380, function() shot("bag_entry") end)
at(390, function() tap(K.A) end)                 -- the context menu
at(450, function() shot("bag_menu"); tap(K.A) end)   -- Use
for i = 0, 9 do
  at(520 + i * 70, function() shot(string.format("bag_msg_%d", i)); tap(K.A) end)
end
at(1300, function() shot("bag_after"); w("cb2 " .. string.format("%08X", cb2())); done() end)

function TEST(f)
  t0 = t0 or f
  for _, p in ipairs(plan) do if f - t0 == p[1] then p[2]() end end
end
