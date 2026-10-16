-- Use an evolution item from the Bag on the lead, as the player does: additem ITEM; START -> Bag (Items pocket) ->
-- the last item -> Use -> the first Pokemon -> the evolution scene, A through it, B back to the field.
-- SPECIES LEVEL ITEM TARGET. Logs the lead before and after; screenshots on the way.
local E = os.getenv
DIR = E("GEN9_DIR")
local TAG = E("TAG") or "ui"
NAME = TAG .. "_use"
dofile("C:/Users/nonth/Desktop/Works & Productivity/gba-trans/hyper-emerald-en-qol/patches/dexnavchain/test_boot.lua")
local SPECIES, LEVEL, ITEM, TARGET = tonumber(E("SPECIES")), tonumber(E("LEVEL") or "30"), tonumber(E("ITEM")), tonumber(E("TARGET"))
local SCRIPT, PARTY = 0x0203F100, 0x020244EC
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1); emu:write8(0x03000E38, 0)
end
local crashed = false
for _, v in ipairs({0x00000000, 0x00000004, 0x0000000C, 0x00000010}) do
  emu:setBreakpoint(function()
    if not crashed then crashed = true; w(string.format("VECTOR %02X lr %08X", v, emu:readRegister("lr"))) end
  end, v)
end
local ncall = 0
emu:setBreakpoint(function()
  ncall = ncall + 1
  if ncall <= 12 then
    w(string.format("evo-target(species %d, mode %d, item %d) from %08X", emu:read16(emu:readRegister("r0") + 0x20),
      emu:readRegister("r1"), emu:readRegister("r2"), emu:readRegister("lr")))
  end
end, 0x09F0534C)
local function lead() return string.format("species %d lv %d item %d", emu:read16(PARTY + 0x20), emu:read8(PARTY + 0x54), emu:read16(PARTY + 0x22)) end
local t0, done_ = nil, false
function TEST(f)
  t0 = t0 or f
  local d = f - t0
  if done_ then return end
  if d == 5 then
    emu:write8(0x020244E9, 5)
    for i = 0, 99 do emu:write8(PARTY + 500 + i, 0) end
    run({0x79, SPECIES & 0xFF, SPECIES >> 8, LEVEL, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0x02})
  end
  if d == 60 then
    for i = 0, 99 do emu:write8(PARTY + i, emu:read8(PARTY + 500 + i)) end
    w("before: lead " .. lead())
    run({0x44, ITEM & 0xFF, ITEM >> 8, 1, 0, 0x02})
  end
  if d == 100 then emu:write8(0x03000F2C, 0); emu:write8(0x0203CE58 + 5, 0) end   -- the Items pocket
  if d == 120 then tap(K.START) end
  if d == 180 then tap(K.DOWN) end
  if d == 196 then tap(K.DOWN) end
  if d == 230 then tap(K.A) end
  if d == 380 then emu:addKey(K.DOWN) end
  if d == 1160 then emu:clearKey(K.DOWN) end
  if d == 1190 then tap(K.UP) end
  if d == 1260 then shot(NAME .. "_0list"); tap(K.A) end           -- the item's menu
  if d == 1330 then shot(NAME .. "_1menu"); tap(K.A) end           -- Use
  if d == 1480 then shot(NAME .. "_2party"); tap(K.A) end          -- the first Pokemon
  if d > 1480 and d < 4200 and (d - 1480) % 40 == 0 then
    if (d - 1480) % 400 == 0 then shot(string.format("%s_3_%04d", NAME, d - 1480)) end
    if emu:read16(PARTY + 0x20) == TARGET then tap(K.B) else tap(K.A) end
  end
  if d > 4200 and d < 4600 and d % 40 == 0 then tap(K.B) end
  if d == 4600 or crashed then
    shot(NAME .. "_4end")
    w("after: lead " .. lead())
    w(crashed and "CRASHED" or (emu:read16(PARTY + 0x20) == TARGET and "EVOLVED into the target" or "did NOT become the target"))
    done_ = true; done()
  end
end
