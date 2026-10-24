"""Egg moves in the Move Relearner (Hyper Emerald v5.7). Apply after iconnight, before kitakami, so Kitakami's editor
builds (on the game before Kitakami) have it too; no other step touches these bytes, so anywhere in the chain works.
usage: python eggrelearn_patch.py <in.gba> <out.gba>

The user (2026-10-21), asked whether an NPC teaches egg moves (none does: every tutor teaches a fixed list, and the
relearner lists level-up moves only): "yeah in party relearner". The party menu's Moves (patches/relearner) opens
the game's own Move Relearner screen, the one the Fallarbor tutor opens, so both now list the egg moves too.

The list (eggrelearn.s): the level-up moves as before (GetMoveRelearnerMoves 0x0806E0B4 -> the hack's 0x09D6A9D9, at
most 24), then the egg moves of the Pokemon's species, of each species it evolved from, and of the species the game
hatches for it, each once and none it knows. Walking back matters: Azumarill gets Marill's list and Azurill's,
Blissey Chansey's and Happiny's (nine lists sit on a middle stage). The walk is the game's own rule (its egg species
routine 0x09F00600, which breeding uses). When the Pokemon evolved from nothing in the table, that routine is called
too, for the cases it hard-wires (Jolteon, Leafeon, Glaceon, Sylveon -> Eevee; Manaphy -> Phione; Hisuian Typhlosion
-> Cyndaquil); for any other species it would only walk the table again (check: no species' list changes).
Time (GetNumberOfRelearnableMoves, measured with breakpoints): 0.1-0.5 frames for most, 1.3-2 for a Pokemon that
evolves from nothing (the hack's routine scans the table slowly), 1.4-1.6 for a three-stage Gen 9 line (the table's
end): the Fallarbor tutor's party screen counts each slot once, the relearner's list is built behind its fade.

Room: the screen's struct (sMoveRelearnerStruct 0x0203BC34) holds the vanilla 25 moves and 25 menu items, so the
egg moves of 56 species would not fit at a high level (Pikachu, the Eeveelutions, Donphan, Victreebel ...; the
longest list in the game is Donphan's 36). Its allocation goes from 0x118 to 0x320 bytes (both sites: CB2_InitLearnMove
0x081606B4 and the way back from the summary screen 0x08160754) and the menu items move to +0x118, room for 64 moves
and Cancel. The items have two readers, both replaced through a trampoline on their first instruction:
CreateLearnableMovesList (0x08161280) and GetCurrentSelectedMove (0x08161054). GetNumberOfRelearnableMoves (the word
at 0x0806E260, the Fallarbor tutor's ABLE / NOT ABLE and "no move to teach") counts the same list.

Code: 0x08FFC900.. (0x08FFC900..0x08FFCC00 kept), inside the blank run 0x08FFA244..0x08FFD5A0 (blank in the hack's
own ROM too, from 0x08FF2454). No word anywhere in the game reads as an address inside 0x08FFC8F8..0x08FFCC02 at any
byte offset: the nearest are 0x08FFC8F7 below (at 0x080C1811, an odd address in code) and 0x08FFCC02 above (at
0x095FEA4B, odd); the patcher checks its own window again. Read watchpoints on the game without it:
_testrun/space/eggrelearn_watch.ps1.
"""
import os, re, struct, sys

from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

HERE = os.path.dirname(os.path.abspath(__file__))
ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)

FREE, FREE_END = 0x00FFC900, 0x00FFCC00
BASE = 0x08000000 + FREE
CREATE, SELECTED = 0x08161280, 0x08161054          # CreateLearnableMovesList, GetCurrentSelectedMove
COUNT_WORD, COUNT_WAS = 0x0806E260, 0x09D6A9E1      # GetNumberOfRelearnableMoves' trampoline word
ALLOCS = (0x081606B4, 0x08160754)                   # movs r0, #0x8c; lsls r0, r0, #1 (0x118) before AllocZeroed
SIZE = 0x118 + 8 * 65                               # + 65 menu items at +0x118: 64 moves and Cancel
EXPECT = [
    # CB2_InitLearnMove / CB2_InitLearnMoveReturnFromSelectMove: ldr r6/r5, =sMoveRelearnerStruct; the size;
    # bl AllocZeroed
    (0x081606B2, "1b4e8c204000a0f648fa"),
    (0x08160752, "1d4d8c204000a0f6f8f9"),
    # GetCurrentSelectedMove: menuItems[listRow + listOffset].id (+0x4C), its pool
    (0x08161054, "054802680549488809884018c0004c32121810687047000034bc030238bc0302"),
    # CreateLearnableMovesList and its pool: GetMoveRelearnerMoves into +0x12, gMoveNames (0x09AB2EC4), the items at
    # +0x48, GetMonData nickname, StringCopy_Nickname(gStringVar1), gText_Cancel, LoadMoveRelearnerMovesList
    (0x08161280, "f0b54f464646c0b483b0364c2168081c4430027864205043334a801812310cf709ff21688826760089190870002520688019007885421eda"
                 "a0460d2084462b4a914647463c68eb00221c4832d2186800211c12310918088867464743381c48441060201c4c30c018098801600135a019"
                 "00788542e5db1b4c206844300178642048431949401802216a4609f705f918486946a7f6fdfb226888256d0053191878c000111c48310918"
                 "124808601878c0004c3212180220404210601878013018702168081c48304919097871f0bdfa2168094a8918087003b018bc9846a146f0bc"
                 "01bc004734bc0302ec440202c42eab09c41c0202f08c5e0811010000"),
    # GetMoveRelearnerMoves / GetNumberOfRelearnableMoves: trampolines into the hack
    (0x0806E0B4, "004a1047d9a9d609"),
    (0x0806E25C, "00490847e1a9d609"),
    # the hack's level-up list (stops at 24: cmp r4, #0x17 at 0x09D6A998) and the two wrappers
    (0x09D6A93E, "f0b5002685b00291028c224b9200d3583821002203930700cdf7bdfb340003061b0e019303237343039ad3185d781a782d0215432bd09b78"
                 "ff2b28d0019a9a4221d3bb8dab421ed0fb8dab421bd03b8eab4218d07b8eab4215d0172c13d8029b002b03d101342406240e10e022000299"
                 "2800fff7b8ff002805d1029a6300013424069d52240e01363606360ecae7200005b0f0bdc046000daf0910b5fff7b0ff10bd10b50021fff7"
                 "abff"),
    # the hack's egg species (species, mode): the hard-wired cases, the walk back through the evolution table
    # (0x0806D140's table, species 1..0x57F, method byte <= 0xF9), then mode 1's random picks
    (0x09F00600, "f8b5314bc3181b041b0c012b01d9872801d18520f8bd2d4b9842fad02c4b98423bd02c4b984230d001242b4b2b4f1e68a3001b19db00f318"
                 "1d0028359a88824225d008339d42f9d101342404240cbc42eed90029ded01d2821d020281fd00300833bff3b1b041b0c012b23d91c4bc318"
                 "002b03d01b4bc318002bcbd11a4b00f081fbc30714d51948c4e79b20c2e71a78f92ad6d820000124cae71548bae7124b00f070fb03001d20"
                 "db07b3d40330b1e71048afe70c4b00f065fb012318408423ff33181aa6e7c046f5fdfffff10200001f0200004304000040d106087f050000"
                 "c3fbffff66fbffffcdf506083d0400001e0200009a040000"),
    # LoadMoveRelearnerMovesList(items, n): the template's items and count, no limit
    (0x081D28C8, "f0b509040c0c064b1a1c0649e0c9e0c2e0c9e0c29c811860052c05d8dc8105e01063000348556208"),
]


def thumb(src, addr):
    """Assemble, and check for Thumb-2 on a twin whose pools are nops so the linear sweep never stops."""
    code = bytes(ks.asm(src, addr)[0])
    twin = bytes(ks.asm(re.sub(r"^(\s*\w+:)\s*\.word\s+.*$", r"\1 mov r8, r8\n    mov r8, r8", src, flags=re.M),
                        addr)[0])
    assert len(twin) == len(code), "pool twin differs in size"
    dis = list(Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(twin, addr))
    assert sum(i.size for i in dis) == len(twin), "disassembly stopped early at %08X" % (
        addr + sum(i.size for i in dis))
    bad = [i for i in dis if i.size == 4 and i.mnemonic != "bl"]
    assert not bad, "Thumb-2 encoding emitted: %s" % [(i.mnemonic, i.op_str) for i in bad]
    assert not [i for i in dis if i.mnemonic == "nop"], "a Thumb-2 nop (00 BF) slipped in: use mov r8, r8"
    return code


def assemble():
    src = open(os.path.join(HERE, "eggrelearn.s"), encoding="ascii").read()
    for pad in ("", "    mov r8, r8"):       # the pool on a word without the assembler's own (Thumb-2) padding
        try:
            code = thumb(src.replace("PADA", pad), BASE)
            break
        except AssertionError as e:
            if "nop" not in str(e):
                raise
    else:
        raise AssertionError("eggrelearn's pool")
    # the entry points, by their first instructions (each is the only one of its kind): create_list is the first
    # function; selected_move opens ldr r0, =struct; ldr r2, [r0]; ldr r1, =menu state; ldrh r0, [r1, #2];
    # count_moves opens push {lr}; sub sp, #0x80
    dis = [(i.address, i.mnemonic, i.op_str) for i in Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(code, BASE)]
    at = {a: k for k, (a, _, _) in enumerate(dis)}
    assert dis[0][1:] == ("push", "{r4, r5, r6, r7, lr}") and dis[1][1:] == ("sub", "sp, #0x90")
    sel = [a for a, m, s in dis if (m, s) == ("ldrh", "r0, [r1, #2]")]
    cnt = [a for a, m, s in dis if (m, s) == ("sub", "sp, #0x80")]
    assert len(sel) == 1 and len(cnt) == 1, (sel, cnt)
    k = at[sel[0]]
    assert [d[1:] for d in dis[k - 3:k]][1] == ("ldr", "r2, [r0]") and dis[k - 3][2].startswith("r0, [pc")
    assert dis[at[cnt[0]] - 1][1:] == ("push", "{lr}")
    entries = {"create_list": BASE, "selected_move": dis[k - 3][0], "count_moves": dis[at[cnt[0]] - 1][0]}
    return code, entries


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    o = lambda a: a - 0x08000000
    u32 = lambda a: struct.unpack_from("<I", rom, o(a))[0]
    for a, hexs in EXPECT:
        assert bytes(rom[o(a):o(a) + len(bytes.fromhex(hexs))]) == bytes.fromhex(hexs), \
            "the game's code at %08X is not as expected (already applied?)" % a
    assert u32(0x08000148) == u32(0x0816136C), "the ROM header's move names are not the relearner's"
    evo, egg = u32(0x0806D140), u32(0x080703F0)
    assert 0x08000000 <= evo < 0x0A000000 and 0x08000000 <= egg < 0x0A000000
    assert struct.unpack_from("<H", rom, o(egg))[0] == 20000 + 1, "the egg move table does not start at Bulbasaur"
    held = [0x08000000 + m.start() for m in re.finditer(re.escape(struct.pack("<I", COUNT_WAS)), bytes(rom))]
    assert held == [COUNT_WORD], "the count's address is held elsewhere too: %s" % ["%08X" % a for a in held]

    code, entries = assemble()
    end = FREE + len(code)
    assert end <= FREE_END and set(rom[FREE:FREE_END]) == {0xFF}, "target region not free"
    for m in re.finditer(rb"(?s).[\xc9-\xcb]\xff\x08", bytes(rom)):     # at any byte offset, not only words
        v = struct.unpack_from("<I", rom, m.start())[0]
        assert not BASE <= v < 0x08000000 + FREE_END, "%08X reads as an address in the target (%08X)" % (
            0x08000000 + m.start(), v)
    rom[FREE:end] = code
    size = bytes(ks.asm("movs r0, #%d\n lsls r0, r0, #2" % (SIZE >> 2), 0)[0])
    assert SIZE % 4 == 0 and SIZE >> 2 < 256 and len(size) == 4
    for a in ALLOCS:
        rom[o(a):o(a) + 4] = size
    for site, name in ((CREATE, "create_list"), (SELECTED, "selected_move")):
        assert site % 4 == 0
        rom[o(site):o(site) + 8] = bytes.fromhex("004b1847") + struct.pack("<I", entries[name] | 1)
    struct.pack_into("<I", rom, o(COUNT_WORD), entries["count_moves"] | 1)
    open(outp, "wb").write(rom)
    print("eggrelearn: %08X..%08X (create_list %08X, selected_move %08X, count_moves %08X); struct 0x%X bytes"
          % (BASE, 0x08000000 + end, entries["create_list"], entries["selected_move"], entries["count_moves"], SIZE))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
