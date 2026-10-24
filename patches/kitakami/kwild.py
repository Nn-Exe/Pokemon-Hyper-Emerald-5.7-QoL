"""Kitakami's wild Pokemon (the user, 2026-10-15: "give it a try", on the wild table being full).

gWildMonHeaders (0x08E17D50) holds 257 headers - the game's 254 and Area Zero's three, which took the 68 spare
bytes after its terminator - so there is no room to add a header where it lies. It is copied into Kitakami's
space with Kitakami's headers before the terminator, and the 15 words that point at it are pointed at the copy:
13 literals of the game's wild-encounter code (0x080B4D48-0x080B5864, 0x0813CC78, 0x0813CCB4, 0x08196C50), the
DexNav search's (0x08FF6CB0) and one in the DexNav chain's data (0x08FDA934). Nothing points into the middle of
the table (checked 2026-10-15), and every lookup walks it to the terminator, as Area Zero's three showed.

The species are Kitakami's (The Teal Mask's Kitakami Pokedex) as far as this game has them (not Dipplin,
Poltchageist or Glimmet), found by name, at post-game levels (Area Zero's are 63-67).
"""
import struct

TABLE = 0x00E17D50
REFS = (0x000B4D48, 0x000B5438, 0x000B54D8, 0x000B5560, 0x000B567C, 0x000B56DC, 0x000B5728, 0x000B579C, 0x000B57DC,
        0x000B5864, 0x0013CC78, 0x0013CCB4, 0x00196C50, 0x00FDA934, 0x00FF6CB0)
HEADERS_WAS = 257

LAND_RATE, WATER_RATE, FISH_RATE = 20, 4, 30
LAND = {}  # 12 slots each: 20 20 10 10 10 10 5 5 4 4 1 1 (%). None since 2026-10-16: the Kitakami Road's and Oni
           # Mountain's grass went with them, the Dreaded Den's floor with the den, and the town has no grass.
WATER = {  # 5 slots: 60 30 5 4 1
    "mossui": (58, 62, ["Lotad", "Poliwag", "Wooper", "Psyduck", "Lombre"]),
}
FISH = [   # 10 slots: the Old Rod 2 (70 30), the Good Rod 3 (60 20 20), the Super Rod 5 (40 40 15 4 1)
    (50, 55, "Magikarp"), (50, 55, "Feebas"),
    (55, 60, "Magikarp"), (55, 60, "Goldeen"), (55, 60, "Basculin"),
    (60, 64, "Basculin"), (60, 64, "Goldeen"), (60, 64, "Seaking"), (60, 64, "Gyarados"), (60, 64, "Feebas"),
]
WHERE = {"mossui": ("water", "fish")}


def species_id(rom, enc, name):
    names = struct.unpack_from("<I", rom, 0x144)[0] - 0x08000000
    e = enc(name) + b"\xFF"
    for i in range(1, 1300):
        if rom[names + 11 * i:names + 11 * i + len(e)] == e:
            stats = struct.unpack_from("<I", rom, 0x1BC)[0] - 0x08000000 + 28 * i
            assert rom[stats] > 0, "%s (%d) has no base stats" % (name, i)
            return i
    raise AssertionError("no species called %s in this ROM" % name)


def check(rom):
    u32 = lambda o: struct.unpack_from("<I", rom, o)[0]
    for r in REFS:
        assert u32(r) == 0x08000000 + TABLE, "a reference to the wild table moved: 0x%08X" % (0x08000000 + r)
    n = 0
    while rom[TABLE + 20 * n] != 0xFF:
        n += 1
    assert n == HEADERS_WAS, "the wild table has %d headers, not %d" % (n, HEADERS_WAS)


def install(rom, blob, enc, known):
    """the tables into blob, and a copy of the header table with Kitakami's; -> the copy's key (point REFS at it)"""
    def mons(key, lo, hi, names):
        return blob.put(("wild_mons", key), b"".join(struct.pack("<BBH", lo, hi, species_id(rom, enc, n)) for n in names))

    def info(key, rate, mons_key):
        p = blob.put(("wild_info", key), struct.pack("<BBBBI", rate, 0, 0, 0, 0))
        blob.ref(mons_key, p - blob.base + 4)
        return ("wild_info", key)

    infos = {}
    for area, (lo, hi, names) in LAND.items():
        mons("land " + area, lo, hi, names)
        infos[(area, "land")] = info("land " + area, LAND_RATE, ("wild_mons", "land " + area))
    for area, (lo, hi, names) in WATER.items():
        mons("water " + area, lo, hi, names)
        infos[(area, "water")] = info("water " + area, WATER_RATE, ("wild_mons", "water " + area))
    blob.put(("wild_mons", "fish"), b"".join(struct.pack("<BBH", lo, hi, species_id(rom, enc, n)) for lo, hi, n in FISH))
    fish = info("fish", FISH_RATE, ("wild_mons", "fish"))
    old = bytes(rom[TABLE:TABLE + 20 * (HEADERS_WAS + 1)])           # every header, and the terminator
    ours = []
    for area, kinds in WHERE.items():
        g, n = known[area]
        ours.append((g, n, [infos.get((area, "land")) if "land" in kinds else None,
                            infos.get((area, "water")) if "water" in kinds else None, None,
                            fish if "fish" in kinds else None]))
    table = old[:20 * HEADERS_WAS] + b"".join(struct.pack("<BBHIIII", g, n, 0, 0, 0, 0, 0) for g, n, _ in ours) + \
        old[20 * HEADERS_WAS:]
    p = blob.put(("wild", "headers"), table)
    for k, (g, n, ptrs) in enumerate(ours):
        for j, key in enumerate(ptrs):
            if key:
                blob.ref(key, p - blob.base + 20 * (HEADERS_WAS + k) + 4 + 4 * j)
    return ("wild", "headers")


def repoint(rom, addr):
    for r in REFS:
        struct.pack_into("<I", rom, r, addr)
