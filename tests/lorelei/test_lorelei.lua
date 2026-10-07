-- The Ice Maze (map 35/53): Lorelei at (20,9) and the sealed Flygon at (25,17), which gives the Flygonite.
-- Written for a report that the game freezes "after Lorelei finishes her dialogue". Clears their two "done" flags
-- (0x4163, 0x4160) so both are back, warps beside one, talks, and logs every change of the main callback, the
-- script pointer and the text buffers, with screenshots. Ends at the battle's action menu, or - with WIN=1 - after
-- the battle is won and the script has finished and the controls are free again ("COMPLETED").
-- Environment:
--   WX, WY, FACE     where to stand and which way to face (default 20,10 UP = Lorelei; 25,16 DOWN = the Flygon)
--   WIN=1            fight to the end: her Pokemon are kept at 1 HP and the lead at full HP
--   REAL=1 ALIVE=n   with WIN: each of her Pokemon first acts for n frames (default 1500) while the lead Splashes
--   LOSE=1           with WIN: lose instead (rough: the harness can end up in the party menu)
--   LAST=id          the trainer fought last this session (0x02038BCA): the script's `special 0x3E` picks the battle
--                    transition from it, before `trainerbattle` loads Lorelei's id
--   TFLAG=0|1        her "fought" flag (0x44A1); FLAGS=0x273+0x274 sets battle-rule flags; DIFF = var 0x409B;
--   LEVEL, COUNT     party levels / party size; GENDER; HOUR; SPEED (text speed 0-3); OPT13, OPT15 (option bytes)
--   LIMIT            frames before giving up (default 4500)
NAME = "lorelei"
dofile((DIR or "./") .. "../dexnavchain/test_boot.lua")
local SCRIPT = 0x0203F100
local ACTION = 0x08057589
local LIMIT = tonumber(os.getenv("LIMIT") or "4500")
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1); emu:write8(0x03000E38, 0)
end
local PUN = {[0x00] = " ", [0xAB] = "!", [0xAC] = "?", [0xAD] = ".", [0xAE] = "-", [0xB0] = "...", [0xB4] = "'", [0xB8] = ",",
  [0xF0] = ":", [0xFE] = " / ", [0xFA] = " // ", [0xFB] = " /// "}
local function text(addr, max)
  local s = ""
  for i = 0, (max or 200) - 1 do
    local c = emu:read8(addr + i)
    if c == 0xFF then break end
    if c >= 0xBB and c <= 0xD4 then s = s .. string.char(65 + c - 0xBB)
    elseif c >= 0xD5 and c <= 0xEE then s = s .. string.char(97 + c - 0xD5)
    elseif c >= 0xA1 and c <= 0xAA then s = s .. string.char(48 + c - 0xA1)
    elseif PUN[c] then s = s .. PUN[c]
    else s = s .. string.format("[%02X]", c) end
  end
  return s
end
local function objects()
  local s = ""
  for i = 0, 15 do
    local o = 0x02037350 + 0x24 * i
    if emu:read8(o) & 1 == 1 then
      s = s .. string.format(" #%d(local %d gfx %d at %d,%d)", i, emu:read8(o + 8), emu:read8(o + 5), emu:read16(o + 0x10) - 7, emu:read16(o + 0x12) - 7)
    end
  end
  return s
end
callbacks:add("crashed", function() w("*** the emulator reports a CRASH"); shot("lorelei_crash"); done() end)
local t0, stage, mark = nil, "warp", nil
local lastcb, lastptr, lastb, lastv, lastctrl, still = 0, 0, "", "", 0, 0
local idle = 0
local lasttf = -1
local curfoe, foeat, lastsig, sigat = -1, 0, "", 0
local ALIVE = tonumber(os.getenv("ALIVE") or "1500")
function TEST(f)
  t0 = t0 or f
  local d = f - t0
  if d == 5 then                                       -- flags 0x4160 (the Flygonite encounter) and 0x4163 (Lorelei): byte sb1+0x988+0x2C
    local a = emu:read32(0x03005D8C) + 0x988 + 0x2C
    w(string.format("flag byte %02X (bit 0 = 0x4160, bit 3 = 0x4163)", emu:read8(a)))
    if os.getenv("KEEPFLAG") ~= "1" then emu:write8(a, emu:read8(a) & 0xF6) end
    local sb1, sb2 = emu:read32(0x03005D8C), emu:read32(0x03005D90)
    w(string.format("difficulty var 0x409B = %d, gender %d, party count %d, lead level %d, hour %d", emu:read16(sb1 + 0x139C + 0x9B * 2),
      emu:read8(sb2 + 8), emu:read8(0x020244E9), emu:read8(0x020244EC + 0x54), emu:read8(0x03005CFA)))
    local v = tonumber(os.getenv("DIFF") or "")
    if v then emu:write16(sb1 + 0x139C + 0x9B * 2, v) end
    v = tonumber(os.getenv("LEVEL") or "")
    if v then for i = 0, 5 do emu:write8(0x020244EC + 100 * i + 0x54, v) end end
    v = tonumber(os.getenv("COUNT") or "")
    if v then emu:write8(0x020244E9, v); for i = v, 5 do emu:write16(0x020244EC + 100 * i + 0x20, 0) end end
    w(string.format("options: 0x13 %02X  0x14 %02X (text speed %d)  0x15 %02X", emu:read8(sb2 + 0x13), emu:read8(sb2 + 0x14),
      emu:read8(sb2 + 0x14) & 7, emu:read8(sb2 + 0x15)))
    v = tonumber(os.getenv("SPEED") or "")
    if v then emu:write8(sb2 + 0x14, (emu:read8(sb2 + 0x14) & 0xF8) | v) end
    v = tonumber(os.getenv("OPT15") or "")
    if v then emu:write8(sb2 + 0x15, v) end
    v = tonumber(os.getenv("OPT13") or "")
    if v then emu:write8(sb2 + 0x13, v) end
    -- Lorelei's "fought" flag as the hack numbers it: trainer 0x3D8 -> flag 0x44A1 -> SaveBlock2+0x88, bit 1
    w(string.format("trainer flag 0x44A1: %d (byte %02X)", (emu:read8(sb2 + 0x88) >> 1) & 1, emu:read8(sb2 + 0x88)))
    v = tonumber(os.getenv("TFLAG") or "")
    if v then emu:write8(sb2 + 0x88, (emu:read8(sb2 + 0x88) & 0xFD) | (v << 1)) end
    local fl = ""
    for _, id in ipairs({0x264, 0x268, 0x272, 0x273, 0x274, 0x276, 0x277, 0x278, 0x27F}) do
      fl = fl .. string.format(" %03X=%d", id, (emu:read8(sb1 + 0x1270 + (id >> 3)) >> (id & 7)) & 1)
    end
    w("battle-rule flags:" .. fl)
    for id in (os.getenv("FLAGS") or ""):gmatch("[^+]+") do
      id = tonumber(id)
      emu:write8(sb1 + 0x1270 + (id >> 3), emu:read8(sb1 + 0x1270 + (id >> 3)) | (1 << (id & 7)))
    end
    v = tonumber(os.getenv("GENDER") or "")
    if v then emu:write8(sb2 + 8, v) end
    v = tonumber(os.getenv("HOUR") or "")
    if v then
      local off = emu:read8(sb2 + 0x9A); if off >= 128 then off = off - 256 end
      emu:write8(sb2 + 0x9A, (off + emu:read8(0x03005CFA) - v) % 24)
    end
  end
  local WX, WY = tonumber(os.getenv("WX") or "20"), tonumber(os.getenv("WY") or "10")
  if d == 10 then run({0x39, 35, 53, 0xFF, WX, 0, WY, 0, 0x02}) end
  local c, p = cb2(), emu:read32(0x03000E48)
  local tf = (emu:read8(emu:read32(0x03005D90) + 0x88) >> 1) & 1
  if tf ~= lasttf then w(string.format("+%d trainer flag 0x44A1 is now %d (cb2 %08X, script %08X)", d, tf, c, p)); lasttf = tf end
  if c ~= lastcb then w(string.format("+%d cb2 %08X -> %08X", d, lastcb, c)); lastcb = c end
  if p ~= lastptr and (p < SCRIPT or p > SCRIPT + 0x40) then
    w(string.format("+%d script at %08X (mode %d, lock %d)", d, p, emu:read8(0x03000E41), lock())); lastptr = p; still = 0
  else still = still + 1 end
  local v = text(0x02021FC4, 120)
  if v ~= lastv then w(string.format("+%d var4: %s", d, v)); lastv = v end
  if c == BATTLE then
    local b = text(0x02022E2C, 120)
    if b ~= lastb then w(string.format("+%d battle: %s", d, b)); lastb = b end
    local k = emu:read32(0x03005D60)
    if k ~= lastctrl and stage ~= "fight" then w(string.format("+%d controller %08X", d, k)); lastctrl = k end
  end
  if stage == "warp" and d > 150 and c == OVERWORLD and lock() == 0 then
    stage = "face"; mark = d
    w(string.format("+%d on the map %d/%d at %d,%d; objects:%s", d, emu:read8(emu:read32(0x03005D8C) + 4), emu:read8(emu:read32(0x03005D8C) + 5),
      emu:read16(emu:read32(0x03005D8C)), emu:read16(emu:read32(0x03005D8C) + 2), objects()))
    shot("lorelei_0_map")
  elseif stage == "face" then
    if d == mark + 20 then tap(os.getenv("FACE") == "DOWN" and K.DOWN or K.UP) end
    if d == mark + 60 then
      -- the trainer fought last in this session: the script's `special 0x3E` picks the battle transition from it
      local v = tonumber(os.getenv("LAST") or "")
      w(string.format("last opponent (0x02038BCA) = %04X%s", emu:read16(0x02038BCA), v and string.format(" -> set to %04X", v) or ""))
      if v then emu:write16(0x02038BCA, v) end
      shot("lorelei_1_facing"); tap(K.A); stage = "talk"; mark = d
    end
  elseif stage == "talk" then
    if (d - mark) % 120 == 60 then shot(string.format("lorelei_t%04d", d - mark)) end
    if c ~= OVERWORLD and c ~= BATTLE and (d - mark) % 12 == 0 then shot(string.format("lorelei_x%04d", d - mark)) end
    if (d - mark) % 40 == 0 then tap(K.A) end
    if c == BATTLE and emu:read32(0x03005D60) == ACTION then
      w("+" .. d .. " REACHED the battle's action menu"); shot("lorelei_9_battle")
      if os.getenv("WIN") == "1" then stage = "fight"; mark = d else stage = "end"; done() end
    end
  elseif stage == "fight" then                        -- win: the foe is kept at 1 HP, the lead at full, A is pressed
    if c == BATTLE then
      local MONS = 0x02024084
      if os.getenv("REAL") == "1" then                -- let each of her Pokemon act for a while: the lead Splashes at full HP
        local foe = emu:read16(MONS + 0x58) * 256 + emu:read8(MONS + 0x58 + 0x54)
        if foe ~= curfoe then curfoe = foe; foeat = d end
        emu:write16(MONS + 0x28, emu:read16(MONS + 0x2C)); emu:write32(MONS + 0x4C, 0); emu:write32(MONS + 0x50, 0)
        if d - foeat < ALIVE then
          emu:write16(MONS + 0x0C, 150); emu:write16(0x020244EC + 0x2C, 150); emu:write8(MONS + 0x24, 20)
        else
          emu:write16(MONS + 0x0C, 332); emu:write16(0x020244EC + 0x2C, 332); emu:write8(MONS + 0x24, 20)
          if emu:read16(MONS + 0x58 + 0x28) > 1 then emu:write16(MONS + 0x58 + 0x28, 1) end
        end
        if emu:read32(0x03005D60) == ACTION then emu:write8(0x020244AC, 0) end
        local sig = lastb .. string.format("%08X", emu:read32(0x03005D60))
        if sig ~= lastsig then lastsig = sig; sigat = d end
        if d - sigat > 2400 then
          w(string.format("+%d STUCK in battle for 2400 frames: controller %08X, text: %s", d, emu:read32(0x03005D60), lastb))
          shot("lorelei_stuck"); stage = "end"; done()
        end
      elseif os.getenv("LOSE") == "1" then                -- lose: the lead on 1 HP with Splash, nobody behind it
        if emu:read16(MONS + 0x28) > 1 then emu:write16(MONS + 0x28, 1) end
        emu:write16(0x020244EC + 0x56, 1)
        for i = 1, 5 do emu:write16(0x020244EC + 100 * i + 0x56, 0) end
        emu:write16(MONS + 0x0C, 150); emu:write16(0x020244EC + 0x2C, 150); emu:write16(0x02023068, 150); emu:write8(MONS + 0x24, 20)
      else
        if emu:read16(MONS + 0x58 + 0x28) > 1 then emu:write16(MONS + 0x58 + 0x28, 1) end
        emu:write16(MONS + 0x28, emu:read16(MONS + 0x2C)); emu:write8(MONS + 0x24, 20)
      end
      if emu:read32(0x03005D60) == 0x08057BFD then emu:write8(0x020244B0, 0) end
    end
    if (d - mark) % 30 == 0 then tap(K.A) end
    if (d - mark) % 300 == 150 then shot(string.format("lorelei_f%05d", d - mark)) end
    if c == OVERWORLD and lock() == 0 and emu:read8(0x03000E41) == 0 then
      idle = (idle or 0) + 1
      if idle == 1 then shot("lorelei_after_first_free_frame") end
      if idle > 240 then
        local a = emu:read32(0x03005D8C) + 0x988 + 0x2C
        w(string.format("+%d COMPLETED: back on the field and free on map %d/%d; flag byte %02X; objects:%s", d,
          emu:read8(emu:read32(0x03005D8C) + 4), emu:read8(emu:read32(0x03005D8C) + 5), emu:read8(a), objects()))
        shot("lorelei_done"); stage = "end"; done()
      end
    else idle = 0 end
  end
  if d > LIMIT and stage ~= "end" then
    w(string.format("TIMEOUT in %s: cb2 %08X, script %08X mode %d, lock %d, frames without script progress %d", stage, c, p,
      emu:read8(0x03000E41), lock(), still))
    shot("lorelei_timeout"); stage = "end"; done()
  end
end
