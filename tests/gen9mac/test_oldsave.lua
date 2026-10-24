-- A save from another version, loaded with Continue (test_boot.lua), on this build.
--   MODE=save: START -> Save (DOWN x SAVEROW, default 5) -> A through "save?" / "overwrite?": the .sav is written
--              (shots save_NN.png every 40 frames). Used to turn an older save into one of the build it runs on.
--   MODE=dump: what the save holds, as read after Continue, one line each so that two builds' dumps can be compared:
--              the party (each Pokemon's 100 bytes: species, level, a checksum), the 14 boxes (species, checksum),
--              the Bag pockets (bagslots' 200 Items at 0x0203DAE0; Key, Balls, TMs, Berries from 0x0203D1C0), money,
--              the player (name, id, map, position), flags and vars (checksums), the Pokedex (seen / caught counts of
--              0-959, the bits 906-959, gen9rest's area: marker, counts), the rest of the save stream (checksum,
--              gen9rest's area left out). Then a shot of the field, and the START menu.
local E = os.getenv
DIR = E("GEN9_DIR")
local MODE = E("MODE") or "dump"
NAME = (E("TAG") or "os") .. "_" .. MODE
dofile("C:/Users/nonth/Desktop/Works & Productivity/gba-trans/hyper-emerald/hyper-emerald-en-qol/patches/dexnavchain/test_boot.lua")
local PARTY, EXT = 0x020244EC, 0x0203DA00
local function sb1() return emu:read32(0x03005D8C) end
local function sb2() return emu:read32(0x03005D90) end
local function sum(a, n, skip)                   -- a checksum of n bytes (skip: a function saying which to leave out)
  local s1, s2 = 1, 0
  for i = 0, n - 1 do
    if not (skip and skip(a + i)) then s1 = (s1 + emu:read8(a + i)) % 65521; s2 = (s2 + s1) % 65521 end
  end
  return string.format("%08X", s2 * 65536 + s1)
end
local function bits(a, lo, hi) local c = 0; for n = lo, hi do c = c + ((emu:read8(a + (n >> 3)) >> (n & 7)) & 1) end; return c end
local function dump()
  local cnt = emu:read8(0x020244E9)
  w("party count " .. cnt)
  for i = 0, 5 do
    local m = PARTY + 100 * i
    w(string.format("party %d: species %d lv %d moves %d %d %d %d item %d sum %s", i + 1, emu:read16(m + 0x20), emu:read8(m + 0x54),
      emu:read16(m + 0x2C), emu:read16(m + 0x2E), emu:read16(m + 0x30), emu:read16(m + 0x32), emu:read16(m + 0x22), sum(m, 100)))
  end
  local st = emu:read32(0x03005D94)
  for b = 0, 13 do
    local sp = {}
    for s = 0, 29 do local v = emu:read16(st + 4 + (b * 30 + s) * 80 + 0x20); if v ~= 0 then sp[#sp + 1] = v end end
    w(string.format("box %2d: %2d Pokemon, sum %s: %s", b + 1, #sp, sum(st + 4 + b * 30 * 80, 30 * 80), table.concat(sp, " ")))
  end
  w("bag Items (200): " .. sum(0x0203DAE0, 800) .. " | Key " .. sum(0x0203D1C0, 200) .. " | Balls " .. sum(0x0203D288, 128) ..
    " | TMs " .. sum(0x0203D308, 520) .. " | Berries " .. sum(0x0203D510, 200))
  local key = emu:read32(sb2() + 0xAC)
  w(string.format("money %d | player id %08X | map %d.%d at %d,%d | play time %d:%02d", emu:read32(sb1() + 0x490) ~ key,
    emu:read32(sb2() + 0x0A), emu:read8(sb1() + 4), emu:read8(sb1() + 5), emu:read16(sb1()), emu:read16(sb1() + 2),
    emu:read16(sb2() + 0x0E), emu:read8(sb2() + 0x10)))
  w("flags " .. sum(sb1() + 0x1270, 0x12C) .. " | vars " .. sum(sb1() + 0x139C, 0x200))
  local s9, c9 = {}, {}
  for n = 906, 959 do
    if (emu:read8(sb1() + 0x560 + (n >> 3)) >> (n & 7)) & 1 == 1 then s9[#s9 + 1] = n end
    if (emu:read8(sb1() + 0x5D8 + (n >> 3)) >> (n & 7)) & 1 == 1 then c9[#c9 + 1] = n end
  end
  w(string.format("pokedex 1-905: seen %d caught %d | 906-959 seen [%s] caught [%s]", bits(sb1() + 0x560, 1, 905),
    bits(sb1() + 0x5D8, 1, 905), table.concat(s9, " "), table.concat(c9, " ")))
  w(string.format("pokedex 960+ area: marker %08X seen %d caught %d", emu:read32(EXT), bits(EXT + 4, 0, 255), bits(EXT + 36, 0, 255)))
  w("save stream (gen9rest's area left out): " .. sum(0x0203CF64, 0x0203DE00 - 0x0203CF64, function(a) return a >= EXT and a < EXT + 68 end))
end
local t0
function TEST(f)
  t0 = t0 or f
  local d = f - t0
  if MODE == "dump" then
    if d == 30 then dump(); shot(NAME .. "_field") end
    if d == 40 then tap(K.START) end
    if d == 140 then shot(NAME .. "_start"); tap(K.B) end
    if d == 240 then dump(); w(string.format("after: cb2 %08X lock %d", cb2(), lock())); done() end
  else
    local ROW = tonumber(E("SAVEROW") or "5")
    if d == 40 then tap(K.START) end
    for k = 0, ROW - 1 do if d == 100 + k * 16 then tap(K.DOWN) end end
    if d == 200 then shot(NAME .. "_menu"); tap(K.A) end
    if d >= 260 and d < 1400 and d % 40 == 0 then tap(K.A) end
    if d >= 200 and d % 40 == 20 and d < 1800 then shot(string.format("%s_%03d", NAME, (d - 200) // 40)) end
    if d == 2000 then w(string.format("after: cb2 %08X lock %d", cb2(), lock())); done() end
  end
end
