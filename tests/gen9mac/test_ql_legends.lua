-- Quest Log, Legends chapter: every row in turn, for comparing two builds by picture (gen9dex: the Area Zero legends'
-- ticks must come out the same with the old numbers and the new). The Quest Log registered to SELECT; the keys
-- that open it are test_ql_panes.lua's (they end with the grid's cursor on Sinnoh, top right); DOWN, LEFT is Legends. A shot of the grid, then of the chapter at each row (leg_NN.png, 0-99).
local E = os.getenv
DIR = E("GEN9_DIR")
NAME = (E("TAG") or "ql") .. "_leg"
dofile("C:/Users/nonth/Desktop/Works & Productivity/gba-trans/hyper-emerald-en-qol/patches/dexnavchain/test_boot.lua")
local plan, t0 = {}, nil
local function at(d, fn) plan[#plan + 1] = {d, fn} end
at(0, function()                                -- SELECT = the Quest Log (item 363), nothing else registered
  local sb1 = emu:read32(0x03005D8C)
  emu:write16(sb1 + 0x496, 363)
  emu:write16(sb1 + 0x9C2, 0); emu:write16(sb1 + 0x9C4, 0); emu:write16(sb1 + 0x9C6, 0)
end)
local t = 10
local function key(k, gap) local kk = k; at(t, function() tap(kk) end); t = t + (gap or 30) end
local function snap(n) local nn = n; at(t, function() shot(NAME .. "_" .. nn) end); t = t + 4 end
key(K.SEL, 60); key(K.UP); key(K.UP); key(K.LEFT); key(K.LEFT); key(K.RIGHT); snap("grid")   -- the ring, then the grid
key(K.DOWN); key(K.LEFT); snap("grid2")
key(K.A, 90); snap("leg_00")
for i = 1, 99 do key(K.DOWN, 14); snap(string.format("leg_%02d", i)) end
key(K.B, 60); key(K.B, 60)
at(t + 200, function() w(string.format("after cb2 %08X lock %d", cb2(), lock())); done() end)
function TEST(f)
  t0 = t0 or f
  for _, p in ipairs(plan) do if f - t0 == p[1] then p[2]() end end
end
