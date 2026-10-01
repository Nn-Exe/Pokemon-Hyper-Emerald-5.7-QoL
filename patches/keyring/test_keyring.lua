-- The key-item ring. Registers the first four key items of the Bag found among the bikes, rods, Itemfinder, Journal,
-- Pokeblock case and Wailmer Pail, then: SELECT on Route 102 (shot), B (every sprite palette tag and colour must be
-- as before), SELECT + A (the PC menu, logged off with B), two items only (grey boxes), SELECT in Lilycove, on rainy
-- Route 119 and in a Pokemon Center (shots, palettes restored each time), and last SELECT + UP uses the first item.
-- Screenshots keyring_*.png; the log keyring_log.txt.
NAME = "keyring"
dofile((DIR or "./") .. "../dexnavchain/test_boot.lua")
local SCRIPT = 0x0203F100
local function sb1() return emu:read32(0x03005D8C) end
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1); emu:write8(0x03000E38, 0)
end
local function palstate()
  local t = {}
  for i = 0, 15 do t[#t + 1] = emu:read16(0x03000CF0 + 2 * i) end
  for i = 0, 255 do t[#t + 1] = emu:read16(0x02037914 + 2 * i); t[#t + 1] = emu:read16(0x02037D14 + 2 * i) end
  return table.concat(t, ",")
end
local function sprites_in_use()
  local n = 0
  for i = 0, 63 do if emu:read8(0x02020630 + 0x44 * i + 0x3E) & 1 == 1 then n = n + 1 end end
  return n
end
local items = {}
local function register(n)
  local offs = {0x496, 0x9C2, 0x9C4, 0x9C6}
  for i = 1, 4 do emu:write16(sb1() + offs[i], (i <= n and items[i]) or 0) end
end
local before, spr_before
local t0, plan, d = nil, {}, 10
local function step(gap, fn) d = d + gap; plan[#plan + 1] = {d, fn} end
local function state(tag)
  w(string.format("%-26s cb2 %08X lock %d sprites in use %d avatar %02X", tag, cb2(), lock(), sprites_in_use(),
    emu:read8(0x02037590)))
end
local function ring(tag, gap)
  step(gap or 20, function() before = palstate(); spr_before = sprites_in_use(); tap(K.SEL) end)
  step(40, function() state(tag .. " open"); shot("keyring_" .. tag) end)
  step(10, function() tap(K.B) end)
  step(40, function()
    state(tag .. " closed")
    w(string.format("  palettes restored: %s, sprites back to %d: %s", tostring(palstate() == before), spr_before,
      tostring(sprites_in_use() == spr_before)))
  end)
end

step(0, function()
  local key = emu:read32(0x02039DD8 + 4 * 8)
  local cap = emu:read8(0x02039DD8 + 4 * 8 + 4)
  local want = {[259] = 1, [272] = 1, [262] = 1, [263] = 1, [264] = 1, [261] = 1, [363] = 1, [260] = 1, [360] = 1}
  for i = 0, cap - 1 do
    local it = emu:read16(key + 4 * i)
    if want[it] and #items < 4 then items[#items + 1] = it end
  end
  w("registering " .. table.concat(items, ", "))
  register(4)
  run({0x39, 0, 17, 0xFF, 10, 0, 7, 0, 0x02})                  -- Route 102
end)
step(400, function() state("route 102") end)
ring("r102_four")
step(20, function() tap(K.SEL) end)                            -- the PC
step(40, function() tap(K.A) end)
step(120, function() state("pc menu"); shot("keyring_pc") end)
for k = 1, 6 do step(40, function() tap(K.B) end) end
step(120, function() state("pc logged off") end)
step(10, function() register(2) end)
ring("r102_two")
step(10, function() register(4) end)
for _, s in ipairs({{"lilycove", 0, 5, 30, 10}, {"route119_rain", 0, 34, 10, 40}, {"centre", 8, 1, 7, 6}}) do
  step(20, function() run({0x39, s[2], s[3], 0xFF, s[4], 0, s[5], 0, 0x02}) end)
  step(420, function() state(s[1]) end)
  ring(s[1])
end
step(20, function() tap(K.SEL) end)                            -- UP: the first item
step(40, function() tap(K.UP) end)
step(150, function() state("after UP"); shot("keyring_used_up") end)
step(30, function() done() end)

function TEST(f)
  t0 = t0 or f
  for _, p in ipairs(plan) do if f - t0 == p[1] then p[2]() end end
end
