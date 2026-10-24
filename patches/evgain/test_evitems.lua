-- The EV items from the Bag (vitamins: Items pocket; the EV-lowering berries: Berries pocket) on the lead Pokemon,
-- near the 510 total: the lead's EVs written, the item put in its pocket's first slot, then Start, Bag, the item,
-- Use, the lead, the message closed; the EVs read back. Not evgain's routine (that is the battles') - the game's own
-- item-effect code (PokemonItemEffects 0x0806BD28, via ItemUseCB_Medicine 0x081B6589 / ItemUseCB_ReduceEV
-- 0x081B67C9), looked at because a stuck 509 was reported. Pictures ei_<case>_*.png.
-- env: EV_DIR (output folder, with the slash), EV_HERE (this folder, with the slash), CASES (optional, see below)
NAME = "ei"
DIR = os.getenv("EV_DIR") or "./"
local HERE = os.getenv("EV_HERE") or "./"
dofile(HERE .. "../dexnavchain/test_boot.lua")
local PARTY, POCKETS, BAGPOS, MENUPOS = 0x020244EC, 0x02039DD8, 0x0203CE58, 0x0203760E
local BAG_ROW = tonumber(os.getenv("BAG_ROW") or "2")     -- the Bag's line in the Start menu
local function evs(m)
  m = m or PARTY
  local t, s = {}, 0
  for k = 0, 5 do t[#t + 1] = emu:read8(m + 0x38 + k); s = s + t[#t] end
  return table.concat(t, ",") .. " = " .. s .. string.format(" (HP %d/%d, Lv %d)", emu:read16(m + 0x56),
    emu:read16(m + 0x58), emu:read8(m + 0x54))
end
local function run(bytes)                                           -- a script, as test_mint_cheren.lua runs one
  local SCRIPT = 0x0203F100
  for k, b in ipairs(bytes) do emu:write8(SCRIPT + k - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1); emu:write8(0x03000E38, 0)
end
local function key16() return emu:read32(emu:read32(0x03005D90) + 0xAC) & 0xFFFF end
local function left(pocket, item)
  local slots = emu:read32(POCKETS + 8 * pocket)
  for k = 0, 99 do if emu:read16(slots + 4 * k) == item then return emu:read16(slots + 4 * k + 2) ~ key16() end end
  return 0
end

local plan, i = {}, 1
local function act(gap, fn) plan[#plan + 1] = {fn = fn, gap = gap} end
local function field(key) plan[#plan + 1] = {field = key} end
local function taps(k, n, gap) for _ = 1, n do act(gap or 14, function() tap(k) end) end end

-- case: label, pocket (0 Items, 3 Berries), item, EVs (HP, Atk, Def, Spe, SpA, SpD), HP, party slot (the lead if nil)
local function use(label, pocket, item, ev, hp, slot)
  slot = slot or 0
  local MON = PARTY + 100 * slot
  act(10, function()
    if hp then emu:write16(MON + 0x56, hp) end
    for k = 1, 6 do if ev then emu:write8(MON + 0x37 + k, ev[k]) end end   -- (nil: as the last case left them)
    local slots = emu:read32(POCKETS + 8 * pocket)
    emu:write16(slots, item); emu:write16(slots + 2, 5 ~ key16())
    emu:write8(BAGPOS + 5, pocket)
    for p = 0, 4 do emu:write16(BAGPOS + 8 + 2 * p, 0); emu:write16(BAGPOS + 18 + 2 * p, 0) end
    emu:write8(MENUPOS, 0)
    w(string.format("%s: item %d (pocket %d), slot %d, EVs before %s", label, item, pocket, slot, evs(MON)))
  end)
  act(40, function() tap(K.START) end)
  act(10, function() shot("ei_" .. label .. "_0_menu") end)
  taps(K.DOWN, BAG_ROW)
  act(120, function() tap(K.A) end)                                  -- the Bag
  act(10, function()                                                 -- the Berries pocket sorts itself on opening:
    local slots, n = emu:read32(POCKETS + 8 * pocket), nil              -- find the item's line, then Down to it
    for k = 0, 99 do if emu:read16(slots + 4 * k) == item then n = k; break end end
    w(string.format("%s: the item is line %s of the pocket", label, tostring(n)))
    for _ = 1, n or 0 do table.insert(plan, i + 1, {gap = 14, fn = function() tap(K.DOWN) end}) end
  end)
  act(10, function() shot("ei_" .. label .. "_1_bag") end)
  act(40, function() tap(K.A) end)                                   -- the item: (Check Tag) / Use / Give / Toss / Cancel
  if pocket == 3 then act(20, function() tap(K.DOWN) end) end         -- a berry's menu starts on Check Tag
  act(10, function() shot("ei_" .. label .. "_2_menu") end)
  act(120, function() tap(K.A) end)                                  -- Use: the party
  act(10, function() shot("ei_" .. label .. "_3_party") end)
  taps(K.DOWN, slot)
  act(90, function() tap(K.A) end)                                   -- the Pokemon
  act(10, function() shot("ei_" .. label .. "_4_used") end)
  act(10, function() w(string.format("%s: EVs after %s", label, evs(MON))) end)
  for k = 1, 4 do
    act(60, function() tap(K.B) end)
    act(10, function() shot("ei_" .. label .. "_5_out" .. k) end)
  end
  field(K.B)
  act(10, function() w(string.format("%s: back on the field, EVs %s, item left %d", label, evs(MON),
    left(pocket, item))) end)
end

act(10, function() w(string.format("lead species %d, EVs %s", emu:read16(PARTY + 0x20), evs())) end)
use("hpup_fainted", 0, 63, {53, 136, 66, 115, 95, 35})  -- the save's lead is fainted (0/293): HP Up, +2 max HP
use("carbos509", 0, 66, {252, 252, 5, 0, 0, 0}, 100)  -- Speed: room for one point (HP 100: the HP EVs written
                                                       -- raise the max when the stats are worked out)
use("carbos510", 0, 66, {252, 252, 5, 1, 0, 0})       -- full: no effect
use("protein509", 0, 64, {5, 252, 252, 0, 0, 0})      -- Attack full, 509: no effect, stays 509
use("zinc505", 0, 70, {252, 252, 1, 0, 0, 0})         -- room for five
use("calcium_low", 0, 67, {0, 0, 0, 0, 95, 0})        -- far from the total: as before
use("pomeg510", 3, 153, {252, 252, 6, 0, 0, 0})       -- HP lowered
use("carbos_after", 0, 66, nil)                       -- the room the berry made
use("pomeg_1hp", 3, 153, nil, 1)                      -- stats as the Carbos left them, 1 HP: the berry lowers max HP
use("pomeg_fainted", 3, 153, nil, 0)                  -- the same, fainted
use("hondew0", 3, 156, {252, 252, 6, 0, 0, 0})        -- SpA at 0: nothing to lower
use("candy_alive", 0, 68, nil, 100, 3)                 -- a Rare Candy on the fourth Pokemon (Lv 72) at 100 HP: + the difference
use("candy_fainted", 0, 68, nil, 0, 3)                 -- the same, fainted
act(10, function()                                     -- a new Pokemon (old max HP 0): a wild one, Zigzagoon Lv 50
  run({0xB6, 0x20, 0x01, 50, 0x00, 0x00, 0xB7, 0x02})
end)
act(700, function()
  local e = 0x02024744
  w(string.format("wild: species %d Lv %d HP %d/%d", emu:read16(e + 0x20), emu:read8(e + 0x54), emu:read16(e + 0x56),
    emu:read16(e + 0x58)))
  shot("ei_wild")
end)
act(10, function() done() end)

local waitUntil, calm = 0, 0
function TEST(f)
  local p = plan[i]
  if not p or f < waitUntil then return end
  if p.field then
    if lock() == 0 and cb2() == OVERWORLD then calm = calm + 1 else calm = 0 end
    if not (lock() == 0 and cb2() == OVERWORLD) and f % 20 == 0 then tap(p.field) end
    if calm >= 60 then calm = 0; i = i + 1 end
    if f > 90000 then w("TIMEOUT at a field wait"); done() end
    return
  end
  local ok, err = pcall(p.fn)
  if not ok then w("ERROR " .. tostring(err)); done() end
  waitUntil = f + p.gap; i = i + 1
end
