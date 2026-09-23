-- Hyper Training end to end: train the lead's six stats the trainer's way, run his success path (0x09812840),
-- log the stats right after, then open the EV-IV Display (SELECT popup, DOWN) and run an IV judge
-- (0x08FF0040). Screenshots t*_*.png. Run next to game.gba/game.sav.
NAME = "htfull"
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
  w(string.format("before: +0x1E %02X | %s | %s", emu:read8(PARTY + 0x1E), ivs(PARTY), stats(PARTY)))
  -- setvar 8004,0 ; setvar 8005,BITS ; callasm 0x098126FD (the trainer's own) ; goto 0x09812840 (his success path)
  run({0x16, 0x04, 0x80, 0x00, 0x00, 0x16, 0x05, 0x80, BITS, 0x00, 0x23, 0xFD, 0x26, 0x81, 0x09,
       0x05, 0x40, 0x28, 0x81, 0x09})
end)
at(90, function() shot("t1_taking") end)
at(100, function() tap(K.A) end)
at(260, function() shot("t2_complete") end)
for k = 0, 5 do at(270 + k * 40, function() tap(K.A) end) end
at(520, function()
  w(string.format("after:  +0x1E %02X | %s | %s  (field lock %d)", emu:read8(PARTY + 0x1E), ivs(PARTY), stats(PARTY), lock()))
  tap(K.SEL)
end)
at(570, function() tap(K.DOWN) end)
at(740, function() shot("t3_evivdisplay") end)
at(760, function() tap(K.R) end)
at(820, function() shot("t4_evivdisplay_r") end)
at(840, function() tap(K.B) end)
at(880, function() tap(K.B) end)
at(1000, function() run({0x05, 0x40, 0x00, 0xFF, 0x08}) end)     -- goto the IV judges' script
at(1100, function() shot("t5_judge1") end)
at(1110, function() tap(K.A) end)
at(1160, function() tap(K.A) end)
at(1260, function() shot("t6_judge2") end)
at(1270, function() tap(K.A) end)
at(1320, function() tap(K.A) end)
at(1400, function() done() end)
function TEST(f)
  t0 = t0 or f
  for _, p in ipairs(plan) do if f - t0 == p[1] then p[2]() end end
end
