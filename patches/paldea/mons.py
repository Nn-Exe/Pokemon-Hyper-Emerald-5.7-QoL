"""Area Zero's own field sprites: the Gen 9 Pokemon as overworld sprites, and the research stations' recorder.

The pictures are in sprites/ (made by sprites/convert.py): the Pokemon as pokeemerald-expansion draws them walking
behind you (three standing frames each: down, up, left), and a small tape machine drawn for this patch. Tests 1-9
stood the Pokemon's 64x64 battle pictures on the map; the user: "it is too big, should not it be sprite?".

A sprite needs three things in the ROM:

  * An entry in the hack's sprite table (0x0839CF00 + 0x24 * n, drawn by an object with graphics 0x4E and n in its
    template's fourth byte). The table has room for 256 entries: 0-239 are the hack's, 240-255 are filler (0x0F
    bytes, nothing points at them, the lookup at 0x094A2BCE has no bound). An entry of ours is a copy of one of
    the hack's of the same size (its OAM and subsprites), with its own palette tag and frames, the game's standard
    animations (so it turns to face you: frames 0 down, 1 up, 2 left, mirrored for right) and palette slot 2, which
    like every slot but 0 and 10 means "by tag" to the hack (0x094A356A gives each tag one of the palettes 4-9).
  * Frames: {pointer, size} x 9, as the standard animations count them (3-8 are the steps: the standing frames
    again, since nothing here walks).
  * Its palette, under its tag, in the field's palette table. That table is vanilla's (0x0850BBC8: 35 rows and a
    zero row) and is full, so it is copied with our rows after it and the three words of code that hold its address
    are pointed at the copy (0x0808E8BC LoadObjectEventPalette, 0x0808E950 PatchObjectPalette, 0x0808E9A8
    FindObjectEventPaletteIndexByTag). The copy ends in tag 0x11FF, the one the search stops at; vanilla's table
    forgot it, so a search for a tag that is not there used to run on into whatever follows.

All of it goes in one block at the far end of the ROM (the free tail after fusionfix), apart from the map blob.
"""
import os, struct

HERE = os.path.dirname(os.path.abspath(__file__))
SPRITES = os.path.join(HERE, "sprites")

PAL_TABLE = 0x0050BBC8
PAL_ROWS = 35                               # then {0, 0}
PAL_REFS = (0x0008E8BC, 0x0008E950, 0x0008E9A8)
PAL_END_TAG = 0x11FF
FILLER_SLOTS = range(240, 256)
FILLER = b"\x0F" * 0x24
# entries of the hack's that ours are copied from: a 32x32 Pokemon (Suicune), a 64x64 one (Giratina), a 16x32 thing
# (a crystal shard), and one that does not animate (a clipboard: its animation table)
LIKE_32, LIKE_64, LIKE_16x32, LIKE_STILL = 73, 83, 20, 28
FRAME_ORDER = (0, 1, 2, 0, 0, 1, 1, 2, 2)   # the standard animations' frames 0-8 from our down, up, left
SLOT_BY_TAG = 2
# file size -> (width, height, frames, the entry to copy)
KINDS = {0x600: (32, 32, 3, LIKE_32), 0x1800: (64, 64, 3, LIKE_64), 0x100: (16, 32, 1, LIKE_16x32),
         0x800: (32, 32, 4, LIKE_32)}       # four frames: a thing that shimmers (the time rift, sprites/rift.py)
# A shimmering thing has an animation table of its own: every animation the game can ask of an object (24 of them)
# is the same loop round its four pictures, SHIMMER frames each, and its frame table has the nine entries the
# standard animations count, so that none can ask for a picture that is not there (patches/sprframe). It is
# "inanimate" to the hack all the same: it never turns. Tried first on top of the finished game
# (rom/unreleased/time-rift/trial-kit).
SHIMMER, SHIMMER_FRAMES, ANIMS = 9, 4, 24


def u16(rom, o): return struct.unpack_from("<H", rom, o)[0]
def u32(rom, o): return struct.unpack_from("<I", rom, o)[0]


def load(name):
    """(picture bytes, palette bytes, width, height, frames, the entry to copy) of sprites/<name>."""
    pic = open(os.path.join(SPRITES, name + ".4bpp"), "rb").read()
    pal = open(os.path.join(SPRITES, name + ".gbapal"), "rb").read()
    assert len(pal) == 32 and len(pic) in KINDS, "sprites/%s is not a picture convert.py made" % name
    return (pic, pal) + KINDS[len(pic)]


def entry(rom, ext_table, n):
    o = ext_table - 0x08000000 + 0x24 * n
    return bytes(rom[o:o + 0x24])


def check(rom, ext_table, sprites, blank):
    """What install() overwrites still looks the way it did. sprites: key -> (file, slot, tag); blank: the slots
    among them that are the hack's unused 16x32 entries (checked by the caller)."""
    for ref in PAL_REFS:
        assert u32(rom, ref) == 0x08000000 + PAL_TABLE, "the palette table's address at %X changed" % ref
    assert struct.unpack_from("<IH", rom, PAL_TABLE + 8 * PAL_ROWS) == (0, 0), "the palette table grew"
    tags = [u16(rom, PAL_TABLE + 8 * i + 4) for i in range(PAL_ROWS)]
    for key, (name, slot, tag) in sprites.items():
        assert tag not in tags and tag != PAL_END_TAG, "palette tag %04X is in use" % tag
        assert slot in blank or (slot in FILLER_SLOTS and entry(rom, ext_table, slot) == FILLER), \
            "sprite slot %d is in use" % slot
    assert len({s for _, s, _ in sprites.values()}) == len(sprites) == len({t for _, _, t in sprites.values()})
    for n, size, w, h in ((LIKE_32, 0x200, 32, 32), (LIKE_64, 0x800, 64, 64), (LIKE_16x32, 0x100, 16, 32),
                          (LIKE_STILL, 0x80, 16, 16)):
        assert struct.unpack_from("<Hhh", entry(rom, ext_table, n), 6) == (size, w, h), "sprite %d changed" % n
    assert entry(rom, ext_table, LIKE_STILL)[12] & 0x40, "sprite %d animates now" % LIKE_STILL
    std = u32(entry(rom, ext_table, LIKE_32), 0x18)
    assert std == u32(entry(rom, ext_table, LIKE_64), 0x18) == u32(entry(rom, ext_table, LIKE_16x32), 0x18), \
        "the three entries copied from no longer share the standard animations"


def put(rom, blob, sprites):
    """The pictures, frame tables, palettes and the longer palette table into `blob`."""
    stored = {}                                            # pictures -> the key they went in under
    for key, (name, slot, tag) in sprites.items():
        pic, pal, w, h, n, like = load(name)
        size = len(pic) // n
        if pic in stored:                                  # the two rifts: one set of pictures, two palettes
            p = blob.addr[("pic", stored[pic])]
        else:
            p = blob.put(("pic", key), pic)
            stored[pic] = key
        if n == SHIMMER_FRAMES:
            order = tuple(k % n for k in range(len(FRAME_ORDER)))
        else:
            order = FRAME_ORDER if n == 3 else (0,) * len(FRAME_ORDER)
        blob.put(("frames", key), b"".join(struct.pack("<IHH", p + size * f, size, 0) for f in order))
        blob.put(("pal", key), pal)
    if any(load(name)[4] == SHIMMER_FRAMES for name, slot, tag in sprites.values()):
        # ANIMCMD_FRAME(picture, SHIMMER) x 4, ANIMCMD_JUMP(0); then the table: every animation is that loop
        loop = blob.put(("shimmer", "loop"), b"".join(struct.pack("<I", f | (SHIMMER << 16))
                                                       for f in range(SHIMMER_FRAMES)) + struct.pack("<I", 0xFFFE))
        blob.put(("shimmer", "anims"), struct.pack("<I", loop) * ANIMS)
    rows = bytes(rom[PAL_TABLE:PAL_TABLE + 8 * (PAL_ROWS + 1)])       # the zero row too: tag 0 stays where it was
    t = blob.put(("paltable",), rows + bytes(8 * len(sprites)) + struct.pack("<IHH", 0, PAL_END_TAG, 0))
    for k, (key, (name, slot, tag)) in enumerate(sprites.items()):
        o = t - blob.base + len(rows) + 8 * k
        struct.pack_into("<H", blob.data, o + 4, tag)
        blob.ref(("pal", key), o)


def install(rom, blob, ext_table, sprites):
    """After blob.link() is written to the ROM: the sprite entries, and the code's palette table."""
    std = u32(entry(rom, ext_table, LIKE_32), 0x18)
    still = u32(entry(rom, ext_table, LIKE_STILL), 0x18)
    for key, (name, slot, tag) in sprites.items():
        pic, pal, w, h, n, like = load(name)
        e = bytearray(entry(rom, ext_table, like))
        assert struct.unpack_from("<Hhh", e, 6) == (len(pic) // n, w, h)
        moves = n == 3                                     # a Pokemon; the recorder is one frame and keeps still
        shimmers = n == SHIMMER_FRAMES                     # the rift: it does not turn either, but its picture goes round
        struct.pack_into("<HHH", e, 0, 0xFFFF, tag, PAL_END_TAG)
        e[12] = SLOT_BY_TAG | (e[12] & 0x30) | (0 if moves else 0x40)
        e[13] = 0                                          # no footprints
        anims = std if moves else blob.addr[("shimmer", "anims")] if shimmers else still
        struct.pack_into("<II", e, 0x18, anims, blob.addr[("frames", key)])
        o = ext_table - 0x08000000 + 0x24 * slot
        rom[o:o + 0x24] = e
    for ref in PAL_REFS:
        struct.pack_into("<I", rom, ref, blob.addr[("paltable",)])


def palettes(rom):
    """tag -> 16 colours, from whichever palette table the ROM's code uses (for the tools that draw sprites)."""
    t = u32(rom, PAL_REFS[2]) - 0x08000000
    out = {}
    for i in range(PAL_ROWS if t == PAL_TABLE else 96):    # vanilla's table has no end mark
        p, tag = u32(rom, t + 8 * i), u16(rom, t + 8 * i + 4)
        if tag == PAL_END_TAG:
            break
        if 0x08000000 <= p < 0x0A000000 - 32:
            out[tag] = [u16(rom, p - 0x08000000 + 2 * k) for k in range(16)]
    return out
