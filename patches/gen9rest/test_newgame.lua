-- A New Game from no save: A through the title and the intro (START now and then for the naming screen) until the
-- player stands on the map; then the Pokedex: every seen / caught byte of SaveBlock1 (+0x560 / +0x5D8) and the
-- 960+ area (EXT 0x0203DA00: marker, 32 seen, 32 caught); then a wild Fidough (961) through setwildbattle: its seen
-- bit must land in the 960+ area, with the marker written.
local E = os.getenv
DIR = E("GEN9_DIR")
NAME = (E("TAG") or "ng") .. "_new"
local NL = string.char(10)
LOG = io.open(DIR .. NAME .. "_log.txt", "w")
local function w(s) LOG:write(s .. NL); LOG:flush() end
local function done() local fh = io.open(DIR .. NAME .. "_done.txt", "w"); fh:write("done"); fh:close() end
local function shot(n) emu:screenshot(DIR .. n .. ".png") end
local K = {A = 0, B = 1, START = 3}
local OVERWORLD, BATTLE = 0x08085E5D, 0x08038421
local SCRIPT, EXT = 0x0203F100, 0x0203DA00
local crashed = false
for _, v in ipairs({0x00000000, 0x00000004, 0x0000000C, 0x00000010}) do
  emu:setBreakpoint(function() if not crashed then crashed = true; w(string.format("VECTOR %02X lr %08X", v, emu:readRegister("lr"))) end end, v)
end
local clears = 0
emu:setBreakpoint(function() clears = clears + 1 end, 0x080C0664 - 0x080C0664 + emu:read32(0x08084394) - 1)   -- dex_clear
local f, rel, phase, still, mark, lastcb = 0, {}, "intro", 0, 0, nil
local function tap(k, len) emu:addKey(k); rel[k] = f + (len or 6) end
local function cb2() return emu:read32(0x030022C4) end
local function lock() return emu:read8(0x03000F2C) end
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1); emu:write8(0x03000E38, 0)
end
local function dex(label)
  local sb1 = emu:read32(0x03005D8C)
  local seen, caught = 0, 0
  for i = 0, 0x77 do
    local a, b = emu:read8(sb1 + 0x560 + i), emu:read8(sb1 + 0x5D8 + i)
    for k = 0, 7 do seen = seen + ((a >> k) & 1); caught = caught + ((b >> k) & 1) end
  end
  local es, ec = 0, 0
  for i = 0, 31 do
    local a, b = emu:read8(EXT + 4 + i), emu:read8(EXT + 36 + i)
    for k = 0, 7 do es = es + ((a >> k) & 1); ec = ec + ((b >> k) & 1) end
  end
  local n = 961 - 960
  w(string.format("%s: numbers 0-959 seen %d caught %d | 960+ marker %08X seen %d caught %d | 961 seen %d", label, seen, caught,
    emu:read32(EXT), es, ec, (emu:read8(EXT + 4 + (n >> 3)) >> (n & 7)) & 1))
end
callbacks:add("frame", function()
  f = f + 1
  for k, t in pairs(rel) do if f >= t then emu:clearKey(k); rel[k] = nil end end
  if phase == "end" then return end
  if cb2() ~= lastcb then w(string.format("f%d cb2 %08X", f, cb2())); lastcb = cb2() end
  if crashed then w("CRASHED"); phase = "end"; done(); return end
  if phase == "intro" then
    if cb2() == OVERWORLD and lock() == 0 then
      still = still + 1
      if still > 240 then
        phase = "field"; mark = f; shot(NAME .. "_field")
        w(string.format("on the map at frame %d; dex_clear ran %d time(s)", f, clears))
        dex("after New Game")
      end
    else
      still = 0
      if f % 25 == 0 then tap(K.A) end
      if f % 400 == 200 then tap(K.START) end
    end
    if f % 3000 == 0 then shot(string.format("%s_%06d", NAME, f)) end
    if f > 60000 then shot(NAME .. "_stuck"); w("never reached the map"); phase = "end"; done() end
  elseif phase == "field" then
    if f == mark + 10 then run({0xB6, 1258 & 0xFF, 1258 >> 8, 5, 0, 0, 0xB7, 0x02}) end
    if f > mark + 10 and cb2() == BATTLE and phase == "field" then phase = "battle"; mark = f end
    if f > mark + 1500 and phase == "field" then w("no battle"); phase = "end"; done() end
  elseif phase == "battle" then
    if f == mark + 600 then shot(NAME .. "_battle"); dex("in the battle with Fidough (961)"); phase = "end"; done() end
  end
end)
