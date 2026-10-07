-- zhtext in battle. MODE=higher (default): a wild Magikarp Lv 5; the lead gets Swords Dance in slot 1 and Attack at
-- +6, then uses it: the message must read "... won't/can't go higher!" (the word comes from the patch's stub).
-- MODE=defeat: a scripted trainer battle (type 3, no intro) against TRAINER with the defeat text the ROM's own script
-- uses (read from SITE, a trainerbattle argument the patch re-pointed); the foe is left with 1 HP and no reserves, the
-- lead uses Swift, and every page of the defeat speech is logged and shot.
-- Log: zhtext_<mode>_log.txt (each new battle string / field string, decoded); shots zh_<mode>_*.png.
local MODE = os.getenv("MODE") or "higher"
local TRAINER = tonumber(os.getenv("TRAINER") or "0x0541")
local SITE = tonumber(os.getenv("SITE") or "0")
NAME = "zhtext_" .. MODE
dofile((DIR or "./") .. "../dexnavchain/test_boot.lua")
local SCRIPT = 0x0203F100
local ACTION, MOVE = 0x08057589, 0x08057BFD
local MONS, PARTY, FOES = 0x02024084, 0x020244EC, 0x02024744
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1); emu:write8(0x03000E38, 0)
end
local function ctrl() return emu:read32(0x03005D60) end
local PUN = {[0x00] = " ", [0xAB] = "!", [0xAC] = "?", [0xAD] = ".", [0xAE] = "-", [0xB0] = "...", [0xB1] = "\"", [0xB2] = "\"",
  [0xB3] = "'", [0xB4] = "'", [0xB8] = ",", [0xF0] = ":", [0xFE] = " / ", [0xFA] = " // ", [0xFB] = " /// ", [0x1B] = "e"}
local function text(addr, max)
  local s, hz = "", 0
  for i = 0, (max or 300) - 1 do
    local c = emu:read8(addr + i)
    if c == 0xFF then break end
    if c >= 0xBB and c <= 0xD4 then s = s .. string.char(65 + c - 0xBB)
    elseif c >= 0xD5 and c <= 0xEE then s = s .. string.char(97 + c - 0xD5)
    elseif c >= 0xA1 and c <= 0xAA then s = s .. string.char(48 + c - 0xA1)
    elseif PUN[c] then s = s .. PUN[c]
    else s = s .. string.format("[%02X]", c); if c >= 1 and c <= 0x1E then hz = hz + 1 end end
  end
  return s, hz
end
local last, lastField, shots, pend = "", "", 0, {}
local function watch(d)
  local s = text(0x02022E2C)
  if s ~= last and #s > 0 then
    last = s; w(string.format("+%d battle: %s", d, s))
    -- shots once the text has been printed: the stat message, the challenge line and the defeat speech (twice: it scrolls)
    if s:find("higher") or s:find("would like") or s:find("defeated") then pend[d + 60] = true end
    if s:find(":") and MODE == "defeat" and d > 1500 then pend[d + 90] = true; pend[d + 200] = true; pend[d + 330] = true end
  end
  if pend[d] then shots = shots + 1; shot(string.format("zh_%s_%02d", MODE, shots)) end
  local g = text(0x02021FC4)                          -- gStringVar4: the trainer's speech is expanded here
  if g ~= lastField and #g > 0 then lastField = g; w(string.format("+%d var4: %s", d, g)) end
end
local t0, phase, mark = nil, "start", nil
local function setmove(id, pp)
  emu:write16(MONS + 0x0C, id); emu:write8(MONS + 0x24, pp)
  emu:write16(PARTY + 0x2C, id); emu:write8(PARTY + 0x34, pp)
  emu:write16(0x02023068, id)
end
function TEST(f)
  t0 = t0 or f
  local d = f - t0
  if d == 10 then
    if MODE == "higher" then run({0xB6, 129, 0, 5, 0, 0, 0xB7, 0x02})
    else
      local p = emu:read8(SITE) | (emu:read8(SITE + 1) << 8) | (emu:read8(SITE + 2) << 16) | (emu:read8(SITE + 3) << 24)
      w(string.format("trainer %04X, defeat text at %08X (from %08X)", TRAINER, p, SITE))
      run({0x5C, 0x03, TRAINER & 0xFF, TRAINER >> 8, 0, 0, p & 0xFF, (p >> 8) & 0xFF, (p >> 16) & 0xFF, (p >> 24) & 0xFF, 0x02})
    end
  end
  if d > 20 and cb2() == BATTLE then watch(d) end
  if phase == "start" and d > 20 then
    if cb2() == BATTLE and ctrl() == ACTION then
      phase = "action"; mark = d
      if MODE == "defeat" then
        for b = 1, 3, 2 do emu:write16(MONS + 0x58 * b + 0x28, 1) end   -- the foes: 1 HP, and nobody behind them
        for i = 2, 5 do emu:write16(FOES + 100 * i + 0x56, 0) end
      end
      w(string.format("action menu at +%d; lead species %d, foe species %d hp %d", d, emu:read16(MONS), emu:read16(MONS + 0x58),
        emu:read16(MONS + 0x58 + 0x28)))
    end
    if d % 20 == 0 and cb2() == BATTLE then tap(K.A) end
  elseif phase == "action" then
    if d == mark + 30 then tap(K.A) end
    if d > mark + 30 and ctrl() == MOVE then phase = "move"; mark = d end
  elseif phase == "move" then
    -- the engine rewrites the battle copy of the lead while the menus are up, so the move and the stat stage are
    -- put in from the move menu until the move has been picked
    if d >= mark + 5 and d <= mark + 40 then
      if MODE == "higher" then setmove(14, 20); emu:write8(MONS + 0x19, 12)      -- Swords Dance; Attack at +6
      else
        setmove(57, 20)                                                          -- Surf: hits both foes
        for b = 1, 3, 2 do emu:write16(MONS + 0x58 * b + 0x28, 1) end
        for i = 0, 1 do emu:write16(FOES + 100 * i + 0x56, 1) end
      end
    end
    if d == mark + 10 then
      while emu:read8(0x020244B0) ~= 0 do emu:write8(0x020244B0, 0) end
      tap(K.A)
    end
    if d > mark + 40 then phase = "after"; mark = d end
  elseif phase == "after" then
    if MODE == "higher" then
      if d == mark + 600 then shot("zh_higher_end") end
      if d > mark + 600 and d % 30 == 0 and cb2() == BATTLE then           -- run away
        if ctrl() == ACTION then emu:write8(0x020244AC, 3); tap(K.A) else tap(K.B) end
      end
    elseif d % 120 == 0 and cb2() ~= OVERWORLD then tap(K.A) end
    if d > mark + 200 and cb2() == OVERWORLD and lock() == 0 then phase = "end"; w("back on the field at +" .. d); done() end
  end
  if d > 9000 and phase ~= "end" then w("TIMEOUT in " .. phase); shot("zh_" .. MODE .. "_timeout"); phase = "end"; done() end
end
