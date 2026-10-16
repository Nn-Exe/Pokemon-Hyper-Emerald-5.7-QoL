-- Tests for gen9rest (a copy of gen9's test_gen9.lua; what differs: the Pokedex flags of numbers 960 and up are
-- read and set in gen9rest's area of the save stream, EXT 0x0203DA00: a marker, 32 bytes seen, 32 caught).
-- Tests for speciesx + gen9: the new species (slots 1200-1237) in the places a species shows up.
-- Run muted next to copies of the ROM and a late-game save, in a folder under _testrun (not %TEMP%):
--   mGBA --script test_gen9.lua -C mute=1 -C fpsTarget=2000 -C audioSync=0 -C videoSync=0 rom.gba
-- Environment: GEN9_DIR (where logs and screenshots go, with a trailing slash), TAG, MODE, and per mode:
--   battle  SPECIES LEVEL [LEAD=1] [SEED=n]  scripted wild battle; both battlers' data read back at the
--                                   action menu (LEAD=1: our lead is made the same species first, for the back
--                                   picture; SEED: the random numbers the wild one is made from, so that the
--                                   same run on the ROM before the patches must log the same lines)
--                                   SHINY=1: the wild one is made shiny as the battle starts
--   fight   SPECIES LEVEL [LEAD=1] [MOVE=id]  the same battle, then Fight + A until it is over; party read back
--   catch   SPECIES LEVEL           the wild one at 1 HP, a ball with R, A until the field is back
--   give    SPECIES LEVEL           givemon into the sixth slot; party, summary pages
--   evolve  SPECIES LEVEL TARGET    givemon as the lead, one experience point short of LEVEL + 1; a win, the
--                                   evolution scene, and the lead must be TARGET
--   dex     FIRST LAST              numbers FIRST..LAST marked caught; the list's end and every entry's page
--   tm      SPECIES                 givemon as the lead, Bag (TM pocket) -> Use: the ABLE / NOT ABLE screen
--   damage  SPECIES LEVEL MOVE FOE FOELV [SUN=1] [TERRAIN=1] [EARLY=1] [ITEM=id] [SEED=n]
--                                   givemon as the lead with MOVE first, a wild FOE; the random numbers are set
--                                   to SEED at the menu, then Fight + the first move: the damage each side takes
--                                   is logged. The same run on a --no-effects build is the control. The sun
--                                   or terrain is set at the menu; EARLY=1 sets it from the battle's first
--                                   frames, before the engine first asks for a speed (Booster Energy cares).
--   duel    SPECIES LEVEL MOVE FOE FOELV [MOVE2=id] [ITEM=id] [FOEMOVE=id] [FOEFAST=n] [TURNS=n] [SUN=1]
--           [TERRAIN=1] [SEED=n]    like damage, but the foe is awake and answers (with FOEMOVE only, when
--                                   given; FOEFAST makes its Speed ours + n). Each turn: who was hit first, what
--                                   each side took, the lead's item, and every change of gen9.s's state bytes.
--                                   From the second turn on the lead uses MOVE2 when there is one.
--                                   SHOTS=n: a screenshot every n frames of the first turn (the animation).
--                                   LATEITEM=id: the lead is handed that item at the second turn's menu.
--                                   TRAINER=id: against that trainer instead of a wild FOE (its AI thinks
--                                   ahead, a wild Pokemon's does not). SPECIES2 [LEVEL2] [ITEM2]: a second
--                                   Pokemon of ours; SWITCH=1: the first turn switches to it.
--   damage and duel: SUPPRESS=1 (the lead's ability suppressed, as by Gastro Acid), FOEITEM=id (the foe's item)
--   double  SPECIES LEVEL SPECIES2 [LEVEL2] [TRAINER=56] [MOVE] [MOVE2] [ITEM] [ITEM2] [TURNS=2] [SEED]
--                                   two of ours in front against one of the game's double-battle trainers
--                                   (56: Gabby & Ty, level 60): every hit, the items, gen9.s's state bytes
--   give    ... [MOVES=a,b,c,d]     the given Pokemon's moves, and the summary's move page with each selected
--   bag     ITEM [COUNT]            additem (not with COUNT=0), then the Items pocket scrolled to its end:
--                                   the last item's picture and text
--   pc      BOX                     the storage screen on that box (for a save that has the new species there)
--   save / check                    givemon + save through the menu / a fresh start reads party, PC and flags
local E = os.getenv
DIR = E("GEN9_DIR") or "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/_testrun/gen9/"
local MODE, TAG = E("MODE") or "battle", E("TAG") or "g9"
NAME = TAG .. "_" .. MODE
dofile(E("GEN9_BOOT") or "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/hyper-emerald-en-qol/patches/dexnavchain/test_boot.lua")
local SPECIES, LEVEL = tonumber(E("SPECIES") or "1221"), tonumber(E("LEVEL") or "70")
local SCRIPT, MONS, PARTY, ENEMY = 0x0203F100, 0x02024084, 0x020244EC, 0x02024744
local ACTION, ABIL16 = 0x08057589, 0x0203F000
local NAMES = emu:read32(0x08000144)
local function sb1() return emu:read32(0x03005D8C) end
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1); emu:write8(0x03000E38, 0)
end
local function wild(sp, lv) run({0xB6, sp & 0xFF, sp >> 8, lv, 0, 0, 0xB7, 0x02}) end
local function give(sp, lv) run({0x79, sp & 0xFF, sp >> 8, lv, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0x02}) end
local function emptySixth()
  emu:write8(0x020244E9, 5)
  for i = 0, 99 do emu:write8(PARTY + 500 + i, 0) end
end
local function becomeSpecies(sp)                 -- the lead's species and nickname, in place
  emu:write16(PARTY + 0x20, sp)
  for i = 0, 9 do emu:write8(PARTY + 0x08 + i, emu:read8(NAMES + 11 * sp + i)) end
end
local function sixthToLead()
  for i = 0, 99 do emu:write8(PARTY + i, emu:read8(PARTY + 500 + i)) end
end
local function partyMon(i)
  local m = PARTY + 100 * i
  return string.format("species %d item %d lv %d exp %d hp %d/%d atk %d def %d spe %d spa %d spd %d moves %d %d %d %d",
    emu:read16(m + 0x20), emu:read16(m + 0x22), emu:read8(m + 0x54), emu:read32(m + 0x24), emu:read16(m + 0x56), emu:read16(m + 0x58),
    emu:read16(m + 0x5A), emu:read16(m + 0x5C), emu:read16(m + 0x5E), emu:read16(m + 0x60), emu:read16(m + 0x62),
    emu:read16(m + 0x2C), emu:read16(m + 0x2E), emu:read16(m + 0x30), emu:read16(m + 0x32))
end
local function battler(i)
  local m = MONS + 0x58 * i
  return string.format("battler %d: species %d lv %d hp %d/%d atk %d def %d spe %d spa %d spd %d types %d/%d item %d ability8 %d ability16 %d",
    i, emu:read16(m), emu:read8(m + 0x2A), emu:read16(m + 0x28), emu:read16(m + 0x2C), emu:read16(m + 2),
    emu:read16(m + 4), emu:read16(m + 6), emu:read16(m + 8), emu:read16(m + 10), emu:read8(m + 0x21),
    emu:read8(m + 0x22), emu:read16(m + 0x2E), emu:read8(m + 0x20), emu:read16(ABIL16 + 2 * i))
end
local function field()
  return string.format("weather %04X field %08X", emu:read16(0x020243CC), emu:read32(emu:read32(0x02024218) + 0xD4))
end
local function cryPlaying(sp)                    -- is the species' own cry sample in the sound engine's RAM?
  local cid = (sp - 1 <= 250) and (sp - 1) or emu:read16(0x08F4FA10 + 2 * (sp - 277))
  local wav = emu:read32(0x08F484E0 + 12 * cid + 4)
  local pat = string.char(wav & 0xFF, (wav >> 8) & 0xFF, (wav >> 16) & 0xFF, (wav >> 24) & 0xFF)
  return emu:readRange(0x03000000, 0x8000):find(pat, 1, true) ~= nil, cid, wav
end
local function pcSpecies(lo, hi)
  local st, found = emu:read32(0x03005D94), {}
  for slot = 0, 14 * 30 - 1 do
    local sp = emu:read16(st + 4 + slot * 80 + 0x20)
    if sp >= lo and sp <= hi then found[#found + 1] = sp .. "@" .. (slot // 30 + 1) .. "/" .. (slot % 30 + 1) end
  end
  return table.concat(found, " ")
end
local EXT, MAGIC = 0x0203DA00, 0x39584544
local function dexFlag(n, caught)
  if n >= 960 then
    if emu:read32(EXT) ~= MAGIC then return false end
    return emu:read8(EXT + 4 + (caught and 32 or 0) + ((n - 960) >> 3)) & (1 << (n & 7)) ~= 0
  end
  return emu:read8(sb1() + (caught and 0x5D8 or 0x560) + (n >> 3)) & (1 << (n & 7)) ~= 0
end
local function dexSet(n)                          -- seen and caught, as the game's routine would set them
  if n >= 960 then
    if emu:read32(EXT) ~= MAGIC then
      for i = 4, 67 do emu:write8(EXT + i, 0) end
      emu:write32(EXT, MAGIC)
    end
    for _, base in ipairs({EXT + 4, EXT + 36}) do
      emu:write8(base + ((n - 960) >> 3), emu:read8(base + ((n - 960) >> 3)) | (1 << (n & 7)))
    end
    return
  end
  for _, base in ipairs({sb1() + 0x560, sb1() + 0x5D8}) do
    emu:write8(base + (n >> 3), emu:read8(base + (n >> 3)) | (1 << (n & 7)))
  end
end
local function finish(msg) w(msg); phase = "end"; done() end

local STATE = 0x0203F130                         -- gen9.s: +0..3 Booster Energy used, +4..7 Glaive Rush's mark
local function stateBytes()
  local t = {}
  for i = 0, 7 do t[#t + 1] = emu:read8(STATE + i) end
  return string.format("booster %d %d %d %d | glaive %d %d %d %d", table.unpack(t))
end
local function setField()                         -- SUN=1: harsh sunlight; TERRAIN=1: Electric Terrain
  if E("SUN") == "1" then emu:write16(0x020243CC, 0x0040) end
  if E("TERRAIN") == "1" and emu:read32(0x02024218) ~= 0 then
    local fw = emu:read32(0x02024218) + 0xD4
    emu:write32(fw, emu:read32(fw) | 0xA000)
  end
end
local function tweak()                            -- at the first menu: SUPPRESS=1 the lead's ability is suppressed
  if E("SUPPRESS") == "1" then                     -- (the bit Gastro Acid sets); FOEITEM=id the foe holds that item
    local at = emu:read32(0x02024218) + 2
    emu:write8(at, emu:read8(at) | 0x40)
  end
  if E("FOEITEM") then emu:write16(MONS + 0x58 + 0x2E, tonumber(E("FOEITEM"))) end
end
local t0, mark, cry = nil, nil, false
local hp0, hp1, dealt, dealtAt, taken, throws, nextThrow
local turn, takenAt, lastState, turnMark, chose
phase = "start"
function TEST(f)
  t0 = t0 or f
  local d = f - t0
  if phase == "end" then return end

  if MODE == "battle" or MODE == "fight" or MODE == "catch" then
    if d == 5 then
      if E("LEAD") == "1" then becomeSpecies(SPECIES) end
      if E("MOVE") then emu:write16(PARTY + 0x2C, tonumber(E("MOVE"))); emu:write8(PARTY + 0x34, 40) end
      w("before: lead " .. partyMon(0))
      if E("SEED") then emu:write32(0x03005D80, tonumber(E("SEED"))) end   -- the same wild Pokemon every run
      wild(SPECIES, LEVEL)
    end
    if phase == "start" and d > 10 and cb2() == BATTLE then
      phase = "intro"; mark = d
      if E("SHINY") == "1" then                              -- a personality that is shiny for this trainer id,
        local pid, otid = emu:read32(ENEMY), emu:read32(ENEMY + 4)      -- in the same class modulo 24
        local want = ((otid >> 16) ~ (otid & 0xFFFF)) & 0xFFFF
        for lo = 0, 0xFFFF do
          local cand = (want ~ lo) * 0x10000 + lo
          if cand % 24 == pid % 24 then emu:write32(ENEMY, cand); break end
        end
        w(string.format("made shiny: personality %08X -> %08X", pid, emu:read32(ENEMY)))
      end
    end
    if phase == "start" and d > 1500 then shot(NAME .. "_nobattle"); finish("the battle never started") end
    if phase ~= "start" and not cry and cryPlaying(SPECIES) then
      local _, cid, wav = cryPlaying(SPECIES)
      cry = true; w(string.format("cry id %d wave %08X heard by the sound engine at +%d", cid, wav, d - mark))
    end
    if phase == "intro" then
      if emu:read32(0x03005D60) == ACTION and d > mark + 200 then phase = "menu"; mark = d
      elseif d % 30 == 0 then tap(K.A) end
      if d > mark + 3000 then shot(NAME .. "_stuck"); finish("no action menu") end
    elseif phase == "menu" then
      if d == mark + 40 then
        shot(NAME)
        w(battler(0)); w(battler(1)); w(field())
        if not cry then w("the cry sample was NOT seen in the sound engine") end
        if MODE == "battle" then finish("battle pass over")
        elseif MODE == "catch" then emu:write16(MONS + 0x58 + 0x28, 1); phase = "throw"; mark = d
        else phase = "fighting"; mark = d end
      end
    elseif phase == "throw" then
      -- R at the action menu throws the first ball of the pocket; it can break free, so again each time
      -- the menu is back (the wild one is kept at 1 HP and asleep)
      if emu:read32(0x03005D60) == ACTION and d >= (nextThrow or 0) then
        emu:write16(MONS + 0x58 + 0x28, 1); emu:write32(MONS + 0x58 + 0x4C, 7)
        tap(K.R, 4); throws = (throws or 0) + 1; nextThrow = d + 90
      elseif d > mark + 60 and d % 24 == 0 then tap(K.B) end -- B: no nickname, and through the messages
      if d > mark + 200 and cb2() == OVERWORLD and lock() == 0 then
        w("balls thrown " .. tostring(throws) .. " | outcome " .. emu:read8(0x0202433A) .. " | party count " .. emu:read8(0x020244E9) .. " | in the PC: " .. pcSpecies(SPECIES, SPECIES))
        for i = 0, 5 do if emu:read16(PARTY + 100 * i + 0x20) == SPECIES then w("in the party, slot " .. (i + 1) .. ": " .. partyMon(i)) end end
        local n = tonumber(E("DEXNO") or "0")
        if n > 0 then w("dex " .. n .. " seen " .. tostring(dexFlag(n, false)) .. " caught " .. tostring(dexFlag(n, true))) end
        finish("catch pass over")
      end
      if d > mark + 20000 then shot(NAME .. "_stuck"); finish("the catch never finished, balls thrown " .. tostring(throws)) end
    elseif phase == "fighting" then
      if d % 20 == 0 then tap(K.A) end                       -- Fight, first move, and through every message
      if d == mark + 400 then shot(NAME .. "_turn") end
      if d > mark + 200 and cb2() == OVERWORLD and lock() == 0 then
        w("outcome " .. emu:read8(0x0202433A)); w("after: lead " .. partyMon(0))
        finish("fight pass over")
      end
      if d > mark + 12000 then shot(NAME .. "_stuck"); w(battler(0)); w(battler(1)); finish("the fight never finished") end
    end

  elseif MODE == "give" then
    if d == 5 then emptySixth(); give(SPECIES, LEVEL) end
    if d == 60 then
      w("party count " .. emu:read8(0x020244E9) .. " | slot 6: " .. partyMon(5)); emu:write8(0x03000F2C, 0)
      local k = 0
      for id in (E("MOVES") or ""):gmatch("%d+") do
        emu:write16(PARTY + 500 + 0x2C + 2 * k, tonumber(id))
        emu:write8(PARTY + 500 + 0x34 + k, emu:read8(0x09D86419 + 12 * tonumber(id) + 4)); k = k + 1
      end
      if k > 0 then w("moves set | slot 6: " .. partyMon(5)) end
    end
    if d == 80 then tap(K.START) end
    if d == 140 then tap(K.DOWN) end
    if d == 170 then tap(K.A) end
    for k = 0, 4 do if d == 300 + k * 16 then tap(K.DOWN) end end
    if d == 420 then shot(NAME .. "_party") end
    if d == 430 then tap(K.A) end
    if d == 480 then tap(K.A) end
    if d == 640 then shot(NAME .. "_1") end
    if d == 650 then tap(K.RIGHT) end
    if d == 730 then shot(NAME .. "_2") end
    if d == 740 then tap(K.RIGHT) end
    if d == 820 then shot(NAME .. "_3") end
    if not E("MOVES") then
      if d == 830 then finish("give pass over") end
    else                                                     -- A: into the moves, each one's description in turn
      if d == 830 then tap(K.A) end
      for k = 0, 3 do
        if d == 900 + k * 60 then shot(NAME .. "_move" .. (k + 1)) end
        if d == 910 + k * 60 then tap(K.DOWN) end
      end
      if d == 1140 then finish("give pass over") end
    end

  elseif MODE == "evolve" then
    local TARGET = tonumber(E("TARGET") or "0")
    if d == 5 then emptySixth(); give(SPECIES, LEVEL) end
    if d == 60 then
      sixthToLead()
      local nxt = LEVEL + 1
      emu:write32(PARTY + 0x24, (5 * nxt * nxt * nxt) // 4 - 1)       -- the Slow group: one point short
      emu:write16(PARTY + 0x2C, 33); emu:write8(PARTY + 0x34, 35)     -- Tackle first: A, A must do damage
      w("before: lead " .. partyMon(0))
      wild(129, 14)                                                   -- a Magikarp that only knows Splash
    end
    if phase == "start" and d > 70 and cb2() == BATTLE then phase = "intro"; mark = d end
    if phase == "intro" and emu:read32(0x03005D60) == ACTION and d > mark + 200 then
      emu:write16(MONS + 0x58 + 0x28, 1); phase = "fighting"; mark = d
    elseif phase == "intro" and d % 30 == 0 then tap(K.A) end
    if phase == "fighting" then
      if d % 20 == 0 then tap(K.A) end
      if d % 400 == 0 then shot(NAME .. "_" .. (d // 400)) end
      if d > mark + 300 and cb2() == OVERWORLD and lock() == 0 then
        w("after: lead " .. partyMon(0))
        w(emu:read16(PARTY + 0x20) == TARGET and "EVOLVED into the target" or "did NOT become the target")
        finish("evolve pass over")
      end
      if d > mark + 9000 then shot(NAME .. "_stuck"); w("after: lead " .. partyMon(0)); finish("the evolution never finished") end
    end

  elseif MODE == "dex" then
    local FIRST, LAST = tonumber(E("FIRST") or "906"), tonumber(E("LAST") or "940")
    if d == 5 then
      for n = FIRST, LAST do dexSet(n) end
      w(string.format("marked %d-%d; the game's own count of caught: see the Pokedex", FIRST, LAST))
    end
    if d == 20 then tap(K.START) end
    if d == 80 then tap(K.A) end
    if d >= 260 and d < 260 + 160 * 24 and (d - 260) % 24 == 0 then tap(K.RIGHT, 4) end   -- a page of seven a tap
    local t = 260 + 160 * 24
    if d == t then emu:addKey(K.DOWN) end
    if d == t + 400 then emu:clearKey(K.DOWN); shot(NAME .. "_list") end
    if d == t + 420 then tap(K.A) end
    local n = LAST - FIRST + 1
    for k = 0, n - 1 do
      if d == t + 560 + k * 220 then shot(string.format("%s_%03d", NAME, LAST - k)) end
      if d == t + 570 + k * 220 and k < n - 1 then tap(K.UP) end          -- the entry before, without leaving
    end
    if d == t + 560 + n * 220 then finish("dex pass over") end

  elseif MODE == "tm" then
    if d == 5 then emptySixth(); give(SPECIES, LEVEL) end
    if d == 60 then
      sixthToLead(); emu:write8(0x03000F2C, 0); w("lead " .. partyMon(0))
      emu:write8(0x0203CE58 + 5, 2)                          -- gBagPosition.pocket: TMs & HMs
    end
    if d == 80 then tap(K.START) end
    if d == 140 then tap(K.DOWN) end
    if d == 156 then tap(K.DOWN) end
    if d == 190 then tap(K.A) end
    local ROW = tonumber(E("TMROW") or "0")                  -- which TM of the pocket, from the top
    for k = 0, ROW - 1 do if d == 330 + k * 16 then tap(K.DOWN) end end
    local t = 330 + ROW * 16
    if d == t + 20 then shot(NAME .. "_pocket") end
    if d == t + 30 then tap(K.A) end
    if d == t + 80 then tap(K.A) end                         -- Use
    if d > t + 80 and d < t + 700 and d % 60 == 0 then tap(K.A) end   -- "Booted up a TM." ... "Teach it?" Yes
    if d == t + 700 then shot(NAME .. "_able") end
    if d == t + 710 then finish("tm pass over") end

  elseif MODE == "damage" then
    local FOE, FOELV, MOVE = tonumber(E("FOE") or "143"), tonumber(E("FOELV") or "100"), tonumber(E("MOVE") or "89")
    -- both Pokemon are made from the random numbers too (IVs, nature): the same numbers for every run
    local SEED = tonumber(E("SEED") or "305419896")
    if d == 5 then emu:write32(0x03005D80, SEED); emptySixth(); give(SPECIES, LEVEL) end
    if d == 60 then
      sixthToLead()
      emu:write16(PARTY + 0x2C, MOVE); emu:write8(PARTY + 0x34, 40)
      if E("ITEM") then emu:write16(PARTY + 0x22, tonumber(E("ITEM"))) end
      emu:write32(0x03005D80, SEED + 1)
      wild(FOE, FOELV)
    end
    if phase == "start" and d > 70 and cb2() == BATTLE then phase = "intro"; mark = d end
    if phase == "start" and d > 1500 then finish("the battle never started") end
    if phase == "intro" then
      if E("EARLY") == "1" and d > mark + 30 then setField() end      -- there before the battle's first events
      if emu:read32(0x03005D60) == ACTION and d > mark + 200 then phase = "menu"; mark = d
      elseif d % 30 == 0 then tap(K.A) end
    elseif phase == "menu" then
      if d == mark + 40 then
        setField(); tweak()
        -- the foe asleep: if it struck first, its damage (which the abilities may also change) would shift
        -- the frame our own roll is drawn on, and the two runs would no longer be the same battle
        emu:write32(MONS + 0x58 + 0x4C, 7)
        emu:write32(0x03005D80, SEED + 2)
        w(battler(0)); w(battler(1)); w(field())
        hp0, hp1 = emu:read16(MONS + 0x28), emu:read16(MONS + 0x58 + 0x28)
        tap(K.A)
      end
      if d == mark + 80 then tap(K.A) end
      if d > mark + 80 then
        -- PINRNG=1: the random numbers held at one value every frame until the hit lands, so that a build
        -- whose turn runs a frame or two longer still draws the same roll
        if E("PINRNG") == "1" and not dealt then emu:write32(0x03005D80, tonumber(E("SEED") or "305419896") + 2) end
        local a, b = emu:read16(MONS + 0x28), emu:read16(MONS + 0x58 + 0x28)
        if b < hp1 and not dealt then
          dealt = hp1 - b; dealtAt = d
          w(string.format("when the hit landed: result flags %02X, move %d, lead's item %d (party) %d (battle), at +%d, rng %08X",
            emu:read8(0x0202427C), emu:read16(0x020241EA), emu:read16(PARTY + 0x22), emu:read16(MONS + 0x2E), d - mark,
            emu:read32(0x03005D80)))
        end
        if a < hp0 and not taken then taken = hp0 - a end
        -- the bars drain over many frames: read the totals a while after the first change
        if dealt and d == dealtAt + 240 then
          w("damage dealt " .. (hp1 - emu:read16(MONS + 0x58 + 0x28)) .. " | damage taken " .. (hp0 - emu:read16(MONS + 0x28)))
          w(string.format("afterwards: lead's item %d (party) %d (battle) | %s", emu:read16(PARTY + 0x22), emu:read16(MONS + 0x2E), stateBytes()))
          shot(NAME); finish("damage pass over")
        end
        if d > mark + 1500 then
          w("no damage dealt | damage taken " .. (hp0 - emu:read16(MONS + 0x28))); shot(NAME); finish("damage pass over")
        end
        if d % 40 == 0 and d > mark + 200 and not dealt then tap(K.B) end
      end
    end

  elseif MODE == "duel" then
    local FOE, FOELV, MOVE = tonumber(E("FOE") or "143"), tonumber(E("FOELV") or "100"), tonumber(E("MOVE") or "89")
    local SEED, TURNS = tonumber(E("SEED") or "305419896"), tonumber(E("TURNS") or "1")
    local SP2 = tonumber(E("SPECIES2") or "0")               -- a second Pokemon of ours, in party slot 2
    local T0 = SP2 > 0 and 60 or 0
    if d == 5 then emu:write32(0x03005D80, SEED); emptySixth(); give(SPECIES, LEVEL) end
    if d == 60 then
      sixthToLead()
      if SP2 > 0 then emptySixth(); give(SP2, tonumber(E("LEVEL2") or tostring(LEVEL))) end
    end
    if d == 60 + T0 then
      if SP2 > 0 then
        for i = 0, 99 do emu:write8(PARTY + 100 + i, emu:read8(PARTY + 500 + i)) end
        emptySixth()
        if E("ITEM2") then emu:write16(PARTY + 100 + 0x22, tonumber(E("ITEM2"))) end
      end
      emu:write16(PARTY + 0x2C, MOVE); emu:write8(PARTY + 0x34, 40)
      if E("MOVE2") then emu:write16(PARTY + 0x2E, tonumber(E("MOVE2"))); emu:write8(PARTY + 0x35, 40) end
      if E("ITEM") then emu:write16(PARTY + 0x22, tonumber(E("ITEM"))) end
      emu:write32(0x03005D80, SEED + 1)
      if E("TRAINER") then                                   -- one of the game's trainers (its AI thinks ahead)
        local id = tonumber(E("TRAINER"))
        run({0x5C, 0x03, id & 0xFF, id >> 8, 0, 0, 0xA0, 0xFE, 0x57, 0x08, 0x02})
      else wild(FOE, FOELV) end
    end
    if phase == "start" and d > 70 + T0 and cb2() == BATTLE then
      phase = "intro"; mark = d
      if E("FOEMOVE") then                                   -- the foe knows this one move (it picks its move as
        for k = 0, 3 do                                      -- the action menu comes up: it has to be in by then)
          emu:write16(ENEMY + 0x2C + 2 * k, k == 0 and tonumber(E("FOEMOVE")) or 0)
          emu:write8(ENEMY + 0x34 + k, k == 0 and 40 or 0)
        end
      end
    end
    if phase == "start" and d > 1500 then finish("the battle never started") end
    if phase ~= "start" then                                 -- every change of the state bytes, as it happens
      local s = stateBytes()
      if s ~= lastState then
        w(string.format("  state at +%d: %s (move %d, attacker %d)", d - mark, s, emu:read16(0x020241EA), emu:read8(0x0202420B)))
        lastState = s
      end
    end
    if phase == "intro" then
      if E("EARLY") == "1" and d > mark + 30 then setField() end
      if emu:read32(0x03005D60) == ACTION and d > mark + 200 then phase = "ready"; mark = d; turn = 1
      elseif d % 30 == 0 then tap(K.A) end
    elseif phase == "ready" then                             -- the action menu is up
      if d == mark + 40 then
        if turn == 1 then
          setField()
          if E("FOEFAST") then emu:write16(MONS + 0x58 + 6, emu:read16(MONS + 6) + tonumber(E("FOEFAST"))) end
          tweak()
          w(battler(0)); w(battler(1)); w(field())
        end
        emu:write32(0x03005D80, SEED + 1 + turn)
        if E("LATEITEM") and turn == 2 then                  -- as if the lead had only now come to hold it
          emu:write16(MONS + 0x2E, tonumber(E("LATEITEM"))); emu:write16(PARTY + 0x22, tonumber(E("LATEITEM")))
        end
        hp0, hp1 = emu:read16(MONS + 0x28), emu:read16(MONS + 0x58 + 0x28)
        dealtAt, takenAt, dealt, taken = nil, nil, 0, 0
        w(string.format("turn %d begins: party slot 1 holds %d, slot 2 holds %d | battler 0 is species %d holding %d", turn,
          emu:read16(PARTY + 0x22), emu:read16(PARTY + 100 + 0x22), emu:read16(MONS), emu:read16(MONS + 0x2E)))
        if E("SWITCH") == "1" and turn == 1 then tap(K.DOWN) else tap(K.A) end      -- Pokemon / Fight
      end
      if E("SWITCH") == "1" and turn == 1 then               -- switch to the second Pokemon instead of attacking
        if d == mark + 60 then tap(K.A) end                  -- the party screen
        if d == mark + 170 then tap(K.RIGHT) end             -- onto slot 2
        if d == mark + 190 then tap(K.A) end                 -- its menu
        if d == mark + 220 then shot(NAME .. "_switch"); tap(K.A); phase = "turn"; turnMark = d end       -- Shift
      else
        if d == mark + 76 and turn == 1 then shot(NAME .. "_moves") end    -- the move menu: name, type, PP
        if d == mark + 80 and turn > 1 and E("MOVE2") then tap(K.RIGHT) end
        if d == mark + 110 then tap(K.A); phase = "turn"; turnMark = d end
      end
    elseif phase == "turn" then
      local a, b = emu:read16(MONS + 0x28), emu:read16(MONS + 0x58 + 0x28)
      if E("DEBUG") == "1" then
        local fn = string.format("%08X %08X move %d by %d", emu:read32(0x03005D60), emu:read32(0x03005D64), emu:read16(0x020241EA), emu:read8(0x0202420B))
        if fn ~= chose then w(string.format("    +%d controllers %s | hp %d %d", d - mark, fn, a, b)); chose = fn end
        if (d - turnMark) % 150 == 0 then shot(string.format("%s_f%04d", NAME, d - mark)) end
      end
      if E("SHOTS") and turn == 1 and d - turnMark < 520 and (d - turnMark) % tonumber(E("SHOTS")) == 0 then
        shot(string.format("%s_a%03d", NAME, d - turnMark))  -- the animation, frame by frame
      end
      if b < hp1 and not dealtAt then                        -- (what a hit took, before Leftovers and the like)
        dealtAt = d; dealt = hp1 - b
        w(string.format("  the lead's hit landed at +%d for %d: result flags %02X, move %d", d - mark, dealt, emu:read8(0x0202427C), emu:read16(0x020241EA)))
      end
      if a < hp0 and not takenAt then
        takenAt = d; taken = hp0 - a
        w(string.format("  the foe's hit landed at +%d for %d: result flags %02X, move %d", d - mark, taken, emu:read8(0x0202427C), emu:read16(0x020241EA)))
      end
      local over = cb2() == OVERWORLD and lock() == 0
      local back = emu:read32(0x03005D60) == ACTION and d > turnMark + 240
      if over or back or d > turnMark + 3000 then
        local first = "nobody was hit"
        if dealtAt and takenAt then first = dealtAt < takenAt and "the lead struck first" or "the foe struck first"
        elseif dealtAt then first = "only the lead's hit landed" elseif takenAt then first = "only the foe's hit landed" end
        w(string.format("turn %d: %s | dealt %d | taken %d | lead's item %d (party) %d (battle) | %s", turn, first,
          dealt, taken, emu:read16(PARTY + 0x22), emu:read16(MONS + 0x2E), stateBytes()))
        if SP2 > 0 then
          w(string.format("        party slot 1 holds %d, slot 2 holds %d | battler 0 is species %d holding %d",
            emu:read16(PARTY + 0x22), emu:read16(PARTY + 100 + 0x22), emu:read16(MONS), emu:read16(MONS + 0x2E)))
        end
        shot(NAME .. "_t" .. turn)
        if over or turn >= TURNS or not back then finish("duel pass over")
        else turn = turn + 1; phase = "ready"; mark = d end
      elseif d % 40 == 0 and d > turnMark + 200 then tap(K.B) end
    end

  elseif MODE == "double" then
    -- two of ours in front (party slots 1 and 2 = battlers 0 and 2) against a trainer whose data says "double"
    local TRAINER, TURNS = tonumber(E("TRAINER") or "56"), tonumber(E("TURNS") or "2")
    local SP2, LV2 = tonumber(E("SPECIES2") or "1216"), tonumber(E("LEVEL2") or tostring(LEVEL))
    local SEED = tonumber(E("SEED") or "305419896")
    if d == 5 then emu:write32(0x03005D80, SEED); emptySixth(); give(SPECIES, LEVEL) end
    if d == 60 then sixthToLead(); emptySixth(); give(SP2, LV2) end
    if d == 120 then
      for i = 0, 99 do emu:write8(PARTY + 100 + i, emu:read8(PARTY + 500 + i)) end
      emptySixth()
      if E("MOVE") then emu:write16(PARTY + 0x2C, tonumber(E("MOVE"))); emu:write8(PARTY + 0x34, 40) end
      if E("MOVE2") then emu:write16(PARTY + 100 + 0x2C, tonumber(E("MOVE2"))); emu:write8(PARTY + 100 + 0x34, 40) end
      if E("ITEM") then emu:write16(PARTY + 0x22, tonumber(E("ITEM"))) end
      if E("ITEM2") then emu:write16(PARTY + 100 + 0x22, tonumber(E("ITEM2"))) end
      w("party 1: " .. partyMon(0)); w("party 2: " .. partyMon(1))
      emu:write32(0x03005D80, SEED + 1)
      -- trainerbattle 3 (no intro text), TRAINER, 0, a text for its defeat; end
      run({0x5C, 0x03, TRAINER & 0xFF, TRAINER >> 8, 0, 0, 0xA0, 0xFE, 0x57, 0x08, 0x02})
    end
    if phase == "start" and d > 130 and cb2() == BATTLE then phase = "intro"; mark = d end
    if phase == "start" and d > 1800 then shot(NAME .. "_nobattle"); finish("the battle never started") end
    if phase ~= "start" then
      local s = stateBytes()
      if s ~= lastState then
        w(string.format("  state at +%d: %s (move %d, attacker %d)", d - mark, s, emu:read16(0x020241EA), emu:read8(0x0202420B)))
        lastState = s
      end
    end
    if phase == "intro" then
      if emu:read32(0x03005D60) == ACTION and d > mark + 200 then
        phase = "fighting"; mark = d; turn = 1; chose = true
        w("battlers on the field: " .. emu:read8(0x0202406C) .. " | battle type " .. string.format("%08X", emu:read32(0x02022FEC)))
        for i = 0, 3 do w(battler(i)) end
        w(field())
        w(string.format("items in the party: slot 1 %d, slot 2 %d", emu:read16(PARTY + 0x22), emu:read16(PARTY + 100 + 0x22)))
        hp0 = {}
        for i = 0, 3 do hp0[i] = emu:read16(MONS + 0x58 * i + 0x28) end
        shot(NAME .. "_start")
      elseif d % 30 == 0 then tap(K.A) end
    elseif phase == "fighting" then
      for i = 0, 3 do                                        -- every hit, as it lands
        local h = emu:read16(MONS + 0x58 * i + 0x28)
        if h < hp0[i] then
          w(string.format("  turn %d +%d: battler %d lost %d (move %d by battler %d, result flags %02X)", turn, d - mark, i,
            hp0[i] - h, emu:read16(0x020241EA), emu:read8(0x0202420B), emu:read8(0x0202427C)))
        end
        hp0[i] = h
      end
      local menu = emu:read32(0x03005D60) == ACTION
      if menu and not chose then                             -- our first Pokemon is asked again: a turn has passed
        w(string.format("turn %d over: items party %d / %d, battle %d / %d | %s", turn, emu:read16(PARTY + 0x22),
          emu:read16(PARTY + 100 + 0x22), emu:read16(MONS + 0x2E), emu:read16(MONS + 0x58 * 2 + 0x2E), stateBytes()))
        shot(NAME .. "_t" .. turn)
        turn = turn + 1
      end
      chose = menu
      local over = cb2() == OVERWORLD and lock() == 0
      if over or turn > TURNS or d > mark + 9000 then
        w(string.format("at the end: items party %d / %d | %s | outcome %d", emu:read16(PARTY + 0x22),
          emu:read16(PARTY + 100 + 0x22), stateBytes(), emu:read8(0x0202433A)))
        finish(over and "double pass over (the battle ended)" or (turn > TURNS and "double pass over" or "double: timed out"))
      elseif d % 16 == 0 then tap(K.A) end                   -- Fight, the first move, the first target, the messages
    end

  elseif MODE == "bag" then
    local ITEM, COUNT = tonumber(E("ITEM") or "769"), tonumber(E("COUNT") or "3")
    if d == 5 and COUNT > 0 then run({0x44, ITEM & 0xFF, ITEM >> 8, COUNT, 0, 0x02}) end   -- COUNT=0: just look
    if d == 40 then emu:write8(0x03000F2C, 0); emu:write8(0x0203CE58 + 5, 0) end       -- the Items pocket
    if d == 60 then tap(K.START) end
    if d == 120 then tap(K.DOWN) end
    if d == 136 then tap(K.DOWN) end
    if d == 170 then tap(K.A) end
    if d == 320 then emu:addKey(K.DOWN) end                  -- down to the end of the pocket, then up one:
    if d == 1100 then emu:clearKey(K.DOWN) end               -- the item just added
    if d == 1130 then tap(K.UP) end
    if d == 1200 then shot(NAME) end
    if d == 1210 then tap(K.A) end                           -- its menu: Use / Give / Toss
    if d == 1280 then shot(NAME .. "_menu") end
    if d == 1290 then finish("bag pass over") end

  elseif MODE == "pc" then
    -- the storage screen on box BOX (a save with the new species in the PC): SELECT ring -> PC -> Move Pokemon
    if d == 5 then emu:write8(emu:read32(0x03005D94), tonumber(E("BOX") or "3") - 1) end
    if d == 20 then tap(K.SEL) end
    if d == 60 then tap(K.A) end
    if d == 200 then tap(K.A) end                            -- "Which PC?": the first, the Pokemon storage
    if d == 330 then tap(K.A) end                            -- "Accessed Lanette's PC."
    if d == 460 then tap(K.A) end                            -- "Pokemon Storage System opened."
    if d == 600 then shot(NAME .. "_menu") end
    if d == 610 then tap(K.DOWN) end
    if d == 630 then tap(K.DOWN) end
    if d == 660 then tap(K.A) end                            -- Move Pokemon
    if d == 1000 then shot(NAME .. "_box") end
    if d == 1010 then tap(K.DOWN) end                        -- from the box's name down onto its first Pokemon
    if d == 1080 then shot(NAME .. "_mon") end
    if d == 1090 then finish("pc pass over") end

  elseif MODE == "save" then
    if d == 5 then emptySixth(); give(SPECIES, LEVEL) end
    if d == 40 then
      emu:write8(0x03000F2C, 0); w("before saving: slot 6 " .. partyMon(5))
      for n in (E("DEXSET") or ""):gmatch("%d+") do dexSet(tonumber(n)) end      -- numbers marked caught
      w(string.format("marker %08X", emu:read32(EXT)))
    end
    if d == 80 then tap(K.START) end
    for k = 0, 4 do if d == 140 + k * 16 then tap(K.DOWN) end end
    if d == 240 then tap(K.A) end
    if d >= 300 and d < 1500 and d % 40 == 0 then tap(K.A) end
    if d == 2100 then finish("save pass over") end

  elseif MODE == "check" then
    if d == 30 then
      for i = 0, 5 do w("party " .. (i + 1) .. ": " .. partyMon(i)) end
      w("in the PC: " .. pcSpecies(1200, 1279))
      local st, lines = emu:read32(0x03005D94), {}           -- and what each of them knows
      for slot = 0, 14 * 30 - 1 do
        local m = st + 4 + slot * 80
        local sp = emu:read16(m + 0x20)
        if sp >= 1200 and sp <= 1279 then
          lines[#lines + 1] = string.format("%d[%d %d %d %d]", sp, emu:read16(m + 0x2C), emu:read16(m + 0x2E), emu:read16(m + 0x30), emu:read16(m + 0x32))
        end
      end
      w("their moves: " .. table.concat(lines, " "))
      local caught = {}
      for n = 906, 1032 do if dexFlag(n, true) then caught[#caught + 1] = n end end
      w("dex numbers 906-1032 caught: " .. table.concat(caught, " "))
      w(string.format("marker %08X; in the PC 1238-1326: %s", emu:read32(EXT), pcSpecies(1238, 1326)))
      finish("check pass over")
    end
  end
end
