-- Egg moves: put two parents in the Day Care (SaveBlock1 + 0x3030, two 0x8C slots), make the egg with the
-- game's own _GiveEggFromDaycare (0x080708C9, through a callasm stub), and log the egg's four moves.
-- Parents are built from party slot 0's data with species, gender (personality), moves and held item set.
-- Set DIR (game.gba/game.sav, output) and HERE (this folder). Log: eggmoves_log.txt.
NAME = "eggmoves"
DIR = DIR or "./"
HERE = HERE or DIR
dofile(HERE .. "../dexnavchain/test_boot.lua")
local SCRIPT, STUB = 0x0203F100, 0x0203F300
local PARTY, COUNT = 0x020244EC, 0x020244E9
local STUBBYTES = {0x10,0xB5,0x05,0x48,0x00,0x68,0x05,0x49,0x40,0x18,0x05,0x4B,0x00,0xF0,0x03,0xF8,
                   0x10,0xBC,0x01,0xBC,0x00,0x47,0x18,0x47,0x8C,0x5D,0x00,0x03,0x30,0x30,0x00,0x00,
                   0xC9,0x08,0x07,0x08}
local NAMES = {[0]="-", [10]="Scratch", [33]="Tackle", [45]="Growl", [52]="Ember", [80]="Petal Dance",
  [92]="Toxic", [130]="Skull Bash", [144]="Transform", [174]="Curse", [187]="Belly Drum", [275]="Ingrain",
  [335]="Block", [407]="Dragon Rush", [22]="Vine Whip", [73]="Leech Seed", [77]="PoisonPowder", [79]="Sleep Powder", [76]="SolarBeam", [188]="Sludge Bomb", [202]="Giga Drain", [321]="Tickle", [276]="Superpower"}
local function mv(m) return NAMES[m] or tostring(m) end
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1)
  emu:write8(0x03000E38, 0)
end
local function daycare() return emu:read32(0x03005D8C) + 0x3030 end
-- parent: {species, female?, moves{...}}
local function put(slot, p)
  local dst = daycare() + slot * 0x8C
  for i = 0, 0x4F do emu:write8(dst + i, emu:read8(PARTY + i)) end
  local pers = emu:read32(PARTY) & 0xFFFFFF00
  emu:write32(dst, pers | (p[2] and 0x00 or 0xFF))            -- low byte: gender against the species' ratio
  emu:write16(dst + 0x20, p[1])
  emu:write16(dst + 0x22, 0)                                   -- no held item
  for i = 0, 3 do emu:write16(dst + 0x2C + i * 2, p[3][i + 1] or 0); emu:write8(dst + 0x34 + i, 10) end
  emu:write32(dst + 0x48, emu:read32(dst + 0x48) & 0x3FFFFFFF) -- not an egg
  emu:write32(dst + 0x88, 0)
end
local CASES = {
  {"mother knows Curse, father not", {1, true, {174, 33}}, {1, false, {33}}},
  {"father knows Curse, mother not", {1, true, {33}}, {1, false, {174, 33}}},
  {"Ditto + female knowing Curse", {132, false, {144}}, {1, true, {174, 33}}},
  {"Ditto + male knowing Curse", {132, false, {144}}, {1, false, {174, 33}}},
  {"mother: 4 egg moves; father: Toxic (TM) + Curse", {1, true, {174, 80, 130, 275}}, {1, false, {92, 174}}},
  {"mother: Skull Bash, Petal Dance; father: Ingrain, Block", {1, true, {130, 80}}, {1, false, {275, 335}}},
  {"mother knows Curse; father 4 TMs", {1, true, {174, 33}}, {1, false, {92, 76, 188, 202}}},
  {"father knows Curse + 3 TMs", {1, true, {33}}, {1, false, {174, 76, 188, 202}}},
  {"Ditto + female: Curse + 3 TMs", {132, false, {144}}, {1, true, {174, 76, 188, 202}}},
  {"Turtwig: mother knows Tickle (its 17th egg move)", {440, true, {321, 33}}, {440, false, {33}}},
  {"Turtwig: father knows Tickle + Superpower (16th)", {440, true, {33}}, {440, false, {321, 276}}},
}
local plan, t0 = {}, nil
local function at(d, fn) plan[#plan + 1] = {d, fn} end
local t = 30
at(t, function()
  for i, b in ipairs(STUBBYTES) do emu:write8(STUB + i - 1, b) end
  if emu:read8(COUNT) >= 6 then emu:write8(COUNT, 5) end
  w("party count " .. emu:read8(COUNT))
end)
for n, c in ipairs(CASES) do
  t = t + 20
  at(t, function()
    put(0, c[2]); put(1, c[3])
    emu:write32(daycare() + 0x118, 0x1234567 + n)              -- offspring personality: an egg is waiting
    run({0x23, 0x01, 0xF3, 0x03, 0x02, 0x02})                  -- callasm STUB | 1; end
  end)
  at(t + 200, function()
    local k = emu:read8(COUNT) - 1
    local e = PARTY + k * 100
    local egg = (emu:read32(e + 0x48) >> 30) & 1
    w(string.format("%-55s -> slot %d species %d egg %d: %s, %s, %s, %s", c[1], k, emu:read16(e + 0x20), egg,
      mv(emu:read16(e + 0x2C)), mv(emu:read16(e + 0x2E)), mv(emu:read16(e + 0x30)), mv(emu:read16(e + 0x32))))
    emu:write8(COUNT, k)                                        -- drop the egg again
  end)
  t = t + 220
end
at(t + 10, function() done() end)
function TEST(f)
  t0 = t0 or f
  for _, p in ipairs(plan) do if f - t0 == p[1] then p[2]() end end
end
