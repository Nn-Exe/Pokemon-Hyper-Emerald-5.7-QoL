-- Repel prompt fixes. CASE=no|yes: a Max Repel with 3 steps left on Route 101 (10,10); walk into "The Repel ended...
-- Use another?" and answer it. CASE=lno|lyes: no repel on; L for the quick repel ("Use the Max Repel?") and answer.
-- Then walk on (STEPS, default 40). Logged: every lock, the steps taken between the answer and the repel going on
-- (must be 0), the Max Repel count, the people on screen still frozen once the prompt is over (must be 0), and any
-- later prompt (there must be none). Screenshots repelfix_<case>_*.png; the log repelfix_<case>_log.txt.
NAME = "repelfix_" .. (os.getenv("CASE") or "no")
dofile((DIR or "./") .. "../dexnavchain/test_boot.lua")
local CASE = os.getenv("CASE") or "no"
local YES = CASE == "yes" or CASE == "lyes"
local LKEY = CASE == "lno" or CASE == "lyes"
local STEPS = tonumber(os.getenv("STEPS") or "40")
local SCRIPT = 0x0203F100
local function sb1() return emu:read32(0x03005D8C) end
local function var() return emu:read16(sb1() + 0x139C + 0x21 * 2) end
local function setvar(v) emu:write16(sb1() + 0x139C + 0x21 * 2, v) end
local function pos()
  local o = 0x02037350 + 0x24 * emu:read8(0x02037590 + 5)
  return emu:read16(o + 0x10) - 7, emu:read16(o + 0x12) - 7
end
local function qty()
  local slots, cap = emu:read32(0x02039DD8), emu:read8(0x02039DD8 + 4)
  for i = 0, cap - 1 do if emu:read16(slots + 4 * i) == 84 then return emu:read16(slots + 4 * i + 2) end end
  return 0
end
local function frozen()
  local pl, a, f = emu:read8(0x02037590 + 5), 0, 0
  for i = 0, 15 do
    local o = 0x02037350 + 0x24 * i
    if i ~= pl and emu:read8(o) & 1 == 1 then a = a + 1; if emu:read8(o + 1) & 1 == 1 then f = f + 1 end end
  end
  return string.format("people %d, frozen %d", a, f)
end
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1); emu:write8(0x03000E38, 0)
end
local phase, t0, steps, locked, prompts, lastpos, lockstart = "setup", nil, 0, false, 0, nil, 0
local q0, answered, set_at, inbattle, menu_at, di, stuck, lasttap, after_at
function TEST(f)
  t0 = t0 or f
  local d = f - t0
  if phase == "setup" then
    if d == 5 then run({0x39, 0, 16, 0xFF, 10, 0, 10, 0, 0x02}) end                  -- Route 101
    if d == 300 then
      setvar(LKEY and (84 << 8) or ((84 << 8) | 3))
      emu:write8(0x020375D4, 0)                                                     -- no Match Call
      q0 = qty()
      local x, y = pos()
      w(string.format("start: var %04X at (%d,%d), Max Repels %d, %s", var(), x, y, q0, frozen()))
      phase = "walk"; lastpos = {x, y}
    end
    return
  end
  if phase ~= "walk" then return end
  if answered and not set_at and var() & 0xFF ~= 0 then
    set_at = steps
    w(string.format("d=%d the repel is on: var %04X after %d steps since the answer", d, var(), steps - answered))
  end
  if cb2() == BATTLE then                                                            -- a wild battle: run
    if not inbattle then inbattle = true; w(string.format("d=%d step %d: wild battle, var %04X", d, steps, var())) end
    if emu:read32(0x03005D60) == 0x08057589 then
      menu_at = menu_at or d
      local k = d - menu_at
      if k == 10 then tap(K.RIGHT) elseif k == 25 then tap(K.DOWN) elseif k == 40 then tap(K.A) end
    elseif d % 20 == 0 then tap(K.B) end
    return
  end
  if inbattle then
    if cb2() ~= OVERWORLD then return end
    inbattle = false; menu_at = nil
    w(string.format("d=%d back on the field: var %04X", d, var()))
  end
  if lock() ~= 0 then
    if not locked then
      locked = true; prompts = prompts + 1; lockstart = d
      w(string.format("d=%d step %d: LOCKED (#%d) var %04X item %d script %08X", d, steps, prompts, var(),
        emu:read16(0x0203CE7C), emu:read32(0x03000E48)))
    end
    local k = d - lockstart
    if prompts == 1 then
      if k == 50 then shot(NAME .. "_prompt") end
      if k == 60 then tap(YES and K.A or K.B); answered = steps end
      if k == 115 and YES then shot(NAME .. "_used") end
      if k > 90 and k % 30 == 0 then tap(K.A) end                                    -- through "... used the ..."
    elseif k % 30 == 0 then tap(K.B) end
    return
  end
  if locked then
    locked = false
    w(string.format("d=%d unlocked: var %04X, Max Repels %d -> %d, %s", d, var(), q0, qty(), frozen()))
    if prompts == 1 then shot(NAME .. "_after"); after_at = d end
  end
  if after_at and d == after_at + 12 then shot(NAME .. "_after12") end
  if LKEY and prompts == 0 then                                                      -- the quick repel: L, stand
    if d == 310 then tap(K.L) end
    if d > 400 then w("L opened nothing"); phase = "done"; done() end
    return
  end
  local x, y = pos()
  if x ~= lastpos[1] or y ~= lastpos[2] then
    steps = steps + 1; lastpos = {x, y}
    if steps % 10 == 0 or steps < 6 then w(string.format("  step %2d at (%d,%d) var %04X %s", steps, x, y, var(), frozen())) end
  end
  if steps >= STEPS + 3 or d > 30000 then
    w(string.format("END: %d steps, %d locks, var %04X, Max Repels %d -> %d, %s", steps, prompts, var(), q0, qty(),
      frozen()))
    phase = "done"; done(); return
  end
  if d % 16 == 0 then                                                                -- walk; turn when blocked
    if lasttap and x == lasttap[1] and y == lasttap[2] then
      stuck = (stuck or 0) + 1
      if stuck >= 2 then di = ((di or 0) % 4) + 1; stuck = 0 end
    else stuck = 0 end
    lasttap = {x, y}
    tap(({K.LEFT, K.UP, K.RIGHT, K.DOWN})[(di or 0) % 4 + 1], 14)
  end
end
