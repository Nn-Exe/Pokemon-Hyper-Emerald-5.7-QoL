-- The DexNav search bar's icon: which palette slot does it draw with, and what is in that slot?
-- Route 102, R opens the DexNav, the ring to Land row ROW column COL, A registers it; back on the field, at a few
-- moments (and after WALK steps on the grass), every sprite in use is logged (position, palette slot, the palette tag
-- its template asks for) with the 16 palette slots: their tags (sSpritePaletteTags) and which mon-icon palette (0-2)
-- each one's colours equal, in palette RAM and in gPlttBufferFaded.
local E = os.getenv
DIR = E("GEN9_DIR")
local TAG = E("TAG") or "bp"
NAME = TAG .. "_bar"
dofile("C:/Users/nonth/Desktop/Works & Productivity/gba-trans/hyper-emerald/hyper-emerald-en-qol/patches/dexnavchain/test_boot.lua")
local ROW, COL, WALK = tonumber(E("ROW") or "2"), tonumber(E("COL") or "0"), tonumber(E("WALK") or "0")
local SCRIPT, STATE = 0x0203F100, 0x0203A660
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1); emu:write8(0x03000E38, 0)
end
local ICONPALS = {}
for k = 0, 2 do
  local p = emu:read32(0x0857C540 + 8 * k)
  local t = {}
  for c = 0, 15 do t[c] = emu:read16(p + 2 * c) end
  ICONPALS[k] = t
end
local function whichIcon(base)
  for k = 0, 2 do
    local same = true
    for c = 1, 15 do if emu:read16(base + 2 * c) ~= ICONPALS[k][c] then same = false; break end end
    if same then return "icon" .. k end
  end
  return "-"
end
local function dump(label)
  w("== " .. label .. string.format(" (registered %d, reserved palettes %d)", emu:read16(STATE + 2), emu:read8(0x0300301C)))
  for i = 0, 63 do
    local s = 0x02020630 + 0x44 * i
    if emu:read8(s + 0x3E) & 1 == 1 then
      local tmpl = emu:read32(s + 0x14)
      local ptag = (tmpl >= 0x08000000 and tmpl < 0x0A000000 or tmpl >= 0x02000000 and tmpl < 0x04000000) and emu:read16(tmpl + 2) or -1
      local y, x = emu:read8(s), emu:read16(s + 2) & 0x1FF
      w(string.format("  sprite %2d at %3d,%3d pal slot %2d template %08X paletteTag %04X cb %08X prio %d", i, x, y,
        emu:read8(s + 5) >> 4, tmpl, ptag & 0xFFFF, emu:read32(s + 0x1C), (emu:read8(s + 5) >> 2) & 3))
    end
  end
  local t = {}
  for k = 0, 15 do
    t[#t + 1] = string.format("%d:%04X %s/%s", k, emu:read16(0x03000CF0 + 2 * k), whichIcon(0x05000200 + 32 * k),
      whichIcon(0x02037D14 + 0x200 + 32 * k))
  end
  w("  slots (tag ram/faded): " .. table.concat(t, "  "))
end
local steps = {}
local function at(d, fn) steps[d] = fn end
at(5, function() run({0x39, 0, 17, 0xFF, 9, 0, 6, 0, 0x02}) end)
at(500, function() dump("field before"); tap(K.R) end)
local d = 700
for _ = 1, ROW do at(d, function() tap(K.DOWN) end); d = d + 40 end
for _ = 1, COL do at(d, function() tap(K.RIGHT) end); d = d + 40 end
at(d, function() shot(NAME .. "_pick"); dump("dexnav screen") end); d = d + 20
at(d, function() tap(K.A) end); d = d + 300
at(d, function() shot(NAME .. "_bar0"); dump("bar up") end)
at(d + 300, function() shot(NAME .. "_bar1"); dump("bar, 300 frames on") end)
local wd = d + 320
for k = 1, WALK do
  local dir = (k % 4 < 2) and K.LEFT or K.RIGHT
  at(wd, function() tap(dir, 16) end)
  if k % 4 == 0 then at(wd + 10, function() shot(string.format("%s_walk%02d", NAME, k)); dump("after step " .. k) end) end
  wd = wd + 30
end
at(wd + 60, function() shot(NAME .. "_end"); dump("end"); done() end)
local t0
function TEST(f)
  t0 = t0 or f
  local fn = steps[f - t0]
  if fn then fn() end
end
