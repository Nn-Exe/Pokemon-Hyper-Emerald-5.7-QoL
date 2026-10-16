-- Breeding, as the game does it: PARENT (Lv 50, made by givemon) and Ditto in the Day Care (SaveBlock1 + 0x3030, two
-- 0x8C slots: the BoxPokemon, then steps at +0x88; offspring personality +0x118, the step counter +0x11C), then the
-- player walks on Route 117. Before each step the second parent's step count is set to 0xFE, so every step makes
-- the game's own roll (TryProduceOrHatchEgg: GetDaycareCompatibilityScore against Random) - an incompatible pair
-- never gets an egg. With one waiting: the Day-Care Man's own script (0/32 object 2 at 47,4: run as if talked to,
-- the warped-in player's A does not reach him), yes; the Egg must be party slot
-- 6. Then its egg cycles (friendship, +0x29) to 0 and the step counter to 254: one step hatches it, B through the
-- scene (no nickname). Logged: the egg (species, moves), the hatched Pokemon; screenshots of the Egg's summary-free
-- life: the party icon is not shown, but the hatch scene is (every 60 frames).
-- Env: PARENT=species, WANT=the species the Egg must be (0: no Egg must come), STEPS=how many rolls to allow (40).
-- EGGMOVE=move: the parent knows it (its first move) before it goes in; the Egg must know it (an egg move passed on).
local E = os.getenv
DIR = E("GEN9_DIR")
NAME = (E("TAG") or "br") .. "_breed"
dofile("C:/Users/nonth/Desktop/Works & Productivity/gba-trans/hyper-emerald-en-qol/patches/dexnavchain/test_boot.lua")
local PARENT, WANT, STEPS = tonumber(E("PARENT")), tonumber(E("WANT") or "0"), tonumber(E("STEPS") or "40")
local SCRIPT, PARTY = 0x0203F100, 0x020244EC
local function sb1() return emu:read32(0x03005D8C) end
local function dc() return sb1() + 0x3030 end
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1); emu:write8(0x03000E38, 0)
end
local function give(sp, lv) run({0x79, sp & 0xFF, sp >> 8, lv, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0x02}) end
local function emptySixth()
  emu:write8(0x020244E9, 5)
  for i = 0, 99 do emu:write8(PARTY + 500 + i, 0) end
end
local function toDaycare(slot)                   -- party slot 6's BoxPokemon into a Day Care slot
  local dst = dc() + slot * 0x8C
  for i = 0, 0x8B do emu:write8(dst + i, 0) end
  for i = 0, 0x4F do emu:write8(dst + i, emu:read8(PARTY + 500 + i)) end
end
local function mon(m)
  return string.format("species %d lv %d egg %d cycles %d moves %d %d %d %d", emu:read16(m + 0x20), emu:read8(m + 0x54),
    (emu:read32(m + 0x48) >> 30) & 1, emu:read8(m + 0x29), emu:read16(m + 0x2C), emu:read16(m + 0x2E), emu:read16(m + 0x30),
    emu:read16(m + 0x32))
end
local t0, phase, mark, rolls, dir, shots = nil, "setup", 0, 0, 0, 0
local settled, talked, hatching
local function finish(msg) w(msg); phase = "end"; done() end
function TEST(f)
  t0 = t0 or f
  local d = f - t0
  if phase == "end" then return end
  if d == 2 then run({0x29, 0x3E, 0x43, 0x02}) end   -- 0x433E: the Oval Charm already given (else his first talk is that)
  if d == 5 then emptySixth(); give(PARENT, 50) end
  if d == 40 and E("EGGMOVE") then emu:write16(PARTY + 500 + 0x2C, tonumber(E("EGGMOVE"))) end
  if d == 40 then toDaycare(0); w("parent 1: " .. mon(dc())); emptySixth(); give(132, 50) end
  if d == 80 then
    toDaycare(1); w("parent 2: " .. mon(dc() + 0x8C)); emptySixth()
    emu:write32(dc() + 0x118, 0); emu:write8(dc() + 0x11C, 0)
    run({0x39, 0, 32, 0xFF, 47, 0, 7, 0, 0x02})                -- Route 117, below the fence
  end
  if phase == "setup" and d > 400 and cb2() == OVERWORLD and lock() == 0 then phase = "walk"; mark = d end
  if phase == "walk" then
    if emu:read32(dc() + 0x118) ~= 0 then
      w(string.format("an Egg is waiting after %d roll(s) (personality %08X)", rolls, emu:read32(dc() + 0x118)))
      phase = "fetch"; mark = d
      run({0x39, 0, 32, 0xFF, 47, 0, 5, 0, 0x02})              -- in the fence's gap, below the man
    elseif rolls >= STEPS then
      shot(NAME .. "_noegg")
      finish(string.format("no Egg after %d rolls%s", rolls, WANT == 0 and " - as it must be (PASS)" or " (FAIL)"))
    else
      local s = dc() + 0x8C + 0x88
      if emu:read32(s) & 0xFF ~= 0xFE then rolls = rolls + 1 end
      emu:write32(s, (emu:read32(s) & 0xFFFFFF00) | 0xFE)
      if (d - mark) % 20 == 0 then
        dir = 1 - dir
        tap(dir == 1 and K.RIGHT or K.LEFT, 14)
      end
    end
  end
  if phase == "fetch" then                        -- the warp done and the field free: face him, A, yes to the Egg
    if not settled and d > mark + 120 and cb2() == OVERWORLD and lock() == 0 then settled = d end
    if settled and d == settled + 20 then tap(K.UP, 3) end
    if settled and d == settled + 60 then                -- his own script (object 2, local 3: 0x08291C18)
      local a = 0x08291C18
      run({0x16, 0x0F, 0x80, 3, 0, 0x05, a & 0xFF, (a >> 8) & 0xFF, (a >> 16) & 0xFF, a >> 24})
    end
    if settled and d > settled + 60 and (d - settled) % 30 == 0 and d < settled + 2400 then tap(K.A) end
    if settled and d == settled + 200 then shot(NAME .. "_man") end
    if settled and lock() ~= 0 then talked = true end
    if talked and cb2() == OVERWORLD and lock() == 0 then
      local count = emu:read8(0x020244E9)
      local m = PARTY + 100 * (count - 1)
      w("party count " .. count .. " | last: " .. mon(m))
      local egg = (emu:read32(m + 0x48) >> 30) & 1
      if egg ~= 1 then shot(NAME .. "_noeggreceived"); finish("no Egg in the party (FAIL)"); return end
      w(string.format("the Egg is species %d (want %d) %s", emu:read16(m + 0x20), WANT, emu:read16(m + 0x20) == WANT and "PASS" or "FAIL"))
      if E("EGGMOVE") then
        local em, has = tonumber(E("EGGMOVE")), false
        for k = 0, 3 do if emu:read16(m + 0x2C + 2 * k) == em then has = true end end
        w(string.format("egg move %d: %s", em, has and "the Egg knows it (PASS)" or "the Egg does not know it"))
      end
      emu:write8(m + 0x29, 0); emu:write8(dc() + 0x11C, 254)
      phase = "hatch"; mark = d; settled = nil
      run({0x39, 0, 32, 0xFF, 47, 0, 7, 0, 0x02})
    end
    if d > mark + 3000 then shot(NAME .. "_stuck"); finish("the Day-Care Man never finished (FAIL)") end
  end
  if phase == "hatch" then
    if not settled and d > mark + 120 and cb2() == OVERWORLD and lock() == 0 then settled = d end
    if settled and d == settled + 20 then tap(K.RIGHT, 14) end
    if settled and d == settled + 60 then tap(K.LEFT, 14) end
    if settled and d > settled + 100 then
      if (d - mark) % 60 == 0 and shots < 30 then shots = shots + 1; shot(string.format("%s_hatch_%02d", NAME, shots)) end
      if (d - mark) % 24 == 0 then tap(K.B) end
      if lock() ~= 0 then hatching = true end
      if hatching and cb2() == OVERWORLD and lock() == 0 then
        local count = emu:read8(0x020244E9)
        local m = PARTY + 100 * (count - 1)
        w("hatched: " .. mon(m))
        local ok = emu:read16(m + 0x20) == WANT and ((emu:read32(m + 0x48) >> 30) & 1) == 0
        shot(NAME .. "_after")
        finish(ok and "hatched into the right Pokemon (PASS)" or "did not hatch right (FAIL)")
      end
      if d > mark + 6000 then shot(NAME .. "_stuck"); finish("the hatching never finished (FAIL)") end
    end
  end
  if d > 20000 and phase ~= "end" then finish("timed out in " .. phase .. " (FAIL)") end
end
