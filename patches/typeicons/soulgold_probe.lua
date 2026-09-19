-- SoulGold badge probe: load the user's save state (a battle), then dump OAM, the sprite table and the
-- OBJ palettes, and save the tiles of every sprite in the badge area (right of the opponent's box).
local dir = "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/_testrun/"
local state = "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/_testrun/soulgold.ss1"
local f = 0
local NL = string.char(10)
local log = io.open(dir .. "sg_log.txt", "w")
local loaded = false
callbacks:add("frame", function()
  f = f + 1
  if f == 5 then
    local ok, err = pcall(function() return emu:loadStateFile(state) end)
    log:write("loadStateFile: " .. tostring(ok) .. " " .. tostring(err) .. NL); log:flush()
  end
  if f == 65 then
    emu:screenshot(dir .. "sg_state.png")
    log:write(string.format("cb2=%08x dispcnt=%04x", emu:read32(0x030022C4), emu:read16(0x04000000)) .. NL)
    log:write("== OAM (all in-use entries) ==" .. NL)
    for i = 0, 127 do
      local a0, a1, a2 = emu:read16(0x07000000 + i * 8), emu:read16(0x07000000 + i * 8 + 2), emu:read16(0x07000000 + i * 8 + 4)
      local y, x = a0 % 256, a1 % 512
      local disabled = (math.floor(a0 / 256) % 4 == 2)
      if not disabled and not (y == 160 and x == 304) then
        log:write(string.format("oam %3d y=%3d x=%3d shape=%d size=%d bpp8=%d pal=%2d tile=%4d prio=%d", i, y, x,
          math.floor(a0 / 16384), math.floor(a1 / 16384), math.floor(a0 / 8192) % 2, math.floor(a2 / 4096), a2 % 1024,
          math.floor(a2 / 1024) % 4) .. NL)
      end
    end
    log:write("== gSprites @02020630 (in use) ==" .. NL)
    for i = 0, 63 do
      local s = 0x02020630 + i * 0x44
      if emu:read16(s + 0x3E) % 2 == 1 then
        local a0, a1, a2 = emu:read16(s), emu:read16(s + 2), emu:read16(s + 4)
        local tmpl = emu:read32(s + 0x14)
        local tt, pt, images, anims = 0, 0, 0, 0
        if tmpl >= 0x08000000 and tmpl < 0x0A000000 then
          tt = emu:read16(tmpl); pt = emu:read16(tmpl + 2); anims = emu:read32(tmpl + 8); images = emu:read32(tmpl + 12)
        end
        log:write(string.format("spr %2d y=%3d x=%3d pal=%2d tile=%4d shape=%d size=%d tmpl=%08x tileTag=%04x palTag=%04x anims=%08x images=%08x cb=%08x animNum=%d", i,
          a0 % 256, a1 % 512, math.floor(a2 / 4096), a2 % 1024, math.floor(a0 / 16384), math.floor(a1 / 16384), tmpl, tt, pt, anims, images,
          emu:read32(s + 0x1C), emu:read8(s + 0x2A)) .. NL)
      end
    end
    local t = "paltags:"
    for i = 0, 15 do t = t .. string.format(" %d:%04x", i, emu:read16(0x03000CF0 + i * 2)) end
    log:write(t .. NL)
    -- OBJ VRAM + palettes to files for offline decoding
    local vram = io.open(dir .. "sg_objvram.bin", "wb")
    for a = 0x06010000, 0x06017FFF, 4 do local v = emu:read32(a); vram:write(string.char(v % 256, math.floor(v / 256) % 256, math.floor(v / 65536) % 256, math.floor(v / 16777216) % 256)) end
    vram:close()
    local pal = io.open(dir .. "sg_objpal.bin", "wb")
    for a = 0x05000200, 0x050003FF, 2 do local v = emu:read16(a); pal:write(string.char(v % 256, math.floor(v / 256))) end
    pal:close()
    log:write("dumped vram+pal" .. NL); log:flush()
    local fh = io.open(dir .. "sg_done.txt", "w"); fh:write("done"); fh:close()
  end
end)
