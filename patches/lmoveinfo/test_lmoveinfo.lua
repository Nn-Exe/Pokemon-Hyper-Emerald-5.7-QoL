-- L move info. A wild Magikarp Lv 5 (scripted); at the action menu A = Fight; then: the tag alone (shot), L held
-- (shots while it slides and when it is in), RIGHT / DOWN / LEFT with L held (the panel must follow the cursor),
-- L let go (it slides out), L again, B back to the action menu (everything of ours must be gone 3 frames later),
-- Fight again (the tag is back), then Run. Logged: the sprites in use and which sprite-tile tags are loaded at each
-- step, so a leak shows as a count that does not come back. Screenshots lmi_*.png; the log lmoveinfo_log.txt.
NAME = "lmoveinfo"
dofile((DIR or "./") .. "../dexnavchain/test_boot.lua")
local SCRIPT = 0x0203F100
local ACTION, MOVE = 0x08057589, 0x08057BFD       -- gBattlerControllerFuncs[0]: the action menu, the move menu
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1); emu:write8(0x03000E38, 0)
end
local function sprites()
  local n = 0
  for i = 0, 63 do if emu:read8(0x02020630 + 0x44 * i + 0x3E) & 1 == 1 then n = n + 1 end end
  return n
end
local function ctrl() return emu:read32(0x03005D60) end
local function move()
  local cur = emu:read8(0x020244B0)
  return emu:read16(0x02023068 + cur * 2), cur
end
local function state(tag)
  local m, cur = move()
  w(string.format("%-22s ctrl %08X sprites %2d cursor %d move %3d held %04X", tag, ctrl(), sprites(), cur, m,
    emu:read16(0x030022EC)))
end
local DOUBLE = os.getenv("DOUBLE") == "1"           -- DOUBLE=1: the same walk in a forced double battle (2 v 2)
local t0, phase, mark, base = nil, "start", nil, nil
local plan = {}
local function at(d, fn) plan[#plan + 1] = {d, fn} end
local function seq(m)                                -- relative to the frame the move menu came up
  at(m + 20, function() base = sprites(); state("move menu"); shot("lmi_1_tag") end)
  at(m + 30, function() emu:addKey(K.L) end)
  at(m + 32, function() shot("lmi_2_slide2") end)
  at(m + 35, function() shot("lmi_3_slide5") end)
  at(m + 50, function() state("L held"); shot("lmi_4_in") end)
  at(m + 60, function() tap(K.RIGHT) end)
  at(m + 75, function() state("L + right"); shot("lmi_5_right") end)
  at(m + 85, function() tap(K.DOWN) end)
  at(m + 100, function() state("L + down"); shot("lmi_6_down") end)
  at(m + 110, function() tap(K.LEFT) end)
  at(m + 125, function() state("L + left"); shot("lmi_7_left") end)
  at(m + 135, function() emu:clearKey(K.L) end)
  at(m + 138, function() shot("lmi_8_out3") end)
  at(m + 160, function() state("L let go"); shot("lmi_9_gone")
    w(string.format("  sprites back to the tag only: %s", tostring(sprites() == base))) end)
  at(m + 170, function() emu:addKey(K.L) end)
  at(m + 195, function() state("L again"); shot("lmi_10_again") end)
  at(m + 200, function() tap(K.B) end)                -- back to the action menu with L still held
  at(m + 230, function() emu:clearKey(K.L); state("action menu"); shot("lmi_11_action")
    w(string.format("  everything of ours gone: %s (sprites %d, the tag was 1 of %d)", tostring(sprites() < base),
      sprites(), base)) end)
  at(m + 250, function() tap(K.A) end)                -- Fight again
  at(m + 290, function() state("move menu again"); shot("lmi_12_tag_again")
    w(string.format("  the tag is back: %s", tostring(sprites() == base))) end)
  at(m + 300, function() tap(K.B) end)
  at(m + 340, function() tap(K.RIGHT) end)            -- Run
  at(m + 360, function() tap(K.DOWN) end)
  at(m + 380, function() tap(K.A) end)
end
function TEST(f)
  t0 = t0 or f
  local d = f - t0
  if d == 10 then run({0xB6, 129, 0, 5, 0, 0, 0xB7, 0x02}) end
  if DOUBLE and phase == "start" and d > 10 and cb2() ~= OVERWORLD then    -- force a double battle while it sets up
    emu:write32(0x02022FEC, emu:read32(0x02022FEC) | 1)
  end
  if phase == "start" and d > 20 then
    if cb2() == BATTLE and ctrl() == ACTION then phase = "action"; mark = d; state("action menu first") end
    if d % 20 == 0 and cb2() == BATTLE then tap(K.B) end
  elseif phase == "action" then
    if d == mark + 30 then tap(K.A) end
    if d > mark + 30 and ctrl() == MOVE then phase = "move"; seq(d); w("move menu at +" .. d) end
  elseif phase == "move" then
    for _, p in ipairs(plan) do if d == p[1] then p[2]() end end
    if d > plan[#plan][1] + 30 and d % 30 == 0 and cb2() ~= OVERWORLD then tap(K.B) end
    if d > plan[#plan][1] + 30 and cb2() == OVERWORLD and lock() == 0 then
      state("back on the field"); phase = "end"; done()
    end
  end
  if d > 6000 and phase ~= "end" then w("TIMEOUT in " .. phase); phase = "end"; done() end
end
