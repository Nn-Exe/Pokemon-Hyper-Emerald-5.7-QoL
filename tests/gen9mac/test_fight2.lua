-- A new Pokemon fighting with its own moves (screenshots of every turn for looking at by eye).
--   MODE=own  SPECIES as our only Pokemon (givemon Lv 100: the moves it learns by then), against a wild Blissey Lv 100.
--             Turn k uses its k-th move, chosen on the move menu with the D-pad (its PP topped up); both
--             sides' HP held at the maximum every frame of the turn, so all four moves are used. The foe attacks, so abilities that answer a
--             hit get their chance.
--   MODE=foe  SPECIES as the wild one (Lv 70, its own moves) against our only Pokemon, a Blissey Lv 100 using
--             Splash; TURNS (4) turns, both held at full HP: the foe's AI picks its own moves.
-- START=k: begin with the k-th move (0-3), to go on past one that ends a wild battle. MOVES=a,b,c,d: our moves
-- instead of its own; SEED=n: the random seed at each menu (n + turn);
-- FOESPLASH=1: the foe only knows Splash. Each turn logs how often the foe's HP fell.
-- Logged at each menu: both battlers (species, HP, ability, moves and PP), so what was used shows as the PP that
-- went down; a turn that does not come back to the menu in 4000 frames is "STUCK". Shots: t<turn>_menu (the move
-- menu, the move highlighted), t<turn>_a / _b at 100 and 220 frames after it is chosen.
local E = os.getenv
DIR = E("GEN9_DIR")
local MODE = E("MODE") or "own"
NAME = (E("TAG") or "f2") .. "_" .. MODE
dofile("C:/Users/nonth/Desktop/Works & Productivity/gba-trans/hyper-emerald/hyper-emerald-en-qol/patches/dexnavchain/test_boot.lua")
local SPECIES, TURNS = tonumber(E("SPECIES")), tonumber(E("TURNS") or "4")
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
  return string.format("species %d hp %d/%d ability %d moves %d %d %d %d pp %d %d %d %d status %08X", emu:read16(m),
    emu:read16(m + 0x28), emu:read16(m + 0x2C), emu:read16(ABIL16 + 2 * i), emu:read16(m + 0x0C), emu:read16(m + 0x0E),
    emu:read16(m + 0x10), emu:read16(m + 0x12), emu:read8(m + 0x24), emu:read8(m + 0x25), emu:read8(m + 0x26),
    emu:read8(m + 0x27), emu:read32(m + 0x4C))
end
local own, hits = {}, 0
local t0, phase, mark, turn, chosen = nil, "setup", 0, 0, nil
local function finish(msg) w(msg); phase = "end"; done() end
function TEST(f)
  t0 = t0 or f
  local d = f - t0
  if phase == "end" then return end
  if d == 5 then
    emu:write8(0x020244E9, 5); for i = 500, 599 do emu:write8(PARTY + i, 0) end
    give(MODE == "own" and SPECIES or 242, 100)
  end
  if d == 40 then
    for i = 0, 99 do emu:write8(PARTY + i, emu:read8(PARTY + 500 + i)) end
    for i = 100, 599 do emu:write8(PARTY + i, 0) end
    emu:write8(0x020244E9, 1)
    local k = 0                                   -- MOVES=a,b,c,d: our Pokemon's moves instead (PP 20 each)
    for id in (E("MOVES") or ""):gmatch("%d+") do
      emu:write16(PARTY + 0x2C + 2 * k, tonumber(id)); emu:write8(PARTY + 0x34 + k, 20); k = k + 1
    end
    for k = 0, 3 do own[k] = emu:read16(PARTY + 0x2C + 2 * k) end
    w(string.format("ours: species %d lv %d moves %d %d %d %d", emu:read16(PARTY + 0x20), emu:read8(PARTY + 0x54),
      own[0], own[1], own[2], own[3]))
    run({0xB6, (MODE == "own" and 242 or SPECIES) & 0xFF, (MODE == "own" and 242 or SPECIES) >> 8,
         MODE == "own" and 100 or 70, 0, 0, 0xB7, 0x02})
  end
  if phase == "setup" and d > 50 and cb2() == BATTLE then phase = "intro"; mark = d end
  if phase == "setup" and d > 2000 then finish("the battle never started (FAIL)") end
  if phase == "intro" or phase == "wait" then
    if emu:read32(0x03005D60) == ACTION and d > mark + 60 then
      if turn > 0 then w(string.format("turn %d: the foe was hit %d time(s)", turn, hits)) end
      hits = 0
      if E("SEED") then emu:write32(0x03005D80, tonumber(E("SEED")) + turn) end
      if E("FOESPLASH") then                       -- the foe only knows Splash: every drop of its HP is our hit
        emu:write16(MONS + 0x58 + 0x0C, 150); emu:write8(MONS + 0x58 + 0x24, 40)
        for k = 1, 3 do emu:write16(MONS + 0x58 + 0x0C + 2 * k, 0) end
      end
      turn = turn + 1
      w(string.format("menu %d: ours %s", turn, bat(0))); w("        foe  " .. bat(1))
      if turn > TURNS then finish("all turns done (PASS)"); return end
      for i = 0, 1 do emu:write16(MONS + 0x58 * i + 0x28, emu:read16(MONS + 0x58 * i + 0x2C)) end
      local slot = (MODE == "own") and (turn - 1 + tonumber(E("START") or "0")) or 0
      if MODE == "own" and slot > 3 then finish("all its moves used (PASS)"); return end
      if MODE == "own" and own[slot] == 0 then finish("all its moves used (PASS)"); return end
      emu:write8(MONS + 0x24 + slot, 10)                      -- PP for the move about to be chosen
      chosen = slot; phase = "choose"; mark = d
    elseif phase == "intro" and (d - mark) % 30 == 0 then tap(K.A)
    elseif phase == "wait" and (d - mark) % 20 == 0 then tap(K.B) end    -- through the messages (B: no "yes")
    if cb2() ~= BATTLE and phase == "wait" and d > mark + 300 then
      local oc = emu:read8(0x0202433A)
      w("the battle ended: outcome " .. oc)
      if oc == 5 or oc == 10 then finish("ended by a move that ends a wild battle (Roar, Whirlwind, Circle Throw, Dragon Tail) - as it should (PASS)")
      else finish("the battle ended before all turns (check)") end
    end
    if d > mark + 4000 then shot(NAME .. "_stuck"); w("ours " .. bat(0)); w("foe  " .. bat(1)); finish("STUCK (FAIL)") end
  end
  if phase == "choose" or phase == "wait" then      -- nobody faints: both sides' HP held at the maximum every frame
    if emu:read16(MONS + 0x58 + 0x28) < emu:read16(MONS + 0x58 + 0x2C) then hits = hits + 1 end   -- each hit on the foe
    for i = 0, 1 do emu:write16(MONS + 0x58 * i + 0x28, emu:read16(MONS + 0x58 * i + 0x2C)) end
  end
  if phase == "choose" then
    if d == mark + 10 then tap(K.A) end                       -- Fight
    if d == mark + 45 then tap(K.UP) end                      -- the 2 x 2 move grid: to the first move, then
    if d == mark + 60 then tap(K.LEFT) end                    -- right for the 2nd / 4th, down for the 3rd / 4th
    if d == mark + 75 and chosen % 2 == 1 then tap(K.RIGHT) end
    if d == mark + 90 and chosen >= 2 then tap(K.DOWN) end
    if d == mark + 110 then shot(string.format("%s_t%d_menu", NAME, turn)); tap(K.A) end
    if d == mark + 210 then shot(string.format("%s_t%d_a", NAME, turn)) end
    if d == mark + 330 then shot(string.format("%s_t%d_b", NAME, turn)); phase = "wait"; mark = d end
  end
end
