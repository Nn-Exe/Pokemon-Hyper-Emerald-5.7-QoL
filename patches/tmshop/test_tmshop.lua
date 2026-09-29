-- Lilycove Dept. Store TM clerk: warp onto the TM floor (13/19) at (9,4), across the counter from him at (9,6),
-- talk, Buy, and buy TM01 (row 0),
-- TM109 (row 100) and TM120 (row 111, the last), logging money and TM counts after each. A purchase the hack's
-- sellable check rejects soft-resets, which shows as cb2 leaving the field/shop and the map changing. TM counts
-- are quantities.
-- Run next to game.gba/game.sav with DIR set; screenshots tm_*.png.
NAME = "tmshop"
dofile((DIR or "./") .. "../dexnavchain/test_boot.lua")
local SCRIPT = 0x0203F100
local t0, plan = nil, {}
local function at(d, fn) plan[#plan + 1] = {d, fn} end
local function count(item)
  local total = 0
  for pocket = 0, 4 do
    local base = emu:read32(0x02039DD8 + pocket * 8)
    local cap = emu:read8(0x02039DD8 + pocket * 8 + 4)
    if base >= 0x02000000 and base < 0x03000000 and cap > 0 and cap < 250 then
      for i = 0, cap - 1 do
        if emu:read16(base + i * 4) == item then total = total + emu:read16(base + i * 4 + 2) end
      end
    end
  end
  return total
end
local function money()
  local sb1, sb2 = emu:read32(0x03005D8C), emu:read32(0x03005D90)
  return emu:read32(sb1 + 0x490) ~ emu:read32(sb2 + 0xAC)
end
local function set_money(v)
  local sb1, sb2 = emu:read32(0x03005D8C), emu:read32(0x03005D90)
  emu:write32(sb1 + 0x490, v ~ emu:read32(sb2 + 0xAC))
end
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1)
  emu:write8(0x03000E38, 0)
end
local function state(tag)
  local sb1 = emu:read32(0x03005D8C)
  w(string.format("%s: map %d/%d pos (%d,%d) cb2 %08X money %d TM01 %d TM100 %d TM109 %d TM120 %d", tag,
    emu:read8(sb1 + 4), emu:read8(sb1 + 5), emu:read16(sb1), emu:read16(sb1 + 2), cb2(), money(),
    count(378), count(477), count(486), count(497)))
end
-- buy the highlighted row: A (item), A (quantity 1), A (YES), then one A to close "Here you go" - a second A
-- would open the same row again
local function buy(d, tag)
  at(d, function() tap(K.A) end)
  at(d + 60, function() shot("tm_" .. tag .. "_qty") end)
  at(d + 70, function() tap(K.A) end)
  at(d + 130, function() shot("tm_" .. tag .. "_confirm") end)
  at(d + 140, function() tap(K.A) end)
  at(d + 260, function() tap(K.A) end)
  at(d + 470, function() state("after " .. tag); shot("tm_" .. tag .. "_done") end)
end
at(10, function() set_money(999999); state("start"); run({0x39, 13, 19, 0xFF, 9, 0, 4, 0, 0x02}) end)
at(300, function() state("warped"); shot("tm_floor") end)
at(310, function() tap(K.DOWN) end)                           -- he is inside the booth; talk across row 5
at(350, function() tap(K.A) end)
at(470, function() shot("tm_talk") end)
at(480, function() tap(K.A) end)
at(580, function() shot("tm_menu") end)
at(590, function() tap(K.A) end)                              -- Buy
at(720, function() state("list open"); shot("tm_list") end)
buy(740, "tm01")
for k = 0, 99 do at(1260 + k * 12, function() tap(K.DOWN, 4) end) end
at(2500, function() shot("tm_row100") end)
buy(2520, "tm109")
for k = 0, 10 do at(3040 + k * 12, function() tap(K.DOWN, 4) end) end
at(3200, function() shot("tm_row111") end)
buy(3220, "tm120")
at(3740, function() tap(K.DOWN, 4) end)
at(3800, function() shot("tm_cancel_row") end)
at(3810, function() tap(K.B) end)
at(3950, function() tap(K.B) end)
at(4100, function() tap(K.A) end)
at(4250, function() state("end"); shot("tm_end"); done() end)
function TEST(f)
  t0 = t0 or f
  for _, p in ipairs(plan) do if f - t0 == p[1] then p[2]() end end
end
