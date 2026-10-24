-- (patches/goldbox/test_goldbox_status.lua: run it with gba-trans/hyper-emerald/_testrun/shinybox2/run.ps1 -Rom <rom> -Tag <name>
--  -Test <this file> -Env "KIND=double;SHINY=1"; the same with SHINY=0 gives the colours to compare with.)
-- Status icons on the healthboxes: the colour the game gives each battler's icon (palette index 12 + battler of
-- the slot its box is on). A wild battle of the kind asked for (KIND); SHINY = 1: every battler shiny the way
-- shinybox reads it. Thunder Wave, Toxic, Will-O-Wisp, Spore in turn (every battler uses the move); after each
-- turn, for every box: the battler's status, the slot the box is on and the icon's colour in palette RAM.
-- Also: is gMain.oamBuffer where goldbox takes it to be (0x030022F8)? The buffer is compared with OAM itself.
NAME = NAME or "status"
dofile(BOOT)
local MONS, TAGS, SPR = 0x02024084, 0x03000CF0, 0x02020630
local SHINY = (os.getenv("SHINY") or "1") == "1"
local WANT = os.getenv("KIND") or "double"
local MOVES = {86, 92, 261, 147}
local function wait(n) for _ = 1, n do coroutine.yield() end end
local function run(bytes)
  local SCRIPT = 0x0203F100
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1)
  emu:write8(0x03000E38, 0)
end
local function menu(b) return emu:read32(0x03005D60 + 4 * (b or 0)) == 0x08057589 end
local function boxes()
  local t = {}
  for i = 0, 63 do
    local s = SPR + i * 0x44
    local fl = emu:read16(s + 0x3E)
    if (fl & 1) == 1 and emu:read32(s + 0x1C) == 0x08007429 then
      local bar = emu:read16(s + 0x38)
      if bar < 64 and emu:read32(SPR + bar * 0x44 + 0x1C) == 0x080728B5 then
        t[emu:read16(s + 0x3A)] = {slot = (emu:read16(s + 4) >> 12) & 15, hidden = (fl & 4) ~= 0}
      end
    end
  end
  return t
end
local function upkeep()
  for b = 0, 3 do
    local m = MONS + b * 0x58
    local p = emu:read32(m + 0x48)
    if p ~= 0 and emu:read16(m) ~= 0 then
      if SHINY and emu:read32(m + 0x54) ~= p then emu:write32(m + 0x54, p) end
      local mx = emu:read16(m + 0x2C)
      if mx > 0 and emu:read16(m + 0x28) ~= mx then emu:write16(m + 0x28, mx) end
    end
  end
end
local move = 0
local function settle(clear)
  for b = 0, 3 do
    local m = MONS + b * 0x58
    if emu:read16(m) ~= 0 then
      for k = 0, 3 do emu:write16(m + 0x0C + 2 * k, move); emu:write8(m + 0x24 + k, 20) end
      if clear then emu:write32(m + 0x4C, 0); emu:write32(m + 0x50, 0) end
    end
  end
end
local same, differ = 0, 0
local function oamcheck()
  local eq = true
  for k = 0, 127 do
    if emu:read32(0x030022F8 + 8 * k) ~= emu:read32(0x07000000 + 8 * k) or emu:read16(0x030022F8 + 8 * k + 4) ~= emu:read16(0x07000000 + 8 * k + 4) then eq = false; break end
  end
  if eq then same = same + 1 else differ = differ + 1 end
end
local STAT = {[0] = "none"}
local function statname(v)
  if v == 0 then return "none" end
  if v & 7 ~= 0 then return "SLP" end
  if v & 0x08 ~= 0 then return "PSN" end
  if v & 0x10 ~= 0 then return "BRN" end
  if v & 0x20 ~= 0 then return "FRZ" end
  if v & 0x40 ~= 0 then return "PAR" end
  if v & 0x80 ~= 0 then return "TOX" end
  return string.format("%X", v)
end
local co = coroutine.create(function()
  run({0x39, 0, 17, 0xFF, 9, 0, 6, 0, 0x02}); wait(390)
  tap(K.UP, 24); wait(90)
  for i = 1, 900 do if lock() == 0 then break end; if i % 30 == 0 then tap(K.B) end; coroutine.yield() end
  local got = false
  for try = 1, 60 do
    local n = 0
    while cb2() ~= BATTLE do
      n = n + 1
      if lock() ~= 0 then if n % 30 == 0 then tap(K.B) end
      else local p = n % 64; if p == 1 then tap(K.LEFT, 28) elseif p == 33 then tap(K.RIGHT, 28) end end
      if n > 60000 then w("no battle"); done(); return end
      coroutine.yield()
    end
    for i = 1, 3000 do if menu() then break end; if i % 30 == 0 then tap(K.A) end; upkeep(); coroutine.yield() end
    wait(30)
    local kind = emu:read16(MONS + 2 * 0x58) ~= 0 and "double" or "single"
    if kind == WANT then got = true; break end
    for i = 1, 900 do
      if cb2() ~= BATTLE then break end
      local q = i % 90
      if menu() or menu(2) then if q == 1 then tap(K.DOWN) elseif q == 20 then tap(K.RIGHT) elseif q == 40 then tap(K.A) end
      elseif q % 30 == 0 then tap(K.A) end
      coroutine.yield()
    end
    for i = 1, 900 do if cb2() == OVERWORLD and lock() == 0 then break end; if i % 20 == 0 then tap(K.B) end; coroutine.yield() end
  end
  if not got then w("no battle of that kind"); done(); return end
  w(string.format("a %s battle, %s", WANT, SHINY and "every battler shiny" or "nobody made shiny"))
  for _, mv in ipairs(MOVES) do
    move = mv
    settle(true)
    local n, left = 0, false
    while n < 5000 do
      n = n + 1
      upkeep()
      if menu(0) then if left and n > 60 then break end elseif not menu(2) then left = true end
      if n % 10 == 0 then tap(K.A) end
      if n % 30 == 15 then settle(false) end
      oamcheck()
      coroutine.yield()
    end
    wait(20)
    shot(string.format("%s_after_%d", NAME, mv))
    local bx = boxes()
    for b = 0, 3 do
      if bx[b] and not bx[b].hidden then
        local st = emu:read32(MONS + b * 0x58 + 0x4C)
        w(string.format("after move %3d: battler %d %-4s box on slot %2d, icon colour %04X", mv, b, statname(st), bx[b].slot,
          emu:read16(0x05000200 + bx[b].slot * 32 + (12 + b) * 2)))
      end
    end
  end
  w(string.format("the OAM buffer at 030022F8 was the same as OAM on %d frames, different on %d", same, differ))
  w("STATUS DONE")
  done()
end)
function TEST(f)
  if coroutine.status(co) == "dead" then return end
  local ok, err = coroutine.resume(co)
  if not ok then w("error: " .. tostring(err)); done() end
end
