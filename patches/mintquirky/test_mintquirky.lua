-- Cheren's Mint offer (0x0984A658) run from a script for each slot of SLOTS (default: Hardy, Lonely, Adamant, Modest,
-- Careful, Quirky): yes, the grid (a picture), the cursor to the slot, A, A through the rest (the party menu's A takes
-- the lead). Then the lead's Mint byte (+0x1F) and its stats are logged, and START -> POKEMON -> lead -> SUMMARY is
-- pictured to see the nature it shows. Log mq_log.txt, pictures mq_*.png.
-- env: MQ_DIR (output folder, with the slash), MQ_HERE (this folder, with the slash), SLOTS=0,1,3 ...
NAME = "mq"
DIR = os.getenv("MQ_DIR") or "./"
local HERE = os.getenv("MQ_HERE") or "./"
dofile(HERE .. "../dexnavchain/test_boot.lua")
local SCRIPT, PARTY = 0x0203F100, 0x020244EC
local NAMES = {[0] = "Hardy", "Lonely", "Brave", "Adamant", "Naughty", "Bold", "Docile", "Relaxed", "Impish", "Lax",
  "Timid", "Hasty", "Serious", "Jolly", "Naive", "Modest", "Mild", "Quiet", "Bashful", "Rash", "Calm", "Gentle", "Sassy",
  "Careful", "Quirky"}
local SLOTS = {}
for n in (os.getenv("SLOTS") or "0,1,3,15,23,24"):gmatch("%d+") do SLOTS[#SLOTS + 1] = tonumber(n) end
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
  for k = 0, 5 do t[#t + 1] = emu:read16(PARTY + 0x58 + 2 * k) end     -- max HP, Atk, Def, Spe, SpA, SpD
  return table.concat(t, ",")
end

-- the plan: a list of actions, each {fn, frames to wait after it} or {"field"} (wait until the field is ours)
local plan = {}
local function act(gap, fn) plan[#plan + 1] = {fn = fn, gap = gap} end
local function field(key) plan[#plan + 1] = {field = key} end
local function taps(k, n) for _ = 1, n do act(14, function() tap(k) end) end end
act(10, function() w(string.format("lead species %d level %d, own nature %s, Mint byte %d, stats %s", emu:read16(PARTY + 0x20),
  emu:read8(PARTY + 0x54), NAMES[emu:read32(PARTY) % 25], emu:read8(PARTY + 0x1F) & 0x7F, stats())) end)
for _, s in ipairs(SLOTS) do
  act(70, function() run({0x6A, 0x05, 0x58, 0xA6, 0x84, 0x09}) end)          -- lock; goto the offer
  act(100, function() tap(K.A) end)                                           -- Yes
  act(10, function() shot(string.format("mq_%02d_grid", s)) end)
  taps(K.DOWN, s // 5); taps(K.RIGHT, s % 5)
  act(20, function() shot(string.format("mq_%02d_cursor", s)) end)
  act(20, function() tap(K.A) end)
  field(K.A)                                                                  -- A through the rest
  act(30, function()
    local b = emu:read8(PARTY + 0x1F) & 0x7F
    w(string.format("slot %2d (%s): Mint byte %d, stats %s", s, NAMES[s], b, stats()))
  end)
  act(60, function() tap(K.START) end)                                        -- the summary's nature
  act(30, function() tap(K.DOWN) end)
  act(110, function() tap(K.A) end)
  act(120, function() tap(K.A) end)
  act(120, function() tap(K.A) end)
  act(10, function() shot(string.format("mq_%02d_summary", s)) end)
  act(40, function() tap(K.B) end)
  act(80, function() tap(K.B) end)
  act(60, function() tap(K.B) end)
  field(K.B)
end
act(10, function() done() end)

local i, waitUntil, calm = 1, 0, 0
function TEST(f)
  local p = plan[i]
  if not p or f < waitUntil then return end
  if p.field then
    if lock() == 0 and cb2() == OVERWORLD then calm = calm + 1 else calm = 0 end
    if not (lock() == 0 and cb2() == OVERWORLD) and f % 20 == 0 then tap(p.field) end
    if calm >= 60 then calm = 0; i = i + 1 end
    return
  end
  local ok, err = pcall(p.fn)
  if not ok then w("ERROR " .. tostring(err)); done() end
  waitUntil = f + p.gap; i = i + 1
end
