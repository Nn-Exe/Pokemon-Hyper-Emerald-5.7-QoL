"""Oval Charm (Hyper Emerald v5.7). Apply after the dexdesc build.
usage: python ovalcharm_patch.py <in.gba> <out.gba>

A new key item. With it in the Bag, the Day Care finds Eggs more often: the chance each time the game rolls
for one (every 256 steps) goes 20% -> 40%, 50% -> 80%, 70% -> 88%, as in the main games. The Day-Care Man on
Route 117 (the Hoenn Day Care) gives it, once, after you have beaten the Hoenn League (flag 0x864,
FLAG_SYS_GAME_CLEAR, set on entering the Hall of Fame).

* The item takes slot 114, one of the hack's unused "???" slots (no script gives, takes or checks it). Its
  entry is a copy of the Shiny Charm's (119: Key Items pocket, "can't use" field routine) with its own name,
  id and description, and its own Bag icon (make_icon.py: the Shiny Charm's string and tassel, an oval gem).
* The egg roll: 38 bytes of TryProduceOrHatchEgg (0x08070B0E..0x08070B33, the compatibility call, the
  Random() * 100 / 0xFFFF roll and the TriggerPendingDaycareEgg call) become a call to egg_roll
  (ovalcharm.s) and a branch on its answer. The other caller of GetDaycareCompatibilityScore - the Day-Care
  Man's "the two seem to get along" line - is untouched, as in the main games.
* The Day-Care Man (Route 117, 0/32 object 2, script 0x08291C18): its first five bytes (lock, faceplayer,
  special 0xB8) become a goto to our script, which gives the charm when it should and otherwise does those
  three commands and rejoins his script at +5. Given flag 0x433E: no script references it, it is not a
  literal anywhere in the code, and it is clear in all 34 saves checked.

Also: item 644, a developer's debug item nobody hands out (its field routine runs a test script), still had
its Chinese name 脚本测试器 and the Grassium Z's description. It is now "Script Tester", "A developer's tool
that runs a test script."
"""
import os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "sinnohmap"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
import make_icon
import sinnohmap_patch as SM                    # the Thumb assembler check
from make_region_map import lz77                # never emits distance-1 references (see NOTES)

FREE = 0x00FF5600                               # in the unreferenced 0xFF run 0x08FF2574..0x08FFD5A0
BASE = 0x08000000 + FREE
ITEMS, ITEM_SIZE, ICONS = 0x00FC2C7C, 44, 0x00FCBFF4
OVAL, SHINY_CHARM, SCRIPT_TESTER = 114, 119, 644
ROLL_SITE, ROLL_END = 0x08070B0E, 0x08070B34
DAYCARE_MAN = 0x08291C18
GIVEN_FLAG, HOENN_CHAMPION = 0x433E, 0x0864
FANFARE = 0x0173                                # the obtain-item fanfare (the Journal patch's gift uses it)
MSG_W = 200                                     # message box text width in pixels
GLYPH_W = 0x006542E4

CHARS = {c: 0xBB + i for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ")}
CHARS.update({c: 0xD5 + i for i, c in enumerate("abcdefghijklmnopqrstuvwxyz")})
CHARS.update({str(i): 0xA1 + i for i in range(10)})
CHARS.update({" ": 0x00, "!": 0xAB, "?": 0xAC, ".": 0xAD, "-": 0xAE, "'": 0xB4, ",": 0xB8, "é": 0x1B})
PLAYER = b"\xFD\x01"


def enc(word):
    out = bytearray(); i = 0
    while i < len(word):
        if word.startswith("{PLAYER}", i):
            out += PLAYER; i += 8
        else:
            out.append(CHARS[word[i]]); i += 1
    return bytes(out)


def message(rom, paragraphs):
    """Wrap each paragraph at MSG_W, two lines to a box: new line 0xFE, next box 0xFA (scroll), paragraphs 0xFB."""
    def w(b):
        return sum(7 * 6 if b[k:k + 2] == PLAYER else rom[GLYPH_W + b[k]] for k in range(len(b))
                   if not (k and b[k - 1:k + 1] == PLAYER))
    out = bytearray()
    for p, text in enumerate(paragraphs):
        if p: out.append(0xFB)
        lines, cur = [], b""
        for word in text.split(" "):
            e = enc(word)
            trial = cur + b"\x00" + e if cur else e
            if cur and w(trial) > MSG_W:
                lines.append(cur); cur = e
            else:
                cur = trial
        lines.append(cur)
        for k, line in enumerate(lines):
            if k: out.append(0xFE if k % 2 else 0xFA)
            out += line
    return bytes(out) + b"\xFF"


def item_text(lines):
    return b"\xFE".join(enc(l) for l in lines) + b"\xFF"


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000

    # what we change must be what we expect
    oval_e, shiny_e, tester_e = (ITEMS + i * ITEM_SIZE for i in (OVAL, SHINY_CHARM, SCRIPT_TESTER))
    assert rom[oval_e:oval_e + 7] == b"\x3d" * 7 and struct.unpack_from("<H", rom, oval_e + 14)[0] == OVAL, \
        "item %d is not an unused slot" % OVAL
    assert rom[shiny_e + 26] == 5 and struct.unpack_from("<H", rom, shiny_e + 14)[0] == SHINY_CHARM
    assert rom[tester_e:tester_e + 10] == bytes.fromhex("0717017b02060c190ab2"), "item 644's name changed"
    roll = bytes.fromhex("301c00f01cf9041c2406240efef757fd0004000c64214843194977f21ef8844201d9fff756fb")
    assert rom[ROLL_SITE - 0x08000000:ROLL_END - 0x08000000] == roll, "the egg roll is not the vanilla one"
    man = DAYCARE_MAN - 0x08000000
    assert rom[man:man + 5] == bytes((0x6A, 0x5A, 0x25, 0xB8, 0x00)), "the Day-Care Man's script changed"

    # ---- data and code in free space
    blob = bytearray(); addr = {}
    def put(name, b, align=1):
        while len(blob) % align: blob.append(0)
        addr[name] = BASE + len(blob); blob.extend(b)

    src = open(os.path.join(HERE, "ovalcharm.s"), encoding="ascii").read().replace("OVAL_CHARM", str(OVAL))
    code, _ = SM.thumb(src, BASE)
    put("EGG_ROLL", code, 4)

    icon = make_icon.draw(rom)
    put("ICON", lz77(make_icon.pack(icon)), 4)
    put("ICON_PAL", lz77(make_icon.palette()), 4)
    put("DESC", item_text(["An oval charm that", "makes Eggs turn up", "at the Day Care."]))
    put("TESTER_DESC", item_text(["A developer's tool", "that runs a test", "script."]))
    put("T_INTRO", message(rom, [
        "Ah, it's you! Word travels fast. You beat the Elite Four and became the Champion of Hoenn!",
        "My wife and I have looked after more Eggs than we can count. I'd like you to have this charm."]))
    put("T_GOT", message(rom, ["{PLAYER} received the Oval Charm!"]))
    put("T_AFTER", message(rom, [
        "Keep that Oval Charm in your Bag, and Eggs will turn up here much more often.",
        "Come and see us anytime!"]))

    # the Day-Care Man's new head
    s = bytearray()
    def ptr_at():
        s.extend(b"\0\0\0\0"); return len(s) - 4
    s += bytes((0x6A, 0x5A))                                          # lock, faceplayer
    s += bytes((0x2B,)) + struct.pack("<H", GIVEN_FLAG)               # checkflag given
    s += bytes((0x06, 0x01)); j_given = ptr_at()                      # goto_if set -> his usual script
    s += bytes((0x2B,)) + struct.pack("<H", HOENN_CHAMPION)            # checkflag Hoenn League beaten
    s += bytes((0x06, 0x00)); j_notyet = ptr_at()                     # goto_if unset -> his usual script
    s += bytes((0x0F, 0x00)) + struct.pack("<I", addr["T_INTRO"]) + bytes((0x09, 0x04))
    s += bytes((0x44,)) + struct.pack("<HH", OVAL, 1)                 # additem (raw: callstd 0 is dead here)
    s += bytes((0x29,)) + struct.pack("<H", GIVEN_FLAG)               # setflag given
    s += bytes((0x31,)) + struct.pack("<H", FANFARE)                  # playfanfare
    s += bytes((0x0F, 0x00)) + struct.pack("<I", addr["T_GOT"]) + bytes((0x09, 0x04))
    s += bytes((0x32,))                                               # waitfanfare
    s += bytes((0x0F, 0x00)) + struct.pack("<I", addr["T_AFTER"]) + bytes((0x09, 0x04))
    s += bytes((0x6C, 0x02))                                          # release, end
    usual = len(s)
    s += bytes((0x25, 0xB8, 0x00))                                    # special 0xB8, as his script began
    s += bytes((0x05,)) + struct.pack("<I", DAYCARE_MAN + 5)          # and on with the rest of it
    put("SCRIPT", b"", 4)
    base = addr["SCRIPT"]
    for off in (j_given, j_notyet):
        struct.pack_into("<I", s, off, base + usual)
    s = bytes(s)
    blob.extend(s)

    end = FREE + len(blob)
    assert end <= 0x00FFD5A0 and set(rom[FREE:end]) == {0xFF}, "target region not free"
    rom[FREE:end] = blob

    # ---- the item entry, its icon
    entry = bytearray(rom[shiny_e:shiny_e + ITEM_SIZE])
    name = enc("Oval Charm") + b"\xFF"
    entry[0:14] = name + bytes(14 - len(name))
    struct.pack_into("<H", entry, 14, OVAL)
    struct.pack_into("<I", entry, 20, addr["DESC"])
    rom[oval_e:oval_e + ITEM_SIZE] = entry
    struct.pack_into("<II", rom, ICONS + OVAL * 8, addr["ICON"], addr["ICON_PAL"])

    # ---- item 644
    name = enc("Script Tester") + b"\xFF"
    assert len(name) <= 14
    rom[tester_e:tester_e + 14] = name + bytes(14 - len(name))
    struct.pack_into("<I", rom, tester_e + 20, addr["TESTER_DESC"])

    # ---- the egg roll: call egg_roll, then trigger the Egg if it says so
    site = """
    adds r0, r6, #0
    ldr r3, lit
    bl go
    cmp r0, #0
    beq done
    bl 0x080701E0
    b done
go:
    bx r3
    mov r8, r8
lit:
    .word 0x%08X
    mov r8, r8
    mov r8, r8
    mov r8, r8
    mov r8, r8
    mov r8, r8
    mov r8, r8
done:
""" % (addr["EGG_ROLL"] | 1)
    patch, _ = SM.thumb(site, ROLL_SITE)
    assert len(patch) == ROLL_END - ROLL_SITE, "site patch is %d bytes" % len(patch)
    rom[ROLL_SITE - 0x08000000:ROLL_END - 0x08000000] = patch

    # ---- the Day-Care Man: goto our head
    rom[man:man + 5] = bytes((0x05,)) + struct.pack("<I", base)

    open(outp, "wb").write(rom)
    print("egg_roll %08X, icon %08X, Day-Care Man script %08X (%d bytes), end %08X"
          % (addr["EGG_ROLL"], addr["ICON"], base, len(s), 0x08000000 + end))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
