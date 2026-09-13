# PC item storage sort (NOT applied, NOT verified)

START in the PC's Withdraw/Toss item list would sort the 50 PC item slots (type -> name -> amount, same cycle as the
bag sort) by hooking ItemStorage_ProcessInput (0x0816C30C) and reusing the game's own swap-finish routine
(0x0816C5A0) to redraw the list. The patcher builds and the injected code disassembles cleanly, but the feature was
never exercised in the emulator: the test saves start in rooms without a PC and the scripted walk to a Pokémon Center
kept failing, so it was shelved. It is not part of the release patch or the rebuild chain. Treat it as a starting
point, not a finished feature.
