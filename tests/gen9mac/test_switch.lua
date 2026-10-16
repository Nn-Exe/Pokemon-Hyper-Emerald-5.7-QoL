-- Switching out and back in (Palafin's Zero to Hero would turn it into its Hero Form in Scarlet/Violet; here the
-- ability is a stand-in and the form must stay, without a freeze): LEAD and SECOND (givemon Lv 50) are the party, a
-- wild Blissey Lv 50 (only Splash). At the action menu: Pokemon -> the second -> Shift; at the next menu the same
-- back to the lead; a third menu. Logged at each menu: our battler (species, HP, ability) and the foe; shots
-- sw_<n>.png at each menu and every 40 frames of the switches.
local E = os.getenv
DIR = E("GEN9_DIR")
NAME = (E("TAG") or "sw") .. "_switch"
dofile("C:/Users/nonth/Desktop/Works & Productivity/gba-trans/hyper-emerald-en-qol/patches/dexnavchain/test_boot.lua")
local LEAD, SECOND = tonumber(E("LEAD")), tonumber(E("SECOND") or "242")
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
local function bat(i)
  local m = MONS + 0x58 * i
  return string.format("species %d hp %d/%d ability %d", emu:read16(m), emu:read16(m + 0x28), emu:read16(m + 0x2C),
    emu:read16(ABIL16 + 2 * i))
end
local t0, phase, mark, menus, shots = nil, "setup", 0, 0, 0
local function finish(msg) w(msg); phase = "end"; done() end
function TEST(f)
  t0 = t0 or f
  local d = f - t0
  if phase == "end" then return end
  if d == 2 then emu:write8(0x020244E9, 0); for i = 0, 599 do emu:write8(PARTY + i, 0) end; give(LEAD, 50) end
  if d == 30 then give(SECOND, 50) end
  if d == 60 then
    w(string.format("party: %d %d (count %d)", emu:read16(PARTY + 0x20), emu:read16(PARTY + 100 + 0x20), emu:read8(0x020244E9)))
    run({0xB6, 242, 0, 50, 0, 0, 0xB7, 0x02})
  end
  if phase == "setup" and d > 70 and cb2() == BATTLE then phase = "intro"; mark = d end
  if phase == "setup" and d > 2000 then finish("the battle never started (FAIL)") end
  if phase ~= "setup" then                       -- the foe knows only Splash
    emu:write16(MONS + 0x58 + 0x0C, 150); for k = 1, 3 do emu:write16(MONS + 0x58 + 0x0C + 2 * k, 0) end
  end
  if phase == "intro" or phase == "wait" then
    if emu:read32(0x03005D60) == ACTION and d > mark + 60 then
      menus = menus + 1
      w(string.format("menu %d: ours %s | foe %s", menus, bat(0), bat(1)))
      shot(string.format("%s_menu%d", NAME, menus))
      if menus == 3 then finish("switched out and back in (PASS)"); return end
      phase = "switch"; mark = d
    elseif (d - mark) % 30 == 0 then tap(phase == "intro" and K.A or K.B) end
    if d > mark + 4000 then shot(NAME .. "_stuck"); finish("STUCK in " .. phase .. " (FAIL)") end
  end
  if phase == "switch" then
    if d == mark + 10 then tap(K.DOWN) end                     -- Pokemon (under Fight)
    if d == mark + 25 then tap(K.LEFT) end
    if d == mark + 40 then tap(K.A) end
    if d == mark + 160 then tap(K.DOWN) end    -- the other one: the battle's party screen puts the one out first
    if d == mark + 200 then shot(string.format("%s_party%d", NAME, menus)); tap(K.A) end
    if d == mark + 260 then shot(string.format("%s_choice%d", NAME, menus)); tap(K.A) end   -- Shift
    if d == mark + 300 then phase = "wait"; mark = d end
  end
  if phase == "wait" and (d - mark) % 40 == 0 and shots < 40 then shots = shots + 1; shot(string.format("%s_w%02d", NAME, shots)) end
end
