-- Sinnoh League attendant texts: run tiny scripts from EWRAM that show the heal line, then the door menu
-- (multichoice 20, 4, 126, ignoreB) with the cursor on each door, then Lucian's line. Screenshots lt_*.png and
-- the menu's answer. Run next to game.gba/game.sav with DIR set.
NAME = "leaguetext"
DIR = DIR or "./"
dofile(DIR .. "../dexnavchain/test_boot.lua")
local SCRIPT = 0x0203F100            -- EWRAM measured free (hyper-emerald-patch skill)
local function le32(v) return {v & 0xFF, (v >> 8) & 0xFF, (v >> 16) & 0xFF, v >> 24} end
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1)
  emu:write8(0x03000E38, 0)
end
local function msg(ptr) local s = {0x67}; for _, b in ipairs(le32(ptr)) do s[#s + 1] = b end
  s[#s + 1] = 0x66; s[#s + 1] = 0x02; return s end
local heal = 0                       -- the message's pointer is unaligned: read32 would round the address down
for i = 3, 0, -1 do heal = (heal << 8) | emu:read8(0x0987549E + i) end
local plan, t0 = {}, nil
local function at(d, fn) plan[#plan + 1] = {d, fn} end
at(30, function() w(string.format("heal text at %08X", heal)); run(msg(heal)) end)
at(200, function() shot("lt_heal") end)
at(210, function() run({0x68, 0x6F, 0x14, 0x04, 0x7E, 0x01, 0x02}) end)
at(280, function() shot("lt_doors_0") end)
at(290, function() tap(K.DOWN) end) at(320, function() shot("lt_doors_1") end)
at(330, function() tap(K.DOWN) end) at(360, function() shot("lt_doors_2") end)
at(370, function() tap(K.DOWN) end) at(400, function() shot("lt_doors_3") end)
at(410, function() tap(K.A) end)
at(460, function() w(string.format("menu answer %d (3 = Far right)", emu:read16(0x020375F0))) end)
at(470, function() run({0x68, 0x67, 0xF9, 0x1C, 0xB4, 0x08, 0x66, 0x02}) end)    -- message 0x08B41CF9
at(640, function() shot("lt_lucian"); done() end)
function TEST(f)
  t0 = t0 or f
  for _, p in ipairs(plan) do if f - t0 == p[1] then p[2]() end end
end
