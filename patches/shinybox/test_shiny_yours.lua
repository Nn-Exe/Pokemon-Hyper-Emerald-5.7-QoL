-- Gold healthbox on both sides: in a wild battle, make my battler shiny, then the opponent too, then put mine
-- back, logging the palette slot of every healthbox sprite at each step.
NAME = "shinyboth"
dofile((DIR or "./") .. "../dexnavchain/test_boot.lua")
local MONS = 0x02024084
local phase, bstart, saved0 = "walk", 0, nil
local function boxes()
  local t = {}
  for i = 0, 63 do
    local s = 0x02020630 + i * 0x44
    if (emu:read16(s + 0x3E) & 1) == 1 then
      local cb = emu:read32(s + 0x1C)
      if cb == 0x08007429 or cb == 0x08072925 then
        local pal = (emu:read16(s + 4) >> 12) & 15
        local who = ""
        if cb == 0x08007429 then who = " battler " .. emu:read16(s + 0x3A) end
        t[#t + 1] = string.format("%s pal %d%s", cb == 0x08007429 and "body" or "half", pal, who)
      end
    end
  end
  return table.concat(t, " | ")
end
function TEST(f)
  if cb2() ~= BATTLE then
    if phase == "walk" then
      local p = f % 96
      if p == 0 then tap(K.RIGHT, 40) elseif p == 48 then tap(K.LEFT, 40) end
      if lock() ~= 0 and f % 26 == 0 then tap(K.A) end
    end
    return
  end
  if phase == "over" then return end
  if phase ~= "battle" then phase = "battle"; bstart = 0; w("battle starts") end
  if bstart == 0 then                                  -- wait for FIGHT/BAG: both boxes are up by then
    if emu:read32(0x03005D60) ~= 0x08057589 then if f % 30 == 0 then tap(K.A) end return end
    bstart = f - 390; w("action menu is up")
  end
  local b = f - bstart
  if b == 400 then w("stock:         " .. boxes()); shot("sb_stock") end
  if b == 410 then saved0 = emu:read32(MONS + 0x54); emu:write32(MONS + 0x54, emu:read32(MONS + 0x48)); w("-> my Pokemon made shiny") end
  if b == 440 then w("mine shiny:    " .. boxes()); shot("sb_mine") end
  if b == 450 then emu:write32(MONS + 0x58 + 0x54, emu:read32(MONS + 0x58 + 0x48)); w("-> opponent made shiny too") end
  if b == 480 then w("both shiny:    " .. boxes()); shot("sb_both") end
  if b == 490 then emu:write32(MONS + 0x54, saved0); w("-> my Pokemon back to normal") end
  if b == 520 then w("mine restored: " .. boxes()); shot("sb_restored"); done(); phase = "over" end
end
