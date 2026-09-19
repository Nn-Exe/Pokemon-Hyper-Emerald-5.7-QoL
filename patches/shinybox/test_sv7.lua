-- Real shiny test: as soon as a wild battle starts, give the wild Pokemon a personality with the wanted
-- shiny value (keeping personality % 24 so the data substructures stay in order, and re-keying the
-- encrypted block), so the game itself treats it as shiny - shiny sprite and, with the patch, gold box.
-- TARGET_SV = 0 -> shiny for any threshold; set it higher to find the hack's shiny threshold.
local TARGET_SV = 7
local TAG = "sv7"
local dir = "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/_testrun/"
local f = 0
local A, B, SELECT, START, RIGHT, LEFT, UP, DOWN, R = 0, 1, 2, 3, 4, 5, 6, 7, 8
local NL = string.char(10)
local log = io.open(dir .. TAG .. "_log.txt", "w")
local phase, battleStart, lastAction, t0, forced = "walk", nil, 0, nil, false
local PARTY = 0x02024744
local function menuReady() return emu:read32(0x03005D60) == 0x08057589 end

local function makeShiny()
  local pid = emu:read32(PARTY)
  local otid = emu:read32(PARTY + 4)
  local want = ((otid >> 16) ~ (otid & 0xFFFF) ~ TARGET_SV) & 0xFFFF
  local res = pid % 24
  local new = nil
  for lo = 0, 0xFFFF do
    local hi = want ~ lo
    local cand = hi * 0x10000 + lo
    if cand % 24 == res then new = cand break end
  end
  if not new then log:write("no personality found" .. NL) return end
  emu:write32(PARTY, new)                           -- this hack stores mon data unencrypted, so only
                                                    -- the personality changes (kept in the same %24 class)
  local sv = (new >> 16) ~ (new & 0xFFFF) ~ (otid >> 16) ~ (otid & 0xFFFF)
  log:write(string.format("pid %08x -> %08x  otid %08x  shinyValue=%d  species=%04x", pid, new, otid, sv,
    emu:read16(PARTY + 0x20)) .. NL)
  log:flush()
end

local function boxes(tag)
  for i = 0, 63 do
    local s = 0x02020630 + i * 0x44
    if emu:read16(s + 0x3E) % 2 == 1 and emu:read32(s + 0x1C) == 0x08007429 then
      log:write(string.format("%s spr %2d pal=%2d battler=%d", tag, i, math.floor(emu:read16(s + 4) / 4096),
        emu:read16(s + 0x3A)) .. NL)
    end
  end
  log:write(string.format("%s battlemon1 pid=%08x otid=%08x species=%04x", tag,
    emu:read32(0x02024084 + 0x58 + 0x48), emu:read32(0x02024084 + 0x58 + 0x54),
    emu:read16(0x02024084 + 0x58)) .. NL)
  log:flush()
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
    if emu:read32(0x030022C4) == 0x08038421 then
      emu:clearKey(LEFT); emu:clearKey(RIGHT); battleStart = f; lastAction = f; phase = "wait"
      log:write("battle at f=" .. f .. NL)
      makeShiny()
    end
    if f > 12000 then
      local fh = io.open(dir .. TAG .. "_done.txt", "w"); fh:write("no battle"); fh:close(); phase = "over"
    end
  elseif phase == "wait" then
    if battleStart and f == battleStart + 60 then emu:screenshot(dir .. TAG .. "_intro.png") end
    if battleStart and f == battleStart + 120 then emu:screenshot(dir .. TAG .. "_intro2.png") end
    if menuReady() and f > lastAction + 150 then
      emu:clearKey(A); t0 = f; phase = "test"
      emu:screenshot(dir .. TAG .. "_menu.png"); boxes("menu")
    else
      if (f - battleStart) % 60 == 30 then emu:addKey(A) end
      if (f - battleStart) % 60 == 34 then emu:clearKey(A) end
      if f > lastAction + 4000 then
        local fh = io.open(dir .. TAG .. "_done.txt", "w"); fh:write("timeout"); fh:close(); phase = "over"
      end
    end
  elseif phase == "test" then
    local d = f - t0
    if d == 60 then
      emu:screenshot(dir .. TAG .. "_battle.png"); boxes("battle")
      local fh = io.open(dir .. TAG .. "_done.txt", "w"); fh:write("done"); fh:close(); phase = "over"
    end
  end
end)
