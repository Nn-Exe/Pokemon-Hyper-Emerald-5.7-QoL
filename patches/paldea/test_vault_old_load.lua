-- Continue from test_vault_old_make.lua's save (made in the Crystal Cavern on test 14) on the build with the
-- Sealed Vault. The save holds the cavern as it was: three of the Ruinous four standing in it and a crystal in
-- front of the second mouth. The build's stamp differs, so the cavern is read again (story.FRESH): they are
-- gone from it, the way to the mouth is clear, and the mouth leads into the vault, where they stand sealed.
STEPS = {
  {"shot", "continued"},
  {"expect", "read_again", map = 35094, pos = {15, 4}, stage = 4, nowhere = {{15, 2}, {15, 11}, {10, 2}, {14, 8}},
   gone = {8}},
  {"walk", 15, 2, "on", "to_the_mouth"}, {"step", "UP", 1}, {"mash", "into_the_vault", 35101},
  {"expect", "in_the_vault", map = 35101, pos = {9, 16}, off = {0x43D8, 0x43D9, 0x43DA}},
  {"slide", "UP", 9, 15}, {"slide", "LEFT", 8, 15}, {"slide", "UP", 8, 5},
  {"expect", "all_three_sealed", here = {4, 6, 8, 9, 10, 11}},
  {"shot", "the_vault"},
  {"finish"},
}
