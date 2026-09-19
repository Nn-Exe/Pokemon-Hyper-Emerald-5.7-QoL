-- Target-selection test: force the double-battle flag at the action menu so choosing a move enters target
-- selection, then log the opponent healthbox's bounce offset (pos2.y) frame by frame.
local dir = "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/_testrun/"
local TAG = os.getenv("TITAG") or "tt"
local f = 0
local A, B, SELECT, START, RIGHT, LEFT, UP, DOWN = 0, 1, 2, 3, 4, 5, 6, 7
local NL = string.char(10)
local log = io.open(dir .. TAG .. "_log.txt", "w")
local phase, battleStart, lastAction, t0 = "walk", nil, 0, nil
local chose, tstart, wp, dumpWriters = false, nil, nil, nil
local function menuReady() return emu:read32(0x03005D60) == 0x08057589 end
local function box()                       -- opponent healthbox body sprite address, or nil
  for i = 0, 63 do
    local s = 0x02020630 + i * 0x44
    if emu:read16(s + 0x3E) % 2 == 1 and emu:read32(s + 0x1C) == 0x08007429 and emu:read16(s + 0x3A) == 1 then
      return s
    end
  end
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
    if emu:read32(0x030022C4) ~= 0x08085e5d then
      emu:clearKey(LEFT); emu:clearKey(RIGHT); battleStart = f; lastAction = f; phase = "forcing"
      log:write("left the overworld at f=" .. f .. NL); log:flush()
    end
    if f > 12000 then local fh = io.open(dir .. TAG .. "_done.txt", "w"); fh:write("no battle"); fh:close(); phase = "over" end
  elseif phase == "forcing" then
    emu:write32(0x02022FEC, emu:read32(0x02022FEC) | 1)       -- double battle, before setup reads it
    if f > battleStart + 150 then
      phase = "wait"
      log:write(string.format("battlers=%d flags=%08x", emu:read8(0x0202406C), emu:read32(0x02022FEC)) .. NL); log:flush()
    end
  elseif phase == "wait" then
    if menuReady() and f > lastAction + 150 then
      emu:clearKey(A); t0 = f; phase = "test"
      log:write(string.format("menu: battlers=%d flags=%08x", emu:read8(0x0202406C), emu:read32(0x02022FEC)) .. NL); log:flush()
    else
      if (f - battleStart) % 60 == 30 then emu:addKey(A) end
      if (f - battleStart) % 60 == 34 then emu:clearKey(A) end
      if f > lastAction + 4000 then local fh = io.open(dir .. TAG .. "_done.txt", "w"); fh:write("timeout"); fh:close(); phase = "over" end
    end
  elseif phase == "test" then
    local d = f - t0
    local cf = emu:read32(0x03005D60)
    if d == 10 then emu:addKey(A) end                       -- Fight
    if d == 14 then emu:clearKey(A) end
    if d > 20 and cf == 0x08057bfd and not chose then       -- move list is up
      if d == 40 then emu:addKey(RIGHT) end                 -- Rock Slide hits both: pick Mud Shot instead
      if d == 44 then emu:clearKey(RIGHT) end
      if d == 70 then emu:addKey(A) end
      if d == 74 then emu:clearKey(A); chose = true; log:write("pressed A on move 2 at d=" .. d .. NL) end
    end
    if cf == 0x08057825 then                                -- target selection
      if not tstart then
        tstart = d; log:write("target selection at d=" .. d .. NL); emu:screenshot(dir .. TAG .. "_target.png")
        local s = box()
        if s then
          local hits, order = {}, {}
          wp = pcall(function()
            emu:setWatchpoint(function()
              local pc = 0; pcall(function() pc = emu:readRegister("pc") end)
              local k = string.format("%08x", pc)
              if not hits[k] then hits[k] = 0; order[#order+1] = k end
              hits[k] = hits[k] + 1
            end, s + 0x26, 1)
          end)
          log:write(string.format("watching pos2.y at %08x (ok=%s)", s + 0x26, tostring(wp)) .. NL)
          dumpWriters = function()
            for _, k in ipairs(order) do log:write(string.format("   writer pc %s x%d", k, hits[k]) .. NL) end
          end
        end
      end
      local s = box()
      if s and d - tstart < 70 then
        local bounce, inuse = 0, 0
        for i = 0, 63 do
          local sp = 0x02020630 + i * 0x44
          if emu:read16(sp + 0x3E) % 2 == 1 then
            inuse = inuse + 1
            if emu:read32(sp + 0x1C) == 0x08039DF9 then bounce = bounce + 1 end
          end
        end
        local hb = emu:read32(emu:read32(0x020244D0) + 4)
        if d - tstart < 4 then
          for i = 0, 63 do
            local sp = 0x02020630 + i * 0x44
            if emu:read16(sp + 0x3E) % 2 == 1 and emu:read32(sp + 0x1C) == 0x08039DF9 then
              log:write(string.format("  bounce spr %2d data0=%d data1=%d data2=%d data3=%d data4=%d", i,
                emu:read16(sp + 0x2E), emu:read16(sp + 0x30), emu:read16(sp + 0x32), emu:read16(sp + 0x34),
                emu:read16(sp + 0x36)) .. NL)
            end
          end
        end
        log:write(string.format("t+%3d pos2.y=%5d bounceSprites=%d inUse=%d flags[1]=%02x id=%02x", d - tstart,
          emu:read16(s + 0x26), bounce, inuse, emu:read8(hb + 12), emu:read8(hb + 12 + 2)) .. NL)
      end
      if d - tstart == 40 then emu:addKey(RIGHT) end
      if d - tstart == 44 then emu:clearKey(RIGHT) end
      if d - tstart == 70 then emu:screenshot(dir .. TAG .. "_target2.png")
        if dumpWriters then dumpWriters() end
        log:flush()
        local fh = io.open(dir .. TAG .. "_done.txt", "w"); fh:write("done"); fh:close(); phase = "over" end
    end
    if d % 30 == 0 and d < 400 then log:write(string.format("d=%3d controller=%08x", d, cf) .. NL); log:flush() end
    if d > 600 then log:flush(); local fh = io.open(dir .. TAG .. "_done.txt", "w"); fh:write("no target select"); fh:close(); phase = "over" end
  end
end)
