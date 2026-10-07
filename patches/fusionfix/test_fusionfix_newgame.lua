-- NEW GAME over a save that has a Pokemon stored inside a fusion (ours: Solgaleo inside Necrozma at 0x0203D5E0
-- and Zekrom inside Kyurem at 0x0203D800). The title screen has already loaded that save, so the slots are full
-- when NEW GAME is chosen; NewGameInitData must empty them (fx_newgame, in front of ClearBag), or the new game
-- starts with a fusion "already stored" and can never fuse. The original game and every build before the patch
-- keep them: there this test says 1 FAILED. Run next to game.gba/game.sav copies with DIR set.
NAME = "fusionfix_newgame"
DIR = DIR or "./"
local NL = string.char(10)
local LOG = io.open(DIR .. NAME .. "_log.txt", "w")
local function w(s) LOG:write(s .. NL); LOG:flush() end
local SLOTS = {{"Necrozma", 0x0203D5E0}, {"Calyrex", 0x0203D644}, {"Kyurem", 0x0203D800}}
local MAINMENU_TASK, CB2_NEWGAME = 0x0803024D, 0x08085EF9
local A, START, DOWN = 0, 3, 7
local f, phase, seen_menu, seen_ng = 0, 0, 0, 0
local function used()
  local n = 0
  for _, s in ipairs(SLOTS) do for k = 0, 99 do if emu:read8(s[2] + k) ~= 0 then n = n + 1 end end end
  return n
end
local function slots()
  local t = {}
  for _, s in ipairs(SLOTS) do
    local used = 0
    for k = 0, 99 do if emu:read8(s[2] + k) ~= 0 then used = used + 1 end end
    t[#t + 1] = string.format("%s slot species %d L%d (%d of 100 bytes not 0)", s[1], emu:read16(s[2] + 0x20),
      emu:read8(s[2] + 0x54), used)
  end
  return table.concat(t, " | ")
end
local function main_menu_up()
  for t = 0, 15 do
    local a = 0x03005E00 + t * 40
    if emu:read8(a + 4) ~= 0 and emu:read32(a) == MAINMENU_TASK then return true end
  end
  return false
end
local function finish()
  local fh = io.open(DIR .. NAME .. "_done.txt", "w"); fh:write("done"); fh:close()
end
callbacks:add("frame", function()
  f = f + 1
  emu:clearKeys(0x3FF)
  if phase == 0 then                                        -- title -> main menu
    if main_menu_up() then
      seen_menu = seen_menu + 1
      if seen_menu == 60 then
        w("main menu, the save loaded: " .. slots())
        emu:addKey(DOWN)                                      -- CONTINUE -> NEW GAME
      elseif seen_menu == 90 then emu:addKey(A); phase = 1; w("NEW GAME chosen at frame " .. f) end
    elseif f % 40 < 4 then emu:addKey(START) end
  elseif phase == 1 then                                    -- Birch's speech, naming: A, START on the keyboard
    if emu:read32(0x030022C4) == CB2_NEWGAME then phase = 2; seen_ng = f; w("CB2_NewGame set at frame " .. f) end
    local c = f % 40
    if c < 4 then emu:addKey(A) elseif c >= 20 and c < 24 and f % 400 < 40 then emu:addKey(START) end
    if f > 60000 then w("CB2_NewGame never came"); finish(); phase = 9 end
  elseif phase == 2 then                                    -- NewGameInitData has run by now
    if f - seen_ng < 600 then return end
    w(string.format("600 frames into the new game (cb2 %08X): %s", emu:read32(0x030022C4), slots()))
    w(used() == 0 and "  ok   the new game starts with nothing inside a fusion" or "  FAIL the new game inherited what was inside a fusion")
    w(used() == 0 and "ALL PASSED" or "1 FAILED")
    emu:screenshot(DIR .. "fusionfix_newgame.png")
    finish()
    phase = 9
  end
end)
