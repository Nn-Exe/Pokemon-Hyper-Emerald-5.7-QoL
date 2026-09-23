@ Rare Candy NPC in Petalburg City's Poke Mart (map 8/6).
@ No assembly: the NPC is an extra entry in a relocated copy of the map's object array, plus this vanilla
@ script bytecode written next to it by candynpc_patch.py.
@
@   69        lock
@   5A        faceplayer
@   44 4400 0100   giveitem item=68 (Rare Candy), amount=1   (shows the game's own "obtained" message)
@   6B        release
@   02        end
@
@ Script opcode handlers: lock 0x0809AAC5, faceplayer 0x0809A9A5, giveitem 0x080999A0,
@ release 0x0809AB45, end 0x080992D4. Both operands of giveitem are halfwords (the handler reads two).
