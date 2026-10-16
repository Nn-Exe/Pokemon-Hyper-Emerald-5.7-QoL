-- The TM screen: ABLE / NOT ABLE for a party of new Pokemon.
--   LIST=a,b,c,d,e,f: the party is exactly these (givemon Lv 50). TMROW=n: the n-th TM of the TM pocket (from 0).
--   START -> Bag (the TM pocket) -> that TM -> Use -> A through "Booted up a TM" / "Teach it?" -> the party screen
--   with ABLE / NOT ABLE under each one: tm_able.png. Logged: the TM pocket (item, count field) and the party.
--   The TM pocket is in the hack's save stream (0x0203D308: Items, Key, Balls before it; 130 slots of 4 bytes).
local E = os.getenv
DIR = E("GEN9_DIR")
NAME = (E("TAG") or "tm") .. "_tm"
dofile("C:/Users/nonth/Desktop/Works & Productivity/gba-trans/hyper-emerald-en-qol/patches/dexnavchain/test_boot.lua")
local LIST = {}
for n in (E("LIST") or ""):gmatch("%d+") do LIST[#LIST + 1] = tonumber(n) end
local ROW = tonumber(E("TMROW") or "0")
local SCRIPT, PARTY, TMPOCKET = 0x0203F100, 0x020244EC, 0x0203D308
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1); emu:write8(0x03000E38, 0)
end
local function give(sp, lv) run({0x79, sp & 0xFF, sp >> 8, lv, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0x02}) end
local plan, t0 = {}, nil
local function at(d, fn) plan[#plan + 1] = {d, fn} end
local function key(t, k) at(t, function() tap(k) end) end
at(2, function()
  local t = {}
  for i = 0, 129 do
    local it = emu:read16(TMPOCKET + 4 * i)
    if it ~= 0 then t[#t + 1] = string.format("%d:%d", i, it) end
  end
  w("TM pocket (slot:item): " .. table.concat(t, " "))
  emu:write8(0x020244E9, 0); for i = 0, 599 do emu:write8(PARTY + i, 0) end
end)
for i, sp in ipairs(LIST) do at(2 + 25 * i, function() give(sp, 50) end) end
local T = 2 + 25 * (#LIST + 1)
at(T, function()
  local t = {}
  for i = 0, 5 do t[#t + 1] = emu:read16(PARTY + 100 * i + 0x20) end
  w("party: " .. table.concat(t, " "))
  emu:write8(0x03000F2C, 0)
  emu:write8(0x0203CE58 + 5, 2)                  -- gBagPosition.pocket: TMs & HMs
end)
key(T + 20, K.START); key(T + 80, K.DOWN); key(T + 96, K.DOWN); key(T + 130, K.A)   -- Bag
for k = 0, ROW - 1 do key(T + 270 + k * 12, K.DOWN) end
local t = T + 270 + ROW * 12 + 20
at(t, function() shot(NAME .. "_pocket") end)
key(t + 10, K.A); key(t + 60, K.A)              -- the TM, Use
local NA = tonumber(E("NA") or "3")
for k = 1, NA do key(t + 60 + 60 * k, K.A) end  -- "Booted up a TM." ... "Teach it?" Yes
if E("SCOUT") then for k = 0, 14 do local kk = k; at(t + 50 + 50 * kk, function() shot(string.format("%s_s%02d", NAME, kk)) end) end end
at(t + 420, function() shot(NAME .. "_able") end)
key(t + 780, K.B); key(t + 900, K.B); key(t + 1000, K.B); key(t + 1100, K.B)
at(t + 1400, function() w(string.format("after: cb2 %08X lock %d", cb2(), lock())); done() end)
function TEST(f)
  t0 = t0 or f
  for _, p in ipairs(plan) do if f - t0 == p[1] then p[2]() end end
end
