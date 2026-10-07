-- L move info, the values. A wild Snorlax Lv 100; once the move menu is up the move list it reads is set to
-- Swords Dance (14: Status, no power), Quick Attack (98: priority +1), Roar (46: priority -6, no accuracy) and
-- Fake Out (252: 100% effect, priority +3). L is held and the cursor walks over all four (shots lmv_<n>.png, each
-- logged with the ROM's own numbers for that move). Then A with L still held uses the first move: the turn must
-- play out and the next action menu must come up with the same number of sprites as the first one.
NAME = "lmoveinfo_moves"
dofile((DIR or "./") .. "../dexnavchain/test_boot.lua")
local SCRIPT, MOVES = 0x0203F100, 0x09D86419
local ACTION, MOVE = 0x08057589, 0x08057BFD
local SET = {14, 98, 46, 252}
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1); emu:write8(0x03000E38, 0)
end
local function sprites()
  local n = 0
  for i = 0, 63 do if emu:read8(0x02020630 + 0x44 * i + 0x3E) & 1 == 1 then n = n + 1 end end
  return n
end
local function ctrl() return emu:read32(0x03005D60) end
local function describe(tag)
  local cur = emu:read8(0x020244B0)
  local m = emu:read16(0x02023068 + cur * 2)
  local e = MOVES + m * 12
  local prio = emu:read8(e + 7); if prio >= 128 then prio = prio - 256 end
  w(string.format("%-10s cursor %d move %3d: power %3d acc %3d effect %3d%% priority %+d contact %d split %d | sprites %d",
    tag, cur, m, emu:read8(e + 1), emu:read8(e + 3), emu:read8(e + 5), prio, emu:read8(e + 8) & 1, emu:read8(e + 10),
    sprites()))
end
local t0, phase, mark, first, plan = nil, "start", nil, nil, {}
local function at(d, fn) plan[#plan + 1] = {d, fn} end
local function seq(m)
  at(m + 5, function()                                -- the list the menu (and the panel) reads; the names in the
    for i, mv in ipairs(SET) do emu:write16(0x02023068 + (i - 1) * 2, mv) end   -- move box were drawn already
  end)
  at(m + 20, function() emu:addKey(K.L) end)
  at(m + 45, function() describe("slot 0"); shot("lmv_0") end)
  at(m + 50, function() tap(K.RIGHT) end)
  at(m + 70, function() describe("slot 1"); shot("lmv_1") end)
  at(m + 75, function() tap(K.DOWN) end)
  at(m + 95, function() describe("slot 3"); shot("lmv_3") end)
  at(m + 100, function() tap(K.LEFT) end)
  at(m + 120, function() describe("slot 2"); shot("lmv_2") end)
  at(m + 125, function() tap(K.UP) end)
  at(m + 145, function() tap(K.A) end)               -- Swords Dance, L still held
  at(m + 150, function() shot("lmv_used5") end)
  at(m + 160, function() emu:clearKey(K.L); shot("lmv_used15"); w("after A: sprites " .. sprites()) end)
end
function TEST(f)
  t0 = t0 or f
  local d = f - t0
  if d == 10 then run({0xB6, 143, 0, 100, 0, 0, 0xB7, 0x02}) end      -- Snorlax Lv 100: it outlasts the turn
  if phase == "start" and d > 20 then
    if cb2() == BATTLE and ctrl() == ACTION then
      phase = "action"; mark = d; first = sprites(); w("first action menu: sprites " .. first)
    end
    if d % 20 == 0 and cb2() == BATTLE then tap(K.B) end
  elseif phase == "action" then
    if d == mark + 30 then tap(K.A) end
    if d > mark + 30 and ctrl() == MOVE then phase = "move"; seq(d) end
  elseif phase == "move" then
    for _, p in ipairs(plan) do if d == p[1] then p[2]() end end
    if d > plan[#plan][1] + 20 then
      if d % 25 == 0 then tap(K.B) end                 -- through the turn's messages
      if ctrl() == ACTION and cb2() == BATTLE then
        phase = "second"; mark = d
      end
      if cb2() == OVERWORLD and lock() == 0 then w("the battle ended during the turn"); phase = "end"; done() end
    end
  elseif phase == "second" then
    if d == mark + 40 then
      w(string.format("second action menu: sprites %d (first %d): %s", sprites(), first, tostring(sprites() == first)))
      shot("lmv_second")
      tap(K.RIGHT)
    end
    if d == mark + 60 then tap(K.DOWN) end
    if d == mark + 80 then tap(K.A) end
    if d > mark + 110 and d % 30 == 0 and cb2() ~= OVERWORLD then tap(K.B) end
    if d > mark + 110 and cb2() == OVERWORLD and lock() == 0 then w("back on the field"); phase = "end"; done() end
  end
  if d > 8000 and phase ~= "end" then w("TIMEOUT in " .. phase); phase = "end"; done() end
end
