-- A battle set up to trigger one ability (gen9rest's stand-ins: each is its template's id in battle, 0x09B00764).
-- Ours: HOLDER (givemon Lv LV, default 50) with ABSLOT (0/1: the IV word's bit 31) and MOVES=a,b,c,d (PP 20);
--   ABIL=n: the battle ability (16-bit at 0x0203F000 and gBattleMons' byte) written at every menu instead (a hidden
--   ability, or a control run with the ability taken away: ABIL=0); ITEM=held item; HP=percent of max HP at the
--   first menu; STATUS=status1 at the first menu (8 poison); SECOND=a second party Pokemon; SWITCH=k: at menu k,
--   switch to it (POKEMON -> the second -> Shift) instead of a move; RUN=1: Run at every menu.
--   OURMOVE=i,j,...: the move slot used at menu 1, 2, ... (default 0).
-- Foe: FOE (wild, Lv FOELV, default 50) knowing only FOEMOVES (written to gBattleMons at each menu, PP 20).
-- SEED=n: the random numbers set to n before the Pokemon are made and to n + menu at each menu (two runs that differ
-- only in ABIL get the same Pokemon and the same rolls).
-- PINRNG=1 (with SEED): the random numbers held at n + menu every frame of the turn, so both runs roll the same.
-- WEATHER=n: gBattleWeather (u16 0x020243CC) at the first menu.
-- TURNS (default 3). Logged: at each menu both battlers (species, HP, ability, stat stages, status), the weather
-- and the field word *(*(0x02024218) + 0xD4); every change of either HP (frame by frame: damage and healing);
-- the outcome. Shots: every 30 frames from the first menu, 80 at most (ab_NNN.png).
local E = os.getenv
DIR = E("GEN9_DIR")
NAME = (E("TAG") or "ab") .. "_ab"
dofile("C:/Users/nonth/Desktop/Works & Productivity/gba-trans/hyper-emerald/hyper-emerald-en-qol/patches/dexnavchain/test_boot.lua")
local function list(s) local t = {}; for n in (s or ""):gmatch("%d+") do t[#t + 1] = tonumber(n) end; return t end
local HOLDER, LV, FOE, FOELV = tonumber(E("HOLDER")), tonumber(E("LV") or "50"), tonumber(E("FOE")), tonumber(E("FOELV") or "50")
local MOVES, FOEMOVES, OURMOVE = list(E("MOVES")), list(E("FOEMOVES")), list(E("OURMOVE"))
local TURNS = tonumber(E("TURNS") or "3")
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
local function field() local p = emu:read32(0x02024218); return p ~= 0 and emu:read32(p + 0xD4) or 0 end
local function bat(i)
  local m = MONS + 0x58 * i
  local st = {}
  for k = 0, 7 do st[#st + 1] = emu:read8(m + 0x18 + k) end
  return string.format("species %d hp %d/%d ability %d (byte %d) stages %s status %08X item %d", emu:read16(m),
    emu:read16(m + 0x28), emu:read16(m + 0x2C), emu:read16(ABIL16 + 2 * i), emu:read8(m + 0x20), table.concat(st, ","),
    emu:read32(m + 0x4C), emu:read16(m + 0x2E))
end
local t0, phase, mark, menu, chosen, shots, lasthp = nil, "setup", 0, 0, 0, 0, {}
local function finish(msg) w(msg); phase = "end"; done() end
local function setAbil()
  if ABIL then emu:write16(ABIL16, ABIL); emu:write8(MONS + 0x20, ABIL & 0xFF) end
end
local function foeMoves()
  if #FOEMOVES == 0 then return end
  for k = 0, 3 do
    emu:write16(MONS + 0x58 + 0x0C + 2 * k, FOEMOVES[k + 1] or 0); emu:write8(MONS + 0x58 + 0x24 + k, FOEMOVES[k + 1] and 20 or 0)
  end
end
function TEST(f)
  t0 = t0 or f
  local d = f - t0
  if phase == "end" then return end
  if E("SEED") and (d == 2 or d == 59) then emu:write32(0x03005D80, tonumber(E("SEED"))) end   -- the same Pokemon each run
  if d == 2 then emu:write8(0x020244E9, 0); for i = 0, 599 do emu:write8(PARTY + i, 0) end; give(HOLDER, LV) end
  if d == 30 and E("SECOND") then give(tonumber(E("SECOND")), LV) end
  if d == 60 then
    local iv = emu:read32(PARTY + 0x48)
    if E("ABSLOT") == "1" then iv = iv | 0x80000000 else iv = iv & 0x7FFFFFFF end
    emu:write32(PARTY + 0x48, iv)
    for k = 0, 3 do emu:write16(PARTY + 0x2C + 2 * k, MOVES[k + 1] or 0); emu:write8(PARTY + 0x34 + k, MOVES[k + 1] and 20 or 0) end
    if E("ITEM") then emu:write16(PARTY + 0x22, tonumber(E("ITEM"))) end
    w(string.format("party: %d %d (count %d), ours ability slot %s", emu:read16(PARTY + 0x20), emu:read16(PARTY + 100 + 0x20),
      emu:read8(0x020244E9), E("ABSLOT") or "0"))
    run({0xB6, FOE & 0xFF, FOE >> 8, FOELV, 0, 0, 0xB7, 0x02})
  end
  if phase == "setup" and d > 70 and cb2() == BATTLE then phase = "intro"; mark = d end
  if phase == "setup" and d > 2000 then finish("the battle never started (FAIL)") end
  if phase ~= "setup" and cb2() == BATTLE then
    setAbil()
    if E("PINRNG") and E("SEED") and phase == "wait" then emu:write32(0x03005D80, tonumber(E("SEED")) + menu) end
    for i = 0, 1 do                             -- every change of HP
      local hp = emu:read16(MONS + 0x58 * i + 0x28)
      if lasthp[i] and hp ~= lasthp[i] and emu:read16(MONS + 0x58 * i) ~= 0 then
        w(string.format("  menu %d +%d: battler %d hp %d -> %d (%+d)", menu, d - mark, i, lasthp[i], hp, hp - lasthp[i]))
      end
      lasthp[i] = hp
    end
  end
  if menu > 0 and d % 30 == 0 and shots < 80 then shots = shots + 1; shot(string.format("%s_%03d", NAME, shots)) end
  if phase == "intro" or phase == "wait" then
    if emu:read32(0x03005D60) == ACTION and d > mark + 60 then
      menu = menu + 1
      foeMoves()
      if menu == 1 then
        if E("STATUS") then emu:write32(MONS + 0x4C, tonumber(E("STATUS"))); emu:write32(PARTY + 0x50, tonumber(E("STATUS"))) end
        if E("WEATHER") then emu:write16(0x020243CC, tonumber(E("WEATHER"))) end
      end
      if E("SEED") then emu:write32(0x03005D80, tonumber(E("SEED")) + menu) end
      w(string.format("menu %d: ours %s", menu, bat(0)))
      w(string.format("        foe  %s", bat(1)))
      w(string.format("        weather %04X field %08X party status %08X / %08X", emu:read16(0x020243CC), field(),
        emu:read32(PARTY + 0x50), emu:read32(PARTY + 100 + 0x50)))
      if menu > TURNS then finish("turns done"); return end
      chosen = OURMOVE[menu] or 0
      phase = (E("RUN") == "1") and "run" or ((tonumber(E("SWITCH") or "0") == menu) and "switch" or "choose"); mark = d
    elseif (d - mark) % 30 == 0 then tap(phase == "intro" and K.A or K.B) end
    if cb2() ~= BATTLE and phase == "wait" and d > mark + 200 then
      finish(string.format("the battle ended: outcome %d", emu:read8(0x0202433A))); return
    end
    if d > mark + 5000 then shot(NAME .. "_stuck"); finish("STUCK in " .. phase .. " (FAIL)") end
  end
  if phase == "choose" then
    if d == mark + 8 and menu == 1 and E("HP") then   -- (written at the menu itself it is put back to full: the
      local hp = emu:read16(MONS + 0x2C) * tonumber(E("HP")) // 100                -- engine refreshes it there)
      emu:write16(MONS + 0x28, hp); emu:write16(PARTY + 0x56, hp); lasthp[0] = hp
      w(string.format("  menu 1 +8: our HP set to %d", hp))
    end
    if d == mark + 10 then tap(K.A) end
    if d == mark + 45 then tap(K.UP) end
    if d == mark + 60 then tap(K.LEFT) end
    if d == mark + 75 and chosen % 2 == 1 then tap(K.RIGHT) end
    if d == mark + 90 and chosen >= 2 then tap(K.DOWN) end
    if d == mark + 110 then tap(K.A) end
    if d == mark + 130 then phase = "wait"; mark = d end
  elseif phase == "switch" then
    if d == mark + 10 then tap(K.DOWN) end
    if d == mark + 25 then tap(K.LEFT) end
    if d == mark + 40 then tap(K.A) end
    if d == mark + 160 then tap(K.DOWN) end
    if d == mark + 200 then tap(K.A) end
    if d == mark + 260 then tap(K.A) end
    if d == mark + 300 then phase = "wait"; mark = d end
  elseif phase == "run" then
    if d == mark + 10 then tap(K.DOWN) end
    if d == mark + 25 then tap(K.RIGHT) end
    if d == mark + 40 then tap(K.A) end
    if d == mark + 60 then phase = "wait"; mark = d end
  end
end
