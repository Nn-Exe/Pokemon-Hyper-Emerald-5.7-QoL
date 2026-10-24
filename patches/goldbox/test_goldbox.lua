-- (patches/goldbox/test_goldbox.lua: run it with gba-trans/hyper-emerald/_testrun/shinybox2/run.ps1 -Rom <rom> -Tag <name>
--  -Test <this file> -Env "KIND=double;FIRST=1;LAST=259", which gives it DIR, BOOT and NAME; final2.ps1 and
--  final3.ps1 there run the whole list.)
-- The gold healthbox, watched through every move in the game (2026-10-13; a report: "the shiny box sometimes still
-- disappear"). A wild battle on Route 102 (single or double, as the game gives it), every battler shiny the way
-- shinybox reads it (gBattleMons[n].otId = personality). Each turn every battler is given the same move (ids
-- FIRST..LAST from the environment), hit points, PP and status are put back, and on every battle frame each visible
-- healthbox is looked at:
--   gold    the box is on a slot from 10 up whose colour 2 in palette RAM is the gold
--   fading  not the gold, but the stock box palette is not at its full colours either (a fade has both)
--   plain   the box is on the stock palette
--   wrong   the box is on a slot from 10 up that holds other colours while the stock box is at full colours
-- Every run of plain / wrong frames is logged with the move, the sprite palette tags and a picture.
-- The turns are played by pressing A (FIGHT, the move under the cursor, the target offered).
-- SKIP: moves that end a wild battle or open the party screen.  Log: <NAME>_log.txt, last line SWEEP DONE.
NAME = NAME or "sweep"
dofile(BOOT)
local MONS, TAGS, SPR = 0x02024084, 0x03000CF0, 0x02020630
local GOLD = 0x1F5F
local FIRST, LAST = tonumber(os.getenv("FIRST") or "1"), tonumber(os.getenv("LAST") or "944")
-- MOVES="105,135,156" (the environment): these moves and no others, in this order
local LIST
if os.getenv("MOVES") then
  LIST = {}
  for id in os.getenv("MOVES"):gmatch("%d+") do LIST[#LIST + 1] = tonumber(id) end
  FIRST, LAST = 1, #LIST
end
local FRESH = tonumber(os.getenv("FRESH") or "10")       -- a new battle every so many moves (what lingers is gone)
local MAXSHOTS = tonumber(os.getenv("MAXSHOTS") or "60")
local NAMES = emu:read32(0x08000148)
local function name(m)
  local s = ""
  for i = 0, 12 do
    local c = emu:read8(NAMES + 13 * m + i)
    if c == 0xFF then break end
    if c >= 0xBB and c <= 0xD4 then s = s .. string.char(65 + c - 0xBB)
    elseif c >= 0xD5 and c <= 0xEE then s = s .. string.char(97 + c - 0xD5)
    elseif c >= 0xA1 and c <= 0xAA then s = s .. string.char(48 + c - 0xA1)
    elseif c == 0 then s = s .. " " elseif c == 0xAE then s = s .. "-" else s = s .. "?" end
  end
  return s
end
-- WATCH="r:08FEE400-08FEEA00,r:08FDA0B0-08FDA1C4" (the environment): a read watchpoint on each stretch, its hits
-- counted from the boot on (is a blank stretch of the ROM ever read? the second one, shinybox's own code, is read
-- on every battle frame: it shows the watchpoints see what there is to see)
local watch = {}
for a, b in (os.getenv("WATCH") or ""):gmatch("r:(%x+)%-(%x+)") do
  local e = {lo = tonumber(a, 16), hi = tonumber(b, 16), n = 0}
  watch[#watch + 1] = e
  emu:setRangeWatchpoint(function() e.n = e.n + 1 end, e.lo, e.hi, C.WATCHPOINT_TYPE.READ)
end
local SKIP = {}
for _, n in ipairs({"roar", "whirlwind", "teleport", "explosion", "selfdestruct", "self-destruct", "memento",
                    "healing wish", "lunar dance", "u-turn", "volt switch", "baton pass", "parting shot", "flip turn",
                    "final gambit", "misty explode", "mistyexplosion", "misty explosi", "dragon tail", "circle throw",
                    "chillyrecept", "chilly recep", "shed tail", "destiny bond", "perish song", "struggle",
                    "revival bless", "revivalblessi", "ally switch", "mirror move", "metronome", "sleep talk", "assist",
                    "copycat", "me first", "nature power", "snatch", "magic coat", "instruct", "after you", "quash",
                    "flatter"}) do SKIP[n] = true end
-- (Flatter: the game itself stops at "used Flatter!" in a double battle, before our patches too)
local function wait(n) for _ = 1, n do coroutine.yield() end end
local function run(bytes)
  local SCRIPT = 0x0203F100
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1)
  emu:write8(0x03000E38, 0)
end
local function ram(slot, i) return emu:read16(0x05000200 + slot * 32 + i * 2) end
local function unfaded(slot, i) return emu:read16(0x02037914 + slot * 32 + i * 2) end
local function tags()
  local s, used = "", 0
  for i = 0, 15 do
    local t = emu:read16(TAGS + 2 * i)
    s = s .. (i > 0 and " " or "") .. (t == 0xFFFF and "----" or string.format("%04X", t))
    if i >= 10 and t ~= 0xFFFF then used = used + 1 end
  end
  return s, used
end
function has(tag) for i = 0, 15 do if emu:read16(TAGS + 2 * i) == tag then return true end end return false end
local function stockslot()
  for i = 0, 15 do if emu:read16(TAGS + 2 * i) == 0xD6FF then return i end end
end
local function shiny(b)
  local p, o = emu:read32(MONS + b * 0x58 + 0x48), emu:read32(MONS + b * 0x58 + 0x54)
  local x = p ~ o
  return p ~= 0 and (((x >> 16) ~ (x & 0xFFFF)) < 8)
end
-- the healthbox bodies: battler -> {slot, hidden, id}
local function boxes()
  local t = {}
  for i = 0, 63 do
    local s = SPR + i * 0x44
    local fl = emu:read16(s + 0x3E)
    if (fl & 1) == 1 and emu:read32(s + 0x1C) == 0x08007429 then
      local bar = emu:read16(s + 0x38)
      if bar < 64 and emu:read32(SPR + bar * 0x44 + 0x1C) == 0x080728B5 then
        t[emu:read16(s + 0x3A)] = {slot = (emu:read16(s + 4) >> 12) & 15, hidden = (fl & 4) ~= 0, id = i}
      end
    end
  end
  return t
end
local function menu(b) return emu:read32(0x03005D60 + 4 * (b or 0)) == 0x08057589 end
local move, shots, frame = 0, 0, 0
local BADGECB, TITAG, GOLDTAG = 0x08FDA9CB, 0x5E62, 0x5E63
local function freeslots()
  local n = 0
  for i = emu:read8(0x0300301C), 15 do if emu:read16(TAGS + 2 * i) == 0xFFFF then n = n + 1 end end
  return n
end
local fails, nfail, calls = {}, 0, 0
emu:setBreakpoint(function()
  if cb2() ~= BATTLE then return end
  calls = calls + 1
  local tag = emu:read16(emu:readRegister("r0") + 4)
  if not has(tag) and freeslots() == 0 and not has(TITAG) and not has(GOLDTAG) then
    nfail = nfail + 1
    fails[move] = (fails[move] or 0) + 1
  end
end, 0x08008744)
emu:setBreakpoint(function()
  if cb2() ~= BATTLE then return end
  calls = calls + 1
  if freeslots() == 0 and not has(TITAG) and not has(GOLDTAG) then nfail = nfail + 1; fails[move] = (fails[move] or 0) + 1 end
end, 0x080087D4)
local nobadge, badgeshots, goldless = {}, 0, {}
local badgewrong = 0
local function badge_check()
  local slot = -1
  for i = 0, 15 do if emu:read16(TAGS + 2 * i) == TITAG then slot = i end end
  for i = 0, 63 do
    local s = SPR + i * 0x44
    local fl = emu:read16(s + 0x3E)
    if (fl & 1) == 1 and (fl & 4) == 0 and emu:read32(s + 0x1C) == BADGECB and ((emu:read16(s + 4) >> 12) & 15) ~= slot then
      badgewrong = badgewrong + 1
      if badgewrong <= 5 then
        w(string.format("   BADGE on slot %d, its palette is in slot %d (move %d, frame %d) | %s", (emu:read16(s + 4) >> 12) & 15, slot, move, frame, (tags())))
        shot(string.format("%s_badge_%d", NAME, badgewrong))
      end
    end
  end
end
-- What was DRAWN on the frame that just ended: OAM and palette RAM as they are now (the game copies the next
-- frame's in the vertical blank that follows). A type badge's OAM entry (its tile number) must be on a slot that
-- holds the badges' palette, a healthbox body's on one that holds the box palette, gold or not.
local dispbad, dispshots, dispseen = {badge = 0, box = 0}, 0, {badge = 0, box = 0}
local function drawn_check()
  local st = stockslot()
  if not st or ram(st, 2) ~= unfaded(st, 2) then return end       -- a fade: colours are on their way
  local badge, box = {}, {}
  for i = 0, 63 do
    local sp = SPR + i * 0x44
    local fl = emu:read16(sp + 0x3E)
    if (fl & 1) == 1 then
      local cb = emu:read32(sp + 0x1C)
      local tile = emu:read16(sp + 4) & 0x3FF
      if cb == BADGECB then badge[tile] = true
      elseif cb == 0x08007429 then
        local bar = emu:read16(sp + 0x38)
        if bar < 64 and emu:read32(SPR + bar * 0x44 + 0x1C) == 0x080728B5 then box[tile] = true end
      end
    end
  end
  for k = 0, 127 do
    local a0, a2 = emu:read16(0x07000000 + 8 * k), emu:read16(0x07000000 + 8 * k + 4)
    if (a0 >> 8) & 3 ~= 2 and (a0 & 0xFF) ~= 160 then               -- (160: an entry nothing is in)
      local tile, p = a2 & 0x3FF, a2 >> 12
      local what
      if badge[tile] then
        dispseen.badge = dispseen.badge + 1
        if ram(p, 1) ~= 0x18C6 or ram(p, 3) ~= 0x62B5 then what = "badge" end
      elseif box[tile] then
        dispseen.box = dispseen.box + 1
        if ram(p, 1) ~= 0x2529 or ram(p, 3) ~= 0x675A then what = "box" end
      end
      if what then
        dispbad[what] = dispbad[what] + 1
        if dispbad[what] <= 4 then
          w(string.format("   DRAWN %s on slot %d with %04X %04X %04X %04X (move %d %s, frame %d) | %s", what, p, ram(p, 1), ram(p, 2), ram(p, 3), ram(p, 4), move, name(move), frame, (tags())))
          if dispshots < 8 then dispshots = dispshots + 1; shot(string.format("%s_drawn_%s_%d", NAME, what, dispbad[what])) end
          -- who has that tile number, and which sprite sheet owns it (sSpriteTileRangeTags 0x030009F0, 64 tags;
          -- sSpriteTileRanges 0x03000A70, {start, count} each)
          local who = {}
          for i = 0, 63 do
            local sp = SPR + i * 0x44
            if (emu:read16(sp + 0x3E) & 1) == 1 and (emu:read16(sp + 4) & 0x3FF) == tile then
              who[#who + 1] = string.format("s%d cb %08X pal %d %s", i, emu:read32(sp + 0x1C), emu:read16(sp + 4) >> 12, (emu:read16(sp + 0x3E) & 4) ~= 0 and "hidden" or "shown")
            end
          end
          local own = {}
          for i = 0, 63 do
            local tag = emu:read16(0x030009F0 + 2 * i)
            local st, cnt = emu:read16(0x03000A70 + 4 * i), emu:read16(0x03000A72 + 4 * i)
            if tag ~= 0xFFFF and tile >= st and tile < st + cnt then own[#own + 1] = string.format("%04X %d+%d", tag, st, cnt) end
          end
          w(string.format("      OAM entry %d tile %d | sprites with that tile: %s | sheets holding it: %s", k, tile, table.concat(who, "; "), table.concat(own, "; ")))
        end
      end
    end
  end
end
-- CONFETTI=1 (debugging): the first frame of each turn a Flatter confetti sprite (callbacks 0x0815CB89 / 0x0815CC35)
-- exists, the sprite tile ranges by tag, the free tiles and the confetti sprites' tile numbers are logged
local confturn = -1
local function confetti_check()
  if not os.getenv("CONFETTI") or confturn == move then return end
  local tiles = {}
  for i = 0, 63 do
    local sp = SPR + i * 0x44
    local cb = emu:read32(sp + 0x1C)
    if (emu:read16(sp + 0x3E) & 1) == 1 and (cb == 0x0815CB89 or cb == 0x0815CC35) then tiles[#tiles + 1] = emu:read16(sp + 4) & 0x3FF end
  end
  if #tiles == 0 then return end
  confturn = move
  local own = {}
  for i = 0, 63 do
    local tag = emu:read16(0x030009F0 + 2 * i)
    if tag ~= 0xFFFF then own[#own + 1] = string.format("%04X %d+%d", tag, emu:read16(0x03000A70 + 4 * i), emu:read16(0x03000A72 + 4 * i)) end
  end
  local free = 0
  for a = 0x02021B3C, 0x02021B3C + 127 do
    local v = emu:read8(a)
    for k = 0, 7 do if (v >> k) & 1 == 0 then free = free + 1 end end
  end
  w(string.format("   CONFETTI at move %d frame %d: sprite tiles %s | free tiles %d (reserved %d) | sheets %s | %s", move, frame,
    table.concat(tiles, ","), free, emu:read16(0x02021B3A), table.concat(own, "; "), (tags())))
end
local function badges_visible()
  local n = 0
  for i = 0, 63 do
    local s = SPR + i * 0x44
    local fl = emu:read16(s + 0x3E)
    if (fl & 1) == 1 and (fl & 4) == 0 and emu:read32(s + 0x1C) == BADGECB then n = n + 1 end
  end
  return n
end
local state = {}
for b = 0, 3 do state[b] = {kind = "none", n = 0} end
local totals = {}                       -- kind -> frames
local bad = {}                          -- move -> frames of plain / wrong
local maxused, usedhist = 0, {}
local function look()
  frame = frame + 1
  local bx = boxes()
  local st = stockslot()
  local tg, used = tags()
  usedhist[used] = (usedhist[used] or 0) + 1
  if used > maxused then maxused = used; w(string.format("   tags: %d of slots 10-15 in use at move %d %s | %s", used, move, name(move), tg)) end
  badge_check()
  drawn_check()
  confetti_check()
  -- a foe's box is up: are its type badges?
  if ((bx[1] and not bx[1].hidden) or (bx[3] and not bx[3].hidden)) and badges_visible() == 0 then
    nobadge[move] = (nobadge[move] or 0) + 1
    if badgeshots < 6 and nobadge[move] == 20 then badgeshots = badgeshots + 1; shot(string.format("%s_nobadge_m%d", NAME, move)) end
  end
  for b = 0, 3 do
    local kind = "none"
    local box = bx[b]
    local slot, col = -1, 0
    if box and not box.hidden and shiny(b) and st then
      slot = box.slot
      local full = ram(st, 2) == unfaded(st, 2)
      col = ram(slot, 2)
      if slot == st then kind = full and "plain" or "plainfading"
      elseif slot >= 10 and col == GOLD then kind = "gold"
      elseif not full then kind = "fading"
      elseif state[b].slot ~= slot then kind = "gold"     -- (just moved there: palette RAM follows at the vertical blank)
      else kind = "wrong" end
    end
    state[b].slot = slot
    totals[kind] = (totals[kind] or 0) + 1
    local s = state[b]
    if kind ~= s.kind then
      if (s.kind == "plain" or s.kind == "wrong") then
        w(string.format("      battler %d: %s for %d frames (move %d %s)", b, s.kind, s.n, s.move or 0, name(s.move or 0)))
      end
      if kind == "plain" or kind == "wrong" then
        w(string.format("   f%d battler %d %s: slot %d colour %04X at move %d %s | tags %s", frame, b, kind, slot, col, move, name(move), tg))
        if shots < MAXSHOTS then shots = shots + 1; shot(string.format("%s_%03d_m%d_b%d_%s", NAME, shots, move, b, kind)) end
      end
      s.kind, s.n, s.move = kind, 0, move
    end
    s.n = s.n + 1
    if kind == "plain" or kind == "wrong" then bad[move] = (bad[move] or 0) + 1 end
  end
end
-- SCEN (the environment): nothing = the moves FIRST..LAST; "throw" = THROWS quick ball throws (R) at the action
-- menu; "levelup" = the second of your Pokemon is put one point short of its next level and the foes are left to
-- faint to MOVE (Surf by default), so the level-up flash of its healthbox runs; "bag" = into the Bag and back.
local SCEN = os.getenv("SCEN")
-- FULLHP=1: hit points held at their maximum, as the first runs had it - with that, moves that heal fail ("HP is
-- full") and their animations never play. Without it: half at the start of each turn, never below a quarter.
FULLHP = os.getenv("FULLHP") == "1"
local HOLD = tonumber(os.getenv("HOLD") or "0")          -- an item every battler holds (200 = Leftovers)
local SHINYALL = (os.getenv("SHINY") or "1") == "1"
local function upkeep()                 -- everyone shiny, nobody faints
  for b = 0, 3 do
    local m = MONS + b * 0x58
    local p = emu:read32(m + 0x48)
    if p ~= 0 and emu:read16(m) ~= 0 then
      if SHINYALL and emu:read32(m + 0x54) ~= p then emu:write32(m + 0x54, p) end
      local mx = emu:read16(m + 0x2C)
      if mx > 0 and not ((SCEN == "levelup" or LEAVING) and b % 2 == 1) then
        local hp = emu:read16(m + 0x28)
        if FULLHP then if hp ~= mx then emu:write16(m + 0x28, mx) end
        elseif hp < (mx + 3) // 4 then emu:write16(m + 0x28, (mx + 1) // 2) end
      end
    end
  end
  if SCEN == "levelup" and has(0xD709) and frame % 3 == 0 and frame < 10000000 then
    LVSHOTS = (LVSHOTS or 0) + 1
    if LVSHOTS <= 40 then shot(string.format("%s_flash_%02d", NAME, LVSHOTS)) end
  end
end
local function settle(first)            -- at the action menu: the turn's move for all, status and stages cleared
  for b = 0, 3 do
    local m = MONS + b * 0x58
    if emu:read16(m) ~= 0 then
      for k = 0, 3 do emu:write16(m + 0x0C + 2 * k, move); emu:write8(m + 0x24 + k, 20) end
      emu:write32(m + 0x4C, 0); emu:write32(m + 0x50, 0)
      for k = 0, 7 do emu:write8(m + 0x18 + k, 6) end
      if first then
        -- (the game copies hit points and the held item back from the party's data at the action menu: both
        -- are written there too - party data +0x56 hit points, +0x22 item; gBattlerPartyIndexes 0x0202406E)
        local pm = (b % 2 == 0 and 0x020244EC or 0x02024744) + 100 * emu:read16(0x0202406E + 2 * b)
        local mx = emu:read16(m + 0x2C)
        if not FULLHP and mx > 1 then emu:write16(m + 0x28, (mx + 1) // 2); emu:write16(pm + 0x56, (mx + 1) // 2) end
        if HOLD > 0 then emu:write16(m + 0x2E, HOLD); emu:write16(pm + 0x22, HOLD) end
      end
    end
  end
  if first then
    -- what would keep a move from being chosen next turn (Disable, Encore, Taunt, Torment ...: gDisableStructs)
    -- and what lingers on a battler (Leech Seed, Ingrain ...: gStatuses3)
    for a = 0x020242BC, 0x020242BC + 0x6C, 4 do emu:write32(a, 0) end
    for a = 0x020242AC, 0x020242AC + 0x0C, 4 do emu:write32(a, 0) end
  end
end
local SHOTMOVE, SHOTSTEP = tonumber(os.getenv("SHOTMOVE") or "-1"), tonumber(os.getenv("SHOTSTEP") or "5")
local sixteenths, lasthp = 0, {}          -- a sixteenth of a battler's hit points coming back (Leftovers: HOLD=200)
local function tick()
  if cb2() == BATTLE then
    upkeep(); look()
    if move == SHOTMOVE and frame % SHOTSTEP == 0 then shot(string.format("%s_m%d_f%06d", NAME, move, frame)) end
    for b = 0, 3 do
      local m = MONS + b * 0x58
      local hp, mx = emu:read16(m + 0x28), emu:read16(m + 0x2C)
      if lasthp[b] and mx >= 16 and hp == lasthp[b] + mx // 16 then sixteenths = sixteenths + 1 end
      if os.getenv("HPLOG") and lasthp[b] and hp ~= lasthp[b] then w(string.format("   hp: battler %d %d -> %d of %d (item %d) at frame %d", b, lasthp[b], hp, mx, emu:read16(m + 0x2E), frame)) end
      lasthp[b] = hp
    end
  end
  coroutine.yield()
end
local function to_battle()
  local n = 0
  while cb2() ~= BATTLE do
    n = n + 1
    if lock() ~= 0 then if n % 30 == 0 then tap(K.B) end
    else local p = n % 64; if p == 1 then tap(K.LEFT, 28) elseif p == 33 then tap(K.RIGHT, 28) end end
    if n > 60000 then w("no battle"); return false end
    coroutine.yield()
  end
  for i = 1, 3000 do if menu() then break end; if i % 30 == 0 then tap(K.A) end; tick() end
  return menu()
end
-- KIND = "single" / "double". The hack makes a wild battle a double one when the grass you stand in has
-- behaviour 0x0D and its chance function says so (0x09D4B2B0(30): RandomRange(100) < 30; the caller at 0x09D60C48
-- then makes a second wild Pokemon and sets bit 0 of gBattleTypeFlags). Its random numbers hardly change within
-- one run of the game, so asking again does not help: while no battle is on, the number that function draws is
-- set here - 0 for a double battle, 99 for a single one. A battle of the wrong kind (other grass) is left.
local WANT = os.getenv("KIND")
if WANT then
  emu:setBreakpoint(function()
    if cb2() ~= BATTLE then emu:writeRegister("r0", WANT == "double" and 0 or 99) end
  end, 0x09D4B2BA)
end
local to_battle_any = to_battle
to_battle = function()
  for try = 1, 60 do
    if not to_battle_any() then return false end
    local kind = emu:read16(MONS + 2 * 0x58) ~= 0 and "double" or "single"
    if (not WANT or WANT == kind) and not (os.getenv("LEAVEFIRST") and try == 1) then return true end
    w(string.format("   (battle %d is a %s one: leaving it)", try, kind))
    leave(kind)
    -- (the same keys on the same frames meet the same kind of battle again and again: wait a different while)
    for _ = 1, (try * 37) % 211 do coroutine.yield() end
  end
  return false
end
function leave(kind)
  do
    if kind == "single" then
      for i = 1, 900 do                                           -- Run is bottom right
        if cb2() ~= BATTLE then break end
        local q = i % 90
        if menu() then if q == 1 then tap(K.DOWN) elseif q == 20 then tap(K.RIGHT) elseif q == 40 then tap(K.A) end
        elseif q % 30 == 0 then tap(K.A) end
        coroutine.yield()
      end
    else                                                          -- (Run does not get you out of a wild double battle:
      LEAVING = true                                              -- the foes are left to faint to Surf)
      for i = 1, 6000 do
        if cb2() ~= BATTLE then break end
        if i % 30 == 1 then
          for b = 0, 2, 2 do
            local m = MONS + b * 0x58
            for k = 0, 3 do emu:write16(m + 0x0C + 2 * k, 57); emu:write8(m + 0x24 + k, 20) end
          end
        end
        if i % 10 == 0 then tap(K.A) end
        upkeep()
        coroutine.yield()
      end
      LEAVING = false
    end
    for i = 1, 1800 do if cb2() == OVERWORLD and lock() == 0 then break end; if i % 20 == 0 then tap(K.A) elseif i % 20 == 10 then tap(K.B) end; coroutine.yield() end
  end
end
local at = 0
local function next_move()
  if LIST then
    at = at + 1
    if at > #LIST then return false end
    move = LIST[at]
    return true
  end
  move = move + 1
  while move <= LAST do
    local nm = string.lower(name(move))
    if nm ~= "" and nm ~= "-" and not SKIP[nm] then return true end
    move = move + 1
  end
  return false
end
local co = coroutine.create(function()
  run({0x39, 0, 17, 0xFF, 9, 0, 6, 0, 0x02}); wait(390)              -- Route 102
  tap(K.UP, 24); wait(90)
  for i = 1, 900 do if lock() == 0 then break end; if i % 30 == 0 then tap(K.B) end; coroutine.yield() end
  if not to_battle() then done(); return end
  local double = emu:read16(MONS + 2 * 0x58) ~= 0
  w(string.format("in battle (%s); tags %s", double and "double" or "single", (tags())))
  move = FIRST - 1
  local stuck = 0
  if SCEN == "throw" then
    if os.getenv("PREMOVE") then                                   -- a move first (one that takes every slot)
      move = tonumber(os.getenv("PREMOVE"))
      settle(true)
      local n, left = 0, false
      while n < 6000 do
        n = n + 1
        if cb2() ~= BATTLE then break end
        if menu(0) then if left and n > 60 then break end elseif not menu(2) then left = true end
        if n % 10 == 0 then tap(K.A) end
        tick()
      end
      w(string.format("   after %s: tags %s", name(move), (tags())))
    end
    move = LAST
    for throw = 1, tonumber(os.getenv("THROWS") or "4") do
      if cb2() ~= BATTLE then w("   the battle ended before throw " .. throw); break end
      tap(K.R)
      local n = 0
      while n < 3000 do
        n = n + 1
        if cb2() ~= BATTLE then break end
        if n > 90 and menu(0) then break end
        if n > 30 and n % 14 == 0 and not menu(0) then tap(K.A) end
        if n % 25 == 0 and n <= 400 then shot(string.format("%s_throw%d_%03d", NAME, throw, n)) end
        tick()
      end
      w(string.format("   throw %d: %d frames; tags now %s", throw, n, (tags())))
    end
  elseif SCEN == "levelup" then
    local slot = emu:read16(0x0202406E + 2 * 2)                     -- gBattlerPartyIndexes[2]
    local mon = 0x020244EC + 100 * slot
    local bm = MONS + 2 * 0x58
    local exp, level, species = emu:read32(bm + 0x44), emu:read8(bm + 0x2A), emu:read16(bm)
    local at
    for k = 0, 96, 4 do if emu:read32(mon + k) == exp then at = k end end
    local growth = emu:read8(emu:read32(0x080001BC) + species * 28 + 0x13)
    local nxt = emu:read32(0x0831F72C + growth * 404 + (level + 1) * 4)
    w(string.format("   battler 2: party slot %d, species %d, level %d, exp %d (at +0x%X of its data), growth %d, next level at %d",
      slot, species, level, exp, at or -1, growth, nxt))
    if at and level < 100 and nxt > exp then
      emu:write32(mon + at, nxt - 1)
      move = tonumber(os.getenv("MOVE") or "57")
      for turn = 1, 3 do
        if cb2() ~= BATTLE then break end
        settle()
        local n, left = 0, false
        while n < 6000 do
          n = n + 1
          if cb2() ~= BATTLE then break end
          if menu(0) then if left and n > 60 then break end elseif not menu(2) then left = true end
          if n % 10 == 0 then tap(K.A) end
          tick()
        end
        w(string.format("   turn %d: %d frames; battler 2 is level %d now; tags %s", turn, n, emu:read8(bm + 0x2A), (tags())))
      end
    else
      w("   could not set the level-up up")
    end
    move = LAST
  elseif SCEN == "switch" then
    -- a move first (MOVE: one whose animation needs every palette slot, so that the idle ball graphics are let
    -- go), then the first Pokemon is taken back and another sent out: its ball has to be loaded again
    move = tonumber(os.getenv("MOVE") or "392")
    settle(true)
    local n, left = 0, false
    while n < 6000 do
      n = n + 1
      if cb2() ~= BATTLE then break end
      if menu(0) then if left and n > 60 then break end elseif not menu(2) then left = true end
      if n % 10 == 0 then tap(K.A) end
      tick()
    end
    w(string.format("   after %s: tags %s", name(move), (tags())))
    tap(K.DOWN); for _ = 1, 20 do tick() end
    shot(NAME .. "_sw_1_cursor")
    tap(K.A)
    n = 0
    while cb2() == BATTLE and n < 600 do n = n + 1; tick() end
    for _ = 1, 100 do tick() end
    shot(NAME .. "_sw_2_party")
    for _ = 1, tonumber(os.getenv("DOWNS") or "4") do tap(K.DOWN); for _ = 1, 16 do tick() end end   -- (the save's fifth: Rayquaza)
    shot(NAME .. "_sw_3_chosen")
    tap(K.A); for _ = 1, 30 do tick() end
    shot(NAME .. "_sw_4_menu")
    tap(K.A)
    n = 0
    local k = 0
    while n < 2400 do
      n = n + 1
      if cb2() == BATTLE then
        k = k + 1
        if k % 4 == 0 and k <= 800 then shot(string.format("%s_sw_b%04d", NAME, k)) end
        if k > 200 and (menu(0) or menu(2)) then break end
        if k % 14 == 0 then tap(K.A) end
      elseif n % 30 == 0 then tap(K.A) end
      tick()
    end
    w(string.format("   after the switch: %d battle frames; tags %s", k, (tags())))
    move = LAST
  elseif SCEN == "keys" then
    -- KEYS="RIGHT,A,wait60,DOWN,A": the keys pressed one after another from the action menu, a picture after each
    -- (to find the way through a menu), then A until the action menu is back, with pictures on the way
    move = LAST
    local step = 0
    for key in (os.getenv("KEYS") or ""):gmatch("[^,]+") do
      step = step + 1
      local wt = key:match("^wait(%d+)$")
      if wt then for _ = 1, tonumber(wt) do tick() end
      else tap(K[key]); for _ = 1, 24 do tick() end end
      shot(string.format("%s_key%02d_%s", NAME, step, key))
      w(string.format("   key %d %s: cb2 %08X tags %s", step, key, cb2(), (tags())))
    end
    local k = 0
    for n = 1, tonumber(os.getenv("AFTER") or "900") do
      if cb2() == BATTLE then
        k = k + 1
        if k % 6 == 0 and k <= 900 then shot(string.format("%s_after_%04d", NAME, k)) end
        if k > 120 and (menu(0) or menu(2)) then break end
        if k % 14 == 0 then tap(K.A) end
      elseif n % 30 == 0 then tap(K.A) end
      tick()
    end
    w(string.format("   after the keys: %d battle frames; tags %s", k, (tags())))
  elseif SCEN == "bag" then
    move = LAST
    for round = 1, 2 do
      tap(K.RIGHT); for _ = 1, 20 do tick() end
      tap(K.A)
      local n = 0
      while cb2() == BATTLE and n < 600 do n = n + 1; tick() end
      for _ = 1, 120 do tick() end
      w(string.format("   in the Bag: cb2 %08X", cb2()))
      tap(K.B)
      n = 0
      while not (cb2() == BATTLE and menu(0)) and n < 900 do n = n + 1; tick() end
      for i = 1, 60 do tick(); if i == 50 then shot(string.format("%s_back_%d", NAME, round)) end end
      tap(K.LEFT); for _ = 1, 20 do tick() end
      w(string.format("   back from the Bag (round %d); tags %s", round, (tags())))
    end
  end
  local played = 0
  while next_move() do
    played = played + 1
    local planned = false
    if FRESH > 0 and played > 1 and (played - 1) % FRESH == 0 and cb2() == BATTLE then
      leave(emu:read16(MONS + 2 * 0x58) ~= 0 and "double" or "single")
      planned = true
    end
    if cb2() ~= BATTLE then
      if not planned then w(string.format("   battle over before move %d %s (cb2 %08X)", move, name(move), cb2())) end
      for i = 1, 1200 do if cb2() == OVERWORLD and lock() == 0 then break end; if i % 20 == 0 then tap(K.B) end; coroutine.yield() end
      if not to_battle() then break end
    end
    -- a turn: from the first battler's action menu until it is there again after having left it
    settle(true)
    local n, left, back = 0, false, false
    while n < 4000 do
      n = n + 1
      if cb2() ~= BATTLE then
        if cb2() == OVERWORLD then break end
        if n % 20 == 0 then tap(K.B) end
      else
        if menu(0) then
          if left and n > 60 then back = true; break end
        elseif not menu(2) then left = true end
        if n % 10 == 0 then tap(K.A) end
        if n % 30 == 15 then settle() end                           -- (the second battler's menu reads them later)
      end
      tick()
    end
    if not back and cb2() == BATTLE then
      stuck = stuck + 1
      w(string.format("   STUCK at move %d %s", move, name(move)))
      shot(string.format("%s_stuck_%d", NAME, move))
      for i = 1, 600 do if menu(0) then break end; if i % 12 == 0 then tap(K.B) end; tick() end
      if stuck > 25 then w("too many stuck turns"); break end
    end
  end
  for b = 0, 3 do local s = state[b]; if s.kind == "plain" or s.kind == "wrong" then w(string.format("      battler %d: %s for %d frames (move %d)", b, s.kind, s.n, s.move or 0)) end end
  local t = {}
  for k, v in pairs(totals) do t[#t + 1] = k .. " " .. v end
  table.sort(t)
  w("frames by kind: " .. table.concat(t, ", "))
  local u = {}
  for k = 0, 6 do u[#u + 1] = string.format("%d used: %d", k, usedhist[k] or 0) end
  w("slots 10-15 in use, frames: " .. table.concat(u, ", "))
  local list = {}
  for m, n in pairs(bad) do list[#list + 1] = {m, n} end
  table.sort(list, function(a, b) return a[1] < b[1] end)
  local nb, total = {}, 0
  for m, n in pairs(nobadge) do nb[#nb + 1] = {m, n}; total = total + n end
  table.sort(nb, function(a, b) return a[1] < b[1] end)
  w(string.format("moves with the type badges hidden while a foe's box is up: %d (%d frames)", #nb, total))
  local line = {}
  for _, e in ipairs(nb) do line[#line + 1] = string.format("%d %s %d", e[1], name(e[1]), e[2]) end
  w("   " .. table.concat(line, ", "))
  local fl = {}
  for m, n in pairs(fails) do fl[#fl + 1] = string.format("%d %s x%d", m, name(m), n) end
  table.sort(fl)
  w(string.format("palette requests that found no slot at all: %d of %d calls%s", nfail, calls, #fl > 0 and (": " .. table.concat(fl, ", ")) or ""))
  w(string.format("frames with a visible type badge on a slot that is not its palette's: %d", badgewrong))
  w(string.format("drawn in colours that are not their own: type badges %d of %d looked at, healthboxes %d of %d", dispbad.badge, dispseen.badge, dispbad.box, dispseen.box))
  if HOLD > 0 then w(string.format("times a battler got a sixteenth of its hit points back (item %d held): %d", HOLD, sixteenths)) end
  w(string.format("moves with a plain or wrong box: %d", #list))
  for _, e in ipairs(list) do w(string.format("   %4d %-13s %d frames", e[1], name(e[1]), e[2])) end
  for _, e in ipairs(watch) do w(string.format("watch: %08X-%08X (%d bytes) read %d times", e.lo, e.hi, e.hi - e.lo, e.n)) end
  w("SWEEP DONE")
  done()
end)
function TEST(f)
  if coroutine.status(co) == "dead" then return end
  local ok, err = coroutine.resume(co)
  if not ok then w("error: " .. tostring(err)); done() end
end
