"""A fusion's slot no longer stays "taken" with nothing to split (Hyper Emerald v5.7).
usage: python fusionfix_patch.py <in.gba> <out.gba>

Reported: "how to fuse Necrozma and Solgaleo - when I select Necrozma it says multiple fusions are not allowed".

How the game does it. The N-Solarizer, the N-Lunarizer and the Unity Reins run one script (0x094A27C0) whose callasm
0x08C60D31 is a trampoline (ldr r0,[pc,#0]; bx r0; .word 0x09F00F59) to the routine that does the work; the DNA
Splicers' script (0x08FD6554) calls 0x08FD7021. The Pokemon that goes inside is kept whole (100 bytes) in the
saved overflow stream: 0x0203D5E0 for Necrozma (Solgaleo or Lunala - one slot for both items, so one fused Necrozma
at a time), 0x0203D644 for Calyrex (Glastrier or Spectrier), 0x0203D800 for Kyurem (Reshiram or Zekrom). The
Necrozma / Calyrex routine answers in var 0x800D: 0 "can't be combined", 1 done, 2 "You are missing a <partner>",
3 "Multiple fusions are not allowed!", 4 choose a move to forget, 5 party full. It answers 3 when a fusion is asked
for and the slot's species (+0x20) is not 0, or a split is asked for and the slot's species is not the partner's
(844 Solgaleo for Dusk Mane, 845 Lunala for Dawn Wings). Kyurem's answers 3 when the slot's first word is not 0.

Three ways a slot said "taken" with nothing the player could split (all reproduced, see test_fusionfix.lua):
  1. v1.5's Hyper Training kept a scratch byte at 0x0203D600, the low byte of the Necrozma slot's species, and
     rewrote its low six bits on every look at the EV-IV Display or an IV judge. The byte is saved; v1.6 moved the
     scratch but left what was in the save. With nothing stored the species reads 1-63: no fusion, with either
     item, on any version since. With Solgaleo or Lunala stored it reads 832-895: no split.
  2. NEW GAME does not empty the slots (the original game's): started over a save that has a fusion, the new game
     inherits the stored Pokemon and can never fuse that one.
  3. The fused Pokemon is gone - released, or case 2 on a save made before this patch.

The patch (fusionfix.s; three pointer words change):
  * the Necrozma / Calyrex trampoline's word -> fx_entry, the DNA Splicers script's callasm -> fx_dna. Before the
    game's routine runs: an empty Necrozma slot gets species 0 back; on a split, a stored species in 832-895
    becomes the chosen form's partner; and when a fusion is asked for while the slot is taken, the slot is emptied
    if the player has none of the forms that could hold what is in it (the game's own "has this species": party,
    PC, Day Care). A slot whose fused Pokemon the player still has is left byte for byte, so a real second fusion
    is refused as before.
  * ClearBag's trampoline (bagslots'; NewGameInitData is its only caller) -> fx_newgame, which empties the three
    slots and goes on to what the trampoline pointed at.

Order: after bagslots (it chains on ClearBag's trampoline); before zhtext, which stays last.
"""
import os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "sinnohmap"))
import sinnohmap_patch as SM                    # the Thumb check

B = 0x08000000
FREE, FREE_END = 0x01FDCD00, 0x01FDCF00         # the hack's tail, after zhtext's stub and names (..0x09FDCC80)
TRAMP = 0x00C60D30                              # ldr r0,[pc,#0]; bx r0; .word fusion
FUSION = 0x09F00F59
DNA_CALL, DNA = 0x00FD655D, 0x08FD7021          # the DNA Splicers script's callasm
CLEARBAG = 0x000D7094                           # ldr r3,[pc,#0]; bx r3; .word clear_bag (bagslots)
OWNED = 0x09F03739                              # r0 = species -> 1 if in the party, a PC box or the Day Care
EVOS, NAMES_PTR = 0x00F387C0, 0x144
NAMES = {853: "Necrozma", 1068: "Dusk Mane", 1069: "Dawn Wings", 1070: "U-Necrozma", 1090: "U-Necrozma",
         844: "Solgaleo", 845: "Lunala", 1098: "Calyrex", 1099: "Calyrex-IR", 1100: "Calyrex-SR",
         696: "Reshiram", 697: "Zekrom", 995: "Kyurem-W", 996: "Kyurem-B"}


def name(rom, sid):
    o = struct.unpack_from("<I", rom, NAMES_PTR)[0] - B + 11 * sid
    out = ""
    for c in rom[o:o + 11]:
        if c == 0xFF:
            break
        out += (chr(65 + c - 0xBB) if 0xBB <= c <= 0xD4 else chr(97 + c - 0xD5) if 0xD5 <= c <= 0xEE
                else {0x00: " ", 0xAE: "-"}.get(c, "?"))
    return out


def bl_target(rom, o):
    h1, h2 = struct.unpack_from("<HH", rom, o)
    assert (h1 & 0xF800) == 0xF000 and (h2 & 0xF800) == 0xF800, "%08X is not a bl" % (B + o)
    off = ((h1 & 0x7FF) << 12) | ((h2 & 0x7FF) << 1)
    return B + o + 4 + (off - 0x800000 if off & 0x400000 else off)


def build(inp, outp):
    with open(inp, "rb") as f:
        rom = bytearray(f.read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    at = lambda o, hexs: bytes(rom[o:o + len(bytes.fromhex(hexs))]) == bytes.fromhex(hexs)
    u32 = lambda o: struct.unpack_from("<I", rom, o)[0]
    for sid, want in NAMES.items():
        assert name(rom, sid) == want, "species %d is %r, not %s" % (sid, name(rom, sid), want)

    # Necrozma / Calyrex: the script's two callasm go through the trampoline; nothing else enters the routine
    assert at(TRAMP, "00480047") and u32(TRAMP + 4) == FUSION, "the fusion callasm is not the game's trampoline"
    assert at(0x014A27D5, "23310dc608") and at(0x014A2826, "23310dc608"), "the fusion script changed"
    assert at(FUSION - 1 - B, "f0b556464d4644465f46f0b4"), "the fusion routine moved"
    assert u32(0x01F012D8) == 0x0203D5E0 and u32(0x01F01300) == 0x0203D644, "the slots are not where they were"
    # by its literals: both Necrozma items use the first slot, with partners 844 / 845 and forms 1068 / 1069
    assert (u32(0x01F012CC), u32(0x01F012D0), u32(0x01F012F4), u32(0x01F012F8)) == (853, 1068, 1069, 845)
    assert (u32(0x01F012A8), u32(0x01F012B0), u32(0x01F012B4)) == (1098, 1099, 1100), "Calyrex's forms moved"
    assert at(0x01F0124A, "00220b210098") and at(0x01F01254, "002861d0"), "the 'already stored' check changed"
    assert at(0x01F01262, "00220b210098") and at(0x01F0126C, "019b9842f2d1"), "the split's partner check changed"
    refs = [k for k in range(0, len(rom) - 3, 4) if u32(k) in (FUSION, FUSION - 1)]
    assert refs == [TRAMP + 4], "the routine has other callers: %s" % ["%08X" % (B + k) for k in refs]
    # the Ultra forms of the two fused ones (evolution table, method 250)
    for sid, ultra in ((1068, 1070), (1069, 1090)):
        assert struct.unpack_from("<HHH", rom, EVOS + sid * 40) == (250, 0, ultra), "Ultra Necrozma's row moved"
    # Kyurem: the script's callasm, the routine, its slot and its "taken" check (the slot's first word)
    assert at(DNA_CALL, "23") and u32(DNA_CALL + 1) == DNA, "the DNA Splicers script changed"
    assert at(DNA - 1 - B, "f7b564240022534b"), "the DNA Splicers routine moved"
    assert at(0x00FD704E, "4e4b1b680700002b01d00323") and u32(0x00FD7188) == 0x0203D800, "Kyurem's slot check changed"
    assert (u32(0x00FD7184), u32(0x00FD71BC)) == (0x100000000 - 696, 0x100000000 - 995), "Kyurem's species changed"
    # "does the player have this species": party, 14 boxes of 30, the two Day Care places
    assert at(OWNED - 1 - B, "f8b564234f464646") and at(0x01F036A8, "0023f0b557464e46"), "the owned check moved"
    assert at(0x01F03728, "0e2b") and (u32(0x01F037C0), u32(0x01F037C4)) == (0x3030, 0x30BC), "the owned check changed"
    # ClearBag: bagslots' trampoline, called only by NewGameInitData
    assert at(CLEARBAG, "004b1847"), "ClearBag is not a trampoline: apply after bagslots"
    old_clear = u32(CLEARBAG + 4)
    assert old_clear & 1 and B <= old_clear < B + len(rom), "ClearBag's trampoline has no target"
    assert bl_target(rom, 0x0008454E) == B + CLEARBAG, "NewGameInitData does not call ClearBag there"

    with open(os.path.join(HERE, "fusionfix.s"), encoding="ascii") as fh:
        src = fh.read().replace("CLEARBAG_ADDR", "0x%08X" % old_clear)
    for want in ("0x%08X" % FUSION, "0x%08X" % DNA, "0x%08X" % OWNED):
        assert want in src, "fusionfix.s does not name %s" % want
    base = B + FREE
    code = None
    for pad in ("", "    mov r8, r8"):          # the literals must start on a 4-byte boundary
        try:
            code, dis = SM.thumb(src.replace("PAD", pad), base)
        except AssertionError:
            continue
        if len(code) % 4 == 0:
            break
        code = None
    assert code, "fusionfix.s does not assemble to Thumb-1"
    funcs = [i.address for i in dis if i.mnemonic == "push"]
    assert len(funcs) == 3, "expected fx_entry, fx_dna and fx_drop_orphan, found %d pushes" % len(funcs)
    entry, dna = funcs[0], funcs[1]
    assert entry == base
    words = {int(w, 0) for w in re.findall(r"\.word\s+(\w+)", src.replace("CLEARBAG_ADDR", "0"))} | {old_clear}
    newgame = None
    for i in dis:                               # each pc-relative load must land on one of the literals
        if i.mnemonic == "ldr" and "pc" in i.op_str:
            t = ((i.address + 4) & ~3) + (int(i.op_str.split("#")[1].rstrip("]"), 16) if "#" in i.op_str else 0) - base
            assert struct.unpack_from("<I", code, t)[0] in words, "a load misses its literal"
    # fx_newgame is the instruction after fx_call3's `bx r3`
    bxs = [k for k, i in enumerate(dis) if i.mnemonic == "bx" and i.op_str == "r3"]
    assert len(bxs) == 1, "expected one `bx r3` (fx_call3)"
    newgame = dis[bxs[0] + 1].address
    assert dis[bxs[0] + 1].mnemonic == "ldr", "fx_newgame does not follow fx_call3"

    end = FREE + len(code)
    assert end <= FREE_END and set(rom[FREE:end]) == {0xFF}, "target region not free"
    for k in range(0, len(rom), 4):
        assert not base <= u32(k) < B + end, "%08X already points into the target" % (B + k)
    rom[FREE:end] = code
    struct.pack_into("<I", rom, TRAMP + 4, entry | 1)
    struct.pack_into("<I", rom, DNA_CALL + 1, dna | 1)
    struct.pack_into("<I", rom, CLEARBAG + 4, newgame | 1)
    with open(outp, "wb") as fh:
        fh.write(rom)
    print("fusionfix: fx_entry %08X, fx_dna %08X, fx_newgame %08X (then %08X), %d bytes @%08X..%08X; words at "
          "%08X, %08X, %08X" % (entry | 1, dna | 1, newgame | 1, old_clear, len(code), base, B + end,
                                B + TRAMP + 4, B + DNA_CALL + 1, B + CLEARBAG + 4))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
