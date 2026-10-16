-- No flying from the Hisui map (HISUI_FLY = False, 2026-10-08). Hisui: warp to Coronet Highlands (37/106), open the
-- map, the box to Firespit Island, A: nothing may happen (no Braviary, no warp, the map stays up); A on Coronet
-- Highlands itself too; B closes it, back on 37/106. Sinnoh, unchanged: Oreburgh (36/3), open, LEFT x3 = Jubilife,
-- A flies there (the save has been there). Log nofly_log.txt, screenshots nf_*.png.
-- env: NOFLY_DIR (output folder, with the slash), NOFLY_HERE (this folder, with the slash)
NAME = "nofly"
DIR = os.getenv("NOFLY_DIR") or "./"
local HERE = os.getenv("NOFLY_HERE") or "./"
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
local function mapdata()
  for i = 0, 15 do
    local t = 0x03005E00 + 40 * i
    local f = emu:read32(t)
    if emu:read8(t + 4) ~= 0 and f >= 0x08FF3000 and f < 0x08FF3800 then return t + 8 end
  end
end
local function cur(tag)
  local d = mapdata()
  if not d then w(string.format("%-18s (no map task) cb2 %08X", tag, cb2())); return end
  local c = emu:read16(d + 14)
  w(string.format("%-18s cursor col %2d row %2d | place %3d | map task state %d | cb2 %08X", tag, c & 31, c >> 5,
    emu:read16(d + 18), emu:read16(d + 6), cb2()))
end
local function where(tag)
  local sb1 = emu:read32(0x03005D8C)
  w(string.format("%-18s map %d/%d (%d,%d) cb2 %08X map task %s", tag, emu:read8(sb1 + 4), emu:read8(sb1 + 5),
    emu:read16(sb1), emu:read16(sb1 + 2), cb2(), mapdata() and "up" or "gone"))
end
local t0, plan, d = nil, {}, 10
local function step(gap, fn) d = d + gap; plan[#plan + 1] = {d, fn} end
local function open_map() step(20, function() emu:write32(0x030022C4, CB2_INIT) end); step(120, function() end) end
local function press(k, n, gap) for i = 1, n do step(gap or 12, function() tap(k) end) end end

step(0, function() run({0x39, 37, 106, 1, 0, 0, 0, 0, 0x02}) end)                -- Hisui: Coronet Highlands
step(420, function() where("hisui") end)
open_map()
step(10, function() cur("hisui open"); shot("nf_1_hisui_open") end)
step(10, function() tap(K.A) end)                                                 -- A where you are
step(300, function() cur("A on coronet"); where("A on coronet"); shot("nf_2_a_here") end)
press(K.RIGHT, 11, 10)                                                            -- (15,9) -> (26,9)
press(K.UP, 4, 10)                                                                -- -> (26,5) Firespit Island
step(20, function() cur("on firespit"); shot("nf_3_firespit") end)
step(10, function() tap(K.A) end)
step(120, function() shot("nf_4_after_a_120") end)
step(360, function() cur("A on firespit"); where("A on firespit"); shot("nf_5_after_a") end)
step(10, function() tap(K.B) end)
step(200, function() where("hisui closed"); shot("nf_6_closed") end)
step(10, function() run({0x39, 36, 3, 1, 0, 0, 0, 0, 0x02}) end)                 -- Sinnoh: Oreburgh
step(420, function() where("oreburgh") end)
open_map()
press(K.LEFT, 3, 12)                                                              -- Oreburgh (9,15) -> Jubilife (6,15)
step(20, function() cur("jubilife"); shot("nf_7_jubilife") end)
step(10, function() tap(K.A) end)
step(480, function() where("sinnoh after A"); shot("nf_8_sinnoh_flew"); done() end)

function TEST(f)
  t0 = t0 or f
  for _, p in ipairs(plan) do
    if f - t0 == p[1] then
      local ok, err = pcall(p[2])
      if not ok then w("ERROR " .. tostring(err)); done() end
    end
  end
end
