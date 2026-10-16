-- roamfix: Tornadus and Thundurus stay in Sinnoh after Continue. Steps for patches/paldea/test_paldea.lua (the
-- harness: STEPSFILE = "../roamfix/test_roamfix.lua"), on the game itself with its late-game save.
--   1. The Valley Windworks researcher (36/54) starts the roaming rain (flags and Pokedex put back to before
--      it): Tornadus, species 694, on a Sinnoh route (map group 36). The News Tracker names that route.
--   2. A warp (as a Fly) moves it; the tracker follows. Put on your route, it is met in the grass within 60
--      battles (one in four), and moves on after the battle.
--   3. Save, reset, Continue: still species 694 in map group 36, the tracker says Sinnoh, and it is met again.
--      (Before the patch: map group 0, "in Hoenn on Route 130" - with OLD=1 that is what is expected.)
--   4. Thundurus (mode 3 of the same special) through a save and a reset: group 36. Latios (mode 1): group 0,
--      before and after - the Hoenn roamers are left alone.
local OLD = os.getenv("OLD") == "1"
local SINNOH = (not OLD) and 36 or 0
local function start(mode) return {0x16, 0x04, 0x80, mode, 0x00, 0x25, 0x2B, 0x01, 0x02} end   -- setvar 0x8004; special 299
local SAVE = {
  {"repel", 250}, {"menutop"}, {"press", "START", 90},
  {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15},
  {"press", "A", 60}, {"mash", "save", 36015},
}
STEPS = {
  {"roamer", "in_the_save"},
  {"clearroamer"},
  {"script", {0x2A, 0xDE, 0x42, 0x2A, 0xE0, 0x42, 0x2A, 0xE1, 0x42, 0x02}, 30},   -- clearflag 0x42DE, 0x42E0, 0x42E1
  {"dex", clear = {641, 642, 645}},
  {"warp", 36, 54, 10, 13}, {"shot", "windworks"},
  {"face", "UP"}, {"a"}, {"mash", "researcher", 36054},
  {"expect", "researcher_told", on = {0x42DE}, off = {0x42E0, 0x42E1}},
  {"roamer", "started", active = 1, species = 694, group = 36},
  {"tracker", "started"},
  {"warp", 36, 15, 44, 5}, {"roamer", "after_warp", active = 1, species = 694, group = 36},
  {"tracker", "after_warp"},
  {"setroamer"}, {"tracker", "on_my_route"},
  {"repel", 0},
  {"hunt", "tornadus", 694, 60},
  {"roamer", "after_battle", active = 1, species = 694, group = 36},
  {"tracker", "after_battle"},
}
local function add(list) for _, st in ipairs(list) do STEPS[#STEPS + 1] = st end end
add(SAVE)
add({
  {"reset"}, {"boot"},
  {"roamer", "after_reload", active = 1, species = 694, group = SINNOH},
  {"tracker", "after_reload"},
  {"warp", 36, 15, 44, 5}, {"roamer", "reload_then_warp", active = 1, species = 694, group = SINNOH},
  {"tracker", "reload_then_warp"},
})
if not OLD then
  add({{"setroamer"}, {"repel", 0}, {"hunt", "tornadus_again", 694, 60},
       {"roamer", "after_2nd_battle", active = 1, species = 694, group = 36}})
end
-- Thundurus
add({{"script", start(3), 60}, {"roamer", "thundurus", active = 1, species = 695, group = 36}, {"tracker", "thundurus"}})
add(SAVE)
add({{"reset"}, {"boot"}, {"roamer", "thundurus_reload", active = 1, species = 695, group = SINNOH},
     {"tracker", "thundurus_reload"}})
-- Latios: a Hoenn roamer stays one
add({{"script", start(1), 60}, {"roamer", "latios", active = 1, species = 408, group = 0}, {"tracker", "latios"}})
add(SAVE)
add({{"reset"}, {"boot"}, {"roamer", "latios_reload", active = 1, species = 408, group = 0}, {"tracker", "latios_reload"},
     {"warp", 36, 15, 44, 5}, {"roamer", "latios_warp", active = 1, species = 408, group = 0},
     {"finish"}})
