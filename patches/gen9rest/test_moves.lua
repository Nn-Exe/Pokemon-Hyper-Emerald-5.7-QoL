-- One new move, used once: Snorlax (Lv 100, ATK=species) against a wild Chansey (Lv 100) that only knows Splash. Logged at the
-- action menu before and after the turn: both sides' HP, stat stages, status, ability; the turn must come back
-- to the menu (or the battle end) - a move that hangs the game shows up as "stuck".
-- MOVE=id; FOE=species (113); TURNS=n (1): the same move n times (charge and recharge moves need two)
local E = os.getenv
DIR = E("GEN9_DIR")
local TAG = E("TAG") or "mt"
NAME = TAG .. "_move"
dofile("C:/Users/nonth/Desktop/Works & Productivity/gba-trans/hyper-emerald-en-qol/patches/dexnavchain/test_boot.lua")
local MOVE, FOE, TURNS = tonumber(E("MOVE")), tonumber(E("FOE") or "113"), tonumber(E("TURNS") or "1")
local ATK = tonumber(E("ATK") or "143")                -- Snorlax (Mew does not obey: not from the event)
local SCRIPT, MONS, PARTY = 0x0203F100, 0x02024084, 0x020244EC
local ACTION = 0x08057589
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1); emu:write8(0x03000E38, 0)
end
local function side(i)
  local m = MONS + 0x58 * i
  local st = {}
  for k = 0, 7 do st[#st + 1] = emu:read8(m + 0x18 + k) - 6 end
  return string.format("hp %d/%d stages %s status1 %X status2 %X ability16 %d types %d/%d moves %d %d pp %d", emu:read16(m + 0x28),
    emu:read16(m + 0x2C), table.concat(st, ","), emu:read32(m + 0x4C), emu:read32(m + 0x50),
    emu:read16(0x0203F000 + 2 * i), emu:read8(m + 0x21), emu:read8(m + 0x22), emu:read16(m + 0x0C), emu:read16(m + 0x0E),
    emu:read8(m + 0x24))
end
local t0, phase, mark, turn = nil, "start", 0, 0
function TEST(f)
  t0 = t0 or f
  local d = f - t0
  if phase == "end" then return end
  if d == 5 then
    emu:write8(0x020244E9, 5)
    for i = 0, 99 do emu:write8(PARTY + 500 + i, 0) end
    run({0x79, ATK & 0xFF, ATK >> 8, 100, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0x02})
  end
  if d == 60 then
    for i = 0, 99 do emu:write8(PARTY + i, emu:read8(PARTY + 500 + i)) end
    for k = 0, 3 do emu:write16(PARTY + 0x2C + 2 * k, k == 0 and MOVE or 0); emu:write8(PARTY + 0x34 + k, k == 0 and 30 or 0) end
    emu:write32(0x03005D80, 305419896)
    run({0xB6, FOE & 0xFF, FOE >> 8, 100, 0, 0, 0xB7, 0x02})
  end
  if phase == "start" and d > 70 and emu:read32(0x030022C4) == BATTLE then phase = "intro"; mark = d end
  if phase == "intro" then
    if emu:read32(0x03005D60) == ACTION and d > mark + 200 then
      local foe = MONS + 0x58
      for k = 0, 3 do emu:write16(foe + 0x0C + 2 * k, k == 0 and 150 or 0); emu:write8(foe + 0x24 + k, k == 0 and 40 or 0) end
      w("move " .. MOVE .. " | before: us " .. side(0)); w("            foe " .. side(1))
      phase = "turn"; mark = d; turn = 1
    elseif d % 30 == 0 then tap(K.A) end
    if d > mark + 3000 then w("stuck before the menu"); phase = "end"; done() end
  elseif phase == "turn" then
    if d < mark + 300 and d % 20 == 0 then tap(K.A) end           -- Fight, the first move
    if d >= mark + 300 and d % 30 == 0 then tap(K.A) end          -- through the messages
    if E("SHOTS") and (d - mark) % 30 == 0 and d - mark <= 600 then shot(string.format("%s_%d_%03d", NAME, turn, d - mark)) end
    if d > mark + 320 and emu:read32(0x03005D60) == ACTION then
      w(string.format("after turn %d: us %s", turn, side(0))); w("             foe " .. side(1))
      if turn >= TURNS then w("TURN DONE"); phase = "end"; done()
      else turn = turn + 1; mark = d end
    elseif emu:read32(0x030022C4) ~= BATTLE and d > mark + 320 then
      w("the battle ended: outcome " .. emu:read8(0x0202433A)); w("TURN DONE"); phase = "end"; done()
    end
    if d > mark + 4000 then shot(NAME .. "_stuck"); w("STUCK in turn " .. turn); phase = "end"; done() end
  end
end
