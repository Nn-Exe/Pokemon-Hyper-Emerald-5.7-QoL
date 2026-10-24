-- iconnight: the screens with Pokemon icons at night (01:00) on Route 104 - the party, the Pokedex - against the
-- field, to see whether any of them is tinted (then its icons would now stand out the other way). The clock is set
-- as the field first comes up (the save's hour offset, SaveBlock2 + 0x9A), and the warp reads it again.
-- In patches/paldea/test_paldea.lua: run.ps1 -Rom w.gba -Steps ../iconnight/steps_night_menus.lua -Extra "NIGHT_HOUR=1"
-- (2026-10-21: neither screen is tinted at night, before or after iconnight; the pictures are the same.)
local HOUR = tonumber(os.getenv("NIGHT_HOUR") or "1")
local set = false
callbacks:add("frame", function()
  if set or emu:read32(0x030022C4) ~= 0x08085E5D then return end
  set = true
  local sb2 = emu:read32(0x03005D90)
  local now = emu:read8(0x03005CFA)
  local off = emu:read8(sb2 + 0x9A); if off > 127 then off = off - 256 end
  emu:write8(sb2 + 0x9A, (off + HOUR - now) % 24)
end)
STEPS = {
  {"repel", 250},
  {"warp", 0, 19, 10, 40},
  {"shot", "field"},
  {"menutop"}, {"press", "START", 90}, {"shot", "menu"},
  {"press", "DOWN", 20}, {"press", "A", 240}, {"shot", "party"},
  {"press", "B", 180}, {"press", "B", 120},
  {"menutop"}, {"press", "START", 90}, {"press", "A", 300}, {"shot", "pokedex"},
  {"press", "B", 240}, {"press", "B", 120},
  {"shot", "field_again"},
  {"finish"},
}
