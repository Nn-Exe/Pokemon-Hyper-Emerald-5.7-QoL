-- Jacq before the hole (2026-10-11; the user: "before the blackhole paldea appears, we should at least have Jacq
-- standing there talking about taking students on trip or something ... like a foreshadowing"). He stands on his
-- tile in Mossdeep from the start of the game; the hole comes when Team Rainbow Rocket is beaten (0x41D5), and
-- he knows you then if you spoke before (0x43E2). STEPS_KIND (the environment):
--   early  no 0x41D5: Jacq there, no hole; his field-trip talk (0x43E2 set, nothing of the story's), the short
--          line the second time, nothing to press where the hole will be. Then 0x41D5: the hole is there on the
--          way in, he says "You! The Trainer from before!" and asks you in (0x43AC, stage 1), then his waiting line.
--   late   0x41D5 from the start, never met: his first talk as it always was (0x43AC, stage 1, 0x43E2 clear).
--   done   after the ending (stage 4): the hole, no Jacq.
--   make   on the build before this one: a save made in Mossdeep before Team Rainbow Rocket (nothing of ours
--          there then). load: continued on this build: Jacq stands there, and talks.
-- (Built-in placements: Jacq 70,32, the hole 68,32.)
local kind = os.getenv("STEPS_KIND") or "early"
local SAVE = {
  {"menutop"}, {"press", "START", 90},
  {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15},
  {"press", "A", 60}, {"mash", "save", 6},
}
if kind == "early" then
  STEPS = {
    {"setup", fresh = true, clear = {0x41D5}, stage = 0},
    {"warp", 0, 6, 70, 33},
    {"expect", "jacq_and_no_hole", map = 6, here = {30}, gone = {31, 32, 33, 34}},
    {"shot", "1_before_the_hole"},
    {"face", "UP"}, {"a"}, {"press", "B", 1}, {"shot", "2_field_trip"}, {"mash", "early", 6},
    {"expect", "met_early", on = {0x43E2}, off = {0x43AC}, stage = 0},
    {"face", "UP"}, {"a"}, {"press", "B", 1}, {"shot", "3_second_time"}, {"mash", "early_again", 6},
    {"walk", 68, 33, "on", "where_the_hole_will_be"}, {"face", "UP"}, {"a"}, {"press", "B", 60},
    {"lockstate", "no_hole"}, {"expect", "still_nothing", off = {0x43AC}, stage = 0, map = 6},
    {"setup", set = {0x41D5}},
    {"warp", 0, 6, 70, 33},
    {"expect", "jacq_and_the_hole", map = 6, here = {30, 31}, gone = {32, 33, 34}},
    {"shot", "4_the_hole_is_open"},
    {"face", "UP"}, {"a"}, {"press", "B", 1}, {"shot", "5_he_knows_you"}, {"mash", "known", 6},
    {"expect", "asked_in", on = {0x43AC, 0x43E2}, stage = 1},
    {"face", "UP"}, {"a"}, {"press", "B", 1}, {"shot", "6_waiting"}, {"mash", "again", 6},
    {"walk", 68, 33, "on", "to_hole"}, {"face", "UP"}, {"a"}, {"mash", "hole", 35089},
    {"expect", "on_the_wall", map = 35089},
    {"finish"},
  }
elseif kind == "late" then
  STEPS = {
    {"setup", fresh = true, set = {0x41D5}, stage = 0},
    {"warp", 0, 6, 70, 33},
    {"expect", "jacq_and_the_hole", map = 6, here = {30, 31}},
    {"face", "UP"}, {"a"}, {"press", "B", 1}, {"shot", "1_first_talk"}, {"mash", "intro", 6},
    {"expect", "asked_in", on = {0x43AC}, off = {0x43E2}, stage = 1},
    {"finish"},
  }
elseif kind == "done" then
  STEPS = {
    {"setup", fresh = true, set = {0x41D5, 0x43AC, 0x43C1}, stage = 4},
    {"warp", 0, 6, 70, 33},
    {"expect", "the_hole_alone", map = 6, here = {31}, gone = {30, 32, 33, 34}},
    {"shot", "1_after_the_ending"},
    {"finish"},
  }
elseif kind == "make" then
  STEPS = {
    {"setup", fresh = true, clear = {0x41D5}, stage = 0},
    {"warp", 0, 6, 70, 33},
    {"expect", "nothing_of_ours_before", map = 6, gone = {30, 31, 32, 33, 34}},
  }
  for _, st in ipairs(SAVE) do STEPS[#STEPS + 1] = st end
  STEPS[#STEPS + 1] = {"finish"}
else                                                         -- load
  STEPS = {
    {"shot", "1_continued"},
    {"expect", "jacq_now", map = 6, pos = {70, 33}, here = {30}, gone = {31, 32, 33, 34}},
    {"face", "UP"}, {"a"}, {"press", "B", 1}, {"shot", "2_field_trip"}, {"mash", "early", 6},
    {"expect", "met_early", on = {0x43E2}, off = {0x43AC}, stage = 0},
    {"finish"},
  }
end
