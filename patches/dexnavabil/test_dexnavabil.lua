-- The DexNav bar names the ability the hunted Pokemon really has. On Route 102, for each species in CASES:
--   1. the slot roll: reroll() 40 times (a `callnative` script). A species with one ability must always get slot
--      0; one with two different abilities must get both slots;
--   2. the bar: with each slot the species has, the name on the bar's second line must be the name of
--      table[species][slot] (0x097A0000, what GetAbilityBySpecies reads). Screenshot dexnavabil_<species>_<slot>.png;
--   3. the Pokemon: the patch is put next to the player, the step starts the hunted battle, and the foe must be
--      that species, with that slot bit, and the battle engine's own ability for it (16 bits, 0x0203F000 +
--      2 * battler) must be the one the bar named. Then run.
-- Cases: Corvisquire (the bar said "-------"; Keen Eye / Unnerve), Bulbasaur (it said Blaze one time in two;
-- Overgrow only), Riolu (Protean; Steadfast / Inner Focus), Tirtouga and Krabby (ids past 255: Solid Rock 333,
-- Shell Armor 260), Charmander (Blaze, right before too).
-- Every case starts from a warp to (9, 6) and steps up: on the save this was written with, (10, 6) starts a script
-- and (7, 3) is a door, and either takes the step away from the hunt. So does any script the game starts on a step
-- (they run before the encounter check): the first step after loading that save is "The Repel ended... Use
-- another?", taken and answered No before the cases, and a case whose step goes that way is done again.
-- On a ROM without the patch this fails on every case but Charmander. The log is dexnavabil_log.txt, last line PASS.
NAME = NAME or "dexnavabil"
dofile(BOOT or ((DIR or "./") .. "../dexnavchain/test_boot.lua"))
local ST, SCRIPT, REROLL, TABLE = 0x0203A660, 0x0203F100, 0x08FDE961, 0x097A0000
local CASES = {1123, 1, 500, 617, 98, 4}
local CH = {[0x00] = " ", [0xAD] = ".", [0xAE] = "-", [0xB4] = "'"}
for i = 0, 25 do CH[0xBB + i] = string.char(65 + i); CH[0xD5 + i] = string.char(97 + i) end
for i = 0, 9 do CH[0xA1 + i] = tostring(i) end
local function text(a, n)
  local s = ""
  for k = 0, n - 1 do
    local c = emu:read8(a + k)
    if c == 0xFF then break end
    s = s .. (CH[c] or "?")
  end
  return s
end
local function sb1() return emu:read32(0x03005D8C) end
local function ability(sp, slot) return emu:read16(TABLE + 6 * sp + 2 * slot) end
local function abilityname(id) return text(emu:read32(0x080001C0) + 13 * id, 13) end
local function pxy() local o = 0x02037350 + emu:read8(0x02037595) * 0x24; return emu:read16(o + 0x10), emu:read16(o + 0x12) end
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1)
  emu:write8(0x03000E38, 0)
end
local function wait(n) for _ = 1, n do coroutine.yield() end end
local fails = 0
local function check(ok, msg)
  if not ok then fails = fails + 1 end
  w((ok and "   ok    " or "   FAIL  ") .. msg)
end

-- what arm_search does, without the DexNav screen: this species, level 20, this map, a land hunt, no chain
local function arm(sp, slot)
  emu:write8(ST + 9, 0); wait(6)                          -- the tick takes the old bar down
  emu:write16(ST + 2, sp); emu:write16(ST + 4, 0); emu:write16(ST + 24, 0)
  emu:write8(ST + 15, 20); emu:write8(ST + 16, 20)
  emu:write8(ST + 10, emu:read8(sb1() + 4)); emu:write8(ST + 11, emu:read8(sb1() + 5))
  emu:write16(0x03005D30, 0)
  if slot then emu:write8(ST + 7, slot) end
  emu:write8(ST + 9, 1)
end

-- the patch on a tile next to the player, then a step onto it; true once the battle is up
local function hunt()
  for _, d in ipairs({{K.UP, 0, -1}, {K.LEFT, -1, 0}, {K.RIGHT, 1, 0}, {K.DOWN, 0, 1}}) do
    local x, y = pxy()
    if emu:read8(ST + 9) & 8 == 0 then emu:write8(ST + 30, 4); emu:write8(ST + 9, emu:read8(ST + 9) | 8) end
    emu:write8(ST + 28, x + d[2]); emu:write8(ST + 29, y + d[3]); emu:write8(ST + 31, 0)
    wait(10); tap(d[1], 24); wait(50)
    local nx, ny = pxy()
    w(string.format("         step: (%d,%d) -> (%d,%d), lock %d flags %02X", x, y, nx, ny, lock(), emu:read8(ST + 9)))
    if nx == x + d[2] and ny == y + d[3] then
      if emu:read8(ST + 9) & 8 ~= 0 then return false end       -- on the patch, and the patch is still there
      for _ = 1, 600 do
        if cb2() == BATTLE then return true end
        coroutine.yield()
      end
      return false
    end
  end
  return false
end

local function flee()
  for i = 0, 6000 do
    if cb2() == OVERWORLD then break end
    local q = i % 90
    if q == 0 then tap(K.DOWN) elseif q == 20 then tap(K.RIGHT) elseif q == 40 then tap(K.A) end
    coroutine.yield()
  end
  for i = 1, 240 do
    if lock() ~= 0 and i % 30 == 0 then tap(K.B) end
    coroutine.yield()
  end
  return cb2() == OVERWORLD and lock() == 0
end

-- a script of the game's own has the field: B until it lets go
local function clear()
  for i = 1, 1800 do
    if lock() == 0 then return end
    if i % 30 == 0 then tap(K.B) end
    coroutine.yield()
  end
end

local function place()
  emu:write8(ST + 9, 0); wait(6)
  run({0x39, 0, 17, 0xFF, 9, 0, 6, 0, 0x02}); wait(390)                   -- Route 102
end

local co = coroutine.create(function()
  place(); tap(K.UP, 24); wait(90); clear()                -- the first step: see the header
  for _, sp in ipairs(CASES) do
    local a0, a1 = ability(sp, 0), ability(sp, 1)
    local two = a1 ~= 0 and a1 ~= a0
    place()
    w(string.format("species %d: %s (%d) / %s (%d), base-stats bytes %d / %d; map %d/%d", sp, abilityname(a0), a0, abilityname(a1), a1,
      emu:read8(emu:read32(0x080001BC) + 28 * sp + 22), emu:read8(emu:read32(0x080001BC) + 28 * sp + 23),
      emu:read8(sb1() + 4), emu:read8(sb1() + 5)))
    arm(sp)
    local n = {[0] = 0, [1] = 0}
    for _ = 1, 40 do
      run({0x23, REROLL & 0xFF, (REROLL >> 8) & 0xFF, (REROLL >> 16) & 0xFF, REROLL >> 24, 0x02}); wait(3)
      local s = emu:read8(ST + 7)
      n[s] = (n[s] or 0) + 1
    end
    if two then check(n[0] > 0 and n[1] > 0 and n[0] + n[1] == 40, string.format("40 rolls: slot 0 %d times, slot 1 %d times", n[0], n[1]))
    else check(n[0] == 40, string.format("40 rolls: slot 0 %d times (one ability)", n[0])) end
    for slot = 0, two and 1 or 0 do
      local id = ability(sp, slot)
      local up = false
      for try = 1, 3 do
        if slot > 0 or try > 1 then place() end
        arm(sp, slot); wait(40)
        if try == 1 then
          local shown = text(ST + 32 + 64, 16)
          check(emu:read8(ST + 14) ~= 0xFF and shown == abilityname(id), string.format("slot %d: the bar says '%s', the table '%s' (%d)", slot, shown, abilityname(id), id))
          shot(string.format("%s_%d_%d", NAME, sp, slot))
        end
        up = hunt()
        if up then break end
        w("         the step went to another script; again"); shot(NAME .. "_taken"); clear()
      end
      if up then
        wait(420)
        local foe = 0x02024744
        local fsp, fslot, engine = emu:read16(foe + 0x20), emu:read32(foe + 0x48) >> 31, emu:read16(0x0203F002)
        check(fsp == sp and fslot == slot and engine == id, string.format(
          "slot %d: the foe is species %d lv %d, slot bit %d, the engine's ability %d '%s' (low byte %d; ours %d)", slot, fsp,
          emu:read8(foe + 0x54), fslot, engine, abilityname(engine), emu:read8(0x02024084 + 0x58 + 0x20), emu:read16(0x0203F000)))
        check(flee(), "back on the field")
      else
        check(false, "no hunted battle: flags " .. string.format("%02X", emu:read8(ST + 9)))
      end
    end
  end
  emu:write8(ST + 9, 0); wait(10)
  w(fails == 0 and "PASS" or ("FAILED: " .. fails))
  done()
end)

function TEST(f)
  if coroutine.status(co) == "dead" then return end
  local ok, err = coroutine.resume(co)
  if not ok then w("error: " .. tostring(err)); done() end
end
