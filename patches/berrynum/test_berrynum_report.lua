-- Every berry in the pocket (vanilla 133-175 plus the hack's 704-727), optionally as a girl (pink Bag);
-- walk the cursor over all of them, screenshot each, and dump the state if the game crashes.
NAME = "berryuser"
dofile((DIR or "./") .. "../dexnavchain/test_boot.lua")
local GIRL = os.getenv("GIRL") == "1"
local plan, t0 = {}, nil
local function at(d, fn) plan[#plan + 1] = {d, fn} end
local n = 0

callbacks:add("crashed", function()
  local s = "CRASH"
  for i = 0, 15 do s = s .. string.format(" r%d=%08X", i, emu:readRegister("r" .. i)) end
  w(s)
  local sp = emu:readRegister("r13")
  local t = {}
  for i = 0, 63 do t[#t + 1] = string.format("%08X", emu:read32(sp + i * 4)) end
  w("stack " .. table.concat(t, " "))
  w("cb2 " .. string.format("%08X", cb2()))
  for k = 0, 15 do
    local b = 0x03005E00 + k * 0x28
    if emu:read8(b + 4) == 1 then w(string.format("task%d %08X", k, emu:read32(b))) end
  end
  shot("user_crash")
  done()
end)

at(0, function()
  if GIRL then emu:write8(emu:read32(0x03005D90) + 8, 1); w("player set to girl") end
  local base = emu:read32(0x02039DD8 + 3 * 8)
  local cap = emu:read8(0x02039DD8 + 3 * 8 + 4)
  -- quantity is stored xor the low half of the save's encryption key (SB2 + 0xAC)
  local key = emu:read16(emu:read32(0x03005D90) + 0xAC)
  -- the user's pocket as far as the screenshot shows it, plus one berry above Pecha and one below Kee
  local ids = {{134,1},{135,2},{138,1},{139,3},{145,1},{704,1},{724,1},{725,1},{726,1},{727,1}}
  local k = 0
  for _, e in ipairs(ids) do
    emu:write16(base + k * 4, e[1]); emu:write16(base + k * 4 + 2, e[2] ~ key); k = k + 1
  end
  for i = k, cap - 1 do emu:write32(base + i * 4, 0) end
  n = k
  w("pocket capacity " .. cap .. ", filled " .. k)
end)
at(20, function() tap(K.START) end)
at(80, function() tap(K.DOWN) end)
at(100, function() tap(K.DOWN) end)
at(150, function() tap(K.A) end)
at(300, function() tap(K.LEFT) end)
at(360, function() tap(K.LEFT) end)

function TEST(f)
  t0 = t0 or f
  local d = f - t0
  for _, p in ipairs(plan) do if d == p[1] then p[2]() end end
  if d >= 440 and (d - 440) % 24 == 0 then
    local k = (d - 440) // 24
    if k < n - 1 then
      if k >= 3 then shot(string.format("user_%02d", k)) end
      tap(K.DOWN)
    elseif k == n + 2 then
      shot("user_end"); w("no crash over " .. n .. " berries; cb2 " .. string.format("%08X", cb2())); done()
    end
  end
end
