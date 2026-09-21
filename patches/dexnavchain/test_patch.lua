-- Shaking patch: arming spawns a patch; stepping onto it forces the hunted battle (retrying if a normal encounter
-- gets in first); a win raises chain and SL and brings a new patch; moving the patch off screen resets the chain;
-- a normal encounter elsewhere is not substituted and resets the chain. Runs on Route 215 of the reference save.
NAME = "patch"
dofile((DIR or "./") .. "test_boot.lua")
local ST = 0x0203A660
local function pxy() local id = emu:read8(0x02037595); local o = 0x02037350 + id*0x24; return emu:read16(o+0x10), emu:read16(o+0x12) end
local function st()
  local x, y = pxy()
  return string.format("chain %d SL %d flags %02X patch (%d,%d) fx %d | player (%d,%d) lastfoe %d", emu:read16(ST+4), emu:read16(ST+24),
    emu:read8(ST+9), emu:read8(ST+28), emu:read8(ST+29), emu:read8(ST+30), x, y, emu:read16(0x03005D30))
end
local ARM = {{10,"START"},{80,"UP"},{110,"UP"},{150,"A"},{340,"DOWN"},{390,"A"},{600,"B"}}
lastfoe = 0
local t0, stage, sAt, phase, bstart, battles = nil, "arm", 0, "field", 0, 0
local function go(s, f) stage = s; sAt = f; w("-> " .. s .. ": " .. st()) end
function TEST(f)
  t0 = t0 or f
  local r, c = f - t0, cb2()
  if c == BATTLE then
    if phase ~= "battle" then phase = "battle"; bstart = f; battles = battles + 1
      w(string.format("BATTLE %d starts during '%s': %s", battles, stage, st())) end
    local b = f - bstart
    if b == 420 then lastfoe = emu:read16(0x02024744+0x20); w(string.format("   foe species %d lv %d", lastfoe, emu:read8(0x02024744+0x54))) end
    if b > 200 then emu:write16(0x02024084 + 0x28, 1) end
    if b > 450 then
      if stage == "normal" then local q = b % 90; if q == 0 then tap(K.DOWN) elseif q == 20 then tap(K.RIGHT) elseif q == 40 then tap(K.A) end
      elseif f % 12 == 0 then tap(K.A) end
    end
    return
  end
  if phase == "battle" and c == OVERWORLD then phase = "field"; bstart = f; w("   back on field, outcome " .. emu:read8(0x0202433A)) end
  if phase == "field" and bstart > 0 then
    if lock() ~= 0 then if f % 30 == 0 then tap(K.B) end return end
    if f - bstart < 240 then return end
    bstart = 0
    w("   240 frames later: " .. st()); shot("patch_after" .. battles)
    if stage == "step" and lastfoe ~= 108 then w("   a normal encounter got in first: placing the patch again"); go("step", f)
    elseif stage == "step" then emu:write16(ST+4, 3); go("away", f)
    elseif stage == "normal" then done() end
    return
  end
  if stage == "arm" then
    for _, s in ipairs(ARM) do if r == s[1] then tap(K[s[2]]) end end
    if r == 700 then w("armed: " .. st()) end
    if r == 710 or r == 722 or r == 734 or r == 746 then shot("patch_shake" .. r) end
    if r == 760 then tap(K.RIGHT, 36); end
    if r == 900 then go("step", f) end
    return
  end
  if stage == "step" then
    local q = f - sAt
    if q == 1 then local x, y = pxy(); emu:write8(ST+28, x); emu:write8(ST+29, y - 1); emu:write8(ST+31, 0); w("   patch moved to just above the player") end
    if q == 40 then tap(K.UP, 24) end
    if q == 600 then w("   no battle after stepping on the patch: " .. st()); done() end
    return
  end
  if stage == "away" then
    local q = f - sAt
    if q == 1 then local x, y = pxy(); emu:write8(ST+28, x + 9); emu:write8(ST+29, y); w("   chain set to 3, patch moved 9 tiles away (off screen)") end
    if q == 30 then w("   after walk-away: " .. st()); emu:write16(ST+4, 3); go("normal", f) end
    return
  end
  if stage == "normal" then
    local q = f - sAt
    if q % 20 == 0 then local x, y = pxy(); emu:write8(ST+28, x + 6); emu:write8(ST+29, y) end  -- keep the patch aside
    if lock() ~= 0 then if f % 30 == 0 then tap(K.B) end return end
    local p = q % 64; if p == 0 then tap(K.UP, 30) elseif p == 32 then tap(K.DOWN, 30) end
    if q > 40000 then w("no normal encounter: " .. st()); done() end
  end
end
