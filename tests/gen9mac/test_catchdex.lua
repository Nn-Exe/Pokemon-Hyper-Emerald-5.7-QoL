-- gen9dex: a Gen 9 Pokemon caught marks its NEW number, and the new-entry page after the catch shows it.
--   SPECIES (slot), NEW (its number now), OLD (its number before gen9dex). Both numbers' seen / caught bits are
--   cleared first (the new scheme: below 960 SaveBlock1, from 960 gen9rest's area under the marker "DEXA"), then a
--   wild one at 1 HP, asleep; R at the action menu throws a ball (again if it breaks free); B now and then for the
--   nickname question and the messages, slowly, so the new-entry page is on screen for a while. A shot every 30
--   frames from the first throw (c_NNN.png); once back on the field both numbers' bits are logged.
local E = os.getenv
DIR = E("GEN9_DIR")
NAME = (E("TAG") or "cd") .. "_catch"
dofile("C:/Users/nonth/Desktop/Works & Productivity/gba-trans/hyper-emerald/hyper-emerald-en-qol/patches/dexnavchain/test_boot.lua")
local SPECIES, NEW, OLD = tonumber(E("SPECIES")), tonumber(E("NEW")), tonumber(E("OLD"))
local SCRIPT, MONS, ACTION, EXT = 0x0203F100, 0x02024084, 0x08057589, 0x0203DA00
local function sb1() return emu:read32(0x03005D8C) end
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1); emu:write8(0x03000E38, 0)
end
local function addr(n, caught)                   -- the byte and bit of a number, in the new scheme
  if n >= 960 then return EXT + 4 + (caught and 32 or 0) + ((n - 960) >> 3), n - 960 end
  return sb1() + (caught and 0x5D8 or 0x560) + (n >> 3), n
end
local function get(n, caught) local a, b = addr(n, caught); return (emu:read8(a) >> (b & 7)) & 1 end
local function clear(n)
  for _, c in ipairs({false, true}) do
    local a, b = addr(n, c); emu:write8(a, emu:read8(a) & ~(1 << (b & 7)) & 0xFF)
  end
end
local function bits(tag)
  w(string.format("%s: marker %08X | new %d seen %d caught %d | old %d seen %d caught %d", tag, emu:read32(EXT),
    NEW, get(NEW, false), get(NEW, true), OLD, get(OLD, false), get(OLD, true)))
end
local t0, phase, mark, throws, nextThrow, k = nil, "start", 0, 0, 0, 0
local function finish(msg) w(msg); phase = "end"; done() end
function TEST(f)
  t0 = t0 or f
  local d = f - t0
  if phase == "end" then return end
  if d == 5 then
    bits("before")
    if emu:read32(EXT) ~= 0x41584544 then finish("the marker is not DEXA: boot did not move the marks (FAIL)"); return end
    clear(NEW); clear(OLD); bits("cleared")
    run({0xB6, SPECIES & 0xFF, SPECIES >> 8, 30, 0, 0, 0xB7, 0x02})
  end
  if phase == "start" and d > 10 and cb2() == BATTLE then phase = "intro"; mark = d end
  if phase == "start" and d > 1500 then finish("the battle never started (FAIL)") end
  if phase == "intro" then
    if emu:read32(0x03005D60) == ACTION and d > mark + 200 then phase = "throw"; mark = d
    elseif d % 30 == 0 then tap(K.A) end
  elseif phase == "throw" then
    if emu:read32(0x03005D60) == ACTION and d >= nextThrow then
      emu:write16(MONS + 0x58 + 0x28, 1); emu:write32(MONS + 0x58 + 0x4C, 7)
      tap(K.R, 4); throws = throws + 1; nextThrow = d + 90
    elseif d > mark + 60 and d % 150 == 0 then tap(K.B) end
    if throws > 0 and d % 30 == 0 then k = k + 1; shot(string.format("%s_c%03d", NAME, k)) end
    if d > mark + 200 and cb2() == OVERWORLD and lock() == 0 then
      w(string.format("balls thrown %d | outcome %d", throws, emu:read8(0x0202433A)))
      bits("after")
      finish("catch over")
    end
    if d > mark + 20000 then shot(NAME .. "_stuck"); finish("the catch never finished (FAIL)") end
  end
end
