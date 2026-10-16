-- Continue from test_edges_make.lua's save, at the crater's west edge. The save holds the tiles round you as the
-- game held them when it was made. From a build before the strips those past the edge are "nothing here" (the
-- border block is drawn): the build's stamp differs, the map is read again (story.FRESH) and the strips are
-- there. From this build they are the strips' own, kept by the save. Either way the cliff runs on to the west.
STEPS = {
  {"shot", "continued"},
  {"expect", "past_the_edge", map = 35090, pos = {4, 16}, stage = 4,
   blocks = {{-3, 11, 0x3479}, {-2, 11, 0x3479}, {-1, 12, 0x3479}, {-3, 13, 0x35EF}, {-2, 14, 0x35D6},
             {-3, 16, 0x35D7}, {-1, 20, 0x35D7}}},
  {"walk", 12, 17, "on", "away"}, {"walk", 4, 16, "on", "and_back"},
  {"expect", "still", pos = {4, 16}, blocks = {{-3, 11, 0x3479}, {-1, 12, 0x3479}}},
  {"shot", "back_at_the_edge"},
  {"finish"},
}
