-- The Pokedex on the renumbered Gen 9 build (gen9dex). Numbers 906-1025 are marked seen and caught in the new
-- scheme (SaveBlock1 bits below 960, gen9rest's area with the marker "DEXA" above), then a key script runs with a
-- screenshot after each step. KEYS = a list of key[*count][@wait] separated by spaces, e.g. "START A@200 R*20 SEL";
-- "shot:name" takes a picture. MARKER=n: dexext's marker word written first (test 4's build: "DEX9" = 0x39584544).
-- Logged: what was marked.
local E = os.getenv
DIR = E("GEN9_DIR")
NAME = (E("TAG") or "pd") .. "_dex"
dofile("C:/Users/nonth/Desktop/Works & Productivity/gba-trans/hyper-emerald/hyper-emerald-en-qol/patches/dexnavchain/test_boot.lua")
local EXT = 0x0203DA00
local function sb1() return emu:read32(0x03005D8C) end
local function setbit(base, n)
  local a = base + (n >> 3)
  emu:write8(a, emu:read8(a) | (1 << (n & 7)))
end
local KEYMAP = {A = K.A, B = K.B, SEL = K.SEL, START = K.START, RIGHT = K.RIGHT, LEFT = K.LEFT, UP = K.UP,
                DOWN = K.DOWN, R = K.R, L = K.L}
local steps = {}
for tok in (E("KEYS") or ""):gmatch("%S+") do
  local shotname = tok:match("^shot:(.+)$")
  if shotname then steps[#steps + 1] = {shot = shotname}
  else
    local k, cnt, wt = tok:match("^(%a+)%*?(%d*)@?(%d*)$")
    steps[#steps + 1] = {key = KEYMAP[k], count = tonumber(cnt) or 1, wait = tonumber(wt) or 30}
  end
end
local t0, d0, i, rep, nextAt = nil, nil, 1, 0, 0
function TEST(f)
  t0 = t0 or f
  local d = f - t0
  if d == 5 then
    if emu:read32(EXT) ~= 0x41584544 then w(string.format("marker before: %08X (not DEXA)", emu:read32(EXT))) end
    if E("MARKER") then                          -- MARKER=0x39584544: test 4's kind ("DEX9"), the area cleared
      emu:write32(EXT, tonumber(E("MARKER"))); for i = 4, 67 do emu:write8(EXT + i, 0) end
    end
    for n = tonumber(E("FIRST") or "906"), tonumber(E("LAST") or "1025") do
      if n < 960 then setbit(sb1() + 0x560, n); setbit(sb1() + 0x5D8, n)
      else setbit(EXT + 4, n - 960); setbit(EXT + 36, n - 960) end
    end
    w(string.format("marked %s-%s seen and caught (marker %08X)", E("FIRST") or "906", E("LAST") or "1025", emu:read32(EXT)))
    nextAt = 30
  end
  if d < 30 or d < nextAt then return end
  local s = steps[i]
  if not s then w("keys done"); done(); nextAt = 1e9; return end
  if s.shot then shot(NAME .. "_" .. s.shot); i = i + 1; nextAt = d + 2; return end
  tap(s.key, 4); rep = rep + 1
  nextAt = d + s.wait
  if rep >= s.count then rep = 0; i = i + 1 end
end
