-- The time rift (2026-10-12): the craters' two time objects, a pale crystal until then, are a shimmering tear in
-- the air - cold blue in the past crater (35/90), warm amber in the future one (35/91). Steps for test_paldea.lua.
-- STEPS_KIND (the environment):
--   look   each rift in each time: five pictures a few frames apart (the shimmer: rift_shimmer.py counts the
--          different ones), every sprite listed (the rift must be 32 x 32: "shape 0 size 2"); then through each
--          rift and back - the same tile in the other time. Run with PALWATCH=1 and BADCOPY (the rift's picture is
--          copied every 9 frames: every copy must be a good one).
--   busy   the rift met after a walk past the crater's other kinds of thing (the palettes given out by tag: six
--          slots), in the past with the legends standing (after the story). Run with PALWATCH=1.
--   make   on the build before: a save made below the dais's time CRYSTAL. load: continued on this build - the
--          rift stands there at once (the build's stamp is another), and takes you through.
-- (Built-in placements: the rifts at 26,30 and 45,20; you stand on the tile below.)
local kind = os.getenv("STEPS_KIND") or "look"
local SPOTS = {{26, 30, "dais"}, {45, 20, "terrace"}}
local function add(list, more) for _, s in ipairs(more) do list[#list + 1] = s end return list end
local function look(list, map, x, y, label)
  add(list, {{"warp", 35, map, x, y + 1}, {"press", "B", 40}})
  for k = 1, 5 do add(list, {{"shot", string.format("%s_%d", label, k)}, {"press", "B", 7}}) end
  return add(list, {{"sprites", label}})
end
if kind == "look" then
  STEPS = {{"setup", fresh = true, set = {0x41D5, 0x43AC, 0x43B5, 0x43B6, 0x43B7, 0x43BC}, stage = 2}}
  for _, sp in ipairs(SPOTS) do
    look(STEPS, 90, sp[1], sp[2], "past_" .. sp[3])
    add(STEPS, {{"face", "UP"}, {"a"}, {"mash", "through_" .. sp[3], 35091},
                {"expect", "future_same_tile_" .. sp[3], map = 35091, pos = {sp[1], sp[2] + 1}}})
    look(STEPS, 91, sp[1], sp[2], "future_" .. sp[3])
    add(STEPS, {{"face", "UP"}, {"a"}, {"mash", "back_" .. sp[3], 35090},
                {"expect", "past_same_tile_" .. sp[3], map = 35090, pos = {sp[1], sp[2] + 1}}})
  end
  add(STEPS, {{"finish"}})
elseif kind == "busy" then
  -- after the story: Koraidon, the three Paradox legends of the past and the crystals are all on the map
  STEPS = {
    {"setup", fresh = true, set = {0x41D5, 0x43AC, 0x43B1, 0x43B2, 0x43B3, 0x43B4, 0x43B5, 0x43B6, 0x43B7, 0x43BC,
                                   0x43BD, 0x43C1}, stage = 4},
    {"warp", 35, 90, 14, 14}, {"objpal", "arrived"},
    {"walk", 37, 44, "on", "picnic"}, {"objpal", "picnic"},
    {"walk", 33, 20, "on", "pond"}, {"objpal", "pond"},
    {"walk", 26, 31, "on", "to_the_dais"}, {"objpal", "dais"}, {"shot", "dais_after_the_walk"}, {"sprites", "dais"},
    {"walk", 45, 21, "on", "to_the_terrace"}, {"objpal", "terrace"}, {"shot", "terrace_after_the_walk"},
    {"face", "UP"}, {"a"}, {"mash", "through", 35091},
    {"walk", 26, 31, "on", "future_dais"}, {"objpal", "future_dais"}, {"shot", "future_dais_after_the_walk"},
    {"finish"},
  }
elseif kind == "make" then
  STEPS = {
    {"setup", fresh = true, set = {0x41D5, 0x43AC, 0x43B5, 0x43B6, 0x43B7, 0x43BC}, stage = 2},
    {"warp", 35, 90, 26, 31}, {"shot", "the_crystal_before"}, {"sprites", "before"},
    {"menutop"}, {"press", "START", 90},
    {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15},
    {"press", "A", 60}, {"mash", "save", 35090},
    {"finish"},
  }
else                                                         -- load
  STEPS = {
    {"shot", "continued"}, {"sprites", "continued"},
    {"expect", "below_the_rift", map = 35090, pos = {26, 31}, here = {1}},   -- (the other rift is too far to be made)
    {"face", "UP"}, {"a"}, {"mash", "through", 35091},
    {"expect", "future_same_tile", map = 35091, pos = {26, 31}},
    {"finish"},
  }
end
