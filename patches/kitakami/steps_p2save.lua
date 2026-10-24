-- Makes the user's "Part 2 start" save (2026-10-17, the user: "give me the part 2 save" -> "Part 1 done, at Briar"):
-- their own game, Part 1's story flags set as its ending leaves them, Ogerpon (Teal Mask, Lv 75) given as its catch
-- gives it (givemon: the party, or the PC when the party is full), standing at Mossui's bus stop beside Briar; saved
-- in the game, then Continue to show it took. No Repel is left running (setup's repel = false).
--   ..\paldea\run.ps1 -Rom p2s.gba -Steps ../../../_testrun/kitakami/steps_p2save.lua -Timeout 600
local MOSSUI = 35106
local PART1 = {0x43E9, 0x43EB, 0x43ED, 0x43F2, 0x43F8, 0x43F9, 0x43FC, 0x43FE, 0x440B, 0x440C, 0x441B, 0x4337, 0x4346,
               0x4347, 0x434A, 0x4352}
local function party()
  local t = {}
  for k = 0, 5 do t[#t + 1] = tostring(emu:read16(0x020244EC + 100 * k + 0x20)) end
  return table.concat(t, " ")
end
local function dex(n)        -- seen, caught of National Dex n (960 and up: gen9rest's block at 0x0203DA00)
  local ext, k = 0x0203DA00, n - 960
  return (emu:read8(ext + 4 + (k >> 3)) >> (k & 7)) & 1, (emu:read8(ext + 36 + (k >> 3)) >> (k & 7)) & 1
end
local last = nil
callbacks:add("frame", function()            -- the party and Ogerpon's Pokedex marks whenever they change
  if emu:read32(0x03005D8C) == 0 then return end
  local sn, cn = dex(1017)
  local now = string.format("party species %s; Pokedex 1017 (Ogerpon) seen %d caught %d", party(), sn, cn)
  if now ~= last then last = now; w("test: " .. now) end
end)
STEPS = {
  {"setup", set = PART1, repel = false},
  {"warp", 35, 106, 23, 46}, {"wait", 60},
  {"script", {0x79, 0xCC, 0x04, 75, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0x02}, 120},      -- givemon Ogerpon (1228) Lv 75
  {"face", "LEFT"}, {"wait", 30},
  {"expect", "part1_done_by_briar", map = MOSSUI, pos = {23, 46}, on = {0x4352}, off = {0x437D}},
  {"shot", "by_briar"},
  {"menutop"},
  {"press", "START", 90},
  {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15},
  {"press", "A", 60}, {"mash", "save", MOSSUI},
  {"reset"}, {"boot"},
  {"expect", "continued", map = MOSSUI, pos = {23, 46}, on = {0x4352}, off = {0x437D}},
  {"shot", "continued"},
  {"finish"},
}
