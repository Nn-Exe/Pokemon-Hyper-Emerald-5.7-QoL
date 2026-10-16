-- EV-IV Display: every picture in its own colours. For each pair (A, B) the lead becomes A and the second Pokemon
-- B (copies of the lead with another species), the display is opened (item 650 on UP of the SELECT ring) and RIGHT
-- goes from A to B, LEFT back to A. The 15 colours in the palette slot of the picture on screen must be the ones
-- the same species gets when the display is opened on it alone. Pairs: three that share a palette tag (species past
-- No. 439 have tag 1 or 0, Bulbasaur has 1), then two that do not (1 and 0; two tags of their own), as controls.
-- Before the patch the shared ones fail: the second picture keeps the first one's colours. Log <NAME>_log.txt, last
-- line PASS; screenshots.
NAME = NAME or "evivpal"
dofile(BOOT or ((DIR or "./") .. "../dexnavchain/test_boot.lua"))
local PARTY, STATE = 0x020244EC, 0x0203FFF0
local PAIRS = {{529, 561}, {1100, 1198}, {1, 529}, {700, 1123}, {25, 150}}
local function sb1() return emu:read32(0x03005D8C) end
local function wait(n) for _ = 1, n do coroutine.yield() end end
local function tag(sp) return emu:read16(0x08F25520 + 8 * sp + 4) end
local fails = 0
local function check(ok, msg)
  if not ok then fails = fails + 1 end
  w((ok and "   ok    " or "   FAIL  ") .. msg)
end
-- the colours of the picture on screen: the slide task's sprite (data[2]), its OAM palette, palette RAM
local function colours()
  local task = emu:read8(emu:read32(STATE) + 4)
  local spr = emu:read16(0x03005E00 + task * 40 + 0xC)
  local pal = emu:read8(0x02020630 + spr * 0x44 + 5) >> 4
  local t = {}
  for i = 1, 15 do t[#t + 1] = string.format("%04X", emu:read16(0x05000200 + pal * 32 + i * 2)) end
  return table.concat(t, " "), pal
end
local lead
local function party(a, b)
  for i, sp in ipairs({a, b}) do
    local m = PARTY + 100 * (i - 1)
    for k = 0, 99 do emu:write8(m + k, lead:byte(k + 1)) end
    emu:write16(m + 0x20, sp)
  end
end
local function open() tap(K.SEL); wait(50); tap(K.UP); wait(200) end
local function close()
  for i = 1, 600 do
    if cb2() == OVERWORLD and lock() == 0 then break end
    if i % 25 == 1 then tap(K.B) end
    coroutine.yield()
  end
  wait(30)
end
local co = coroutine.create(function()
  emu:write16(sb1() + 0x496, 650)
  lead = emu:readRange(PARTY, 100)
  local saved = emu:readRange(PARTY + 100, 100)
  local ref = {}
  for _, p in ipairs(PAIRS) do
    for _, sp in ipairs(p) do
      if not ref[sp] then party(sp, sp); open(); ref[sp] = colours(); close() end
    end
  end
  for _, p in ipairs(PAIRS) do
    local a, b = p[1], p[2]
    party(a, b); open()
    local ca = colours()
    tap(K.RIGHT); wait(200)
    local cb, pb = colours()
    shot(string.format("%s_%d_%d", NAME, a, b))
    tap(K.LEFT); wait(200)
    local ca2, pa2 = colours()
    check(ca == ref[a] and cb == ref[b] and ca2 == ref[a], string.format(
      "%d (tag %d) -> %d (tag %d) -> back: the pictures' colours %s, %s, %s (slots %d, %d)", a, tag(a), b, tag(b),
      ca == ref[a] and "right" or "WRONG", cb == ref[b] and "right" or ("WRONG: " .. (cb == ref[a] and "the first one's" or "other")),
      ca2 == ref[a] and "right" or "WRONG", pb, pa2))
    close()
  end
  for k = 0, 99 do emu:write8(PARTY + k, lead:byte(k + 1)); emu:write8(PARTY + 100 + k, saved:byte(k + 1)) end
  w(fails == 0 and "PASS" or ("FAILED: " .. fails))
  done()
end)
function TEST(f)
  if coroutine.status(co) == "dead" then return end
  local ok, err = coroutine.resume(co)
  if not ok then w("error: " .. tostring(err)); done() end
end
