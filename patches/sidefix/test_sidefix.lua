-- sidefix: walk up to Blue / the demon soul, press A and play it through with A (yes to every question, the first
-- move in battle). SCEN picks the case; the log is sidefix_<scen>_log.txt, screenshots sidefix_<scen>_NN.png.
--   blue        Lilycove Museum 1F: stand at 3,3, face up, A.
--               Expect: a battle with Blue, then 0x40B9 set and species 1081-1085 in slots 1-5.
--   soul_dawn   Steven's Island 35/8 top room, Dawn already beaten (0x4118 set), 0x4552 clear: stand at 7,8, face up,
--               A. Expect: the fee, a battle, a Magikarp (species 129) in slot 1, 0x4552 set, 0x4118 still set.
--   soul_done   the same with 0x4552 set: his last line only, no battle, no Magikarp.
-- On the game before the fix, blue does nothing and soul_dawn gives no Magikarp (the controls).
-- The battles are not played: the party is cut to its first Pokemon at 1 HP and flag 0x273 is set, which makes the
-- hack treat a lost trainer battle as won (NOTES, Lorelei) - so the script goes on past the battle at once.
local SCEN = os.getenv("SCEN") or "blue"
NAME = "sidefix_" .. SCEN
dofile((HERE or DIR or "./") .. "../dexnavchain/test_boot.lua")
local SCRIPT, PARTY = 0x0203F100, 0x020244EC
local function sb1() return emu:read32(0x03005D8C) end
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1); emu:write8(0x03000E38, 0)
end
-- The hack's flags from 0x4000 up are not in SaveBlock1's array: set and read them with script commands.
local FL = {0x40B9, 0x4552, 0x4118}
local function probe()                          -- VAR 0x8000 + i - 1 = flag FL[i]
  local b = {}
  for i, f in ipairs(FL) do
    local v = 0x8000 + i - 1
    local skip = SCRIPT + #b + 19
    for _, c in ipairs({0x16, v & 0xFF, v >> 8, 0, 0, 0x2B, f & 0xFF, f >> 8,
                        0x06, 0x00, skip & 0xFF, (skip >> 8) & 0xFF, (skip >> 16) & 0xFF, skip >> 24,
                        0x16, v & 0xFF, v >> 8, 1, 0}) do b[#b + 1] = c end
  end
  b[#b + 1] = 0x02
  return b
end
local function party()
  local t = {}
  for i = 0, 5 do local s = emu:read16(PARTY + 100 * i + 0x20); if s ~= 0 then t[#t + 1] = s end end
  return table.concat(t, ",")
end
local function state(tag)
  local s, t = sb1(), {}
  for i, f in ipairs(FL) do t[#t + 1] = string.format("%04X=%d", f, emu:read16(0x020375D8 + 2 * (i - 1))) end
  w(string.format("%-12s map %d/%d xy %d,%d  %s | party %s | battles %d", tag, emu:read8(s + 4), emu:read8(s + 5),
    emu:read16(s), emu:read16(s + 2), table.concat(t, " "), party(), BATTLES or 0))
end
local function objs(tag)
  local t = {}
  for k = 0, 15 do
    local o = 0x02037350 + k * 0x24
    if emu:read8(o) & 1 == 1 then
      t[#t + 1] = string.format("%d:g%d@%d,%d%s", emu:read8(o + 8), emu:read8(o + 5), emu:read16(o + 0x10) - 7,
        emu:read16(o + 0x12) - 7, (emu:read8(o + 1) & 0x20 ~= 0) and "i" or "")
    end
  end
  w(string.format("%-12s objects %s", tag, table.concat(t, " ")))
end
local CASES = {     -- setup flags {flag, on}, warp {group, num, x, y}
  blue      = {{{0x40B9, false}, {0x273, true}}, {13, 2, 3, 3}},
  soul_dawn = {{{0x4118, true}, {0x4552, false}, {0x273, true}}, {35, 8, 7, 8}},
  soul_done = {{{0x4118, true}, {0x4552, true}, {0x273, true}}, {35, 8, 7, 8}},
}
local c = CASES[SCEN]
local setup = {}
for _, fv in ipairs(c[1]) do
  for _, b in ipairs({fv[2] and 0x29 or 0x2A, fv[1] & 0xFF, fv[1] >> 8}) do setup[#setup + 1] = b end
end
setup[#setup + 1] = 0x02
BATTLES = 0
local plan, t0, talk, ended, shots, inb = {}, nil, nil, nil, 0, false
local function at(d, fn) plan[#plan + 1] = {d, fn} end
at(10, function() run(setup) end)
at(25, function()
  for i = 100, 599 do emu:write8(PARTY + i, 0) end
  emu:write8(0x020244E9, 1)
  emu:write16(PARTY + 0x56, 1)
  run(probe())
end)
at(40, function() state("set up") end)
at(50, function() local m = c[2]; run({0x39, m[1], m[2], 0xFF, m[3], 0, m[4], 0, 0x02}) end)
at(400, function() objs("arrived"); shot(NAME .. "_00") end)
at(410, function() emu:addKey(K.UP) end)
at(414, function() emu:clearKey(K.UP) end)
at(460, function() tap(K.A); talk = 460 end)
function TEST(f)
  t0 = t0 or f
  local d = f - t0
  for _, p in ipairs(plan) do if d == p[1] then p[2]() end end
  if not talk then return end
  if ended then
    if d == ended + 10 then run(probe()) end
    if d == ended + 25 then state("afterwards"); shot(NAME .. "_99"); done() end
    return
  end
  local k = d - talk
  local b = cb2() == BATTLE
  if b and not inb then BATTLES = BATTLES + 1 end
  inb = b
  if k > 0 and k % 150 == 0 and shots < 40 then shots = shots + 1; shot(string.format("%s_%02d", NAME, shots)) end
  if k > 0 and k % 10 == 0 then tap(K.A, 4) end
  if k > 300 and lock() == 0 and cb2() == OVERWORLD then ended = d end
  if k > 30000 and not ended then ended = d; w("timed out") end
end
