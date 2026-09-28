-- Items pocket 200 slots, other players' saves: boot one made by make_test_saves.py (CASE = "full_junk" or
-- "already") and check what the loader left in both Items areas. Set CASE, DIR and HERE.
NAME = "bagslots_" .. CASE
DIR = DIR or "./"   -- holds game.gba, game.sav (one of the made saves) and expect.lua
HERE = HERE or DIR
dofile(HERE .. "../dexnavchain/test_boot.lua")
dofile(DIR .. "expect.lua")
local NEW, OLD, MARKER = 0x0203DAE0, 0x0203D030, 0x0203DADC
local fails, ran = 0, false
local function ok(c, m) w((c and "  ok   " or "  FAIL ") .. m); if not c then fails = fails + 1 end end
local function area(base, n) local t = {}; for i = 0, n - 1 do t[#t + 1] = emu:read32(base + 4 * i) end; return t end
local function same(a, b) if #a ~= #b then return false end; for i = 1, #a do if a[i] ~= b[i] then return false end end; return true end
local function zeros(n) local t = {}; for i = 1, n do t[i] = 0 end; return t end
function TEST(f)
  if ran then return end; ran = true
  ok(emu:read32(0x02039DD8) == NEW and emu:read8(0x02039DD8 + 4) == 200, "Items pocket is NEW x200")
  ok(emu:read32(MARKER) == 0x32474142, "MARKER set")
  local new = area(NEW, 200)
  if CASE == "full_junk" then
    local want = {}; for i = 1, 100 do want[i] = EXP_A_OLD[i] end; for i = 101, 200 do want[i] = 0 end
    ok(same(new, want), "all 100 old items copied in order, the junk in slots 100-199 cleared")
    ok(same(area(OLD, 100), EXP_A_OLD), "the old area left as it was")
  else
    ok(same(new, EXP_B_NEW), "already-upgraded save: its 150 items untouched (no migration)")
    ok(same(area(OLD, 100), EXP_B_OLD), "its stale old area not copied over")
  end
  w(fails == 0 and "ALL PASSED" or (fails .. " FAILED"))
  done()
end
