-- A report: "I entered the Petalburg Woods and saved my game (didn't take a single step). I reloaded the save,
-- now I'm stuck inside of a tree." Route 104 below one of the woods' doors (env ROUTE_X, default 10: the doors at
-- 10,38 / 11,38 lead to the woods' warps 2 / 3; 32 / 33,42 to 4 / 5), up through the door, save from the Start
-- menu at once, reset, Continue, then try every way out.
-- Runs in patches/paldea/test_paldea.lua (a copy of _testrun/paldea/run.ps1 in _testrun/woods, the ROM and its .sav
-- beside it; the save of "(my placements 27)" was used, standing in the Timeless Woods):
--   run.ps1 -Rom w.gba -Steps ../contexit/steps_woods.lua -Extra "ROUTE_X=10;ROUTE_Y=40;TURN=LEFT"
-- Before contexit, TURN=LEFT ends inside the tree at 25,42 and no step moves you; with it you stay on 26,42.
local rx = tonumber(os.getenv("ROUTE_X") or "10")
local ry = tonumber(os.getenv("ROUTE_Y") or "40")
local turn = os.getenv("TURN")                             -- TURN=LEFT / RIGHT / DOWN: one tap in the woods
-- ONWARP=26,43: then the player is put on that tile (a warp: setobjectxy, as no walk can stand you on one), to
-- see that Continue still takes you off a real door
local wx, wy = (os.getenv("ONWARP") or ""):match("(%d+),(%d+)")
STEPS = {
  {"repel", 250},
  {"warp", 0, 19, rx, ry},
  {"shot", "route104"},
  {"step", "UP", 2},
  {"wait", 240},
  {"shot", "woods_in"},
  {"avatar", "in"},
  turn and {"face", turn} or {"wait", 1},
  {"wait", 30},
  wx and {"script", {0x57, 0xFF, 0x00, tonumber(wx), 0, tonumber(wy), 0, 0x02}, 30} or {"wait", 1},
  {"avatar", "turned"},
  {"menutop"},
  {"press", "START", 90},
  {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15},
  {"shot", "menu_save"},
  {"press", "A", 60}, {"mash", "save", 0},
  {"shot", "saved"},
  {"avatar", "saved"},
  os.getenv("REC") and {"rec", "boot", 8} or {"wait", 1},
  {"reset"}, {"boot"},
  {"recstop"},
  {"shot", "continued"},
  {"avatar", "continued"},
  {"step", "UP", 1}, {"wait", 30}, {"avatar", "up"}, {"shot", "up"},
  {"step", "LEFT", 1}, {"wait", 30}, {"avatar", "left"}, {"shot", "left"},
  {"step", "RIGHT", 2}, {"wait", 30}, {"avatar", "right"}, {"shot", "right"},
  {"step", "DOWN", 1}, {"wait", 30}, {"avatar", "down"}, {"shot", "down"},
  {"finish"},
}

-- WATCH=1: the player's object event (gObjectEvents[0], 0x24 bytes) whenever it changes from the reset on, the
-- saved copy when the save is written, and pc / lr of every write to its tile (x at +0x10, y at +0x12)
if os.getenv("WATCH") then
  local PL = 0x02037350
  local function hex(a, n)
    local t = {}
    for k = 0, n - 1 do t[#t + 1] = string.format("%02X", emu:read8(a + k)) end
    return table.concat(t, " ")
  end
  local on, fr, last = false, 0, nil
  local function sb1() return emu:read32(0x03005D8C) end
  callbacks:add("reset", function() on = true; fr = 0; w("-- reset") end)
  callbacks:add("savedataUpdated", function()
    if on then return end
    local s = sb1()
    w(string.format("save written: pos %d,%d location %s | live %s | saved %s", emu:read16(s), emu:read16(s + 2),
      hex(s + 4, 8), hex(PL, 0x24), hex(s + 0xA30, 0x24)))
  end)
  callbacks:add("frame", function()
    if not on then return end
    fr = fr + 1
    local s = hex(PL, 0x24)
    if s ~= last and fr < 3000 then
      w(string.format("f%-5d cb2 %08X lock %d player %s | pos %d,%d", fr, emu:read32(0x030022C4), emu:read8(0x03000F2C), s,
        emu:read16(sb1()), emu:read16(sb1() + 2)))
      last = s
    end
  end)
  emu:setRangeWatchpoint(function()
    if not on then return end
    w(string.format("   write to the player's tile at f%d: pc %08X lr %08X r0 %08X r1 %08X r2 %08X", fr,
      emu:readRegister("pc"), emu:readRegister("lr"), emu:readRegister("r0"), emu:readRegister("r1"), emu:readRegister("r2")))
  end, PL + 0x10, PL + 0x14, C.WATCHPOINT_TYPE.WRITE)
end
