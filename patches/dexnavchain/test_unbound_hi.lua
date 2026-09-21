-- Second session on the save test_unbound.lua left: the search level must load back from flash, then SL 150 /
-- chain 48 are injected to exercise the 100+ odds row and the 50th-encounter shiny burst (27 rolls).
NAME = "hi"
PLAN = {"win", "win", "win", "win", "win", "win"}
function INJECT()
  emu:write8(0x0203A660 + 24, 150); emu:write16(0x0203A660 + 4, 48)
  w("injected SL 150, chain 48 (next reroll uses them)")
end
dofile((DIR or "./") .. "test_unbound.lua")
