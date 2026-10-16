-- Why does a new species not evolve? The evolve pass of test_gen9rest.lua with a trace of the hack's
-- GetEvolutionTargetSpecies (0x09F0534C): its arguments and what it returns (a breakpoint on the return address).
local E = os.getenv
DIR = E("GEN9_DIR")
local TAG = E("TAG") or "et"
NAME = TAG .. "_trace"
dofile("C:/Users/nonth/Desktop/Works & Productivity/gba-trans/hyper-emerald-en-qol/patches/dexnavchain/test_boot.lua")
local SPECIES, LEVEL, TARGET = tonumber(E("SPECIES")), tonumber(E("LEVEL")), tonumber(E("TARGET"))
local SCRIPT, MONS, PARTY = 0x0203F100, 0x02024084, 0x020244EC
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1); emu:write8(0x03000E38, 0)
end
local calls, rets = 0, {}
emu:setBreakpoint(function()
  calls = calls + 1
  local lr = emu:readRegister("lr") & ~1
  local mon = emu:readRegister("r0")
  if calls <= 20 then
    w(string.format("GetEvolutionTargetSpecies(mon %08X species %d, mode %d, item %d) from %08X", mon,
      emu:read16(mon + 0x20), emu:readRegister("r1"), emu:readRegister("r2"), lr))
  end
  if not rets[lr] then
    rets[lr] = true
    emu:setBreakpoint(function() w(string.format("   returned %d (at %08X)", emu:readRegister("r0") & 0xFFFF, lr)) end, lr)
  end
end, 0x09F0534C)
local t0, phase, mark = nil, "start", 0
function TEST(f)
  t0 = t0 or f
  local d = f - t0
  if phase == "end" then return end
  if d == 3 and E("ADD") then                       -- the game's clock: the save's time offset (SaveBlock2 +0x9A, hours)
    local cur, sb2 = emu:read8(0x03005CFA), emu:read32(0x03005D90)
    local add = tonumber(E("ADD") or "0")
    local h = emu:read8(sb2 + 0x9A); if h > 127 then h = h - 256 end
    h = h + add; if h > 23 then h = h - 24; emu:write16(sb2 + 0x98, emu:read16(sb2 + 0x98) + 1) end
    emu:write8(sb2 + 0x9A, h & 0xFF)
    w(string.format("clock: hour was %d, offset hours now %d", cur, h))
  end
  if d == 50 and E("ADD") then w("clock: hour now " .. emu:read8(0x03005CFA)) end
  if d == 5 then
    emu:write8(0x020244E9, 5)
    for i = 0, 99 do emu:write8(PARTY + 500 + i, 0) end
    run({0x79, SPECIES & 0xFF, SPECIES >> 8, LEVEL, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0x02})
  end
  if d == 60 then
    for i = 0, 99 do emu:write8(PARTY + i, emu:read8(PARTY + 500 + i)) end
    local nxt = LEVEL + 1
    local growth = emu:read8(emu:read32(0x080001BC) + 28 * SPECIES + 19)
    local n3 = nxt * nxt * nxt
    local er = nxt <= 50 and (n3 * (100 - nxt)) // 50 or nxt <= 68 and (n3 * (150 - nxt)) // 100 or nxt <= 98 and (n3 * ((1911 - 10 * nxt) // 3)) // 500 or (n3 * (160 - nxt)) // 100
    local need = ({[0] = n3, [1] = er, [3] = (6 * n3) // 5 - 15 * nxt * nxt + 100 * nxt - 140, [4] = (4 * n3) // 5,
                   [5] = (5 * n3) // 4})[growth] or n3
    emu:write32(PARTY + 0x24, need - 1)                  -- one point short of the next level, by its own group
    w("growth group " .. growth)
    emu:write16(PARTY + 0x2C, 33); emu:write8(PARTY + 0x34, 35)
    if E("HELD") then emu:write16(PARTY + 0x22, tonumber(E("HELD"))) end          -- HELD=item: the lead holds it
    if E("KNOWS") then emu:write16(PARTY + 0x2E, tonumber(E("KNOWS"))); emu:write8(PARTY + 0x35, 5) end  -- KNOWS=move: its second move
    w(string.format("lead species %d lv %d exp %d item %d moves %d %d", emu:read16(PARTY + 0x20), emu:read8(PARTY + 0x54), emu:read32(PARTY + 0x24), emu:read16(PARTY + 0x22), emu:read16(PARTY + 0x2C), emu:read16(PARTY + 0x2E)))
    run({0xB6, 129, 0, 14, 0, 0, 0xB7, 0x02})
  end
  if phase == "start" and d > 70 and cb2() == BATTLE then phase = "intro"; mark = d end
  if phase == "intro" and emu:read32(0x03005D60) == 0x08057589 and d > mark + 200 then
    emu:write16(MONS + 0x58 + 0x28, 1); phase = "fighting"; mark = d
  elseif phase == "intro" and d % 30 == 0 then tap(K.A) end
  if phase == "fighting" then
    if d % 20 == 0 then tap(K.A) end
    if d > mark + 300 and cb2() == OVERWORLD and lock() == 0 then
      w("clock: the game's hour after the battle " .. emu:read8(0x03005CFA))
      w(string.format("after: species %d lv %d item %d (target %d) %s", emu:read16(PARTY + 0x20), emu:read8(PARTY + 0x54), emu:read16(PARTY + 0x22), TARGET, emu:read16(PARTY + 0x20) == TARGET and "EVOLVED" or "NOT evolved"))
      phase = "end"; done()
    end
    if d > mark + 9000 then w("stuck"); phase = "end"; done() end
  end
end
