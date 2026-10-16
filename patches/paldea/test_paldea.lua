-- Area Zero, walked: warp next to a place, then walk (routes found on the live map, walk.lua), face, press A and
-- mash A until the field is ours again. Every scene's end goes to paldea_log.txt with the map, the position, the
-- stage var and the flags; screenshots every SHOT frames while a scene runs and at each "shot" step.
-- env: PALDEA_DIR (output folder, with the slash), PALDEA_HERE (this folder), STEPSFILE (default test_steps.lua)
NAME = "paldea"
DIR = os.getenv("PALDEA_DIR") or "./"
HERE = os.getenv("PALDEA_HERE") or "./"
BOOT_QUIET_FIELD = true                                     -- (a save made in Area Zero reads its map again)
dofile(HERE .. "../dexnavchain/test_boot.lua")
dofile(HERE .. (os.getenv("STEPSFILE") or "test_steps.lua"))
dofile(HERE .. "walk.lua")
local SHOT = tonumber(os.getenv("SHOT") or "60")
local SCRIPT = 0x0203F100
local STAGE = 0x40A8
local FLAGS = {0x41D5, 0x43AB, 0x43AC, 0x43AD}
-- Area Zero's story flags (story.py), cleared by {"setup", fresh = true}
local STORY_FLAGS = {}
for f = 0x43AC, 0x43BE do STORY_FLAGS[#STORY_FLAGS + 1] = f end
for f = 0x43C0, 0x43DD do STORY_FLAGS[#STORY_FLAGS + 1] = f end      -- (0x43D8-0x43DD: the vault, the item balls)
STORY_FLAGS[#STORY_FLAGS + 1] = 0x43E2                               -- (Jacq met before the hole opened)
local function sb1() return emu:read32(0x03005D8C) end
local function sb2() return emu:read32(0x03005D90) end
local function flagbyte(f)
  if f < 0x4000 then return sb1() + 0x1270 + (f >> 3) end
  local i = (f - 0x4000) >> 3
  if i <= 0x33 then return sb1() + 0x988 + i end
  if i <= 0x67 then return sb1() + 0x3B24 + i - 0x34 end
  if i <= 0x9B then return sb2() + 0x5C + i - 0x68 end
  return sb2() + 0x28 + i - 0x9C
end
local function setflag(f, on)
  local a = flagbyte(f); local b = emu:read8(a)
  if on then b = b | (1 << (f & 7)) else b = b & ~(1 << (f & 7)) & 0xFF end
  emu:write8(a, b)
end
local function flag(f) return (emu:read8(flagbyte(f)) >> (f & 7)) & 1 end
local function var(v) return emu:read16(sb1() + 0x139C + (v - 0x4000) * 2) end
local function setvar(v, x) emu:write16(sb1() + 0x139C + (v - 0x4000) * 2, x) end
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1); emu:write8(0x03000E38, 0)
end
local function mapid() return emu:read8(sb1() + 4) * 1000 + emu:read8(sb1() + 5) end
local function objs()
  local t = {}
  for k = 0, 15 do
    local o = 0x02037350 + k * 0x24
    if emu:read8(o) & 1 == 1 then
      t[#t + 1] = string.format("%d:g%d@%d,%d%s", emu:read8(o + 8), emu:read8(o + 5), emu:read16(o + 0x10) - 7,
        emu:read16(o + 0x12) - 7, (emu:read8(o + 1) & 0x20 ~= 0) and "i" or "")
    end
  end
  return table.concat(t, " ")
end
local function active(id)                                   -- is the map's object with this local id on the map?
  for k = 1, 15 do
    local o = 0x02037350 + k * 0x24
    if emu:read8(o) & 1 == 1 and emu:read8(o + 8) == id then return true end
  end
  return false
end
local function where(id)                                    -- the tile of the map's object with this local id
  for k = 0, 15 do                                          -- (255: you)
    local o = 0x02037350 + k * 0x24
    if emu:read8(o) & 1 == 1 and emu:read8(o + 8) == id then return emu:read16(o + 0x10) - 7, emu:read16(o + 0x12) - 7 end
  end
end
local function template(id)                                 -- where the map places its object with this local id,
  for k = 0, 63 do                                          -- and its hide flag (the saved templates): x, y, flag
    local o = sb1() + 0xC70 + k * 24
    if emu:read8(o) == id then return emu:read16(o + 4), emu:read16(o + 6), emu:read16(o + 20) end
  end
end
local function who(x, y)                                    -- the local id of what stands on a tile (not you)
  for k = 1, 15 do
    local o = 0x02037350 + k * 0x24
    if emu:read8(o) & 1 == 1 and emu:read16(o + 0x10) - 7 == x and emu:read16(o + 0x12) - 7 == y then return emu:read8(o + 8) end
  end
end
local function state()
  local fl = {}
  for _, f in ipairs(FLAGS) do fl[#fl + 1] = string.format("%04X=%d", f, flag(f)) end
  local pl = 0x02037350
  return string.format("map %d/%d (%d,%d) stage %d %s", emu:read8(sb1() + 4), emu:read8(sb1() + 5),
    emu:read16(pl + 0x10) - 7, emu:read16(pl + 0x12) - 7, var(STAGE), table.concat(fl, " "))
end

local KEYS = {UP = K.UP, DOWN = K.DOWN, LEFT = K.LEFT, RIGHT = K.RIGHT}
local i, t0, calm = 1, nil, 0

-- a text of the game as letters (for the log): A-Z, a-z, 0-9, space; FE a new line; anything else <hex>
local function gtext(a, n)
  local t = {}
  for k = 0, (n or 120) - 1 do
    local c = emu:read8(a + k)
    if c == 0xFF then break end
    if c >= 0xBB and c <= 0xD4 then t[#t + 1] = string.char(65 + c - 0xBB)
    elseif c >= 0xD5 and c <= 0xEE then t[#t + 1] = string.char(97 + c - 0xD5)
    elseif c >= 0xA1 and c <= 0xAA then t[#t + 1] = string.char(48 + c - 0xA1)
    elseif c == 0x00 then t[#t + 1] = " "
    elseif c == 0xFE or c == 0xFA or c == 0xFB then t[#t + 1] = " / "
    elseif c == 0xAD then t[#t + 1] = "."
    elseif c == 0xB8 then t[#t + 1] = ","
    elseif c == 0xAB then t[#t + 1] = "!"
    else t[#t + 1] = string.format("<%02X>", c) end
  end
  return table.concat(t)
end
-- the roaming Pokemon: SaveBlock1 + 0x31DC (species +8, hp +0xA, level +0xC, active +0x13) and where it is, which
-- is not in the save: sRoamerLocation 0x0203BC86 (map group, map number)
local function roamer()
  local r = sb1() + 0x31DC
  local g, n = emu:read8(0x0203BC86), emu:read8(0x0203BC87)
  local sec = "?"
  local hdr = emu:read32(emu:read32(0x08A54698 + 4 * g) + 4 * n)
  if hdr >= 0x08000000 and hdr < 0x0A000000 then sec = tostring(emu:read8(hdr + 0x14)) end
  return string.format("active %d species %d level %d hp %d | at %d/%d (map section %s)", emu:read8(r + 0x13),
    emu:read16(r + 8), emu:read8(r + 0xC), emu:read16(r + 0xA), g, n, sec), emu:read8(r + 0x13), emu:read16(r + 8), g, n
end

-- PALWATCH=1: every frame, every sprite in use that draws with an object palette slot (4-10): the tag that slot
-- held when the sprite was first seen with it. If the slot's tag changes while the same sprite (same callback,
-- same data[0], same object event's local id) still draws with it, the sprite now shows another kind's colours:
-- logged (objpal.py: the hack's allocator did that to the seventh kind of thing on a map and after).
-- And every 8 frames: does the slot hold its tag's colours at all? The colours a palette was loaded with
-- (gPlttBufferUnfaded, 0x02037714, sprites from +0x200) against that tag's row of the field's palette table (its
-- address is the literal at 0x0808E8BC). The hack's slot 10 held the red crystal's while Walking Wake, its tag
-- there, stood in it: the tag never changed, the colours did.
local PALWATCH = os.getenv("PALWATCH") == "1"
local pw_seen, pw_bad, pw_wrong, pw_said = {}, 0, 0, {}
local pw_pal = nil
local function pw_palette(tag)                             -- the ROM address of a tag's 16 colours, or nil
  if not pw_pal then
    pw_pal = {}
    local t = emu:read32(0x0808E8BC)
    for k = 0, 400 do
      local row = t + 8 * k
      local tg = emu:read16(row + 4)
      if tg == 0x11FF then break end                         -- (the game's search stops there only: the copy
      if tg ~= 0 then pw_pal[tg] = pw_pal[tg] or emu:read32(row) end   -- keeps vanilla's old zero row, 35, inside)
    end
  end
  return pw_pal[tag]
end
local pw_miss, pw_runs, pw_faded, pw_looked = {}, 0, 0, 0
local function pw_colours(f)
  -- a fade or the weather's tint changes what is shown from what was loaded: only while the player's slot (0)
  -- shows what it was loaded with is a slot that shows something else wrong; and it must stay wrong for two looks
  local UNF, FAD = 0x02037714 + 0x200, 0x02037B14 + 0x200
  pw_runs = pw_runs + 1
  for c = 1, 15 do
    if emu:read16(FAD + 2 * c) ~= emu:read16(UNF + 2 * c) then pw_faded = pw_faded + 1; return end
  end
  for id = 0, 63 do
    local sp = 0x02020630 + id * 0x44
    if emu:read8(sp + 0x3E) & 1 == 1 then
      local pal = emu:read16(sp + 4) >> 12
      local tag = (pal >= 4 and pal <= 10) and emu:read16(0x03000CF0 + 2 * pal) or 0xFFFF
      local src = tag ~= 0xFFFF and pw_palette(tag)
      local key = string.format("%d/%d/%04X", id, pal, tag)
      if src then
        pw_looked = pw_looked + 1
        local loaded, shown = true, true
        for c = 1, 15 do
          local want = emu:read16(src + 2 * c)
          if emu:read16(UNF + 32 * pal + 2 * c) ~= want then loaded = false end
          if emu:read16(FAD + 32 * pal + 2 * c) ~= want then shown = false end
        end
        if loaded and shown then
          pw_miss[key] = nil
        else
          pw_miss[key] = (pw_miss[key] or 0) + 1
          if pw_miss[key] == 2 and not pw_said[key] then
            pw_said[key] = true
            pw_wrong = pw_wrong + 1
            if pw_wrong <= 30 then
              w(string.format("PALWATCH sprite %d draws with slot %d, its tag %04X, but the slot %s that tag's colours (frame %d) | %s",
                id, pal, tag, loaded and "was loaded with, yet does not show," or "does not hold", f, state()))
            end
          end
        end
      end
    end
  end
end
local function palwatch(f)
  if f % 8 == 0 then pw_colours(f) end
  for id = 0, 63 do
    local sp = 0x02020630 + id * 0x44
    if emu:read8(sp + 0x3E) & 1 == 0 then
      pw_seen[id] = nil
    else
      local pal = emu:read16(sp + 4) >> 12
      if pal < 4 or pal > 10 then
        pw_seen[id] = nil
      else
        local d0 = emu:read16(sp + 0x2E)
        local who = string.format("%08X/%d/%d", emu:read32(sp + 0x1C), d0, d0 < 16 and emu:read8(0x02037350 + d0 * 0x24 + 8) or 0)
        local tag = emu:read16(0x03000CF0 + 2 * pal)
        local r = pw_seen[id]
        if not r or r.pal ~= pal or r.who ~= who then
          pw_seen[id] = {pal = pal, tag = tag, who = who}
        elseif r.tag ~= tag then
          pw_bad = pw_bad + 1
          if pw_bad <= 30 then
            w(string.format("PALWATCH sprite %d (%s) draws with slot %d, which held %04X when it was first seen and holds %04X now (frame %d) | %s",
              id, who, pal, r.tag, tag, f, state()))
          end
          r.tag = tag
        end
      end
    end
  end
end

-- TILEWATCH=1: the map's tile pictures in video memory (0x06000000..0x06008000: 1,024 cells of 32 bytes, the
-- two tilesets) against a copy taken once the field has been yours for 90 frames on a map; taken again after
-- anything else had the screen (a battle, a menu) or the map changed. Every 60 frames: how many cells differ. A
-- tileset's own animations change a few dozen; more than TILEWATCH_MANY (default 150) is logged with a picture,
-- the first time and whenever the count grows by another 100. (A player's report: the ground of a Hisui map
-- turned to stripes until the next battle.)
local TILEWATCH = os.getenv("TILEWATCH") == "1"
local TW_MANY = tonumber(os.getenv("TILEWATCH_MANY") or "150")
local tw = {ref = nil, map = nil, calm = 0, said = 0, shots = 0}
local function tilewatch(f)
  if cb2() ~= OVERWORLD then tw.ref, tw.calm, tw.said = nil, 0, 0; return end
  if lock() ~= 0 then tw.calm = 0; return end
  if tw.map ~= mapid() then tw.map, tw.ref, tw.calm, tw.said = mapid(), nil, 0, 0 end
  tw.calm = tw.calm + 1
  if not tw.ref then
    if tw.calm >= 90 then tw.ref = emu:readRange(0x06000000, 0x8000) end
    return
  end
  if f % 60 ~= 0 then return end
  local now = emu:readRange(0x06000000, 0x8000)
  if now == tw.ref then return end
  local n, first, last = 0, nil, nil
  for t = 0, 1023 do
    if now:sub(t * 32 + 1, t * 32 + 32) ~= tw.ref:sub(t * 32 + 1, t * 32 + 32) then
      n = n + 1; first = first or t; last = t
    end
  end
  if n > TW_MANY and n >= tw.said + 100 then
    tw.said = n
    tw.shots = tw.shots + 1
    if tw.shots <= 12 then shot(string.format("tilewatch_%02d_f%d", tw.shots, f)) end
    w(string.format("TILEWATCH %d of the 1024 tile cells differ from when the map came up (cells %d..%d) at frame %d | %s",
      n, first, last, f, state()))
  end
end

-- SPRWATCH=1: every 4 frames, the picture cells each sprite in use owns in sprite memory (1,024 cells from
-- 0x06010000; a sprite that is not drawn from a sheet owns width x height / 64 cells from its OAM tile number):
-- two sprites on the same cells, or one that runs past cell 1023 (what is written there wraps round: onto the
-- first sprites on a GBA, somewhere else on an emulator that mirrors video memory otherwise). Logged once per pair.
local SPRWATCH = os.getenv("SPRWATCH") == "1"
local sw_said, sw_n = {}, 0
local SPR_DIM = {[0] = {{8, 8}, {16, 16}, {32, 32}, {64, 64}}, [1] = {{16, 8}, {32, 8}, {32, 16}, {64, 32}},
                 [2] = {{8, 16}, {8, 32}, {16, 32}, {32, 64}}}
local function sprwatch(f)
  if f % 4 ~= 0 or cb2() ~= OVERWORLD then return end
  local own = {}
  for id = 0, 63 do
    local sp = 0x02020630 + id * 0x44
    if emu:read16(sp + 0x3E) & 1 == 1 and emu:read8(sp + 0x3F) & 0x40 == 0 then     -- in use, not from a sheet
      local a0, a1, a2 = emu:read16(sp), emu:read16(sp + 2), emu:read16(sp + 4)
      local d = (SPR_DIM[a0 >> 14] or SPR_DIM[0])[(a1 >> 14) + 1]
      local first, n = a2 & 0x3FF, d[1] * d[2] // 64
      local cb = emu:read32(sp + 0x1C)
      if first + n > 1024 then
        local key = "end/" .. id .. "/" .. cb
        if not sw_said[key] then
          sw_said[key] = true; sw_n = sw_n + 1
          w(string.format("SPRWATCH sprite %d (callback %08X, pictures %08X, %dx%d) owns cells %d..%d: past the end of sprite memory (frame %d) | %s",
            id, cb, emu:read32(sp + 0x0C), d[1], d[2], first, first + n - 1, f, state()))
          if sw_n <= 6 then shot(string.format("sprwatch_%02d_f%d", sw_n, f)) end
        end
      end
      for t = first, math.min(first + n - 1, 1023) do
        local o = own[t]
        if o and o ~= id then
          local key = "pair/" .. math.min(o, id) .. "/" .. math.max(o, id) .. "/" .. cb
          if not sw_said[key] then
            sw_said[key] = true; sw_n = sw_n + 1
            w(string.format("SPRWATCH sprites %d and %d both own cell %d (sprite %d: callback %08X, pictures %08X, cells %d..%d) (frame %d) | %s",
              o, id, t, id, cb, emu:read32(sp + 0x0C), first, first + n - 1, f, state()))
            if sw_n <= 6 then shot(string.format("sprwatch_%02d_f%d", sw_n, f)) end
          end
          break
        end
        own[t] = id
      end
    end
  end
end

-- BIGWRITE=1: every frame on the field, video memory (96 KB) and EWRAM (256 KB) in 4 KB blocks
-- against the frame before: BIGWRITE_MANY blocks (default 6) of one of them changed in a single frame is logged,
-- with the blocks and the first words now in the first of them. (mGBA's own log shows the game copying 0xB000
-- bytes out of an address where there is no memory, 0x22BB0000: this finds where that copy lands.)
local BIGWRITE = os.getenv("BIGWRITE") == "1"
local BW_MANY = tonumber(os.getenv("BIGWRITE_MANY") or "6")
local bw = {prev = {}, n = 0}
local BW_AREAS = {{"VRAM", 0x06000000, 0x18000}, {"EWRAM", 0x02000000, 0x40000}}     -- (IWRAM is 8 blocks: the stack alone moves most of them)
local function bigwrite(f)
  local field = cb2() == OVERWORLD
  for _, a in ipairs(BW_AREAS) do
    local now = emu:readRange(a[2], a[3])
    local was = bw.prev[a[1]]
    if was and field and bw.field and now ~= was then
      local changed = {}
      for b = 0, a[3] // 0x1000 - 1 do
        if now:sub(b * 0x1000 + 1, (b + 1) * 0x1000) ~= was:sub(b * 0x1000 + 1, (b + 1) * 0x1000) then changed[#changed + 1] = b end
      end
      if #changed >= BW_MANY then
        bw.n = bw.n + 1
        local b0 = changed[1]
        local words = {}
        for k = 0, 7 do words[#words + 1] = string.format("%04X", emu:read16(a[2] + b0 * 0x1000 + 2 * k)) end
        if bw.n <= 40 then
          w(string.format("BIGWRITE %s: %d blocks of 4 KB changed in one frame, %08X..%08X; now at %08X: %s (frame %d, lock %d) | %s",
            a[1], #changed, a[2] + b0 * 0x1000, a[2] + (changed[#changed] + 1) * 0x1000 - 1, a[2] + b0 * 0x1000,
            table.concat(words, " "), f, lock(), state()))
          shot(string.format("bigwrite_%02d_f%d", bw.n, f))
        end
      end
    end
    bw.prev[a[1]] = now
  end
  bw.field = field
end

-- WATCHADDR="r:22BB0000" (or w: / rw:, several with commas): a watchpoint on those two bytes; each of the first
-- WATCHADDR_MAX hits (default 6) is logged with the registers, the top of the stack and where you are. (This
-- build's breakpoints and watchpoints do call back: measured 2026-10-11, _testrun/tornadus/wp.)
local wa = {n = 0, max = tonumber(os.getenv("WATCHADDR_MAX") or "6"), frame = 0}
for kind, hex in (os.getenv("WATCHADDR") or ""):gmatch("(%a+):(%x+)") do
  local a = tonumber(hex, 16)
  local ty = ({r = C.WATCHPOINT_TYPE.READ, w = C.WATCHPOINT_TYPE.WRITE, rw = C.WATCHPOINT_TYPE.RW})[kind]
  emu:setRangeWatchpoint(function()
    wa.n = wa.n + 1
    if wa.frame ~= wa.last then
      wa.last, wa.events, wa.pending = wa.frame, (wa.events or 0) + 1, true
      -- a new event: every sprite in use with what its animation is at (the game copies a sprite's picture for
      -- a frame from images[frame number] = {address, size}: a frame number past the table copies anything)
      if wa.events <= 8 then
        local owner = {}
        for k = 0, 15 do
          local o = 0x02037350 + k * 0x24
          if emu:read8(o) & 1 == 1 then
            owner[emu:read8(o + 4)] = string.format("obj %d (local %d, gfx %d) at %d,%d", k, emu:read8(o + 8), emu:read8(o + 5),
              emu:read16(o + 0x10) - 7, emu:read16(o + 0x12) - 7)
          end
        end
        for id = 0, 63 do
          local sp = 0x02020630 + id * 0x44
          local fl = emu:read16(sp + 0x3E)
          if fl & 1 == 1 then
            local anims, images, num, cmd = emu:read32(sp + 8), emu:read32(sp + 0x0C), emu:read8(sp + 0x2A), emu:read8(sp + 0x2B)
            local frame, img = "?", "?"
            if anims >= 0x08000000 and anims < 0x0A000000 then
              local list = emu:read32(anims + 4 * num)
              if list >= 0x08000000 and list < 0x0A000000 then
                local c = emu:read32(list + 4 * cmd)
                frame = string.format("%d", c & 0xFFFF)
                if images >= 0x08000000 and images < 0x0A000000 and (c & 0xFFFF) < 0x8000 then
                  img = string.format("%08X size %04X", emu:read32(images + 8 * (c & 0xFFFF)), emu:read16(images + 8 * (c & 0xFFFF) + 4))
                end
              end
            end
            w(string.format("   WATCHADDR event %d: s%-2d tile %4d sheet %s | cb %08X template %08X anims %08X images %08X | anim %d cmd %d: frame %s -> %s | %s",
              wa.events, id, emu:read16(sp + 4) & 0x3FF, (emu:read8(sp + 0x3F) & 0x40 ~= 0) and "yes" or "no ",
              emu:read32(sp + 0x1C), emu:read32(sp + 0x14), anims, images, num, cmd, frame, img, owner[id] or ""))
          end
        end
      end
    end
    if wa.n > wa.max then return end
    local r = {}
    for k = 0, 12 do r[#r + 1] = string.format("r%d %08X", k, emu:readRegister("r" .. k)) end
    local sp = emu:readRegister("sp")
    local st = {}
    for k = 0, 23 do st[#st + 1] = string.format("%08X", emu:read32(sp + 4 * k)) end
    w(string.format("WATCHADDR %s:%08X hit %d at frame %d: pc %08X lr %08X sp %08X cpsr %08X | %s | stack %s | %s",
      kind, a, wa.n, wa.frame, emu:readRegister("pc"), emu:readRegister("lr"), sp, emu:readRegister("cpsr"),
      table.concat(r, " "), table.concat(st, " "), state()))
  end, a, a + 2, ty)
end

-- BADCOPY=1: a breakpoint on the game's ProcessSpriteCopyRequests where it calls CpuSet (0x08007458: r0 the
-- picture's address, r1 where in sprite memory, r2 its size in halfwords). A sprite's animation frame n is copied
-- from images[n] = {address, size}; a table with fewer pictures than its animations ask for hands over whatever
-- lies after it. Logged: every copy whose address is not in ROM or RAM, or that is longer than 0x1000 bytes, or
-- that runs past the end of sprite memory (0x06018000); the kinds are counted for the end of the run.
-- On a ROM with patches/sprframe the copy is made in its guard instead: BADCOPY_AT=<the address the patcher prints
-- as "the copy itself"> counts the copies that are made, and BADCOPY_IN=<the guard's address> the bad ones that
-- are asked for (there r2 is the request, its size at +8) - none of which may be made.
local BADCOPY = os.getenv("BADCOPY") == "1"
local bc = {n = 0, kinds = {}, order = {}, frame = 0, all = 0, asked = 0, akinds = {}, aorder = {}}
local function bc_bad(src, dst, bytes)
  local reg = src >> 24
  return (reg ~= 2 and reg ~= 3 and reg ~= 8 and reg ~= 9) or bytes == 0 or bytes > 0x1000 or dst + bytes > 0x06018000
end
if BADCOPY then
  emu:setBreakpoint(function()
    local src, dst, bytes = emu:readRegister("r0"), emu:readRegister("r1"), emu:readRegister("r2") * 2
    bc.all = bc.all + 1
    if not bc_bad(src, dst, bytes) then
      bc.sizes = bc.sizes or {}                              -- the good ones: how many of each size, from where
      local k = string.format("%04X bytes from %02X......", bytes, src >> 24)
      bc.sizes[k] = (bc.sizes[k] or 0) + 1
      return
    end
    local key = string.format("from %08X, %5d bytes", src & 0xFFFFFFFF, bytes)
    if not bc.kinds[key] then bc.kinds[key] = 0; bc.order[#bc.order + 1] = key end
    bc.kinds[key] = bc.kinds[key] + 1
    bc.n = bc.n + 1
    -- the first of each kind: video memory as it is now, to see at the next frame what the BIOS made of it
    if bc.kinds[key] == 1 and not bc.probe then bc.probe = {key = key, was = emu:readRange(0x06000000, 0x18000)} end
    if bc.n <= 12 then
      w(string.format("BADCOPY %d at frame %d: %s to %08X (sprite cell %d), ends at %08X | %s | objs %s", bc.n, bc.frame, key, dst,
        (dst - 0x06010000) // 32, dst + bytes, state(), objs()))
    end
  end, tonumber(os.getenv("BADCOPY_AT") or "0x08007458"))
  if os.getenv("BADCOPY_IN") then
    emu:setBreakpoint(function()
      local src, dst = emu:readRegister("r0"), emu:readRegister("r1")
      local bytes = emu:read16(emu:readRegister("r2") + 8)
      bc.asked_all = (bc.asked_all or 0) + 1
      if not bc_bad(src, dst, bytes) then return end
      local key = string.format("from %08X, %5d bytes", src & 0xFFFFFFFF, bytes)
      if not bc.akinds[key] then bc.akinds[key] = 0; bc.aorder[#bc.aorder + 1] = key end
      bc.akinds[key] = bc.akinds[key] + 1
      bc.asked = bc.asked + 1
      if bc.asked <= 6 then
        w(string.format("BADCOPY asked for (%d) at frame %d: %s to %08X (sprite cell %d) | %s", bc.asked, bc.frame, key, dst,
          (dst - 0x06010000) // 32, state()))
      end
    end, tonumber(os.getenv("BADCOPY_IN")))
  end
end

-- WATCHRANGES="r:0968D000-096C4A00,r:09A10000-09AB810C" (r, w or rw; any number of them): a watchpoint on each
-- stretch of memory; every hit is counted, the first WATCHRANGES_MAX (default 5) of each are logged with pc and lr,
-- and the end of the run says how many there were. (Is a blank stretch of the ROM really unused? Run the game
-- without the patch that wants it and see whether anything ever reads it: _testrun/space.)
local wr = {list = {}, frame = 0, max = tonumber(os.getenv("WATCHRANGES_MAX") or "5")}
for kind, a, b in (os.getenv("WATCHRANGES") or ""):gmatch("(%a+):(%x+)%-(%x+)") do
  local lo, hi = tonumber(a, 16), tonumber(b, 16)
  local e = {kind = kind, lo = lo, hi = hi, n = 0}
  wr.list[#wr.list + 1] = e
  emu:setRangeWatchpoint(function()
    e.n = e.n + 1
    if e.n <= wr.max then
      w(string.format("WATCHRANGES %s:%08X-%08X hit %d at frame %d: pc %08X lr %08X r0 %08X r1 %08X r2 %08X | %s", kind, lo, hi,
        e.n, wr.frame, emu:readRegister("pc"), emu:readRegister("lr"), emu:readRegister("r0"), emu:readRegister("r1"),
        emu:readRegister("r2"), state()))
    end
  end, lo, hi, ({r = C.WATCHPOINT_TYPE.READ, w = C.WATCHPOINT_TYPE.WRITE, rw = C.WATCHPOINT_TYPE.RW})[kind])
end

function TEST(f)
  bc.frame = f
  wr.frame = f
  if bc.probe then
    local now, was = emu:readRange(0x06000000, 0x18000), bc.probe.was
    local spr, bg = 0, 0
    for k = 0, 0x17FFF, 32 do
      if now:sub(k + 1, k + 32) ~= was:sub(k + 1, k + 32) then
        if k >= 0x10000 then spr = spr + 1 elseif k < 0x8000 then bg = bg + 1 end
      end
    end
    w(string.format("BADCOPY %s: by the next frame %d of the 1024 sprite cells and %d of the 1024 tile cells had changed%s",
      bc.probe.key, spr, bg, (spr > 40 or bg > 40) and "" or " (the BIOS refused it)"))
    if spr > 40 then shot(string.format("badcopy_%s_f%d", bc.probe.key:sub(6, 13), f)) end
    bc.probe = nil
  end
  if wa.pending then                                         -- the frame after a hit: a picture and video memory
    wa.pending = false
    if wa.events <= 8 then
      shot(string.format("watchaddr_%02d_f%d", wa.events, f))
      local fh = io.open(DIR .. string.format("watchaddr_%02d.bin", wa.events), "wb")
      fh:write(emu:readRange(0x06000000, 0x18000)); fh:write(emu:readRange(0x05000000, 0x400)); fh:close()
      w(string.format("WATCHADDR event %d: %d hits so far, picture and video memory written at frame %d | %s | objs %s",
        wa.events, wa.n, f, state(), objs()))
    end
  end
  wa.frame = f
  if BIGWRITE then bigwrite(f) end
  if PALWATCH then palwatch(f) end
  if TILEWATCH then tilewatch(f) end
  if SPRWATCH then sprwatch(f) end
  if REC and (f - REC.f0) % REC.every == 0 then          -- {"rec", tag, every}: a picture every `every` frames
    shot(string.format("rec_%s_%04d", REC.tag, REC.n)); REC.n = REC.n + 1
  end
  local s = STEPS[i]
  if not s then return end
  t0 = t0 or f
  local dt = f - t0
  if s[1] == "rec" then
    -- {"rec", tag, every}: from now on a picture every `every` frames (rec_<tag>_0000.png ...), until "recstop"
    REC = {tag = s[2], every = s[3] or 6, f0 = f, n = 0}; i = i + 1; t0 = f + 1; return
  elseif s[1] == "recstop" then
    REC = nil; i = i + 1; t0 = f + 1; return
  elseif s[1] == "wait" then
    -- {"wait", frames}: nothing for that long
    if dt >= s[2] then i = i + 1; t0 = f + 1 end
    return
  elseif s[1] == "daynight_off" then
    -- {"daynight_off"}: the Option menu's Day/Night set to Off (bit 4 of SaveBlock2 + 0x15, daynight's tint_gate):
    -- the field in its daytime colours whatever the save's clock says, from the next map load on
    local sb2 = emu:read32(0x03005D90)
    emu:write8(sb2 + 0x15, emu:read8(sb2 + 0x15) | 0x10); i = i + 1; t0 = f + 1; return
  end
  local function nextstep() i = i + 1; t0 = f + 1 end
  if s[1] == "setup" then
    if s.fresh then for _, fl in ipairs(STORY_FLAGS) do setflag(fl, false) end end
    for _, fl in ipairs(s.set or {}) do setflag(fl, true) end
    for _, fl in ipairs(s.clear or {}) do setflag(fl, false) end
    if s.stage then setvar(STAGE, s.stage) end
    if s.repel ~= false then setvar(0x4021, 250) end       -- a Repel's steps: no wild battles in the grass
    w("setup | " .. state()); nextstep()
  elseif s[1] == "warp" then
    if dt == 0 then run({0x3A, s[2], s[3], 0xFF, s[4] & 0xFF, s[4] >> 8, s[5] & 0xFF, s[5] >> 8, 0x02}) end
    if dt == 200 then w(string.format("warp       | %s | objs %s", state(), objs())); nextstep() end
  elseif s[1] == "shot" then
    if dt == 0 then shot(string.format("%02d_%s", i, s[2])); w(string.format("shot %-5s | %s | objs %s", s[2], state(), objs())) end
    if dt == 2 then nextstep() end
  elseif s[1] == "walk" then
    -- {"walk", x, y, "on"|"act", label}: walk onto (x, y), or next to it
    if not s.started then
      if lock() ~= 0 or cb2() ~= OVERWORLD then t0 = f + 1; return end
      s.started = true
      local rp = var(0x4021)
      if rp > 0 and rp < 80 then setvar(0x4021, 250) end   -- a Repel running low would stop the walk with its prompt
      local ok, n = walk_start(s[2], s[3], s[4] == "act")
      if not ok then
        w(string.format("%-10s NO ROUTE to (%d,%d) | %s", s[5] or "walk", s[2], s[3], state()))
        done(); i = 9999; return
      end
    end
    local r = walk_tick(f, KEYS)
    if dt % 40 == 0 then shot(string.format("%02d_walk_%s_%03d", i, s[5] or "", dt // 40)) end
    if r == "stuck" then
      local x, y = player_xy()
      w(string.format("%-10s STUCK at (%d,%d) block %04X | %s", s[5] or "walk", x, y, block_at(x, y), state()))
      done(); i = 9999; return
    elseif r == "done" or r == "interrupted" then
      w(string.format("%-10s %s | %s", s[5] or "walk", r, state())); nextstep()
    end
  elseif s[1] == "face_to" then
    if dt == 0 then
      local x, y = player_xy()
      local d = (s[3] < y and "UP") or (s[3] > y and "DOWN") or (s[2] < x and "LEFT") or "RIGHT"
      walk_face(d, KEYS)
    end
    if dt == 12 then nextstep() end
  elseif s[1] == "face" then
    if dt == 0 then tap(KEYS[s[2]], 2) end
    if dt == 12 then nextstep() end
  elseif s[1] == "a" then
    if dt == 0 then tap(K.A) end
    if dt == 10 then nextstep() end
  elseif s[1] == "mash" then
    -- {"mash", label, map (group * 1000 + num, or 0 for any)}: A while a script owns the screen
    if dt % SHOT == 0 then shot(string.format("%02d_%s_%03d", i, s[2], dt // SHOT)) end
    if dt % 14 == 0 and (lock() ~= 0 or cb2() ~= OVERWORLD or dt < 30) then tap(K.A, 4) end
    local mapok = (s[3] == 0) or (mapid() == s[3])
    if dt > 90 and cb2() == OVERWORLD and lock() == 0 and mapok then calm = calm + 1 else calm = 0 end
    if calm >= 45 then
      calm = 0
      w(string.format("%-10s done after %5d | %s | objs %s", s[2], dt, state(), objs())); nextstep()
    elseif dt > 12000 then
      w(string.format("%-10s TIMEOUT | %s cb2 %08X lock %d", s[2], state(), cb2(), lock())); done(); i = 9999
    end
  elseif s[1] == "step" then
    -- {"step", dir, n}: n single steps (into a cave mouth: the warp happens on the step)
    if dt % 20 == 0 and dt // 20 < s[3] then tap(KEYS[s[2]], 10) end
    if dt == 20 * s[3] + 4 then nextstep() end
  elseif s[1] == "slide" then
    -- {"slide", dir}: one press of a direction, held until you set off (or for 20 frames: a wall, and you only
    -- turn), then wait until you have stood still for 24 frames with the field yours: on ice that is where the
    -- slide ends (the Sealed Vault); on floor it is one step. {"slide", dir, x, y}: and you must be there, or
    -- the run stops.
    if dt == 0 then s.fx, s.fy = player_xy() end
    if not s.off then
      local x, y = player_xy()
      if x ~= s.fx or y ~= s.fy or dt >= 20 then s.off = dt else tap(KEYS[s[2]], 2) end
    elseif dt > s.off + 2 then
      local x, y = player_xy()
      if x == s.lx and y == s.ly and lock() == 0 and cb2() == OVERWORLD then s.still = (s.still or 0) + 1 else s.still = 0 end
      s.lx, s.ly = x, y
      if s.still >= 24 then
        if s[3] and (x ~= s[3] or y ~= s[4]) then
          w(string.format("FAIL slide %s from %d,%d ended at %d,%d, not %d,%d | %s", s[2], s.fx, s.fy, x, y, s[3], s[4], state()))
          done(); i = 9999; return
        end
        w(string.format("slide %-5s | %d,%d -> %d,%d", s[2], s.fx, s.fy, x, y)); nextstep()
      elseif dt > 1200 then
        w("slide TIMEOUT | " .. state()); done(); i = 9999
      end
    end
  elseif s[1] == "hold" then
    -- {"hold", dir, frames}: hold a direction that long, as a player who keeps it down through a slide does, then
    -- wait until you have stood still for 24 frames with the field yours (or a map has come in its place)
    if dt == 0 then s.fx, s.fy = player_xy(); tap(KEYS[s[2]], s[3]) end
    if dt > s[3] then
      local x, y = player_xy()
      if x == s.lx and y == s.ly and lock() == 0 and cb2() == OVERWORLD then s.still = (s.still or 0) + 1 else s.still = 0 end
      s.lx, s.ly = x, y
      if s.still >= 24 then
        w(string.format("hold %-5s %d frames | %d,%d -> %d,%d | %s", s[2], s[3], s.fx, s.fy, x, y, state())); nextstep()
      elseif dt > s[3] + 1200 then
        w("hold TIMEOUT | " .. state()); done(); i = 9999
      end
    end
  elseif s[1] == "pull" then
    -- {"pull", {local ids}, label, map}: the Sealed Vault's stakes, in whatever order they can be come to a stop
    -- beside (the walker slides: walk.lua), until none is left standing. For each: walk up to it, face it, A,
    -- and A through its script. The run stops if some are left and none can be reached.
    s.left = s.left or {table.unpack(s[2])}
    if not s.phase then
      if lock() ~= 0 or cb2() ~= OVERWORLD then t0 = f + 1; return end
      local standing = {}
      for _, id in ipairs(s.left) do
        local x, y, fl = template(id)
        if x and not (fl ~= 0 and flag(fl) == 1) then standing[#standing + 1] = {id, x, y} end
      end
      if #standing == 0 then w(string.format("ok   %-10s every stake pulled | %s", s[3] or "pull", state())); nextstep(); return end
      s.now = nil
      for _, c in ipairs(standing) do
        if walk_start(c[2], c[3], true) then s.now = c; break end
      end
      if not s.now then
        local px, py = player_xy()
        w(string.format("FAIL %-10s no stake can be reached from %d,%d (%d left) | %s", s[3] or "pull", px, py, #standing, state()))
        done(); i = 9999; return
      end
      s.phase, s.t = "walk", 0
    elseif s.phase == "walk" then
      local r = walk_tick(f, KEYS)
      if r == "stuck" or r == "noroute" or r == "interrupted" then
        w(string.format("FAIL %-10s %s on the way to the stake %d | %s", s[3] or "pull", r, s.now[1], state())); done(); i = 9999; return
      elseif r == "done" then s.phase, s.t = "face", 0 end
    elseif s.phase == "face" then
      s.t = s.t + 1
      if s.t == 1 then
        local x, y = player_xy()
        local d = (s.now[3] < y and "UP") or (s.now[3] > y and "DOWN") or (s.now[2] < x and "LEFT") or "RIGHT"
        walk_face(d, KEYS)
      elseif s.t == 14 then tap(K.A)
      elseif s.t >= 24 then s.phase, s.t, s.calm = "mash", 0, 0; s.at = {player_xy()} end
    elseif s.phase == "mash" then
      s.t = s.t + 1
      if s.t % SHOT == 1 then shot(string.format("%02d_%s_%d_%03d", i, s[3] or "pull", s.now[1], s.t // SHOT)) end
      if s.t % 14 == 0 and (lock() ~= 0 or cb2() ~= OVERWORLD or s.t < 30) then tap(K.A, 4) end
      local x, y = player_xy()                            -- (pulled from the ice you slide on: wait for that too)
      if s.t > 90 and cb2() == OVERWORLD and lock() == 0 and x == s.lx and y == s.ly then s.calm = s.calm + 1 else s.calm = 0 end
      s.lx, s.ly = x, y
      if s.calm >= 45 then
        w(string.format("pulled %d at %d,%d from %d,%d, now at %d,%d | %s | objs %s", s.now[1], s.now[2], s.now[3],
          s.at[1], s.at[2], x, y, state(), objs()))
        local keep = {}
        for _, id in ipairs(s.left) do if id ~= s.now[1] then keep[#keep + 1] = id end end
        s.left, s.phase = keep, nil
      elseif s.t > 6000 then
        w(string.format("%-10s TIMEOUT | %s", s[3] or "pull", state())); done(); i = 9999
      end
    end
  elseif s[1] == "pals" then
    -- {"pals", label}: the tags of the sixteen sprite palettes as the game holds them (sSpritePaletteTags). The
    -- hack gives every object its palette by tag out of slots 4-9, and a seventh tag goes to slot 10.
    local t = {}
    for k = 0, 15 do t[#t + 1] = string.format("%04X", emu:read16(0x03000CF0 + 2 * k)) end
    w(string.format("pals %-10s %s | objs %s", s[2] or "", table.concat(t, " "), objs())); nextstep()
  elseif s[1] == "objpal" then
    -- {"objpal", label}: each object's sprite and the palette slot it draws with (its OAM), every other sprite in
    -- use (its slot, place and callback: a reflection is one), the tags of the sixteen slots, and the first colours
    -- of slots 4-11 as the screen has them
    local t, other, mine = {}, {}, {}
    for k = 0, 15 do
      local o = 0x02037350 + k * 0x24
      if emu:read8(o) & 1 == 1 then
        local id = emu:read8(o + 4)
        mine[id] = true
        t[#t + 1] = string.format("%d:g%d=s%d/p%d", emu:read8(o + 8), emu:read8(o + 5), id,
          emu:read16(0x02020630 + id * 0x44 + 4) >> 12)
      end
    end
    for id = 0, 63 do
      local sp = 0x02020630 + id * 0x44
      local pal = emu:read16(sp + 4) >> 12
      if emu:read8(sp + 0x3E) & 1 == 1 and not mine[id] then
        other[#other + 1] = string.format("s%d/p%d@%d,%d:%08X", id, pal, emu:read16(sp + 0x20), emu:read16(sp + 0x22),
          emu:read32(sp + 0x1C))
      end
    end
    local tags, cols = {}, {}
    for k = 0, 15 do tags[#tags + 1] = string.format("%04X", emu:read16(0x03000CF0 + 2 * k)) end
    for k = 4, 11 do
      cols[#cols + 1] = string.format("%d:%04X.%04X.%04X", k, emu:read16(0x05000200 + 32 * k + 2),
        emu:read16(0x05000200 + 32 * k + 4), emu:read16(0x05000200 + 32 * k + 6))
    end
    local unf, fad = {}, {}                                 -- the same from the loaded and the faded buffers
    for _, k in ipairs({0, 4, 5, 10, 11}) do
      unf[#unf + 1] = string.format("%d:%04X.%04X.%04X", k, emu:read16(0x02037914 + 32 * k + 2),
        emu:read16(0x02037914 + 32 * k + 4), emu:read16(0x02037914 + 32 * k + 6))
      fad[#fad + 1] = string.format("%d:%04X.%04X.%04X", k, emu:read16(0x02037D14 + 32 * k + 2),
        emu:read16(0x02037D14 + 32 * k + 4), emu:read16(0x02037D14 + 32 * k + 6))
    end
    w(string.format("objpal %-8s %s | others %s | tags %s | cols %s | unfaded %s | faded %s", s[2] or "",
      table.concat(t, " "), table.concat(other, " "), table.concat(tags, " "), table.concat(cols, " "),
      table.concat(unf, " "), table.concat(fad, " ")))
    nextstep()
  elseif s[1] == "flee" then
    -- {"flee", label, map}: A through what comes before a wild battle (the cry, the line, "Battle it?"), then in
    -- the battle Run (the action menu's bottom right: Right, Down, A) and A through "Got away safely!"; done when
    -- the field has been ours for 45 frames on that map
    -- (the battle's callback is not BATTLE on every frame of its intro: frames are counted from the first, and
    -- each key goes once its moment has passed; after Run only B, which never picks a move)
    if not s.inb and cb2() == BATTLE then s.inb = dt end
    if s.inb then
      local b = dt - s.inb
      if b < 800 and b > 0 and b % 30 == 0 then tap(K.B, 4)        -- through "Wild ... appeared!" and the rest
      elseif b >= 900 and not s.k1 then
        s.k1 = true; shot(string.format("%02d_%s_menu", i, s[2]))
        w(string.format("%-10s battle: foe %d | %s", s[2], emu:read16(0x02024744 + 0x20), state()))
        tap(K.RIGHT, 4)
      elseif b >= 915 and not s.k2 then s.k2 = true; tap(K.DOWN, 4)
      elseif b >= 930 and not s.k3 then s.k3 = true; shot(string.format("%02d_%s_run", i, s[2])); tap(K.A, 4)
      elseif b > 960 and (b - 960) % 30 == 0 then tap(K.B, 4) end
    elseif dt % 14 == 0 and dt > 0 then
      tap(K.A, 4)
    end
    local mapok = (s[3] == nil) or (mapid() == s[3])
    if s.inb and cb2() == OVERWORLD and lock() == 0 and mapok then calm = calm + 1 else calm = 0 end
    if calm >= 45 then
      calm = 0
      w(string.format("%-10s fled after %d | outcome %d | %s | objs %s", s[2], dt, emu:read8(0x0202433A), state(),
        objs()))
      nextstep()
    elseif dt > 6000 then
      w(string.format("%-10s TIMEOUT | %s cb2 %08X", s[2], state(), cb2())); done(); i = 9999
    end
  elseif s[1] == "journal" then
    -- {"journal"}: the Journal registered to SELECT (as patches/questlog/test_questlog.lua does), so SELECT then
    -- UP opens the Quest Log
    emu:write16(sb1() + 0x496, 363)
    emu:write16(sb1() + 0x9C2, 0); emu:write16(sb1() + 0x9C4, 0); emu:write16(sb1() + 0x9C6, 0)
    nextstep()
  elseif s[1] == "dex" then
    -- {"dex", caught = {national dex numbers}, clear = {...}}: the Pokedex's seen and caught bits (the hack's arrays,
    -- 120 bytes each: SaveBlock1 + 0x560 seen, + 0x5D8 caught; a number's bit is bit `number`, not number - 1:
    -- found by the Legends count on the Gen 9 test save, whose Dex has the Gen 9 numbers)
    for _, d in ipairs(s.clear or {}) do
      for _, base in ipairs({0x560, 0x5D8}) do
        local a = sb1() + base + (d >> 3)
        emu:write8(a, emu:read8(a) & ~(1 << (d & 7)) & 0xFF)
      end
    end
    for _, d in ipairs(s.caught or {}) do
      for _, base in ipairs({0x560, 0x5D8}) do
        local a = sb1() + base + (d >> 3)
        emu:write8(a, emu:read8(a) | (1 << (d & 7)))
      end
    end
    nextstep()
  elseif s[1] == "dex9" then
    -- {"dex9", seen = {...}, caught = {...}, legends = n}: Pokedex marks as the whole Gen 9 build keeps them once
    -- gen9dex has moved a save's marks (the game does it the first time it asks for one): numbers below 960 as
    -- "dex" does, 960 and up in gen9rest's block (0x0203DA00: the marker "DEXA", then 32 bytes seen and 32
    -- caught; bit n & 7 of byte (n - 960) >> 3). legends = n: every number of the Quest Log's Legends rows 1..n
    -- caught (the table at the literal 0x08FEB23C)
    local EXT = 0x0203DA00
    if emu:read32(EXT) ~= 0x41584544 then
      w(string.format("FAIL dex9: the marker is %08X, not DEXA", emu:read32(EXT))); done(); i = 9999; return
    end
    local function mark(d, caught)
      local seen_at, caught_at, k = sb1() + 0x560, sb1() + 0x5D8, d
      if d >= 960 then seen_at, caught_at, k = EXT + 4, EXT + 36, d - 960 end
      local bit = 1 << (k & 7)
      local a = seen_at + (k >> 3)
      emu:write8(a, emu:read8(a) | bit)
      if caught then a = caught_at + (k >> 3); emu:write8(a, emu:read8(a) | bit) end
    end
    for _, d in ipairs(s.clear or {}) do                     -- clear = {...}: neither seen nor caught
      local seen_at, caught_at, k = sb1() + 0x560, sb1() + 0x5D8, d
      if d >= 960 then seen_at, caught_at, k = EXT + 4, EXT + 36, d - 960 end
      for _, a in ipairs({seen_at + (k >> 3), caught_at + (k >> 3)}) do
        emu:write8(a, emu:read8(a) & ~(1 << (k & 7)) & 0xFF)
      end
    end
    for _, d in ipairs(s.seen or {}) do mark(d, false) end
    for _, d in ipairs(s.caught or {}) do mark(d, true) end
    if s.legends then
      local t = emu:read32(0x08FEB23C)
      for r = 1, s.legends do mark(emu:read16(t + 16 * r), true) end
    end
    nextstep()
  elseif s[1] == "qcard" then
    -- {"qcard", chapter}: with the Quest Log's grid up, its cursor (V+0) on that chapter's card, so A opens it
    local v
    for k = 0, 15 do
      local b = 0x03005E00 + k * 40
      if emu:read32(b) == 0x08FEAC8D and emu:read8(b + 4) == 1 then v = emu:read32(b + 8) + 0x800 end
    end
    if not v then w("FAIL qcard: the Quest Log is not open"); done(); i = 9999; return end
    emu:write8(v, s[2]); nextstep()
  elseif s[1] == "evosel" then
    -- {"evosel", row}: in the Quest Log's Evolutions list, the cursor (V+0xFC, 16 bits) one row above `row` and the
    -- top row (V+0xFE) four above that; a DOWN press after it lands on `row` and draws the list and its page
    local v
    for k = 0, 15 do
      local b = 0x03005E00 + k * 40
      if emu:read32(b) == 0x08FEAC8D and emu:read8(b + 4) == 1 then v = emu:read32(b + 8) + 0x800 end
    end
    if not v then w("FAIL evosel: the Quest Log is not open"); done(); i = 9999; return end
    emu:write16(v + 0xFC, s[2] - 1); emu:write16(v + 0xFE, math.max(0, s[2] - 5)); nextstep()
  elseif s[1] == "lmove" then
    -- {"lmove", label}: in a battle that has started, through its opening lines (B), then FIGHT: the move menu with
    -- the L tag (a picture), L held: the move's info panel (a picture), L let go and B back to the action menu
    if not s.inb and cb2() == BATTLE then s.inb = dt end
    if s.inb then
      local b = dt - s.inb
      if b < 800 and b > 0 and b % 30 == 0 then tap(K.B, 4)
      elseif b == 900 then shot(string.format("%02d_%s_action", i, s[2])); tap(K.A, 4)
      elseif b == 980 then shot(string.format("%02d_%s_moves", i, s[2]))
        w(string.format("%-10s battle: foe %d | %s", s[2], emu:read16(0x02024744 + 0x20), state()))
        emu:addKey(K.L)
      elseif b == 1060 then shot(string.format("%02d_%s_info", i, s[2])); emu:clearKey(K.L)
      elseif b == 1140 then shot(string.format("%02d_%s_closed", i, s[2])); tap(K.B, 4)
      elseif b == 1200 then nextstep() end
    elseif dt > 3000 then
      w(string.format("%-10s NO BATTLE | %s", s[2], state())); done(); i = 9999
    end
  elseif s[1] == "qlog" then
    -- {"qlog", label}: with the Quest Log open, its current objective (V+6), the status of every Journal row
    -- (V+0x40.., one digit each) and the grid's done count per chapter (V+0xC8..)
    local v
    for k = 0, 15 do
      local b = 0x03005E00 + k * 40
      if emu:read32(b) == 0x08FEAC8D and emu:read8(b + 4) == 1 then v = emu:read32(b + 8) + 0x800 end
    end
    if not v then w(string.format("FAIL qlog %s: the Quest Log is not open", s[2])); done(); i = 9999; return end
    local st, cnt = {}, {}
    for k = 0, 0x87 do st[#st + 1] = string.format("%d", emu:read8(v + 0x40 + k)) end
    for k = 0, 8 do cnt[#cnt + 1] = string.format("%d", emu:read8(v + 0xC8 + k)) end
    w(string.format("qlog %-10s cur %d page %d sel %d | counts %s | %s", s[2], emu:read8(v + 6), emu:read8(v),
      emu:read8(v + 2), table.concat(cnt, ","), table.concat(st, "")))
    nextstep()
  elseif s[1] == "avatar" then
    -- {"avatar", label}: gPlayerAvatar's flags (bit 3 surfing) and the way you face (1 down, 2 up, 3 left, 4 right)
    w(string.format("avatar %-10s flags %02X facing %d | %s", s[2] or "", emu:read8(0x02037590),
      emu:read8(0x02037350 + 0x18) & 0x0F, state())); nextstep()
  elseif s[1] == "press" then
    -- {"press", key, wait}: one button, then wait
    if dt == 0 then tap(K[s[2]], 6) end
    if dt >= (s[3] or 60) then nextstep() end
  elseif s[1] == "reset" then
    if dt == 0 then emu:reset() end
    if dt == 30 then nextstep() end
  elseif s[1] == "boot" then
    -- from the title screen to the field: START / A until the field has been ours for 120 frames (Continue)
    if cb2() == OVERWORLD and lock() == 0 and dt > 300 then calm = calm + 1 else calm = 0 end
    if calm == 0 and cb2() ~= OVERWORLD then
      if dt % 60 == 0 then tap(K.START) elseif dt % 60 == 30 then tap(K.A) end
    end
    if calm >= 120 then calm = 0; w(string.format("%-10s field after %d | %s | objs %s", "boot", dt, state(), objs())); nextstep() end
    if dt > 6000 then w("boot TIMEOUT cb2 " .. string.format("%08X", cb2())); done(); i = 9999 end
  elseif s[1] == "repel" then
    setvar(0x4021, s[2]); nextstep()
  elseif s[1] == "seed" then
    -- {"seed", value}: gRngValue (0x03005D80) set, so that two builds run on from here alike (the hack seeds it
    -- from the clock at power-on: rngseed; people's turns and steps differ from run to run without this)
    emu:write32(0x03005D80, s[2]); nextstep()
  elseif s[1] == "wild" then
    -- {"wild", label}: pace in the grass until a battle starts, log the wild Pokemon, then win it
    if cb2() ~= BATTLE and not s.inb then
      if dt > 6000 then w(string.format("%-10s NO BATTLE | %s", s[2], state())); done(); i = 9999; return end
      if dt % 30 == 0 then tap(((dt // 30) % 2 == 0) and K.LEFT or K.RIGHT, 14) end
      return
    end
    s.inb = s.inb or dt
    local b = dt - s.inb
    if b == 420 then
      local m = 0x02024744
      w(string.format("%-10s battle: species %d lv %d | %s", s[2], emu:read16(m + 0x20), emu:read8(m + 0x54), state()))
      shot(string.format("%02d_%s", i, s[2]))
    end
    if b > 420 then
      -- finish it with the OHKO cheat: our battler's Atk / Sp. Atk / Speed pinned at 9999,
      -- its first move Dark Pulse (399), A mashed
      if cb2() == BATTLE then
        local base = 0x02024084
        emu:write16(base + 2, 9999); emu:write16(base + 6, 9999); emu:write16(base + 8, 9999)
        emu:write16(base + 0x0C, 399)
        if (b - 420) % 14 == 0 then tap(K.A, 4) end
      elseif lock() ~= 0 and (b - 420) % 14 == 0 then tap(K.A, 4) end
      if (b - 420) % 600 == 0 then shot(string.format("%02d_%s_end_%03d", i, s[2], (b - 420) // 600)) end
      if cb2() == OVERWORLD and lock() == 0 then calm = calm + 1 else calm = 0 end
      if calm >= 45 then calm = 0; w(string.format("%-10s over after %d | %s", s[2], b, state())); nextstep() end
      if b > 12000 then w(string.format("%-10s STILL IN BATTLE | %s", s[2], state())); done(); i = 9999 end
    end
  elseif s[1] == "fight" then
    -- {"fight", label, map}: a script that holds battles (a Titan, a trainer, the finale's three): A through its
    -- text; in battle our battlers are pinned (Atk / Sp. Atk / Speed 9999, HP full, move 1 Dark Pulse) and A
    -- mashed. Done when the field has been ours for 45 frames on the given map.
    if cb2() == BATTLE then
      for _, b in ipairs({0x02024084, 0x02024084 + 2 * 0x58}) do
        emu:write16(b + 2, 9999); emu:write16(b + 6, 9999); emu:write16(b + 8, 9999)
        emu:write16(b + 0x0C, 399); emu:write16(b + 0x28, emu:read16(b + 0x2C))
      end
      if not s.inb then
        s.inb = true; s.n = (s.n or 0) + 1
        s.t_in = dt
      end
      if s.t_in and dt - s.t_in == 420 then
        local m = 0x02024744
        w(string.format("%-10s battle %d: foe %d lv %d (2nd %d) | %s", s[2], s.n, emu:read16(m + 0x20),
          emu:read8(m + 0x54), emu:read16(m + 0x64 + 0x20), state()))
        shot(string.format("%02d_%s_battle%d", i, s[2], s.n))
      end
    else
      s.inb = false
    end
    if dt % SHOT == 0 then shot(string.format("%02d_%s_%03d", i, s[2], dt // SHOT)) end
    if dt % 14 == 0 and (lock() ~= 0 or cb2() ~= OVERWORLD or dt < 30) then tap(K.A, 4) end
    local mapok = (s[3] == 0) or (mapid() == s[3])
    if dt > 90 and cb2() == OVERWORLD and lock() == 0 and mapok then calm = calm + 1 else calm = 0 end
    if calm >= 45 then
      calm = 0
      w(string.format("%-10s done after %5d, %d battles | %s | objs %s", s[2], dt, s.n or 0, state(), objs()))
      nextstep()
    elseif dt > 60000 then
      w(string.format("%-10s TIMEOUT | %s cb2 %08X lock %d", s[2], state(), cb2(), lock())); done(); i = 9999
    end
  elseif s[1] == "roam" then
    -- {"roam", label, frames}: walk about for that many frames as a player might: a fixed round of directions,
    -- each held a while (the same keys on every ROM, so two builds can be compared picture for picture); B
    -- through anything that takes the screen outside a battle (a trainer's lines, a sign: B says no to a
    -- question), and a battle won as "fight" does. Pictures every SHOT frames.
    local ROUND = {{"RIGHT", 64}, {"DOWN", 48}, {"LEFT", 96}, {"UP", 64}, {"RIGHT", 32}, {"DOWN", 80},
                   {"LEFT", 48}, {"UP", 96}, {"RIGHT", 112}, {"DOWN", 32}, {"LEFT", 64}, {"UP", 48}}
    if dt == 0 then s.k, s.left = 0, 0 end
    if dt % SHOT == 0 then shot(string.format("%02d_%s_%03d", i, s[2], dt // SHOT)) end
    if cb2() == BATTLE then
      for _, b in ipairs({0x02024084, 0x02024084 + 2 * 0x58}) do
        emu:write16(b + 2, 9999); emu:write16(b + 6, 9999); emu:write16(b + 8, 9999)
        emu:write16(b + 0x0C, 399); emu:write16(b + 0x28, emu:read16(b + 0x2C))
      end
      if dt % 14 == 0 then tap(K.A, 4) end
    elseif lock() ~= 0 then
      if dt % 14 == 0 then tap(K.B, 4) end
    else
      if s.left <= 0 then
        s.k = s.k % #ROUND + 1
        s.left = ROUND[s.k][2]
        tap(KEYS[ROUND[s.k][1]], ROUND[s.k][2])
      end
      s.left = s.left - 1
    end
    if dt >= s[3] then
      w(string.format("%-10s roamed %d frames | %s | objs %s", s[2], dt, state(), objs())); nextstep()
    end
  elseif s[1] == "roamer" then
    -- {"roamer", label, active = 0|1, species = n, group = g}: log the roaming Pokemon and where it is; with the
    -- named fields, the run stops if they are not so
    local line, act, sp, g, n = roamer()
    local bad = {}
    if s.active and act ~= s.active then bad[#bad + 1] = "active is " .. act end
    if s.species and sp ~= s.species then bad[#bad + 1] = "species is " .. sp end
    if s.group and g ~= s.group then bad[#bad + 1] = "it is in map group " .. g end
    w(string.format("%sroamer %-12s %s%s | you: %s", #bad > 0 and "FAIL " or "", s[2] or "", line,
      #bad > 0 and (" | " .. table.concat(bad, ", ")) or "", state()))
    if #bad > 0 then done(); i = 9999 else nextstep() end
  elseif s[1] == "clearroamer" then
    emu:write8(sb1() + 0x31DC + 0x13, 0); nextstep()
  elseif s[1] == "setroamer" then
    -- {"setroamer"}: the roaming Pokemon is put on the map you are on (as when you have tracked it down)
    emu:write8(0x0203BC86, emu:read8(sb1() + 4)); emu:write8(0x0203BC87, emu:read8(sb1() + 5)); nextstep()
  elseif s[1] == "script" then
    -- {"script", {bytes}, wait}: a script of the game's commands, run as the harness runs its warps
    if dt == 0 then run(s[2]) end
    if dt >= (s[3] or 60) then nextstep() end
  elseif s[1] == "tracker" then
    -- {"tracker", label}: the News Tracker (item 695) used as a player does: registered on the SELECT ring's
    -- UP, and in the Key Items pocket if it was not; SELECT, UP; the message it shows is logged (gStringVar4)
    -- with a picture, then B until the field is yours again
    if dt == 0 then
      local pocket, cap = emu:read32(0x02039DD8 + 4 * 8), emu:read8(0x02039DD8 + 4 * 8 + 4)
      local have, free = false, nil
      for k = 0, cap - 1 do
        local it = emu:read16(pocket + 4 * k)
        if it == 695 then have = true end
        if it == 0 and not free then free = k end
      end
      if not have and free then                             -- (a quantity is kept XORed with the save's key)
        emu:write16(pocket + 4 * free, 695)
        emu:write16(pocket + 4 * free + 2, 1 ~ (emu:read32(sb2() + 0xAC) & 0xFFFF))
      end
      w(string.format("tracker: Key Items pocket of %d, the News Tracker %s", cap,
        have and "is in it" or (free and ("put in slot " .. free) or "DOES NOT FIT")))
      emu:write16(sb1() + 0x496, 695)
      tap(K.SEL)
    end
    if dt == 50 then tap(K.UP) end
    if dt == 250 then
      shot(string.format("%02d_tracker_%s", i, s[2] or ""))
      local line = roamer()
      w(string.format("tracker %-10s says: %s | region '%s' place '%s' | roamer %s", s[2] or "", gtext(0x02021FC4, 160),
        gtext(0x02021DC4, 20), gtext(0x02021EC4, 30), line))
    end
    if dt > 250 and dt % 20 == 0 and (lock() ~= 0 or cb2() ~= OVERWORLD) then tap(K.B, 4) end
    if dt > 300 and lock() == 0 and cb2() == OVERWORLD then calm = calm + 1 else calm = 0 end
    if calm >= 40 then calm = 0; nextstep() end
    if dt > 3000 then w("tracker TIMEOUT | " .. state()); done(); i = 9999 end
  elseif s[1] == "hunt" then
    -- {"hunt", label, species, battles}: pace in the grass (or on the water) until a wild battle; if it is that
    -- species, log it with a picture and run; if not, run and pace on; at most `battles` battles (default 40).
    -- The roaming Pokemon comes up one battle in four on the map it is on.
    s.n = s.n or 0
    if not s.inb then
      if cb2() == BATTLE then s.inb = dt
      elseif lock() ~= 0 then if dt % 14 == 0 then tap(K.B, 4) end
      else
        if dt % 30 == 0 then tap(((dt // 30) % 2 == 0) and K.LEFT or K.RIGHT, 14) end
        if dt > 40000 then w(string.format("%-10s NO BATTLE | %s", s[2], state())); done(); i = 9999 end
      end
      return
    end
    local b = dt - s.inb
    if b < 800 and b > 0 and b % 30 == 0 then tap(K.B, 4)
    elseif b == 800 then
      s.n = s.n + 1
      s.foe = emu:read16(0x02024744 + 0x20)
      w(string.format("%-10s battle %d: foe species %d level %d hp %d | roamer %s", s[2], s.n, s.foe,
        emu:read8(0x02024744 + 0x54), emu:read16(0x02024744 + 0x56), (roamer())))
      if s.foe == s[3] then shot(string.format("%02d_%s_found", i, s[2])) end
    elseif b == 900 then tap(K.RIGHT, 4)
    elseif b == 915 then tap(K.DOWN, 4)
    elseif b == 930 then tap(K.A, 4)
    elseif b > 960 and (b - 960) % 30 == 0 then tap(K.B, 4) end
    if b > 960 and cb2() == OVERWORLD and lock() == 0 then calm = calm + 1 else calm = 0 end
    if calm >= 45 then
      calm = 0
      if s.foe == s[3] then
        w(string.format("%-10s found after %d battles | outcome %d | roamer %s", s[2], s.n, emu:read8(0x0202433A), (roamer())))
        nextstep()
      elseif s.n >= (s[4] or 40) then
        w(string.format("FAIL %-10s %d battles and no species %d | roamer %s | %s", s[2], s.n, s[3], (roamer()), state()))
        done(); i = 9999
      else
        s.inb = nil; t0 = f + 1
      end
    elseif b > 8000 then
      w(string.format("%-10s STILL IN BATTLE | %s", s[2], state())); done(); i = 9999
    end
  elseif s[1] == "dexnav" then
    -- {"dexnav", species}: a DexNav search armed for this species on the map you are on, as its screen's A does
    -- (patches/dexnavabil/test_dexnavabil.lua's arm: the state block 0x0203A660): the bar comes up on the field
    local ST = 0x0203A660
    if dt == 0 then emu:write8(ST + 9, 0) end
    if dt == 6 then
      emu:write16(ST + 2, s[2]); emu:write16(ST + 4, 0); emu:write16(ST + 24, 0)
      emu:write8(ST + 15, 20); emu:write8(ST + 16, 20)
      emu:write8(ST + 10, emu:read8(sb1() + 4)); emu:write8(ST + 11, emu:read8(sb1() + 5))
      emu:write16(0x03005D30, 0)
      emu:write8(ST + 9, 1)
    end
    if dt >= 40 then nextstep() end
  elseif s[1] == "sprites" then
    -- {"sprites", label}: every sprite in use: where it is drawn (its position with the offsets and the corner
    -- vector), its OAM shape / size / tile number / palette, whether it draws from a sheet and that sheet's first
    -- tile, its callback and its pictures' address; and which object it is, if it is one
    local owner = {}
    for k = 0, 15 do
      local o = 0x02037350 + k * 0x24
      if emu:read8(o) & 1 == 1 then
        owner[emu:read8(o + 4)] = string.format("obj %d (local %d, gfx %d) at %d,%d", k, emu:read8(o + 8), emu:read8(o + 5),
          emu:read16(o + 0x10) - 7, emu:read16(o + 0x12) - 7)
      end
    end
    w(string.format("sprites %s | %s", s[2] or "", state()))
    local function s16(v) if v >= 0x8000 then return v - 0x10000 end return v end
    local function s8(v) if v >= 0x80 then return v - 0x100 end return v end
    for id = 0, 63 do
      local sp = 0x02020630 + id * 0x44
      local fl = emu:read16(sp + 0x3E)
      if fl & 1 == 1 then
        local a0, a1, a2 = emu:read16(sp), emu:read16(sp + 2), emu:read16(sp + 4)
        local x = s16(emu:read16(sp + 0x20)) + s16(emu:read16(sp + 0x24)) + s8(emu:read8(sp + 0x28))
        local y = s16(emu:read16(sp + 0x22)) + s16(emu:read16(sp + 0x26)) + s8(emu:read8(sp + 0x29))
        w(string.format("   s%-2d at %4d,%4d shape %d size %d tile %4d pal %2d%s%s sheet %s start %5d | cb %08X images %08X | %s",
          id, x, y, a0 >> 14, a1 >> 14, a2 & 0x3FF, a2 >> 12, (fl & 4 ~= 0) and " INVISIBLE" or "",
          (fl & 2 ~= 0) and " (map coords)" or "", (emu:read8(sp + 0x3F) & 0x40 ~= 0) and "yes" or "no ",
          emu:read16(sp + 0x40), emu:read32(sp + 0x1C), emu:read32(sp + 0x0C), owner[id] or ""))
      end
    end
    nextstep()
  elseif s[1] == "playtime" then
    -- {"playtime", label}: the game's clock (SaveBlock2 + 0x0E: hours, minutes, seconds) and where you are: to
    -- tell which of two saves or save states of one game is the later
    w(string.format("playtime %-10s %d:%02d:%02d | %s | objs %s", s[2] or "", emu:read16(sb2() + 0x0E), emu:read8(sb2() + 0x10),
      emu:read8(sb2() + 0x11), state(), objs()))
    nextstep()
  elseif s[1] == "lockstate" then
    -- {"lockstate", label}: is the field yours (0) or does a script, a menu or a message hold it; the script
    -- context's state and where it is reading; where the map's people are
    w(string.format("lockstate %-8s lock %d, script context mode %d status %d at %08X | %s | objs %s", s[2] or "", lock(),
      emu:read8(0x03000E41), emu:read8(0x03000E38), emu:read32(0x03000E48), state(), objs()))
    nextstep()
  elseif s[1] == "cells" then
    -- {"cells", "keep"}: the first 400 cells of the map's first tileset in video memory are kept (from 432 on they
    -- move by themselves: water, shore, flowers). {"cells", "check", label, same = true} or {..., differ = true}:
    -- how many differ now; the run stops if that is not as said. (patches/sprframe: a sprite's missing picture
    -- frame was copied over them.)
    if s[2] == "keep" then
      bc.cells = emu:readRange(0x06000000, 400 * 32)
      w("cells kept | " .. state())
      nextstep()
    else
      local now, n, first, last = emu:readRange(0x06000000, 400 * 32), 0, nil, nil
      for t = 0, 399 do
        if now:sub(t * 32 + 1, t * 32 + 32) ~= bc.cells:sub(t * 32 + 1, t * 32 + 32) then n = n + 1; first = first or t; last = t end
      end
      local bad = (s.same and n > 0) or (s.differ and n == 0)
      w(string.format("%scells %-10s %d of the first 400 tile cells differ%s | %s", bad and "FAIL " or "", s[3] or "", n,
        n > 0 and string.format(" (cells %d..%d; cell %d now starts %s)", first, last, first,
          string.format("%02X %02X %02X %02X", emu:read8(0x06000000 + first * 32), emu:read8(0x06000001 + first * 32),
            emu:read8(0x06000002 + first * 32), emu:read8(0x06000003 + first * 32))) or "", state()))
      if bad then done(); i = 9999 else nextstep() end
    end
  elseif s[1] == "vram" then
    -- {"vram", name}: video memory (0x06000000, 96 KB), the two palette buffers' hardware copy (0x05000000, 1 KB)
    -- and the registers BG0CNT-BG3CNT and DISPCNT written to <name>.bin in the output folder, for a look outside
    local fh = io.open(DIR .. s[2] .. ".bin", "wb")
    fh:write(emu:readRange(0x06000000, 0x18000)); fh:write(emu:readRange(0x05000000, 0x400))
    fh:close()
    w(string.format("vram %s | DISPCNT %04X BG0CNT %04X BG1CNT %04X BG2CNT %04X BG3CNT %04X | %s", s[2],
      emu:read16(0x04000000), emu:read16(0x04000008), emu:read16(0x0400000A), emu:read16(0x0400000C),
      emu:read16(0x0400000E), state()))
    nextstep()
  elseif s[1] == "flags" then
    -- {"flags", f1, f2, ...}: log those flags' values
    local t = {}
    for k = 2, #s do t[#t + 1] = string.format("%04X=%d", s[k], flag(s[k])) end
    w("flags      " .. table.concat(t, " ")); nextstep()
  elseif s[1] == "expect" then
    -- {"expect", label, on = {flags}, off = {flags}, here = {local ids}, gone = {local ids}, map = g * 1000 + n,
    -- stage = n}: the flags must be set / clear, the map's people with those ids must be on the map / not on it,
    -- the map and the stage var must be those; the run stops if not
    local bad = {}
    if s.map and mapid() ~= s.map then bad[#bad + 1] = "the map is " .. mapid() end
    if s.stage and var(STAGE) ~= s.stage then bad[#bad + 1] = "the stage is " .. var(STAGE) end
    for _, fl in ipairs(s.on or {}) do if flag(fl) ~= 1 then bad[#bad + 1] = string.format("%04X is clear", fl) end end
    for _, fl in ipairs(s.off or {}) do if flag(fl) ~= 0 then bad[#bad + 1] = string.format("%04X is set", fl) end end
    for _, id in ipairs(s.here or {}) do if not active(id) then bad[#bad + 1] = "nobody " .. id end end
    for _, id in ipairs(s.gone or {}) do if active(id) then bad[#bad + 1] = id .. " is here" end end
    -- at = {{local id, x, y}, ...}: on the map, on that tile; nowhere = {{x, y}, ...}: nothing of the map's stands
    -- there; pos = {x, y}: where you stand
    for _, e in ipairs(s.at or {}) do
      local x, y = where(e[1])
      if not x then bad[#bad + 1] = "nobody " .. e[1]
      elseif x ~= e[2] or y ~= e[3] then bad[#bad + 1] = string.format("%d is at %d,%d, not %d,%d", e[1], x, y, e[2], e[3]) end
    end
    for _, e in ipairs(s.nowhere or {}) do
      local id = who(e[1], e[2])
      if id then bad[#bad + 1] = string.format("%d stands at %d,%d", id, e[1], e[2]) end
    end
    -- blocks = {{x, y, value}, ...}: the map's tile there, as the game holds it (metatile, collision, height)
    for _, e in ipairs(s.blocks or {}) do
      local v = block_at(e[1], e[2])
      if v ~= e[3] then bad[#bad + 1] = string.format("the tile at %d,%d is %04X, not %04X", e[1], e[2], v, e[3]) end
    end
    if s.pos then
      local x, y = where(255)
      if x ~= s.pos[1] or y ~= s.pos[2] then bad[#bad + 1] = string.format("you are at %s,%s", tostring(x), tostring(y)) end
    end
    if #bad > 0 then
      w(string.format("FAIL %-10s %s | %s | objs %s", s[2], table.concat(bad, ", "), state(), objs())); done(); i = 9999
    else
      w(string.format("ok   %-10s", s[2])); nextstep()
    end
  elseif s[1] == "loadstate" then
    -- {"loadstate", path}: an emulator save state (the user plays with them), then a second for it to settle
    if dt == 0 then
      local ok = emu:loadStateFile(s[2])
      w("loadstate " .. tostring(ok) .. " " .. s[2])
      if not ok then done(); i = 9999; return end
    end
    if dt == 60 then w("after load | " .. state() .. " | objs " .. objs()); nextstep() end
  elseif s[1] == "menutop" then
    -- the Start menu opens where it was left: put its cursor on the first line (sStartMenuCursorPos)
    emu:write8(0x0203760E, 0); nextstep()
  elseif s[1] == "finish" then
    if SPRWATCH then w(string.format("sprwatch: %d finding%s", sw_n, sw_n == 1 and "" or "s")) end
    for _, e in ipairs(wr.list) do
      w(string.format("watchranges: %s %08X-%08X (%d bytes): %d hits", e.kind, e.lo, e.hi, e.hi - e.lo, e.n))
    end
    if BADCOPY then
      w(string.format("badcopy: %d of the %d sprite picture copies made were bad", bc.n, bc.all))
      for _, k in ipairs(bc.order) do w(string.format("   %5d x %s", bc.kinds[k], k)) end
      local ks = {}
      for k in pairs(bc.sizes or {}) do ks[#ks + 1] = k end
      table.sort(ks)
      for _, k in ipairs(ks) do w(string.format("   %5d x good: %s", bc.sizes[k], k)) end
      if os.getenv("BADCOPY_IN") then
        w(string.format("badcopy: %d copies were asked for, %d of them bad: %d good ones asked for, %d made%s", bc.asked_all or 0,
          bc.asked, (bc.asked_all or 0) - bc.asked, bc.all,
          ((bc.asked_all or 0) - bc.asked == bc.all) and "" or "   <-- FAIL: the guard dropped a good one or let a bad one by"))
        w(string.format("badcopy: %d bad ones were asked for", bc.asked))
        for _, k in ipairs(bc.aorder) do w(string.format("   %5d x asked: %s", bc.akinds[k], k)) end
      end
      -- BADCOPY_MUST=none: no bad copy may have been made, and (with BADCOPY_IN) some must have been asked for,
      -- or the run proved nothing; BADCOPY_MUST=some: some must have been made (the ROM without the fix)
      local must = os.getenv("BADCOPY_MUST")
      if must == "none" and (bc.n > 0 or (os.getenv("BADCOPY_IN") and bc.asked == 0)) then
        w("FAIL badcopy: " .. (bc.n > 0 and "bad copies were made" or "no bad copy was asked for: nothing was tested"))
      elseif must == "some" and bc.n == 0 then
        w("FAIL badcopy: no bad copy was made")
      end
    end
    if PALWATCH then w(string.format("palwatch: %d time%s a sprite's slot went to another kind; %d sprite%s in a slot without its colours (%d looks, %d in a fade, %d sprites looked at)",
      pw_bad, pw_bad == 1 and "" or "s", pw_wrong, pw_wrong == 1 and "" or "s", pw_runs, pw_faded, pw_looked)) end
    w("finished | " .. state()); done(); i = 9999
  end
end
