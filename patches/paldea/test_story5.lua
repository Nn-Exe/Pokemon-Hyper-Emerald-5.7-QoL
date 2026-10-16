-- After the story: Koraidon at the picnic (battled and knocked out: gone for good since test 18, as each legend
-- is once caught or knocked out), Walking Wake on the river above the
-- waterfall (surfed up to and talked to from the water), Chien-Pao in the icy cave, the Crystal Cavern's ladder
-- down to the Underdepths and Terapagos. (Ting-Lu, Chi-Yu and Wo-Chien stood in the cavern up to test 14; they
-- are in the Sealed Vault now: test_steps_vault.lua.)
STEPS = {
  {"setup", fresh = true, set = {0x41D5, 0x43AC, 0x43AD, 0x43B1, 0x43B2, 0x43B3, 0x43B4, 0x43B5, 0x43B6,
                                 0x43B7, 0x43B8, 0x43B9, 0x43BA, 0x43BB, 0x43BC, 0x43BD, 0x43BE, 0x43C0, 0x43C1},
   stage = 4},
  {"warp", 35, 90, 26, 31},
  {"shot", "past_after"},
  -- run from Gouging Fire: it stays; then knock it out: gone
  {"walk", 8, 34, "act", "to_gouging_fire"}, {"face_to", 8, 34}, {"a"}, {"flee", "gouging_fire", 35090},
  {"expect", "gouging_fire_stays", off = {0x43C6}, here = {25}},
  {"a"}, {"fight", "gouging_fire", 35090},
  {"expect", "gouging_fire_gone", on = {0x43C6}, gone = {25}},
  {"walk", 39, 43, "on", "to_koraidon"}, {"face", "UP"}, {"a"}, {"fight", "koraidon", 35090},
  {"expect", "koraidon_gone", on = {0x43C3}, gone = {20}}, {"shot", "koraidon_gone"},
  {"warp", 35, 90, 33, 20},                                    -- the pond's south shore
  {"face", "UP"}, {"a"}, {"mash", "surf", 35090},
  {"step", "UP", 4},
  {"face", "UP"}, {"a"}, {"mash", "waterfall", 35090},
  {"shot", "top_of_the_falls"},
  {"step", "UP", 3},                                           -- up the river until it is in the way
  {"shot", "walking_wake"},
  {"expect", "walking_wake_there", here = {24}},
  {"face", "UP"}, {"a"}, {"fight", "walking_wake", 35090},
  {"expect", "walking_wake_gone", on = {0x43C5}, gone = {24}},
  {"shot", "walking_wake_after"},
  {"warp", 35, 95, 6, 7},
  {"shot", "icecave"},
  {"walk", 6, 5, "on", "to_chien_pao"}, {"face", "UP"}, {"shot", "chien_pao"}, {"a"},
  {"fight", "chien_pao", 35095},
  {"expect", "chien_pao_gone", on = {0x43CE}}, {"shot", "chien_pao_gone"},
  {"warp", 35, 94, 3, 2},
  {"shot", "cavern"},
  {"walk", 6, 10, "on", "to_ladder"}, {"step", "DOWN", 1}, {"mash", "down_ladder", 35100},
  {"shot", "underdepths"},
  {"walk", 12, 16, "on", "to_terapagos"}, {"face", "UP"}, {"a"}, {"fight", "terapagos", 35100},
  {"expect", "terapagos_gone", on = {0x43D1}}, {"shot", "terapagos_gone"},
  {"warp", 35, 90, 26, 31},                                    -- back in the past: still gone
  {"expect", "still_gone", map = 35090, gone = {20, 24}},
  {"finish"},
}
