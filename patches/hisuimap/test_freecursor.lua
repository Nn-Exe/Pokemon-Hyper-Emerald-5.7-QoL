-- The region map's free cursor. Sinnoh: warp to Oreburgh (36/3), open the map (CB2 set directly); the box starts on
-- the marker; RIGHT once, RIGHT held (auto-repeat), back LEFT to Oreburgh, LEFT x3 = Jubilife, A flies there if
-- Jubilife is visited on this save; then open again, walk the box to the top rows (the name box must move to the
-- bottom) and against the top-left corner (it must stop). Hisui: warp to 37/106, open, D/L/U steps, B.
-- The cursor's cell and the name box come from the map task's data ([7] cell, [6] box, [9] the place shown).
-- Screenshots fc_*.png; the log freecursor_log.txt.
NAME = "freecursor"
dofile((DIR or "./") .. "../dexnavchain/test_boot.lua")
local SCRIPT = 0x0203F100
local CB2_INIT = tonumber(os.getenv("CB2") or "0x08FF3141")
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
  w(string.format("%-18s cursor col %2d row %2d | box %s | place %3d | marker cell %d", tag, c & 31, c >> 5,
    emu:read16(d + 12) == 0 and "top" or "bottom", emu:read16(d + 18), emu:read16(d + 2)))
end
local function where(tag)
  local sb1 = emu:read32(0x03005D8C)
  w(string.format("%-18s map %d/%d (%d,%d) cb2 %08X", tag, emu:read8(sb1 + 4), emu:read8(sb1 + 5),
    emu:read16(sb1), emu:read16(sb1 + 2), cb2()))
end
local t0, plan, d = nil, {}, 10
local function step(gap, fn) d = d + gap; plan[#plan + 1] = {d, fn} end
local function open_map() step(20, function() emu:write32(0x030022C4, CB2_INIT) end); step(120, function() end) end
local function press(k, n, gap) for i = 1, n do step(gap or 12, function() tap(k) end) end end

step(0, function() run({0x39, 36, 3, 1, 0, 0, 0, 0, 0x02}) end)                 -- Oreburgh
step(400, function() where("oreburgh") end)
open_map()
step(10, function() cur("open"); shot("fc_1_open") end)
press(K.RIGHT, 1)
step(20, function() cur("right x1"); shot("fc_2_right1") end)
step(10, function() tap(K.RIGHT, 60) end)                                          -- held 60 frames
step(80, function() cur("right held 60f"); shot("fc_3_held") end)
step(10, function() tap(K.LEFT, 60) end)                                           -- and back
step(80, function() cur("left held 60f") end)
step(10, function() tap(K.RIGHT, 1) end)
step(20, function() cur("reset") end)
step(10, function() emu:write32(0x030022C4, 0x08085E5D) end)                      -- (close without fading)
step(60, function() end)
open_map()
press(K.LEFT, 3, 12)                                                              -- Oreburgh (9,15) -> Jubilife (6,15)
step(20, function() cur("jubilife"); shot("fc_4_jubilife") end)
step(10, function() tap(K.A) end)
step(480, function() where("after A"); shot("fc_5_after_a") end)
open_map()
step(10, function() cur("open again") end)
press(K.UP, 14, 10)
step(20, function() cur("top rows"); shot("fc_6_top") end)
press(K.LEFT, 35, 8)
press(K.UP, 5, 8)
step(20, function() cur("corner"); shot("fc_7_corner") end)
step(10, function() tap(K.B) end)
step(200, function() where("closed") end)
step(10, function() run({0x39, 37, 106, 1, 0, 0, 0, 0, 0x02}) end)                -- Hisui
step(420, function() where("hisui") end)
open_map()
step(10, function() cur("hisui open"); shot("fc_8_hisui") end)
press(K.DOWN, 4, 12)
press(K.LEFT, 6, 12)
step(20, function() cur("hisui moved"); shot("fc_9_hisui_moved") end)
press(K.UP, 9, 12)
step(20, function() cur("hisui up"); shot("fc_10_hisui_up") end)
step(10, function() tap(K.B) end)
step(200, function() where("hisui closed"); done() end)

function TEST(f)
  t0 = t0 or f
  for _, p in ipairs(plan) do
    if f - t0 == p[1] then
      local ok, err = pcall(p[2])
      if not ok then w("ERROR " .. tostring(err)); done() end
    end
  end
end
