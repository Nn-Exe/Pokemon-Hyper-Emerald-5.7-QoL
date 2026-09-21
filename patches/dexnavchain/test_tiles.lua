-- Patch tile choice: forces hundreds of respawns and checks every chosen tile against the map data in RAM
-- (inside the map, collision 0, the player's height or 0/15, no object on it). For a map without encounter tiles,
-- repoint the IsLandWildEncounter literal in a scratch copy to a return-TRUE gadget (see DEXNAV-PROGRESS).
NAME = "tiles"
dofile((DIR or "./") .. "test_boot.lua")
local ST = 0x0203A660
local t0, n, bad, seen = nil, 0, 0, {}
local function pl() local id = emu:read8(0x02037595); return 0x02037350 + id*0x24 end
function TEST(f)
  t0 = t0 or f
  local r = f - t0
  if r == 5 then
    local sb1 = emu:read32(0x03005D8C)
    w(string.format("map %d.%d layout %dx%d", emu:read8(sb1+4), emu:read8(sb1+5), emu:read32(0x03005DC0), emu:read32(0x03005DC4)))
    emu:write16(ST+2, 108); emu:write16(ST+4, 0); emu:write8(ST+6, 65); emu:write8(ST+9, 1)
    emu:write8(ST+10, emu:read8(sb1+4)); emu:write8(ST+11, emu:read8(sb1+5)); emu:write8(ST+14, 0xFF); emu:write8(ST+18, 0xFF)
  end
  if r < 10 then return end
  if emu:read8(ST+9) & 8 ~= 0 then
    local x, y = emu:read8(ST+28), emu:read8(ST+29)
    local w_, h = emu:read32(0x03005DC0), emu:read32(0x03005DC4)
    local e = emu:read16(emu:read32(0x03005DC8) + (x + y * w_) * 2)
    local coll, elev = (e >> 10) & 3, e >> 12
    local pe = emu:read8(pl() + 11) & 15
    local obj = false
    for i = 0, 15 do local o = 0x02037350 + i*0x24
      if emu:read8(o) & 1 == 1 and emu:read16(o+0x10) == x and emu:read16(o+0x12) == y then obj = true end end
    local why = {}
    if x < 7 or x >= w_ - 8 or y < 7 or y >= h - 7 then why[#why+1] = "out of map" end
    if coll ~= 0 then why[#why+1] = "blocked" end
    if not (elev == pe or elev == 0 or elev == 15) then why[#why+1] = "height " .. elev .. " vs " .. pe end
    if obj then why[#why+1] = "object" end
    n = n + 1
    seen[x .. "," .. y] = true
    if #why > 0 then bad = bad + 1; w(string.format("BAD (%d,%d): %s", x, y, table.concat(why, ", "))) end
    emu:write8(ST+9, emu:read8(ST+9) & 0xF7)       -- clear the patch: another one next frame
  end
  if r == 2500 or n >= 400 then
    local k = 0; for _ in pairs(seen) do k = k + 1 end
    w(string.format("%d patches checked, %d distinct tiles, %d bad", n, k, bad)); done()
  end
end
