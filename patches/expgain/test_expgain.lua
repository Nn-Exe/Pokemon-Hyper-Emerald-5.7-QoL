-- The Option menu's "Exp. Gain" row (the hack's EXP switch, labelled "Sound  Mono / Stereo" before expgain).
-- A wild Lv 2 Magikarp as saved (On) -> Options, row 3 RIGHT (Off), B -> the battle again -> Options, row 3 LEFT
-- (On), B -> the battle again. Logs flag 0x267, the saved option bit and the EXP each battle gave every party
-- member: expect EXP, none, EXP. Screenshots expgain_off.png / expgain_on.png (and *_before). Log expgain_log.txt.
NAME = "expgain"
dofile((HERE or DIR or "./") .. "../dexnavchain/test_boot.lua")
local SCRIPT = 0x0203F100
local PARTY, COUNT = 0x020244EC, 0x020244E9
local ROW = tonumber(os.getenv("ROW") or "3")
local q, now = {}, 0
local function after(d, fn) q[#q + 1] = {now + d, fn} end
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1); emu:write8(0x03000E38, 0)
end
local function flag(n) return (emu:read8(emu:read32(0x03005D8C) + 0x1270 + (n >> 3)) >> (n & 7)) & 1 end
local function state(tag)
  w(string.format("%-22s flag 0x267 = %d, option bit = %d", tag, flag(0x267), emu:read8(emu:read32(0x03005D90) + 0x15) & 1))
end
local function exps()
  local t = {}
  for i = 0, emu:read8(COUNT) - 1 do t[#t + 1] = emu:read32(PARTY + i * 100 + 0x24) end
  return t
end
local function battle(tag, fn)
  local before = exps()
  run({0xB6, 129, 0, 2, 0, 0, 0xB7, 0x02})
  for f = 200, 2200, 30 do after(f, function() tap(K.A) end) end
  after(2300, function()
    local s = {}
    for i, v in ipairs(exps()) do s[#s + 1] = tostring(v - before[i]) end
    w(string.format("%-22s EXP gained per party slot: %s (outcome %d)", tag, table.concat(s, ", "), emu:read8(0x0202433A)))
    fn()
  end)
end
local function options(key, shotname, fn)                 -- START -> Option, down to the row, key, B
  tap(K.START)
  after(60, function()
    local n, cur, idx = emu:read8(0x0203760F), emu:read8(0x0203760E), nil
    for i = 0, n - 1 do if emu:read8(0x02037610 + i) == 6 then idx = i end end
    local downs = (idx - cur) % n
    for d = 1, downs do after(d * 14, function() tap(K.DOWN) end) end
    after(downs * 14 + 20, function() tap(K.A) end)
    local t = downs * 14 + 20 + 150
    for d = 1, ROW do after(t + d * 14, function() tap(K.DOWN) end) end
    t = t + ROW * 14 + 20
    after(t, function() shot(shotname .. "_before") end)
    after(t + 10, function() tap(key) end)
    after(t + 40, function() shot(shotname) end)
    after(t + 50, function() tap(K.B) end)
    after(t + 200, function() tap(K.B) end)
    after(t + 300, fn)
  end)
end
local function begin()
  state("at start")
  battle("battle 1 (as saved)", function()
    options(K.RIGHT, "expgain_off", function()
      state("after row 3 -> right")
      battle("battle 2", function()
        options(K.LEFT, "expgain_on", function()
          state("after row 3 -> left")
          battle("battle 3", function() done() end)
        end)
      end)
    end)
  end)
end
local started = false
function TEST(f)
  now = now + 1
  if not started then started = true; after(30, begin) end
  local i = 1
  while i <= #q do if q[i][1] <= now then local fn = q[i][2]; table.remove(q, i); fn() else i = i + 1 end end
end
