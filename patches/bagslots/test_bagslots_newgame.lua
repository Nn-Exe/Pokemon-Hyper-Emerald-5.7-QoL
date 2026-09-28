-- Items pocket 200 slots: NEW GAME over an old-layout save. The title screen has already loaded (and migrated)
-- that save, so the old Items area still holds its items. When NewGameInitData runs (CB2_NewGame), clear_bag
-- must empty the Items pocket, zero the old area and set MARKER - or the new game's first save would be
-- mistaken for an old one on the next load. Run next to game.gba/game.sav copies with DIR set.
NAME = "bagslots_newgame"
DIR = DIR or "./"
local NL = string.char(10)
local LOG = io.open(DIR .. NAME .. "_log.txt", "w")
local function w(s) LOG:write(s .. NL); LOG:flush() end
local NEW, OLD, MARKER, MAGIC = 0x0203DAE0, 0x0203D030, 0x0203DADC, 0x32474142
local MAINMENU_TASK, CB2_NEWGAME = 0x0803024D, 0x08085EF9
local A, START, DOWN = 0, 3, 7
local f, phase, seen_menu, fails, checked, seen_ng = 0, 0, 0, 0, false, 0
local function ok(cond, msg) w((cond and "  ok   " or "  FAIL ") .. msg); if not cond then fails = fails + 1 end end
local function count(base, n) local c = 0; for i = 0, n - 1 do if emu:read16(base + 4 * i) ~= 0 then c = c + 1 end end; return c end
local function main_menu_up()
  for t = 0, 15 do
    local a = 0x03005E00 + t * 40
    if emu:read8(a + 4) ~= 0 and emu:read32(a) == MAINMENU_TASK then return true end
  end
  return false
end
local function finish()
  w(fails == 0 and "ALL PASSED" or (fails .. " FAILED"))
  local fh = io.open(DIR .. NAME .. "_done.txt", "w"); fh:write("done"); fh:close()
end
callbacks:add("frame", function()
  f = f + 1
  emu:clearKeys(0x3FF)
  if phase == 0 then                                        -- title -> main menu
    if main_menu_up() then
      seen_menu = seen_menu + 1
      if seen_menu == 60 then
        w(string.format("main menu at frame %d: MARKER %08X, old area %d items, Items pocket %d items",
          f, emu:read32(MARKER), count(OLD, 100), count(NEW, 200)))
        ok(emu:read32(MARKER) == MAGIC and count(OLD, 100) > 0 and count(NEW, 200) == count(OLD, 100),
          "the title screen's load migrated the save (old area still full)")
        emu:addKey(DOWN)                                      -- CONTINUE -> NEW GAME
      elseif seen_menu == 90 then emu:addKey(A); phase = 1; w("NEW GAME chosen at frame " .. f) end
    elseif f % 40 < 4 then emu:addKey(START) end
  elseif phase == 1 then                                    -- Birch's speech, naming: A, START on the keyboard
    if emu:read32(0x030022C4) == CB2_NEWGAME and not checked then phase = 2; seen_ng = f; w("CB2_NewGame set at frame " .. f) end
    local c = f % 40
    if c < 4 then emu:addKey(A) elseif c >= 20 and c < 24 and f % 400 < 40 then emu:addKey(START) end
    if f > 60000 then ok(false, "CB2_NewGame never came"); finish(); phase = 9 end
  elseif phase == 2 then                                    -- wait for NewGameInitData: the old area empties
    if count(OLD, 100) ~= 0 and f - seen_ng < 600 then return end
    checked = true
    w(string.format("after NewGameInitData, frame %d (cb2 %08X): MARKER %08X, old area %d items, Items pocket %d items",
      f, emu:read32(0x030022C4), emu:read32(MARKER), count(OLD, 100), count(NEW, 200)))
    ok(emu:read32(0x02039DD8) == NEW and emu:read8(0x02039DD8 + 4) == 200, "Items pocket is NEW x200")
    ok(emu:read32(MARKER) == MAGIC, "MARKER set by the new game")
    ok(count(OLD, 100) == 0, "the old Items area is empty")
    ok(count(NEW, 200) == 0, "the new game's Items pocket is empty")
    emu:screenshot(DIR .. "bs_newgame.png")
    finish()
    phase = 9
  end
end)
