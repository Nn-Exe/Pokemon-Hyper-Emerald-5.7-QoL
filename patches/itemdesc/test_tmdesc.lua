-- TM descriptions in the Bag. Fills the TM pocket with the TMs itemdesc rewrote (TM75 and the 19 of 2026-10-01),
-- opens the Bag on that pocket from the Start menu and screenshots each one with the cursor on it
-- (tmdesc_NN.png, NN = the row), then logs the item under the cursor for every shot. The log tmdesc_log.txt.
NAME = "tmdesc"
DIR = DIR or "./"
HERE = HERE or DIR
dofile(HERE .. "../dexnavchain/test_boot.lua")
local POCKETS, BAGPOS = 0x02039DD8, 0x0203CE58
local TMS = {8, 9, 11, 12, 28, 31, 38, 40, 50, 54, 56, 63, 65, 69, 75, 80, 87, 101, 103, 118}
local q, now = {}, 0
local function after(d, fn) q[#q + 1] = {now + d, fn} end
local function waitfor(cond, fn, limit, tag)
  local start = now
  local function poll()
    if cond() then fn() elseif now - start > limit then w("FAIL timed out waiting for " .. tag); done()
    else after(1, poll) end
  end
  after(1, poll)
end
local function key() return emu:read32(emu:read32(0x03005D90) + 0xAC) & 0xFFFF end
local function start_menu(action, fn)
  tap(K.START)
  after(60, function()
    local n, cur, idx = emu:read8(0x0203760F), emu:read8(0x0203760E), nil
    for i = 0, n - 1 do if emu:read8(0x02037610 + i) == action then idx = i end end
    if not idx then w("FAIL no action " .. action .. " in the Start menu"); done(); return end
    local downs = (idx - cur) % n
    for d = 1, downs do after(d * 14, function() tap(K.DOWN) end) end
    after(downs * 14 + 20, function() tap(K.A); after(1, fn) end)
  end)
end
local function begin()
  local slots, cap = emu:read32(POCKETS + 16), emu:read8(POCKETS + 20)
  local k = key()
  for i = 0, cap - 1 do
    local it = TMS[i + 1] and (377 + TMS[i + 1]) or 0
    emu:write16(slots + 4 * i, it); emu:write16(slots + 4 * i + 2, it ~= 0 and (1 ~ k) or 0)
  end
  w(string.format("TM pocket %08X x%d filled with %d TMs", slots, cap, #TMS))
  emu:write8(BAGPOS + 5, 2); emu:write16(BAGPOS + 8 + 4, 0); emu:write16(BAGPOS + 0x12 + 4, 0)
  start_menu(2, function()
    waitfor(function() return cb2() == 0x081AAD5D end, function()
      after(150, function()
        for r = 0, #TMS - 1 do
          after(r * 24, function()
            if r > 0 then tap(K.DOWN) end
            after(16, function()
              local row = emu:read16(BAGPOS + 8 + 4) + emu:read16(BAGPOS + 0x12 + 4)
              w(string.format("row %2d: item %d (TM%d) pocket %d", row, emu:read16(slots + 4 * row),
                emu:read16(slots + 4 * row) - 377, emu:read8(BAGPOS + 5)))
              shot(string.format("tmdesc_%02d", r))
            end)
          end)
        end
        after(#TMS * 24 + 30, function() w("done"); done() end)
      end)
    end, 600, "the Bag")
  end)
end
local started = false
function TEST(f)
  now = now + 1
  if not started then started = true; after(30, begin) end
  local i = 1
  while i <= #q do
    if q[i][1] <= now then local fn = q[i][2]; table.remove(q, i); fn() else i = i + 1 end
  end
end
