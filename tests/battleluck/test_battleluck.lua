-- Is a battle's luck replayed from a saved moment? Language-independent: the foe's turn is read from RAM (its PP
-- went down = it acted; its HP went down without PP = it hurt itself in confusion; neither = fully paralysed).
-- A scripted battle (KIND=trainer with TRAINER id, or KIND=wild with SPECIES / LEVEL); the lead gets Glare, Confuse
-- Ray, Splash, Growl. STATUS=para: Glare on turn 1, then Splash. STATUS=conf: Confuse Ray every turn.
--   MODE=replay: at the move menu of turn REPLAY_TURN the state is saved; TRIALS times it is reloaded, a different
--                number of frames is waited, the same move is chosen, and the foe's turn is logged.
--   MODE=seq:    plays TURNS turns and logs the foe's turn each time, as one line (to compare two starts).
-- DELAY = frames to wait on the field before the battle starts (a different start of the same battle).
-- DIFF (var 0x409B) and GYM (flags 0x273 / 0x27F / 0x274) as in the gym scripts.
local E = os.getenv
NAME = E("TAG") or "rngtest"
dofile(HERE .. "../../patches/dexnavchain/test_boot.lua")
local MODE, STATUS, KIND = E("MODE") or "replay", E("STATUS") or "para", E("KIND") or "trainer"
local DIFF, GYM = tonumber(E("DIFF") or "1"), E("GYM") == "1"
local TRAINER, SPECIES, LEVEL = tonumber(E("TRAINER") or "265"), tonumber(E("SPECIES") or "143"), tonumber(E("LEVEL") or "50")
local REPLAY_TURN, TRIALS, TURNS = tonumber(E("REPLAY_TURN") or "3"), tonumber(E("TRIALS") or "16"), tonumber(E("TURNS") or "12")
local DELAY = tonumber(E("DELAY") or "5")
local SCRIPT, TEXT, MONS = 0x0203F100, 0x0203F180, 0x02024084
local ACTION, MOVE = 0x08057589, 0x08057BFD
local function sb1() return emu:read32(0x03005D8C) end
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1); emu:write8(0x03000E38, 0)
end
local function setflag(f, on)
  local a = sb1() + 0x1270 + (f >> 3)
  local b = emu:read8(a)
  if on then b = b | (1 << (f & 7)) else b = b & ~(1 << (f & 7)) & 0xFF end
  emu:write8(a, b)
end
local function ctrl() return emu:read32(0x03005D60) end
local function foe()                                  -- gBattleMons[1]: species, hp, the four PP, status1, status2
  local m = MONS + 0x58
  local pp = 0
  for i = 0, 3 do pp = pp + emu:read8(m + 0x24 + i) end
  return {sp = emu:read16(m), hp = emu:read16(m + 0x28), pp = pp, s1 = emu:read32(m + 0x4C), s2 = emu:read32(m + 0x50)}
end
local function outcome(a, b)
  if b.sp ~= a.sp then return "switched" end
  if b.pp < a.pp then return "acted" end
  if b.hp < a.hp then return "HURT ITSELF" end
  return "COULD NOT MOVE"
end
local t0, phase, mark, turn = nil, "start", nil, 0
local snap, trial, pre, idle, before, seq = nil, 0, nil, 0, nil, {}
function TEST(f)
  t0 = t0 or f
  local d = f - t0
  if d == DELAY then
    local va = sb1() + 0x139C + 0x9B * 2
    w(string.format("%s %s | %s | difficulty %d -> %d | gym flags %s | start delay %d", MODE, STATUS,
      KIND == "wild" and ("wild " .. SPECIES .. " Lv" .. LEVEL) or ("trainer " .. TRAINER), emu:read16(va), DIFF,
      tostring(GYM), DELAY))
    emu:write16(va, DIFF)
    for _, fl in ipairs({0x273, 0x27F, 0x274}) do setflag(fl, GYM) end
    local mon = 0x020244EC
    for i, m in ipairs({137, 109, 150, 45}) do emu:write16(mon + 0x2C + (i - 1) * 2, m); emu:write8(mon + 0x34 + i - 1, 60) end
    emu:write8(TEXT, 0xFF)
    if KIND == "wild" then run({0xB6, SPECIES & 0xFF, SPECIES >> 8, LEVEL, 0, 0, 0xB7, 0x02})
    else run({0x5C, 3, TRAINER & 0xFF, TRAINER >> 8, 0, 0, TEXT & 0xFF, (TEXT >> 8) & 0xFF, (TEXT >> 16) & 0xFF, TEXT >> 24, 0x02}) end
  end
  if d < DELAY + 30 or phase == "end" then return end
  local slot = (STATUS == "para") and ((turn == 1) and 0 or 2) or 1
  if phase == "start" or phase == "wait" then
    if cb2() == BATTLE and ctrl() == ACTION then
      if phase == "wait" and before then
        local o = outcome(before, foe())
        seq[#seq + 1] = (o == "acted") and "." or (o == "COULD NOT MOVE" and "P" or (o == "HURT ITSELF" and "H" or "s"))
      end
      phase = "action"; mark = d; turn = turn + 1; emu:write8(0x020244AC, 0)
      emu:write16(MONS + 0x28, emu:read16(MONS + 0x2C))   -- our lead back to full HP (trap damage would end the test)
      if MODE == "seq" and turn > TURNS then
        w("foe's turns (. acted, P could not move, H hurt itself): " .. table.concat(seq))
        phase = "end"; done(); return
      end
    elseif d % 20 == 0 then tap(K.B) end
    if cb2() == OVERWORLD and lock() == 0 and d > DELAY + 900 then w("battle over after turn " .. turn .. ": " .. table.concat(seq)); phase = "end"; done() end
  elseif phase == "action" then
    if d == mark + 12 then tap(K.A) end
    if ctrl() == MOVE then
      mark = d
      phase = (MODE == "replay" and turn == REPLAY_TURN) and "snap" or "move"
    end
  elseif phase == "move" then
    if d == mark + 6 then emu:write8(0x020244B0, slot); before = foe() end
    if d == mark + 10 then tap(K.A) end
    if d > mark + 14 and ctrl() ~= MOVE then phase = "wait" end
  elseif phase == "snap" then
    if d == mark + 20 then
      snap = emu:saveStateBuffer(); phase = "trial"; trial = 0; mark = nil
      local x = foe()
      w(string.format("saved at turn %d: foe species %d hp %d status1 %08X status2 %08X (paralysis = bit 6, confusion = low 3 bits)",
        turn, x.sp, x.hp, x.s1, x.s2))
    end
  elseif phase == "trial" then
    if not mark then
      if not pre then pre = d; emu:clearKey(K.A); emu:clearKey(K.B) end
      if d < pre + 12 then return end
      pre = nil
      trial = trial + 1
      if trial > TRIALS then phase = "end"; done(); return end
      emu:loadStateBuffer(snap)
      idle = 3 + (trial * 37) % 211
      mark = d
    end
    if d == mark + idle then emu:write8(0x020244B0, slot); before = foe() end
    if d == mark + idle + 4 then tap(K.A) end
    if d > mark + idle + 10 and ctrl() ~= MOVE then phase = "trialwait"; mark = d end
  elseif phase == "trialwait" then
    if d % 20 == 0 and ctrl() ~= ACTION then tap(K.B) end
    if (cb2() == BATTLE and ctrl() == ACTION and d > mark + 60) or d > mark + 6000 then
      w(string.format("trial %2d: waited %3d frames, main RNG %08X -> the foe %s", trial, idle, emu:read32(0x03005D80),
        outcome(before, foe())))
      phase = "trial"; mark = nil
    end
  end
  if mark and d > mark + 20000 and phase ~= "end" and phase ~= "trial" then      -- a stall: say where, and show it
    w(string.format("STALL in %s at turn %d: cb2 %08X ctrl %08X lock %d | so far %s", phase, turn, cb2(), ctrl(), lock(),
      table.concat(seq)))
    shot(NAME .. "_stall"); phase = "end"; done()
  end
  if d > 400000 and phase ~= "end" then w("TIMEOUT in " .. phase); phase = "end"; done() end
end
