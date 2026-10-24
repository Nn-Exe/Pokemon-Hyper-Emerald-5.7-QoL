-- Kitakami: warp into Mossui Town at the bus stop (town revision 7: 23,47), walk up the market's aisle, under its
-- gate, up the avenue and over the bridge, up between the stone lanterns to the avenue's top end at the wood (the
-- town alone since 2026-10-16: no road, no Oni Mountain, no den). A screenshot at each stop (walk_NN.png) and the
-- map and the player's tile in walk_log.txt. MAPNUM: Mossui's number in group 35 (106).
NAME = "walk"
dofile((HERE or DIR or "./") .. "../dexnavchain/test_boot.lua")
local SCRIPT, MOSSUI = 0x0203F100, tonumber(os.getenv("MAPNUM") or "106")
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1); emu:write8(0x03000E38, 0)
end
local function where()
  local s = emu:read32(0x03005D8C)
  local id = emu:read8(0x02037590 + 5)
  local o = 0x02037350 + 0x24 * id
  return emu:read8(s + 4), emu:read8(s + 5), emu:read16(o + 0x10) - 7, emu:read16(o + 0x12) - 7
end
local function log(tag)
  local g, n, x, y = where()
  w(string.format("%-10s map %d/%d at %d,%d  cb2 %08X lock %d", tag, g, n, x, y, cb2(), lock()))
end
-- the route: {key, until(map, x, y) is true, a screenshot's name or nil}; a key is held until its target is met, or
-- until the player has not moved for 90 frames (logged as "stuck")
local STEPS = {
  {nil, nil, "arrive"},
  {K.UP, function(n, x, y) return y <= 40 end, "market"},
  {K.UP, function(n, x, y) return y <= 33 end, "gate"},
  {K.UP, function(n, x, y) return y <= 27 end, "avenue"},
  {K.UP, function(n, x, y) return y <= 11 end, "bridge"},
  {K.UP, function(n, x, y) return y <= 5 end, "north_end"},      -- the avenue's top end, signboard 3 beside it
  {K.UP, function(n, x, y) return y <= 4 end, nil},               -- the wood stops you: logged STUCK at y 5
}
local t0, step, holding, last, still, settle, shots = nil, 0, nil, nil, 0, nil, 0
local function finish_step(tag)
  if holding then emu:clearKey(holding); holding = nil end
  local s = STEPS[step]
  if s and s[3] then shots = shots + 1; settle = {string.format("walk_%02d_%s", shots, s[3]), tag} else log(tag) end
end
function TEST(f)
  t0 = t0 or f
  local d = f - t0
  if d == 10 then run({0x39, 35, MOSSUI, 0xFF, 23, 0, 47, 0, 0x02}) end
  if d < 200 then return end
  if settle then                                    -- let the walk end and the screen settle, then the picture
    settle[3] = (settle[3] or 0) + 1
    if settle[3] == 24 then shot(settle[1]); log(settle[2]); settle = nil end
    return
  end
  if holding and (lock() ~= 0 or cb2() ~= OVERWORLD) then   -- an Egg hatching, a phone call: B through it, then on
    emu:clearKey(holding); INTERRUPTED = holding; holding = nil
    w("interrupted (cb2 " .. string.format("%08X", cb2()) .. ")")
  end
  if INTERRUPTED then
    if lock() == 0 and cb2() == OVERWORLD then
      CALM = (CALM or 0) + 1
      if CALM > 40 then emu:addKey(INTERRUPTED); holding = INTERRUPTED; INTERRUPTED = nil; CALM = 0; still = 0 end
    else
      CALM = 0
      if f % 30 == 0 then tap(K.B) end
    end
    return
  end
  if holding then
    local g, n, x, y = where()
    local s = STEPS[step]
    if s[2](n, x, y) then finish_step(s[3] or "-"); return end
    local pos = n * 65536 + x * 256 + y
    if pos == last then still = still + 1 else still = 0; last = pos end
    if still > 90 then finish_step("STUCK") end
    return
  end
  step = step + 1
  local s = STEPS[step]
  if not s then if not ENDED then ENDED = true; w("finished"); done() end; return end
  if s[1] then emu:addKey(s[1]); holding = s[1]; still = 0; last = nil else finish_step(s[3]) end
end
