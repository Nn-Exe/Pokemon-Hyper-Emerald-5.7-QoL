-- The normal DexNav (seen-first rules) on Route 102 with a new Pokemon. SEE=species: meet it first in a scripted
-- wild battle and run (the Pokedex marks it seen), else not. Then R, the ring to Land row 2 column COL, a shot (a
-- shadow and "?????" when unseen), A; the registration is logged; on the field the player walks the grass until a
-- battle, whose species is logged (a registered search brings that species). Seen flags of 954 (Nymble, the old
-- arrays) and 961 (Fidough, the 960+ area) logged at each step.
local E = os.getenv
DIR = E("GEN9_DIR")
NAME = (E("TAG") or "dnn") .. "_dexnav"
dofile("C:/Users/nonth/Desktop/Works & Productivity/gba-trans/hyper-emerald-en-qol/patches/dexnavchain/test_boot.lua")
local SEE, COL = tonumber(E("SEE") or "0"), tonumber(E("COL") or "1")
local SCRIPT, STATE, ENEMY, EXT, ACTION = 0x0203F100, 0x0203A660, 0x02024744, 0x0203DA00, 0x08057589
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1); emu:write8(0x03000E38, 0)
end
local function flags(label)
  local sb1 = emu:read32(0x03005D8C)
  local n954 = (emu:read8(sb1 + 0x560 + (954 >> 3)) >> (954 & 7)) & 1
  local m = emu:read32(EXT)
  local n961 = (m == 0x39584544) and ((emu:read8(EXT + 4 + (1 >> 3)) >> 1) & 1) or 0
  w(string.format("%s: Nymble (954) seen %d | Fidough (961) seen %d (960+ marker %08X)", label, n954, n961, m))
end
local t0, phase, mark, n, step = nil, "warp", 0, 0, 0
function TEST(f)
  t0 = t0 or f
  local d = f - t0
  if phase == "end" then return end
  if d == 5 then run({0x39, 0, 17, 0xFF, 9, 0, 6, 0, 0x02}) end
  if phase == "warp" and d > 300 and cb2() == OVERWORLD and lock() == 0 then
    flags("at the start")
    if SEE > 0 then phase = "see"; mark = d; run({0xB6, SEE & 0xFF, SEE >> 8, 4, 0, 0, 0xB7, 0x02})
    else phase = "dexnav"; mark = d end
  elseif phase == "see" then
    if cb2() == BATTLE and emu:read32(0x03005D60) == ACTION and step == 0 then step = 1; mark = d
    elseif cb2() == BATTLE and step == 0 and d % 30 == 0 then tap(K.A) end
    if step == 1 then
      if d == mark + 60 then tap(K.RIGHT) elseif d == mark + 90 then tap(K.DOWN) elseif d == mark + 120 then tap(K.A) end  -- Run
      if d > mark + 150 and d % 30 == 0 then tap(K.B) end
      if d > mark + 200 and cb2() == OVERWORLD and lock() == 0 then flags("after meeting it"); phase = "dexnav"; mark = d end
    end
    if d > mark + 4000 and step == 0 then w("no battle to see it"); phase = "end"; done() end
  elseif phase == "dexnav" then
    local k = d - mark
    if k == 60 then tap(K.R) end
    if k == 260 then tap(K.DOWN) end
    if k == 300 then tap(K.DOWN) end
    for c = 1, COL do if k == 300 + 40 * c then tap(K.RIGHT) end end
    if k == 340 + 40 * COL then shot(NAME .. "_cell") end
    if k == 360 + 40 * COL then tap(K.A) end
    if k == 420 + 40 * COL then shot(NAME .. "_afterA") end
    if k == 700 + 40 * COL then
      w(string.format("registered: species %d flags %02X | cb2 %08X", emu:read16(STATE + 2), emu:read8(STATE + 9), cb2()))
      if cb2() ~= OVERWORLD then tap(K.B) end
    end
    if k > 760 + 40 * COL and cb2() == OVERWORLD and lock() == 0 then
      if emu:read16(STATE + 2) == 0 then w("nothing registered (as for an unseen one)"); phase = "end"; done()
      else shot(NAME .. "_bar"); phase = "walk"; n = 0 end
    end
    if k > 3000 then w("stuck in the DexNav"); phase = "end"; done() end
  elseif phase == "walk" then
    n = n + 1
    if cb2() == BATTLE then
      if n > 20 and emu:read16(ENEMY + 0x20) ~= 0 then
        shot(NAME .. "_battle")
        w(string.format("wild battle: species %d level %d (registered %d)", emu:read16(ENEMY + 0x20), emu:read8(ENEMY + 0x54), emu:read16(STATE + 2)))
        phase = "end"; done()
      end
    elseif n == 2 then run({0x16, 0x21, 0x40, 200, 0, 0x02})        -- setvar VAR_REPEL_STEP_COUNT 200: only the patch's encounter
    elseif n == 12 then emu:write8(0x03000F2C, 0)                    -- run() locked the field; the script did not release it
    elseif lock() ~= 0 then if n % 30 == 0 then tap(K.B) end
    elseif n % 24 == 0 then                                        -- one step toward the shaking patch (state +28 / +29)
      local id = emu:read8(0x02037590 + 5)
      local ox = 0x02037350 + 0x24 * id
      local x, y, px, py = emu:read16(ox + 0x10), emu:read16(ox + 0x12), emu:read8(STATE + 28), emu:read8(STATE + 29)
      if n % 240 == 0 then w(string.format("  player %d,%d patch %d,%d", x, y, px, py)) end
      if px ~= 0 then
        if x < px then tap(K.RIGHT, 14) elseif x > px then tap(K.LEFT, 14) elseif y < py then tap(K.DOWN, 14) elseif y > py then tap(K.UP, 14) end
      end
    end
    if n > 30000 then w("no battle"); phase = "end"; done() end
  end
end
