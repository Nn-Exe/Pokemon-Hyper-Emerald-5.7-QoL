-- Faster surfing. Warps onto Route 109's water at (3,48) - a warp onto surfable water starts the player surfing -
-- with a Max Repel's 250 steps (VAR 0x4021) so no battle cuts in, turns east, then holds RIGHT. MODE (env):
--   speed - AUTO (0/1: Auto Run off/on) and HOLDB (0/1): RIGHT held 64 frames, B held with it if HOLDB; logs tiles
--   land  - Auto Run off, B + RIGHT held 240 frames: across the 24 tiles of water to the beach at x 27, where the
--           game's own dismount must put the player on foot
-- The position is logged every 16 frames of the hold. A PokeNav Match Call rolls every 10 steps and stopped two runs
-- at x 13, so the test keeps its step counter (sMatchCallState+6, 0x0203CD86) at 0.
-- Screenshots <NAME>_*.png; the log in <NAME>_log.txt.
NAME = "fastsurf_" .. (os.getenv("MODE") or "speed") .. "_a" .. (os.getenv("AUTO") or "0") .. "_b" .. (os.getenv("HOLDB") or "0")
dofile((DIR or "./") .. "../dexnavchain/test_boot.lua")
local MODE = os.getenv("MODE") or "speed"
local AUTO, HOLDB = os.getenv("AUTO") == "1", os.getenv("HOLDB") == "1"
local SCRIPT, AVATAR = 0x0203F100, 0x02037590
local t0, plan = nil, {}
local function at(d, fn) plan[#plan + 1] = {d, fn} end
local function sb1() return emu:read32(0x03005D8C) end
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1)
  emu:write8(0x03000E38, 0)
end
local function pos()
  local obj = 0x02037350 + 0x24 * emu:read8(AVATAR + 5)
  return emu:read16(obj + 0x10) - 7, emu:read16(obj + 0x12) - 7
end
local function state(tag)
  local x, y = pos()
  w(string.format("%-10s map %d/%d (%d,%d) avatar flags %02X surfing %d  cb2 %08X lock %d", tag,
    emu:read8(sb1() + 4), emu:read8(sb1() + 5), x, y, emu:read8(AVATAR), (emu:read8(AVATAR) >> 3) & 1, cb2(), lock()))
end

local x0
at(10, function()
  emu:write16(sb1() + 0x139C + 0x21 * 2, (84 << 8) | 250)             -- a Max Repel, 250 steps
  local sb2 = emu:read32(0x03005D90)
  emu:write8(sb2 + 0x13, (MODE == "speed" and AUTO) and 4 or 0)      -- Auto Run
  run({0x39, 0, 24, 0xFF, 3, 0, 48, 0, 0x02})                        -- warp: Route 109 (3,48), on the water
end)
at(400, function() state("warped"); tap(K.RIGHT, 3) end)             -- a tap turns without a step
at(460, function() state("facing"); x0 = pos(); shot(NAME .. "_start") end)
local HOLD = MODE == "land" and 240 or 64
at(470, function()
  tap(K.RIGHT, HOLD)
  if HOLDB or MODE == "land" then tap(K.B, HOLD + 2) end
end)
for k = 0, HOLD + 8, 4 do                                            -- the track, and anything that interrupts it
  at(470 + k, function()
    local x = pos()
    emu:write8(0x0203CD80 + 6, 0)       -- sMatchCallState.stepCounter: no PokeNav call rolls during the test
    if k % 16 == 0 or lock() ~= 0 then w(string.format("  +%3d frames: x %d%s", k, x, lock() ~= 0 and "  (screen locked: a call?)" or "")) end
  end)
end
at(470 + 20, function() shot(NAME .. "_moving") end)
at(470 + 22, function() shot(NAME .. "_moving2") end)
at(470 + HOLD + 60, function()
  local x = pos()
  state("after")
  w(string.format("RESULT %s auto=%s B=%s: %d tiles in %d frames held", MODE, tostring(AUTO), tostring(HOLDB or MODE == "land"),
    x - x0, HOLD))
  shot(NAME .. "_end")
end)
at(470 + HOLD + 140, function() state("settled"); shot(NAME .. "_settled"); done() end)

function TEST(f)
  t0 = t0 or f
  local d = f - t0
  for _, p in ipairs(plan) do if d == p[1] then p[2]() end end
end
