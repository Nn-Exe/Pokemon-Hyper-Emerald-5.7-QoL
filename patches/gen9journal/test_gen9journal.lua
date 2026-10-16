-- The Quest Log's Gen 9 rows (gen9journal) and the L tag in battle (lmoveinfo's art), on the whole build, from a
-- copy of the user's newest save. A steps file of patches/paldea/test_paldea.lua (its run.ps1:
-- -Steps ..\gen9journal\test_gen9journal.lua). What it shows, in pictures and the log:
--   * the first opening: the save's Gen 9 marks moved to the official numbers (gen9dex), every chapter's count;
--   * the grid (Legends x/119, Side Content x/55), the Legends list round the Gen 9 rows and at its end (the five
--     Locked rows), a Locked row's detail, Side Content's ten new rows and a detail, the Badges chapter after them;
--   * some Paradox Pokemon seen / caught and some Side Content flags set: the same screens again;
--   * every Legends row caught: "Gotta catch 'em all!" ticked (the Locked rows not needed);
--   * Nemona's rematch in Research Station No. 3 won: story.F_NEMONA_REMATCH (0x43E4) set, not before;
--   * a wild battle: the move menu with the L tag, L for the info panel.
local function cat(...)
  local out = {}
  for _, l in ipairs({...}) do for _, s in ipairs(l) do out[#out + 1] = s end end
  return out
end
local function rep(key, n, wait)
  local out = {}
  for _ = 1, n do out[#out + 1] = {"press", key, wait or 14} end
  return out
end
local OPEN = {{"journal"}, {"press", "SEL", 30}, {"press", "UP", 90}, {"press", "A", 240}}
local CLOSE = {{"press", "B", 30}, {"press", "B", 30}, {"press", "B", 60}}
local function tour(tag)
  -- from the chapter the log opens on: the grid, the Legends, Side Content, Badges; then closed
  return cat(
    {{"press", "B", 40}, {"shot", tag .. "_grid"}},
    {{"qcard", 4}, {"press", "A", 60}, {"shot", tag .. "_legends_top"}},
    rep("DOWN", 94), {{"press", "DOWN", 30}, {"shot", tag .. "_legends_95"}},
    {{"press", "A", 40}, {"shot", tag .. "_brute_bonnet_detail"}, {"press", "B", 30}},
    rep("DOWN", 5), {{"press", "DOWN", 30}, {"shot", tag .. "_legends_101"}},
    rep("DOWN", 8), {{"press", "DOWN", 30}, {"shot", tag .. "_legends_110"}},
    rep("DOWN", 8), {{"press", "DOWN", 30}, {"shot", tag .. "_legends_119"}},
    rep("DOWN", 4), {{"press", "DOWN", 30}, {"shot", tag .. "_legends_end"}},
    {{"press", "A", 40}, {"shot", tag .. "_locked_detail"}, {"press", "B", 30}},
    rep("UP", 4), {{"press", "UP", 30}, {"press", "A", 40}, {"shot", tag .. "_terapagos_detail"}, {"press", "B", 30}},
    {{"press", "B", 40}, {"qcard", 6}, {"press", "A", 60}},
    rep("DOWN", 44), {{"press", "DOWN", 30}, {"shot", tag .. "_side_45"}},
    rep("DOWN", 8), {{"press", "DOWN", 30}, {"shot", tag .. "_side_54"}},
    {{"press", "A", 40}, {"shot", tag .. "_booster_detail"}, {"press", "B", 30}},
    rep("UP", 3), {{"press", "UP", 30}, {"press", "A", 40}, {"shot", tag .. "_nemona_detail"}, {"press", "B", 30}},
    {{"press", "B", 40}, {"qcard", 7}, {"press", "A", 60}, {"shot", tag .. "_badges"}},
    CLOSE)
end
local NEMONA = 0x43E4
STEPS = cat(
  {{"boot"}, {"flags", NEMONA, 0x43D8, 0x43D9, 0x43DA, 0x43DC, 0x43DD, 0x43B5, 0x43B6, 0x43B8, 0x43B9, 0x43BA,
              0x43BB}},
  OPEN, {{"qlog", "first"}}, tour("save"),
  -- some marks: Scream Tail, Iron Bundle, Roaring Moon only seen, Brute Bonnet and Iron Valiant not even that,
  -- Great Tusk and Iron Treads caught; Nemona's rematch, the tablets' stake, both Booster Energy balls
  {{"dex9", clear = {985, 986, 991, 1005, 1006}, caught = {984, 990}, seen = {985, 991, 1005}},
   {"setup", set = {NEMONA, 0x43D8, 0x43DC, 0x43DD}}},
  OPEN, {{"qlog", "marked"}}, tour("marked"),
  -- every Legends row caught
  {{"dex9", legends = 119}},
  OPEN, {{"qlog", "all"}}, {{"press", "B", 40}, {"shot", "all_grid"}, {"qcard", 4}, {"press", "A", 60},
                            {"shot", "all_legends_top"}}, CLOSE,
  -- Nemona's rematch after the ending (test_story9's way): not set before, set once she is beaten
  {{"setup", fresh = true, set = {0x41D5, 0x43AC, 0x43AD, 0x43B1, 0x43B2, 0x43B3, 0x43B4, 0x43B5, 0x43B6,
                                  0x43B7, 0x43B8, 0x43B9, 0x43BA, 0x43BB, 0x43BC, 0x43BD, 0x43BE, 0x43C0, 0x43C1},
    clear = {NEMONA}, stage = 4},
   {"warp", 35, 97, 8, 6},
   {"expect", "nemona_home", here = {1}, off = {NEMONA}},
   {"walk", 8, 5, "on", "to_nemona"}, {"face", "UP"}, {"shot", "nemona"}, {"a"}, {"fight", "nemona_rematch", 35097},
   {"expect", "rematch_won", on = {NEMONA}},
   -- a wild Iron Hands (a big picture), the move menu and L
   {"script", {0xB6, 1208 & 0xFF, 1208 >> 8, 50, 0, 0, 0xB7, 0x02}, 10},
   {"lmove", "ltag"},
   {"flee", "ltag_run", 35097},
   {"finish"}})
