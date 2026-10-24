-- Kitakami's wild Pokemon: warp into tall grass (or a cave's floor) and walk left and right until a battle starts;
-- log the wild Pokemon's species and level (gEnemyParty, unencrypted here: species +0x20, level +0x54), then run.
-- AREA: r101 (0/16, 16,4: the game's own Route 101, served by the wild table this patch moved; the same on the ROM
-- before the patch). Kitakami has no land Pokemon since 2026-10-16 (no road, no Oni Mountain, no den): its own are
-- in Mossui's water, which test_dexnav lists. ROUNDS battles each.
local AREA = os.getenv("AREA") or "r101"
local ROUNDS = tonumber(os.getenv("ROUNDS") or "4")
NAME = "wild_" .. AREA
dofile((HERE or DIR or "./") .. "../dexnavchain/test_boot.lua")
local SCRIPT, ENEMY = 0x0203F100, 0x02024744
local PLACES = {r101 = {0, 16, 16, 4, 14, 18}}
local P = PLACES[AREA]
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1); emu:write8(0x03000E38, 0)
end
local function where()
  local s = emu:read32(0x03005D8C)
  local id = emu:read8(0x02037590 + 5)
  local o = 0x02037350 + 0x24 * id
  return emu:read8(s + 4), emu:read8(s + 5), emu:read16(o + 0x10) - 7, emu:read16(o + 0x12) - 7
end
local t0, phase, dir, battles, inb, held = nil, "warp", K.LEFT, 0, 0, nil
function TEST(f)
  t0 = t0 or f
  local d = f - t0
  if phase == "warp" then
    if d == 10 then run({0x39, P[1], P[2], 0xFF, P[3], 0, P[4], 0, 0x02}) end
    if d == 200 then phase = "walk"; local g, n, x, y = where(); w(string.format("in %d/%d at %d,%d", g, n, x, y)) end
    return
  end
  if phase == "walk" then
    if cb2() == BATTLE or (cb2() ~= OVERWORLD and lock() ~= 0) then
      if held then emu:clearKey(held); held = nil end
      phase = "battle"; inb = 0; return
    end
    if lock() ~= 0 then if f % 30 == 0 then tap(K.B) end; return end
    local g, n, x, y = where()
    if x <= P[5] then dir = K.RIGHT elseif x >= P[6] then dir = K.LEFT end
    if held ~= dir then if held then emu:clearKey(held) end; emu:addKey(dir); held = dir end
    if d > 60000 then w("no battle in time"); done(); phase = "end" end
    return
  end
  if phase == "battle" then
    inb = inb + 1
    if inb == 420 then
      battles = battles + 1
      local sp, lv = emu:read16(ENEMY + 0x20), emu:read8(ENEMY + 0x54)
      w(string.format("battle %d: species %d level %d (cb2 %08X)", battles, sp, lv, cb2()))
      shot(string.format("wild_%s_%d", AREA, battles))
    end
    -- run: Down then Right picks Run in the fight menu (Fight Bag / Pokemon Run), then A; B through texts
    if inb > 440 and inb % 60 == 0 then tap(K.DOWN) end
    if inb > 440 and inb % 60 == 15 then tap(K.RIGHT) end
    if inb > 440 and inb % 60 == 30 then tap(K.A) end
    if inb > 440 and inb % 60 == 45 then tap(K.B) end
    if inb > 600 and cb2() == OVERWORLD and lock() == 0 then
      if battles >= ROUNDS then w("finished"); done(); phase = "end" else phase = "walk" end
    end
    if inb > 6000 then w("stuck in battle"); done(); phase = "end" end
  end
end
