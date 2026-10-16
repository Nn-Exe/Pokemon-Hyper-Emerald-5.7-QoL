-- Playing the story the way a player would, one plan at a time (PLAN=<a Lua file returning a list of actions>),
-- on the save it is given (or New Game when NEWGAME=1: A through the intro, START at the naming screens).
-- Actions, in order:
--   {"warp", g, n, x, y}          travel (the test's shortcut for walking between places; logged)
--   {"enter", g, n, door}         the same, arriving through that map's door (as a player walking in)
--   {"walk", x, y}                walk to a tile of this map (a path over the map in RAM, around people);
--                                 map = "g.n": only if still on that map (a scene may have moved us on)
--   {"talk", localId}             walk next to that person of this map, face them, A
--   {"edge", dir}                 walk off this map's edge ("up", "down", "left", "right") into the next one
--   {"face", dir} / {"press", key, n[, hold]}   dir: "up" / "down" / "left" / "right"; key: "A", "B", "START", ...
--   {"expect", flag[, frames]}    keep playing (A through text, the battle player in battles) until the flag is set
--   {"expectvar", var, value[, frames]}
--   {"wait", frames}              keep playing that long
--   {"heal"}                      special HealPlayerParty (as a visit to a Pokemon Center)
--   {"grind", level[, frames]}    train in the grass here (random steps within 4 tiles, wild battles, a heal when
--                                 the lead is under 60%) until the lead reaches that level
--   {"team", {species...}, level} the party made these, at that level (the test's stand-in for training)
--   {"setflag", flag}             (only for what a player would have done off-plan, logged)
--   {"settle"}                    A through any text until the field is free and the player stands still
--   {"save"}                      START -> Save -> yes (the save of the next plan), once the field is free
--   {"shot", name}
-- In battle (any time): at the action menu FIGHT and the move that hurts the foe most (power x type x STAB, PP
-- left); every message A or B at random (B says No to "forget a move?", A gets through the rest; the soak showed
-- the mix never sticks); a fainted Pokemon replaced by the next one standing. Out of battle, while a script holds
-- the field, A every 20 frames; naming screens get START + A.
-- Logged: each action as it starts and ends (frame, map, position), every battle (foe, outcome), every flag the plan
-- expects; FAIL lines when an action times out. Shots: each action's end, every battle's start, failures.
local E = os.getenv
DIR = E("GEN9_DIR")
NAME = (E("TAG") or "pl") .. "_play"
if E("NEWGAME") == "1" then
  local NL = string.char(10)
  LOG = io.open(DIR .. NAME .. "_log.txt", "w")
  function w(s) LOG:write(s .. NL); LOG:flush() end
  function done() local fh = io.open(DIR .. NAME .. "_done.txt", "w"); fh:write("done"); fh:close() end
  function shot(n) emu:screenshot(DIR .. n .. ".png") end
  K = {A = 0, B = 1, SEL = 2, START = 3, RIGHT = 4, LEFT = 5, UP = 6, DOWN = 7, R = 8, L = 9}
  OVERWORLD, BATTLE = 0x08085E5D, 0x08038421
  function cb2() return emu:read32(0x030022C4) end
  function lock() return emu:read8(0x03000F2C) end
  local rel, fr = {}, 0
  function tap(k, len) emu:addKey(k); rel[k] = fr + (len or 6) end
  callbacks:add("frame", function()
    fr = fr + 1
    for k, t in pairs(rel) do if fr >= t then emu:clearKey(k); rel[k] = nil end end
    if TEST then TEST(fr) end
  end)
else
  dofile("C:/Users/nonth/Desktop/Works & Productivity/gba-trans/hyper-emerald-en-qol/patches/dexnavchain/test_boot.lua")
end
local PLAN = dofile(E("PLAN"))
math.randomseed(tonumber(E("SEED") or "1"))
local SCRIPT, PARTY, MONS, ACTION, ABIL16 = 0x0203F100, 0x020244EC, 0x02024084, 0x08057589, 0x0203F000
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
local function flag(f) return (emu:read8(flagbyte(f)) >> (f & 7)) & 1 end
local function setflag(f) local a = flagbyte(f); emu:write8(a, emu:read8(a) | (1 << (f & 7))) end
local function var(v) return emu:read16(sb1() + 0x139C + (v - 0x4000) * 2) end
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1); emu:write8(0x03000E38, 0)
end
local function mapgn() return emu:read8(sb1() + 4), emu:read8(sb1() + 5) end
local function player()
  local id = emu:read8(0x02037590 + 5)
  local o = 0x02037350 + 0x24 * id
  return emu:read16(o + 0x10), emu:read16(o + 0x12), emu:read8(o + 0x18) & 0x0F
end
local DIRK = {up = K.UP, down = K.DOWN, left = K.LEFT, right = K.RIGHT}
local FACING = {down = 1, up = 2, left = 3, right = 4}
local function idle() return emu:read8(0x02037590 + 2) == 0 end   -- gPlayerAvatar.runningState: NOT_MOVING
local KEYS = {A = K.A, B = K.B, START = K.START, SEL = K.SEL, R = K.R, L = K.L, UP = K.UP, DOWN = K.DOWN, LEFT = K.LEFT, RIGHT = K.RIGHT}

-- ---------------------------------------------------------------- the map and the way through it
local WATER = {[0x10] = 1, [0x11] = 1, [0x12] = 1, [0x14] = 1, [0x15] = 1, [0x17] = 1, [0x19] = 1, [0x1A] = 1}
local behCache, behLay = {}, nil
local function behaviour(mt)                     -- a metatile's behaviour (cached per layout)
  local lay = emu:read32(0x02037318)
  if lay ~= behLay then behCache = {}; behLay = lay end
  local v = behCache[mt]
  if v then return v end
  local ts = emu:read32(lay + (mt < 512 and 0x10 or 0x14))
  v = emu:read16(emu:read32(ts + 0x10) + 2 * (mt < 512 and mt or mt - 512)) & 0xFF
  behCache[mt] = v
  return v
end
local gridCache = {key = nil, at = 0, blk = nil}
local frameNow = 0
local function grid()                            -- the map's blocks (gBackupMapLayout), read again on a new map or
  local w, h, map = emu:read32(0x03005DC0), emu:read32(0x03005DC4), emu:read32(0x03005DC8)   -- every 300 frames
  local key = string.format("%d.%d.%d.%d", w, h, map, emu:read32(0x02037318))
  if gridCache.key ~= key or frameNow - gridCache.at > 300 then
    local t = {}
    local raw = emu:readRange(map, 2 * w * h)
    for i = 0, w * h - 1 do t[i] = raw:byte(2 * i + 1) | (raw:byte(2 * i + 2) << 8) end
    gridCache = {key = key, at = frameNow, blk = t, w = w, h = h}
  end
  return gridCache.blk, gridCache.w, gridCache.h
end
local function people()                         -- tiles taken by someone (map coordinates + 7), the player left out
  local t, me = {}, emu:read8(0x02037590 + 5)
  for i = 0, 15 do
    local o = 0x02037350 + 0x24 * i
    if i ~= me and (emu:read8(o) & 1) == 1 then t[emu:read16(o + 0x12) * 4096 + emu:read16(o + 0x10)] = i end
  end
  return t
end
local function path(tx, ty, adjacent)            -- steps (keys) from the player to (tx,ty) or, adjacent, next to it
  local G, w, h = grid()
  local sx, sy = player()
  local surf = (emu:read8(0x02037590) & 0x08) ~= 0
  local occ = people()
  local function goal(x, y)
    if type(tx) == "function" then return tx(x, y) end   -- any test: the nearest tile that passes it
    if adjacent == "edge" then                   -- tx = the edge: past the map, in the neighbour's rows
      local mw, mh = emu:read32(emu:read32(0x02037318)), emu:read32(emu:read32(0x02037318) + 4)
      if tx == "up" then return y < 7 elseif tx == "down" then return y >= 7 + mh
      elseif tx == "left" then return x < 7 else return x >= 7 + mw end
    end
    if adjacent then return math.abs(x - tx) + math.abs(y - ty) == 1 end
    return x == tx and y == ty
  end
  local lay = emu:read32(0x02037318)
  local mw, mh = emu:read32(lay), emu:read32(lay + 4)
  local function ok(x, y)
    if x < 0 or y < 0 or x >= w or y >= h then return false end
    local inx, iny = x >= 7 and x < 7 + mw, y >= 7 and y < 7 + mh
    if not (inx and iny) then                    -- outside the map: only the strip past the edge being crossed
      if adjacent ~= "edge" then return false end
      if tx == "up" and not (inx and y < 7) then return false end
      if tx == "down" and not (inx and y >= 7 + mh) then return false end
      if tx == "left" and not (iny and x < 7) then return false end
      if tx == "right" and not (iny and x >= 7 + mw) then return false end
    end
    if x == tx and y == ty and adjacent == false then return true end -- the goal itself (a door has collision)
    if occ[y * 4096 + x] then return false end
    local b = G[y * w + x]
    if (b >> 10) & 3 ~= 0 then return false end
    local beh = behaviour(b & 0x3FF)
    if beh >= 0x60 and beh <= 0x6F and not (x == tx and y == ty) then return false end   -- doors and warps
    return (WATER[beh] ~= nil) == surf
  end
  local function ledge(x, y)                     -- the tile's jump direction (0x38 E, 0x39 W, 0x3A N, 0x3B S) or nil
    if x < 0 or y < 0 or x >= w or y >= h then return nil end
    local beh = behaviour(G[y * w + x] & 0x3FF)
    if beh >= 0x38 and beh <= 0x3B then return beh end
  end
  local function elev(x, y) return (G[y * w + x] >> 12) & 0xF end
  local function canStep(ce, x, y)               -- the game's elevation rule: 0 and 15 go with anything
    if x == tx and y == ty and adjacent == false then return true end       -- the goal (a door) itself
    local te = elev(x, y)
    if ce == 0 or ce == 15 or te == 0 or te == 15 then return true end
    return ce == te
  end
  local function after(ce, x, y) local te = elev(x, y); if te == 15 then return ce end; return te end
  local start = sy * 4096 + sx
  local me = emu:read8(0x02037350 + 0x24 * emu:read8(0x02037590 + 5) + 0xB) & 0xF   -- the player's elevation
  local el = {[start] = me}
  local prev, q, head = {[start] = -1}, {start}, 1
  while head <= #q do
    local c = q[head]; head = head + 1
    local x, y = c % 4096, c // 4096
    if goal(x, y) then
      local steps = {}
      while prev[c] ~= -1 do
        local p = prev[c]
        local px, py = p % 4096, p // 4096
        table.insert(steps, 1, (x > px and K.RIGHT) or (x < px and K.LEFT) or (y > py and K.DOWN) or K.UP)
        c = p; x, y = px, py
      end
      return steps
    end
    for _, dv in ipairs({{1, 0, 0x38}, {-1, 0, 0x39}, {0, -1, 0x3A}, {0, 1, 0x3B}}) do   -- the ledge each way jumps
      local nx, ny = x + dv[1], y + dv[2]
      local led = ledge(nx, ny)
      local ce = el[c] or me
      if led then                                -- a ledge: only jumped over, in its own direction, to the tile past it
        if led == dv[3] then
          local jx, jy = nx + dv[1], ny + dv[2]
          local k = jy * 4096 + jx
          if prev[k] == nil and #q < 30000 and ok(jx, jy) then prev[k] = c; el[k] = after(ce, jx, jy); q[#q + 1] = k end
        end
      else
        local k = ny * 4096 + nx
        if prev[k] == nil and #q < 30000 and ok(nx, ny) and nx >= 0 and ny >= 0 and nx < w and ny < h and canStep(ce, nx, ny) then
          prev[k] = c; el[k] = after(ce, nx, ny); q[#q + 1] = k
        end
      end
    end
  end
end
local function templateAt(localId)               -- where the map puts that person (gMapHeader.events' templates)
  local ev = emu:read32(0x02037318 + 4)
  local n, list = emu:read8(ev), emu:read32(ev + 4)
  for i = 0, n - 1 do
    local o = list + 24 * i
    if emu:read8(o) == localId then return emu:read16(o + 4) + 7, emu:read16(o + 6) + 7 end
  end
end
local function personAt(localId)                 -- that person's tile (map coordinates + 7)
  local g, n = mapgn()
  for i = 0, 15 do
    local o = 0x02037350 + 0x24 * i
    if (emu:read8(o) & 1) == 1 and emu:read8(o + 8) == localId and emu:read8(o + 9) == n and emu:read8(o + 10) == g then
      return emu:read16(o + 0x10), emu:read16(o + 0x12)
    end
  end
end

local function dumpMap(r)                       -- the map as the walker sees it: # wall, P person, D door, ~ water, L ledge
  local w_, h_, map = emu:read32(0x03005DC0), emu:read32(0x03005DC4), emu:read32(0x03005DC8)
  local px, py = player()
  local occ = people()
  w(string.format("    map %dx%d, player %d,%d (avatar %02X)", w_, h_, px - 7, py - 7, emu:read8(0x02037590)))
  for y = math.max(0, py - r), math.min(h_ - 1, py + r) do
    local row = {}
    for x = math.max(0, px - r), math.min(w_ - 1, px + r) do
      local b = emu:read16(map + 2 * (y * w_ + x))
      local beh = behaviour(b & 0x3FF)
      local c = "."
      if (b >> 10) & 3 ~= 0 then c = "#" end
      if beh >= 0x60 and beh <= 0x6F then c = "D" end
      if beh >= 0x38 and beh <= 0x3B then c = "L" end
      if WATER[beh] then c = "~" end
      if occ[y * 4096 + x] then c = "P" end
      if x == px and y == py then c = "@" end
      row[#row + 1] = c
    end
    w(string.format("    %3d %s", y - 7, table.concat(row)))
  end
  for y = math.max(0, py - 3), math.min(h_ - 1, py + 3) do
    local row = {}
    for x = math.max(0, px - r), math.min(w_ - 1, px + r) do
      row[#row + 1] = string.format("%X", (emu:read16(map + 2 * (y * w_ + x)) >> 12) & 0xF)
    end
    w(string.format("    z%3d %s", y - 7, table.concat(row)))
  end
  for i = 0, 15 do
    local o = 0x02037350 + 0x24 * i
    if (emu:read8(o) & 1) == 1 then
      w(string.format("    person: local %d at %d,%d gfx %d", emu:read8(o + 8), emu:read16(o + 0x10) - 7, emu:read16(o + 0x12) - 7, emu:read8(o + 5)))
    end
  end
end

-- ---------------------------------------------------------------- the battle player
local MOVES_T = emu:read32(0x080001CC)           -- move data: 12 bytes, power +1, type +2
local CHART = {}                                 -- attack type -> {defending type -> multiplier}, the game's ids
do
  local N = {Normal = 0, Fighting = 1, Flying = 2, Poison = 3, Ground = 4, Rock = 5, Bug = 6, Ghost = 7, Steel = 8,
             Fire = 10, Water = 11, Grass = 12, Electric = 13, Psychic = 14, Ice = 15, Dragon = 16, Dark = 17, Fairy = 23}
  local rows = {
    Normal = {Rock = .5, Ghost = 0, Steel = .5},
    Fighting = {Normal = 2, Flying = .5, Poison = .5, Rock = 2, Bug = .5, Ghost = 0, Steel = 2, Psychic = .5, Ice = 2, Dark = 2, Fairy = .5},
    Flying = {Fighting = 2, Rock = .5, Bug = 2, Steel = .5, Grass = 2, Electric = .5},
    Poison = {Poison = .5, Ground = .5, Rock = .5, Ghost = .5, Steel = 0, Grass = 2, Fairy = 2},
    Ground = {Flying = 0, Poison = 2, Rock = 2, Bug = .5, Steel = 2, Fire = 2, Grass = .5, Electric = 2},
    Rock = {Fighting = .5, Flying = 2, Ground = .5, Bug = 2, Steel = .5, Fire = 2, Ice = 2},
    Bug = {Fighting = .5, Flying = .5, Poison = .5, Ghost = .5, Steel = .5, Fire = .5, Grass = 2, Psychic = 2, Dark = 2, Fairy = .5},
    Ghost = {Normal = 0, Ghost = 2, Psychic = 2, Dark = .5},
    Steel = {Rock = 2, Steel = .5, Fire = .5, Water = .5, Electric = .5, Ice = 2, Fairy = 2},
    Fire = {Rock = .5, Bug = 2, Steel = 2, Fire = .5, Water = .5, Grass = 2, Ice = 2, Dragon = .5},
    Water = {Ground = 2, Rock = 2, Fire = 2, Water = .5, Grass = .5, Dragon = .5},
    Grass = {Flying = .5, Poison = .5, Ground = 2, Rock = 2, Bug = .5, Steel = .5, Fire = .5, Water = 2, Grass = .5, Dragon = .5},
    Electric = {Flying = 2, Ground = 0, Water = 2, Grass = .5, Electric = .5, Dragon = .5},
    Psychic = {Fighting = 2, Poison = 2, Steel = .5, Psychic = .5, Dark = 0},
    Ice = {Flying = 2, Ground = 2, Steel = .5, Fire = .5, Water = .5, Grass = 2, Ice = .5, Dragon = 2},
    Dragon = {Steel = .5, Dragon = 2, Fairy = 0},
    Dark = {Fighting = .5, Ghost = 2, Psychic = 2, Dark = .5, Fairy = .5},
    Fairy = {Fighting = 2, Poison = .5, Steel = .5, Fire = .5, Dragon = 2, Dark = 2},
  }
  for an, r in pairs(rows) do
    local t = {}
    for dn, m in pairs(r) do t[N[dn]] = m end
    CHART[N[an]] = t
  end
end
local function eff(mt, d1, d2)
  local r = CHART[mt] or {}
  local m = (r[d1] or 1)
  if d2 ~= d1 then m = m * (r[d2] or 1) end
  return m
end
local function bestMove()                        -- slot 0-3 of our battler 0 against battler 1
  local me, foe = MONS, MONS + 0x58
  local t1, t2 = emu:read8(me + 0x21), emu:read8(me + 0x22)
  local d1, d2 = emu:read8(foe + 0x21), emu:read8(foe + 0x22)
  local best, bs, attack = 0, -1, false
  for k = 0, 3 do
    local mv, pp = emu:read16(me + 0x0C + 2 * k), emu:read8(me + 0x24 + k)
    if mv ~= 0 and pp > 0 then
      local pw, ty = emu:read8(MOVES_T + 12 * mv + 1), emu:read8(MOVES_T + 12 * mv + 2)
      local s = (pw == 1 and 60 or pw) * eff(ty, d1, d2) * ((ty == t1 or ty == t2) and 1.5 or 1) + k * 0.01
      if pw == 0 then s = 0.5 else attack = true end
      if s > bs then bs = s; best = k end
    end
  end
  return best, attack
end

-- the screens that are not the field or a battle, and the keys that get a player through each, in turn
SCREENS = {
  [0x08134C9D] = {K.UP, K.A},                    -- the wall clock: "Is this the correct time?" Yes is on top
  [0x081B01B1] = {K.B, K.B, K.DOWN, K.A, K.A},   -- the party screen in battle: B out of a stray visit; a fainted
                                                 --  one to replace: B does nothing, the next one goes in (Shift)
}
screensSeen = {}

-- ---------------------------------------------------------------- the runner of actions
local t0, ai, astart, phase, mark, sub = nil, 1, 0, "boot", 0, {}
local inBattle, battles, lastStep, stepTries = false, 0, nil, 0
battlesAtStart = 0
pendingHeal, healAt, heals = false, nil, 0
local function A() return PLAN[ai] end
local function where() local g, n = mapgn(); local x, y = player(); return string.format("%d.%d %d,%d", g, n, x - 7, y - 7) end
local function finish(msg) w(msg); shot(NAME .. "_end"); phase = "over"; done() end
local function nextAction(d, ok, msg)
  local a = A()
  w(string.format("  [%d] %s %s at +%d frames (%s)%s", ai, a[1], ok and "done" or "FAIL", d - astart, where(), msg and (": " .. msg) or ""))
  shot(string.format("%s_a%03d", NAME, ai))
  if not ok then
    if a[1] == "walk" or a[1] == "edge" or a[1] == "talk" then dumpMap(9) end
    finish(string.format("stopped at action %d (FAIL)", ai)); return
  end
  ai = ai + 1; sub = {}; astart = d; battlesAtStart = battles
  if not PLAN[ai] then finish(string.format("plan done: %d actions, %d battles (PASS)", #PLAN, battles)) end
end
local function battleTick(d)
  if not inBattle then
    inBattle = true; battles = battles + 1; sub.bmark = d
    w(string.format("    battle %d at %s: foe species %d lv %d (type %08X)", battles, where(), emu:read16(0x02024744 + 0x20),
      emu:read8(0x02024744 + 0x54), emu:read32(0x02022FEC)))
    shot(string.format("%s_b%03d", NAME, battles))
  end
  if sub.choosing then                           -- a move being chosen: FIGHT, the D-pad to it, A - to the end
    local k = d - sub.choosing
    if k == 4 then tap(K.UP) end                                -- the action menu keeps its cursor: to FIGHT
    if k == 12 then tap(K.LEFT) end                             --  (top left) first
    if k == 20 then tap(K.A) end                                -- FIGHT
    if k == 45 and emu:read32(0x03005D60) ~= 0x08057BFD then    -- the move list did not open: start again
      sub.choosing = nil; sub.chosenAt = d - 30; return
    end
    if k == 50 then tap(K.UP) end                               -- the 2 x 2 move grid: to the first move,
    if k == 62 then tap(K.LEFT) end                             --  right for the 2nd / 4th, down for the 3rd / 4th
    if k == 74 and sub.slot % 2 == 1 then tap(K.RIGHT) end
    if k == 86 and sub.slot >= 2 then tap(K.DOWN) end
    if k == 104 then tap(K.A) end
    if k >= 130 then sub.choosing = nil; sub.chosenAt = d end
    return
  end
  if sub.running then                            -- RUN: bottom right of the action menu
    local k = d - sub.running
    if k == 4 then tap(K.DOWN) end
    if k == 12 then tap(K.RIGHT) end
    if k == 20 then tap(K.A) end
    if k >= 60 then sub.running = nil; sub.chosenAt = d end
    return
  end
  if emu:read32(0x03005D60) == ACTION and (not sub.chosenAt or d - sub.chosenAt > 40) then
    local slot, attack = bestMove()
    if not attack and (emu:read32(0x02022FEC) & 0x08) == 0 then     -- a wild battle, nothing to hit with: run
      sub.running = d; w("      turn: no attack left - Run"); return
    end
    sub.choosing = d; sub.slot = slot
    local me, foe = MONS, MONS + 0x58
    w(string.format("      turn: ours %d HP %d/%d vs %d HP %d/%d, slot %d (move %d) of %d %d %d %d", emu:read16(me),
      emu:read16(me + 0x28), emu:read16(me + 0x2C), emu:read16(foe), emu:read16(foe + 0x28), emu:read16(foe + 0x2C), sub.slot,
      emu:read16(me + 0x0C + 2 * sub.slot), emu:read16(me + 0x0C), emu:read16(me + 0x0E), emu:read16(me + 0x10), emu:read16(me + 0x12)))
    return
  end
  if emu:read32(0x03005D60) ~= ACTION and d % 18 == 0 then tap(math.random() < 0.55 and K.A or K.B) end
end
local function fieldTalk(d)                      -- a script holds the field: through its text
  if d % 20 == 0 then tap(K.A) end
end
-- the story's state: every var 0x4000-0x40FF and every flag (all four areas) that changes, logged as it changes
local seenVars, seenFlags = nil, nil
local QUIETVARS = {[0x402A] = true, [0x402B] = true}   -- step counters: they change with every step
local FLAG_AREAS = {{0x0000, function() return sb1() + 0x1270 end, 0x12C}, {0x4000, function() return sb1() + 0x988 end, 0x34},
                    {0x41A0, function() return sb1() + 0x3B24 end, 0x34}, {0x4340, function() return sb2() + 0x5C end, 0x34},
                    {0x44E0, function() return sb2() + 0x28 end, 0x34}}
local function watch(d)
  local vs, fs = {}, {}
  for v = 0, 255 do vs[v] = emu:read16(sb1() + 0x139C + 2 * v) end
  for _, ar in ipairs(FLAG_AREAS) do
    local base = ar[2]()
    for i = 0, ar[3] - 1 do fs[ar[1] + 8 * i] = emu:read8(base + i) end
  end
  if seenVars then
    local ch = {}
    for v = 0, 255 do if vs[v] ~= seenVars[v] and not QUIETVARS[0x4000 + v] then ch[#ch + 1] = string.format("var %04X %d->%d", 0x4000 + v, seenVars[v], vs[v]) end end
    for f0, b in pairs(fs) do
      local o = seenFlags[f0]
      if o and o ~= b then
        for k = 0, 7 do
          if ((b ~ o) >> k) & 1 == 1 then ch[#ch + 1] = string.format("flag %04X %s", f0 + k, ((b >> k) & 1 == 1) and "set" or "cleared") end
        end
      end
    end
    if #ch > 0 and #ch < 60 then w(string.format("      state at %s: %s", where(), table.concat(ch, ", "))) end
    if #ch >= 60 then w(string.format("      state at %s: %d changes (a load)", where(), #ch)) end
  end
  seenVars, seenFlags = vs, fs
end
function TEST(f)
  t0 = t0 or f
  local d = f - t0
  if phase == "over" then return end
  frameNow = d
  if phase ~= "boot" and d % 30 == 0 then watch(d) end
  if phase == "boot" then
    if E("NEWGAME") == "1" then                  -- through the intro to the field
      if cb2() == OVERWORLD and lock() == 0 then sub.still = (sub.still or 0) + 1 else sub.still = 0 end
      if sub.still > 240 then w("New Game: on the field at " .. where()); phase = "go"; astart = d; return end
      if cb2() == OVERWORLD then                 -- on the field only B: it moves text on and closes any menu
        if lock() ~= 0 and d % 25 == 0 then tap(K.B) end
      else                                       -- the intro's screens; START for the naming screen's OK
        if d % 25 == 0 then tap(K.A) end
        if d % 400 == 200 then tap(K.START) end
      end
      if d > 60000 then finish("never reached the field (FAIL)") end
      return
    end
    if d > 30 then w("Continue: on the field at " .. where()); phase = "go"; astart = d end
    return
  end
  local cb = cb2()
  if cb == BATTLE then battleTick(d); return end
  if inBattle and cb ~= OVERWORLD then           -- a screen inside or after the battle (the party, an evolution:
    local keys = SCREENS[cb] or {K.A}            --  A only - B would stop the evolution)
    if not SCREENS[cb] and not screensSeen[cb] then
      screensSeen[cb] = true; w(string.format("    a screen in a battle, not in the table: %08X (A)", cb))
    end
    if d % 30 == 0 then sub.bk = ((sub.bk or 0) % #keys) + 1; tap(keys[sub.bk]) end
    return
  end
  if inBattle then
    inBattle = false
    w(string.format("    battle %d over: outcome %d, back at %s", battles, emu:read8(0x0202433A), where()))
    pendingHeal = true
  end
  if pendingHeal and cb == OVERWORLD and lock() == 0 then   -- after a battle: under half HP, a Pokemon Center visit
    pendingHeal = false
    do                                           -- and the strongest one in front, as a player would put it
      local best, bl = 0, emu:read8(PARTY + 0x54)
      for i = 1, emu:read8(0x020244E9) - 1 do
        local m = PARTY + 100 * i
        local egg = (emu:read32(m + 0x48) >> 30) & 1
        if egg == 0 and emu:read8(m + 0x54) > bl and emu:read16(m + 0x56) > 0 then best, bl = i, emu:read8(m + 0x54) end
      end
      if best > 0 then
        local a, b = emu:readRange(PARTY, 100), emu:readRange(PARTY + 100 * best, 100)
        for k = 0, 99 do emu:write8(PARTY + k, b:byte(k + 1)); emu:write8(PARTY + 100 * best + k, a:byte(k + 1)) end
        w(string.format("    party: slot %d (Lv %d) put in front", best + 1, bl))
      end
    end
    local hp, mhp = emu:read16(PARTY + 0x56), emu:read16(PARTY + 0x58)
    local pp = 0
    for k = 0, 3 do
      local mv = emu:read16(PARTY + 0x2C + 2 * k)
      if mv ~= 0 and emu:read8(MOVES_T + 12 * mv + 1) > 0 then pp = pp + emu:read8(PARTY + 0x34 + k) end
    end
    if mhp > 0 and (hp * 2 < mhp or pp < 5) and E("NOHEAL") ~= "1" then
      run({0x25, 0x00, 0x00, 0x02}); healAt = d; heals = heals + 1
      w(string.format("    healed (lead %d/%d HP, %d PP to attack): a Pokemon Center visit, %d so far", hp, mhp, pp, heals))
    end
  end
  if healAt and d - healAt == 30 then emu:write8(0x03000F2C, 0); healAt = nil end
  local a = A()
  if not a then return end
  local op, age = a[1], d - astart
  if age == 0 then w(string.format("  [%d] %s %s", ai, op, table.concat({tostring(a[2] or ""), tostring(a[3] or ""), tostring(a[4] or ""), tostring(a[5] or "")}, " "))) end
  if cb ~= OVERWORLD then                        -- a screen of its own: the keys it wants (SCREENS), else A
    local keys = SCREENS[cb] or {K.A}
    if not SCREENS[cb] and not screensSeen[cb] then
      screensSeen[cb] = true; shot(string.format("%s_screen_%08X", NAME, cb)); w(string.format("    a screen not in the table: %08X", cb))
    end
    if d % 30 == 0 then sub.k = ((sub.k or 0) % #keys) + 1; tap(keys[sub.k]) end
    sub.inScreen = (sub.lastcb == cb) and (sub.inScreen or 0) + 1 or 0
    sub.lastcb = cb
    if sub.inScreen == 1800 then                 -- half a minute in one screen: what is the game doing?
      local t = {}
      for i = 0, 15 do
        local tk = 0x03005E00 + 0x28 * i
        if emu:read8(tk + 4) ~= 0 then t[#t + 1] = string.format("%08X", emu:read32(tk)) end
      end
      w(string.format("    LONG in callback %08X: callback1 %08X, pc %08X, lock %d, field %s, tasks %s", cb,
        emu:read32(0x030022C0), emu:read32(0x030022C0 + 0) and emu:readRegister("pc") or 0, lock(), where(), table.concat(t, " ")))
      shot(string.format("%s_long_%d", NAME, d))
    end
    if sub.inScreen > 20000 then nextAction(d, false, string.format("stuck in callback %08X", cb)) end
    return
  end
  sub.inScreen, sub.lastcb = 0, nil
  local free = lock() == 0
  if op == "warp" or op == "enter" then          -- enter: through that map's door number a[4] (where a player arrives)
    local wid, x, y = 0xFF, a[4] or 0, a[5] or 0
    if op == "enter" then wid, x, y = a[4] or 0, 0, 0 end
    if age == 2 then run({0x39, a[2], a[3], wid, x & 0xFF, x >> 8, y & 0xFF, y >> 8, 0x02}) end
    if age > 120 and free then
      local g, n = mapgn()
      nextAction(d, g == a[2] and n == a[3], g == a[2] and n == a[3] and nil or "not on the map")
    end
  elseif op == "walk" or op == "talk" then
    if not free then fieldTalk(d); if sub.seen then sub.engaged = true end; return end
    if a.map then                                -- only on that map ("g.n"): a scene may already have moved us on
      local g, n = mapgn()
      if string.format("%d.%d", g, n) ~= a.map then nextAction(d, true, "not on " .. a.map .. ": passed over"); return end
    end
    do                                           -- a walk through a door ends on the other side
      local g, n = mapgn()
      sub.startmap = sub.startmap or (g * 256 + n)
      if g * 256 + n ~= sub.startmap then nextAction(d, true, "through to another map"); return end
    end
    if d % 6 ~= 0 then return end
    local x, y = player()
    local tx, ty
    if op == "walk" then tx, ty = a[2] + 7, a[3] + 7
    else
      tx, ty = personAt(a[2])
      if tx then sub.seen = true end
      if not tx and sub.seen and (sub.engaged or battlesAtStart ~= battles) then
        nextAction(d, true, "the event happened and they left"); return
      end
      if not tx then                             -- not loaded yet (people appear near the camera): toward the
        local px, py = templateAt(a[2])          --  map's place for them
        if not px then nextAction(d, false, "no such person on this map"); return end
        local st = path(px, py, true)
        if st and #st > 0 then tap(st[1], 10); sub.moving = d end
        if age > 30000 then nextAction(d, false, "never found them") end
        return
      end
    end
    if op == "walk" and x == tx and y == ty then
      if idle() then sub.still = (sub.still or 0) + 1 else sub.still = 0 end
      if sub.still >= 3 then nextAction(d, true) end
      return
    end
    if op == "talk" and math.abs(x - tx) + math.abs(y - ty) == 1 and not sub.talked then
      if not idle() then return end
      local want = (tx > x and 4) or (tx < x and 3) or (ty > y and 1) or 2
      local _, _, facing = player()
      if facing ~= want then tap(({K.DOWN, K.UP, K.LEFT, K.RIGHT})[want], 3); return end
      sub.faced = (sub.faced or 0) + 1
      if sub.faced >= 3 then tap(K.A); sub.talked = d end
      return
    end
    if sub.talked then
      if d - sub.talked > 60 and free then nextAction(d, true) end
      return
    end
    if sub.moving and d - sub.moving < 20 then return end
    local steps = path(tx, ty, op == "talk")
    if not steps or #steps == 0 then
      stepTries = stepTries + 1
      if stepTries > 300 then nextAction(d, false, "no way there"); stepTries = 0 end
      return
    end
    stepTries = 0
    tap(steps[1], 10); sub.moving = d
    if age > 30000 then nextAction(d, false, "too long") end
  elseif op == "edge" then                       -- {"edge", dir}: walk off this map's edge into the next map
    if not free then fieldTalk(d); return end
    local g, n = mapgn()
    sub.startmap = sub.startmap or (g * 256 + n)
    if g * 256 + n ~= sub.startmap then
      if idle() then nextAction(d, true, string.format("into %d.%d", g, n)) end
      return
    end
    if d % 6 ~= 0 or (sub.moving and d - sub.moving < 20) then return end
    local steps = path(a[2], nil, "edge")
    if not steps or #steps == 0 then
      tap(DIRK[a[2]], 16); sub.moving = d                 -- at the edge already: push on
      stepTries = stepTries + 1
      if stepTries > 300 then stepTries = 0; nextAction(d, false, "no way to the edge") end
      return
    end
    stepTries = 0
    if age % 1000 < 6 then
      local names = {[K.UP] = "U", [K.DOWN] = "D", [K.LEFT] = "L", [K.RIGHT] = "R"}
      local t = {}; for i = 1, math.min(#steps, 12) do t[#t + 1] = names[steps[i]] end
      local x, y = player()
      w(string.format("      edge %s: at %d,%d, %d steps: %s", a[2], x - 7, y - 7, #steps, table.concat(t)))
    end
    tap(steps[1], 10); sub.moving = d
    if age > 30000 then nextAction(d, false, "too long") end
  elseif op == "grind" then                      -- {"grind", level[, frames]}: train in the grass around here
    if not free then fieldTalk(d); return end
    local lv, hp, mhp = emu:read8(PARTY + 0x54), emu:read16(PARTY + 0x56), emu:read16(PARTY + 0x58)
    if lv >= a[2] then nextAction(d, true, string.format("the lead is Lv %d", lv)); return end
    if mhp > 0 and hp * 10 < mhp * 6 and not sub.healing then          -- a Pokemon Center visit
      run({0x25, 0x00, 0x00, 0x02}); sub.healing = d; sub.heals = (sub.heals or 0) + 1; return
    end
    if sub.healing and d - sub.healing > 30 then emu:write8(0x03000F2C, 0); sub.healing = nil end
    if sub.healing then return end
    if age % 3000 == 0 then
      local x, y = player()
      w(string.format("      grind: Lv %d, at %d,%d, free %s, avatar %02X %02X %02X %02X", lv, x - 7, y - 7, tostring(free),
        emu:read8(0x02037590), emu:read8(0x02037591), emu:read8(0x02037592), emu:read8(0x02037593)))
    end
    if d % 6 ~= 0 or (sub.moving and d - sub.moving < 24) or not idle() then return end
    local x, y = player()
    local G, w_, h_ = grid()
    local occ = people()
    local function grass(tx, ty)                 -- tall grass (0x02) or long grass (0x03), free of people
      if tx < 0 or ty < 0 or tx >= w_ or ty >= h_ then return false end
      local b = G[ty * w_ + tx]
      local bh = behaviour(b & 0x3FF)
      return (bh == 0x02 or bh == 0x03) and (b >> 10) & 3 == 0 and not occ[ty * 4096 + tx]
    end
    local dirs = {{K.UP, 0, -1}, {K.DOWN, 0, 1}, {K.LEFT, -1, 0}, {K.RIGHT, 1, 0}}
    local opts = {}
    for _, dv in ipairs(dirs) do if grass(x + dv[2], y + dv[3]) then opts[#opts + 1] = dv end end
    if #opts > 0 then
      local pick = opts[math.random(#opts)]
      tap(pick[1], 16); sub.moving = d
    else                                         -- not in the grass: to the nearest patch one can walk to
      local st = path(grass, nil, false)
      if not st then nextAction(d, false, "no grass to walk to"); return end
      if #st > 0 then tap(st[1], 10); sub.moving = d end
    end
    if age > (a[3] or 60000) then nextAction(d, false, string.format("still Lv %d", lv)) end
  elseif op == "face" then
    if d % 6 ~= 0 or not idle() then return end
    local _, _, facing = player()
    if facing == FACING[a[2]] then nextAction(d, true) else tap(DIRK[a[2]], 3) end
    if age > 600 then nextAction(d, false, "could not turn") end
  elseif op == "press" then
    local n, hold = a[3] or 1, a[4] or 6           -- {"press", key, times, frames held}
    local gap = math.max(30, hold + 20)
    if age % gap == 2 and age // gap < n then tap(KEYS[a[2]], hold) end
    if age >= gap * n + 20 then nextAction(d, true) end
  elseif op == "expect" or op == "expectvar" then
    local ok = (op == "expect") and flag(a[2]) == 1 or (op == "expectvar" and var(a[2]) == a[3])
    if ok then nextAction(d, true, op == "expect" and string.format("flag %04X set", a[2]) or string.format("var %04X = %d", a[2], a[3])); return end
    if not free then fieldTalk(d) end
    local lim = (op == "expect") and (a[3] or 6000) or (a[4] or 6000)
    if age > lim then nextAction(d, false, op == "expect" and string.format("flag %04X never set", a[2]) or string.format("var %04X = %d", a[2], var(a[2]))) end
  elseif op == "wait" then
    if not free then fieldTalk(d) end
    if age >= a[2] then nextAction(d, true) end
  elseif op == "heal" then
    if age == 2 then run({0x25, 0x00, 0x00, 0x02}) end
    if age == 30 then emu:write8(0x03000F2C, 0) end
    if age > 40 then nextAction(d, true) end
  elseif op == "team" then
    if age == 2 then emu:write8(0x020244E9, 0); for i = 0, 599 do emu:write8(PARTY + i, 0) end end
    local k = (age - 4) // 25
    if age >= 4 and (age - 4) % 25 == 0 and a[2][k + 1] then
      local sp = a[2][k + 1]; run({0x79, sp & 0xFF, sp >> 8, a[3], 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0x02})
    end
    if age == 4 + 25 * #a[2] + 10 then
      emu:write8(0x03000F2C, 0)
      local t = {}; for i = 0, 5 do t[#t + 1] = emu:read16(PARTY + 100 * i + 0x20) .. "/" .. emu:read8(PARTY + 100 * i + 0x54) end
      nextAction(d, true, "party " .. table.concat(t, " "))
    end
  elseif op == "setflag" then
    setflag(a[2]); nextAction(d, true, string.format("flag %04X set by the test", a[2]))
  elseif op == "settle" then                     -- through any text until the field is free and the player still
    if not free then fieldTalk(d); sub.free = 0; return end
    if idle() then sub.free = (sub.free or 0) + 1 end
    if sub.free > 60 then nextAction(d, true) end
    if age > (a[2] or 20000) then nextAction(d, false, "never free") end
  elseif op == "save" then                       -- the Start menu: cursor 0x0203760E, count +1, entries from 0x02037610
    if not sub.ready then                        -- first the field free for a second (no script talking)
      if not free then fieldTalk(d); sub.free = 0; return end
      sub.free = (sub.free or 0) + 1
      if sub.free < 60 then return end
      sub.ready = age
    end
    age = age - sub.ready
    if age == 10 then tap(K.START) end
    if age == 80 then
      local n, cur, at = emu:read8(0x0203760F), emu:read8(0x0203760E), nil
      for i = 0, n - 1 do if emu:read8(0x02037610 + i) == 5 then at = i end end
      if not at then nextAction(d, false, "no Save in the Start menu"); return end
      sub.downs = (at - cur) % n
    end
    if sub.downs and age >= 100 and age < 100 + 20 * sub.downs and (age - 100) % 20 == 0 then tap(K.DOWN) end
    if sub.downs and age == 120 + 20 * sub.downs then shot(NAME .. "_savemenu"); tap(K.A); sub.saveAt = age end
    if sub.saveAt then                           -- A for "save?" and "overwrite?" only; then B (A would talk to
      local k = age - sub.saveAt                 --  whoever stands in front of the player)
      if E("SAVESHOTS") and k % 30 == 0 and k < 1500 then shot(string.format("%s_sv%04d", NAME, k)) end
      if not free then sub.held = k end           -- the menu and its messages hold the field: A to each
      if not free and k % 60 == 0 then tap(K.A) end        --  ("save?", "overwrite?", "saved"); once the
      if free and sub.held and k - sub.held > 120 then nextAction(d, true) end   -- field is free, stop
      if k > 6000 then nextAction(d, false, "the save never finished") end
    end
  elseif op == "dump" then
    dumpMap(a[2] or 10)
    if a[3] then
      local st = path(a[3] + 7, a[4] + 7, false)
      w(string.format("    path to %d,%d: %s", a[3], a[4], st and (#st .. " steps") or "none"))
    end
    nextAction(d, true)
  elseif op == "show" then                       -- {"show", 0x4051, 0x0074, ...}: log vars (>= 0x4000 below 0x8000) / flags
    local t = {}
    for i = 2, #a do
      local v = a[i]
      if v >= 0x4000 and v < 0x4100 then t[#t + 1] = string.format("var %04X = %d", v, var(v))
      else t[#t + 1] = string.format("flag %04X = %d", v, flag(v)) end
    end
    nextAction(d, true, table.concat(t, ", "))
  elseif op == "shot" then
    shot(NAME .. "_" .. a[2]); nextAction(d, true)
  end
end
