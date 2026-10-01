-- Instant text. MODE (env):
--   menu   - START -> Option with Text Speed at Fast: RIGHT (Instant), RIGHT (wraps to Slow), LEFT (back to Instant),
--            LEFT x3 (Fast, Mid, Slow), LEFT (Instant); B saves; the option byte must read 3; reopen and look
--   text   - SPEED (env, 0-3) set, then a scripted message of three lines and two pages ("\l" scroll, "\p" clear):
--            logs, per page, the frame the printer starts waiting for A and how many characters it printed
--   battle - SPEED set, a wild Magikarp Lv 5 (B every 20 frames through the intro); RUN from the action menu;
--            logs the frames to the menu and back
-- Screenshots <NAME>_*.png; the log in <NAME>_log.txt.
NAME = "instanttext_" .. (os.getenv("MODE") or "menu") .. (os.getenv("SPEED") and ("_" .. os.getenv("SPEED")) or "")
dofile((DIR or "./") .. "../dexnavchain/test_boot.lua")
local MODE, SPEED = os.getenv("MODE") or "menu", tonumber(os.getenv("SPEED") or "3")
local SCRIPT, TEXT, PRINTERS = 0x0203F100, 0x0203F160, 0x020201B0
local t0, plan = nil, {}
local function at(d, fn) plan[#plan + 1] = {d, fn} end
local function sb2() return emu:read32(0x03005D90) end
local function speed() return emu:read8(sb2() + 0x14) & 7 end
local function setspeed(v) emu:write8(sb2() + 0x14, (emu:read8(sb2() + 0x14) & 0xF8) | v) end
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1)
  emu:write8(0x03000E38, 0)
end

if MODE == "menu" then
  local function open_option(d)       -- START, the cursor on OPTION (6) from the menu's own list, A
    at(d, function() tap(K.START) end)
    at(d + 60, function()
      local n, idx = emu:read8(0x0203760F), nil
      local acts = {}
      for i = 0, n - 1 do acts[#acts + 1] = emu:read8(0x02037610 + i); if emu:read8(0x02037610 + i) == 6 then idx = i end end
      w("start menu: {" .. table.concat(acts, ",") .. "} option at " .. tostring(idx))
      emu:write8(0x0203760E, idx or 0); tap(K.B)
    end)
    at(d + 120, function() tap(K.START) end)
    at(d + 200, function() tap(K.A) end)
  end
  at(10, function() setspeed(2); w("option = " .. speed()) end)
  open_option(20)
  local steps = {{"start", nil}, {"right1", K.RIGHT}, {"right2", K.RIGHT}, {"left1", K.LEFT}, {"left2", K.LEFT},
                 {"left3", K.LEFT}, {"left4", K.LEFT}, {"left5", K.LEFT}}
  for i, s in ipairs(steps) do
    local d = 500 + i * 40
    if s[2] then at(d, function() tap(s[2]) end) end
    at(d + 25, function() shot(NAME .. "_" .. i .. "_" .. s[1]) end)
  end
  at(900, function() tap(K.B) end)
  at(1100, function() w(string.format("after B: option = %d  cb2 %08X", speed(), cb2())) end)
  at(1150, function() tap(K.B) end)             -- close the start menu if it came back
  open_option(1250)
  at(1700, function() shot(NAME .. "_reopened"); w("reopened, option = " .. speed()) end)
  at(1720, function() tap(K.B) end)
  at(1900, function() w("end: option = " .. speed() .. string.format("  cb2 %08X", cb2())); done() end)

elseif MODE == "text" then
  -- "The quick brown fox jumps over / the lazy dog, twice, and then \l a third line scrolls in. \p Page two."
  local ENCODED = os.getenv("TEXTHEX")
  at(10, function()
    setspeed(SPEED)
    local i = 0
    for hx in ENCODED:gmatch("%x%x") do emu:write8(TEXT + i, tonumber(hx, 16)); i = i + 1 end
    w("speed " .. speed() .. ", text " .. i .. " bytes")
    run({0x67, TEXT & 0xFF, (TEXT >> 8) & 0xFF, (TEXT >> 16) & 0xFF, TEXT >> 24, 0x66, 0x6D, 0x68, 0x6B, 0x02})
  end)
  local started, page, lastwait, waitsince, first, c0 = nil, 1, nil, nil, nil, nil
  local function printer()
    for i = 0, 31 do
      local p = PRINTERS + 0x24 * i
      if emu:read8(p + 0x1B) ~= 0 then return p, i end
    end
  end
  function STEP(d)
    local p, idx = printer()
    if p and not started then
      started = d; first = d; c0 = emu:read32(p)
      w(string.format("printer %d active at d=%d, textSpeed %d", idx, d, emu:read8(p + 0x1D)))
    end
    if not started then return end
    if first and d <= first + 5 then
      w(string.format("  +%d: state %d, %d chars", d - first, p and emu:read8(p + 0x1C) or -1, p and (emu:read32(p) - c0) or -1))
      shot(NAME .. "_open" .. (d - first))
    end
    if p then
      local st, n = emu:read8(p + 0x1C), emu:read32(p) - c0
      if (st == 1 or st == 2 or st == 3) and not waitsince then
        waitsince = d
        w(string.format("page %d: waiting (state %d) at +%d frames, %d bytes in", page, st, d - started, n))
        shot(NAME .. "_page" .. page)
      end
      if waitsince and d == waitsince + 20 then tap(K.A); page = page + 1; started = d; waitsince = nil end
    elseif started and not waitsince then
      waitsince = d
      w(string.format("printer done at +%d frames after the last A", d - started))
    end
    if waitsince and not p and d == waitsince + 20 then tap(K.A) end      -- waitbuttonpress
    if waitsince and not p and d == waitsince + 60 then
      w(string.format("closed: script status %d", emu:read8(0x03000E38))); shot(NAME .. "_closed"); done(); STEP = nil
    end
    if d > 3000 then w("TIMEOUT"); done(); STEP = nil end
  end

elseif MODE == "battle" then
  local started, menu, back = nil, nil, nil
  at(10, function()
    setspeed(SPEED); w("speed " .. speed())
    started = 10
    run({0xB6, 129, 0, 5, 0, 0, 0xB7, 0x02})    -- setwildbattle Magikarp, Lv 5, no item; dowildbattle
  end)
  local ran = false
  function STEP(d)
    if not started or d < 20 then return end
    if cb2() == BATTLE and emu:read32(0x03005D60) == 0x08057589 and not menu then
      menu = d; w("action menu at +" .. (d - started) .. " frames"); shot(NAME .. "_menu")
    end
    if not menu and d % 20 == 0 and cb2() == BATTLE then tap(K.B) end   -- "Wild ... appeared!" waits for a button
    if menu and not ran then
      if d == menu + 8 then shot(NAME .. "_menu8") end
      if d == menu + 10 then tap(K.RIGHT) end
      if d == menu + 25 then tap(K.DOWN) end
      if d == menu + 40 then tap(K.A); ran = true; w("chose Run") end
    end
    if ran and (d == menu + 70 or d == menu + 100) then shot(NAME .. "_run" .. (d - menu)) end
    if ran and d > menu + 110 and d % 30 == 0 and cb2() ~= OVERWORLD then tap(K.B) end
    if ran and cb2() == OVERWORLD and lock() == 0 and not back then
      back = d; w("back on the field at +" .. (d - started) .. " frames (" .. (d - menu) .. " after the menu)")
      shot(NAME .. "_back"); done()
    end
    if d == started + 45 then shot(NAME .. "_intro45") end
    if d > 4000 and not back then w(string.format("TIMEOUT cb2 %08X", cb2())); shot(NAME .. "_timeout"); done(); back = d end
  end
end

function TEST(f)
  t0 = t0 or f
  local d = f - t0
  for _, p in ipairs(plan) do if d == p[1] then p[2]() end end
  if STEP then STEP(d) end
end
