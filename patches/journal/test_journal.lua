-- Journal: every scenario in test_journal_cases.lua (made by make_tests.py) writes its story flags, uses the
-- registered Journal from the field (SELECT, then UP in the key-item popup), and logs the message the game
-- built in gStringVar4. check_journal.py
-- then compares each against expected.json byte for byte. Also checks the overworld hook handed the item out.
NAME = "journal"
dofile((DIR or "./") .. "../dexnavchain/test_boot.lua")
dofile((DIR or "./") .. "test_journal_cases.lua")

local JOURNAL = 363
local STRVAR4 = 0x02021FC4

local function sb1() return emu:read32(0x03005D8C) end
local function sb2() return emu:read32(0x03005D90) end
-- the same layout tools/romdata/savefile.py reads: vanilla flags, then the hack's four custom ranges
local function flagbyte(f)
  if f < 0x4000 then return sb1() + 0x1270 + (f >> 3) end
  local i = (f - 0x4000) >> 3
  if i <= 0x33 then return sb1() + 0x988 + i end
  if i <= 0x67 then return sb1() + 0x3B24 + i - 0x34 end
  if i <= 0x9B then return sb2() + 0x5C + i - 0x68 end
  return sb2() + 0x28 + i - 0x9C
end
local function setflag(f, on)
  local a = flagbyte(f)
  local b = emu:read8(a)
  if on then b = b | (1 << (f & 7)) else b = b & ~(1 << (f & 7)) & 0xFF end
  emu:write8(a, b)
end

local function has_journal()
  local base = emu:read32(0x02039DD8 + 4 * 8)
  local cap = emu:read8(0x02039DD8 + 4 * 8 + 4)
  for i = 0, cap - 1 do
    if emu:read16(base + i * 4) == JOURNAL then return true end
  end
  return false
end

local function message_hex()
  local t = {}
  for i = 0, 999 do
    local b = emu:read8(STRVAR4 + i)
    if b == 0xFF then break end
    t[#t + 1] = string.format("%02x", b)
  end
  return table.concat(t)
end

local saved = {}
local phase, n, t0, taps = "start", 1, 0, 0
function TEST(f)
  if phase == "start" then
    w("journal in bag: " .. tostring(has_journal()))
    -- register the Journal alone: the vanilla slot, and the keyreg patch's three extra slots emptied
    emu:write16(sb1() + 0x496, JOURNAL)
    emu:write16(sb1() + 0x9C2, 0); emu:write16(sb1() + 0x9C4, 0); emu:write16(sb1() + 0x9C6, 0)
    phase, t0 = "case", f
  elseif phase == "case" then
    if f < t0 + 20 then return end
    local c = CASES[n]
    for _, fl in ipairs(c.clear) do setflag(fl, false) end
    for _, fl in ipairs(c.set) do setflag(fl, true) end
    emu:write8(STRVAR4, 0xFF)
    tap(K.SEL)                  -- the keyreg popup (it always opens in this build); UP is the first slot
    phase, t0, taps = "pick", f, 0
  elseif phase == "pick" then
    if f == t0 + 30 then tap(K.UP); phase, t0 = "wait", f end
  elseif phase == "wait" then
    if f == t0 + 60 then
      w("CASE " .. n .. " " .. CASES[n].name .. " | " .. message_hex())
      if n == 1 or CASES[n].name == "badges 2/8" or CASES[n].name == "plates 4/17" then shot("journal_" .. n) end
      phase, t0 = "close", f
    end
  elseif phase == "close" then
    -- A through every page until the field is ours again
    if (f - t0) % 24 == 0 then
      if lock() == 0 and taps > 0 then
        n = n + 1
        if n > #CASES then w("finished"); done(); phase = "end" else phase, t0 = "case", f end
        return
      end
      tap(K.A); taps = taps + 1
      if taps > 60 then w("CASE " .. n .. " never closed"); done(); phase = "end" end
    end
  end
end
