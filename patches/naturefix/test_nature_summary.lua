-- Nature display: set the lead Pokemon's nature override (mon+0x1F bits 0-6, bit 7 kept) to OVR, then open
-- START -> Party -> Summary and screenshot page 1. Logs the personality's own nature for comparison.
local OVR = tonumber(os.getenv("OVR") or "13")
NAME = "nat" .. OVR
dofile((DIR or "./") .. "../dexnavchain/test_boot.lua")
local PARTY = 0x020244EC
local t0, plan = nil, {}
local function at(d, fn) plan[#plan + 1] = {d, fn} end
at(0, function()
  local b = emu:read8(PARTY + 0x1F)
  emu:write8(PARTY + 0x1F, (b & 0x80) | OVR)
  w(string.format("lead species %d, personality %% 25 = %d, override %d -> %d",
    emu:read16(PARTY + 0x20), emu:read32(PARTY) % 25, b & 0x7F, OVR))
end)
at(20, function() tap(K.START) end)
at(80, function() tap(K.DOWN) end)
at(110, function() tap(K.A) end)
at(220, function() tap(K.A) end)
at(280, function() shot("nat" .. OVR .. "_actions") end)
at(300, function() tap(K.A) end)
at(420, function() shot("nat" .. OVR .. "_summary"); done() end)
function TEST(f)
  t0 = t0 or f
  for _, p in ipairs(plan) do if f - t0 == p[1] then p[2]() end end
end
