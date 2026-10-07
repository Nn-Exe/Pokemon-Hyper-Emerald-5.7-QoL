-- A fusion's slot that says "taken" with nothing to split (patches/fusionfix). Run next to game.gba / game.sav: a
-- save with a fused Necrozma in the party, its Solgaleo stored, and a fused Kyurem in the PC - ours has all three.
-- Most steps enter the item's script past its party-choice screen: the item id goes into gSpecialVar_ItemId, the
-- chosen slot into var 0x8004, and the script starts at its callasm (0x094A27D5; the DNA Splicers' at 0x08FD6559).
-- `bag` uses the item for real (registered, SELECT popup, the party screen).
--
-- SCEN (env) picks a list below - v15 (default), gone_necrozma, gone_calyrex, gone_kyurem - or STEPS gives one,
-- comma separated. A slot is a number, or n the Necrozma, p its Solgaleo / Lunala in the party, x / y two others.
--   room                 drop a party member so a split has room (6 -> 5)
--   use:ITEM:SLOT:R      use the item (641 N-Solarizer, 642 N-Lunarizer, 742 Unity Reins, 671 DNA Splicers) and
--                        expect answer R in var 0x800D. Necrozma / Calyrex: 0 can't be combined, 1 done, 2 missing
--                        the partner, 3 "Multiple fusions are not allowed!", 5 party full. Kyurem: 1 fused, 2 no
--                        Kyurem, 3 the same refusal, 4 split. "1/3" = 1 on the patched build, 3 with OLD=1 (none).
--   bag:ITEM:SLOT:R      the same through the SELECT popup and the party screen, with screenshots
--   w8:ADDR:V  w16:ADDR:V    write to memory (hex address)
--   set:SLOT:SPECIES     give a party slot another species (the Solgaleo stands in for Lunala, and so on)
--   boxset:FROM:TO       the same for every Pokemon of a species in the PC
--   nomove4:SLOT         forget the fourth move, so a fusion's move has a place
--   has:SPECIES          the party must hold one
--   keep[:ADDR] / kept[:ADDR]    remember a slot's 100 bytes (Necrozma's without ADDR) / they must be the same
--   eviv                 open the EV-IV Display (item 650) and close it: on v1.5 this is what leaves the byte
--   save                 save from the Start menu
--   log                  party and the three slots
--   old:STEP / new:STEP  only with OLD=1 (puts by hand what the patch would have, so the next case starts
--                        the same) / only without it
-- Scenario "a v1.5 save carried over": on a v1.5 build NAME=mk STEPS=room,use:641:n:1,eviv,save ; then that .sav
-- on the build under test with STEPS=bag:641:n:1/3. NEW GAME is test_fusionfix_newgame.lua.
NAME = os.getenv("NAME") or "fusionfix"
dofile((DIR or "./") .. "../dexnavchain/test_boot.lua")
local OLD = os.getenv("OLD") == "1"
local SCENS = {
  -- what v1.5's scratch byte did to the Necrozma slot, and what must stay as it was
  v15 = {
    "log", "room",
    "use:641:n:1",                    -- split: Necrozma and Solgaleo in the party, the slot empty
    "w8:0203D600:21",                 -- A. what v1.5 left in an empty slot
    "use:641:n:1/3",                  --    fuse (the report)
    "old:w16:0203D600:0", "old:use:641:n:1",
    "w8:0203D600:126",                -- B. the stored Solgaleo reads 894
    "use:641:n:1/3",                  --    split
    "old:w16:0203D600:844", "old:use:641:n:1", "has:844",
    "use:641:n:1",                    -- fused again, cleanly
    "w16:0203D600:845",               -- C. the stored Solgaleo reads 845, Lunala
    "use:641:n:1/3",
    "old:w16:0203D600:844", "old:use:641:n:1", "has:844",
    "set:p:845",                      -- D. the same with the N-Lunarizer (the Solgaleo stands in for Lunala)
    "use:642:n:1",
    "w8:0203D600:115",                --    the stored Lunala reads 883
    "use:642:n:1/3",
    "old:w16:0203D600:845", "old:use:642:n:1", "has:845",
    "set:p:844",
    "set:x:1098", "set:y:1088", "nomove4:x",    -- E. the Unity Reins go through untouched (Calyrex and Glastrier)
    "use:742:x:1", "use:742:x:1", "has:1088",
    "use:641:n:1",                    -- F. a real fusion stored: a second one is still refused, the slot untouched
    "keep", "set:x:853", "set:y:844",
    "use:641:x:3", "kept",
    "use:642:n:0",                    --    and the wrong item on Dusk Mane still "can't be combined"
    "kept",
  },
  -- the slot holds a Solgaleo and no fused Necrozma is left (released, or a new game over a fused save)
  gone_necrozma = {
    "log", "room",
    "set:n:853",                      -- the Dusk Mane is gone: a plain Necrozma in its place,
    "set:y:844",                      -- and a Solgaleo to fuse it with
    "use:641:n:1/3", "new:has:1068", "log",
  },
  gone_calyrex = {
    "room",
    "set:x:1098", "set:y:1088", "nomove4:x",
    "use:742:x:1",                    -- Ice Rider, the Glastrier stored
    "keep:0203D644", "set:1:1098", "set:3:1088", "nomove4:1",
    "use:742:1:3", "kept:0203D644",   -- a second Calyrex while the rider is in the party: refused, slot untouched
    "set:x:1098",                     -- the rider is gone: a plain Calyrex in its place
    "use:742:1:1/3", "new:has:1099", "log",
  },
  gone_kyurem = {
    "log", "room",
    "set:x:697", "set:y:699",         -- a Zekrom to choose and a Kyurem in the party
    "keep:0203D800",
    "use:671:x:3", "kept:0203D800",   -- Black Kyurem is in the PC: refused, slot untouched
    "boxset:996:699",                 -- it is gone
    "use:671:x:1/3", "new:has:996", "log",
  },
}
local STEPS = {}
if os.getenv("STEPS") then for s in os.getenv("STEPS"):gmatch("[^,]+") do STEPS[#STEPS + 1] = s end
else STEPS = SCENS[os.getenv("SCEN") or "v15"] end

local SCRIPT, PARTY, COUNT, RESULT, ITEMID = 0x0203F100, 0x020244EC, 0x020244E9, 0x020375F0, 0x0203CE7C
local SLOT1, SLOT2, SLOT3, PARTYCUR = 0x0203D5E0, 0x0203D644, 0x0203D800, 0x0203CED1     -- gPartyMenu.slotId
local NECRO = {[853] = true, [1068] = true, [1069] = true}
local fails = 0
local function ok(cond, msg) w((cond and "  ok   " or "  FAIL ") .. msg); if not cond then fails = fails + 1 end end
local q, now = {}, 0
local function after(d, fn) q[#q + 1] = {now + d, fn} end
local function species(i) return emu:read16(PARTY + 100 * i + 0x20) end
local function pid(i) return emu:read32(PARTY + 100 * i) end
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1)
  emu:write8(0x03000E38, 0)
end
local function bytes100(a)
  local t = {}
  for k = 0, 99, 4 do t[#t + 1] = string.format("%08X", emu:read32(a + k)) end
  return table.concat(t)
end
local function state()
  local t = {}
  for i = 0, 5 do t[#t + 1] = string.format("%d/L%d", species(i), emu:read8(PARTY + 100 * i + 0x54)) end
  return string.format("party(%d) %s | Necrozma slot %d/L%d | Calyrex slot %d/L%d | Kyurem slot %d/L%d", emu:read8(COUNT),
    table.concat(t, " "), emu:read16(SLOT1 + 0x20), emu:read8(SLOT1 + 0x54), emu:read16(SLOT2 + 0x20),
    emu:read8(SLOT2 + 0x54), emu:read16(SLOT3 + 0x20), emu:read8(SLOT3 + 0x54))
end
-- n / x / y are followed by personality (a fusion closes the gap its partner leaves, so slots move). All six
-- slots are looked at: the routine puts a split-off partner in the next slot and leaves gPlayerPartyCount to
-- the game's next recount.
local who = {}
local function find(p) for i = 0, 5 do if species(i) ~= 0 and pid(i) == p then return i end end end
local function slot_of(s)
  if tonumber(s) then return tonumber(s) end
  if s == "p" then
    for i = 0, 5 do
      if (species(i) == 844 or species(i) == 845) and pid(i) ~= who.x and pid(i) ~= who.y then return i end
    end
    return nil
  end
  if not who.n then
    for i = 0, 5 do if NECRO[species(i)] then who.n = pid(i); break end end
    for i = 0, 5 do
      if species(i) ~= 0 and not NECRO[species(i)] and species(i) ~= 844 and species(i) ~= 845 then
        if not who.x then who.x = pid(i) elseif not who.y then who.y = pid(i) end
      end
    end
  end
  return who[s] and find(who[s])
end
local function expected(s)
  local new, old = s:match("^(%d+)/(%d+)$")
  if new then return tonumber(OLD and old or new) end
  return tonumber(s)
end
local function start_menu(action, fn)          -- open the Start menu and pick the entry with this action id
  tap(K.START)
  after(60, function()
    local n, cur, idx = emu:read8(0x0203760F), emu:read8(0x0203760E), nil
    for i = 0, n - 1 do if emu:read8(0x02037610 + i) == action then idx = i end end
    if not idx then ok(false, "no action " .. action .. " in the Start menu"); return end
    local downs = (idx - cur) % n
    for d = 1, downs do after(d * 14, function() tap(K.DOWN) end) end
    after(downs * 14 + 20, function() tap(K.A); after(1, fn) end)
  end)
end

local k, kept = 0, nil
local step
local function settle(fn)                       -- A through the messages until the field is ours again
  local t0, quiet = now, 0
  local function poll()
    if lock() == 0 and cb2() == OVERWORLD then quiet = quiet + 1 else quiet = 0 end
    if quiet > 60 then fn(); return end
    if now - t0 > 2400 then ok(false, "the script never gave the field back"); fn(); return end
    if (now - t0) % 24 == 0 then tap(K.A) end
    after(1, poll)
  end
  after(1, poll)
end
local function answer(a, tag)
  local r, want = emu:read16(RESULT), expected(a[4] or "")
  if want then ok(r == want, string.format("%s: answer %d (expected %d)", tag, r, want))
  else w(string.format("  %s: answer %d", tag, r)) end
end
local DO = {}
function DO.log(a) w("  " .. state()); step() end
function DO.room(a)
  slot_of("n")
  if emu:read8(COUNT) == 6 then
    local v = find(who.y) or 5                  -- y leaves; the last member takes its place
    for i = 0, 99 do
      emu:write8(PARTY + 100 * v + i, emu:read8(PARTY + 500 + i)); emu:write8(PARTY + 500 + i, 0)
    end
    emu:write8(COUNT, 5)
    who.x, who.y, who.n = nil, nil, nil
  end
  w("  " .. state()); step()
end
function DO.w8(a) emu:write8(tonumber(a[2], 16), tonumber(a[3])); w("  " .. state()); step() end
function DO.w16(a) emu:write16(tonumber(a[2], 16), tonumber(a[3])); w("  " .. state()); step() end
function DO.set(a)
  local i = slot_of(a[2])
  if not i then ok(false, "no slot " .. a[2]) else emu:write16(PARTY + 100 * i + 0x20, tonumber(a[3])) end
  w("  " .. state()); step()
end
function DO.nomove4(a) emu:write16(PARTY + 100 * slot_of(a[2]) + 0x32, 0); step() end
function DO.has(a)
  local found = false
  for i = 0, 5 do if species(i) == tonumber(a[2]) then found = true end end
  ok(found, "the party holds species " .. a[2]); step()
end
function DO.keep(a) kept = bytes100(a[2] and tonumber(a[2], 16) or SLOT1); step() end
function DO.kept(a)
  ok(bytes100(a[2] and tonumber(a[2], 16) or SLOT1) == kept, "the slot is byte for byte what it was"); step()
end
function DO.boxset(a)
  local base, n = emu:read32(0x03005D94), 0   -- gPokemonStoragePtr: 14 boxes of 30, 80 bytes each, after 4 bytes
  for i = 0, 14 * 30 - 1 do
    local m = base + 4 + i * 80
    if emu:read16(m + 0x20) == tonumber(a[2]) then emu:write16(m + 0x20, tonumber(a[3])); n = n + 1 end
  end
  w("  " .. n .. " in the PC"); step()
end
function DO.use(a)
  local item, i = tonumber(a[2]), slot_of(a[3])
  if not i then ok(false, "no slot " .. a[3]); step(); return end
  emu:write16(ITEMID, item); emu:write16(RESULT, 99)
  w(string.format("  item %d on slot %d (species %d)", item, i, species(i)))
  if item == 671 then    -- lock ; setvar 0x8004 slot ; goto 0x08FD6559 (bufferpartymonnick, then the callasm)
    run({0x6A, 0x16, 0x04, 0x80, i, 0x00, 0x05, 0x59, 0x65, 0xFD, 0x08})
  else                   -- lock ; setvar 0x8006 0 ; setvar 0x8004 slot ; goto 0x094A27D5
    run({0x6A, 0x16, 0x06, 0x80, 0x00, 0x00, 0x16, 0x04, 0x80, i, 0x00, 0x05, 0xD5, 0x27, 0x4A, 0x09})
  end
  after(150, function()
    shot(string.format("%s_%02d", NAME, k)); answer(a, "use")
    settle(function() w("  " .. state()); step() end)
  end)
end
function DO.bag(a)
  local item, i = tonumber(a[2]), slot_of(a[3])
  emu:write16(emu:read32(0x03005D8C) + 0x496, item)        -- registered to UP in the SELECT popup
  emu:write16(RESULT, 99)
  w(string.format("  item %d from the SELECT popup, slot %d (species %d)", item, i, species(i)))
  after(10, function() tap(K.SEL) end)
  after(60, function() tap(K.UP) end)
  local t0 = now
  local function pick()
    if cb2() == OVERWORLD then
      if now - t0 > 900 then ok(false, "the party screen never opened"); step(); return end
      after(1, pick); return
    end
    after(120, function()
      local function move()
        local cur = emu:read8(PARTYCUR)
        if cur ~= i and now - t0 < 2000 then tap(K.DOWN); after(16, move); return end
        shot(string.format("%s_%02d_party", NAME, k))
        ok(cur == i, "the cursor is on slot " .. i)
        tap(K.A)
        local function back()
          if cb2() ~= OVERWORLD and now - t0 < 3000 then after(1, back); return end
          after(150, function()
            shot(string.format("%s_%02d_message", NAME, k)); answer(a, "bag")
            settle(function() shot(string.format("%s_%02d_after", NAME, k)); w("  " .. state()); step() end)
          end)
        end
        after(30, back)
      end
      move()
    end)
  end
  after(70, pick)
end
function DO.eviv(a)
  emu:write16(emu:read32(0x03005D8C) + 0x496, 650)
  after(10, function() tap(K.SEL) end)
  after(60, function() tap(K.UP) end)
  after(240, function() shot(string.format("%s_%02d_eviv", NAME, k)) end)
  after(260, function() tap(K.B) end)
  after(300, function() tap(K.B) end)
  after(420, function()
    w(string.format("  byte 0203D600 = %d | %s", emu:read8(0x0203D600), state())); step()
  end)
end
function DO.save(a)
  local counter = emu:read32(0x03006200)
  start_menu(5, function()
    after(90, function() tap(K.A) end)          -- save? YES
    after(200, function() tap(K.A) end)         -- overwrite? YES
    after(900, function()
      ok(emu:read32(0x03006200) ~= counter, "saved"); tap(K.A)
    end)
    after(960, function() tap(K.B) end)
    after(1060, step)
  end)
end
step = function()
  k = k + 1
  local s = STEPS[k]
  if not s then
    w(fails == 0 and "ALL PASSED" or (fails .. " FAILED")); done(); return
  end
  local only_old = s:match("^old:(.*)$")
  if only_old then
    if not OLD then step(); return end
    s = only_old
  end
  local only_new = s:match("^new:(.*)$")
  if only_new then
    if OLD then step(); return end
    s = only_new
  end
  local a = {}
  for x in s:gmatch("[^:]+") do a[#a + 1] = x end
  w(string.format("%d) %s", k, s))
  if DO[a[1]] then DO[a[1]](a) else ok(false, "unknown step"); step() end
end
function TEST(f)
  now = f
  if k == 0 then w((OLD and "OLD=1: expecting the unpatched answers" or "expecting the patched answers")); step() end
  local i = 1
  while i <= #q do
    if q[i][1] <= f then local fn = q[i][2]; table.remove(q, i); fn() else i = i + 1 end
  end
end
