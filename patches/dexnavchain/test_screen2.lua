-- DexNav screen: "A: Register" hint and the red row border; cursor moves redraw only the border (the icons keep
-- animating instead of being recreated); A returns straight to the field with the bar up; moving the patch off
-- screen ends the search. Needs the START menu cursor at its default on boot.
NAME = "ui2"
dofile((DIR or "./") .. "test_boot.lua")
local ST = 0x0203A660
local t0
local function pxy() local id = emu:read8(0x02037595); local o = 0x02037350 + id*0x24; return emu:read16(o+0x10), emu:read16(o+0x12) end
local function icons() local t = {}; for i = 0, 63 do local b = 0x02020630 + i*0x44; if emu:read8(b+0x3E) & 1 == 1 then t[#t+1] = string.format("%d:%d", i, emu:read8(b+0x2C) & 0x3F) end end return table.concat(t, " ") end
local seq = {{10,"START"},{80,"UP"},{110,"UP"},{150,"A"},{330,"shot:ui2_open"},{331,"icons"},{340,"DOWN"},{343,"shot:ui2_d1a"},{380,"DOWN"},{420,"DOWN"},{460,"shot:ui2_d3"},{461,"icons"},{470,"UP"},{510,"shot:ui2_u1"},{520,"A"},{800,"shot:ui2_field"},{801,"state"},{820,"RIGHT"},{880,"state"},{900,"away"},{940,"state"},{950,"shot:ui2_away"}}
function TEST(f)
  t0 = t0 or f
  local r = f - t0
  for _, s in ipairs(seq) do if r == s[1] then
    local a = s[2]
    if a:sub(1,5) == "shot:" then shot(a:sub(6))
    elseif a == "icons" then w("sprites in use (slot:anim state): " .. icons())
    elseif a == "state" then local x, y = pxy(); w(string.format("cb2 %08X lock %d flags %02X window %d player (%d,%d)", cb2(), lock(), emu:read8(ST+9), emu:read8(ST+14), x, y))
    elseif a == "away" then local x, y = pxy(); emu:write8(ST+28, x + 9); emu:write8(ST+29, y); w("patch moved off screen")
    else tap(K[a]) end
  end end
  if r == 960 then done() end
end
