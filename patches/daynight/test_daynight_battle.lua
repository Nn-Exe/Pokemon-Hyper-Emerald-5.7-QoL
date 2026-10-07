-- Day/Night Off in a battle and in the Bag at 23:00 on Route 102 (BIT=1, the default here; BIT=0 for the game as it
-- was). Logs how many screen colours differ from the game's finished palette on the field, in the Bag, at the
-- battle's action menu and back on the field: all 0 with BIT=1.
local BIT = tonumber(os.getenv("BIT") or "1")
NAME = "daynight_battle" .. BIT
dofile((DIR or "./") .. "../dexnavchain/test_boot.lua")
local SCRIPT = 0x0203F100
local ACTION = 0x08057589
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1); emu:write8(0x03000E38, 0)
end
local function sb2() return emu:read32(0x03005D90) end
local function tinted()
  local n = 0
  for i = 0, 0x3FE, 2 do
    if emu:read16(0x05000000 + i) ~= emu:read16(0x02037B14 + i) then n = n + 1 end
  end
  return n
end
local function note(tag) w(string.format("%-14s tinted colours %3d  cb2 %08X", tag, tinted(), cb2())); shot("dnb" .. BIT .. "_" .. tag) end
local t0, stage, mark = nil, "start", nil
function TEST(f)
  t0 = t0 or f
  local d = f - t0
  if d == 5 then
    local off = emu:read8(sb2() + 0x9A); if off >= 128 then off = off - 256 end
    emu:write8(sb2() + 0x9A, (off + emu:read8(0x03005CFA) - 23) % 24)
    local b = emu:read8(sb2() + 0x15)
    emu:write8(sb2() + 0x15, BIT == 1 and (b | 0x10) or (b & 0xEF))
  end
  if d == 45 then run({0x39, 0, 17, 0xFF, 10, 0, 7, 0, 0x02}) end
  if d == 350 then note("field") ; tap(K.START) end
  if d == 380 then tap(K.DOWN) end
  if d == 410 then tap(K.DOWN) end
  if d == 440 then tap(K.A) end
  if d == 600 then note("bag"); tap(K.B) end
  if d == 720 then tap(K.B) end
  if d == 800 then run({0xB6, 129, 0, 5, 0, 0, 0xB7, 0x02}); stage = "battle"; mark = d end
  if stage == "battle" then
    if d == mark + 200 then note("battle_intro") end
    if cb2() == BATTLE and emu:read32(0x03005D60) == ACTION and d > mark + 60 then
      stage = "menu"; mark = d
    elseif d % 20 == 0 and cb2() == BATTLE then tap(K.A) end
  elseif stage == "menu" then
    if d == mark + 30 then note("battle_menu"); emu:write8(0x020244AC, 3); tap(K.A) end      -- Run
    if d > mark + 60 and d % 30 == 0 and cb2() ~= OVERWORLD then tap(K.A) end
    if d > mark + 60 and cb2() == OVERWORLD and lock() == 0 then stage = "after"; mark = d end
  elseif stage == "after" then
    if d == mark + 60 then note("field_after"); done(); stage = "end" end
  end
  if d > 5000 and stage ~= "end" then w("TIMEOUT in " .. stage); done(); stage = "end" end
end
