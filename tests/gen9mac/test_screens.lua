-- The screens an owned Pokemon is seen on, for looking at by eye (visual glitches): screenshots only, plus a log of
-- what was put where.
--   MODE=party LIST=a,b,c,d,e,f [SHINY=1]: the party is exactly these (givemon Lv 50; SHINY=1 rewrites each one's
--     personality to a shiny one for the player's id), START -> POKEMON: the party screen, then for each slot A ->
--     Summary -> its three pages (RIGHT), B, DOWN.          shots: party.png, s<slot>_p<page>.png
--   MODE=pc LIST=up to 30 species BOX=n: the box's 30 slots are these (BoxPokemon copies of givemon'd ones), the PC
--     opened from the SELECT ring (as patches/gen9rest/test_gen9rest.lua's pc mode does on the user's save), Move
--     Pokemon, and the cursor over each slot in turn (the panel shows that Pokemon's picture and name).
--                                                           shots: box.png, slot<nn>.png
local E = os.getenv
DIR = E("GEN9_DIR")
local MODE = E("MODE") or "party"
NAME = (E("TAG") or "sc") .. "_" .. MODE
dofile("C:/Users/nonth/Desktop/Works & Productivity/gba-trans/hyper-emerald/hyper-emerald-en-qol/patches/dexnavchain/test_boot.lua")
local LIST = {}
for n in (E("LIST") or ""):gmatch("%d+") do LIST[#LIST + 1] = tonumber(n) end
local SCRIPT, PARTY = 0x0203F100, 0x020244EC
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1); emu:write8(0x03000E38, 0)
end
local function give(sp, lv) run({0x79, sp & 0xFF, sp >> 8, lv, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0x02}) end
local function shiny(m)                          -- the same low half, a high half that makes it shiny for this OT
  local otid = emu:read32(m + 4)
  local lo = emu:read32(m) & 0xFFFF
  emu:write32(m, ((((otid >> 16) ~ (otid & 0xFFFF)) ~ lo) & 0xFFFF) << 16 | lo)
end
local plan, t0 = {}, nil
local function at(d, fn) plan[#plan + 1] = {d, fn} end
local function key(t, k) at(t, function() tap(k) end) end
local function snap(t, n) at(t, function() shot(NAME .. "_" .. n) end) end
local T = 0
if MODE == "party" then
  at(2, function() emu:write8(0x020244E9, 0); for i = 0, 599 do emu:write8(PARTY + i, 0) end end)
  for i, sp in ipairs(LIST) do at(2 + 25 * i, function() give(sp, 50) end) end
  T = 2 + 25 * (#LIST + 1)
  at(T, function()
    if E("SHINY") == "1" then for i = 0, #LIST - 1 do shiny(PARTY + 100 * i) end end
    local t = {}
    for i = 0, 5 do t[#t + 1] = emu:read16(PARTY + 100 * i + 0x20) end
    w("party: " .. table.concat(t, " ") .. (E("SHINY") == "1" and " (shiny)" or ""))
    emu:write8(0x03000F2C, 0)
  end)
  key(T + 20, K.START); key(T + 80, K.DOWN); key(T + 110, K.A)
  snap(T + 360, "party")
  local t = T + 370
  for s = 1, #LIST do                            -- (generous waits: the party screen fades back in after a summary)
    key(t, K.A); key(t + 80, K.A)                -- the action menu, Summary
    snap(t + 260, string.format("s%d_p1", s)); key(t + 270, K.RIGHT)
    snap(t + 360, string.format("s%d_p2", s)); key(t + 370, K.RIGHT)
    snap(t + 460, string.format("s%d_p3", s)); key(t + 470, K.B)
    key(t + 620, K.B)                            -- the summary closes onto "Do what with this PKMN?": close it too
    snap(t + 700, string.format("s%d_back", s))
    if s < #LIST then key(t + 720, K.DOWN) end
    t = t + 800
  end
  key(t, K.B); key(t + 60, K.B)
  at(t + 300, function() w(string.format("back: cb2 %08X lock %d", cb2(), lock())); done() end)
else
  local BOX = tonumber(E("BOX") or "12") - 1
  local function st() return emu:read32(0x03005D94) end
  at(2, function() emu:write8(0x020244E9, 5); for i = 500, 599 do emu:write8(PARTY + i, 0) end end)
  for i, sp in ipairs(LIST) do
    at(2 + 30 * i, function() give(sp, 50) end)
    at(2 + 30 * i + 20, function()
      local dst = st() + 4 + (BOX * 30 + i - 1) * 80
      for k = 0, 79 do emu:write8(dst + k, emu:read8(PARTY + 500 + k)) end
      emu:write8(0x020244E9, 5); for k = 500, 599 do emu:write8(PARTY + k, 0) end
    end)
  end
  T = 2 + 30 * (#LIST + 1)
  at(T, function()
    for i = #LIST, 29 do local dst = st() + 4 + (BOX * 30 + i) * 80; for k = 0, 79 do emu:write8(dst + k, 0) end end
    local t = {}
    for i = 0, 29 do t[#t + 1] = emu:read16(st() + 4 + (BOX * 30 + i) * 80 + 0x20) end
    w("box " .. (BOX + 1) .. ": " .. table.concat(t, " "))
    emu:write8(st(), BOX); emu:write8(0x03000F2C, 0)
  end)
  key(T + 20, K.SEL); key(T + 60, K.A); key(T + 200, K.A); key(T + 330, K.A); key(T + 460, K.A)
  key(T + 610, K.DOWN); key(T + 630, K.DOWN); key(T + 660, K.A)   -- Move Pokemon
  snap(T + 1000, "box")                         -- the cursor opens on the box's first slot
  local t = T + 1080
  for i = 0, 29 do                              -- snake through the 6 x 5 grid; shots named by the box slot
    local row, col = i // 6, i % 6
    local slot = row * 6 + ((row % 2 == 0) and col or 5 - col)
    if slot < #LIST then snap(t, string.format("slot%02d", slot + 1)) end
    if col == 5 then key(t + 10, K.DOWN) else key(t + 10, (row % 2 == 0) and K.RIGHT or K.LEFT) end
    t = t + 70
  end
  at(t + 20, function() done() end)
end
function TEST(f)
  t0 = t0 or f
  for _, p in ipairs(plan) do if f - t0 == p[1] then p[2]() end end
end
