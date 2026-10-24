-- Random play for a long time, to catch rare freezes: MINUTES of game time (default 60) of random input weighted by
-- where the game is - on the field mostly walking (and the grass's wild battles), with A, B, START, SELECT (the key
-- ring), R (the DexNav) and L now and then; in battle mostly A (Fight, a move, the messages), B and the D-pad; in any
-- menu A, B and the D-pad. Every WARP_EVERY frames (default 9000), when the field is free, a warp to the next map
-- of WARPS ("g.n.x.y g.n.x.y ..."). SEED: Lua's random numbers. PARTY9=1: the party made six random new Pokemon
-- (slots 1200-1326, Lv 70) first.
-- Watched: a hash of OAM, the palettes and the BG scroll registers every 60 frames - unchanged for 2400 frames while
-- keys are pressed is a SUSPECTED freeze (logged with a shot, the run goes on); unchanged for 9000 is FROZEN (the run
-- stops); the CPU's pc outside the BIOS, EWRAM, IWRAM and the ROM is a CRASH. Logged each game minute: the callback,
-- the map, battles and warps so far; every callback seen once. Shots: one a minute (soak_MMM.png).
local E = os.getenv
DIR = E("GEN9_DIR")
NAME = (E("TAG") or "sk") .. "_soak"
dofile("C:/Users/nonth/Desktop/Works & Productivity/gba-trans/hyper-emerald/hyper-emerald-en-qol/patches/dexnavchain/test_boot.lua")
local MINUTES, WARP_EVERY = tonumber(E("MINUTES") or "60"), tonumber(E("WARP_EVERY") or "9000")
math.randomseed(tonumber(E("SEED") or "1"))
local WARPS = {}
for g, n, x, y in (E("WARPS") or ""):gmatch("(%d+)%.(%d+)%.(%d+)%.(%d+)") do WARPS[#WARPS + 1] = {tonumber(g), tonumber(n), tonumber(x), tonumber(y)} end
local SCRIPT, PARTY = 0x0203F100, 0x020244EC
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1); emu:write8(0x03000E38, 0)
end
local function give(sp, lv) run({0x79, sp & 0xFF, sp >> 8, lv, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0x02}) end
local function hash()
  local h = 0
  for a = 0x07000000, 0x070003FC, 4 do h = (h * 31 + emu:read32(a)) % 4294967291 end
  for a = 0x05000000, 0x050003FC, 8 do h = (h * 31 + emu:read32(a)) % 4294967291 end
  for a = 0x04000010, 0x0400001C, 4 do h = (h * 31 + emu:read32(a)) % 4294967291 end
  return h
end
local function sb1() return emu:read32(0x03005D8C) end
local t0, nextAct, held, lastHash, sameSince, suspect, battles, warps, wasBattle, warpi, lastWarp = nil, 0, nil, nil, 0, false, 0, 0, false, 0, 0
local seen, pressed = {}, 0
local KEYS = {A = K.A, B = K.B, START = K.START, SEL = K.SEL, R = K.R, L = K.L, UP = K.UP, DOWN = K.DOWN, LEFT = K.LEFT, RIGHT = K.RIGHT}
local DIRS = {K.UP, K.DOWN, K.LEFT, K.RIGHT}
local function pick(t) local r, acc = math.random(), 0; for _, e in ipairs(t) do acc = acc + e[2]; if r <= acc then return e[1] end end; return t[#t][1] end
local over = false
local function finish(msg) w(msg); done(); over = true end
function TEST(f)
  t0 = t0 or f
  local d = f - t0
  if over then return end
  if d == 5 and E("PARTY9") == "1" then emu:write8(0x020244E9, 0); for i = 0, 599 do emu:write8(PARTY + i, 0) end end
  if E("PARTY9") == "1" and d >= 10 and d < 10 + 6 * 25 and (d - 10) % 25 == 0 then give(1200 + math.random(0, 126), 70) end
  if d == 10 + 6 * 25 then
    emu:write8(0x03000F2C, 0)
    local t = {}; for i = 0, 5 do t[#t + 1] = emu:read16(PARTY + 100 * i + 0x20) end
    w("party: " .. table.concat(t, " "))
  end
  if d < 200 then return end
  local cb = cb2()
  if not seen[cb] then seen[cb] = true; w(string.format("  callback %08X first seen at minute %d", cb, d // 3600)) end
  local inBattle = (cb == BATTLE)
  if inBattle and not wasBattle then battles = battles + 1 end
  wasBattle = inBattle
  -- a crash: the pc outside every region that holds code
  local pc = emu:readRegister("pc")
  if not ((pc < 0x4000) or (pc >= 0x02000000 and pc < 0x02040000) or (pc >= 0x03000000 and pc < 0x03008000) or
          (pc >= 0x08000000 and pc < 0x0A000000)) then
    shot(NAME .. "_crash"); finish(string.format("CRASH: pc %08X at minute %d, callback %08X", pc, d // 3600, cb)); return
  end
  -- a freeze: nothing on screen changes while keys are pressed
  if d % 60 == 0 then
    local h = hash()
    if h == lastHash then
      if pressed > 0 and d - sameSince >= 2400 and not suspect then
        suspect = true; shot(string.format("%s_suspect_%d", NAME, d // 60))
        w(string.format("SUSPECTED freeze at minute %d: the screen unchanged for %d frames, callback %08X, pc %08X, lock %d",
          d // 3600, d - sameSince, cb, pc, lock()))
      end
      if d - sameSince >= 9000 then
        shot(NAME .. "_frozen"); finish(string.format("FROZEN at minute %d: callback %08X pc %08X", d // 3600, cb, pc)); return
      end
    else
      if suspect then w(string.format("  it moved again after %d frames", d - sameSince)) end
      lastHash = h; sameSince = d; suspect = false; pressed = 0
    end
  end
  if d % 3600 == 0 then
    w(string.format("minute %d: callback %08X map %d.%d battles %d warps %d", d // 3600, cb, emu:read8(sb1() + 4), emu:read8(sb1() + 5), battles, warps))
    shot(string.format("%s_%03d", NAME, d // 3600))
    if d // 3600 >= MINUTES then finish(string.format("played %d minutes: no crash, no freeze (%d battles, %d warps)", MINUTES, battles, warps)); return end
  end
  -- a warp now and then, when the field is free
  if #WARPS > 0 and d - lastWarp >= WARP_EVERY and cb == OVERWORLD and lock() == 0 then
    warpi = warpi % #WARPS + 1
    local wp = WARPS[warpi]
    run({0x39, wp[1], wp[2], 0xFF, wp[3] & 0xFF, wp[3] >> 8, wp[4] & 0xFF, wp[4] >> 8, 0x02})
    warps = warps + 1; lastWarp = d
    return
  end
  -- the input
  if held and d >= held[2] then emu:clearKey(held[1]); held = nil end
  if d < nextAct then return end
  local k, len
  if inBattle then
    k = pick({{K.A, 0.55}, {K.B, 0.2}, {DIRS[math.random(4)], 0.23}, {K.L, 0.02}}); len = 4
  elseif cb == OVERWORLD and lock() == 0 then
    k = pick({{DIRS[math.random(4)], 0.78}, {K.A, 0.08}, {K.B, 0.05}, {K.START, 0.03}, {K.SEL, 0.02}, {K.R, 0.03}, {K.L, 0.01}})
    len = (k == K.UP or k == K.DOWN or k == K.LEFT or k == K.RIGHT) and math.random(16, 64) or 4
  else
    k = pick({{K.A, 0.32}, {K.B, 0.38}, {DIRS[math.random(4)], 0.27}, {K.START, 0.02}, {K.R, 0.01}}); len = 4
  end
  emu:addKey(k); held = {k, d + len}; pressed = pressed + 1
  nextAct = d + len + math.random(6, 24)
end
