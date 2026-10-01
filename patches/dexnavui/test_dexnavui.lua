-- The new DexNav screen, driven on the user's save. Route 102 with Ralts made unseen (a shadow): R opens it;
-- shots of screen 0, the ring moved RIGHT x2 and DOWN, screen 1 (R) and back (L); A on the ring's Pokemon (Lotad,
-- after LEFT x2 / UP) registers it and drops to the field; R again shows "Hunting" and STOP; A stops it; the START
-- menu's DexNav then B goes back to the start menu. A on the shadow must change nothing and keep the screen.
-- Then Lilycove and Petalburg, one shot of each screen.
-- Screenshots dexnavui_*.png; the log dexnavui_log.txt.
NAME = "dexnavui"
dofile((DIR or "./") .. "../dexnavchain/test_boot.lua")
local SCRIPT, STATE = 0x0203F100, 0x0203A660
local function sb1() return emu:read32(0x03005D8C) end
local function setseen(n, on)
  local a = sb1() + 0x560 + (n >> 3)
  local b = emu:read8(a)
  if on then b = b | (1 << (n & 7)) else b = b & ~(1 << (n & 7)) & 0xFF end
  emu:write8(a, b)
end
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1)
  emu:write8(0x03000E38, 0)
end
local function log(tag)
  w(string.format("%-16s cb2 %08X lock %d | hunt flags %02X species %d chain %d", tag, cb2(), lock(),
    emu:read8(STATE + 9), emu:read16(STATE + 2), emu:read16(STATE + 4)))
end
local t0, plan = nil, {}
local function at(d, fn) plan[#plan + 1] = {d, fn} end
local d = 10
local function step(gap, fn) d = d + gap; at(d, fn) end

step(0, function() setseen(280, false); setseen(270, true); emu:write8(STATE + 9, emu:read8(STATE + 9) & 0xFE)
  run({0x39, 0, 17, 0xFF, 10, 0, 7, 0, 0x02}) end)                       -- Route 102
step(390, function() log("route 102"); tap(K.R) end)
step(260, function() log("open (R)"); shot("dexnavui_01_r102") end)
step(20, function() tap(K.RIGHT) end)
step(30, function() tap(K.RIGHT) end)
step(40, function() shot("dexnavui_02_right2") end)
step(20, function() tap(K.DOWN) end)
step(40, function() shot("dexnavui_03_down") end)
step(20, function() tap(K.LEFT) end)
step(30, function() tap(K.LEFT) end)
step(40, function() shot("dexnavui_03b_shadow") end)                    -- Ralts, not seen
step(20, function() tap(K.A) end)                                       -- refused: buzz, stays open
step(90, function() log("A on the shadow") end)
step(20, function() tap(K.RIGHT) end)
step(30, function() tap(K.RIGHT) end)
step(20, function() tap(K.DOWN) end)
step(40, function() shot("dexnavui_04_down2") end)
step(20, function() tap(K.R) end)
step(60, function() shot("dexnavui_05_screen1") end)
step(20, function() tap(K.L) end)
step(60, function() shot("dexnavui_06_back") end)
step(20, function() tap(K.UP) end)                                      -- to the top row (Water)
step(30, function() tap(K.UP) end)
step(40, function() shot("dexnavui_07_top") end)
step(20, function() tap(K.A) end)                                       -- register what is under the ring
step(300, function() log("after A"); shot("dexnavui_08_field") end)
step(60, function() tap(K.R) end)
step(260, function() log("open again"); shot("dexnavui_09_hunting") end)
step(20, function() tap(K.A) end)                                       -- stop it
step(300, function() log("after stop") end)
step(20, function() tap(K.START) end)                                   -- the START menu's DexNav
step(60, function()
  local n, idx = emu:read8(0x0203760F), nil
  for i = 0, n - 1 do if emu:read8(0x02037610 + i) == 13 then idx = i end end
  w("start menu dexnav at " .. tostring(idx)); emu:write8(0x0203760E, idx or 0); tap(K.B) end)
step(60, function() tap(K.START) end)
step(80, function() tap(K.A) end)
step(260, function() log("open (START)"); shot("dexnavui_10_start") end)
step(20, function() tap(K.B) end)
step(200, function() log("B"); shot("dexnavui_11_back_to_menu") end)
step(20, function() tap(K.B) end)
for _, s in ipairs({{"lilycove", 0, 5, 40, 20}, {"petalburg", 0, 0, 15, 15}}) do
  step(100, function() run({0x39, s[2], s[3], 0xFF, s[4], 0, s[5], 0, 0x02}) end)
  step(390, function() tap(K.R) end)
  step(260, function() log(s[1]); shot("dexnavui_" .. s[1] .. "_0") end)
  step(20, function() tap(K.R) end)
  step(60, function() shot("dexnavui_" .. s[1] .. "_1") end)
  step(20, function() tap(K.B) end)
  step(200, function() log(s[1] .. " closed") end)
end
step(60, function() log("end"); done() end)

function TEST(f)
  t0 = t0 or f
  local dd = f - t0
  for _, p in ipairs(plan) do if dd == p[1] then p[2]() end end
end
