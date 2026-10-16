-- The gold healthbox fades with the screen. A wild battle on Route 102, both battlers made shiny the way shinybox
-- reads it (gBattleMons[n].otId = personality), then, watching palette RAM every frame - colour 2, the box fill, of
-- the gold slot against the same colour of the stock box palette (tag 0xD6FF):
--   1. at the action menu the boxes are on the gold slot and it holds the gold;
--   2. into the Bag (a fade to black): the gold is never left brighter than the stock box, and is black when it is;
--   3. back from the Bag: the boxes are gold again, at full brightness;
--   4. running away (the end-of-battle fade): as 2.
-- Before the patch 2 and 4 fail: the gold stays at full brightness to the last frame. Screenshots <NAME>_*.png,
-- the log <NAME>_log.txt, last line PASS. Every case starts from a warp to (9, 6): see test_dexnavabil.lua.
NAME = NAME or "shinyfade"
dofile(BOOT or ((DIR or "./") .. "../dexnavchain/test_boot.lua"))
local MONS, TAGS = 0x02024084, 0x03000CF0
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
local function bright(c) return (c & 31) + ((c >> 5) & 31) + ((c >> 10) & 31) end
local function ram(slot, i) return emu:read16(0x05000200 + slot * 32 + i * 2) end
local function unfaded(slot, i) return emu:read16(0x02037914 + slot * 32 + i * 2) end
local function stockslot()
  for i = 0, 15 do if emu:read16(TAGS + 2 * i) == 0xD6FF then return i end end
end
-- the palette slots of the healthbox bodies, by battler
local function boxes()
  local t = {}
  for i = 0, 63 do
    local s = 0x02020630 + i * 0x44
    if (emu:read16(s + 0x3E) & 1) == 1 and emu:read32(s + 0x1C) == 0x08007429 then
      local bar = emu:read16(s + 0x38)
      if bar < 64 and emu:read32(0x02020630 + bar * 0x44 + 0x1C) == 0x080728B5 then t[emu:read16(s + 0x3A)] = (emu:read16(s + 4) >> 12) & 15 end
    end
  end
  return t
end
local function menu() return emu:read32(0x03005D60) == 0x08057589 end
-- every frame until `stop` says so: how bright the gold is next to the stock box, as fractions of their full colours
local function watch(tag, gold, full, stop, shots)
  local n, worst, lit, dark, lastg = 0, 0, 0, 0, 2
  while not stop(n) and n < 900 do
    coroutine.yield(); n = n + 1
    local st = stockslot()
    local b = boxes()
    if st and (b[0] == gold or b[1] == gold) then
      local g = bright(ram(gold, 2)) / bright(full)
      local s = bright(ram(st, 2)) / bright(unfaded(st, 2))
      if g - s > worst then worst = g - s end
      if s < 0.05 then dark = dark + 1; if g > 0.05 then lit = lit + 1 end end
      if shots and shots[n] then shot(string.format("%s_%s_%02d", NAME, tag, n)) end
    end
  end
  check(worst <= 0.15 and lit == 0, string.format("%s: %d frames; the gold at most %.2f brighter than the stock box; lit on %d of the %d frames the box was black",
    tag, n, worst, lit, dark))
end
local co = coroutine.create(function()
  run({0x39, 0, 17, 0xFF, 9, 0, 6, 0, 0x02}); wait(390)              -- Route 102
  tap(K.UP, 24); wait(90)                                            -- the save's Repel prompt, if it has one
  for i = 1, 900 do if lock() == 0 then break end; if i % 30 == 0 then tap(K.B) end; coroutine.yield() end
  local n = 0
  while cb2() ~= BATTLE do                                            -- walk the grass until something bites
    n = n + 1
    if lock() ~= 0 then if n % 30 == 0 then tap(K.B) end
    else local p = n % 64; if p == 1 then tap(K.LEFT, 28) elseif p == 33 then tap(K.RIGHT, 28) end end
    if n > 40000 then w("no battle"); done(); return end
    coroutine.yield()
  end
  for i = 1, 3000 do if menu() then break end; if i % 30 == 0 then tap(K.A) end; coroutine.yield() end
  wait(30)
  emu:write32(MONS + 0x54, emu:read32(MONS + 0x48))
  emu:write32(MONS + 0x58 + 0x54, emu:read32(MONS + 0x58 + 0x48))
  wait(30)
  local b = boxes()
  local gold = b[0]
  local full = gold and unfaded(gold, 2) or 0
  check(gold and gold >= 10 and b[1] == gold and ram(gold, 2) == full and bright(full) > 40,
    string.format("at the menu: my box on slot %s, the foe's on %s; colour 2 there %04X (unfaded %04X)", tostring(b[0]), tostring(b[1]), gold and ram(gold, 2) or 0, full))
  shot(NAME .. "_1_gold")
  tap(K.RIGHT); wait(20); tap(K.A)
  watch("into the Bag", gold, full, function(k) return cb2() ~= BATTLE end, {[6] = true, [12] = true, [18] = true, [22] = true})
  wait(120); w(string.format("in the Bag: cb2 %08X", cb2()))
  tap(K.B)
  for i = 1, 600 do if cb2() == BATTLE and menu() then break end; coroutine.yield() end
  wait(40)
  b = boxes()
  check(b[0] and b[0] >= 10 and b[1] == b[0] and ram(b[0], 2) == full, string.format("back from the Bag: boxes on slots %s / %s, colour 2 %04X",
    tostring(b[0]), tostring(b[1]), b[0] and ram(b[0], 2) or 0))
  shot(NAME .. "_2_back")
  gold = b[0] or gold
  -- run: Bag is under the cursor, Run is below it
  local started = false
  watch("running away", gold, full, function(k)
    if cb2() ~= BATTLE then return true end
    local q = k % 90
    if q == 1 then tap(K.DOWN) elseif q == 20 then tap(K.RIGHT) elseif q == 40 then tap(K.A) end
    return false
  end, {})
  check(cb2() ~= BATTLE, string.format("the battle is over: cb2 %08X", cb2()))
  w(fails == 0 and "PASS" or ("FAILED: " .. fails))
  done()
end)
function TEST(f)
  if coroutine.status(co) == "dead" then return end
  local ok, err = coroutine.resume(co)
  if not ok then w("error: " .. tostring(err)); done() end
end
