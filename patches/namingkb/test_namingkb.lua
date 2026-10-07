-- The naming keyboard. Opens the nickname screen for the first party Pokemon (special ChangePokemonNickname,
-- 0xA1 in this ROM) and runs KEYS, one letter a key - A B, S = SELECT, T = START, U D L R = the pad, l r = the
-- shoulder buttons, '.' = wait - with a screenshot after each (namingkb_NN.png). The default types "ABbz" + a
-- female sign + "1" from the three pages (two waits after each SELECT: keys are ignored while the page turns),
-- presses both shoulder buttons (nothing may change), and confirms with START, A. Then logs the nickname's
-- bytes: expect BB BC D6 EE B6 A2 FF. The log namingkb_log.txt.
NAME = "namingkb"
dofile((HERE or DIR or "./") .. "../dexnavchain/test_boot.lua")
local KEYS = os.getenv("KEYS") or "ARAS..ADDAS..AUUArlS..TA...A.A"
local SCRIPT, PARTY = 0x0203F100, 0x020244EC
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1); emu:write8(0x03000E38, 0)
end
local function nick()
  local t = {}
  for i = 0, 10 do t[#t + 1] = string.format("%02X", emu:read8(PARTY + 8 + i)) end
  return table.concat(t, " ")
end
local map = {A = K.A, B = K.B, S = K.SEL, T = K.START, U = K.UP, D = K.DOWN, L = K.LEFT, R = K.RIGHT, l = K.L, r = K.R}
local plan, t0 = {}, nil
local function at(d, fn) plan[#plan + 1] = {d, fn} end
at(20, function() w("nickname before: " .. nick()) end)
at(30, function() run({0x16, 0x04, 0x80, 0x00, 0x00, 0x25, 0xA1, 0x00, 0x27, 0x02}) end)
at(330, function() w(string.format("naming screen: cb2 %08X", cb2())); shot("namingkb_00") end)
local t = 330
for i = 1, #KEYS do
  local c = KEYS:sub(i, i)
  t = t + (c == "S" and 70 or 30)
  local tt = t
  at(tt - 20, function() if c ~= "." then tap(map[c]) end end)
  at(tt, function() shot(string.format("namingkb_%02d", i)) end)
end
at(t + 120, function() w(string.format("after: cb2 %08X", cb2())); w("nickname after:  " .. nick()); done() end)
function TEST(f)
  t0 = t0 or f
  for _, p in ipairs(plan) do if f - t0 == p[1] then p[2]() end end
end
