-- Sky Pillar summit: Zinnia's scene and the Rayquaza battle, end to end, on a save that already finished it.
-- Set: 0x1C0 clear (the scene runs again), 0x50 cleared by the map's own transition script (VAR 0x40CA >= 2),
-- the 3rd Meteorite (item 690, Items pocket) in the Bag; warp next to the trigger (12,11) on 24/85 and step onto it.
-- MODE = "catch" (a Master Ball from the battle Bag), "ko" (knock it out: the script gives Rayquaza anyway),
-- "run" (run first: "must face Rayquaza!" and the battle again, then ko). Outside battle: B moves text on and says
-- No to the nickname prompts. MODE = "lose": the lead at 1 HP, the rest fainted, the foe kept alive - a blackout must
-- leave the event to do again. Screenshots sp_NNN.png every 45 frames; the result in skypillar_log.txt.
-- Run next to game.gba/game.sav copies with DIR (output) and HERE (this folder) set.
NAME = "skypillar"
DIR = DIR or "./"
HERE = HERE or DIR
MODE = MODE or "catch"
dofile(HERE .. "../../patches/dexnavchain/test_boot.lua")
local SCRIPT = 0x0203F100
local function sb1() return emu:read32(0x03005D8C) end
local function sb2() return emu:read32(0x03005D90) end
local function flagbyte(f)
  if f < 0x4000 then return sb1() + 0x1270 + (f >> 3) end
  local i = (f - 0x4000) >> 3
  if i <= 0x33 then return sb1() + 0x988 + i end
  if i <= 0x67 then return sb1() + 0x3B24 + i - 0x34 end
  if i <= 0x9B then return sb2() + 0x5C + i - 0x68 end
  return sb2() + 0x28 + i - 0x9C
end
local function setflag(f, on)
  local a = flagbyte(f); local b = emu:read8(a)
  if on then b = b | (1 << (f & 7)) else b = b & ~(1 << (f & 7)) & 0xFF end
  emu:write8(a, b)
end
local function flag(f) return (emu:read8(flagbyte(f)) >> (f & 7)) & 1 end
local function var(v) return emu:read16(sb1() + 0x139C + (v - 0x4000) * 2) end
local function setvar(v, x) emu:write16(sb1() + 0x139C + (v - 0x4000) * 2, x) end
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1); emu:write8(0x03000E38, 0)
end
local function key() return emu:read32(sb2() + 0xAC) & 0xFFFF end
local function pocket(i) return emu:read32(0x02039DD8 + 8 * i), emu:read8(0x02039DD8 + 8 * i + 4) end
local function count_item(id)
  local n = 0
  for p = 0, 4 do
    local base, cap = pocket(p)
    for s = 0, cap - 1 do if emu:read16(base + 4 * s) == id then n = n + (emu:read16(base + 4 * s + 2) ~ key()) end end
  end
  return n
end
local function give_item(p, id, qty)
  local base, cap = pocket(p)
  for s = 0, cap - 1 do
    if emu:read16(base + 4 * s) == 0 or emu:read16(base + 4 * s) == id then
      emu:write16(base + 4 * s, id); emu:write16(base + 4 * s + 2, qty ~ key()); return
    end
  end
end
local RAYQUAZA = 406
local function count_species(sp)
  local n = 0
  for i = 0, emu:read8(0x020244E9) - 1 do if emu:read16(0x020244EC + 100 * i + 0x20) == sp then n = n + 1 end end
  local st = emu:read32(0x03005D94)
  for b = 0, 13 do for s = 0, 29 do
    if emu:read16(st + 4 + (b * 30 + s) * 80 + 0x20) == sp then n = n + 1 end
  end end
  return n
end
local function state(tag)
  local pl = 0x02037350
  w(string.format("%-12s map %d/%d (%d,%d) cb2 %08X lock %d | 1C0=%d 50=%d 8C1=%d 4001=%d 40D7=%d | item690 %d item648 %d | Rayquaza %d | outcome %d",
    tag, emu:read8(sb1() + 4), emu:read8(sb1() + 5), emu:read16(pl + 0x10) - 7, emu:read16(pl + 0x12) - 7, cb2(), lock(),
    flag(0x1C0), flag(0x50), flag(0x8C1), var(0x4001), var(0x40D7), count_item(690), count_item(648),
    count_species(RAYQUAZA), emu:read8(0x0202433A)))
end

local t0, phase, calm, shots, battles, ran, last = nil, "setup", 0, 0, 0, false, 0
local before = {}
function TEST(f)
  t0 = t0 or f
  local d = f - t0
  if phase == "setup" then
    setflag(0x1C0, false); setflag(0x50, false); setvar(0x4001, 0)
    if var(0x40CA) < 2 then setvar(0x40CA, 2) end
    if count_item(690) == 0 then give_item(0, 690, 1) end   -- the 3rd Meteorite: an Items-pocket item
    before.r = count_species(RAYQUAZA); before.i690 = count_item(690); before.i648 = count_item(648)
    state("before")
    run({0x39, 24, 85, 0xFF, 12, 0, 12, 0, 0x02})                 -- warp: summit, one below the trigger
    phase = "warping"; last = d
  elseif phase == "warping" then
    if d - last > 60 and cb2() == OVERWORLD and lock() == 0 then
      calm = calm + 1
      if calm > 60 then state("at summit"); shot("sp_000_summit"); tap(K.UP, 24); phase = "scene"; last = d; calm = 0 end
    else calm = 0 end
  elseif phase == "scene" then
    if (d - last) % 45 == 0 and shots < 200 then shots = shots + 1; shot(string.format("sp_%03d", shots)) end
    if d - last == 200 and lock() == 0 and cb2() == OVERWORLD then state("NOT STARTED"); shot("sp_notstarted"); phase = "done"; done(); return end
    if cb2() ~= OVERWORLD then                                      -- the battle, its Bag, its transitions
      if not inb then inb = true; battles = battles + 1; w("battle " .. battles .. " starts at d=" .. d) end
      if cb2() == BATTLE and emu:read32(0x03005D60) == 0x08057589 then   -- the action menu
        if MODE == "run" and not ran then
          ran = true; tap(K.DOWN); last_act = d
        elseif MODE == "catch" then
          if not threw then
            threw = true
            local bb = pocket(1); emu:write16(bb, 1); emu:write16(bb + 2, 1 ~ key())   -- a Master Ball first
            emu:write8(0x0203CE58 + 5, 1); emu:write16(0x0203CE58 + 8 + 2, 0); emu:write16(0x0203CE58 + 0x12 + 2, 0)
            tap(K.RIGHT); bagstep = d
          end
        elseif MODE == "lose" then
          emu:write16(0x02024084 + 0x28, 1)                          -- our lead at 1 HP, the foe kept alive
          emu:write16(0x02024084 + 0x58 + 0x28, 500)
          for i = 1, emu:read8(0x020244E9) - 1 do emu:write16(0x020244EC + 100 * i + 0x56, 0) end
          if (d % 30) == 0 then tap(K.A) end
        else
          emu:write16(0x02024084 + 0x58 + 0x28, 1)                  -- the foe's HP to 1, then Fight, first move
          if (d % 30) == 0 then tap(K.A) end
        end
      end
      if MODE == "run" and ran and last_act and d == last_act + 20 then tap(K.RIGHT) end
      if MODE == "run" and ran and last_act and d == last_act + 40 then tap(K.A); w("chose Run") end
      if MODE == "catch" and bagstep then
        if d == bagstep + 20 then tap(K.A) end                      -- Bag
        if d == bagstep + 200 then shot("sp_bag"); tap(K.A) end      -- the Master Ball
        if d == bagstep + 260 then tap(K.A); w("threw the Master Ball") end   -- Use
      end
      if cb2() == BATTLE and not (MODE == "catch" and bagstep and d < bagstep + 300) and emu:read32(0x03005D60) ~= 0x08057589 and d % 20 == 0 then
        if MODE == "ko" or MODE == "lose" then tap(K.A) else tap(K.B) end              -- ko: through the move menu; else text, "No"
      end
    else
      if inb then inb = false; state("after battle " .. battles); if MODE == "run" and battles == 1 then MODE = "ko" end end
      if MODE == "lose" and battles > 0 and cb2() == OVERWORLD and lock() == 0 and not (emu:read8(sb1() + 4) == 24 and emu:read8(sb1() + 5) == 85) then
        calm = calm + 1
        if calm > 120 then state("after loss"); shot("sp_after_loss"); phase = "done"; done(); return end
      elseif cb2() == OVERWORLD and lock() == 0 and flag(0x1C0) == 1 then
        calm = calm + 1
        if calm > 120 then
          state("after")
          shot("sp_end")
          local ok = flag(0x1C0) == 1 and flag(0x50) == 1 and count_species(RAYQUAZA) == before.r + 1
                     and count_item(690) == before.i690 - 1 and count_item(648) == before.i648 + 1
          w(string.format("result: Rayquaza %d -> %d, item690 %d -> %d, item648 %d -> %d, battles %d: %s",
            before.r, count_species(RAYQUAZA), before.i690, count_item(690), before.i648, count_item(648), battles,
            ok and "PASS" or "CHECK"))
          phase = "done"; done(); return
        end
      else
        calm = 0
        if d % 20 == 0 then tap(K.B) end
      end
    end
    if d > 30000 then state("TIMEOUT"); shot("sp_timeout"); phase = "done"; done() end
  end
end
