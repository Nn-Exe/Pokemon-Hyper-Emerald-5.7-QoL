-- A wild Pokemon keeps the item it was given (wilditem). Boots the save, keeps a state of the field, then RUNS times:
-- back to that state, a new seed in gRngValue, and one of the game's scripts (SCRIPT, default the Abandoned Ship's
-- Pikachu, 0x098B96CB: setwildbattle Pikachu Lv 34 holding the Light Ball, 202). A taps through its picture. At
-- SetWildMonHeldItem's entry (0x0806EA68) and end (0x0806EB90) the foe's held item is noted, and again 240 frames
-- into the battle; then the next run. The log (wilditem_<TAG>_log.txt): one line a run, and the count of each item.
--   SCRIPT=0x...  another script;  RUNS=n (40);  TAG=name;  ITEMSET=n  a script of our own instead: setwildbattle
--   SPECIES (25) Lv LEVEL (34) holding ITEMSET (0 = none), dowildbattle
local TAG = os.getenv("TAG") or "x"
NAME = "wilditem_" .. TAG
dofile((HERE or DIR or "./") .. "../dexnavchain/test_boot.lua")
local SCRIPT_AT = tonumber(os.getenv("SCRIPT") or "0x098B96CB")
local RUNS = tonumber(os.getenv("RUNS") or "40")
local ITEMSET = os.getenv("ITEMSET")
local SPECIES, LEVEL = tonumber(os.getenv("SPECIES") or "25"), tonumber(os.getenv("LEVEL") or "34")
local RAM, ENEMY, RNG = 0x0203F100, 0x02024744, 0x03005D80
local function held() return emu:read16(ENEMY + 0x22) end
local function species() return emu:read16(ENEMY + 0x20) end
local function run_script()
  local bytes
  if ITEMSET then
    local it = tonumber(ITEMSET)
    bytes = {0xB6, SPECIES & 0xFF, SPECIES >> 8, LEVEL, it & 0xFF, it >> 8, 0xB7, 0x02}
  else
    bytes = {0x05, SCRIPT_AT & 0xFF, (SCRIPT_AT >> 8) & 0xFF, (SCRIPT_AT >> 16) & 0xFF, SCRIPT_AT >> 24}
  end
  for i, b in ipairs(bytes) do emu:write8(RAM + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, RAM)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1); emu:write8(0x03000E38, 0)
end
local entry, exit_ = nil, nil                         -- every call: "item(caller)" at the entry, the item at the end
emu:setBreakpoint(function()
  entry = (entry and entry .. " " or "") .. string.format("%d(%08X, battle type %08X)", held(), emu:readRegister("lr"),
    emu:read32(0x02022FEC))
end, 0x0806EA68)
emu:setBreakpoint(function() exit_ = (exit_ and exit_ .. " " or "") .. held() end, 0x0806EB90)
local state, run, t0, inbattle, counts = nil, 0, nil, nil, {}
local function seed(n) return (n * 0x9E3779B1 + 0x1234567) & 0xFFFFFFFF end
local function start_run()
  run = run + 1
  emu:loadStateBuffer(state)
  emu:write32(RNG, seed(run))
  entry, exit_, inbattle = nil, nil, nil
  run_script()
end
function TEST(f)
  if not state then
    for k = 0, 9 do emu:clearKey(k) end
    state = emu:saveStateBuffer()
    w(string.format("script %s, %d runs", ITEMSET and ("setwildbattle " .. SPECIES .. " Lv" .. LEVEL .. " item " .. ITEMSET)
      or string.format("%08X", SCRIPT_AT), RUNS))
    t0 = f; start_run(); return
  end
  local d = f - t0
  if cb2() == BATTLE and not inbattle then inbattle = d end
  if not inbattle then
    if d % 40 == 20 then tap(K.A, 4) end              -- the Pikachu's picture waits for a button
    if d > 3000 then w(string.format("run %d: no battle after 3000 frames", run)); t0 = f; start_run() end
    return
  end
  if d - inbattle == 240 then
    local h = held()
    if run == 1 then shot(NAME .. "_battle") end
    w(string.format("run %2d  seed %08X  species %d  item at the roll's entry %s, at its end %s, in battle %d (var 8000 = %d)",
      run, seed(run), species(), tostring(entry), tostring(exit_), h, emu:read16(0x020375D8)))
    counts[h] = (counts[h] or 0) + 1
    if run >= RUNS then
      local keys = {}
      for k in pairs(counts) do keys[#keys + 1] = k end
      table.sort(keys)
      for _, k in ipairs(keys) do w(string.format("item %d: %d of %d", k, counts[k], RUNS)) end
      done()
      return
    end
    t0 = f; start_run()
  end
end
