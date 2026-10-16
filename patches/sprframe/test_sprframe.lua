-- sprframe: a sprite's picture frame that does not exist is no longer copied. Steps for
-- patches/paldea/test_paldea.lua (the harness: STEPSFILE = "../sprframe/test_sprframe.lua"), on the game itself
-- with its late-game save.
--   with the fix:    BADCOPY=1 BADCOPY_AT=0x08FEFA4E BADCOPY_IN=0x08FEFA20 BADCOPY_MUST=none
--                    (the two addresses sprframe_patch.py prints: the copy itself, the guard)
--   without the fix: BADCOPY=1 BADCOPY_MUST=some
-- Prelude Beach (37/104). Two of its wandering wild Pokemon have a picture table shorter than the walking
-- animation they are given: local id 13 on the sand by (25,21) and local id 8 at sea by (38,37).
--   1. On the sand at (22,22): the first tileset's cells are kept; ten seconds beside local 13, which wanders
--      by itself (a step every second or two). A picture.
--   2. Surf from (22,20), out to about (38,32), in sight of local 8; fifteen seconds there. A picture, and the
--      tileset's cells compared: they must be as they were.
--      (Walking the two by script - lockall, applymovement - stalled one run in three, with the fix and without:
--      a wanderer frozen in mid-step never ends the script's movement. Waiting does as well.)
-- The end of the run counts the copies (the harness's "badcopy" lines). Without the fix the bad ones are made:
-- in mGBA, as on a console, the BIOS itself refuses two of the four kinds (a source that starts or ends below
-- 0x02000000: {0xFFFFFFFF, 0xFFFF} and {0xE0FF28E0, 0xE039}), and the other two turn every sprite after the
-- Pokemon to stripes ({0x22BB0000, 0xB000}) or the next 92 cells to coloured noise ({0x05300200, 0x0B90}, which
-- is palette memory). An emulator whose BIOS does not refuse makes all four, and the 65,534-byte one runs on
-- from sprite memory over the first cells of the tileset: the player's report. With the fix none is made.
STEPS = {
  {"repel", 250},
  {"warp", 37, 104, 22, 22}, {"press", "B", 120},
  {"expect", "on_the_sand", here = {13}},
  {"cells", "keep"}, {"shot", "1_sand_before"},
  {"press", "B", 600},
  {"cells", "check", "sand", same = true}, {"shot", "2_sand_after"},
  {"warp", 37, 104, 22, 20}, {"press", "B", 60},
  {"face", "RIGHT"}, {"a"}, {"mash", "surf", 37104}, {"press", "B", 30},
}
-- (a tile at a time: Surf is fast in this game, and a held key goes two)
for _, leg in ipairs({{"RIGHT", 11}, {"DOWN", 10}, {"RIGHT", 4}, {"DOWN", 3}}) do
  for _ = 1, leg[2] do STEPS[#STEPS + 1] = {"slide", leg[1]} end
end
for _, st in ipairs({
  {"expect", "at_sea", here = {8}},
  {"shot", "3_sea_before"},
  {"press", "B", 900},
  {"cells", "check", "sea", same = true}, {"shot", "4_sea_after"},
  {"slide", "LEFT"}, {"slide", "LEFT"}, {"shot", "5_sea_later"},
  {"finish"},
}) do STEPS[#STEPS + 1] = st end
