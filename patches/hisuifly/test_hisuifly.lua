-- Flying from the Hisui map once 0x431E is set (hisuifly, 2026-10-22). 1. 0x431E clear: Coronet Highlands (37/106),
-- open the map, the box to Firespit Island, A: nothing may happen (no Braviary, no warp, the map stays up); B closes
-- it, still on 37/106. 2. 0x431E set: the same, A: Mingyao's Braviary, A, and we are on Firespit Island (37/105).
-- 3. From there to Prelude Beach (37/104, her warp 1). 4. Sinnoh, unchanged: Oreburgh (36/3), LEFT x3 = Jubilife, A
-- flies there. Log hfly_log.txt, screenshots hf_*.png.
-- env: HFLY_DIR (output folder, with the slash), HFLY_HERE (this folder, with the slash)
NAME = "hfly"
DIR = os.getenv("HFLY_DIR") or "./"
local HERE = os.getenv("HFLY_HERE") or "./"
dofile(HERE .. "../dexnavchain/test_boot.lua")
local SCRIPT = 0x0203F100
local CB2_INIT = 0x08FF3141
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1); emu:write8(0x03000E38, 0)
end
local function flagbyte(f)                  -- where the hack keeps a flag (patches/paldea/test_paldea.lua's)
  local sb1, sb2 = emu:read32(0x03005D8C), emu:read32(0x03005D90)
  if f < 0x4000 then return sb1 + 0x1270 + (f >> 3) end
  local i = (f - 0x4000) >> 3
  if i <= 0x33 then return sb1 + 0x988 + i end
  if i <= 0x67 then return sb1 + 0x3B24 + i - 0x34 end
  if i <= 0x9B then return sb2 + 0x5C + i - 0x68 end
  return sb2 + 0x28 + i - 0x9C
end
local function flag(f) return (emu:read8(flagbyte(f)) >> (f & 7)) & 1 end
local function mapdata()
  for i = 0, 15 do
    local t = 0x03005E00 + 40 * i
    local f = emu:read32(t)
    if emu:read8(t + 4) ~= 0 and f >= 0x08FF3000 and f < 0x08FF3800 then return t + 8 end
  end
end
local function cur(tag)
  local d = mapdata()
  if not d then w(string.format("%-20s (no map task) cb2 %08X", tag, cb2())); return end
  local c = emu:read16(d + 14)
  w(string.format("%-20s cursor col %2d row %2d | place %3d | map task state %d | cb2 %08X", tag, c & 31, c >> 5,
    emu:read16(d + 18), emu:read16(d + 6), cb2()))
end
local function where(tag)
  local sb1 = emu:read32(0x03005D8C)
  w(string.format("%-20s map %d/%d (%d,%d) cb2 %08X map task %s flag 431E=%d", tag, emu:read8(sb1 + 4),
    emu:read8(sb1 + 5), emu:read16(sb1), emu:read16(sb1 + 2), cb2(), mapdata() and "up" or "gone", flag(0x431E)))
end
local t0, plan, d = nil, {}, 10
local function step(gap, fn) d = d + gap; plan[#plan + 1] = {d, fn} end
local function open_map() step(20, function() emu:write32(0x030022C4, CB2_INIT) end); step(120, function() end) end
local function press(k, n, gap) for i = 1, n do step(gap or 12, function() tap(k) end) end end
local CORONET = {0x39, 37, 106, 1, 0, 0, 0, 0, 0x02}

-- 1. before Rei and Cogita's report
step(0, function() run({0x2A, 0x1E, 0x43, table.unpack(CORONET)}) end)       -- clearflag 0x431E; warp 37/106
step(420, function() where("1 coronet") end)
open_map()
step(10, function() cur("1 open"); shot("hf_1a_open") end)
press(K.RIGHT, 11, 10)                                                         -- (15,9) -> (26,9)
press(K.UP, 4, 10)                                                             -- -> (26,5) Firespit Island
step(20, function() cur("1 on firespit"); shot("hf_1b_firespit") end)
step(10, function() tap(K.A) end)
step(120, function() shot("hf_1c_after_a_120") end)
step(360, function() cur("1 A on firespit"); where("1 A on firespit"); shot("hf_1d_after_a") end)
step(10, function() tap(K.B) end)
step(200, function() where("1 closed"); shot("hf_1e_closed") end)
-- 2. after it
step(10, function() run({0x29, 0x1E, 0x43, table.unpack(CORONET)}) end)      -- setflag 0x431E; warp 37/106
step(420, function() where("2 coronet") end)
open_map()
step(10, function() cur("2 open"); shot("hf_2a_open") end)
press(K.RIGHT, 11, 10)
press(K.UP, 4, 10)
step(20, function() cur("2 on firespit"); shot("hf_2b_firespit") end)
step(10, function() tap(K.A) end)
step(60, function() shot("hf_2c_after_a_60") end)
step(180, function() where("2 braviary"); shot("hf_2d_braviary") end)
step(10, function() tap(K.A) end)                                              -- waitbuttonpress
step(500, function() where("2 flew"); shot("hf_2e_flew") end)
-- 3. Firespit Island -> Prelude Beach
open_map()
step(10, function() cur("3 open"); shot("hf_3a_open") end)
press(K.LEFT, 16, 10)                                                          -- (26,5) -> (10,5)
press(K.DOWN, 9, 10)                                                           -- -> (10,14) Prelude Beach
step(20, function() cur("3 on prelude"); shot("hf_3b_prelude") end)
step(10, function() tap(K.A) end)
step(240, function() where("3 braviary"); shot("hf_3c_braviary") end)
step(10, function() tap(K.A) end)
step(500, function() where("3 flew"); shot("hf_3d_flew") end)
-- 4. Sinnoh, unchanged
step(10, function() run({0x39, 36, 3, 1, 0, 0, 0, 0, 0x02}) end)              -- Sinnoh: Oreburgh
step(420, function() where("4 oreburgh") end)
open_map()
press(K.LEFT, 3, 12)                                                           -- Oreburgh (9,15) -> Jubilife (6,15)
step(20, function() cur("4 jubilife"); shot("hf_4a_jubilife") end)
step(10, function() tap(K.A) end)
step(480, function() where("4 sinnoh after A"); shot("hf_4b_sinnoh_flew"); done() end)

function TEST(f)
  t0 = t0 or f
  for _, p in ipairs(plan) do
    if f - t0 == p[1] then
      local ok, err = pcall(p[2])
      if not ok then w("ERROR " .. tostring(err)); done() end
    end
  end
end
