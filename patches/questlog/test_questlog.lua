-- Quest Log: every scenario in ../journal/test_journal_cases.lua writes its story flags, opens the Quest Log from
-- the field (SELECT, then UP in the key-item popup), and logs the row the screen marks as current, the chapter
-- and row it opened on, and - after A on that row - the detail text it laid out. check_questlog.py compares
-- them with ../journal/expected.json: the current row must be the Journal's objective and the detail its text.
-- Needs DIR set to the folder holding game.gba/game.sav and these scripts.
NAME = "questlog"
dofile((DIR or "./") .. "../dexnavchain/test_boot.lua")
dofile((DIR or "./") .. "../journal/test_journal_cases.lua")

local JOURNAL = 363
local TASK = tonumber(TASK_FN or "0x08FEA7E9")

local function sb1() return emu:read32(0x03005D8C) end
local function sb2() return emu:read32(0x03005D90) end
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

local function state()
  for i = 0, 15 do
    local b = 0x03005E00 + i * 40
    if emu:read32(b) == TASK and emu:read8(b + 4) == 1 then return emu:read32(b + 8) + 0x800 end
  end
end

local function detail_hex(v)
  local t, p = {}, emu:read8(v + 5)
  local a = v + 0x100
  for _ = 1, p do
    repeat
      local b = emu:read8(a); a = a + 1
      t[#t + 1] = string.format("%02x", b)
    until b == 0xFF
  end
  return table.concat(t)
end

local phase, n, t0 = "start", 1, 0
function TEST(f)
  if phase == "start" then
    emu:write16(sb1() + 0x496, JOURNAL)
    emu:write16(sb1() + 0x9C2, 0); emu:write16(sb1() + 0x9C4, 0); emu:write16(sb1() + 0x9C6, 0)
    phase, t0 = "case", f
  elseif phase == "case" then
    if f < t0 + 20 then return end
    local c = CASES[n]
    for _, fl in ipairs(c.clear) do setflag(fl, false) end
    for _, fl in ipairs(c.set) do setflag(fl, true) end
    tap(K.SEL)
    phase, t0 = "pick", f
  elseif phase == "pick" then
    if f == t0 + 30 then tap(K.UP); phase, t0 = "open", f end
  elseif phase == "open" then
    -- the log opens on the chapter grid with the current chapter selected: A goes into it
    if f == t0 + 90 then tap(K.A); phase, t0 = "open2", f end
  elseif phase == "open2" then
    if f == t0 + 40 then
      local v = state()
      if not v then w("CASE " .. n .. " no screen"); done(); phase = "end"; return end
      local st = {}
      for k = 0, 84 do st[#st + 1] = string.format("%d", emu:read8(v + 0x40 + k)) end
      w(string.format("CASE %d %s | cur %d page %d sel %d | %s", n, CASES[n].name, emu:read8(v + 6),
        emu:read8(v), emu:read8(v + 2), table.concat(st, "")))
      if CASES[n].name == "badges 2/8" or CASES[n].name == "tapus 2/4" then shot("questlog_list_" .. n) end
      tap(K.A)
      phase, t0 = "detail", f
    end
  elseif phase == "detail" then
    if f == t0 + 20 then
      local v = state()
      w(string.format("DETAIL %d mode %d | %s", n, emu:read8(v + 3), detail_hex(v)))
      if n == 1 or CASES[n].name == "badges 2/8" or CASES[n].name == "tapus 2/4" then shot("questlog_" .. n) end
      tap(K.B)                  -- detail -> list
    elseif f == t0 + 40 then
      tap(K.B)                  -- list -> chapter grid
    elseif f == t0 + 60 then
      tap(K.B)                  -- grid -> closed
    elseif f > t0 + 80 and cb2() == OVERWORLD and lock() == 0 then
      n = n + 1
      if n > #CASES then w("finished"); done(); phase = "end" else phase, t0 = "case", f end
    elseif f > t0 + 600 then
      w("CASE " .. n .. " never got back to the field"); done(); phase = "end"
    end
  end
end
