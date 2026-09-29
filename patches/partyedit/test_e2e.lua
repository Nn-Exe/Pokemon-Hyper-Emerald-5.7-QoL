-- END-TO-END: the user's exact flow. Max the Attack EV on the selected mon, exit, then open the party
-- summary and screenshot the stats page. Nothing is poked from Lua except the key presses and the reads.
local DIR = "/Users/ribeiro/Downloads/Pokemon-Hyper-Emerald-5.7-QoL/build/test/"
local A, B, START, DOWN, UP, RIGHT, R = 0, 1, 3, 7, 6, 4, 8
local frames, done = 0, false
local log = io.open(DIR .. "e2e_log.txt", "w")
local function w(s) log:write(s .. string.char(10)); log:flush() end
local PARTY = 0x020244EC
local function snap(tag)
  w(string.format("%s: atk_stat=%d hp=%d/%d ev_atk=%d nature=%d cb2=%08X", tag,
    emu:read16(PARTY + 0x5A), emu:read16(PARTY + 0x56), emu:read16(PARTY + 0x58),
    emu:read8(PARTY + 0x39), emu:read8(PARTY + 0x1F), emu:read32(0x030022C0 + 4)))
end
local function tap(f, key)
  if frames == f then emu:addKey(key) end
  if frames == f + 4 then emu:clearKey(key) end
end

callbacks:add("frame", function()
  frames = frames + 1
  if frames < 1900 and frames % 90 == 0 then emu:addKey(START) end
  if frames < 1900 and frames % 90 == 5 then emu:clearKey(START) end
  if frames == 2000 then emu:addKey(A) end
  if frames == 2004 then emu:clearKey(A) end
  if frames == 2400 then snap("before") end
  -- editor: 1 mon, so the action list is {Summary, Item, Edit, Moves, Cancel}
  tap(2600, START); tap(2750, DOWN); tap(2900, A); tap(3200, A)
  tap(3400, DOWN); tap(3470, DOWN); tap(3600, A)
  if frames == 3900 then snap("editor open") end
  -- EV page (START), row 1 = Atk EV, then +5 fifty times = +250
  tap(4000, START)
  tap(4200, DOWN)
  for k = 0, 49 do tap(4400 + k * 40, R) end
  if frames == 6600 then snap("after +250 Atk EV"); emu:screenshot(DIR .. "screens/e2e_edited.png") end
  tap(6800, B)
  if frames == 7200 then snap("back in field") end
  -- reopen: START menu cursor is on Party; party menu; action list cursor remembered on Edit -> UP x2
  tap(7400, START); tap(7600, A)
  if frames == 7800 then emu:screenshot(DIR .. "screens/e2e_party.png") end
  tap(7900, A)
  if frames == 8100 then emu:screenshot(DIR .. "screens/e2e_actions.png") end
  -- the action-list cursor starts on Summary again, so just press A (UP would wrap round to Moves)
  tap(8400, A)
  if frames == 8800 then emu:screenshot(DIR .. "screens/e2e_summary1.png"); snap("summary page1") end
  tap(9000, RIGHT)
  if frames == 9300 then emu:screenshot(DIR .. "screens/e2e_stats.png"); snap("summary page2") end
  if frames >= 9600 and not done then
    done = true; local f = io.open(DIR .. "e2e_done.txt", "w"); f:write("ok\n"); f:close()
  end
end)
