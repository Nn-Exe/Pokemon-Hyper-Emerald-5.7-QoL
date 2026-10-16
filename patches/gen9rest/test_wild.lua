-- Meet one wild Pokemon where the game puts it: warp to map G/N tile (X,Y), then the game's own encounter -
-- SweetScentWildEncounter (0x080B5578: the land or water table by the tile under the player) or, for KIND=fish,
-- FishingWildEncounter (0x080B5734, the rod ROD in r0) - with the slot the game's random pick returns set to SLOT
-- (land / water: 0x080B4FB6; fishing: 0x080B5030). At the battle's action menu the wild Pokemon is read back.
-- Env: G N X Y KIND SLOT ROD SP LO HI.
local E = os.getenv
DIR = E("GEN9_DIR")
local TAG = E("TAG") or "wt"
NAME = TAG .. "_wild"
dofile("C:/Users/nonth/Desktop/Works & Productivity/gba-trans/hyper-emerald-en-qol/patches/dexnavchain/test_boot.lua")
local G, N, X, Y = tonumber(E("G")), tonumber(E("N")), tonumber(E("X")), tonumber(E("Y"))
local KIND, SLOT, ROD = E("KIND"), tonumber(E("SLOT")), tonumber(E("ROD"))
local SP, LO, HI = tonumber(E("SP")), tonumber(E("LO")), tonumber(E("HI"))
local SCRIPT, ENEMY, ACTION = 0x0203F100, 0x02024744, 0x08057589
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1); emu:write8(0x03000E38, 0)
end
local forced, rodset, armed, rets = 0, false, false, {}
-- the game's slot pickers: whoever calls the one of this kind once the encounter has begun gets SLOT back
local PICK = {land = 0x080B4AC8, water = 0x080B4B84, fish = 0x080B4BD8}
emu:setBreakpoint(function()
  if not armed then return end
  local ret = emu:readRegister("lr") & ~1
  if not rets[ret] then
    rets[ret] = true
    emu:setBreakpoint(function()
      if armed then
        w(string.format("the game picked slot %d (caller %08X) -> forced %d", emu:readRegister("r0"), ret, SLOT))
        emu:writeRegister("r0", SLOT); forced = forced + 1; armed = false
      end
    end, ret)
  end
end, PICK[KIND])
emu:setBreakpoint(function()
  if KIND == "fish" and not rodset then rodset = true; emu:writeRegister("r0", ROD) end
end, 0x080B5734)
if E("TRACE") then
  for _, a in ipairs({0x080B4AC8, 0x080B4B84, 0x080B4BD8, 0x080B4C74, 0x080B4E68, 0x080B4F4C, 0x080B5024, 0x080B5578, 0x080B5734, 0x09F06068}) do
    emu:setBreakpoint(function() w(string.format("  hit %08X lr %08X r0 %08X r1 %08X r2 %08X", a, emu:readRegister("lr"), emu:readRegister("r0"), emu:readRegister("r1"), emu:readRegister("r2"))) end, a)
  end
end
local t0, phase, mark = nil, "warp", 0
local function finish(msg) w(msg); phase = "end"; done() end
function TEST(f)
  t0 = t0 or f
  local d = f - t0
  if phase == "end" then return end
  if d == 5 then run({0x39, G, N, 0xFF, X & 0xFF, X >> 8, Y & 0xFF, Y >> 8, 0x02}) end
  if phase == "warp" and d > 200 and cb2() == OVERWORLD and lock() == 0 then
    phase = "go"; mark = d
    local sb1 = emu:read32(0x03005D8C)
    w(string.format("on map %d/%d at %d,%d", emu:read8(sb1 + 4), emu:read8(sb1 + 5), emu:read16(sb1), emu:read16(sb1 + 2)))
    shot(NAME .. "_field")
    armed = true
    local fn = (KIND == "fish") and 0x080B5735 or 0x080B5579
    run({0x23, fn & 0xFF, (fn >> 8) & 0xFF, (fn >> 16) & 0xFF, fn >> 24, 0x02})
  end
  if phase == "warp" and d > 1500 then finish("NO WARP") end
  if phase == "go" then
    if cb2() == BATTLE then phase = "battle"; mark = d
    elseif d > mark + 600 then shot(NAME .. "_noenc"); finish("NO ENCOUNTER (slot forced " .. forced .. "x)") end
  end
  if phase == "battle" then
    if emu:read32(0x03005D60) == ACTION and d > mark + 200 then
      shot(NAME .. "_battle")
      local sp, lv = emu:read16(ENEMY + 0x20), emu:read8(ENEMY + 0x54)
      local ok = sp == SP and lv >= LO and lv <= HI
      finish(string.format("MET species %d lv %d (want %d lv %d-%d) %s", sp, lv, SP, LO, HI, ok and "PASS" or "FAIL"))
    elseif d % 30 == 0 then tap(K.A) end
    if d > mark + 3000 then shot(NAME .. "_stuck"); finish("battle never reached the menu") end
  end
end
