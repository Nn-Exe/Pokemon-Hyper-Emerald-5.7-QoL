-- gen9abil's battles: one set up to make an ability act, every message of the battle logged as text.
-- (From tests/gen9mac/test_ability.lua: the same setup and keys, plus the messages, gen9abil's state, the foe's side.)
-- Ours: HOLDER (givemon Lv LV, default 50) with ABSLOT (0/1: the IV word's bit 31) and MOVES=a,b,c,d (PP 20);
--   ABIL=n: our battle ability (16-bit at 0x0203F000, and gBattleMons' byte) written at every menu instead (a hidden
--   ability, or a control run: ABIL=0); ITEM=held item; HP=percent of max HP at the first menu; STATUS=status1 at
--   the first menu; SECOND=a second party Pokemon (SECONDITEM, SECONDMOVES); SWITCH=k: at menu k switch to it;
--   OURMOVE=i,j,...: the move slot used at menu 1, 2, ... (default 0). STAGES=atk,def,spe,spa,spd: our stat stages
--   (6 neutral) at the first menu.
-- Foe: FOE (wild, Lv FOELV, default 50) knowing only FOEMOVES (written at each menu, PP 20); FOEABIL like ABIL;
--   FOEITEM; FOESTATUS; FOEHP percent. TRAINER=id: that trainer instead of a wild one (FOE... then apply to its lead).
-- SEED=n: the random numbers set to n before the Pokemon are made and to n + menu at each menu; PINRNG=1 holds them
-- there through the turn. WEATHER=n (gBattleWeather), TERRAIN=e (the field word's electric terrain turns), at the
-- first menu, or from the battle's first frames with EARLY=1.
-- TURNS (default 3). Logged: every battle message ("msg"), at each menu both battlers (HP, ability, stages,
-- status, item), the weather, the field word, gen9abil's state; every change of HP. Shots: SHOTS=1, every 30 frames.
local E = os.getenv
DIR = E("G9_DIR")
NAME = (E("TAG") or "g9") .. "_g9a"
dofile("C:/Users/nonth/Desktop/Works & Productivity/gba-trans/hyper-emerald/hyper-emerald-en-qol/patches/dexnavchain/test_boot.lua")
local function list(s) local t = {}; for n in (s or ""):gmatch("%-?%d+") do t[#t + 1] = tonumber(n) end; return t end
local HOLDER, LV, FOE, FOELV = tonumber(E("HOLDER")), tonumber(E("LV") or "50"), tonumber(E("FOE") or "143"), tonumber(E("FOELV") or "50")
local MOVES, FOEMOVES, OURMOVE = list(E("MOVES")), list(E("FOEMOVES")), list(E("OURMOVE"))
local TURNS = tonumber(E("TURNS") or "3")
local ABIL = E("ABIL") and tonumber(E("ABIL"))
local FOEABIL = E("FOEABIL") and tonumber(E("FOEABIL"))
local SCRIPT, PARTY, MONS, ACTION, ABIL16 = 0x0203F100, 0x020244EC, 0x02024084, 0x08057589, 0x0203F000
local MSG = 0x02022E2C                          -- gDisplayedStringBattle
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1); emu:write8(0x03000E38, 0)
end
local function give(sp, lv) run({0x79, sp & 0xFF, sp >> 8, lv, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0x02}) end
local function nbs() return emu:read32(0x02024218) end
local function field() local p = nbs(); return p ~= 0 and emu:read32(p + 0xD4) or 0 end
local function g9state()
  local p = nbs()
  if p == 0 then return "-" end
  local t = {}
  for k = 0, 15 do t[#t + 1] = string.format("%02X", emu:read8(p + 0x118 + k)) end
  return table.concat(t, " ")
end
local function bat(i)
  local m = MONS + 0x58 * i
  local st = {}
  for k = 0, 7 do st[#st + 1] = emu:read8(m + 0x18 + k) end
  return string.format("species %d hp %d/%d ability %d (byte %d) stages %s status %08X status2 %08X item %d", emu:read16(m),
    emu:read16(m + 0x28), emu:read16(m + 0x2C), emu:read16(ABIL16 + 2 * i), emu:read8(m + 0x20), table.concat(st, ","),
    emu:read32(m + 0x4C), emu:read32(m + 0x50), emu:read16(m + 0x2E))
end

-- the game's text, back to letters
local CH = {[0x00] = " ", [0xAB] = "!", [0xAC] = "?", [0xAD] = ".", [0xAE] = "-", [0xB0] = "...", [0xB1] = '"',
  [0xB2] = '"', [0xB3] = "'", [0xB4] = "'", [0xB8] = ",", [0xBA] = "/", [0xF0] = ":", [0x1B] = "e", [0x5C] = "+"}
for k = 0, 9 do CH[0xA1 + k] = tostring(k) end
for k = 0, 25 do CH[0xBB + k] = string.char(65 + k); CH[0xD5 + k] = string.char(97 + k) end
local function decode(a)
  local s = {}
  for k = 0, 200 do
    local b = emu:read8(a + k)
    if b == 0xFF then break end
    if b == 0xFE or b == 0xFA or b == 0xFB then s[#s + 1] = " / "
    elseif b == 0xFC then s[#s + 1] = "{FC}"
    else s[#s + 1] = CH[b] or string.format("{%02X}", b) end
  end
  return table.concat(s)
end
local lastMsg = ""
local function inAction()                       -- an action menu is up: ours, or our second battler's
  return emu:read32(0x03005D60) == ACTION or emu:read32(0x03005D68) == ACTION
end
-- BREAKS=addr,addr,...: each time the code reaches one, its registers are logged (BREAKMAX each, default 20)
local brk = {}
for a in (E("BREAKS") or ""):gmatch("%x+") do
  local at = tonumber(a, 16)
  brk[at] = 0
  emu:setBreakpoint(function()
    brk[at] = brk[at] + 1
    if brk[at] <= tonumber(E("BREAKMAX") or "20") then
      local mem = {}
      for spec in (E("BREAKMEM") or ""):gmatch("[^,]+") do       -- addr:bytes, read at the break
        local a, n = spec:match("(%x+):(%d+)")
        local hex = {}
        for k = 0, tonumber(n) - 1 do hex[#hex + 1] = string.format("%02X", emu:read8(tonumber(a, 16) + k)) end
        mem[#mem + 1] = a .. "=" .. table.concat(hex)
      end
      w(string.format("  break %08X: r0 %X r1 %X r2 %X r3 %X lr %08X %s", at, emu:readRegister("r0"), emu:readRegister("r1"),
        emu:readRegister("r2"), emu:readRegister("r3"), emu:readRegister("lr"), table.concat(mem, " ")))
    end
  end, at)
end
-- READWATCH=lo-hi (hex, hi exclusive): every read of those bytes, its pc and lr logged (BREAKMAX at most, default 20)
local rw = 0
for lo, hi in (E("READWATCH") or ""):gmatch("(%x+)-(%x+)") do
  emu:setRangeWatchpoint(function()
    rw = rw + 1
    if rw <= tonumber(E("BREAKMAX") or "20") then
      w(string.format("  read %s-%s: pc %08X lr %08X r0 %X r1 %X r2 %X r3 %X", lo, hi, emu:readRegister("pc"),
        emu:readRegister("lr"), emu:readRegister("r0"), emu:readRegister("r1"), emu:readRegister("r2"), emu:readRegister("r3")))
    end
  end, tonumber(lo, 16), tonumber(hi, 16), C.WATCHPOINT_TYPE.READ)
end

local t0, phase, mark, menu, chosen, shots, lasthp = nil, "setup", 0, 0, 0, 0, {}
local function finish(msg) w(msg); phase = "end"; done() end
local function setAbil()
  if ABIL then emu:write16(ABIL16, ABIL); emu:write8(MONS + 0x20, ABIL & 0xFF) end
  if FOEABIL then emu:write16(ABIL16 + 2, FOEABIL); emu:write8(MONS + 0x58 + 0x20, FOEABIL & 0xFF) end
end
local function foeMoves()
  if #FOEMOVES == 0 then return end
  for k = 0, 3 do
    emu:write16(MONS + 0x58 + 0x0C + 2 * k, FOEMOVES[k + 1] or 0); emu:write8(MONS + 0x58 + 0x24 + k, FOEMOVES[k + 1] and 20 or 0)
  end
end
local function setField()
  if E("WEATHER") then emu:write16(0x020243CC, tonumber(E("WEATHER"))) end
  if E("TERRAIN") and nbs() ~= 0 then
    local fw = nbs() + 0xD4
    emu:write32(fw, (emu:read32(fw) & ~0x1E000) | (tonumber(E("TERRAIN")) << 13))
  end
end
function TEST(f)
  t0 = t0 or f
  local d = f - t0
  if phase == "end" then return end
  if E("SEED") and (d == 2 or d == 59) then emu:write32(0x03005D80, tonumber(E("SEED"))) end
  if d == 2 then emu:write8(0x020244E9, 0); for i = 0, 599 do emu:write8(PARTY + i, 0) end; give(HOLDER, LV) end
  if d == 30 and E("SECOND") then give(tonumber(E("SECOND")), tonumber(E("LV2") or tostring(LV))) end
  if d == 60 then
    local iv = emu:read32(PARTY + 0x48)
    if E("ABSLOT") == "1" then iv = iv | 0x80000000 else iv = iv & 0x7FFFFFFF end
    emu:write32(PARTY + 0x48, iv)
    for k = 0, 3 do emu:write16(PARTY + 0x2C + 2 * k, MOVES[k + 1] or 0); emu:write8(PARTY + 0x34 + k, MOVES[k + 1] and 20 or 0) end
    if E("ITEM") then emu:write16(PARTY + 0x22, tonumber(E("ITEM"))) end
    if E("SECOND") then
      local sm = list(E("SECONDMOVES"))
      for k = 0, 3 do if sm[k + 1] then emu:write16(PARTY + 100 + 0x2C + 2 * k, sm[k + 1]); emu:write8(PARTY + 100 + 0x34 + k, 20) end end
      if E("SECONDITEM") then emu:write16(PARTY + 100 + 0x22, tonumber(E("SECONDITEM"))) end
      if E("ABSLOT2") == "1" then emu:write32(PARTY + 100 + 0x48, emu:read32(PARTY + 100 + 0x48) | 0x80000000) end
      if E("SECONDHP") then                      -- the second Pokemon's HP, percent of its max, before the battle
        emu:write16(PARTY + 100 + 0x56, emu:read16(PARTY + 100 + 0x58) * tonumber(E("SECONDHP")) // 100)
      end
    end
    w(string.format("party: %d %d (count %d), ours ability slot %s", emu:read16(PARTY + 0x20), emu:read16(PARTY + 100 + 0x20),
      emu:read8(0x020244E9), E("ABSLOT") or "0"))
    if E("TRAINER") then
      local t = tonumber(E("TRAINER"))
      run({0x5C, 3, t & 0xFF, t >> 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0x02})        -- trainerbattle (no intro text)
    else
      run({0xB6, FOE & 0xFF, FOE >> 8, FOELV, 0, 0, 0xB7, 0x02})
    end
  end
  if phase == "setup" and d > 70 and cb2() == BATTLE then phase = "intro"; mark = d end
  if phase == "setup" and d > 2000 then finish("the battle never started (FAIL)") end
  if phase ~= "setup" and cb2() == BATTLE then
    setAbil()
    if E("ALLYSTAGES") and phase == "intro" and menu == 0 then    -- our second battler's stat stages, at entry
      local st = list(E("ALLYSTAGES"))
      for k = 1, #st do emu:write8(MONS + 0x58 * 2 + 0x18 + k, st[k]) end
    end
    if E("EARLY") == "1" and phase == "intro" and d > mark + 2 and d < mark + 40 then
      setField()
      if E("FOEITEM") then emu:write16(MONS + 0x58 + 0x2E, tonumber(E("FOEITEM"))) end
    end
    if E("PINRNG") and E("SEED") and phase == "wait" then emu:write32(0x03005D80, tonumber(E("SEED")) + menu) end
    local m = decode(MSG)
    if m ~= lastMsg then
      if m ~= "" then w(string.format("  msg (menu %d +%d): %s", menu, d - mark, m)) end
      lastMsg = m
    end
    for i = 0, 3 do                             -- every change of HP
      local hp = emu:read16(MONS + 0x58 * i + 0x28)
      if lasthp[i] and hp ~= lasthp[i] and emu:read16(MONS + 0x58 * i) ~= 0 then
        w(string.format("  menu %d +%d: battler %d hp %d -> %d (%+d)", menu, d - mark, i, lasthp[i], hp, hp - lasthp[i]))
      end
      lasthp[i] = hp
    end
  end
  -- SHOTS=1: a picture every 30 frames; SHOTS=n (n > 1): every n frames while the turn plays (SHOTMAX, 80)
  -- SHOTANIM=lo-hi (hex): only while the animation script pointer (0x020383F0) is in lo..hi, or was within the
  -- last 400 frames (a script of the game's that one of ours calls)
  if E("FINDPTR") and phase == "wait" and d % 4 == 0 and not foundPtr then   -- which RAM word points into lo..hi
    local lo, hi = E("FINDPTR"):match("(%x+)-(%x+)")
    for a = 0x02020000, 0x0203FFFC, 4 do
      local v = emu:read32(a)
      if v >= tonumber(lo, 16) and v < tonumber(hi, 16) then
        w(string.format("  FINDPTR %08X = %08X", a, v)); foundPtr = true
      end
    end
  end
  local every = tonumber(E("SHOTS") or "0")
  local inanim = true
  if E("SHOTANIM") then
    local lo, hi = E("SHOTANIM"):match("(%x+)-(%x+)")
    local p = emu:read32(0x020383F0)
    if p >= tonumber(lo, 16) and p < tonumber(hi, 16) then lastAnim = d end
    inanim = lastAnim ~= nil and d - lastAnim < 400 and p >= 0x08000000
  end
  local intro = E("SHOTINTRO") and phase == "intro"         -- SHOTINTRO=1: the battle's intro too
  if every > 0 and (menu > 0 or intro) and inanim and (every == 1 or phase == "wait" or intro) and
     d % (every == 1 and 30 or every) == 0 and
     shots < tonumber(E("SHOTMAX") or "80") then
    shots = shots + 1; shot(string.format("%s_%03d", NAME, shots))
  end
  if phase == "intro" or phase == "wait" then
    if inAction() and d > mark + 60 then
      menu = menu + 1
      foeMoves()
      if menu == 1 then
        if E("STATUS") then emu:write32(MONS + 0x4C, tonumber(E("STATUS"))); emu:write32(PARTY + 0x50, tonumber(E("STATUS"))) end
        if E("FOESTATUS") then emu:write32(MONS + 0x58 + 0x4C, tonumber(E("FOESTATUS"))) end
        if E("FOEITEM") then emu:write16(MONS + 0x58 + 0x2E, tonumber(E("FOEITEM"))) end
        if E("FOEHP") then emu:write16(MONS + 0x58 + 0x28, emu:read16(MONS + 0x58 + 0x2C) * tonumber(E("FOEHP")) // 100) end
        local st = list(E("STAGES"))
        for k = 1, #st do emu:write8(MONS + 0x18 + k, st[k]) end
        if E("EARLY") ~= "1" then setField() end
      end
      if E("SEED") then emu:write32(0x03005D80, tonumber(E("SEED")) + menu) end
      w(string.format("menu %d: ours %s", menu, bat(0)))
      w(string.format("        foe  %s", bat(1)))
      if emu:read8(0x0202406C) > 2 then
        w(string.format("        ally %s", bat(2)))
        w(string.format("        foe2 %s", bat(3)))
      end
      w(string.format("        weather %04X field %08X | g9 %s", emu:read16(0x020243CC), field(), g9state()))
      if menu > TURNS then finish("turns done"); return end
      chosen = OURMOVE[menu] or 0
      phase = ((tonumber(E("SWITCH") or "0") == menu) and "switch" or "choose"); mark = d
    elseif (d - mark) % 30 == 0 and not inAction() then   -- (B at a double battle's second
      tap(phase == "intro" and K.A or K.B)                                   -- action menu takes the first back)
    end
    if cb2() ~= BATTLE and phase == "wait" and d > mark + 200 then
      finish(string.format("the battle ended: outcome %d", emu:read8(0x0202433A))); return
    end
    if d > mark + 5000 then shot(NAME .. "_stuck"); finish("STUCK in " .. phase .. " (FAIL)") end
  end
  if (phase == "choose" or phase == "switch") and d == mark + 6 and menu == 1 and E("FAINTED") then
    emu:write8(0x03005D10, tonumber(E("FAINTED")))     -- gBattleResults: how many of ours have fainted
    w(string.format("  menu 1 +6: our fainted count set to %s", E("FAINTED")))
  end
  if phase == "choose" then
    if d == mark + 8 and menu == 1 and E("HP") then
      local hp = emu:read16(MONS + 0x2C) * tonumber(E("HP")) // 100
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
  end
end
