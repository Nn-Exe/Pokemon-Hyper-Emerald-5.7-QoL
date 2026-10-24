-- The Mint from Cheren himself (mintquirky): Rustboro's Trainer's School (11/4, Cheren at 6,3; his hide flag 0x0051
-- cleared: set in the user's save) - stand beside him (7,3: below him is a desk), face
-- him, A, Yes, Quirk (the grid's last slot), A through the rest (the party menu's A takes the lead); then the EV-IV
-- Display (item 650, registered to UP in the SELECT popup as test_hypertrain.lua does) and the summary. Then Jubilife
-- (37/77, Cheren at 13,2) the same with Hardy. Logged: the lead's Mint byte and stats after each; pictures mc_*.png.
-- env: MQ_DIR (output folder, with the slash), MQ_HERE (this folder, with the slash)
NAME = "mc"
DIR = os.getenv("MQ_DIR") or "./"
local HERE = os.getenv("MQ_HERE") or "./"
dofile(HERE .. "../dexnavchain/test_boot.lua")
local SCRIPT, PARTY = 0x0203F100, 0x020244EC
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1); emu:write8(0x03000E38, 0)
end
local function stats()
  local t = {}
  for k = 0, 5 do t[#t + 1] = emu:read16(PARTY + 0x58 + 2 * k) end
  return table.concat(t, ",")
end
local function where()
  local sb1 = emu:read32(0x03005D8C)
  return string.format("map %d/%d (%d,%d)", emu:read8(sb1 + 4), emu:read8(sb1 + 5), emu:read16(sb1), emu:read16(sb1 + 2))
end
local function register_display()
  local kp, cap, have, free = emu:read32(0x02039DD8 + 32), emu:read8(0x02039DD8 + 36), false, nil
  for i = 0, cap - 1 do
    local id = emu:read16(kp + 4 * i)
    if id == 650 then have = true elseif id == 0 and not free then free = i end
  end
  if not have and free then
    emu:write16(kp + 4 * free, 650)
    emu:write16(kp + 4 * free + 2, 1 ~ (emu:read32(emu:read32(0x03005D90) + 0xAC) & 0xFFFF))
  end
  emu:write16(emu:read32(0x03005D8C) + 0x496, 650)
end

local plan = {}
local function act(gap, fn) plan[#plan + 1] = {fn = fn, gap = gap} end
local function field(key) plan[#plan + 1] = {field = key} end
local function taps(k, n) for _ = 1, n do act(14, function() tap(k) end) end end

local function mint_at(label, g, n, x, y, slot, hide, face)
  act(400, function()                                                -- (his hide flag cleared first), warp below him
    local s = {}
    if hide then s = {0x2A, hide & 0xFF, hide >> 8} end
    for _, v in ipairs({0x39, g, n, 0xFF, x & 0xFF, x >> 8, y & 0xFF, y >> 8, 0x02}) do s[#s + 1] = v end
    run(s)
  end)
  act(10, function() w(string.format("%s: at %s, lead's Mint byte %d", label, where(), emu:read8(PARTY + 0x1F) & 0x7F)) end)
  act(20, function() tap(face or K.UP) end)                          -- face him (he is in the way: a turn only)
  act(30, function() shot("mc_" .. label .. "_0_facing") end)
  act(90, function() tap(K.A) end)                                   -- talk: "Do you need a Mint?"
  act(10, function() shot("mc_" .. label .. "_1_ask") end)
  act(100, function() tap(K.A) end)                                  -- Yes
  act(10, function() shot("mc_" .. label .. "_2_grid") end)
  taps(K.DOWN, slot // 5); taps(K.RIGHT, slot % 5)
  act(20, function() shot("mc_" .. label .. "_3_cursor") end)
  act(20, function() tap(K.A) end)
  field(K.A)
  act(30, function()
    w(string.format("%s: slot %d -> Mint byte %d, stats %s (%s)", label, slot, emu:read8(PARTY + 0x1F) & 0x7F, stats(),
      where()))
  end)
end

act(10, function()
  w(string.format("lead species %d, own nature %d, Mint byte %d, stats %s", emu:read16(PARTY + 0x20),
    emu:read32(PARTY) % 25, emu:read8(PARTY + 0x1F) & 0x7F, stats()))
  register_display()
end)
mint_at("rustboro", 11, 4, 7, 3, 24, 0x0051, K.LEFT)    -- beside him: below him is a desk          -- (his hide flag: set in the user's save)
act(40, function() tap(K.SEL) end)                                   -- the EV-IV Display
act(60, function() tap(K.UP) end)
act(170, function() shot("mc_rustboro_4_evivdisplay") end)
act(10, function() tap(K.R) end)
act(60, function() shot("mc_rustboro_5_evivdisplay_r") end)
act(20, function() tap(K.B) end)
act(60, function() tap(K.B) end)
field(K.B)
mint_at("jubilife", 37, 77, 13, 3, 0)
act(40, function() tap(K.SEL) end)
act(60, function() tap(K.UP) end)
act(170, function() shot("mc_jubilife_4_evivdisplay") end)
act(20, function() tap(K.B) end)
field(K.B)
act(10, function() done() end)

local i, waitUntil, calm = 1, 0, 0
function TEST(f)
  local p = plan[i]
  if not p or f < waitUntil then return end
  if p.field then
    if lock() == 0 and cb2() == OVERWORLD then calm = calm + 1 else calm = 0 end
    if not (lock() == 0 and cb2() == OVERWORLD) and f % 20 == 0 then tap(p.field) end
    if calm >= 60 then calm = 0; i = i + 1 end
    if f > 60000 then w("TIMEOUT at a field wait"); done() end
    return
  end
  local ok, err = pcall(p.fn)
  if not ok then w("ERROR " .. tostring(err)); done() end
  waitUntil = f + p.gap; i = i + 1
end
