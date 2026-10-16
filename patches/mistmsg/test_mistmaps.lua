-- Messages in the mist, map by map. For every map in LISTFILE (lines "group num x y weather name", made by
-- mistmaps.py from the map headers: every map whose weather is fog, diagonal fog or underwater) the player is
-- warped in, the weather is left 420 frames to settle, then a message is put up and closed:
--   - the weather running must be a mist one (6, 9, 10, 14), with see-through sprites on screen;
--   - with the message up, BLDCNT / BLDALPHA / WININ must be what the weather has (no see-through box);
--   - after it, the same.
-- Then Mt. Pyre Exterior (24/21), the one map that switches fog on by script: arriving from the summit (its
-- on-transition script sets fog above row 12) and walking onto its fog trigger at (25, 21) from below.
-- Screenshots <NAME>_<group>_<num>_field.png / _msg.png. The log <NAME>_log.txt, last line PASS.
NAME = NAME or "mistmaps"
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
local function clear() for i = 1, 900 do if lock() == 0 and cb2() == OVERWORLD then return true end; if i % 30 == 0 then tap(K.B) end; coroutine.yield() end return false end
local function regs() return emu:read16(0x04000050), emu:read16(0x04000052), emu:read16(0x04000048) end
local function copy() return emu:read16(0x03000868), emu:read16(0x0300086A) end
local function semi()
  local n = 0
  for i = 0, 127 do
    local a0 = emu:read16(0x07000000 + i * 8)
    if (a0 & 0x300) ~= 0x200 and ((a0 >> 10) & 3) == 1 then n = n + 1 end
  end
  return n
end
local MIST = {[6] = true, [9] = true, [10] = true, [14] = true}
local TEXT = {0xC2, 0xD9, 0xE0, 0xE0, 0xE3, 0xAD, 0xFF}             -- "Hello."
-- the message, on the map the player is on now
local function msgcheck(tag, g, m)
  local cur = emu:read8(0x02038454 + 0x6D0)
  local c0, a0 = copy()
  tag = string.format("%s (running weather %d, %d see-through sprites)", tag, cur, semi())
  shot(string.format("%s_%02d_%03d_field", NAME, g, m))
  for i, b in ipairs(TEXT) do emu:write8(0x0203F120 + i - 1, b) end
  run({0x0F, 0x00, 0x20, 0xF1, 0x03, 0x02, 0x09, 0x04, 0x68, 0x02}); wait(70)     -- loadword 0, text; callstd 4; closemessage
  local c1, a1, wi1 = regs()
  shot(string.format("%s_%02d_%03d_msg", NAME, g, m))
  tap(K.A); wait(40); clear(); wait(20)
  local c2, a2, wi2 = regs()
  check(MIST[cur] and c1 == c0 and a1 == a0 and wi1 == 0x1F1F and c2 == c0 and a2 == a0 and wi2 == 0x1F1F, string.format(
    "%s: weather's BLDCNT %04X BLDALPHA %04X; message up %04X %04X WININ %04X; after %04X %04X WININ %04X", tag, c0, a0, c1, a1, wi1, c2, a2, wi2))
end
local co = coroutine.create(function()
  local maps = {}
  for line in io.open(os.getenv("LISTFILE")):lines() do
    local g, m, x, y, wt, nm = line:match("(%d+) (%d+) (%d+) (%d+) (%d+) (%S+)")
    if g then maps[#maps + 1] = {tonumber(g), tonumber(m), tonumber(x), tonumber(y), tonumber(wt), nm} end
  end
  run({0x39, 0, 17, 0xFF, 9, 0, 6, 0, 0x02}); wait(420)              -- the save's first-step prompt, on Route 102
  tap(K.UP, 24); wait(90); clear()
  for _, mp in ipairs(maps) do
    local g, m, x, y, wt, nm = table.unpack(mp)
    run({0x39, g, m, 0xFF, x, 0, y, 0, 0x02}); wait(420)
    local free = clear(); wait(30)
    local tag = string.format("%d/%d %s (header weather %d%s)", g, m, nm, wt, free and "" or ", a script still had the field")
    if emu:read8(sb1() + 4) ~= g or emu:read8(sb1() + 5) ~= m then check(false, tag .. ": the warp did not land there")
    else msgcheck(tag, g, m) end
  end
  run({0x39, 24, 21, 1, 0, 0, 0, 0, 0x02}); wait(420); clear(); wait(30)                 -- Mt. Pyre Exterior, from the summit
  msgcheck("24/21 MtPyre_Exterior, arriving from the summit", 24, 21)
  run({0x39, 0, 17, 0xFF, 9, 0, 6, 0, 0x02}); wait(420); clear()                          -- away (sunny), then below the trigger
  run({0x39, 24, 21, 0xFF, 25, 0, 22, 0, 0x02}); wait(420); clear(); wait(30)
  w(string.format("   Mt. Pyre Exterior at (25, 22): weather %d", emu:read8(0x02038454 + 0x6D0)))
  tap(K.UP, 24); wait(60); clear(); wait(300)
  msgcheck("24/21 MtPyre_Exterior, after its fog trigger at (25, 21)", 24, 210)
  w(fails == 0 and "PASS" or ("FAILED: " .. fails))
  done()
end)
function TEST(f)
  if coroutine.status(co) == "dead" then return end
  local ok, err = coroutine.resume(co)
  if not ok then w("error: " .. tostring(err)); done() end
end
