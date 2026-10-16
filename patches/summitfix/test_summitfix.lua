-- The summit fix. SCEN picks one case; each sets the save up (the stone = item 745, the Dried Fish = 744, the
-- fish ball's flag 0x4322, the summit's flag 0x4323), runs one of the game's scripts from where a player would
-- reach it, presses B through the text (B also answers No), and logs what is in the Bag afterwards.
--   down        in the Moonbow Dome with the stone, the way down the mountain (0x098C5F06): the stone must stay
--   bored       the "I'm getting a bit bored" line (0x098C6143), then the way down: screenshots of the hint
--   kitty_lost  fish taken, no fish, no stone, summit not done: Kitty must give a stone
--   kitty_has   the same with the stone in the Bag: her greeting, still one stone
--   kitty_done  the same with the summit done and no stone: her greeting, no stone
--   kitty_fish  a Dried Fish in the Bag: her trade - fish gone, stone given
--   kitty_new   the fish never picked up: her greeting, no stone
-- Screenshots summitfix_<scen>_NN.png every 40 frames while the script runs; the log summitfix_<scen>_log.txt.
local SCEN = os.getenv("SCEN") or "down"
NAME = "summitfix_" .. SCEN
dofile((HERE or DIR or "./") .. "../dexnavchain/test_boot.lua")
local SCRIPT, POCKETS = 0x0203F100, 0x02039DD8
local STONE, FISH, F_FISH, F_DONE = 745, 744, 0x4322, 0x4323
local function sb1() return emu:read32(0x03005D8C) end
-- The hack keeps flags from 0x4000 up somewhere of its own, so they are set and read with script commands:
-- probe() leaves 0x4322 and 0x4323 in VAR 0x8004 / 0x8005 (0x020375E0 / E2), which state() prints.
local function has(item)                                  -- in the Key Items pocket
  local slots, cap = emu:read32(POCKETS + 32), emu:read8(POCKETS + 36)
  for i = 0, cap - 1 do if emu:read16(slots + 4 * i) == item then return 1 end end
  return 0
end
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1); emu:write8(0x03000E38, 0)
end
local function goto_(a) return {0x05, a & 0xFF, (a >> 8) & 0xFF, (a >> 16) & 0xFF, a >> 24} end
local function item_cmd(op, item) return {op, item & 0xFF, item >> 8, 1, 0} end
local function probe()
  local a1, a2 = SCRIPT + 19, SCRIPT + 38
  return {0x16, 0x04, 0x80, 0, 0, 0x2B, F_FISH & 0xFF, F_FISH >> 8, 0x06, 0x00, a1 & 0xFF, (a1 >> 8) & 0xFF, (a1 >> 16) & 0xFF, a1 >> 24,
          0x16, 0x04, 0x80, 1, 0,
          0x16, 0x05, 0x80, 0, 0, 0x2B, F_DONE & 0xFF, F_DONE >> 8, 0x06, 0x00, a2 & 0xFF, (a2 >> 8) & 0xFF, (a2 >> 16) & 0xFF, a2 >> 24,
          0x16, 0x05, 0x80, 1, 0,
          0x02}
end
local function give_take(stone, fish, f_fish, f_done)     -- a script that leaves exactly these in the Bag and the flags
  local b = {}
  for _, x in ipairs({{F_FISH, f_fish}, {F_DONE, f_done}}) do
    b[#b + 1] = x[2] == 1 and 0x29 or 0x2A; b[#b + 1] = x[1] & 0xFF; b[#b + 1] = x[1] >> 8
  end
  for _, x in ipairs({{STONE, stone}, {FISH, fish}}) do
    for _, c in ipairs(item_cmd(0x45, x[1])) do b[#b + 1] = c end                 -- removeitem (no harm if absent)
    if x[2] == 1 then for _, c in ipairs(item_cmd(0x44, x[1])) do b[#b + 1] = c end end
  end
  b[#b + 1] = 0x02
  return b
end
local function state(tag)
  local s = sb1()
  w(string.format("%-12s map %d/%d  stone %d  fish %d  flag 4322=%d 4323=%d", tag, emu:read8(s + 4), emu:read8(s + 5),
    has(STONE), has(FISH), emu:read16(0x020375E0), emu:read16(0x020375E2)))
end
local CASES = {              -- stone, fish, flag 0x4322, flag 0x4323, the script, warp into the dome first
  down       = {1, 0, 1, 0, 0x098C5F06, true},
  bored      = {1, 0, 1, 0, 0x098C6143, true},
  kitty_lost = {0, 0, 1, 0, 0x098B1F85, false},
  kitty_has  = {1, 0, 1, 0, 0x098B1F85, false},
  kitty_done = {0, 0, 1, 1, 0x098B1F85, false},
  kitty_fish = {0, 1, 1, 0, 0x098B1F85, false},
  kitty_new  = {0, 0, 0, 0, 0x098B1F85, false},
}
local c = CASES[SCEN]
local plan, t0, started, shots, finished, ending, timed_out = {}, nil, nil, 0, false, nil, false
local function at(d, fn) plan[#plan + 1] = {d, fn} end
at(10, function() run(probe()) end)
at(20, function() state("as saved") end)
at(30, function() if c[6] then run({0x39, 35, 10, 0xFF, 10, 0, 19, 0, 0x02}) end end)
at(400, function() run(give_take(c[1], c[2], c[3], c[4])) end)
at(415, function() run(probe()) end)
at(430, function() state("set up"); run(goto_(c[5])); started = 430 end)
function TEST(f)
  t0 = t0 or f
  local d = f - t0
  for _, p in ipairs(plan) do if d == p[1] then p[2]() end end
  if not started or finished then return end
  local k = d - started
  if k > 0 and k % 40 == 0 and shots < 30 then shots = shots + 1; shot(string.format("%s_%02d", NAME, shots)) end
  if k > 0 and k % 40 == 10 and not ending then tap(K.B) end
  if not ending and ((k > 200 and lock() == 0 and cb2() == OVERWORLD) or k > 4000) then
    ending = d; timed_out = k > 4000
  end
  if ending and d == ending + 120 then run(probe()) end        -- (after a warp the new map is up by then)
  if ending and d == ending + 135 then
    finished = true
    state(timed_out and "TIMED OUT" or "afterwards"); done()
  end
end
