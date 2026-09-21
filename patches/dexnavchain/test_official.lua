-- ORAS chain rules: idle + menus must not break; SL goes past 255 and into flash; a battle we did not seed
-- (simulated through gBattleResults) breaks the chain but keeps SL; re-arming reads SL back from flash;
-- leaving the map (simulated) breaks the chain. Needs the START menu cursor at its default on boot.
NAME = "official"
dofile((DIR or "./") .. "test_boot.lua")
local ST = 0x0203A660
local function st() return string.format("species %d chain %d SL %d flags %02X win %d lastfoe %d", emu:read16(ST+2), emu:read16(ST+4), emu:read16(ST+24), emu:read8(ST+9), emu:read8(ST+14), emu:read16(0x03005D30)) end
local ARM = {{10,"START"},{80,"UP"},{110,"UP"},{150,"A"},{340,"DOWN"},{390,"A"},{600,"B"}}
local t0, stage, sAt, phase, bstart = nil, 1, 0, "field", 0
local ARM2 = {{10,"START"},{150,"A"},{340,"DOWN"},{390,"A"},{600,"B"}}
local function run(seq, r) for _, s in ipairs(seq) do if r == s[1] then tap(K[s[2]]) end end end
function TEST(f)
  t0 = t0 or f
  local r = f - t0
  local c = cb2()
  if stage == 1 then run(ARM, r); if r == 700 then w("armed: " .. st()); emu:write16(ST+24, 300); emu:write16(ST+4, 5); stage = 2; sAt = f end return end
  if stage == 2 then -- idle + menus: must not break
    local q = f - sAt
    if q == 100 or q == 400 then tap(K.START) elseif q == 200 or q == 500 then tap(K.B) end
    if q == 900 then w("after idle+menus: " .. st()); shot("official_sl300"); stage = 3; sAt = f; tap(K.RIGHT, 36) end
    return
  end
  if stage == 3 then -- one win
    if c == BATTLE then
      if phase ~= "battle" then phase = "battle"; bstart = f end
      if f - bstart > 200 then emu:write16(0x02024084 + 0x28, 1) end
      if f - bstart > 450 and f % 12 == 0 then tap(K.A) end
      return
    end
    if phase == "battle" and c == OVERWORLD then phase = "back"; bstart = f end
    if phase == "back" then
      if lock() ~= 0 and f % 30 == 0 then tap(K.B) end
      if f - bstart == 300 then w("after win: " .. st()); stage = 4; sAt = f end
      return
    end
    if c ~= OVERWORLD or lock() ~= 0 then if f % 30 == 0 then tap(K.B) end return end
    local p = (f - sAt) % 64; if p == 0 then tap(K.UP, 30) elseif p == 32 then tap(K.DOWN, 30) end
    return
  end
  if stage == 4 then -- foreign battle
    local q = f - sAt
    if q == 10 then emu:write16(0x03005D30, 25); w("simulated a trainer battle (lastfoe 25)") end
    if q == 60 then w("after foreign battle: " .. st()); emu:write16(ST+24, 0); w("zeroed SL in RAM, so the re-arm must read it from flash"); stage = 5; sAt = f end
    return
  end
  if stage == 5 then -- re-arm: SL must come back from flash
    run(ARM2, f - sAt)
    if f - sAt == 690 then shot("official_rearm") end
    if f - sAt == 700 then w("re-armed: " .. st()); stage = 6; sAt = f end
    return
  end
  if stage == 6 then -- leave the map
    local q = f - sAt
    if q == 10 then emu:write8(ST+11, emu:read8(ST+11) ~ 1); w("simulated leaving the map") end
    if q == 60 then w("after leaving: " .. st()); done() end
  end
end
