-- Forced trainer battle: set BATTLE_TYPE_TRAINER and an opponent id while the battle initialises,
-- then dump OBJ palette tags, healthbox sprites and badge sprites at the action menu.
local dir = "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/_testrun/"
local f, phase, battleStart, lastAction, t0 = 0, "walk", nil, 0, nil
local A, B, SELECT, START, RIGHT, LEFT, UP, DOWN = 0, 1, 2, 3, 4, 5, 6, 7
local NL = string.char(10)
local TRAINER = tonumber(os.getenv("TRAINER_ID") or "265")
local log = io.open(dir .. "tr_log_" .. TRAINER .. ".txt", "w")
local function menuReady() return emu:read32(0x03005D60) == 0x08057589 end
local function dump(tag)
  log:write("== " .. tag .. " ==" .. NL)
  local tags = {}
  for i = 0, 15 do tags[#tags + 1] = string.format("%d:%04x", i, emu:read16(0x03000CF0 + i * 2)) end
  log:write("palette tags: " .. table.concat(tags, " ") .. NL)
  local badges = 0
  for i = 0, 63 do
    local s = 0x02020630 + i * 0x44
    if emu:read16(s + 0x3E) % 2 == 1 then
      local cb = emu:read32(s + 0x1C)
      local pal = emu:read16(s + 4) >> 12
      if cb == 0x08007429 then
        log:write(string.format("  sprite %2d dummy-cb pal %2d x %3d y %3d data5 %d data6 %d", i, pal, emu:read16(s + 0x20), emu:read16(s + 0x22), emu:read16(s + 0x38), emu:read16(s + 0x3A)) .. NL)
      elseif cb == 0x08fda9cb then
        badges = badges + 1
        log:write(string.format("  BADGE %2d pal %2d x %3d y %3d flags %04x type %d battler %d", i, pal, emu:read16(s + 0x20), emu:read16(s + 0x22), emu:read16(s + 0x3E), emu:read16(s + 0x2E), emu:read16(s + 0x3A)) .. NL)
      end
    end
  end
  log:write(string.format("badges: %d; gBattleTypeFlags %08x; opponent species %d types %d/%d", badges, emu:read32(0x02022FEC), emu:read16(0x02024084 + 0x58), emu:read8(0x02024084 + 0x58 + 0x21), emu:read8(0x02024084 + 0x58 + 0x22)) .. NL)
  log:flush()
end
local function setcaught()
  local sb1 = emu:read32(0x03005D8C)
  local sp = emu:read16(0x02024084 + 0x58)
  local dex = emu:read16(0x08F50370 + 2 * (sp - 1))            -- SpeciesToNationalPokedexNum table
  local a, m = sb1 + 0x5D8 + (dex >> 3), 1 << (dex % 8)
  log:write(string.format("forcing caught: species %d -> dex %d (byte %02x -> %02x)", sp, dex, emu:read8(a), emu:read8(a) | m) .. NL)
  emu:write8(a, emu:read8(a) | m)
end
callbacks:add("frame", function()
  f = f + 1
  if f < 1900 and f % 90 == 0 then emu:addKey(START) end
  if f < 1900 and f % 90 == 5 then emu:clearKey(START) end
  if f == 2000 then emu:addKey(A) end
  if f == 2004 then emu:clearKey(A) end
  if phase == "walk" and f > 2600 then
    local k = math.floor((f - 2600) / 40) % 2
    if k == 0 then emu:clearKey(RIGHT); emu:addKey(LEFT) else emu:clearKey(LEFT); emu:addKey(RIGHT) end
    if emu:read32(0x030022C4) ~= 0x08085E5D then
      emu:write32(0x02022FEC, emu:read32(0x02022FEC) | 0x08)   -- BATTLE_TYPE_TRAINER
      emu:write16(0x02038BCA, TRAINER)                          -- gTrainerBattleOpponent_A
    end
    if emu:read32(0x030022C4) == 0x08038421 then
      emu:clearKey(LEFT); emu:clearKey(RIGHT); battleStart = f; lastAction = f; phase = "wait"
    end
    if f > 12000 then local fh = io.open(dir .. "tr_done_" .. TRAINER .. ".txt", "w"); fh:write("no battle"); fh:close(); phase = "over" end
  elseif phase == "wait" then
    if menuReady() and f > lastAction + 150 then emu:clearKey(A); t0 = f; phase = "test"
    else
      if (f - battleStart) % 60 == 30 then emu:addKey(A) end
      if (f - battleStart) % 60 == 34 then emu:clearKey(A) end
      if f > lastAction + 4000 then dump("timeout"); emu:screenshot(dir .. "tr_timeout_" .. TRAINER .. ".png"); local fh = io.open(dir .. "tr_done_" .. TRAINER .. ".txt", "w"); fh:write("timeout"); fh:close(); phase = "over" end
    end
  elseif phase == "test" then
    local d = f - t0
    if d == 5 then dump("at the action menu (before forcing caught)"); emu:screenshot(dir .. "tr_menu_" .. TRAINER .. ".png") end
    if d == 10 then setcaught() end
    if d == 90 then dump("80 frames after forcing caught"); emu:screenshot(dir .. "tr_caught_" .. TRAINER .. ".png")
      local fh = io.open(dir .. "tr_done_" .. TRAINER .. ".txt", "w"); fh:write("done"); fh:close(); phase = "over" end
  end
end)
