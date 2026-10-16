-- Messages in the mist. On Route 102 (warp to (9, 6)), for weathers 0, 1, 6, 7, 8, 9, 10, 14 (setweather / doweather),
-- a message is put up (msgbox of a text in RAM) and closed, reading the blend registers and the game's copy of them
-- (sGpuRegBuffer, what SetGpuReg last wrote):
--   - in mist (6 and 9, fog; 10 and 14, the underwater haze) the message leaves BLDCNT / BLDALPHA as the weather has them -
--     no see-through box, so the fog is not changed;
--   - in the others the hack's see-through box is still there (BLDCNT 0x1E41);
--   - after the message, in every weather, BLDCNT / BLDALPHA are the weather's own again (before: always 0x080C).
-- Then the same in Rusturf Tunnel (24/4), its own mist. Before the patch the mist checks and the after-the-message
-- checks for 0, 7, 8, 10 and 14 fail. Every map with a mist weather: test_mistmaps.lua. Screenshots <NAME>_*.png, the log <NAME>_log.txt, last line PASS.
NAME = NAME or "mistmsg"
dofile(BOOT or ((DIR or "./") .. "../dexnavchain/test_boot.lua"))
local function sb1() return emu:read32(0x03005D8C) end
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
local fails = 0
local function check(ok, msg)
  if not ok then fails = fails + 1 end
  w((ok and "   ok    " or "   FAIL  ") .. msg)
end
local function cnt() return emu:read16(0x04000050) end
local function alpha() return emu:read16(0x04000052) end
local function copycnt() return emu:read16(0x03000818 + 0x50) end
local function copyalpha() return emu:read16(0x03000818 + 0x52) end
local function clear() for i = 1, 900 do if lock() == 0 and cb2() == OVERWORLD then return end; if i % 30 == 0 then tap(K.B) end; coroutine.yield() end end
local TEXT = {0xC2, 0xD9, 0xE0, 0xE0, 0xE3, 0xAD, 0x00, 0xC2, 0xD9, 0xE0, 0xE0, 0xE3, 0xAD, 0xFF}       -- "Hello. Hello."
local MIST = {[6] = true, [9] = true, [10] = true, [14] = true}
-- a message up and gone; tag for the log, weather for what to expect
local function message(tag, weather)
  for i, b in ipairs(TEXT) do emu:write8(0x0203F120 + i - 1, b) end
  local c0, a0 = copycnt(), copyalpha()
  run({0x0F, 0x00, 0x20, 0xF1, 0x03, 0x02, 0x09, 0x04, 0x68, 0x02}); wait(70)   -- loadword 0, text; callstd 4; closemessage
  shot(string.format("%s_%s", NAME, tag))
  if MIST[weather] then
    check(cnt() == c0 and alpha() == a0, string.format("%s, message up: BLDCNT %04X BLDALPHA %04X - the weather's own (%04X %04X): no see-through box", tag, cnt(), alpha(), c0, a0))
  else
    check(cnt() == 0x1E41, string.format("%s, message up: BLDCNT %04X BLDALPHA %04X - the see-through box", tag, cnt(), alpha()))
  end
  tap(K.A); wait(40); clear(); wait(20)
  check(cnt() == copycnt() and alpha() == copyalpha() and emu:read16(0x04000048) == 0x1F1F, string.format(
    "%s, after it: BLDCNT %04X BLDALPHA %04X WININ %04X - the weather's own %04X %04X", tag, cnt(), alpha(), emu:read16(0x04000048), copycnt(), copyalpha()))
end
local co = coroutine.create(function()
  run({0x39, 0, 17, 0xFF, 9, 0, 6, 0, 0x02}); wait(420)              -- Route 102
  tap(K.UP, 24); wait(90); clear(); wait(30)
  for _, n in ipairs({0, 1, 6, 7, 8, 9, 10, 14}) do
    run({0xA4, n, 0, 0xA5, 0x02}); wait(300)                         -- setweather n; doweather
    message(string.format("weather_%02d", n), n)
  end
  run({0xA4, 0, 0, 0xA5, 0x02}); wait(60)
  run({0x39, 24, 4, 0, 0, 0, 0, 0, 0x02}); wait(420)                 -- Rusturf Tunnel
  clear(); wait(30)
  local wt = emu:read8(sb1() + 0x2E)
  w(string.format("Rusturf Tunnel: weather %d", wt))
  message("rusturf", wt)
  w(fails == 0 and "PASS" or ("FAILED: " .. fails))
  done()
end)
function TEST(f)
  if coroutine.status(co) == "dead" then return end
  local ok, err = coroutine.resume(co)
  if not ok then w("error: " .. tostring(err)); done() end
end
