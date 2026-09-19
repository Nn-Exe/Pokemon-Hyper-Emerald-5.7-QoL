"""Type badges beside the opponent's healthbox (Hyper Emerald v5.7). Apply after the dexnav build.
usage: python typeicons_patch.py <in.gba> <out.gba>

In battle, the opponent's healthbox gets one or two 16x16 type badges to its right (type 1 above type 2),
like the SoulSilver-style hacks. The badge art is the glyph half of the hack's own summary-screen type
labels (badges.bin, 24 frames, cut from the sheet at 0x090D0000 and re-palettised to one 16-colour palette
so the feature costs a single OBJ palette slot in battle). Types are read from gBattleMons every frame, so
type changes (Soak, Protean, Transform) show too. Your own box is untouched.

ROM changes: the shinybox hook's "bl shiny_boxes" (at 0x08FDA0BA, inside our own free-space code) is
retargeted to `entry`, which calls shiny_boxes and then the badge update. Everything else is new code and
data in free space. No vanilla bytes are touched. Requires the shinybox patch.
"""
import struct, sys, os
from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

HERE = os.path.dirname(os.path.abspath(__file__))
FREE = 0x00FDA9BC
BASE = 0x08000000 + FREE
ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)

SHINY_BL = 0xFDA0BA                     # bl shiny_boxes inside the shinybox stub
SHINY_BOXES = 0x08FDA0C2                # shiny_boxes itself (push {r4-r7, lr})
OURTAG = 0x5E62
FRAME = 128                             # one badge = 16x16 sprite (9x12 drawn: SoulGold's 8-wide tiles + a border column)
SUMMARY_ANIMS = 0x09D3813C              # the summary screen's type anim table: copy its END encoding
DUMMY_AFFINE = 0x082EC6A8


def thumb(src, addr):
    code = bytes(ks.asm(src, addr)[0])
    dis = list(Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(code, addr))
    bad = [i for i in dis if i.size == 4 and i.mnemonic != "bl"]
    assert not bad, "Thumb-2 encoding emitted: %s" % [(i.mnemonic, i.op_str) for i in bad]
    return code, dis


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    bl = list(Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(bytes(rom[SHINY_BL:SHINY_BL + 4]), 0x08000000 + SHINY_BL))
    assert bl and bl[0].mnemonic == "bl" and int(bl[0].op_str.lstrip("#"), 0) == SHINY_BOXES, "shinybox stub not found"
    assert rom[SHINY_BOXES - 0x08000000:SHINY_BOXES - 0x08000000 + 2] == b"\xf0\xb5", "shiny_boxes prologue differs"
    seq0 = struct.unpack_from("<I", rom, SUMMARY_ANIMS - 0x08000000)[0] - 0x08000000
    frame0, end = struct.unpack_from("<II", rom, seq0)
    assert frame0 == 0 and (end & 0xFFFF) == 0xFFFF, "summary anim format unexpected: %08X %08X" % (frame0, end)

    badges = open(os.path.join(HERE, "badges_sg.bin"), "rb").read()   # SoulGold's 8x16 badges, 24 frames
    pal = open(os.path.join(HERE, "badges_sg.pal"), "rb").read()
    assert len(badges) == 24 * FRAME and len(pal) == 32

    src = open(os.path.join(HERE, "typeicons.s"), encoding="ascii").read()

    def data_blob(base, badge_cb):
        d = bytearray(); addrs = {}
        def put(name, b, align=4):
            while len(d) % align: d.append(0)
            addrs[name] = base + len(d); d.extend(b)
        put("BADGES", badges)
        put("PAL", pal)
        put("OAM", bytes((0x00, 0x00, 0x00, 0x40, 0x00, 0x04, 0x00, 0x00)))    # 16x16, 4bpp, priority 1
        seqs = []
        for n in range(24):
            put("SEQ%d" % n, struct.pack("<II", n, end))                       # frame n, then END
            seqs.append(addrs["SEQ%d" % n])
        put("ANIMS", struct.pack("<24I", *seqs))
        put("IMAGES", b"".join(struct.pack("<IHH", addrs["BADGES"] + n * FRAME, FRAME, 0) for n in range(24)))
        put("TEMPLATE", struct.pack("<HHIIIII", 0xFFFF, OURTAG, addrs["OAM"], addrs["ANIMS"], addrs["IMAGES"],
                                    DUMMY_AFFINE, badge_cb))
        put("PALSTRUCT", struct.pack("<IHH", addrs["PAL"], OURTAG, 0))
        return bytes(d), addrs

    def assemble(addrs, badge_cb):
        s = src.replace("OURTAG", "0x%04X" % OURTAG).replace("BADGECB_ADDR", "0x%08X" % badge_cb)
        for k in ("TEMPLATE", "PALSTRUCT"):
            s = s.replace(k + "_ADDR", "0x%08X" % addrs[k])
        return thumb(s, BASE)

    _, dummy = data_blob(BASE, BASE)
    code, dis = assemble(dummy, BASE)
    badge_cb = next(i.address for i in dis if i.mnemonic == "bx" and i.op_str == "lr") | 1   # badge_cb: bx lr
    code_len = (len(code) + 3) & ~3
    data, daddrs = data_blob(BASE + code_len, badge_cb)
    code, _ = assemble(daddrs, badge_cb)
    assert (len(code) + 3) & ~3 == code_len

    blob = bytearray(code) + bytes(code_len - len(code)) + data
    end_off = FREE + len(blob)
    assert set(rom[FREE:end_off]) == {0xFF}, "target region not free"
    rom[FREE:end_off] = blob
    newbl = bytes(ks.asm("bl 0x%08X" % BASE, 0x08000000 + SHINY_BL)[0])
    assert len(newbl) == 4
    rom[SHINY_BL:SHINY_BL + 4] = newbl
    open(outp, "wb").write(rom)
    print("code %d bytes @%08X (badge_cb %08X), data @%08X, end %08X" % (
        len(code), BASE, badge_cb, BASE + code_len, 0x08000000 + end_off))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
