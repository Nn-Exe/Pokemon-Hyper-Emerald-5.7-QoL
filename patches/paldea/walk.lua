-- (Copied from an earlier test harness of this project.)
-- Walking for the tests: find a route on the live map (collision and elevation as the game checks them, objects
-- in the way) and press the D-pad one tile at a time, waiting for each step to land. No warping.
-- On ice (behaviour 0x20, the Sealed Vault's floor) a press is a slide: it goes on until the next tile cannot be
-- entered, or onto the first tile that is not ice. A route is then so many presses, and a press has landed when
-- you have stood still for a while.
--   walk_start(tx, ty, stop_next_to)  then call walk_tick(f) every frame until it returns "done" or "stuck".
local MAPOFS = 7
local PL = 0x02037350                      -- gObjectEvents[0], the player
local function layout() return emu:read32(0x03005DC0), emu:read32(0x03005DC4), emu:read32(0x03005DC8) end
function player_xy() return emu:read16(PL + 0x10) - MAPOFS, emu:read16(PL + 0x12) - MAPOFS end
function player_elev() return emu:read8(PL + 0x0B) & 15 end
function block_at(x, y)
  local w, h, m = layout()
  local gx, gy = x + MAPOFS, y + MAPOFS
  if gx < 0 or gy < 0 or gx >= w or gy >= h then return 0x0400 end
  return emu:read16(m + 2 * (gy * w + gx))
end
local function flag_on(f)
  local sb1, sb2 = emu:read32(0x03005D8C), emu:read32(0x03005D90)
  local a
  if f < 0x4000 then a = sb1 + 0x1270 + (f >> 3)
  else
    local i = (f - 0x4000) >> 3
    if i <= 0x33 then a = sb1 + 0x988 + i elseif i <= 0x67 then a = sb1 + 0x3B24 + i - 0x34
    elseif i <= 0x9B then a = sb2 + 0x5C + i - 0x68 else a = sb2 + 0x28 + i - 0x9C end
  end
  return (emu:read8(a) >> (f & 7)) & 1 == 1
end
local function objects_at()
  local t = {}
  -- every person the map places (saved templates, SaveBlock1 + 0xC70), unless hidden by its flag - an object off
  -- screen is not spawned yet but will stand there when we arrive
  local sb1 = emu:read32(0x03005D8C)
  for k = 0, 63 do
    local o = sb1 + 0xC70 + k * 24
    local fl = emu:read16(o + 20)
    if emu:read8(o) ~= 0 and not (fl ~= 0 and flag_on(fl)) then
      t[emu:read16(o + 4) .. "," .. emu:read16(o + 6)] = true
    end
  end
  for i = 1, 15 do
    local o = PL + i * 0x24
    if emu:read8(o) & 1 == 1 then
      t[(emu:read16(o + 0x10) - MAPOFS) .. "," .. (emu:read16(o + 0x12) - MAPOFS)] = true
    end
  end
  return t
end
-- can a walker at elevation e step onto (x, y)? returns the elevation after the step, or nil
local WARPTILE = {[790] = true, [604] = true, [734] = true}   -- portal centres: only when they are the target
local GOAL = nil
local function enter(x, y, e)
  local b = block_at(x, y)
  if (b >> 10) & 3 ~= 0 then return nil end
  if WARPTILE[b & 0x3FF] and not (GOAL and GOAL[1] == x and GOAL[2] == y) then return nil end
  if STEPS_AVOID and STEPS_AVOID[x .. "," .. y] and not (GOAL and GOAL[1] == x and GOAL[2] == y) then return nil end
  local z = b >> 12
  if z == 1 then return nil end                           -- water (height 1): Surf, which the tests don't use
  if z == 15 then return e end                            -- a bridge keeps your height
  if z == 0 then return 0 end                             -- stairs: height 0, from which any height may follow
  if e ~= 0 and e ~= 15 and z ~= e then return nil end
  return z
end
local DIRS = {{0, -1, "UP"}, {0, 1, "DOWN"}, {-1, 0, "LEFT"}, {1, 0, "RIGHT"}}
-- a tile's behaviour, from the current map's two tilesets (gMapHeader.mapLayout: 0x02037318; attributes are a
-- word a metatile, the behaviour its low byte)
local BEH, BEH_OF = {}, nil
local function behaviour(mid)
  local lay = emu:read32(0x02037318)
  if lay ~= BEH_OF then BEH, BEH_OF = {}, lay end
  if BEH[mid] == nil then
    local ts = emu:read32(lay + ((mid < 512) and 0x10 or 0x14))
    BEH[mid] = emu:read16(emu:read32(ts + 0x10) + 2 * (mid % 512)) & 0xFF
  end
  return BEH[mid]
end
local function ice(x, y) return behaviour(block_at(x, y) & 0x3FF) == 0x20 end
-- where a press of a direction leaves a walker at (x, y), elevation e: x, y, e there, or nil if it cannot move
local function go(x, y, e, d, objs)
  local nx, ny = x + d[1], y + d[2]
  if objs[nx .. "," .. ny] then return nil end
  local ne = enter(nx, ny, e)
  if not ne then return nil end
  while ice(nx, ny) do
    local mx, my = nx + d[1], ny + d[2]
    if objs[mx .. "," .. my] then break end
    local me = enter(mx, my, ne)
    if not me then break end
    nx, ny, ne = mx, my, me
  end
  return nx, ny, ne
end
local function route(tx, ty, near)
  GOAL = {tx, ty}
  local sx, sy = player_xy()
  local se = player_elev()
  local objs = objects_at()
  local key = function(x, y, e) return x .. "," .. y .. "," .. e end
  local prev, q, head = {}, {{sx, sy, se}}, 1
  prev[key(sx, sy, se)] = false
  while head <= #q do
    local x, y, e = q[head][1], q[head][2], q[head][3]; head = head + 1
    local goal = (x == tx and y == ty) or (near and math.abs(x - tx) + math.abs(y - ty) == 1)
    if goal then
      local path, k = {}, key(x, y, e)
      while prev[k] do table.insert(path, 1, prev[k][2]); k = prev[k][1] end
      return path, x, y
    end
    for _, d in ipairs(DIRS) do
      local nx, ny, ne = go(x, y, e, d, objs)
      if nx then
        local k2 = key(nx, ny, ne)
        if prev[k2] == nil then prev[k2] = {key(x, y, e), d[3]}; q[#q + 1] = {nx, ny, ne} end
      end
    end
    if #q > 20000 then break end
  end
  return nil
end

local W = nil
function walk_start(tx, ty, near)
  local path = route(tx, ty, near)
  W = {path = path, i = 1, t = 0, tries = 0, tx = tx, ty = ty}
  local o = {}
  for k, _ in pairs(objects_at()) do o[#o + 1] = k end
  W.debug = "route " .. (path and table.concat(path, " ") or "none") .. " | objects " .. table.concat(o, " ")
  return path ~= nil, path and #path or 0
end
-- "walking", "done", "stuck" (a step that did not land), "noroute", "interrupted" (a script took over)
function walk_tick(f, keys)
  if not W then return "done" end
  if not W.path then return "noroute" end
  if W.i > #W.path then return "done" end
  if lock() ~= 0 then return "interrupted" end
  W.t = W.t + 1
  local x, y = player_xy()
  if W.t == 1 then W.last = {x, y}; W.still, W.moved = 0, false; tap(keys[W.path[W.i]], 6) end
  if x ~= W.last[1] or y ~= W.last[2] then W.moved = true; W.still = 0; W.last = {x, y} else W.still = W.still + 1 end
  if W.moved then                                          -- landed: 18 frames without a new tile (a step takes 16;
    if W.still >= 18 then W.i = W.i + 1; W.t = 0; W.tries = 0 end   -- a slide goes on from tile to tile)
  elseif W.t >= 20 then                                    -- it only turned you, or something is in the way
    W.tries = W.tries + 1; W.t = 0
    if W.tries >= 4 then return "stuck" end
  end
  return "walking"
end
function walk_face(dir, keys) tap(keys[dir], 2) end

function walk_debug() return W and W.debug or "" end
