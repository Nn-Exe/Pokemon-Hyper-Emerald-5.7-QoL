-- objpal on the game itself: from the save, warp to ROAM_AT ("group,num,x,y": a map's first door), walk about
-- (the harness's "roam": the same keys on every build) and log each object's palette slot before and after. Run
-- with PALWATCH=1 (test_paldea.lua's watchdog: a sprite whose slot goes to another kind, or does not show its
-- tag's colours). tiles: objpal_tests.ps1.
local g, n, x, y = (os.getenv("ROAM_AT") or "0,1,10,10"):match("(%d+),(%d+),(%d+),(%d+)")
STEPS = {
  {"repel", 250}, {"seed", 0x5EED0B7A},
  {"warp", tonumber(g), tonumber(n), tonumber(x), tonumber(y)}, {"objpal", "arrived"}, {"shot", "arrived"},
  {"roam", "roam", tonumber(os.getenv("ROAM_FRAMES") or "2400")}, {"objpal", "after"}, {"shot", "after"},
  {"finish"},
}
