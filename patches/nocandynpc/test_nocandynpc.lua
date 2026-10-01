-- nocandynpc: the Rare Candy NPC is gone from Petalburg's Poke Mart (8/6), and a game saved with him
-- loaded does not break.
--   MODE=gone  (patched ROM)   warp into the Mart at (4,6), list its objects, walk right onto (5,6) where he
--                              stood, press A: no object 5, the step succeeds, candies unchanged.
--   MODE=save  (pre-patch ROM) warp in, face him, write a save state to STATE (he is loaded on (5,6)).
--   MODE=ghost (patched ROM)   load that state (the "saved inside the Mart" case: object 5 still in RAM),
--                              talk to him: nothing happens, no candies, the game stays on the field; then
--                              warp into the Mart again: he is gone.
-- Run muted from a scratch folder holding <rom>.gba + <rom>.sav copies:
--   MODE=gone TEST_DIR=<scratch>/ mGBA -C mute=1 -C fpsTarget=2000 -C audioSync=0 -C videoSync=0 \
--     --script test_nocandynpc.lua <scratch>/new.gba
MODE = os.getenv("MODE") or "gone"
DIR = os.getenv("TEST_DIR") or "./"
NAME = "nocandy_" .. MODE
local HERE = (debug.getinfo(1, "S").source:match("^@(.*/)")) or "./"
dofile(HERE .. "../dexnavchain/test_boot.lua")
local STATE = os.getenv("STATE") or (DIR .. "in_mart.ss")
local SCRIPT = 0x0203F100
local OBJECTS, OBJ_SIZE, NOBJ = 0x02037350, 0x24, 16   -- gObjectEvents
local t0, plan = nil, {}
local function at(d, fn) plan[#plan + 1] = {d, fn} end

local function candy()                     -- Rare Candies (item 68) across the Bag's pockets
  local total = 0
  for pocket = 0, 4 do
    local base = emu:read32(0x02039DD8 + pocket * 8)
    local cap = emu:read8(0x02039DD8 + pocket * 8 + 4)
    if base >= 0x02000000 and base < 0x03000000 and cap > 0 and cap < 250 then
      for i = 0, cap - 1 do
        if emu:read16(base + i * 4) == 68 then total = total + emu:read16(base + i * 4 + 2) end
      end
    end
  end
  return total
end

local function objects()                   -- active object events as "localId@(x,y)", map coordinates
  local out = {}
  for i = 0, NOBJ - 1 do
    local o = OBJECTS + i * OBJ_SIZE
    if emu:read8(o) & 1 == 1 then
      local x, y = emu:read16(o + 0x10), emu:read16(o + 0x12)
      if x >= 0x8000 then x = x - 0x10000 end
      if y >= 0x8000 then y = y - 0x10000 end
      out[#out + 1] = string.format("%d@(%d,%d)", emu:read8(o + 8), x - 7, y - 7)
    end
  end
  return table.concat(out, " ")
end

local function run(bytes)                  -- start a script from EWRAM (as test_candy_mart.lua does)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1)
  emu:write8(0x03000E38, 0)
end
local WARP_MART = {0x39, 0x08, 0x06, 0xFF, 0x04, 0x00, 0x06, 0x00, 0x02}   -- warp 8/6 (4,6); end

local function state(tag)
  local sb1 = emu:read32(0x03005D8C)
  w(string.format("%s: map %d/%d pos (%d,%d) candy %d cb2 %08X lock %d | objects %s", tag,
    emu:read8(sb1 + 4), emu:read8(sb1 + 5), emu:read16(sb1), emu:read16(sb1 + 2), candy(), cb2(), lock(), objects()))
end

if MODE == "gone" then
  at(10, function() run(WARP_MART) end)
  at(260, function() state("in the Mart"); shot("nc1_mart") end)
  at(270, function() tap(K.RIGHT, 16) end)   -- a full step: only possible if (5,6) is empty
  at(330, function() state("stepped right") end)
  at(340, function() tap(K.A) end)
  at(460, function() state("pressed A"); shot("nc2_after_a") end)
  at(480, function() done() end)
elseif MODE == "save" then
  at(10, function() run(WARP_MART) end)
  at(260, function() tap(K.RIGHT, 3) end)    -- he blocks (5,6), so this only turns the player
  at(320, function() state("saved with him loaded"); emu:saveStateFile(STATE); shot("nc3_saved") end)
  at(340, function() done() end)
elseif MODE == "ghost" then
  at(10, function() emu:loadStateFile(STATE) end)
  at(40, function() state("loaded the old state") end)
  at(50, function() tap(K.A) end)
  at(170, function() state("talked to the leftover NPC"); shot("nc4_ghost") end)
  for k = 0, 3 do at(190 + k * 40, function() tap(K.B) end) end
  at(360, function() state("after closing") end)
  at(370, function() run(WARP_MART) end)
  at(620, function() state("re-entered the Mart"); shot("nc5_reentered") end)
  at(640, function() done() end)
end

function TEST(f)
  t0 = t0 or f
  for _, p in ipairs(plan) do if f - t0 == p[1] then p[2]() end end
end
