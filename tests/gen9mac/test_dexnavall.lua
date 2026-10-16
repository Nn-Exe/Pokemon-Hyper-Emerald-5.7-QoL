-- The DexNav for one wild Pokemon where it lives: warp to map G/N tile (X,Y) (a water tile: the warp puts the player
-- on the water, surfing), R opens the DexNav, the ring is moved with the D-pad onto SP in its list (KIND land /
-- water on the first screen; fish on the second, R switches; a fishing Pokemon is hunted from the water), a shot
-- (ring.png), A registers and starts the search; on the field the player steps toward the patch (state +28 / +29)
-- (a path found over the map in RAM) until a battle, whose species must be SP. Repel's counter is set and the lead
-- made Lv 100, so that no other wild Pokemon comes on the way. When the search ends or the patch stays out of reach,
-- the DexNav is opened and the search started again (5 searches at most).
-- Run on the "(DexNav open)" build (it registers unseen Pokemon) or with SP seen. The ui block's address is in the
-- DexNav task's data[0..1] (dexnavui.s: +4 screen, +5 row, +6 col; lists at +16 land x12, +64 water x5,
-- +84 rock x5, +104 fish x10, 4 bytes each, the species first).
local E = os.getenv
DIR = E("GEN9_DIR")
NAME = (E("TAG") or "dna") .. "_dn"
dofile("C:/Users/nonth/Desktop/Works & Productivity/gba-trans/hyper-emerald-en-qol/patches/dexnavchain/test_boot.lua")
local G, N, X, Y = tonumber(E("G")), tonumber(E("N")), tonumber(E("X")), tonumber(E("Y"))
local SP, KIND = tonumber(E("SP")), E("KIND") or "land"
local SCRIPT, STATE, ENEMY = 0x0203F100, 0x0203A660, 0x02024744
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1); emu:write8(0x03000E38, 0)
end
local LISTS = {land = {16, 12}, water = {64, 5}, rock = {84, 5}, fish = {104, 10}}
local function findUi()                          -- the task whose data[0..1] points at a block listing SP
  for t = 0, 15 do
    local tk = 0x03005E00 + 0x28 * t
    if emu:read8(tk + 4) ~= 0 then
      local p = emu:read16(tk + 8) | (emu:read16(tk + 10) << 16)
      if p >= 0x02000000 and p < 0x0203F000 then
        local at, n = LISTS[KIND][1], LISTS[KIND][2]
        for i = 0, n - 1 do if emu:read16(p + at + 4 * i) == SP then return p, i end end
      end
    end
  end
end
local function target(i)                         -- (screen, row, col) of list entry i
  if KIND == "land" then return 0, 1 + i // 6, i % 6
  elseif KIND == "water" then return 0, 0, i
  elseif KIND == "rock" then return 1, 0, i
  else return 1, 1 + i // 5, i % 5 end
end
local function pos()
  local id = emu:read8(0x02037590 + 5)
  local ox = 0x02037350 + 0x24 * id
  return emu:read16(ox + 0x10), emu:read16(ox + 0x12)
end
-- the way to the patch: a breadth-first search over the map in RAM (gBackupMapLayout 0x03005DC0: width, height,
-- the blocks; coordinates are the map's + 7, as the player's and the patch's are). A block is passable when its
-- collision bits are 0 and it is water while surfing / not water on foot (its behaviour from the layout's tilesets).
local WATER = {[0x10] = 1, [0x11] = 1, [0x12] = 1, [0x14] = 1, [0x15] = 1, [0x17] = 1, [0x19] = 1, [0x1A] = 1}
local function behaviour(mt)
  local lay = emu:read32(0x02037318)
  local ts = emu:read32(lay + (mt < 512 and 0x10 or 0x14))
  return emu:read16(emu:read32(ts + 0x10) + 2 * (mt < 512 and mt or mt - 512)) & 0xFF
end
local function path(sx, sy, tx, ty)
  local w, h, map = emu:read32(0x03005DC0), emu:read32(0x03005DC4), emu:read32(0x03005DC8)
  local surf = (emu:read8(0x02037590) & 0x08) ~= 0
  local function ok(x, y)
    if x < 0 or y < 0 or x >= w or y >= h then return false end
    if x == tx and y == ty then return true end
    local b = emu:read16(map + 2 * (y * w + x))
    if (b >> 10) & 3 ~= 0 then return false end
    local wat = WATER[behaviour(b & 0x3FF)] ~= nil
    return wat == surf
  end
  local prev, q, head = {[sy * 4096 + sx] = -1}, {sy * 4096 + sx}, 1
  while head <= #q do
    local c = q[head]; head = head + 1
    local x, y = c % 4096, c // 4096
    if x == tx and y == ty then
      local steps = {}
      while prev[c] ~= -1 do
        local p = prev[c]
        local px, py = p % 4096, p // 4096
        table.insert(steps, 1, (x > px and K.RIGHT) or (x < px and K.LEFT) or (y > py and K.DOWN) or K.UP)
        c = p; x, y = px, py
      end
      return steps
    end
    for _, dv in ipairs({{1, 0}, {-1, 0}, {0, 1}, {0, -1}}) do
      local nx, ny = x + dv[1], y + dv[2]
      local k = ny * 4096 + nx
      if prev[k] == nil and ok(nx, ny) and #q < 20000 then prev[k] = c; q[#q + 1] = k end
    end
  end
end
local t0, phase, mark, n, ui, idx, lastpos, stuck, alt = nil, "warp", 0, 0, nil, nil, nil, 0, 0
local tries, best, bestAt = 1, nil, 0
local function finish(msg) w(msg); phase = "end"; done() end
function TEST(f)
  t0 = t0 or f
  local d = f - t0
  if phase == "end" then return end
  if d == 5 then run({0x39, G, N, 0xFF, X & 0xFF, X >> 8, Y & 0xFF, Y >> 8, 0x02}) end
  if phase == "warp" and d > 300 and cb2() == OVERWORLD and lock() == 0 then
    local px, py = pos()
    w(string.format("on map %d/%d at %d,%d (avatar flags %02X)", G, N, px - 7, py - 7, emu:read8(0x02037590)))
    phase = "open"; mark = d; tap(K.R)
  elseif phase == "open" then
    if d == mark + 200 then
      ui, idx = findUi()
      if not ui then shot(NAME .. "_nolist"); finish(string.format("species %d is not in this map's %s list (FAIL)", SP, KIND)); return end
      local s = target(idx)
      if emu:read8(ui + 4) ~= s then tap(K.R) end
      phase = "ring"; mark = d
    end
    if d > mark + 3000 then finish("the DexNav did not open (FAIL)") end
  elseif phase == "ring" then
    if (d - mark) % 20 == 0 and d > mark + 60 then
      ui, idx = findUi()
      local s, r, c = target(idx)
      local cs, cr, cc = emu:read8(ui + 4), emu:read8(ui + 5), emu:read8(ui + 6)
      if cs ~= s then tap(K.R)
      elseif cr < r then tap(K.DOWN) elseif cr > r then tap(K.UP)
      elseif cc < c then tap(K.RIGHT) elseif cc > c then tap(K.LEFT)
      else shot(NAME .. "_ring"); tap(K.A); phase = "registered"; mark = d end
    end
    if d > mark + 2000 then shot(NAME .. "_ringstuck"); finish("could not reach the cell (FAIL)") end
  elseif phase == "registered" then
    if d > mark + 200 and cb2() == OVERWORLD and lock() == 0 then
      w(string.format("registered: species %d flags %02X", emu:read16(STATE + 2), emu:read8(STATE + 9)))
      if emu:read16(STATE + 2) ~= SP then finish("not registered (FAIL)"); return end
      if (emu:read8(STATE + 9) & 1) == 0 then      -- A on the one being hunted stops the search: A again
        phase = "open"; mark = d; tap(K.R); return
      end
      run({0x16, 0x21, 0x40, 200, 0, 0x02})        -- setvar VAR_REPEL_STEP_COUNT 200, and the party at Lv 100 so
      for p = 0, 5 do                                -- that Repel keeps every other wild Pokemon away (it asks the
        if emu:read16(0x020244EC + 100 * p + 0x20) ~= 0 then emu:write8(0x020244EC + 100 * p + 0x54, 100) end
      end                                            -- first one that is not an Egg)
      phase = "walk"; mark = d; n = 0
    end
    if d > mark + 3000 then finish("did not come back to the field (FAIL)") end
  elseif phase == "walk" then
    n = n + 1
    if n == 10 then emu:write8(0x03000F2C, 0) end
    if cb2() == BATTLE then
      if emu:read16(ENEMY + 0x20) ~= 0 then
        local sp = emu:read16(ENEMY + 0x20)
        local x, y = pos()
        w(string.format("  battle began: player %d,%d patch %d,%d flags %02X repel %d", x, y, emu:read8(STATE + 28),
          emu:read8(STATE + 29), emu:read8(STATE + 9), emu:read16(emu:read32(0x03005D8C) + 0x139C + 2 * 0x21)))
        shot(NAME .. "_battle")
        finish(string.format("wild battle: species %d level %d after %d frames, search %d (want %d) %s", sp,
          emu:read8(ENEMY + 0x54), n, tries, SP, sp == SP and "PASS" or "FAIL"))
      end
    elseif n > 12 and lock() ~= 0 then if n % 30 == 0 then tap(K.B) end
    elseif n > 12 and n % 24 == 0 then
      local x, y = pos()
      local px, py = emu:read8(STATE + 28), emu:read8(STATE + 29)
      if n % 480 == 0 then w(string.format("  player %d,%d patch %d,%d flags %02X", x, y, px, py, emu:read8(STATE + 9))) end
      if E("DEBUG") and n % 480 == 0 and px ~= 0 then
        local w_, map = emu:read32(0x03005DC0), emu:read32(0x03005DC8)
        for yy = math.min(y, py) - 2, math.max(y, py) + 2 do
          local row = {}
          for xx = math.min(x, px) - 3, math.max(x, px) + 3 do
            local b = emu:read16(map + 2 * (yy * w_ + xx))
            row[#row + 1] = string.format("%02X%s", behaviour(b & 0x3FF), ((b >> 10) & 3) ~= 0 and "#" or ((xx == x and yy == y) and "P" or ((xx == px and yy == py) and "*" or ".")))
          end
          w("    " .. yy .. ": " .. table.concat(row, " "))
        end
        local st = path(x, y, px, py); w("    path: " .. (st and #st or "none"))
      end
      if lastpos and lastpos == x * 1000 + y then stuck = stuck + 1 else stuck = 0 end
      lastpos = x * 1000 + y
      local dist = (px ~= 0) and (math.abs(px - x) + math.abs(py - y)) or 999
      if not best or dist < best then best = dist; bestAt = n end
      if (emu:read8(STATE + 9) & 1) == 0 or n - bestAt > 1500 then   -- the search ended, or no nearer for a while:
        if tries >= 5 then shot(NAME .. "_gaveup"); finish("never reached a patch in 5 searches (FAIL)"); return end
        tries = tries + 1; best = nil                                -- search again, as a player would
        w(string.format("  search %d: player %d,%d patch %d,%d flags %02X", tries, x, y, px, py, emu:read8(STATE + 9)))
        phase = "open"; mark = d; tap(K.R); return
      end
      if px ~= 0 then
        local steps = path(x, y, px, py)
        local k = steps and steps[1]
        if not k or stuck > 2 then                -- no way found, or blocked anyway: a step aside
          alt = alt + 1; k = ({K.UP, K.LEFT, K.DOWN, K.RIGHT})[alt % 4 + 1]
        end
        tap(k, 14)
      elseif n % 96 == 0 then tap(({K.LEFT, K.RIGHT})[(n // 96) % 2 + 1], 14) end
    end
    if n > 20000 then shot(NAME .. "_nobattle"); finish("no battle (FAIL)") end
  end
end
