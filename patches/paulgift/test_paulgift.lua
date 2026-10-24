-- paulgift: Paul's rematch in Fortree City played through, and what you have before and after.
-- TAG names the run (log paulgift_<tag>_log.txt, screenshots paulgift_<tag>_NNN.png in DIR); HERE is this folder.
-- Set up on a late-game save: flag 0x42B1 (his rematch done) clear, var 0x400A (the trigger's) 0, flag 0x273 set,
-- which makes the hack treat a lost trainer battle as won (NOTES, Lorelei) - with the party cut to its first Pokemon
-- at 1 HP the battle ends at once. Warp to 22,12, step up onto the trigger at 22,11, A through everything.
-- Expect on the fixed game: the battle, his speech, no "I'll give you this", no item; he flies off; 0x42AF and 0x42B1
-- set; the EV-IV Displays in the Bag and the PC the same as before. On the game before the fix (the control) the
-- Bag has one more afterwards.
local TAG = os.getenv("TAG") or "new"
NAME = "paulgift_" .. TAG
HERE = HERE or os.getenv("HERE")
DIR = DIR or os.getenv("DIR")
dofile(HERE .. "../dexnavchain/test_boot.lua")
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
local EVIV = 650
-- VAR 0x8000-0x8002: Bag has >= 1, 2, 3; 0x8003-0x8005: PC has >= 1, 2, 3; 0x8006/7: flags 0x42AF/0x42B1;
-- 0x8008: var 0x400A
local FL = {0x42AF, 0x42B1}
local function probe()
  local b = {}
  local function add(t) for _, c in ipairs(t) do b[#b + 1] = c end end
  for q = 1, 3 do
    add({0x47, EVIV & 0xFF, EVIV >> 8, q, 0, 0x19, q - 1, 0x80, 0x0D, 0x80})
    add({0x4A, EVIV & 0xFF, EVIV >> 8, q, 0, 0x19, q + 2, 0x80, 0x0D, 0x80})
  end
  for i, f in ipairs(FL) do
    local v = 0x8005 + i
    local skip = SCRIPT + #b + 19
    add({0x16, v & 0xFF, v >> 8, 0, 0, 0x2B, f & 0xFF, f >> 8,
         0x06, 0x00, skip & 0xFF, (skip >> 8) & 0xFF, (skip >> 16) & 0xFF, skip >> 24,
         0x16, v & 0xFF, v >> 8, 1, 0})
  end
  add({0x19, 0x08, 0x80, 0x0A, 0x40, 0x02})
  return b
end
local function var(n) return emu:read16(0x020375D8 + 2 * (n - 0x8000)) end
-- every address of Paul's script (0x0987D721..0x0987D7AE) the script context stands at, in order: its own
-- pointer, and the return addresses on its stack while a standard script (a message box, the item box) runs -
-- "ret 0987D77D" is his "I'll give you this" line, "ret 0987D789" the giveitem
local PAUL_LO, PAUL_HI, seen, trail = 0x0987D721, 0x0987D7AE, {}, {}
local function trace()
  local ctx = 0x03000E40
  local function note(a, how)
    local key = how .. a
    if a >= PAUL_LO and a <= PAUL_HI and not seen[key] then seen[key] = true; trail[#trail + 1] = string.format("%s%08X", how, a) end
  end
  note(emu:read32(ctx + 8), "")
  for i = 0, math.min(emu:read8(ctx), 20) - 1 do note(emu:read32(ctx + 0x0C + 4 * i), "ret ") end
end
local function count(first)
  local n = 0
  for k = 0, 2 do if var(first + k) == 1 then n = k + 1 end end
  return n == 3 and "3+" or tostring(n)
end
local function state(tag)
  local s = sb1()
  w(string.format("%-12s map %d/%d xy %d,%d | EV-IV Display: Bag %s, PC %s | 42AF=%d 42B1=%d 400A=%d | battles %d",
    tag, emu:read8(s + 4), emu:read8(s + 5), emu:read16(s), emu:read16(s + 2), count(0x8000), count(0x8003),
    var(0x8006), var(0x8007), var(0x8008), BATTLES or 0))
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
-- clearflag 0x42B1, setflag 0x273, setvar 0x400A 0
local setup = {0x2A, 0xB1, 0x42, 0x29, 0x73, 0x02, 0x16, 0x0A, 0x40, 0, 0, 0x02}
BATTLES = 0
local plan, t0, talk, ended, shots, inb = {}, nil, nil, nil, 0, false
local function at(d, fn) plan[#plan + 1] = {d, fn} end
at(10, function() run(probe()) end)
at(25, function() state("before") end)
at(35, function() run(setup) end)
at(50, function()
  for i = 100, 599 do emu:write8(PARTY + i, 0) end
  emu:write8(0x020244E9, 1)
  emu:write16(PARTY + 0x56, 1)
end)
at(60, function() run({0x39, 0, 4, 0xFF, 22, 0, 12, 0, 0x02}) end)
at(400, function() run(probe()) end)
at(415, function() state("arrived"); objs("arrived"); shot(NAME .. "_000") end)
at(420, function() emu:addKey(K.UP) end)
at(436, function() emu:clearKey(K.UP); talk = 436 end)
function TEST(f)
  t0 = t0 or f
  local d = f - t0
  for _, p in ipairs(plan) do if d == p[1] then p[2]() end end
  if not talk then return end
  if ended then
    if d == ended + 10 then run(probe()) end
    if d == ended + 25 then
      state("afterwards"); objs("afterwards"); shot(NAME .. "_999")
      w("script ran at " .. table.concat(trail, " "))
      done()
    end
    return
  end
  trace()
  local k = d - talk
  local b = cb2() == BATTLE
  if b and not inb then BATTLES = BATTLES + 1 end
  inb = b
  if k > 0 and k % 40 == 0 and shots < 400 then shots = shots + 1; shot(string.format("%s_%03d", NAME, shots)) end
  if k > 0 and k % 10 == 0 then tap(K.A, 4) end
  if k > 300 and lock() == 0 and cb2() == OVERWORLD then ended = d end
  if k > 30000 and not ended then ended = d; w("timed out") end
end
