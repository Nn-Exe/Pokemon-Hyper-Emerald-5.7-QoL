-- DexNav probe: breakpoints on find() entry/return log every call while the screen draws;
-- after the screen is up, dump in-use sprites and OAM to see whether the icons exist.
local dir = "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/_testrun/"
local f = 0
local A, B, SELECT, START, RIGHT, LEFT, UP, DOWN = 0, 1, 2, 3, 4, 5, 6, 7
local NL = string.char(10)
local log = io.open(dir .. "dnp_log.txt", "w")
local addrs = {}
for line in io.lines(dir .. "dn_addrs.txt") do
  local k, v = line:match("(%S+)%s+(%x+)")
  if k then addrs[k] = tonumber(v, 16) end
end
log:write(string.format("find=%08x find_ret=%08x draw_page=%08x", addrs.find, addrs.find_ret, addrs.draw_page) .. NL)
local calls = 0
local ok1 = pcall(function()
  emu:setBreakpoint(function()
    calls = calls + 1
    if calls <= 40 then
      log:write(string.format("  find(target=%d) sp=%08x", emu:readRegister("r0"), emu:readRegister("sp")) .. NL)
    end
  end, addrs.find)
  emu:setBreakpoint(function()
    if calls <= 40 then
      log:write(string.format("    -> found=%d count=%d", emu:readRegister("r0"), emu:readRegister("r1")) .. NL)
    end
    log:flush()
  end, addrs.find_ret)
end)
log:write("breakpoints installed: " .. tostring(ok1) .. NL); log:flush()

local function dumpSprites(tag)
  local n = 0
  for i = 0, 63 do
    local s = 0x02020630 + i * 0x44
    if emu:read16(s + 0x3E) % 2 == 1 then
      n = n + 1
      local a0, a1, a2 = emu:read16(s), emu:read16(s + 2), emu:read16(s + 4)
      log:write(string.format("%s spr %2d y=%3d x=%3d pal=%2d tile=%4d cb=%08x", tag, i, a0 % 256, a1 % 512,
        math.floor(a2 / 4096), a2 % 1024, emu:read32(s + 0x1C)) .. NL)
    end
  end
  log:write(string.format("%s sprites in use: %d  dispcnt=%04x", tag, n, emu:read16(0x04000000)) .. NL)
  local t = tag .. " objpal tags:"
  for i = 0, 15 do t = t .. string.format(" %d:%04x", i, emu:read16(0x03000CF0 + i * 2)) end
  log:write(t .. NL)
  log:write(string.format("%s scratch: species=%d min=%d max=%d sec=%d", tag, emu:read16(0x02021DC4),
    emu:read8(0x02021DC6), emu:read8(0x02021DC7), emu:read8(0x02021DC8)) .. NL)
  log:flush()
end

local plan = {}
local function at(fr, fn) plan[#plan + 1] = {fr, fn} end
local function tap(key, fr) at(fr, function() emu:addKey(key) end); at(fr + 4, function() emu:clearKey(key) end) end
local t = 2600
tap(START, t + 10)
for i = 0, 6 do tap(DOWN, t + 80 + i * 12) end
tap(A, t + 190)
at(t + 300, function() emu:screenshot(dir .. "dnp_p1.png"); dumpSprites("p1") end)
at(t + 320, function() local fh = io.open(dir .. "dnp_done.txt", "w"); fh:write("done"); fh:close() end)
callbacks:add("frame", function()
  f = f + 1
  if f < 1900 and f % 90 == 0 then emu:addKey(START) end
  if f < 1900 and f % 90 == 5 then emu:clearKey(START) end
  if f == 2000 then emu:addKey(A) end
  if f == 2004 then emu:clearKey(A) end
  for _, p in ipairs(plan) do if f == p[1] then p[2]() end end
end)
