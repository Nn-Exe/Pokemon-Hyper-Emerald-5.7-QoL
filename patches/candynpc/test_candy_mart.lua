-- Rare Candy NPC: warp into Petalburg's Poke Mart (8/6) at (4,6), face right at the NPC on (5,6), talk,
-- say yes, count Rare Candies (item 68) before/after, then talk again (should refuse). Logs the given flag (0x433F).
NAME = "candy"
dofile((DIR or "./") .. "../dexnavchain/test_boot.lua")
local SCRIPT = 0x0203F100
local t0, plan = nil, {}
local function at(d, fn) plan[#plan + 1] = {d, fn} end
local function candy()
  local total = 0
  for pocket = 0, 4 do
    local base = emu:read32(0x02039DD8 + pocket * 8)
    local cap = emu:read8(0x02039DD8 + pocket * 8 + 4)
    if base >= 0x02000000 and base < 0x03000000 and cap > 0 and cap < 250 then
      for i = 0, cap - 1 do
        if emu:read16(base + i * 4) == 68 then total = total + emu:read16(base + i * 4 + 2) end
      end
    end
  end
  return total
end
local GIVEN = tonumber(os.getenv("GIVEN") or "0x433F")
local function flag()                       -- the hack's custom flags (GetFlagAddr 0x09F00CEC)
  local sb1, sb2 = emu:read32(0x03005D8C), emu:read32(0x03005D90)
  local i = (GIVEN - 0x4000) >> 3
  local a
  if i <= 0x33 then a = sb1 + 0x988 + i elseif i <= 0x67 then a = sb1 + 0x3B24 + i - 0x34
  elseif i <= 0x9B then a = sb2 + 0x5C + i - 0x68 else a = sb2 + 0x28 + i - 0x9C end
  return (emu:read8(a) >> (GIVEN & 7)) & 1
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
  w(string.format("%s: map %d/%d pos (%d,%d) candy %d flag %d", tag, emu:read8(sb1 + 4), emu:read8(sb1 + 5),
    emu:read16(sb1), emu:read16(sb1 + 2), candy(), flag()))
end
at(10, function() state("start"); run({0x39, 0x08, 0x06, 0xFF, 0x04, 0x00, 0x06, 0x00, 0x02}) end)
at(260, function() state("in the Mart"); shot("c1_mart") end)
at(270, function() tap(K.RIGHT) end)
at(310, function() tap(K.A) end)
at(420, function() shot("c2_question") end)
at(440, function() tap(K.A) end)           -- the question page, then the yes/no box
at(520, function() shot("c3_yesno") end)
at(540, function() tap(K.A) end)           -- YES
at(700, function() state("after yes"); shot("c4_given") end)
for k = 0, 4 do at(720 + k * 40, function() tap(K.A) end) end
at(960, function() state("closed"); tap(K.A) end)   -- talk again
at(1080, function() shot("c5_again") end)
for k = 0, 3 do at(1100 + k * 40, function() tap(K.A) end) end
at(1300, function() state("end"); done() end)
function TEST(f)
  t0 = t0 or f
  for _, p in ipairs(plan) do if f - t0 == p[1] then p[2]() end end
end
