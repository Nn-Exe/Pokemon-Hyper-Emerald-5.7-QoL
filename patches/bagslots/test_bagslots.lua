-- Items pocket 200 slots. Run next to game.gba/game.sav copies (an old-layout save) with DIR and HERE set.
-- 1) After boot: the pocket table, MARKER, and the migration (new[0..99] = old[0..99], new[100..199] empty).
-- 2) 200 distinct items written in; the field Bag scrolled to the last row and Cancel (bs_top/bs_mid/bs_end.png),
--    the list buffers' heap blocks, the 200th name; three sorts (START) keep the same 200 items.
-- 3) additem: into the last free slot (1), a 201st distinct item (0, pocket unchanged), stacking (1).
-- 4) A wild battle: the Bag from the battle menu scrolled to Cancel (bs_battle.png), then the battle won.
-- 5) Saved from the Start menu; the slots go to bs_saved_sig.txt for test_bagslots_reload.lua (a fresh boot of
--    that save: the same 200 slots, MARKER set, no second migration). (emu:reset() stalls the script.)
-- 6) The unused margin 0x0203D908..MARKER is filled with a pattern first and checked last (and after reload).
NAME = "bagslots"
DIR = DIR or "./"
HERE = HERE or DIR
dofile(HERE .. "../dexnavchain/test_boot.lua")
local POCKETS, OLD, NEW, MARKER, MAGIC = 0x02039DD8, 0x0203D030, 0x0203DAE0, 0x0203DADC, 0x32474142
local MARGIN_LO, PATTERN = 0x0203D908, 0x5AA5C33C
local SCRIPT, BAGPOS, RESULT = 0x0203F100, 0x0203CE58, 0x020375F0
local ITEMS_TABLE = 0x08FC2C7C
local FILL = {13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,
  46,47,48,49,50,51,52,53,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,73,74,75,76,77,78,79,80,81,83,84,85,86,87,
  88,89,90,91,92,93,94,95,96,97,98,99,100,101,102,103,104,105,106,107,108,109,110,111,112,113,121,122,123,124,125,
  126,127,128,129,130,131,132,179,180,181,183,184,185,186,187,188,189,190,191,192,193,194,195,196,197,198,199,200,
  201,202,203,204,205,206,207,208,209,210,211,212,213,214,215,216,217,218,219,220,221,222,223,224,225,248,249,250,
  251,252,253,254,255,256,257,258,286,287,304,305,306,307,308,309,310,311,312,313,314,315,316,317,318,319,320,321,
  322,323,324,325,326,327,328,329,330,331,332,333,334,335}
local EXTRA1, EXTRA2 = 336, 337                   -- Items-pocket items not in FILL
local fails = 0
local function ok(cond, msg) w((cond and "  ok   " or "  FAIL ") .. msg); if not cond then fails = fails + 1 end end

-- a small scheduler: after(d, fn) runs fn d frames from now; waitfor polls a condition
local q, now = {}, 0
local function after(d, fn) q[#q + 1] = {now + d, fn} end
local function waitfor(cond, fn, limit, tag, nudge)
  local start = now
  local function poll()
    if cond() then fn() elseif now - start > limit then w("  FAIL timed out waiting for " .. tag); fails = fails + 1; fn()
    else if nudge and (now - start) % 30 == 29 then nudge() end; after(1, poll) end
  end
  after(1, poll)
end
function TEST(f)
  now = f
  local i = 1
  while i <= #q do
    if q[i][1] <= f then local fn = q[i][2]; table.remove(q, i); fn() else i = i + 1 end
  end
end

local function key() return emu:read32(emu:read32(0x03005D90) + 0xAC) & 0xFFFF end
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1)
  emu:write8(0x03000E38, 0)
end
local function additem(id, n) run({0x44, id & 0xFF, id >> 8, n, 0, 0x02}) end
local function slots()
  local t = {}
  for i = 0, 199 do t[i] = {emu:read16(NEW + 4 * i), emu:read16(NEW + 4 * i + 2) ~ key()} end
  return t
end
local function sig(t)
  local s = {}
  for i = 0, 199 do s[#s + 1] = t[i][1] .. "x" .. t[i][2] end
  return table.concat(s, ",")
end
local function multiset(t)
  local ids = {}
  for i = 0, 199 do if t[i][1] ~= 0 then ids[#ids + 1] = t[i][1] * 1000 + t[i][2] end end
  table.sort(ids)
  return table.concat(ids, ",")
end
local function used() local n = 0; for i = 0, 199 do if emu:read16(NEW + 4 * i) ~= 0 then n = n + 1 end end; return n end
local function has(id) for i = 0, 199 do if emu:read16(NEW + 4 * i) == id then return i end end end
local function margin_ok()
  local bad = 0
  for a = MARGIN_LO, MARKER - 4, 4 do if emu:read32(a) ~= PATTERN then bad = bad + 1 end end
  return bad
end
local function name_of(id)
  local s = {}
  for k = 0, 13 do local c = emu:read8(ITEMS_TABLE + id * 44 + k); if c == 0xFF then break end; s[#s + 1] = c end
  return s
end
local function start_menu(action, fn)          -- open the Start menu and pick the entry with this action id
  tap(K.START)
  after(60, function()
    local n, cur, idx = emu:read8(0x0203760F), emu:read8(0x0203760E), nil
    local acts = {}
    for i = 0, n - 1 do acts[#acts + 1] = emu:read8(0x02037610 + i); if emu:read8(0x02037610 + i) == action then idx = i end end
    w("  start menu actions " .. table.concat(acts, " ") .. ", cursor " .. cur)
    if not idx then ok(false, "no action " .. action .. " in the Start menu"); return end
    local downs = (idx - cur) % n
    for d = 1, downs do after(d * 14, function() tap(K.DOWN) end) end
    after(downs * 14 + 20, function() tap(K.A); after(1, fn) end)
  end)
end
local function scroll_bag(taps, shots, fn)      -- DOWN taps inside an open Bag, screenshots at given counts
  for d = 1, taps do
    after(d * 10, function() tap(K.DOWN) end)
    if shots[d] then after(d * 10 + 8, function() shot(shots[d]) end) end
  end
  after(taps * 10 + 30, fn)
end
local function bag_row() return emu:read16(BAGPOS + 8) + emu:read16(BAGPOS + 0x12) end   -- Items: cursor + scroll
local function to_items() emu:write8(BAGPOS + 5, 0); emu:write16(BAGPOS + 8, 0); emu:write16(BAGPOS + 0x12, 0) end

local before_save
local function step_done()
  ok(margin_ok() == 0, "the margin 0x0203D908..0x0203DADC still holds the pattern (" .. margin_ok() .. " words changed)")
  w(fails == 0 and "ALL PASSED" or (fails .. " FAILED"))
  done()
end
local function step_save()
  w("5) save from the Start menu (test_bagslots_reload.lua boots the result)")
  before_save = sig(slots())
  local fh = io.open(DIR .. "bs_saved_sig.txt", "w"); fh:write(before_save); fh:close()
  local counter = emu:read32(0x03006200)
  start_menu(5, function()
    after(90, function() tap(K.A) end)          -- save? YES
    after(200, function() tap(K.A) end)         -- overwrite? YES
    after(900, function()
      ok(emu:read32(0x03006200) ~= counter, string.format("save counter moved (%d -> %d)", counter, emu:read32(0x03006200)))
      tap(K.A)
    end)
    after(960, function() tap(K.B) end)
    after(1060, step_done)
  end)
end
local function step_battle()
  w("4) wild battle, Bag from the battle menu")
  to_items()
  run({0xB6, 129, 0, 2, 0, 0, 0xB7, 0x02})      -- setwildbattle Magikarp Lv2; dowildbattle
  waitfor(function() return emu:read32(0x03005D60) == 0x08057589 end, function()
    tap(K.RIGHT)
    after(20, function() tap(K.A) end)
    waitfor(function() return cb2() == 0x081AAD5D end, function()
      after(120, function()
        ok(emu:read8(POCKETS + 4) == 200, "battle Bag: capacity 200")
        scroll_bag(206, {[206] = "bs_battle"}, function()
          ok(bag_row() == 200, "battle Bag: the last row reached is Cancel (row " .. bag_row() .. ")")
          tap(K.B)
          waitfor(function() return emu:read32(0x03005D60) == 0x08057589 end, function()
            tap(K.LEFT)
            local function fight()
              if cb2() == OVERWORLD then
                ok(emu:read8(0x0202433A) == 1, "battle won (outcome " .. emu:read8(0x0202433A) .. ")")
                after(60, step_save); return
              end
              if now % 20 == 0 then tap(K.A) end
              after(1, fight)
            end
            after(20, fight)
          end, 1500, "the battle menu after the Bag", function() tap(K.B) end)
        end)
      end)
    end, 600, "the battle Bag")
  end, 3000, "the battle menu", function() tap(K.B) end)   -- B moves the intro text on and picks nothing
end
local function step_additem()
  w("3) additem at the limit")
  -- make room for exactly one: drop the last slot's item
  local last = emu:read16(NEW + 4 * 199)
  emu:write32(NEW + 4 * 199, 0)
  additem(EXTRA1, 1)
  after(30, function()
    ok(emu:read16(RESULT) == 1 and has(EXTRA1) ~= nil and used() == 200, "a new item into the 200th slot (result " .. emu:read16(RESULT) .. ", used " .. used() .. ")")
    local before = sig(slots())
    additem(EXTRA2, 1)
    after(30, function()
      ok(emu:read16(RESULT) == 0 and has(EXTRA2) == nil and sig(slots()) == before, "a 201st distinct item is refused, pocket unchanged")
      local i = has(FILL[2]); local q0 = slots()[i][2]
      additem(FILL[2], 5)
      after(30, function()
        ok(emu:read16(RESULT) == 1 and slots()[i][2] == q0 + 5, "stacking onto an existing item still works")
        after(30, step_battle)
      end)
    end)
  end)
end
local function step_sort(n, ms, fn)
  if n == 0 then fn(); return end
  tap(K.START)
  after(90, function()
    shot("bs_sort" .. (4 - n))
    ok(multiset(slots()) == ms and used() == 200, "sort " .. (4 - n) .. " keeps the same 200 items")
    step_sort(n - 1, ms, fn)
  end)
end
local function step_bag()
  w("2) 200 items, field Bag")
  local k = key()
  for i = 0, 199 do emu:write16(NEW + 4 * i, FILL[i + 1]); emu:write16(NEW + 4 * i + 2, ((i % 99) + 1) ~ k) end
  local ms = multiset(slots())
  to_items()
  start_menu(2, function()
    waitfor(function() return cb2() == 0x081AAD5D end, function()
      after(150, function()
        shot("bs_top")
        local b1, b2 = emu:read32(0x0203CE74), emu:read32(0x0203CE78)
        w(string.format("  list buffers %08X (block %d B), %08X (block %d B)", b1, emu:read32(b1 - 12), b2, emu:read32(b2 - 12)))
        ok(emu:read32(b1 - 12) >= 201 * 8 and emu:read32(b2 - 12) >= 200 * 24, "list buffers hold 201 rows and 200 names")
        local want, good = name_of(FILL[200]), true
        for k2, c in ipairs(want) do if emu:read8(b2 + 199 * 24 + k2 - 1) ~= c then good = false end end
        ok(good, "the 200th name in the list is item " .. FILL[200] .. "'s")
        scroll_bag(206, {[100] = "bs_mid", [206] = "bs_end"}, function()
          ok(bag_row() == 200, "field Bag: the last row reached is Cancel (row " .. bag_row() .. ")")
          for u = 1, 206 do after(u * 4, function() tap(K.UP, 2) end) end
          after(206 * 4 + 40, function()
            step_sort(3, ms, function()
              tap(K.B)
              after(120, function() tap(K.B) end)
              waitfor(function() return cb2() == OVERWORLD and lock() == 0 end, function() after(30, step_additem) end, 600, "the field")
            end)
          end)
        end)
      end)
    end, 600, "the Bag")
  end)
end
local function step_boot()
  w("1) after boot")
  w(string.format("  pockets: Items %08X x%d, Key %08X x%d, Balls %08X x%d, TMs %08X x%d, Berries %08X x%d",
    emu:read32(POCKETS), emu:read8(POCKETS + 4), emu:read32(POCKETS + 32), emu:read8(POCKETS + 36),
    emu:read32(POCKETS + 8), emu:read8(POCKETS + 12), emu:read32(POCKETS + 16), emu:read8(POCKETS + 20),
    emu:read32(POCKETS + 24), emu:read8(POCKETS + 28)))
  ok(emu:read32(POCKETS) == NEW and emu:read8(POCKETS + 4) == 200, "Items pocket is NEW x200")
  ok(emu:read32(POCKETS + 8) == 0x0203D288 and emu:read32(POCKETS + 16) == 0x0203D308 and emu:read32(POCKETS + 24) == 0x0203D510
     and emu:read32(POCKETS + 32) == 0x0203D1C0, "the other four pockets did not move")
  ok(emu:read32(MARKER) == MAGIC, "MARKER set")
  local same, n = true, 0
  for i = 0, 99 do
    if emu:read32(NEW + 4 * i) ~= emu:read32(OLD + 4 * i) then same = false end
    if emu:read16(OLD + 4 * i) ~= 0 then n = n + 1 end
  end
  local rest = true
  for i = 100, 199 do if emu:read32(NEW + 4 * i) ~= 0 then rest = false end end
  ok(same and n > 0, "migrated: new[0..99] = old[0..99] (" .. n .. " items)")
  ok(rest, "new[100..199] empty")
  for a = MARGIN_LO, MARKER - 4, 4 do emu:write32(a, PATTERN) end
  after(30, step_bag)
end
after(1, step_boot)
