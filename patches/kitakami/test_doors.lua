-- Kitakami: every kind of door. From Mossui's Kitakami Hall door: the Mask Hall (one floor since 2026-10-17: the
-- user, "we need only one floor"; drawn for Kitakami, khall.py), up its carpet to the stage and back out over the
-- mat; then the homes; the Pokemon Center (A at the nurse, B through her lines), the other home. A screenshot at
-- each stop (doors_NN_name.png), the map and tile of every stop in doors_log.txt. Maps since 2026-10-17: Mossui 106,
-- hall 107, family 108, pc 109, home1 110, home2 111.
-- Mossui's doors (revision 6): the hall 12,14 (down its steps, through the torii's court, to the street at y 30),
-- Carmine and Kieran's 18,29, the old woman's 7,29, the Pokemon Center 30,29, the old couple's 40,29.
NAME = "doors"
dofile((HERE or DIR or "./") .. "../dexnavchain/test_boot.lua")
local SCRIPT = 0x0203F100
local MOSSUI, HALL, FAMILY, PC, HOME1, HOME2 = 106, 107, 108, 109, 110, 111
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
  w(string.format("%-12s map %d/%d at %d,%d  cb2 %08X lock %d", tag, g, n, x, y, cb2(), lock()))
end
local function at_map(m) return function(n) return n == m end end
local function ys(m, c) return function(n, x, y) return n == m and c(x, y) end end
-- {key, until(map, x, y), name}: hold the key until it holds (WARP: a warp script; TALK: A then B through it)
local STEPS = {
  {"WARP", {MOSSUI, 12, 15}, "mossui_hall"},
  {K.UP, at_map(HALL), "hall"},                                          -- on its mat (6,14)
  {K.UP, ys(HALL, function(x, y) return y <= 8 end), "mask_hall"},      -- up the carpet to the stage
  {K.DOWN, ys(HALL, function(x, y) return y >= 14 end), nil},           -- back to the mat
  {K.DOWN, at_map(MOSSUI), "back_out"},
  {K.DOWN, ys(MOSSUI, function(x, y) return y >= 21 end), "torii"},     -- down the steps, under the torii
  {K.DOWN, ys(MOSSUI, function(x, y) return y >= 30 end), nil},          -- on to the street
  {K.RIGHT, ys(MOSSUI, function(x, y) return x >= 18 end), nil},
  {K.UP, at_map(FAMILY), "family_house"},                               -- Carmine and Kieran's (18,29)
  {K.DOWN, at_map(MOSSUI), nil},
  {K.DOWN, ys(MOSSUI, function(x, y) return y >= 30 end), nil},
  {K.LEFT, ys(MOSSUI, function(x, y) return x <= 7 end), nil},
  {K.UP, at_map(HOME1), "home1"},                                       -- the old woman's (7,29)
  {K.DOWN, at_map(MOSSUI), nil},
  {K.DOWN, ys(MOSSUI, function(x, y) return y >= 30 end), nil},
  {K.RIGHT, ys(MOSSUI, function(x, y) return x >= 40 end), nil},
  {K.UP, at_map(HOME2), "home2"},                                       -- the old couple's (40,29)
  {K.DOWN, at_map(MOSSUI), nil},
  {K.DOWN, ys(MOSSUI, function(x, y) return y >= 30 end), nil},
  {K.LEFT, ys(MOSSUI, function(x, y) return x <= 30 end), nil},
  {K.UP, at_map(PC), "pokemon_center"},                                 -- (30,29)
  {K.UP, ys(PC, function(x, y) return y <= 6 end), nil},
  {K.RIGHT, ys(PC, function(x, y) return x >= 7 end), nil},
  {K.UP, ys(PC, function(x, y) return y <= 4 end), nil},
  {"TALK", nil, "nurse"},
}
local t0, step, holding, last, still, settle, shots, talk = nil, 0, nil, nil, 0, nil, 0, nil
local function finish_step(tag)
  if holding then emu:clearKey(holding); holding = nil end
  local s = STEPS[step]
  if s and s[3] then shots = shots + 1; settle = {string.format("doors_%02d_%s", shots, s[3]), tag} else log(tag) end
end
function TEST(f)
  t0 = t0 or f
  local d = f - t0
  if d < 30 then return end
  if settle then
    settle[3] = (settle[3] or 0) + 1
    if settle[3] == 40 then shot(settle[1]); log(settle[2]); settle = nil end
    return
  end
  if talk then                                          -- A at the nurse, then B until the field is free again
    talk = talk + 1
    if talk == 2 then tap(K.A) end
    if talk == 90 then shots = shots + 1; shot(string.format("doors_%02d_nurse_talking", shots)) end
    if talk > 100 and talk % 25 == 0 then tap(K.B) end
    if talk > 140 and lock() == 0 and cb2() == OVERWORLD then talk = nil; finish_step("talked") end
    if talk and talk > 1500 then talk = nil; finish_step("TALK TIMED OUT") end
    return
  end
  if holding and (lock() ~= 0 or cb2() ~= OVERWORLD) then  -- a door's warp, an Egg, a call: let it play out
    emu:clearKey(holding); PAUSED = holding; holding = nil
  end
  if PAUSED then
    local s = STEPS[step]
    local g, n, x, y = where()
    if lock() == 0 and cb2() == OVERWORLD then
      CALM = (CALM or 0) + 1
      if CALM > 30 then
        CALM = 0
        if s[2](n, x, y) then PAUSED = nil; finish_step(s[3] or "-")
        else emu:addKey(PAUSED); holding = PAUSED; PAUSED = nil; still = 0 end
      end
    else
      CALM = 0
      if f % 40 == 0 and not (s[2] and s[2](n, x, y)) then tap(K.B) end
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
  if s[1] == "WARP" then
    local m, x, y = s[2][1], s[2][2], s[2][3]
    run({0x39, 35, m, 0xFF, x & 0xFF, x >> 8, y & 0xFF, y >> 8, 0x02})
    PAUSED = K.UP; s[2] = function(n) return n == m end
    emu:clearKey(K.UP)
  elseif s[1] == "TALK" then
    talk = 0
  else
    emu:addKey(s[1]); holding = s[1]; still = 0; last = nil
  end
end
