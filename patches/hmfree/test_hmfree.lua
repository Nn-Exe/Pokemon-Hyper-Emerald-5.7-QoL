-- Field moves without a Pokemon that can learn them. The party's first Pokemon is turned into a Magikarp, which
-- can learn no HM. MODE (env):
--   unit  - call the hack's routine 0x08FF1BA0 for each HM move without / with the HM, Rock Climb, and a
--           Chimchar control that can learn Cut (the hack's own answer must stand)
--   surf  - badge 5 + HM03, Petalburg (19,7) facing the pond: A, yes, check the surfing bit
--   cut   - badge 1 + HM01, Route 102 (10,7) facing the tree at (11,7): A, yes, check the tree's flag 0x12
--   party - badge 6 + HM02: party menu lists Fly (24); choose it, the Fly map opens
--   flash - badge 2 + HM05 in Granite Cave (34/71, dark): party menu lists Flash (20); choose it, flag 0x888
-- NOHM=1 runs surf/cut/party/flash without the HM (control: nothing may happen); KNOWS=1 teaches the Pokemon Fly
-- first (party: Fly must be listed once, by the game). Screenshots <NAME>_*.png.
NAME = "hmfree_" .. (os.getenv("MODE") or "unit") .. (os.getenv("NOHM") == "1" and "_nohm" or "")
dofile((DIR or "./") .. "../dexnavchain/test_boot.lua")
local MODE, NOHM = os.getenv("MODE") or "unit", os.getenv("NOHM") == "1"
local SCRIPT, PARTY, VAR8004 = 0x0203F100, 0x020244EC, 0x020375E0
local HM_MOVES = {15, 19, 57, 70, 148, 249, 127, 291}
local t0, plan = nil, {}
local function at(d, fn) plan[#plan + 1] = {d, fn} end
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1)
  emu:write8(0x03000E38, 0)
end
local function lo(v) return v & 0xFF end
local function hi(v) return v >> 8 end
local function flagaddr(fl) return emu:read32(0x03005D8C) + 0x1270 + (fl >> 3) end
local function setflag(fl) local a = flagaddr(fl); emu:write8(a, emu:read8(a) | (1 << (fl & 7))) end
local function flag(fl) return (emu:read8(flagaddr(fl)) >> (fl & 7)) & 1 end
local function species(s) emu:write16(PARTY + 0x20, s) end
local function hmcount(item)
  local n = 0
  for pocket = 0, 4 do
    local base, cap = emu:read32(0x02039DD8 + pocket * 8), emu:read8(0x02039DD8 + pocket * 8 + 4)
    if base >= 0x02000000 and base < 0x03000000 and cap > 0 and cap < 250 then
      for i = 0, cap - 1 do if emu:read16(base + i * 4) == item then n = n + 1 end end
    end
  end
  return n
end
local function give(item) run({0x44, lo(item), hi(item), 1, 0, 0x02}) end
local function take(item) run({0x45, lo(item), hi(item), 1, 0, 0x02}) end
local function ask(move) run({0x16, 0x04, 0x80, lo(move), hi(move), 0x23, 0xA1, 0x1B, 0xFF, 0x08, 0x02}) end
local function actions()
  local p = emu:read32(0x0203CEC4)
  if p < 0x02000000 or p >= 0x02040000 then return "none" end
  local n, out = emu:read8(p + 0x17), {}
  for i = 0, n - 1 do out[#out + 1] = tostring(emu:read8(p + 0xF + i)) end
  return table.concat(out, ",")
end
local function where()
  local sb1 = emu:read32(0x03005D8C)
  return string.format("map %d/%d (%d,%d) cb2 %08X avatar %02X", emu:read8(sb1 + 4), emu:read8(sb1 + 5),
    emu:read16(sb1), emu:read16(sb1 + 2), cb2(), emu:read8(0x02037590))
end
local function warp(g, n, id, x, y) run({0x39, g, n, id, lo(x), hi(x), lo(y), hi(y), 0x02}) end
local function open_party(d)       -- START, cursor to POKEMON, open it, pick the first Pokemon
  at(d, function() tap(K.START) end)
  at(d + 100, function() tap(K.DOWN) end)
  at(d + 150, function() tap(K.A) end)
  at(d + 400, function() tap(K.A) end)
end

if MODE == "unit" then
  local d = 10
  at(d, function() species(129); w("party[0] = Magikarp") end)
  for k, mv in ipairs(HM_MOVES) do
    local item = 497 + k
    at(d + 20, function() take(item) end)
    at(d + 50, function() take(item) end)
    at(d + 80, function() ask(mv) end)
    at(d + 110, function() w(string.format("HM%02d move %3d without: count %d -> %d", k, mv, hmcount(item),
      emu:read16(VAR8004))) end)
    at(d + 120, function() give(item) end)
    at(d + 150, function() ask(mv) end)
    at(d + 180, function() w(string.format("HM%02d move %3d with:    count %d -> %d", k, mv, hmcount(item),
      emu:read16(VAR8004))) end)
    d = d + 180
  end
  at(d + 20, function() ask(431) end)
  at(d + 50, function() w("Rock Climb 431, Magikarp: -> " .. emu:read16(VAR8004)) end)
  at(d + 60, function() species(390); take(498) end)
  at(d + 90, function() ask(15) end)
  at(d + 120, function() w(string.format("control Chimchar, Cut, no HM01 (count %d): -> %d", hmcount(498),
    emu:read16(VAR8004))) end)
  at(d + 130, function() ask(431) end)
  at(d + 160, function() w("control Chimchar, Rock Climb: -> " .. emu:read16(VAR8004)); done() end)
else
  local cfg = ({surf = {0x86B, 500}, cut = {0x867, 498}, party = {0x86C, 499}, flash = {0x868, 502}})[MODE]
  at(10, function() species(129); setflag(cfg[1]); take(cfg[2])
    if os.getenv("KNOWS") == "1" then emu:write16(PARTY + 0x2C, 19); w("move 1 = Fly") end end)
  at(40, function() take(cfg[2]) end)
  at(70, function() if not NOHM then give(cfg[2]) end end)
  at(100, function() w(string.format("badge %X = %d, HM %d count %d", cfg[1], flag(cfg[1]), cfg[2],
    hmcount(cfg[2]))) end)
  if MODE == "surf" then
    at(110, function() warp(0, 0, 0xFF, 19, 7) end)
    at(400, function() w("warped: " .. where()); tap(K.UP) end)
    at(440, function() tap(K.A) end)
    at(600, function() shot(NAME .. "_prompt") end)
    at(620, function() tap(K.A) end)
    at(700, function() tap(K.A) end)
    at(760, function() shot(NAME .. "_yes") end)
    for k = 0, 5 do at(780 + k * 40, function() tap(K.A) end) end
    at(1300, function() w("after: " .. where() .. string.format("  surfing=%d", (emu:read8(0x02037590) >> 3) & 1))
      shot(NAME .. "_done"); done() end)
  elseif MODE == "cut" then
    at(110, function() warp(0, 17, 0xFF, 10, 7) end)
    at(400, function() w("warped: " .. where() .. "  tree flag 0x12 = " .. flag(0x12)); tap(K.RIGHT) end)
    at(440, function() tap(K.A) end)
    at(600, function() shot(NAME .. "_prompt") end)
    at(620, function() tap(K.A) end)
    at(700, function() tap(K.A) end)
    at(760, function() shot(NAME .. "_yes") end)
    for k = 0, 5 do at(780 + k * 40, function() tap(K.A) end) end
    at(1300, function() w("after: " .. where() .. "  tree flag 0x12 = " .. flag(0x12)); shot(NAME .. "_done"); done() end)
  else
    local start = 110
    if MODE == "party" then                    -- outdoors: the save starts in a Mart, where Fly is refused
      at(110, function() warp(0, 0, 0xFF, 19, 7) end)
      at(400, function() w("warped: " .. where()) end)
      start = 420
    elseif MODE == "flash" then
      at(110, function() warp(34, 71, 0, 0, 0) end)
      at(400, function() w(string.format("warped: %s  cave=%d flash flag=%d", where(), emu:read8(0x02037318 + 0x15),
        flag(0x888))); shot(NAME .. "_dark") end)
      start = 420
    end
    open_party(start)
    at(start + 600, function() w("actions: {" .. actions() .. "}"); shot(NAME .. "_actions") end)
    at(start + 620, function() tap(K.DOWN) end)
    at(start + 660, function() tap(K.DOWN) end)
    at(start + 720, function() shot(NAME .. "_cursor"); tap(K.A) end)
    at(start + 1200, function() w("chosen: " .. where() .. "  flash flag=" .. flag(0x888)); shot(NAME .. "_chosen") end)
    at(start + 1300, function() tap(K.A) end)
    at(start + 1700, function() w("end: " .. where() .. "  flash flag=" .. flag(0x888)); shot(NAME .. "_end"); done() end)
  end
end
if os.getenv("SEQ") == "1" then          -- a screenshot every 60 frames, for looking at the whole sequence
  for k = 7, 30 do at(k * 60, function() shot(string.format("%s_seq%02d", NAME, k)) end) end
end
function TEST(f)
  t0 = t0 or f
  for _, p in ipairs(plan) do if f - t0 == p[1] then p[2]() end end
end
