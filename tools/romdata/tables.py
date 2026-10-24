"""Where this build keeps the tables the site tools read: up to v1.8 at fixed addresses, since v1.9 (the whole of
Gen 9) partly elsewhere. Every address is read from the words the game itself uses and checked, so a build that
moves them again stops here instead of giving the site wrong data.

    import tables; T = tables.of(rom)
    T.species         slots in the species tables (1,200 up to v1.8; 1,408 in v1.9)
    T.table[name]     file offset of one of the 23 species tables (names as in SPECIES_TABLES)
    T.moves           move ids are 1..T.moves-1 (a blank name is an unused id)
    T.move_names      13 bytes a move (header 0x148)
    T.move_descs      a pointer a move, indexed [move - 1]
    T.abilities       ability ids are 1..T.abilities-1; v1.9's Gen 9 abilities are aliases from id 256 on, and
                      since gen9abil (2026-10-21) ids of their own, 0x101..0x12C (patches/gen9abil/gen9abil_data.py)
    T.ability_names   13 bytes an ability (header 0x1C0); T.ability_descs: a pointer an ability (header 0x1C4)
    T.items           item ids are 1..T.items-1
    T.egg_moves       the egg-move list: species + 20000, then its moves; 0xFFFF ends
    T.dex_entries     32 bytes a National Dex number
    T.trainer_classes class names are 0..T.trainer_classes-1, 13 bytes each at CLASS_NAMES

Who moved what (the patches are in the dev repository's patches/ folder):
    speciesx  the 23 species tables to 0x0968D000, 1,280 slots each, one after another in SPECIES_TABLES' order,
              each rounded up to 4 bytes; gen9rest moved them again the same way to 0x09AC0000, 1,408 slots each
    gen9      the move names and descriptions (1,024 entries) and the ability names and texts (1,793) to longer
              copies; the header words name the names, the descriptions are found by their first 64 bytes
    gen9dex   the Pokédex entries (the word at 0x080BFA20 names them); gen9egg the egg moves (0x080703F0)
    gen9      item 769 (Booster Energy), gen9rest items 770-775; paldea trainer classes 71 and 72
"""
import struct

B = 0x08000000
# (name, bytes a slot, where v1.8 has it)
SPECIES_TABLES = [
    ("base stats", 28, 0x0F186E0), ("front pictures", 8, 0x0F20A20), ("back pictures", 8, 0x0F22FA0),
    ("palettes", 8, 0x0F25520), ("shiny palettes", 8, 0x0F27AA0), ("icons", 4, 0x0F2A020),
    ("icon palette ids", 1, 0x0F2B2E0), ("names", 11, 0x0F2B790), ("evolutions", 40, 0x0F387C0),
    ("front coordinates", 4, 0x0F44340), ("back coordinates", 4, 0x0F45600), ("front anim ids", 1, 0x0F468C0),
    ("anim delays", 1, 0x0F46D70), ("footprints", 4, 0x0F47220), ("elevation", 1, 0x0F4F560),
    ("national dex no.", 2, 0x0F50370), ("hoenn to national", 2, 0x0F50CD0), ("hoenn dex no.", 2, 0x0F51630),
    ("back anim sets", 1, 0x0F51F90), ("front anim tables", 4, 0x0F52440), ("level-up pointers", 4, 0x1D89578),
    ("TM/HM bits", 16, 0x0FCD8F4), ("tutor bits", 16, 0x1750000),
]
GROWN = [(1280, 0x0168D000), (1408, 0x01AC0000)]           # speciesx, gen9rest: (slots, the first table)
HEADER = {"front pictures": 0x128, "palettes": 0x130, "shiny palettes": 0x134, "icons": 0x138, "names": 0x144,
          "base stats": 0x1BC}
NATDEX_LITERAL = 0x06D448                                   # SpeciesToNationalPokedexNum's
MOVE_NAMES_V18, MOVE_DESCS_V18 = 0x01D30258, 0x01D2AD00
EGG_MOVES_WORD, DEX_ENTRIES_WORD = 0x0703F0, 0x0BFA20
CLASS_NAMES = 0x030FCD4


class Tables:
    pass


def of(rom):
    u16 = lambda o: struct.unpack_from("<H", rom, o)[0]
    u32 = lambda o: struct.unpack_from("<I", rom, o)[0]
    t = Tables()

    layouts = [(1200, {name: at for name, _, at in SPECIES_TABLES})]
    for n, start in GROWN:
        lay, p = {}, start
        for name, size, _ in SPECIES_TABLES:
            lay[name] = p
            p = (p + size * n + 3) & ~3
        layouts.append((n, lay))
    found = [(n, lay) for n, lay in layouts if all(u32(w) == B + lay[name] for name, w in HEADER.items())]
    assert found, "the species tables are not where v1.8, speciesx or gen9rest put them"
    t.species, t.table = found[0]
    assert u32(NATDEX_LITERAL) == B + t.table["national dex no."], "the National Dex table is not with the others"
    stats = t.table["base stats"]
    assert rom[stats + 28:stats + 34] == bytes([45, 49, 49, 45, 65, 65]), "Bulbasaur's base stats"
    assert struct.unpack_from("<HHH", rom, t.table["evolutions"] + 40) == (4, 16, 2), "Bulbasaur's evolution row"
    assert u16(u32(t.table["level-up pointers"] + 4) - B) == 33, "Bulbasaur's level-up list (Tackle first)"

    t.move_names = u32(0x148) - B
    t.ability_names, t.ability_descs = u32(0x1C0) - B, u32(0x1C4) - B
    if t.move_names == MOVE_NAMES_V18:
        t.moves, t.abilities, descs = 937, 400, MOVE_DESCS_V18
    else:                                       # gen9's copies: find the descriptions by their first entries
        head = rom[MOVE_DESCS_V18:MOVE_DESCS_V18 + 64]
        hits, k = [], rom.find(head)
        while k >= 0:
            if k != MOVE_DESCS_V18 and k % 4 == 0:
                hits.append(k)
            k = rom.find(head, k + 1)
        assert len(hits) == 1, "the move descriptions: %s" % [hex(h) for h in hits]
        t.moves, t.abilities, descs = 1024, 1793, hits[0]
        assert all(B <= u32(descs + 4 * (m - 1)) < B + len(rom) for m in range(1, t.moves)), "a move description"
    t.move_descs = descs

    t.items = 769
    items = u32(0x1C8) - B
    while rom[items + 44 * t.items] != 0xC8 or rom[items + 44 * t.items + 1:items + 44 * t.items + 4] != b"\xd9\xeb\x00":
        t.items += 1                            # up to the first "New Item", the name of every unused id
        assert t.items < 800, "no end to the items"

    t.egg_moves = u32(EGG_MOVES_WORD) - B
    assert u16(t.egg_moves) > 20000, "the egg-move list does not start with a species"
    t.dex_entries = u32(DEX_ENTRIES_WORD) - B
    assert 0 <= t.dex_entries < len(rom), "the Pokédex entries"

    t.trainer_classes = 71
    while rom[CLASS_NAMES + 13 * t.trainer_classes] not in (0xFF, 0x00):
        t.trainer_classes += 1
    return t
