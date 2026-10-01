-- DexNav, unseen species hidden. Route 102's first page is Ralts, Lotad, Sentret, Seedot, Rookidee, Hatenna,
-- Yungoos. The test clears the Pokedex's seen bit for Ralts (dex 280) and Sentret (161) and sets it for Lotad
-- (270), then: R opens the DexNav (shot); A on Ralts must not register; DOWN to Lotad ("A: Register"), DOWN to
-- Sentret ("Not seen yet"), A again refused; B out. A wild Ralts battle (Run) must mark it seen through the game's
-- own path; the DexNav then shows it, and A on it registers it and drops back to the field.
-- Screenshots dexnavseen_*.png; the log dexnavseen_log.txt.
NAME = "dexnavseen"
dofile((DIR or "./") .. "../dexnavchain/test_boot.lua")
local SCRIPT, STATE = 0x0203F100, 0x0203A660
local RALTS, RALTS_DEX, SENTRET_DEX, LOTAD_DEX = 392, 280, 161, 270
local function sb1() return emu:read32(0x03005D8C) end
local function seenaddr(n) return sb1() + 0x560 + (n >> 3) end
local function seen(n) return (emu:read8(seenaddr(n)) >> (n & 7)) & 1 end
local function setseen(n, on)
  local a, b = seenaddr(n), emu:read8(seenaddr(n))
  if on then b = b | (1 << (n & 7)) else b = b & ~(1 << (n & 7)) & 0xFF end
  emu:write8(a, b)
end
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1)
  emu:write8(0x03000E38, 0)
end
local function hunt() return string.format("hunt flags %02X species %d", emu:read8(STATE + 9), emu:read16(STATE + 2)) end
local function log(tag)
  w(string.format("%-14s cb2 %08X lock %d | seen Ralts %d Sentret %d Lotad %d | %s", tag, cb2(), lock(),
    seen(RALTS_DEX), seen(SENTRET_DEX), seen(LOTAD_DEX), hunt()))
end

local t0, plan = nil, {}
local function at(d, fn) plan[#plan + 1] = {d, fn} end
local phase, mark, menu, ran = "script", 0, nil, false
at(10, function()
  setseen(RALTS_DEX, false); setseen(SENTRET_DEX, false); setseen(LOTAD_DEX, true)
  emu:write8(STATE + 9, emu:read8(STATE + 9) & 0xFE)       -- no hunt going
  log("set")
  run({0x39, 0, 17, 0xFF, 10, 0, 7, 0, 0x02})               -- Route 102 (10,7)
end)
at(400, function() log("on Route 102"); tap(K.R) end)
at(650, function() log("dexnav open"); shot("dexnavseen_1_page") end)
at(660, function() tap(K.A) end)                             -- Ralts: unseen
at(760, function() log("A on Ralts"); shot("dexnavseen_2_ralts_refused") end)
at(780, function() tap(K.DOWN) end)
at(840, function() shot("dexnavseen_3_lotad") end)
at(860, function() tap(K.DOWN) end)
at(920, function() shot("dexnavseen_4_sentret") end)
at(940, function() tap(K.A) end)                             -- Sentret: unseen
at(1040, function() log("A on Sentret"); shot("dexnavseen_5_sentret_refused") end)
at(1060, function() tap(K.B) end)
at(1260, function() tap(K.B) end)                            -- the start menu, if the DexNav went back to it
at(1400, function() log("closed"); phase = "battle"; mark = 1400
  run({0xB6, RALTS & 0xFF, RALTS >> 8, 5, 0, 0, 0xB7, 0x02}) end)   -- a wild Ralts, Lv 5

function STEP(d)
  if phase == "battle" then
    if d < mark + 20 then return end
    if cb2() == BATTLE and emu:read32(0x03005D60) == 0x08057589 and not menu then menu = d; log("action menu") end
    if not menu and d % 20 == 0 and cb2() == BATTLE then tap(K.B) end
    if menu and not ran then
      if d == menu + 10 then tap(K.RIGHT) end
      if d == menu + 25 then tap(K.DOWN) end
      if d == menu + 40 then tap(K.A); ran = true end
    end
    if ran and d % 30 == 0 and cb2() ~= OVERWORLD then tap(K.B) end
    if ran and cb2() == OVERWORLD and lock() == 0 then phase = "back"; mark = d; log("after battle") end
    if d > mark + 4000 then log("TIMEOUT battle"); shot("dexnavseen_timeout"); done(); phase = "done" end
  elseif phase == "back" then
    if d == mark + 60 then tap(K.R) end
    if d == mark + 310 then log("dexnav again"); shot("dexnavseen_6_ralts_seen") end
    if d == mark + 330 then tap(K.A) end                      -- Ralts, seen now: registers and leaves
    if d == mark + 600 then log("A on Ralts"); shot("dexnavseen_7_registered"); done(); phase = "done" end
  end
end

function TEST(f)
  t0 = t0 or f
  local d = f - t0
  for _, p in ipairs(plan) do if d == p[1] then p[2]() end end
  STEP(d)
end
