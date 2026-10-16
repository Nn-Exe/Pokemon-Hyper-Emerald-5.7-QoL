# Playing the story by hand (test_play.lua)

`../test_play.lua` plays a plan - a Lua file returning a list of actions (walk, edge, talk, enter, expect, grind,
heal, settle, save, ...; the file's header lists them all) - from New Game (`NEWGAME=1`) or a save, the way a player
would: a path over the live map (walls, doors, ledges, heights, people), A through text, a battle player (the move
that hurts most, Run when nothing can), a heal after a battle that leaves the lead under half HP or out of attacks,
the strongest Pokemon kept in front. It logs every var 0x4000-0x40FF and every flag the game's scripts change.

Run one plan with `../runner.py` and a job like
`{"name": "c01", "rom": "<build>", "sav": null, "lua": ".../test_play.lua", "env": {"NEWGAME": "1", "PLAN": ".../ch01.lua"}}`;
the next chapter's `sav` is the previous run's `game.sav` (each plan ends with an in-game save).

- `ch01.lua` New Game -> Birch, the starter, the lab (flag 0x0860); `ch02.lua` the rival on Route 103, the
  Pokedex (0x0861); `ch03a.lua` Petalburg (Norman, Wally), the Timeless Woods round the Cut tree, Route 104,
  Petalburg Woods (the Aqua grunt); `ch03b.lua` training, Rustboro, Roxanne (0x0867) - not passed yet.
- `mapinfo.py <rom> g.n` a map's people, doors, triggers, signs; `mapgrid.py <rom> g.n [-z]` the map as text
  (walls, grass, water, ledges, doors, people; heights); `bfs.py <rom> g.n x0,y0 x1,y1` the walker's rules offline.
- The route of every Journal step (who sets each flag, where, on what conditions) comes from
  `tools/romdata/prereq.py` over a script index built from the build itself (`dump_tables`, `dump_maps`,
  `scripts.py` with `HE_ROM` set).
