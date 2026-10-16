"""Egg moves for Gen 9 - for the Whole Gen 9 TEST build only (after gen9rest and gen9dex).

    python -I gen9egg_patch.py <whole Gen 9 build> <out.gba>

Found while testing test 5 (the user, 2026-10-15: "Learning moves: ... the Move Relearner and the egg moves"): of the
Gen 9 Pokemon only Frigibax has an egg-move list (gen9 added it); gen9rest added none, so a Sprigatito, Lechonk or
Tinkatink bred at the Day Care never got an egg move, and the DexNav (which gives a found Pokemon one of its egg moves
now and then, 0x08FDEA70) had none to give. This adds Scarlet/Violet's list (official.json "egg", PokeAPI) for each
Gen 9 Pokemon an Egg hatches as: a slot nothing evolves into, that can breed (not "no-eggs"), with no list yet.
A move this game does not have is left out, as gen9rest leaves it out of the Pokemon's other lists (its move()).

The table (species + 20000, then its moves; 0xFFFF at the end) is full where it is (408 bytes after it), so it is
copied whole to zero-filled space and the new lists go after the old ones. Three words name it: GetEggMoves'
(0x080703F0), BuildEggMoveset's (0x08070468) and the DexNav's egg-move picker's (0x08FDEAE0); GetEggMoves' bound
(0x08070464: the number of halfwords before the 0xFFFF, minus one) grows with it. The eggmoves patch's buffer holds
32 moves: every list must fit. The main game (rom/) is not touched; its Gen 9 is gen9's, which has Frigibax's list.
"""
import json, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path[:0] = [os.path.join(REPO, "patches", "gen9"), os.path.join(REPO, "patches", "gen9rest")]
import gen9_data as D9
import gen9rest_data as D

B = 0x08000000
OLD_TABLE = 0x09D78128
TABLE_WORDS = [0x080703F0, 0x08070468, 0x08FDEAE0]
BOUND = 0x08070464
NEW_AT, NEW_END = 0x09C29000, 0x09C30000             # zero-filled, after gen9dex (nothing points in)
MARK, END = 20000, 0xFFFF
BUFFER = 32                                          # eggmoves: the egg's list buffer (0x02031C00, 32 moves)
GROW_AT, NEW_N = 0x01AC0000, 1408                    # gen9rest's species tables (speciesx's 23, in its order)


def u16(rom, a): return struct.unpack_from("<H", rom, a - B)[0]
def u32(rom, a): return struct.unpack_from("<I", rom, a - B)[0]


def norm(s):
    return "".join(c for c in s.lower() if c.isalnum())


def game_names(rom):
    """move name (normalised) -> id, from the game's own table (header 0x148), as gen9rest's move_by"""
    chars = {}
    for i, c in enumerate("0123456789!?.-"):
        chars[0xA1 + i] = c
    for i in range(26):
        chars[0xBB + i], chars[0xD5 + i] = chr(65 + i), chr(97 + i)
    chars[0x00], chars[0xB4], chars[0xAE] = " ", "'", "-"
    names = u32(rom, B + 0x148)
    by = {}
    for m in range(1, D.FIRST_MOVE):
        raw = rom[names - B + 13 * m:names - B + 13 * m + 13].split(b"\xff")[0]
        nm = "".join(chars.get(b, "?") for b in raw)
        if nm.strip("-").strip():
            by.setdefault(norm(nm), m)
    return by


def move_id(name, species, move_by):
    """gen9rest_patch.move(): the same mapping, so a Pokemon's egg moves are named as its other lists are"""
    name = D.MOVE_BY_SPECIES.get((name, species), name)
    name = D9.MOVE_BY_SPECIES.get((name, species), name)
    new_move = {k: D.FIRST_MOVE + i for i, (k, *_) in enumerate(D.NEW_MOVES)}
    if name in new_move:
        return new_move[name]
    if name in D.MOVES_LEFT_OUT or name in D9.MOVES_NOT_IN_GAME and name not in new_move:
        return None
    g9 = [k for k, *_ in D9.NEW_MOVES]
    if name in g9:
        return D9.FIRST_MOVE + g9.index(name)
    m = move_by.get(norm(D9.MOVE_NAMES.get(name, name)))
    assert m, "%s: not in the game and not listed" % name
    return m


def table_entries(rom, at):
    out = []
    while u16(rom, at + 2 * len(out)) != END:
        out.append(u16(rom, at + 2 * len(out)))
    return out


def main(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    old = table_entries(rom, OLD_TABLE)
    assert all(u32(rom, w) == OLD_TABLE for w in TABLE_WORDS), "the egg table is not where it was"
    assert u32(rom, BOUND) == len(old) - 1, "GetEggMoves' bound"
    assert not any(rom[NEW_AT - B:NEW_END - B]), "the new table's room is not empty"
    have = {v - MARK for v in old if v > MARK}

    # the species: slots 1200-1326 with the official key each
    o9 = json.load(open(os.path.join(REPO, "patches", "gen9", "official.json"), encoding="utf-8"))
    o9r = json.load(open(os.path.join(REPO, "patches", "gen9rest", "official.json"), encoding="utf-8"))
    key_of = {}
    for i, t in enumerate(D9.SPECIES):
        k = t[0] if t[0] in o9 else t[0].split("-")[0]
        key_of[D9.FIRST_SLOT + i] = (k, o9[k])
    for i, t in enumerate(D.SPECIES):
        key_of[D.FIRST_SLOT + i] = (t[0], o9r[t[0]])
    # what evolves into what: the evolution table (40 bytes a species: five {method, parameter, target, 0})
    sys.path.insert(0, os.path.join(REPO, "patches", "speciesx"))
    import speciesx_patch as SX
    lay, pos = {}, GROW_AT
    for name, _, size, *_ in SX.TABLES:
        lay[name] = pos
        pos = (pos + size * NEW_N + 3) & ~3
    assert B + lay["names"] == u32(rom, B + 0x144) and B + lay["base stats"] == u32(rom, B + 0x1BC), \
        "the species tables are not gen9rest's"
    targets = set()
    for s in range(1, NEW_N):
        for k in range(5):
            method, _, target = struct.unpack_from("<HHH", rom, lay["evolutions"] + 40 * s + 8 * k)
            if method:
                targets.add(target)

    move_by = game_names(rom)
    added, report, left_out = [], [], set()
    for slot in sorted(key_of):
        key, o = key_of[slot]
        if slot in targets or slot in have or "no-eggs" in o["egg_groups"] or not o.get("egg"):
            continue
        ids = []
        for mv in o["egg"]:
            m = move_id(mv, key, move_by)
            if m is None:
                left_out.add(mv)
            elif m not in ids:
                ids.append(m)
        if not ids:
            continue
        assert len(ids) <= BUFFER, "%s: %d egg moves" % (key, len(ids))
        added.append([MARK + slot] + sorted(ids))
        report.append("  %4d %-24s %2d" % (slot, key, len(ids)))
    new = old + [v for row in added for v in row]
    data = struct.pack("<%dH" % (len(new) + 1), *new, END)
    assert NEW_AT + len(data) <= NEW_END
    rom[NEW_AT - B:NEW_AT - B + len(data)] = data
    for w in TABLE_WORDS:
        struct.pack_into("<I", rom, w - B, NEW_AT)
    struct.pack_into("<I", rom, BOUND - B, len(new) - 1)
    open(outp, "wb").write(rom)
    print("gen9egg: %d Gen 9 lists (%d moves) after the %d halfwords of the old table, now at %08X..%08X; "
          "bound %d; left out (not in the game): %s"
          % (len(added), sum(len(r) - 1 for r in added), len(old), NEW_AT, NEW_AT + len(data), len(new) - 1,
             ", ".join(sorted(left_out)) or "none"))
    print("\n".join(report))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
