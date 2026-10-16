-- The new moves' texts, for looking at by eye: does each fit its box?
--   MOVES=a,b,c,d: the only party Pokemon (SPECIES, default Mew 151, Lv 50) knows these four.
--   MODE=summary: START -> POKEMON -> A -> Summary -> the Battle Moves page; A on the first move, then DOWN:
--                 the description of each (s_m<k>.png), B out.
--   MODE=battle:  a wild Blissey; Fight; for each move: the cursor on it, L held (lmoveinfo's panel: name, Power,
--                 Accuracy, kind, contact, priority, effect chance) - b_m<k>.png - and let go.
local E = os.getenv
DIR = E("GEN9_DIR")
local MODE = E("MODE") or "summary"
NAME = (E("TAG") or "mt") .. "_" .. MODE
dofile("C:/Users/nonth/Desktop/Works & Productivity/gba-trans/hyper-emerald-en-qol/patches/dexnavchain/test_boot.lua")
local MOVES = {}
for n in (E("MOVES") or ""):gmatch("%d+") do MOVES[#MOVES + 1] = tonumber(n) end
local SPECIES = tonumber(E("SPECIES") or "151")
local SCRIPT, PARTY, ACTION = 0x0203F100, 0x020244EC, 0x08057589
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1); emu:write8(0x03000E38, 0)
end
local function give(sp, lv) run({0x79, sp & 0xFF, sp >> 8, lv, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0x02}) end
local plan, t0 = {}, nil
local function at(d, fn) plan[#plan + 1] = {d, fn} end
local function key(t, k, len) at(t, function() tap(k, len) end) end
local function snap(t, n) at(t, function() shot(NAME .. "_" .. n) end) end
at(2, function() emu:write8(0x020244E9, 0); for i = 0, 599 do emu:write8(PARTY + i, 0) end; give(SPECIES, 50) end)
at(40, function()
  for k = 0, 3 do emu:write16(PARTY + 0x2C + 2 * k, MOVES[k + 1] or 0); emu:write8(PARTY + 0x34 + k, MOVES[k + 1] and 10 or 0) end
  w(string.format("ours: species %d moves %d %d %d %d", emu:read16(PARTY + 0x20), emu:read16(PARTY + 0x2C),
    emu:read16(PARTY + 0x2E), emu:read16(PARTY + 0x30), emu:read16(PARTY + 0x32)))
  emu:write8(0x03000F2C, 0)
end)
if MODE == "summary" then
  local T = 60
  key(T, K.START); key(T + 60, K.DOWN); key(T + 90, K.A)          -- POKEMON (the menu's cursor sits on Pokedex)
  key(T + 340, K.A); key(T + 420, K.A)                            -- the only Pokemon, Summary
  key(T + 680, K.RIGHT); key(T + 780, K.RIGHT)                    -- Skills, Battle Moves
  snap(T + 880, "page")
  key(T + 890, K.A)
  local t = T + 960
  for k = 1, #MOVES do
    snap(t, "m" .. k)
    if k < #MOVES then key(t + 10, K.DOWN) end
    t = t + 50
  end
  key(t, K.B); key(t + 60, K.B); key(t + 160, K.B); key(t + 260, K.B); key(t + 360, K.B)
  at(t + 600, function() w(string.format("back: cb2 %08X lock %d", cb2(), lock())); done() end)
else
  local phase, mark, k = "start", 0, 0
  at(50, function() run({0xB6, 242 & 0xFF, 0, 50, 0, 0, 0xB7, 0x02}) end)
  function BATTLE_STEP(d)
    if phase == "start" and d > 60 and cb2() == BATTLE then phase = "intro"; mark = d end
    if phase == "intro" then
      if emu:read32(0x03005D60) == ACTION and d > mark + 200 then phase = "menu"; mark = d
      elseif (d - mark) % 30 == 0 then tap(K.A) end
    elseif phase == "menu" then
      if d == mark + 20 then tap(K.A) end                         -- Fight
      if d == mark + 60 then tap(K.UP) end
      if d == mark + 75 then tap(K.LEFT) end
      if d == mark + 100 then phase = "moves"; mark = d; k = 1 end
    elseif phase == "moves" then
      local base = mark + (k - 1) * 120
      if d == base and k == 2 then tap(K.RIGHT) end
      if d == base and k == 3 then tap(K.LEFT) end
      if d == base + 10 and k == 3 then tap(K.DOWN) end
      if d == base and k == 4 then tap(K.RIGHT) end
      if d == base + 20 then emu:addKey(K.L) end
      if d == base + 70 then shot(string.format("%s_m%d", NAME, k)) end
      if d == base + 80 then emu:clearKey(K.L) end
      if d == base + 119 then
        k = k + 1
        if k > #MOVES then phase = "end"; w("all panels taken"); done() end
      end
    end
    if d > 6000 and phase ~= "end" then shot(NAME .. "_stuck"); w("stuck in " .. phase); phase = "end"; done() end
  end
end
function TEST(f)
  t0 = t0 or f
  local d = f - t0
  for _, p in ipairs(plan) do if d == p[1] then p[2]() end end
  if BATTLE_STEP then BATTLE_STEP(d) end
end
