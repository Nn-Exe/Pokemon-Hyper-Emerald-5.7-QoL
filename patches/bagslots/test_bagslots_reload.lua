-- Items pocket 200 slots, second half: boot the save test_bagslots.lua made (same DIR) and check it came back:
-- the pocket table, MARKER, the 200 slots against bs_saved_sig.txt (so no second migration), the margin pattern.
NAME = "bagslots_reload"
DIR = DIR or "./"
HERE = HERE or DIR
dofile(HERE .. "../dexnavchain/test_boot.lua")
local POCKETS, NEW, MARKER, MAGIC = 0x02039DD8, 0x0203DAE0, 0x0203DADC, 0x32474142
local fails = 0
local function ok(cond, msg) w((cond and "  ok   " or "  FAIL ") .. msg); if not cond then fails = fails + 1 end end
local function key() return emu:read32(emu:read32(0x03005D90) + 0xAC) & 0xFFFF end
local ran = false
function TEST(f)
  if ran then return end
  ran = true
  local fh = io.open(DIR .. "bs_saved_sig.txt", "r"); local want = fh:read("a"); fh:close()
  local s = {}
  for i = 0, 199 do s[#s + 1] = emu:read16(NEW + 4 * i) .. "x" .. (emu:read16(NEW + 4 * i + 2) ~ key()) end
  ok(emu:read32(POCKETS) == NEW and emu:read8(POCKETS + 4) == 200, "Items pocket is NEW x200")
  ok(emu:read32(MARKER) == MAGIC, "MARKER set")
  ok(table.concat(s, ",") == want, "the 200 slots came back exactly as saved (no second migration)")
  local bad = 0
  for a = 0x0203D908, MARKER - 4, 4 do if emu:read32(a) ~= 0x5AA5C33C then bad = bad + 1 end end
  ok(bad == 0, "the margin pattern came back through the save (" .. bad .. " words differ)")
  w(fails == 0 and "ALL PASSED" or (fails .. " FAILED"))
  done()
end
