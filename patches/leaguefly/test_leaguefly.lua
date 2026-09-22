-- Sinnoh Map fly to the Sinnoh League: set 0x42EA (and 0x42EB unless DOOR_FLAG = false), open the map from
-- the Bag, hop the cursor from Route 210 to the League (RRRURRU, from the map's snap rule), press A and log
-- where we land: (14,6) at the League door with 0x42EB, (10,35) at the Pokemon Center without.
NAME = NAME or "lf"
DIR = DIR or "./"
dofile(DIR .. "../dexnavchain/test_boot.lua")
local DOOR = DOOR_FLAG ~= false
local function sb1() return emu:read32(0x03005D8C) end
local function setflag(fl, on)
  local i = (fl - 0x4000) >> 3
  local a = sb1() + 0x3B24 + i - 0x34
  local b = emu:read8(a)
  if on then b = b | (1 << (fl & 7)) else b = b & ~(1 << (fl & 7)) & 0xFF end
  emu:write8(a, b)
end
local function where()
  return string.format("map %d/%d pos (%d,%d)", emu:read8(sb1() + 4), emu:read8(sb1() + 5), emu:read16(sb1()), emu:read16(sb1() + 2))
end
local function boxtext()
  local s, a = "", 0x02021CC4
  for i = 0, 24 do
    local c = emu:read8(a + i)
    if c == 0xFF then break end
    if c >= 0xBB and c <= 0xD4 then s = s .. string.char(65 + c - 0xBB)
    elseif c >= 0xD5 and c <= 0xEE then s = s .. string.char(97 + c - 0xD5)
    elseif c >= 0xA1 and c <= 0xAA then s = s .. string.char(48 + c - 0xA1)
    elseif c == 0 then s = s .. " " else s = s .. "." end
  end
  return s
end
local t0, phase, pt, hops, lastname, stuck, dir = nil, "setup", 0, 0, "", 0, 4
function TEST(f)
  t0 = t0 or f
  local r = f - t0
  if phase == "setup" then
    setflag(0x42EA, true); setflag(0x42EB, DOOR)
    local base = emu:read32(0x02039DD8 + 4 * 8)
    local cap = emu:read8(0x02039DD8 + 4 * 8 + 4)
    for i = 0, cap - 1 do
      if emu:read16(base + i * 4) == 361 then
        local a, b = emu:read16(base), emu:read16(base + 2)
        emu:write16(base + i * 4, a); emu:write16(base + i * 4 + 2, b)
        emu:write16(base, 361); emu:write16(base + 2, 1)
      end
    end
    w("start " .. where() .. " door flag " .. tostring(DOOR))
    phase, pt = "open", r
  elseif phase == "open" then
    local d = r - pt
    if d == 20 then tap(K.START) elseif d == 80 or d == 100 then tap(K.DOWN)
    elseif d == 150 then tap(K.A) elseif d == 300 then tap(K.LEFT) elseif d == 380 then tap(K.A)
    elseif d == 440 then tap(K.A) elseif d == 560 then w("map open: " .. boxtext()); phase, pt = "hop", r end
  elseif phase == "hop" then
    local d = r - pt
    if d == 0 then
      local n = boxtext()
      if n:find("League") then w("on " .. n); shot("lf_pick"); tap(K.A); phase, pt = "fly", r; return end
      hops = hops + 1
      local seq = "RRRURRU"
      local c = seq:sub(hops, hops)
      dir = (c == "U") and 6 or 4
      if hops > #seq then w("never found the League"); done(); phase = "end"; return end
      w("hop " .. hops .. " at " .. n); tap(dir)
    elseif d == 26 then pt = r + 1
    end
  elseif phase == "fly" then
    local d = r - pt
    if d % 120 == 0 and d > 0 then w(string.format("+%d %s cb2 %08X", d, where(), cb2())) end
    if d == 900 then shot("lf_after"); done(); phase = "end" end
  end
end
