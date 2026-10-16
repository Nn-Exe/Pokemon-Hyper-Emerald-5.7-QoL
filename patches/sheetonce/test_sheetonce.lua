-- Who loads the 32-tile sheets tagged 0x2345 / 0x2346 / 0x2347 (and 0x1234) in a battle, and who frees them?
-- A wild battle of the kind asked for (KIND), TURNS turns of Tackle (A pressed through everything). Every call of
-- LoadSpriteSheet (0x080084F8: r0 = {data, u16 size, u16 tag}) and FreeSpriteTilesByTag (0x08008568: r0 = tag)
-- with one of those tags is logged with its caller, and at the end of each turn the free sprite tiles and how
-- many ranges each of the tags holds (sSpriteTileRangeTags 0x030009F0, sSpriteTileAllocBitmap 0x02021B3C).
NAME = NAME or "leak"
dofile(BOOT)
local MONS = 0x02024084
local WANT = os.getenv("KIND") or "double"
local TURNS = tonumber(os.getenv("TURNS") or "8")
local MODE = os.getenv("MODE") or "fight"             -- "fight": a move each turn; "menu": the move menu opened and shut
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
local OURS = {[0x1234] = true, [0x2345] = true, [0x2346] = true, [0x2347] = true}
local frame, logged = 0, 0
emu:setBreakpoint(function()
  if cb2() ~= BATTLE then emu:writeRegister("r0", WANT == "double" and 0 or 99) end
end, 0x09D4B2BA)
emu:setBreakpoint(function()
  local st = emu:readRegister("r0")
  local tag = emu:read16(st + 6)
  if OURS[tag] and cb2() == BATTLE then
    logged = logged + 1
    if logged <= 60 then
      local sp = emu:readRegister("sp")
      w(string.format("   f%d LOAD %04X (data %08X, %d tiles) from lr %08X | stack %08X %08X %08X %08X %08X %08X | funcs %08X %08X", frame, tag,
        emu:read32(st), emu:read16(st + 4) // 32, emu:readRegister("lr"), emu:read32(sp), emu:read32(sp + 4), emu:read32(sp + 8),
        emu:read32(sp + 12), emu:read32(sp + 16), emu:read32(sp + 20), emu:read32(0x03005D60), emu:read32(0x03005D68)))
    end
  end
end, 0x080084F8)
emu:setBreakpoint(function()
  local tag = emu:readRegister("r0") & 0xFFFF
  if OURS[tag] and cb2() == BATTLE then
    logged = logged + 1
    if logged <= 60 then w(string.format("   f%d FREE %04X from lr %08X", frame, tag, emu:readRegister("lr"))) end
  end
end, 0x08008568)
local function tiles()
  local free = 0
  for a = 0x02021B3C, 0x02021B3C + 127 do
    local v = emu:read8(a)
    for k = 0, 7 do if (v >> k) & 1 == 0 then free = free + 1 end end
  end
  local n = {}
  for i = 0, 63 do
    local tag = emu:read16(0x030009F0 + 2 * i)
    if OURS[tag] then n[tag] = (n[tag] or 0) + 1 end
  end
  return string.format("free tiles %d; ranges held: 1234 x%d, 2345 x%d, 2346 x%d, 2347 x%d", free, n[0x1234] or 0, n[0x2345] or 0, n[0x2346] or 0, n[0x2347] or 0)
end
local co = coroutine.create(function()
  run({0x39, 0, 17, 0xFF, 9, 0, 6, 0, 0x02}); wait(390)
  tap(K.UP, 24); wait(90)
  for i = 1, 900 do if lock() == 0 then break end; if i % 30 == 0 then tap(K.B) end; coroutine.yield() end
  local n = 0
  while cb2() ~= BATTLE do
    n = n + 1
    if lock() ~= 0 then if n % 30 == 0 then tap(K.B) end
    else local p = n % 64; if p == 1 then tap(K.LEFT, 28) elseif p == 33 then tap(K.RIGHT, 28) end end
    if n > 60000 then w("no battle"); done(); return end
    coroutine.yield()
  end
  for i = 1, 3000 do if menu() then break end; if i % 30 == 0 then tap(K.A) end; frame = frame + 1; coroutine.yield() end
  wait(30)
  w(string.format("a %s battle; at the first menu: %s", emu:read16(MONS + 2 * 0x58) ~= 0 and "double" or "single", tiles()))
  for turn = 1, TURNS do
    if cb2() ~= BATTLE then break end
    if MODE == "menu" then
      tap(K.A); for _ = 1, 40 do frame = frame + 1; coroutine.yield() end
      shot(string.format("%s_menu_%02d", NAME, turn))
      tap(K.B); for _ = 1, 40 do frame = frame + 1; coroutine.yield() end
      w(string.format("the move menu opened and shut %d: %s", turn, tiles()))
    else
      for b = 0, 3 do
        local m = MONS + b * 0x58
        if emu:read16(m) ~= 0 then for k = 0, 3 do emu:write16(m + 0x0C + 2 * k, 45); emu:write8(m + 0x24 + k, 20) end end
      end
      local k, left = 0, false
      while k < 4000 do
        k = k + 1; frame = frame + 1
        if cb2() ~= BATTLE then break end
        if menu(0) then if left and k > 60 then break end elseif not menu(2) then left = true end
        if k % 10 == 0 then tap(K.A) end
        coroutine.yield()
      end
      w(string.format("turn %d over: %s", turn, tiles()))
    end
  end
  w("LEAK DONE")
  done()
end)
function TEST(f)
  if coroutine.status(co) == "dead" then return end
  local ok, err = coroutine.resume(co)
  if not ok then w("error: " .. tostring(err)); done() end
end
