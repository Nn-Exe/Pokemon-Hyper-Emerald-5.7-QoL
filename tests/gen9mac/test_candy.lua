-- A Rare Candy from the Bag on the lead, as the player does (tests/gen9mac copy of patches/gen9rest/test_useitem.lua):
-- the Items pocket rewritten so that one Rare Candy is its last item; START -> Bag
-- (Items pocket) -> the last item -> Use -> the first Pokemon -> level up -> the evolution scene, A through it (a move
-- to forget: the first), B back to the field. SPECIES LEVEL TARGET [HELD=item] [KNOWS=move] [HOUR=h, the game's clock].
-- Logs the lead before and after; screenshots on the way.
local E = os.getenv
DIR = E("GEN9_DIR")
local TAG = E("TAG") or "ui"
NAME = TAG .. "_use"
dofile("C:/Users/nonth/Desktop/Works & Productivity/gba-trans/hyper-emerald-en-qol/patches/dexnavchain/test_boot.lua")
local SPECIES, LEVEL, ITEM, TARGET = tonumber(E("SPECIES")), tonumber(E("LEVEL") or "30"), 68, tonumber(E("TARGET"))
local function key() return emu:read32(emu:read32(0x03005D90) + 0xAC) end
local function count68()
  local n = 0
  for s = 0, 199 do
    local a = 0x0203DAE0 + 4 * s
    if emu:read16(a) == 68 then n = n + ((emu:read16(a + 2) ~ (key() & 0xFFFF)) & 0xFFFF) end
  end
  return n
end
local SCRIPT, PARTY = 0x0203F100, 0x020244EC
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1); emu:write8(0x03000E38, 0)
end
local crashed = false
for _, v in ipairs({0x00000000, 0x00000004, 0x0000000C, 0x00000010}) do
  emu:setBreakpoint(function()
    if not crashed then crashed = true; w(string.format("VECTOR %02X lr %08X", v, emu:readRegister("lr"))) end
  end, v)
end
local ncall = 0
emu:setBreakpoint(function()
  ncall = ncall + 1
  if ncall <= 12 then
    w(string.format("evo-target(species %d, mode %d, item %d) from %08X", emu:read16(emu:readRegister("r0") + 0x20),
      emu:readRegister("r1"), emu:readRegister("r2"), emu:readRegister("lr")))
  end
end, 0x09F0534C)
local function lead() return string.format("species %d lv %d item %d", emu:read16(PARTY + 0x20), emu:read8(PARTY + 0x54), emu:read16(PARTY + 0x22)) end
local t0, done_ = nil, false
function TEST(f)
  t0 = t0 or f
  local d = f - t0
  if done_ then return end
  if d == 2 and E("HOUR") then                     -- local time = RTC - the save's offset (SaveBlock2 +0x98: days, hours)
    local cur, sb2 = emu:read8(0x03005CFA), emu:read32(0x03005D90)
    local h = emu:read8(sb2 + 0x9A); if h > 127 then h = h - 256 end
    h = h + (cur - tonumber(E("HOUR"))) % 24
    if h > 23 then h = h - 24; emu:write16(sb2 + 0x98, emu:read16(sb2 + 0x98) + 1) end
    emu:write8(sb2 + 0x9A, h & 0xFF)
  end
  if d == 3 then                                 -- the Items pocket (bagslots: 200 slots at 0x0203DAE0) rewritten
    local n, items = count68(), {}                 -- in its own order without Rare Candy, then one Rare Candy last
    for s = 0, 199 do
      local a = 0x0203DAE0 + 4 * s
      local id = emu:read16(a)
      if id ~= 0 and id ~= 68 then items[#items + 1] = {id, emu:read16(a + 2)} end
    end
    for s = 0, 199 do
      local a = 0x0203DAE0 + 4 * s
      local it = items[s + 1]
      if it then emu:write16(a, it[1]); emu:write16(a + 2, it[2])
      elseif s == #items then emu:write16(a, 68); emu:write16(a + 2, (1 ~ key()) & 0xFFFF)
      else emu:write32(a, 0) end
    end
    w(string.format("Rare Candies in the Bag before: %d; the pocket now ends with one (%d items)", n, #items + 1))
  end
  if d == 5 then
    emu:write8(0x020244E9, 5)
    for i = 0, 99 do emu:write8(PARTY + 500 + i, 0) end
    run({0x79, SPECIES & 0xFF, SPECIES >> 8, LEVEL, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0x02})
  end
  if d == 60 then
    for i = 0, 99 do emu:write8(PARTY + i, emu:read8(PARTY + 500 + i)) end
    if E("HELD") then emu:write16(PARTY + 0x22, tonumber(E("HELD"))) end
    if E("KNOWS") then emu:write16(PARTY + 0x2E, tonumber(E("KNOWS"))); emu:write8(PARTY + 0x35, 5) end
    w("before: lead " .. lead() .. " | Rare Candies " .. count68())
  end
  if d == 100 then emu:write8(0x03000F2C, 0); emu:write8(0x0203CE58 + 5, 0) end   -- the Items pocket
  if d == 120 then tap(K.START) end
  if d == 180 then tap(K.DOWN) end
  if d == 196 then tap(K.DOWN) end
  if d == 230 then tap(K.A) end
  if d == 380 then emu:addKey(K.DOWN) end
  if d == 1160 then emu:clearKey(K.DOWN) end
  if d == 1190 then tap(K.UP) end
  if d == 1260 then shot(NAME .. "_0list"); tap(K.A) end           -- the item's menu
  if d == 1330 then shot(NAME .. "_1menu"); tap(K.A) end           -- Use
  if d == 1480 then shot(NAME .. "_2party"); tap(K.A) end          -- the first Pokemon
  if d > 1480 and d < 4200 and (d - 1480) % 40 == 0 then
    if (d - 1480) % 400 == 0 then shot(string.format("%s_3_%04d", NAME, d - 1480)) end
    if emu:read16(PARTY + 0x20) == TARGET then tap(K.B) else tap(K.A) end
  end
  if d > 4200 and d < 4600 and d % 40 == 0 then tap(K.B) end
  if d == 4600 or crashed then
    shot(NAME .. "_4end")
    w("after: lead " .. lead() .. " | the game's hour " .. emu:read8(0x03005CFA))
    w(crashed and "CRASHED" or (emu:read16(PARTY + 0x20) == TARGET and "EVOLVED into the target" or "did NOT become the target"))
    done_ = true; done()
  end
end
