-- Egg moves in the Move Relearner (patches/eggrelearn). Boots the save (test_boot.lua), then by MODE:
--   list  : LIST=a,b,... one at a time as the only party Pokemon (givemon Lv LEVEL, default 50); the relearner opened
--           as the party menu's "Moves" does (CB2_InitLearnMove 0x081606A1 as callback2, gSpecialVar_0x8004 = 0).
--           Logged: the Pokemon's moves, then the list read from the menu items (ids at ITEMS + 4, default 0x11C;
--           0x4C on a game without the patch), numMenuChoices +0x110 with Cancel. Shots: <tag>_r<i>_list / _down.
--   learn : SPECIES at LEVEL (four moves known); the last move of the list (above Cancel) is taught over move 1:
--           A, Yes, Yes to deleting, the summary screen's move 1, then the messages. Logged at each step: the
--           callback, the list's length and the cursor (sMoveRelearnerMenuSate 0x0203BC38: listOffset, listRow),
--           and at the end the Pokemon's moves. Shots: <tag>_l<step>.
--   count : LIST as above; GetNumberOfRelearnableMoves(party[0]) through a stub the harness writes into this copy of
--           the ROM at STUB (default 0x08FFCB80, after the patch's code), run by a callnative script; logged
--           against the list's length.
local E = os.getenv
DIR = E("GEN9_DIR")
NAME = (E("TAG") or "egg") .. "_" .. (E("MODE") or "list")
dofile("C:/Users/nonth/Desktop/Works & Productivity/gba-trans/hyper-emerald/hyper-emerald-en-qol/patches/dexnavchain/test_boot.lua")
local MODE = E("MODE") or "list"
local LIST = {}
for n in (E("LIST") or ""):gmatch("%d+") do LIST[#LIST + 1] = tonumber(n) end
local LEVEL = tonumber(E("LEVEL") or "50")
local ITEMS = tonumber(E("ITEMS") or "0x118")
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
local function moves()
  return string.format("%d %d %d %d", emu:read16(PARTY + 0x2C), emu:read16(PARTY + 0x2E), emu:read16(PARTY + 0x30),
    emu:read16(PARTY + 0x32))
end
local function list()
  local st = emu:read32(0x0203BC34)
  local n, mv = emu:read8(st + 0x110), {}
  for k = 0, n - 1 do mv[#mv + 1] = string.format("%d", emu:read32(st + ITEMS + 4 + 8 * k) & 0xFFFF) end
  return n, table.concat(mv, " ")
end
local function cursor()
  return string.format("offset %d row %d", emu:read16(0x0203BC38), emu:read16(0x0203BC3A))
end
local function fresh(sp, lv)
  emu:write8(0x020244E9, 0); for k = 0, 599 do emu:write8(PARTY + k, 0) end; give(sp, lv)
end
local function open_relearner()
  emu:write8(0x03000F2C, 0); emu:write16(0x020375E0, 0); emu:write32(0x030022C4, 0x081606A1)
end
local plan, t0 = {}, nil
local function at(d, fn) plan[#plan + 1] = {d, fn} end
local function key(t, k) at(t, function() tap(k) end) end
local t = 2
if MODE == "list" then
  for i, sp in ipairs(LIST) do
    local ii = i
    at(t, function() fresh(sp, LEVEL) end)
    at(t + 40, function()
      w(string.format("r%d: species %d lv %d moves %s", ii, emu:read16(PARTY + 0x20), emu:read8(PARTY + 0x54), moves()))
      open_relearner()
    end)
    at(t + 300, function()
      shot(string.format("%s_r%02d_list", NAME, ii))
      local n, s = list()
      w(string.format("r%d: list %d: %s", ii, n, s))
    end)
    for k = 0, 69 do key(t + 310 + 12 * k, K.DOWN) end
    at(t + 1160, function() shot(string.format("%s_r%02d_down", NAME, ii)); w(string.format("r%d: down %s", ii, cursor())) end)
    key(t + 1170, K.B); key(t + 1240, K.A); key(t + 1300, K.A); key(t + 1360, K.B)
    at(t + 1600, function() w(string.format("r%d: back cb2 %08X lock %d", ii, cb2(), lock())) end)
    t = t + 1640
  end
elseif MODE == "learn" then
  local sp = tonumber(E("SPECIES"))
  local n0
  local function step(name) shot(string.format("%s_l%s", NAME, name))
    local n, s = list()
    w(string.format("%s: cb2 %08X list %d %s moves %s", name, cb2(), n, cursor(), moves()))
  end
  at(t, function() fresh(sp, LEVEL) end)
  at(t + 40, function() w(string.format("species %d lv %d moves %s", emu:read16(PARTY + 0x20), emu:read8(PARTY + 0x54), moves())); open_relearner() end)
  local tl = t                                            -- (t has moved on by the time this runs)
  at(t + 300, function()
    local n, s = list()
    n0 = n
    w(string.format("list %d: %s", n, s))
    step("00_list")
    for k = 1, n - 2 do key(tl + 300 + 12 * k, K.DOWN) end -- to the last move above Cancel (a gap between taps)
  end)
  at(t + 700, function()
    local n, s = list()
    local st = emu:read32(0x0203BC34)
    local pos = emu:read16(0x0203BC38) + emu:read16(0x0203BC3A)
    w(string.format("chosen: item %d of %d = move %d", pos, n, emu:read32(st + ITEMS + 4 + 8 * pos) & 0xFFFF))
    step("01_cursor")
  end)
  key(t + 710, K.A);  at(t + 900, function() step("02_teach") end)        -- "Teach <move>?"
  key(t + 910, K.A);  at(t + 1100, function() step("03_four") end)        -- can't learn more than four
  key(t + 1110, K.A); at(t + 1300, function() step("04_delete") end)      -- delete an older move? Yes/No
  key(t + 1310, K.A); at(t + 1700, function() step("05_summary") end)     -- the summary's moves page
  key(t + 1710, K.A); at(t + 1900, function() step("06_chosen") end)
  key(t + 1910, K.A); at(t + 2300, function() step("07_back") end)        -- the relearner again
  key(t + 2310, K.A); at(t + 2500, function() step("08_msg1") end)
  key(t + 2510, K.A); at(t + 2700, function() step("09_msg2") end)
  key(t + 2710, K.A); at(t + 2900, function() step("10_msg3") end)
  key(t + 2910, K.A); at(t + 3200, function() step("11_after") end)
  key(t + 3210, K.B); at(t + 3400, function() step("12_after_b") end)
  key(t + 3410, K.A); at(t + 3600, function() step("13_end"); w("final moves " .. moves()) end)
  t = t + 3700
elseif MODE == "count" then
  local STUB = tonumber(E("STUB") or "0x08FFCB80") | 1      -- Thumb
  -- how long the call takes: breakpoints on the stub's bl and the instruction after it, in scanlines (1,232 cycles
  -- each, 228 a frame) from the frame number and VCOUNT
  local t_in
  local function now() return emu:currentFrame() * 228 + emu:read16(0x04000006) end
  emu:setBreakpoint(function() t_in = now() end, (STUB & ~1) + 6)
  emu:setBreakpoint(function() if t_in then w(string.format("time: %d scanlines (%.2f frames)", now() - t_in, (now() - t_in) / 228)) end end, (STUB & ~1) + 10)
  for i, sp in ipairs(LIST) do
    local ii = i
    at(t, function() fresh(sp, LEVEL) end)
    at(t + 40, function()
      w(string.format("c%d: species %d lv %d moves %s", ii, emu:read16(PARTY + 0x20), emu:read8(PARTY + 0x54), moves()))
      emu:write16(0x020375E2, 0xBEEF)
      run({0x23, STUB & 0xFF, (STUB >> 8) & 0xFF, (STUB >> 16) & 0xFF, STUB >> 24, 0x02})   -- callnative STUB; end
    end)
    at(t + 80, function() w(string.format("c%d: count %d", ii, emu:read16(0x020375E2))); open_relearner() end)
    at(t + 340, function() local n, s = list(); w(string.format("c%d: list %d: %s", ii, n, s)) end)
    key(t + 350, K.B); key(t + 420, K.A); key(t + 480, K.A); key(t + 540, K.B)
    t = t + 800
  end
end
at(t, function() done() end)
function TEST(f)
  t0 = t0 or f
  for _, p in ipairs(plan) do if f - t0 == p[1] then p[2]() end end
end
