-- Buy one item at a Poke Mart list, as the player does: pokemart LIST, Buy, ROW downs, A through the questions.
-- Every change of the main callbacks is logged with its frame, a screenshot every 40 frames after choosing,
-- and breakpoints on the CPU's reset / exception vectors log the registers if the game crashes.
-- LIST=address (0x09B00DD0, the Lilycove clerk's in test 1); ROW=n (19 = the first new item)
local E = os.getenv
DIR = E("GEN9_DIR")
local TAG = E("TAG") or "mb"
NAME = TAG .. "_mart"
dofile("C:/Users/nonth/Desktop/Works & Productivity/gba-trans/hyper-emerald/hyper-emerald-en-qol/patches/dexnavchain/test_boot.lua")
local LIST = tonumber(E("LIST") or "0x09B00DD0")
local ROW = tonumber(E("ROW") or "19")
local NPC = E("NPC")
local SCRIPT = 0x0203F100
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1); emu:write8(0x03000E38, 0)
end
local function regs(what)
  local t = {}
  for _, r in ipairs({"r0", "r1", "r2", "r3", "r4", "r5", "r6", "r7", "lr", "sp", "pc", "cpsr"}) do
    t[#t + 1] = string.format("%s=%08X", r, emu:readRegister(r))
  end
  w(what .. " " .. table.concat(t, " "))
end
local crashed = false
for _, v in ipairs({0x00000000, 0x00000004, 0x0000000C, 0x00000010}) do
  emu:setBreakpoint(function()
    if not crashed then crashed = true; regs(string.format("VECTOR %02X:", v)) end
  end, v)
end
-- the hack's buy guard (0x096FFF00): what it reads
emu:setBreakpoint(function()
  local r4 = emu:readRegister("r4")
  local items = emu:read32(r4 + 0x28)
  local t = {}
  for k = -0x100, 0x20, 4 do t[#t + 1] = string.format("%08X", emu:read32(items + k)) end
  w(string.format("GUARD r4 %08X qty %d item %d row %d (task2 %08X) items %08X [items-0xC0] %08X (%d); items-0x100..+0x20: %s",
    r4, emu:read8(r4 + 2), emu:read16(r4 + 0xA), emu:read8(r4 + 0x42), emu:read32(r4 + 0x20), items,
    emu:read32(items - 0xC0), emu:read32(items - 0xC0), table.concat(t, " ")))
  local list = {}
  for k = 0, 30 do local id = emu:read32(items + 8 * k + 4); list[#list + 1] = tostring(id); if id >= 800 then break end end
  w("   the list menu's ids: " .. table.concat(list, " "))
end, 0x096FFF00)
local t0, last1, last2, phase, mark = nil, nil, nil, "start", 0
function TEST(f)
  t0 = t0 or f
  local d = f - t0
  if phase == "end" then return end
  local c1, c2 = emu:read32(0x030022C0), emu:read32(0x030022C4)
  if c1 ~= last1 or c2 ~= last2 then w(string.format("+%d cb1 %08X cb2 %08X", d, c1, c2)); last1, last2 = c1, c2 end
  if NPC and d == 5 then          -- NPC="group,num,x,y": warp below the clerk, face up, talk (A until the menu)
    local g, n, x, y = NPC:match("(%d+),(%d+),(%d+),(%d+)")
    g, n, x, y = tonumber(g), tonumber(n), tonumber(x), tonumber(y)
    run({0x39, g, n, 0xFF, x & 0xFF, x >> 8, y & 0xFF, y >> 8, 0x02})
  end
  if NPC and d == 300 then shot(NAME .. "_npc0"); tap(E("FACE") == "down" and K.DOWN or K.UP, 3) end
  if NPC and d == 330 then tap(K.A) end
  if NPC and d == 380 then shot(NAME .. "_npc1"); tap(K.A) end
  if not NPC and d == 5 then
    run({0x86, LIST & 0xFF, (LIST >> 8) & 0xFF, (LIST >> 16) & 0xFF, LIST >> 24, 0x02})
    local items = {}
    for k = 0, 40 do local it = emu:read16(LIST + 2 * k); if it == 0 then break end; items[#items + 1] = it end
    w("list " .. table.concat(items, " ") .. " | row " .. ROW .. " = item " .. tostring(items[ROW + 1]))
  end
  local o = NPC and 400 or 0
  if d == 150 + o then shot(NAME .. "_0menu"); tap(K.A) end
  if d == 400 + o then shot(NAME .. "_1buy") end
  for k = 0, ROW - 1 do if d == 420 + o + 14 * k then tap(K.DOWN, 4) end end
  local t = 420 + o + 14 * ROW + 40
  if d == t then shot(NAME .. "_2row"); tap(K.A) end
  if d > t and d < t + 1200 then
    if (d - t) % 40 == 0 then shot(string.format("%s_3_%04d", NAME, d - t)); tap(K.A) end
  end
  if d == t + 1200 or crashed then
    w(crashed and "CRASHED" or "no crash")
    phase = "end"; done()
  end
end
