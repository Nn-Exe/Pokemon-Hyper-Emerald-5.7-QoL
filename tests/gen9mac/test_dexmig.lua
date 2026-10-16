-- gen9dex: the Pokedex marks of the Gen 9 numbers, as the save holds them.
--   SCEN=boot   the save as it is, read after boot (by then the game has asked for a mark: on the renumbered build
--               the marks are moved): every seen / caught number 900-1032 as the bytes hold them, and the marker.
--   SCEN=nomark the main game's kind of save: after boot the marker word cleared, the Gen 9 bits of SaveBlock1 set to
--               the OLD numbers of Koraidon (927, caught), Great Tusk (906, seen), Sprigatito (941, caught), the area
--               zeroed; then a wild Pidgey (the game asks for its mark) and the bits read again.
--   SCEN=dex9   a test build's kind: the marker "DEX9", old 1000 (gen9rest's Gholdengo... at its old number) caught
--               in the area, old 935 (Gouging Fire) seen in SaveBlock1; then the Pidgey and the read.
local E = os.getenv
local SCEN = E("SCEN") or "boot"
DIR = E("GEN9_DIR")
NAME = (E("TAG") or "dm") .. "_" .. SCEN
dofile("C:/Users/nonth/Desktop/Works & Productivity/gba-trans/hyper-emerald-en-qol/patches/dexnavchain/test_boot.lua")
local SCRIPT, EXT = 0x0203F100, 0x0203DA00
local function sb1() return emu:read32(0x03005D8C) end
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1); emu:write8(0x03000E38, 0)
end
local function bit(base, n) return (emu:read8(base + (n >> 3)) >> (n & 7)) & 1 end
local function setbit(base, n, v)
  local a = base + (n >> 3)
  local b = emu:read8(a)
  if v == 1 then b = b | (1 << (n & 7)) else b = b & ~(1 << (n & 7)) & 0xFF end
  emu:write8(a, b)
end
local function dump(tag)
  local s, c = {}, {}
  for n = 900, 959 do
    if bit(sb1() + 0x560, n) == 1 then s[#s + 1] = n end
    if bit(sb1() + 0x5D8, n) == 1 then c[#c + 1] = n end
  end
  for n = 960, 1032 do
    if bit(EXT + 4, n - 960) == 1 then s[#s + 1] = n end
    if bit(EXT + 36, n - 960) == 1 then c[#c + 1] = n end
  end
  w(string.format("%s: marker %08X", tag, emu:read32(EXT)))
  w(tag .. " seen: " .. table.concat(s, " "))
  w(tag .. " caught: " .. table.concat(c, " "))
end
local plan, t0 = {}, nil
local function at(d, fn) plan[#plan + 1] = {d, fn} end
at(5, function() dump("after boot") end)
if SCEN ~= "boot" then
  at(10, function()
    for n = 906, 959 do setbit(sb1() + 0x560, n, 0); setbit(sb1() + 0x5D8, n, 0) end
    for i = 0, 67 do emu:write8(EXT + i, 0) end
    if SCEN == "nomark" then
      setbit(sb1() + 0x560, 927, 1); setbit(sb1() + 0x5D8, 927, 1)
      setbit(sb1() + 0x560, 906, 1)
      setbit(sb1() + 0x560, 941, 1); setbit(sb1() + 0x5D8, 941, 1)
    else
      emu:write32(EXT, 0x39584544)
      setbit(EXT + 4, 1000 - 960, 1); setbit(EXT + 36, 1000 - 960, 1)
      setbit(sb1() + 0x560, 935, 1)
    end
    dump("set up")
  end)
  at(30, function() run({0xB6, 16, 0, 5, 0, 0, 0xB7, 0x02}) end)   -- a wild Pidgey: the game asks for its mark
  at(400, function() dump("after a mark was asked for"); done() end)
else
  at(20, function() done() end)
end
function TEST(f)
  t0 = t0 or f
  for _, p in ipairs(plan) do if f - t0 == p[1] then p[2]() end end
end
