-- R and the Option menu: R opens the DexNav and B comes straight back; R + A registers; A on the registered
-- species shows "A: Unregister" and unregisters; the Auto Run row flips Off/On, saves as optionsButtonMode 4,
-- and walking without B then runs. Needs the START menu cursor at its default on boot.
NAME = "rb"
dofile((DIR or "./") .. "../dexnavchain/test_boot.lua")
local ST = 0x0203A660
local function sb2() return emu:read32(0x03005D90) end
local function st(tag) w(string.format("%-22s cb2 %08X lock %d flags %02X species %d window %d btnmode %d sb1+31 %d avatar %02X",
  tag, cb2(), lock(), emu:read8(ST+9), emu:read16(ST+2), emu:read8(ST+14), emu:read8(sb2()+0x13), emu:read8(emu:read32(0x03005D8C)+0x31), emu:read8(0x02037590))) end
local seq = {
  {10,"st:start"}, {20,"R"}, {160,"shot:rb_dexnav"}, {161,"st:after R"}, {170,"B"}, {330,"shot:rb_backB"}, {331,"st:after B"},
  {360,"R"}, {500,"DOWN"}, {540,"A"}, {720,"shot:rb_registered"}, {721,"st:after register"},
  {760,"R"}, {900,"DOWN"}, {940,"shot:rb_unreg_hint"}, {950,"A"}, {1130,"shot:rb_unregistered"}, {1131,"st:after unregister"},
  {1160,"START"}, {1220,"UP"}, {1250,"UP"}, {1280,"UP"}, {1320,"shot:rb_menu"}, {1330,"A"}, {1500,"DOWN"}, {1520,"DOWN"}, {1540,"DOWN"}, {1560,"DOWN"},
  {1600,"shot:rb_opt_off"}, {1610,"RIGHT"}, {1650,"shot:rb_opt_on"}, {1651,"st:option on"}, {1660,"B"}, {1850,"B"}, {1950,"st:saved"},
  {2000,"holdR"}, {2020,"st:walking"}, {2040,"shot:rb_run"}, {2060,"release"}, {2100,"st:end"} }
local t0
function TEST(f)
  t0 = t0 or f
  local r = f - t0
  for _, s in ipairs(seq) do if r == s[1] then
    local a = s[2]
    if a:sub(1,5) == "shot:" then shot(a:sub(6))
    elseif a:sub(1,3) == "st:" then st(a:sub(4))
    elseif a == "holdR" then emu:addKey(K.LEFT)
    elseif a == "release" then emu:clearKey(K.LEFT)
    else tap(K[a]) end
  end end
  if r == 2110 then done() end
end
