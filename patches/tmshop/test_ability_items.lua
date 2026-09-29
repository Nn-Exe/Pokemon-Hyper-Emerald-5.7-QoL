-- The hack's Ability Patch / Pill really do something: give one, set gSpecialVar_ItemId (0x0203CE7C), run the
-- items' field script 0x08F7F0D0 (choose a Pokemon, callasm 0x08C60D29, message), pick the first Pokemon, and log
-- the item count, VAR_RESULT and which bytes of the Pokemon changed. After a refusal the script
-- returns to the chooser, which ignored B and Cancel when the script is run this way (not from the Bag). ITEM (env) = 741 Patch (default) or 646 Pill.
-- Screenshots ab_<item>_*.png.
local ITEM = tonumber(os.getenv("ITEM") or "741")
NAME = "ability_" .. ITEM
dofile((DIR or "./") .. "../dexnavchain/test_boot.lua")
local SCRIPT, PARTY = 0x0203F100, 0x020244EC
local t0, plan = nil, {}
local function at(d, fn) plan[#plan + 1] = {d, fn} end
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1)
  emu:write8(0x03000E38, 0)
end
local function count(item)
  local n = 0
  for pocket = 0, 4 do
    local base, cap = emu:read32(0x02039DD8 + pocket * 8), emu:read8(0x02039DD8 + pocket * 8 + 4)
    if base >= 0x02000000 and base < 0x03000000 and cap > 0 and cap < 250 then
      for i = 0, cap - 1 do if emu:read16(base + i * 4) == item then n = n + emu:read16(base + i * 4 + 2) end end
    end
  end
  return n
end
local before = {}
local function snap() for i = 0, 99 do before[i] = emu:read8(PARTY + i) end end
local function diff()
  local out = {}
  for i = 0, 99 do
    local v = emu:read8(PARTY + i)
    if v ~= before[i] then out[#out + 1] = string.format("+%02X %02X->%02X", i, before[i], v) end
  end
  return #out > 0 and table.concat(out, " ") or "nothing"
end
at(10, function() run({0x44, ITEM & 0xFF, ITEM >> 8, 1, 0, 0x02}) end)
at(60, function() snap(); emu:write16(0x0203CE7C, ITEM)
  w(string.format("item %d count %d, species %d", ITEM, count(ITEM), emu:read16(PARTY + 0x20)))
  run({0x05, 0xD0, 0xF0, 0xF7, 0x08}) end)
at(400, function() shot(NAME .. "_choose"); tap(K.A) end)
at(900, function() shot(NAME .. "_message")
  w(string.format("VAR_RESULT %d, count %d, changed: %s", emu:read16(0x020375F0), count(ITEM), diff())) end)
at(920, function() tap(K.A) end)
at(1100, function() w(string.format("after: cb2 %08X lock %d", cb2(), lock())); done() end)
function TEST(f)
  t0 = t0 or f
  for _, p in ipairs(plan) do if f - t0 == p[1] then p[2]() end end
end
