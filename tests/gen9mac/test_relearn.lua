-- The Move Relearner for new Pokemon: LIST=a,b,... (givemon Lv LEVEL, default 50) one at a time as the only party
-- Pokemon; gSpecialVar_0x8004 = 0 and the relearner's screen started the way the party menu's "Moves" does
-- (patches/relearner: CB2_InitLearnMove 0x081606A1 as callback2). Shots: r<i>_list.png (the list), r<i>_down.png
-- (scrolled to its end with DOWN), then B out to the field. Logged: the Pokemon's moves and the relearner's list
-- (sMoveRelearnerStruct at 0x0203BC34: movesToLearn +0x12, numMenuChoices +0x110 with Cancel).
local E = os.getenv
DIR = E("GEN9_DIR")
NAME = (E("TAG") or "rl") .. "_rl"
dofile("C:/Users/nonth/Desktop/Works & Productivity/gba-trans/hyper-emerald-en-qol/patches/dexnavchain/test_boot.lua")
local LIST = {}
for n in (E("LIST") or ""):gmatch("%d+") do LIST[#LIST + 1] = tonumber(n) end
local LEVEL = tonumber(E("LEVEL") or "50")
local SCRIPT, PARTY = 0x0203F100, 0x020244EC
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
local t = 2
for i, sp in ipairs(LIST) do
  local ii = i
  at(t, function() emu:write8(0x020244E9, 0); for k = 0, 599 do emu:write8(PARTY + k, 0) end; give(sp, LEVEL) end)
  at(t + 40, function()
    w(string.format("r%d: species %d lv %d moves %d %d %d %d", ii, emu:read16(PARTY + 0x20), emu:read8(PARTY + 0x54),
      emu:read16(PARTY + 0x2C), emu:read16(PARTY + 0x2E), emu:read16(PARTY + 0x30), emu:read16(PARTY + 0x32)))
    emu:write8(0x03000F2C, 0); emu:write16(0x020375E0, 0); emu:write32(0x030022C4, 0x081606A1)
  end)
  at(t + 300, function()
    shot(string.format("%s_r%02d_list", NAME, ii))
    local st = emu:read32(0x0203BC34)            -- sMoveRelearnerStruct: movesToLearn at +0x12, numMenuChoices +0x110
    local n, mv = emu:read8(st + 0x110), {}
    for k = 0, n - 2 do mv[#mv + 1] = emu:read16(st + 0x12 + 2 * k) end
    w(string.format("r%d: list %d: %s", ii, n - 1, table.concat(mv, " ")))
    if E("DUMP") then
      local d = {}
      for k = 0, 0x117, 2 do d[#d + 1] = string.format("%X:%d", k, emu:read16(st + k)) end
      w(string.format("struct at %08X: %s", st, table.concat(d, " ")))
    end
  end)
  for k = 0, 24 do key(t + 310 + 8 * k, K.DOWN) end
  at(t + 560, function() shot(string.format("%s_r%02d_down", NAME, ii)) end)
  key(t + 570, K.B); key(t + 640, K.A); key(t + 700, K.A); key(t + 760, K.B)
  at(t + 1000, function() w(string.format("r%d: back cb2 %08X lock %d", ii, cb2(), lock())) end)
  t = t + 1040
end
at(t, function() done() end)
function TEST(f)
  t0 = t0 or f
  for _, p in ipairs(plan) do if f - t0 == p[1] then p[2]() end end
end
