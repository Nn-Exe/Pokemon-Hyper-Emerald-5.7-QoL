-- Oval Charm. Set DIR (game.gba/game.sav and output) and HERE (this folder).
--   MODE=GIFT (default): warp below the Day-Care Man on Route 117, talk to him, page through, check the Bag
--     for item 114, talk again. Screenshots oc_*.png. Needs a save where the Hoenn League is beaten.
--     NOHOF=1 clears flag 0x864 first: he must then say only his usual line and give nothing.
--   MODE=BAG: gives the Oval Charm and item 644, opens Key Items: oc_bag_oval.png, oc_bag_tester.png.
--   MODE=ODDS: needs a test ROM whose egg_roll reads its compatibility score from EWRAM 0x0203F201
--     (a stub `movs r0, #N; bx lr` this script writes); runs egg_roll 5000 times per score, with and
--     without the charm, and logs the hit rate. ROLL = egg_roll's address.
NAME = "ovalcharm"
DIR = DIR or "./"
HERE = HERE or DIR
dofile(HERE .. "../dexnavchain/test_boot.lua")
local MODE = os.getenv("MODE") or "GIFT"
local ROLL = tonumber(os.getenv("ROLL") or "0x08FF5601")
local SCRIPT = 0x0203F100
local function le32(v) return {v & 0xFF, (v >> 8) & 0xFF, (v >> 16) & 0xFF, (v >> 24) & 0xFF} end
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1)
  emu:write8(0x03000E38, 0)
end
local function has_oval()
  local base = emu:read32(0x02039DD8 + 4 * 8)
  local cap = emu:read8(0x02039DD8 + 4 * 8 + 4)
  for i = 0, cap - 1 do if emu:read16(base + i * 4) == 114 then return true end end
  return false
end
local function where()
  local sb1 = emu:read32(0x03005D8C)
  return string.format("map %d/%d pos (%d,%d)", emu:read8(sb1 + 4), emu:read8(sb1 + 5), emu:read16(sb1), emu:read16(sb1 + 2))
end
local plan, t0 = {}, nil
local function at(d, fn) plan[#plan + 1] = {d, fn} end

if MODE == "BAG" then
  -- the Bag's Key Items with the Oval Charm (and item 644, the Script Tester) at the top
  at(30, function() run({0x44, 114, 0, 1, 0, 0x44, 0x84, 0x02, 1, 0, 0x02}) end)
  at(200, function()
    local base = emu:read32(0x02039DD8 + 4 * 8)
    local cap = emu:read8(0x02039DD8 + 4 * 8 + 4)
    local want, slot = {114, 644}, 0
    for _, id in ipairs(want) do
      for i = 0, cap - 1 do
        if emu:read16(base + i * 4) == id then
          local a, b = emu:read16(base + slot * 4), emu:read16(base + slot * 4 + 2)
          emu:write16(base + i * 4, a); emu:write16(base + i * 4 + 2, b)
          emu:write16(base + slot * 4, id); emu:write16(base + slot * 4 + 2, 1)
        end
      end
      slot = slot + 1
    end
  end)
  at(220, function() tap(K.START) end)
  at(250, function() tap(K.DOWN) end) at(270, function() tap(K.DOWN) end)
  at(290, function() tap(K.A) end)
  at(420, function() tap(K.LEFT) end)
  at(480, function() shot("oc_bag_oval") end)
  at(490, function() tap(K.DOWN) end)
  at(540, function() shot("oc_bag_tester"); done() end)
elseif MODE == "GIFT" then
  at(30, function() w("start: " .. where() .. " oval " .. tostring(has_oval()))
    local s = {0x39, 0, 32, 0xFF, 47, 0, 5, 0, 0x02}                   -- warp 0.32 to (47,5), below him
    if os.getenv("NOHOF") == "1" then s = {0x2A, 0x64, 0x08, 0x39, 0, 32, 0xFF, 47, 0, 5, 0, 0x02} end
    run(s) end)
  at(330, function() w("warped: " .. where()); tap(K.UP) end)
  at(360, function() tap(K.A) end)
  local d = 420
  for i = 1, 14 do
    at(d, function() shot(string.format("oc_%02d", i)) end)
    at(d + 10, function() tap(K.A) end)
    d = d + 70
  end
  at(d, function() w("after gift: oval in bag " .. tostring(has_oval()) .. ", lock " .. lock()) end)
  at(d + 60, function() tap(K.A) end)                                -- talk again: his usual line
  at(d + 150, function() shot("oc_again") end)
  for i = 1, 8 do at(d + 160 + i * 40, function() tap(K.B) end) end
  at(d + 600, function() w("end: lock " .. lock()); done() end)
else
  local CALL = 0x0203F300
  local OUT = 0x0203F400
  -- push {r4, r5, lr}; ldr r4, =5000; movs r5, #0
  -- loop: movs r0, #0; ldr r3, =ROLL; bl callr3; adds r5, r5, r0; subs r4, #1; bne loop
  -- ldr r0, =OUT; str r5, [r0]; pop {r4, r5}; pop {r0}; bx r0; callr3: bx r3; pool at +0x20
  -- (bytes from Keystone)
  local stub = {0x30,0xB5, 0x07,0x4C, 0x00,0x25,
                0x00,0x20, 0x06,0x4B, 0x00,0xF0,0x08,0xF8, 0x2D,0x18, 0x01,0x3C, 0xF8,0xD1,
                0x04,0x48, 0x05,0x60, 0x30,0xBC, 0x01,0xBC, 0x00,0x47, 0x18,0x47}
  local pool = {}
  for _, b in ipairs(le32(5000)) do pool[#pool + 1] = b end
  for _, b in ipairs(le32(ROLL)) do pool[#pool + 1] = b end
  for _, b in ipairs(le32(OUT)) do pool[#pool + 1] = b end
  local function setup(score)
    for i, b in ipairs(stub) do emu:write8(CALL + i - 1, b) end
    for i, b in ipairs(pool) do emu:write8(CALL + 0x20 + i - 1, b) end
    emu:write16(0x0203F200, 0x2000 | score)      -- movs r0, #score
    emu:write16(0x0203F202, 0x4770)              -- bx lr
    emu:write32(OUT, 0xFFFFFFFF)
  end
  local t = 30
  local function trial(score, label)
    at(t, function() setup(score); local b = le32(CALL | 1); run({0x23, b[1], b[2], b[3], b[4], 0x02}) end)
    at(t + 200, function() w(string.format("%s score %d: %d / 5000 = %.1f%%", label, score,
      emu:read32(OUT), emu:read32(OUT) / 50)) end)
    t = t + 240
  end
  for _, s in ipairs({0, 20, 50, 70}) do trial(s, "no charm ") end
  at(t, function() run({0x44, 114, 0, 1, 0, 0x02}); end)                  -- additem Oval Charm
  t = t + 200
  at(t, function() w("charm in bag: " .. tostring(has_oval())) end)
  t = t + 10
  for _, s in ipairs({0, 20, 50, 70}) do trial(s, "with charm") end
  at(t + 10, function() done() end)
end

function TEST(f)
  t0 = t0 or f
  for _, p in ipairs(plan) do if f - t0 == p[1] then p[2]() end end
end
