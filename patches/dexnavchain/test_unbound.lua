-- Arms a hunt through START -> DexNav (row 2), then catch / win / win / run: the chain must count the catch,
-- the run must break it, and the search level must rise on every encounter and land in flash sector 30.
NAME = NAME or "full"
dofile((DIR or "./") .. "test_boot.lua")
local ST = 0x0203A660
PLAN = PLAN or {"catch", "win", "win", "run"}
local t0, phase, bstart, n, fieldAt = nil, "arm", 0, 0, 0
local seq = {{10,"START"},{80,"UP"},{110,"UP"},{150,"A"},{340,"DOWN"},{390,"A"},{600,"B"}}
local function st() return string.format("chain %d SL %d lv %d stars %d item %d egg %d flags %02X",
  emu:read16(ST+4), emu:read8(ST+24), emu:read8(ST+6), emu:read8(ST+8), emu:read16(ST+26), emu:read16(ST+12), emu:read8(ST+9)) end
local function foe()
  local b = 0x02024744
  local iv = emu:read32(b+0x48); local n31 = 0
  for i=0,5 do if (iv >> (i*5)) & 31 == 31 then n31 = n31 + 1 end end
  local pid, otid = emu:read32(b), emu:read32(b+4)
  local sh = ((otid & 0xFFFF) ~ (otid >> 16) ~ (pid & 0xFFFF) ~ (pid >> 16)) < 8
  return string.format("foe sp %d lv %d item %d moves %d/%d/%d/%d pp0 %d 31s %d abil %d shiny %s",
    emu:read16(b+0x20), emu:read8(b+0x54), emu:read16(b+0x22), emu:read16(b+0x2C), emu:read16(b+0x2E),
    emu:read16(b+0x30), emu:read16(b+0x32), emu:read8(b+0x34), n31, iv >> 31, tostring(sh))
end
function TEST(f)
  t0 = t0 or f
  local r = f - t0
  if phase == "arm" then
    for _, s in ipairs(seq) do if r == s[1] then tap(K[s[2]]) end end
    if r == 700 then w("armed: species " .. emu:read16(ST+2) .. " " .. st()); if INJECT then INJECT() end; shot(NAME .. "_bar0"); phase = "field"; fieldAt = f; tap(K.RIGHT, 36) end
    return
  end
  local c = cb2()
  if c == BATTLE then
    if phase ~= "battle" then phase = "battle"; bstart = f; n = n + 1; w(string.format("battle %d (%s) starts, %s", n, PLAN[n] or "?", st())) end
    local b = f - bstart
    if b == 420 then w("   " .. foe()) end
    if b > 200 then emu:write16(0x02024084 + 0x28, 1) end
    local what = PLAN[n] or "run"
    if b > 450 then
      if what == "catch" then
        if b % 40 == 0 then tap(K.R) elseif b % 40 == 20 then tap(K.B) end
      elseif what == "win" then
        if b % 12 == 0 then tap(K.A) end
      else
        local q = b % 90
        if q == 0 then tap(K.DOWN) elseif q == 20 then tap(K.RIGHT) elseif q == 40 then tap(K.A) end
      end
    end
    return
  end
  if phase == "battle" and c == OVERWORLD then
    phase = "field"; fieldAt = f
    w(string.format("   ended outcome %d, lastfoe %d", emu:read8(0x0202433A), emu:read16(0x03005D30)))
  end
  if phase == "field" and fieldAt > 0 and f - fieldAt == 200 then
    w("   field: " .. st()); shot(NAME .. "_bar" .. n)
    if n >= #PLAN then phase = "end"; fieldAt = f end
  end
  if phase == "end" then
    if f - fieldAt == 900 then done() end
    return
  end
  if c ~= OVERWORLD or lock() ~= 0 then if f % 30 == 0 then tap(K.B) end return end
  if f - fieldAt > 220 then local p = (f - fieldAt) % 64; if p == 0 then tap(K.UP, 30) elseif p == 32 then tap(K.DOWN, 30) end end
  if r > 120000 then w("timeout"); done() end
end
