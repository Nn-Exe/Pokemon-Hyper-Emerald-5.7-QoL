-- Sell one item at the Lilycove clerk, as the player does: additem ITEM x2, warp above the counter, talk, Sell,
-- the Items pocket's last item, one, Yes. Money (SaveBlock1 +0x490 xor SaveBlock2 +0xAC) and the item's count in the
-- Items pocket (bagslots: 200 slots at 0x0203DAE0, quantity xor the key's low half) before and after.
local E = os.getenv
DIR = E("GEN9_DIR")
local TAG = E("TAG") or "ms"
NAME = TAG .. "_sell"
dofile("C:/Users/nonth/Desktop/Works & Productivity/gba-trans/hyper-emerald-en-qol/patches/dexnavchain/test_boot.lua")
local ITEM = tonumber(E("ITEM") or "770")
local SCRIPT = 0x0203F100
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
  emu:setBreakpoint(function() if not crashed then crashed = true; w(string.format("VECTOR %02X lr %08X", v, emu:readRegister("lr"))) end end, v)
end
local function key() return emu:read32(emu:read32(0x03005D90) + 0xAC) end
local function money() return emu:read32(emu:read32(0x03005D8C) + 0x490) ~ key() end
local function count()
  local n = 0
  for s = 0, 199 do
    local a = 0x0203DAE0 + 4 * s
    if emu:read16(a) == ITEM then n = n + ((emu:read16(a + 2) ~ (key() & 0xFFFF)) & 0xFFFF) end
  end
  return n
end
local t0, done_ = nil, false
function TEST(f)
  t0 = t0 or f
  local d = f - t0
  if done_ then return end
  if d == 5 then run({0x44, ITEM & 0xFF, ITEM >> 8, 2, 0, 0x02}) end
  if d == 60 then
    emu:write8(0x0203CE58 + 5, 0)
    w(string.format("before: money %d, item %d x%d", money(), ITEM, count()))
    run({0x39, 13, 19, 0xFF, 7, 0, 4, 0, 0x02})
  end
  if d == 360 then tap(K.DOWN, 3) end
  if d == 390 then tap(K.A) end
  if d == 440 then tap(K.A) end
  if d == 550 then shot(NAME .. "_0menu"); tap(K.DOWN) end
  if d == 580 then tap(K.A) end                       -- Sell
  if d == 760 then shot(NAME .. "_1bag"); emu:addKey(K.DOWN) end
  if d == 1500 then emu:clearKey(K.DOWN) end
  if d == 1530 then tap(K.UP) end
  if d == 1600 then shot(NAME .. "_2item"); tap(K.A) end                  -- the item
  if d == 1700 then shot(NAME .. "_3howmany"); tap(K.A) end               -- one
  if d == 1800 then shot(NAME .. "_4price"); tap(K.A) end                 -- Yes
  if d == 1900 then shot(NAME .. "_5after"); tap(K.A) end
  if d == 2000 then shot(NAME .. "_6"); tap(K.A) end
  if d == 2100 or crashed then
    w(string.format("after: money %d, item %d x%d", money(), ITEM, count()))
    w(crashed and "CRASHED" or "no crash")
    done_ = true; done()
  end
end
