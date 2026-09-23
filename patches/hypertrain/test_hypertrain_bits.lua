-- Does the stat calculation honour the hyper-training bits (mon+0x1E)? Set them the NPC's way, then run
-- CalculateMonStats on the lead through the hack's nature routine 0x08FF0E01 (VAR_8004 slot, VAR_8005 nature:
-- the lead's own override, so the nature does not change) and compare the stats.
NAME = "htstats"
dofile((DIR or "./") .. "../dexnavchain/test_boot.lua")
local SCRIPT, PARTY = 0x0203F100, 0x020244EC
local BITS = tonumber(os.getenv("BITS") or "126")
local t0, plan = nil, {}
local function at(d, fn) plan[#plan + 1] = {d, fn} end
local function ivs(mon)
  local w32 = emu:read32(mon + 0x48)
  local t = {}
  for i = 0, 5 do t[#t + 1] = (w32 >> (i * 5)) & 31 end
  return string.format("IVs HP %d Atk %d Def %d Spe %d SpA %d SpD %d", table.unpack(t))
end
local function stats(mon)
  return string.format("maxHP %d Atk %d Def %d Spe %d SpA %d SpD %d", emu:read16(mon + 0x58), emu:read16(mon + 0x5A),
    emu:read16(mon + 0x5C), emu:read16(mon + 0x5E), emu:read16(mon + 0x60), emu:read16(mon + 0x62))
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
at(0, function()
  local nat = emu:read8(PARTY + 0x1F) & 0x7F
  w(string.format("before: +0x1E %02X nature override %d | %s | %s", emu:read8(PARTY + 0x1E), nat, ivs(PARTY), stats(PARTY)))
  -- recalc only, no training: a control
  run({0x16, 0x04, 0x80, 0x00, 0x00, 0x16, 0x05, 0x80, nat, 0x00, 0x23, 0x01, 0x0E, 0xFF, 0x08, 0x6B, 0x02})
end)
at(30, function()
  local nat = emu:read8(PARTY + 0x1F) & 0x7F
  w(string.format("recalc, untrained: +0x1E %02X | %s | %s", emu:read8(PARTY + 0x1E), ivs(PARTY), stats(PARTY)))
  -- train (the NPC's callasm), then recalc
  run({0x16, 0x04, 0x80, 0x00, 0x00, 0x16, 0x05, 0x80, BITS, 0x00, 0x23, 0xFD, 0x26, 0x81, 0x09,
       0x16, 0x05, 0x80, nat, 0x00, 0x23, 0x01, 0x0E, 0xFF, 0x08, 0x6B, 0x02})
end)
at(60, function()
  w(string.format("recalc, trained:   +0x1E %02X | %s | %s", emu:read8(PARTY + 0x1E), ivs(PARTY), stats(PARTY)))
  done()
end)
function TEST(f)
  t0 = t0 or f
  for _, p in ipairs(plan) do if f - t0 == p[1] then p[2]() end end
end
