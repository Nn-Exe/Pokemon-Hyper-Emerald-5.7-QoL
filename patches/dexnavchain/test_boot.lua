-- Shared harness: boots the battery save to the field, then calls TEST(frame) every frame.
-- Run muted, next to game.gba/game.sav copies in DIR:
--   mGBA --script test_unbound.lua -C mute=1 -C fpsTarget=2000 -C audioSync=0 -C videoSync=0 game.gba
-- shared: boot from the battery save to the overworld, then hand over to TEST(f)
DIR = DIR or "./"
local NL = string.char(10)
LOG = io.open(DIR .. (NAME or "probe") .. "_log.txt", "w")
function w(s) LOG:write(s .. NL); LOG:flush() end
K = {A=0, B=1, SEL=2, START=3, RIGHT=4, LEFT=5, UP=6, DOWN=7, R=8, L=9}
OVERWORLD, BATTLE = 0x08085E5D, 0x08038421
function cb2() return emu:read32(0x030022C4) end
function lock() return emu:read8(0x03000F2C) end
function done() local fh = io.open(DIR .. (NAME or "probe") .. "_done.txt", "w"); fh:write("done"); fh:close() end
function shot(n) emu:screenshot(DIR .. n .. ".png") end
local f, booted, bootF = 0, false, 0
local rel = {}
function tap(k, len) emu:addKey(k); rel[k] = f + (len or 6) end
callbacks:add("frame", function()
  f = f + 1
  for k, t in pairs(rel) do if f >= t then emu:clearKey(k); rel[k] = nil end end
  if not booted then
    if cb2() == OVERWORLD and lock() == 0 and f > 300 then
      bootF = bootF + 1
      if bootF > 120 then booted = true; w("booted at frame " .. f) end
      return
    end
    bootF = 0
    if f % 60 == 0 then tap(K.START) elseif f % 60 == 30 then tap(K.A) end
    if f > 6000 then w("boot failed cb2=" .. string.format("%08X", cb2())); done() end
    return
  end
  TEST(f)
end)
