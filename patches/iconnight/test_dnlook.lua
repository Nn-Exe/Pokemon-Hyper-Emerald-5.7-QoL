-- The DexNav on another map: warp there (warpsilent to the map's warp WARP), R, pictures of the screen; then the
-- cursor moves KEYS (a string of U/D/L/R, l/r for the shoulder buttons) and A registers, and the bar is photographed every 10 frames for a while
-- (its icon has two frames).
-- env: DN_DIR, TAG, GROUP, NUM, WARP (0), KEYS (""), SEEN (dex numbers), HOUR (the game's clock, roughly: the warp
-- reads it again; the log says the hour it got)
-- Runs through _testrun/dnstars/run.ps1 -Script test_dnlook.lua (a copy of this file there). iconnight: Route 104
-- (GROUP 0, NUM 19), SEEN "191 21", KEYS DRRRRR (Sunkern) or DDR (Spearow), at night: the log's "slot colours" of
-- the bar's icon must be the same as at noon.
local E = os.getenv
DIR = E("DN_DIR") or "./"
NAME = E("TAG") or "dnlook"
dofile("C:/Users/nonth/Desktop/Works & Productivity/gba-trans/hyper-emerald/hyper-emerald-en-qol/patches/dexnavchain/test_boot.lua")
local SCRIPT, ST = 0x0203F100, 0x0203A660
local GROUP, NUM, WARP = tonumber(E("GROUP") or "0"), tonumber(E("NUM") or "19"), tonumber(E("WARP") or "0")
local MOVES = E("KEYS") or ""
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1); emu:write8(0x03000E38, 0)
end
local KEYMAP = {U = K.UP, D = K.DOWN, L = K.LEFT, R = K.RIGHT, l = K.L, r = K.R}   -- l / r: the shoulder buttons
local t0
function TEST(f)
  t0 = t0 or f
  local d = f - t0
  if d == 5 and E("HOUR") then                             -- HOUR: the save's clock offset moved so that the
    local sb2 = emu:read32(0x03005D90)                     -- game's hour is HOUR after the warp re-reads it
    local now = emu:read8(0x03005CFA)
    local off = emu:read8(sb2 + 0x9A); if off > 127 then off = off - 256 end
    local new = (off + tonumber(E("HOUR")) - now) % 24
    emu:write8(sb2 + 0x9A, new)
    w(string.format("hour %d, offset %d -> %d", now, off, new))
  end
  if d == 300 then w(string.format("hour after the warp: %d, time of day %d", emu:read8(0x03005CFA), emu:read8(0x0203C000))) end
  if d == 5 then                                           -- SEEN: dex numbers marked seen and caught (as
    for n in (E("SEEN") or ""):gmatch("%d+") do            -- test_gen9rest.lua's dexSet, numbers below 960)
      n = tonumber(n)
      local sb1 = emu:read32(0x03005D8C)
      for _, base in ipairs({sb1 + 0x560, sb1 + 0x5D8}) do
        emu:write8(base + (n >> 3), emu:read8(base + (n >> 3)) | (1 << (n & 7)))
      end
    end
  end
  if d == 10 then run({0x3A, GROUP, NUM, WARP, 0, 0, 0, 0, 0x02}) end
  if d == 300 then shot(NAME .. "_0_arrived"); tap(K.R) end
  if d == 480 then shot(NAME .. "_1_screen") end
  if d == 490 then shot(NAME .. "_1_screen_b") end
  if d == 500 then shot(NAME .. "_1_screen_c") end
  for j = 1, #MOVES do
    if d == 500 + 20 * j then tap(KEYMAP[MOVES:sub(j, j)]) end
  end
  local after = 520 + 20 * #MOVES
  if d == after + 20 then shot(NAME .. "_2_cursor") end
  if d == after + 30 then shot(NAME .. "_2_cursor_b") end
  if d == after + 40 then tap(K.A) end
  if d > after + 240 and d <= after + 400 and (d - after) % 10 == 0 then
    shot(string.format("%s_3_bar_%03d", NAME, d - after - 240))
  end
  if d == after + 300 or d == after + 400 then              -- the sprite palette slots, and the bar icon's
    local tags = {}
    for i = 0, 15 do tags[#tags + 1] = string.format("%d:%04X", i, emu:read16(0x03000CF0 + 2 * i)) end
    w("palette tags: " .. table.concat(tags, " "))
    local spr = emu:read8(ST + 18)
    if spr < 64 then
      local s = 0x02020630 + 0x44 * spr
      local pal = emu:read16(s + 4) >> 12
      local cols = {}
      for k = 0, 15 do cols[#cols + 1] = string.format("%04X", emu:read16(0x05000200 + 32 * pal + 2 * k)) end
      w(string.format("icon sprite %d: palette slot %d, template tag %04X | slot colours %s", spr, pal,
        emu:read16(emu:read32(s + 0x14) + 2), table.concat(cols, " ")))
    end
  end
  if d == after + 410 then
    w(string.format("registered: species %d flags %02X window %d icon sprite %d", emu:read16(ST + 2), emu:read8(ST + 9),
      emu:read8(ST + 14), emu:read8(ST + 18)))
    done()
  end
end
