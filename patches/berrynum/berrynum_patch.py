"""Berry numbers in the Bag (Hyper Emerald v5.7): python berrynum_patch.py in.gba out.gba

The hack's own berries (items 704-727 and 762-765) showed as "No?2" in the Berries pocket: the game prints
item id - 132 in two digits. They now continue after Enigma (No43): Occa No44 ... Maranga No67, then No68-71.

ROM changes: four trampolines where the game computes that number - the hack's own item-name routine that
the Bag list uses, in two copies (10 bytes each at 0x08FD5E32 and 0x08FD7D4E), the vanilla list routine (10 bytes at 0x081C5422) and the Bag's
item-name routine (8 bytes at 0x081AB420) - to a stub in free space that replays what they
cover with the new number. Nothing else changes.
"""
import struct, sys, os, re
from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

HERE = os.path.dirname(os.path.abspath(__file__))
FREE = 0x00FE9000                       # past the Journal (ends 0x08FE84F0 and grows with its text: keep ~2.8 KB
                                        # clear), in the run free to 0x08FF0000. Was 0x08FE8400 until 2026-09-22.
BASE = 0x08000000 + FREE
GSTRINGVAR1 = 0x02021CC4
HACK_SITE = 0x00FD5E32                  # subs r1,#0x84; movs r3,#2; movs r2,#2; ldr r0,[pc,#0x8c]; ldr r6,[pc,#0x90]
HACK_ORIGINAL = bytes.fromhex("8439022302222348244e")
HACK2_SITE = 0x00FD7D4E                 # the second copy of the same routine, same bytes
LIST_SITE = 0x1C5422                    # ldr r0,[pc,#0x20]; adds r1,r4,#0; subs r1,#0x84; movs r2,#2; movs r3,#2
LIST_ORIGINAL = bytes.fromhex("0848211c843902220223")
NAME_SITE = 0x1AB420                    # ldr r0,[pc,#0x20]; adds r1,r5,#0; subs r1,#0x84; movs r2,#2
NAME_ORIGINAL = bytes.fromhex("0848291c84390222")
ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)


def thumb(src, addr):
    """Assemble, and check for Thumb-2 on a twin whose pools are nops so the linear sweep never stops."""
    code = bytes(ks.asm(src, addr)[0])
    twin = bytes(ks.asm(re.sub(r"^(\s*\w+:)\s*\.word\s+.*$", r"\1 mov r8, r8\n    mov r8, r8", src, flags=re.M),
                        addr)[0])
    assert len(twin) == len(code), "pool twin differs in size"
    dis = list(Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(twin, addr))
    assert sum(i.size for i in dis) == len(twin), "disassembly stopped early"
    assert not [i for i in dis if i.size == 4 and i.mnemonic != "bl"], "Thumb-2 encoding emitted"
    return code, dis


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    assert bytes(rom[HACK_SITE:HACK_SITE + 10]) == HACK_ORIGINAL, "the hack's berry-number code is not what this patch expects"
    assert struct.unpack_from("<I", rom, 0xFD5EC8)[0] == GSTRINGVAR1 and struct.unpack_from("<I", rom, 0xFD5ECC)[0] == 0x08008CC1
    assert bytes(rom[0xFD604E:0xFD6050]) == bytes.fromhex("3047"), "the bx r6 veneer moved"
    assert bytes(rom[HACK2_SITE:HACK2_SITE + 10]) == HACK_ORIGINAL, "the second copy is not what this patch expects"
    assert struct.unpack_from("<I", rom, 0xFD7DE4)[0] == GSTRINGVAR1 and struct.unpack_from("<I", rom, 0xFD7DE8)[0] == 0x08008CC1
    assert bytes(rom[0xFD7F6A:0xFD7F6C]) == bytes.fromhex("3047"), "the second copy's bx r6 veneer moved"
    assert bytes(rom[LIST_SITE:LIST_SITE + 10]) == LIST_ORIGINAL, "the Bag list's berry-number code is not what this patch expects"
    assert bytes(rom[NAME_SITE:NAME_SITE + 8]) == NAME_ORIGINAL, "the item-name routine's berry case is not what this patch expects"
    for site in (LIST_SITE, NAME_SITE):         # both ldr r0,[pc,#0x20] must load gStringVar1
        lit = ((0x08000000 + site + 4) & ~3) + 0x20 - 0x08000000
        assert struct.unpack_from("<I", rom, lit)[0] == GSTRINGVAR1

    src = open(os.path.join(HERE, "berrynum.s"), encoding="ascii").read()
    # keystone pads .align with 00 BF, a Thumb-2 nop; pad by hand with mov r8, r8 when the pool needs it
    for pad in ("", "    mov r8, r8"):
        code, dis = thumb(src.replace("PAD", pad), BASE)
        if not [i for i in dis if i.mnemonic == "nop"]:
            break
    else:
        raise AssertionError("could not pad the literal pool without a Thumb-2 nop")
    # hack_hook is first and hack2_hook follows its one-instruction branch; list_hook and name_hook start right
    # after the two jumps home through r12 (hack_common's and list_hook's)
    hack_hook, hack2_hook = BASE, BASE + 4
    ends = [i for i in dis if i.mnemonic == "bx" and i.op_str == "ip"]
    assert len(ends) == 2, "expected two bx r12 (hack_common, list_hook)"
    list_hook, name_hook = ends[0].address + 2, ends[1].address + 2
    assert [i.mnemonic for i in dis[:3]] == ["ldr", "b", "ldr"], "hack2_hook is not where expected"

    end = FREE + ((len(code) + 3) & ~3)
    assert set(rom[FREE:end]) == {0xFF}, "target region not free"
    rom[FREE:FREE + len(code)] = code
    # list site is 2 mod 4: the 10-byte form, ldr r3,[pc,#4]; bx r3; mov r8,r8; .word
    assert HACK_SITE % 4 == 2 and HACK2_SITE % 4 == 2 and LIST_SITE % 4 == 2 and NAME_SITE % 4 == 0
    rom[HACK2_SITE:HACK2_SITE + 10] = bytes.fromhex("014b1847c046") + struct.pack("<I", hack2_hook | 1)
    rom[HACK_SITE:HACK_SITE + 10] = bytes.fromhex("014b1847c046") + struct.pack("<I", hack_hook | 1)
    rom[LIST_SITE:LIST_SITE + 10] = bytes.fromhex("014b1847c046") + struct.pack("<I", list_hook | 1)
    rom[NAME_SITE:NAME_SITE + 8] = bytes.fromhex("004b1847") + struct.pack("<I", name_hook | 1)
    open(outp, "wb").write(rom)
    print("stub %d bytes @%08X; trampolines @%08X, @%08X, @%08X, @%08X" % (
        len(code), BASE, 0x08000000 + HACK_SITE, 0x08000000 + HACK2_SITE, 0x08000000 + LIST_SITE, 0x08000000 + NAME_SITE))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
