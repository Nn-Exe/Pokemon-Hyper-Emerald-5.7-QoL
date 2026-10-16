-- Hospitality (gen9rest's stand-in: Healer) in a double battle: HOLDER (slot 1, ability slot ABSLOT) beside ALLY
-- (slot 2), both Lv 100 knowing only Splash, against TRAINER (56: a double battle); the ally poisoned (status 8,
-- in battle and in the party) at the first menu. Both sides' HP held every frame (nobody faints); A through every
-- choice and message. ABIL=n: the holder's battle ability written every frame instead (ABIL=0: the control).
-- Logged: each turn's end, the ally's status; "cured at turn k" the first time it is 0. Healer: 30% a turn.
local E = os.getenv
DIR = E("GEN9_DIR")
NAME = (E("TAG") or "hl") .. "_healer"
dofile("C:/Users/nonth/Desktop/Works & Productivity/gba-trans/hyper-emerald-en-qol/patches/dexnavchain/test_boot.lua")
local HOLDER, ALLY = tonumber(E("HOLDER")), tonumber(E("ALLY") or "242")
local TRAINER, TURNS = tonumber(E("TRAINER") or "56"), tonumber(E("TURNS") or "12")
local ABIL = E("ABIL") and tonumber(E("ABIL"))
local SCRIPT, PARTY, MONS, ACTION, ABIL16 = 0x0203F100, 0x020244EC, 0x02024084, 0x08057589, 0x0203F000
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1); emu:write8(0x03000E38, 0)
end
local function give(sp, lv) run({0x79, sp & 0xFF, sp >> 8, lv, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0x02}) end
local t0, phase, mark, menus, cured, shots = nil, "setup", 0, 0, nil, 0
local function finish(msg) w(msg); phase = "end"; done() end
function TEST(f)
  t0 = t0 or f
  local d = f - t0
  if phase == "end" then return end
  if d == 2 then emu:write8(0x020244E9, 0); for i = 0, 599 do emu:write8(PARTY + i, 0) end; give(HOLDER, 100) end
  if d == 30 then give(ALLY, 100) end
  if d == 60 then
    local iv = emu:read32(PARTY + 0x48)
    emu:write32(PARTY + 0x48, E("ABSLOT") == "1" and (iv | 0x80000000) or (iv & 0x7FFFFFFF))
    for p = 0, 1 do
      emu:write16(PARTY + 100 * p + 0x2C, 150); emu:write8(PARTY + 100 * p + 0x34, 40)
      for k = 1, 3 do emu:write16(PARTY + 100 * p + 0x2C + 2 * k, 0); emu:write8(PARTY + 100 * p + 0x34 + k, 0) end
    end
    emu:write32(PARTY + 100 + 0x50, 8)
    w(string.format("party: %d %d (count %d)", emu:read16(PARTY + 0x20), emu:read16(PARTY + 100 + 0x20), emu:read8(0x020244E9)))
    run({0x5C, 0x03, TRAINER & 0xFF, TRAINER >> 8, 0, 0, 0xA0, 0xFE, 0x57, 0x08, 0x02})
  end
  if phase == "setup" and d > 70 and cb2() == BATTLE then phase = "battle"; mark = d end
  if phase == "setup" and d > 2000 then finish("the battle never started (FAIL)") end
  if phase == "battle" then
    if ABIL then emu:write16(ABIL16, ABIL); emu:write8(MONS + 0x20, ABIL & 0xFF) end
    for i = 0, 3 do emu:write16(MONS + 0x58 * i + 0x28, emu:read16(MONS + 0x58 * i + 0x2C)) end
    local atMenu = emu:read32(0x03005D60) == ACTION
    if atMenu and not inMenu then
      menus = menus + 1
      if menus == 1 then
        emu:write32(MONS + 0x58 * 2 + 0x4C, 8); emu:write32(PARTY + 100 + 0x50, 8)
        w(string.format("battlers: %d (ability %d) and %d beside it | foes %d %d | battle type %08X", emu:read16(MONS),
          emu:read16(ABIL16), emu:read16(MONS + 0x58 * 2), emu:read16(MONS + 0x58), emu:read16(MONS + 0x58 * 3),
          emu:read32(0x02022FEC)))
      end
      local st = emu:read32(MONS + 0x58 * 2 + 0x4C)
      w(string.format("turn %d begins: the ally's status %08X (party %08X)", menus, st, emu:read32(PARTY + 100 + 0x50)))
      if st == 0 and not cured and menus > 1 then cured = menus - 1; w("cured at the end of turn " .. cured) end
      if menus > TURNS or cured then
        shot(NAME .. "_end")
        finish(cured and ("the ally was cured (turn " .. cured .. ")") or ("not cured in " .. TURNS .. " turns"))
        return
      end
    end
    inMenu = atMenu
    if (d - mark) % 20 == 0 then tap(K.A) end
    if d % 60 == 0 and shots < 60 then shots = shots + 1; shot(string.format("%s_%03d", NAME, shots)) end
    if d > mark + 40000 then finish("timed out (FAIL)") end
  end
end
