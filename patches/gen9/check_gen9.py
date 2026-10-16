"""Audit a build with speciesx + gen9 against the ROM it was made from: every byte that differs must be one of
the changes the two patches are meant to make, and everything below slot 1200 must read as it did.
usage: python check_gen9.py <before.gba> <after.gba>      (exits 1 on anything unexplained)

Checks:
  1. each changed byte falls in a listed place: the new table block, gen9's data block, a repointed literal
     (the word before was a table address, the word after is the same table's new address), a count site, the
     ability table's new rows, the cry tables' rows 388-425, the cry-id entries of the new slots, the Pokedex
     entries 906-940, the end of the egg move list and its bound, the move data and animation entries of the
     new moves, Booster Energy's item row and picture entry, the six hook sites;
  2. the first 1,200 entries of every moved table are byte-identical to the old table (1,199 for the tables
     indexed by species - 1, and for the tutor bits), and the old tables are untouched;
  3. the first 342 ability names and texts are the old ones but for the ids gen9 names;
  4. the first 938 move names, Z-Move and Max Move power bytes and the first 937 description pointers are the
     old ones (the 938th description entry belonged to no move and is now the first new move's);
  5. what a span check cannot see: no code literal still holds a moved table's old address, the number of
     repointed words is the number the two patchers expect, the count sites hold 1,280, and the hook sites
     either still hold the engine's own words (a --no-effects build) or all lead into gen9's code.
"""
import os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "speciesx"))
sys.path.insert(0, HERE)
import speciesx_patch as SX
import gen9_data as D
import gen9_patch as G


def main(before_path, after_path):
    a = open(before_path, "rb").read()
    b = open(after_path, "rb").read()
    assert len(a) == len(b) == 0x2000000
    u32 = lambda d, o: struct.unpack_from("<I", d, o)[0]
    lay = SX.layout()
    old = {t[0]: (t[1], t[2], t[4]) for t in SX.TABLES}
    n_new = len(D.SPECIES)
    first, last = D.FIRST_SLOT, D.FIRST_SLOT + n_new - 1
    problems = []

    # ---- 2. the old species read as before
    for name, (off, size, minus_one) in old.items():
        keep = SX.OLD_N - 1 if minus_one else SX.OLD_N
        if b[lay[name]:lay[name] + size * keep] != a[off:off + size * keep]:
            problems.append("%s: the first %d entries differ from the old table" % (name, keep))
        if b[off:off + size * SX.OLD_N] != a[off:off + size * SX.OLD_N]:
            problems.append("%s: the old table was written to" % name)
    names_at, texts_at = u32(b, 0x1C0) - 0x08000000, u32(b, 0x1C4) - 0x08000000
    named = {v[0] for v in D.ABILITY_ALIAS.values()} | {v[0] for v in D.ABILITY_NEW.values()}
    for i in range(G.OLD_ABILITIES):
        if i in named:
            continue
        if b[names_at + 13 * i:names_at + 13 * i + 13] != a[G.ABILITY_NAMES + 13 * i:G.ABILITY_NAMES + 13 * i + 13]:
            problems.append("ability %d: name changed" % i)
        if u32(b, texts_at + 4 * i) != u32(a, G.ABILITY_TEXT + 4 * i):
            problems.append("ability %d: text pointer changed" % i)

    # ---- 4. the old moves read as before
    moved = {"move names": (G.MOVE_NAMES_AT, u32(b, 0x148) - 0x08000000, 13 * G.OLD_MOVES),
             "move descriptions": (G.MOVE_TEXT, u32(b, 0x1C3EFC) - 0x08000000, 4 * (G.OLD_MOVES - 1)),
             "Z-Move power": (G.Z_POWER, u32(b, 0x1D5F050) - 0x08000000, G.OLD_MOVES),
             "Max Move power": (G.MAX_POWER, u32(b, 0x1D5F060) - 0x08000000, G.OLD_MOVES)}
    for name, (was, now, size) in moved.items():
        if not (G.SPACE <= now < G.SPACE_END):
            problems.append("%s: not moved into gen9's data (%08X)" % (name, 0x08000000 + now))
        elif b[now:now + size] != a[was:was + size]:
            problems.append("%s: the old entries differ from the old table" % name)
    n_moves = len(D.NEW_MOVES)
    for i, row in enumerate(D.NEW_MOVES):
        m = D.FIRST_MOVE + i
        at = moved["move names"][1] + 13 * m
        if b[at:at + len(row[1]) + 1] != G.text(row[1]):
            problems.append("move %d is not named %s" % (m, row[1]))
        if not G.SPACE <= u32(b, moved["move descriptions"][1] + 4 * (m - 1)) - 0x08000000 < G.SPACE_END:
            problems.append("move %d has no description" % m)
        if b[moved["Z-Move power"][1] + m] != row[10] or b[moved["Max Move power"][1] + m] != row[11]:
            problems.append("move %d: Z-Move or Max Move power" % m)

    # ---- Frigibax's egg moves: after the old list, inside the bound GetEggMoves searches up to
    eggs = struct.unpack_from("<%dH" % 3000, b, G.EGG_MOVES)
    marker = 20000 + first + [k for k, *_ in D.SPECIES].index("frigibax")
    if marker not in eggs or eggs.index(marker) > u32(b, G.EGG_BOUND):
        problems.append("Frigibax's egg moves are not inside the list's bound")
    elif eggs[:eggs.index(marker)] != struct.unpack_from("<%dH" % eggs.index(marker), a, G.EGG_MOVES):
        problems.append("the egg move list before Frigibax's entry changed")

    # ---- 1. every changed byte is explained
    table_moves = {0x08000000 + off: 0x08000000 + lay[name] for name, (off, size, _) in old.items()}
    table_moves[0x08000000 + G.ABILITY_NAMES] = 0x08000000 + names_at
    table_moves[0x08000000 + G.ABILITY_TEXT] = 0x08000000 + texts_at
    for name, (was, now, size) in moved.items():
        table_moves[0x08000000 + was] = 0x08000000 + now
    for k, field in SX.FIELD_WORDS:
        table_moves[0x08000000 + old["base stats"][0] + field] = 0x08000000 + lay["base stats"] + field
    spans = [(SX.DEST, SX.DEST_END, "the new species tables"),
             (G.SPACE, G.SPACE_END, "gen9's data"),
             (G.ABILITY_TABLE + 6 * first, G.ABILITY_TABLE + 6 * (last + 1), "ability rows of the new slots"),
             (G.CRY + 12 * 388, G.CRY + 12 * (388 + n_new), "cry table rows"),
             (G.CRY_REVERSE + 12 * 388, G.CRY_REVERSE + 12 * (388 + n_new), "reverse cry table rows"),
             (G.CRY_IDS + 2 * (first - 277), G.CRY_IDS + 2 * (last + 1 - 277), "cry ids of the new slots"),
             (G.DEX_ENTRIES + 32 * D.FIRST_DEX, G.DEX_ENTRIES + 32 * (D.FIRST_DEX + n_new), "Pokedex entries"),
             (G.EGG_END, G.EGG_END + 32, "the end of the egg move list"),
             (G.EGG_BOUND, G.EGG_BOUND + 4, "the egg move list's bound"),
             (G.MOVE_DATA + 12 * D.FIRST_MOVE, G.MOVE_DATA + 12 * (D.FIRST_MOVE + n_moves), "data of the new moves"),
             (G.MOVE_ANIMS + 4 * D.FIRST_MOVE, G.MOVE_ANIMS + 4 * (D.FIRST_MOVE + n_moves), "animations of the new moves"),
             (G.ITEMS + 44 * D.BOOSTER_ENERGY, G.ITEMS + 44 * (D.BOOSTER_ENERGY + 1), "Booster Energy's item row"),
             (G.ITEM_ICONS + 8 * D.BOOSTER_ENERGY, G.ITEM_ICONS + 8 * (D.BOOSTER_ENERGY + 1), "Booster Energy's picture"),
             (G.ENTER, G.ENTER + 8, "hook: the ability of the Pokemon coming in"),
             (G.LOOKUP, G.LOOKUP + 8, "hook: the engine's ability lookup"),
             (G.SPEED, G.SPEED + 8, "hook: the engine's speed routine"),
             (G.COMMAND_0, G.COMMAND_0 + 4, "hook: command 0, a battler starts on a move"),
             (G.COMMAND_5, G.COMMAND_5 + 4, "hook: command 5, the damage calculation"),
             (G.FIXED_DAMAGE, G.FIXED_DAMAGE + 4, "hook: routine 24, the fixed-damage calculation")]
    spans += [(off, off + len(was) // 2, "species count") for off, was, how in SX.COUNT_SITES]
    counts, literals = {}, 0
    i, n = 0, len(a)
    while i < n:
        if a[i] == b[i]:
            # skip ahead quickly over equal stretches
            j = i + 4096
            if a[i:j] == b[i:j]:
                i = j
                continue
            i += 1
            continue
        why = next((label for lo, hi, label in spans if lo <= i < hi), None)
        if why is None:
            w = i & ~3
            if table_moves.get(u32(a, w)) == u32(b, w):
                why, literals = "repointed literals", literals + (1 if i == w or a[w:i] == b[w:i] else 0)
        if why is None:
            problems.append("%08X: %02X -> %02X is not explained" % (0x08000000 + i, a[i], b[i]))
            if len(problems) > 40:
                break
        else:
            counts[why] = counts.get(why, 0) + 1
        i += 1
    # ---- 5. content the spans cannot vouch for
    expected = sum(t[3] for t in SX.TABLES) + len(SX.FIELD_WORDS) + G.ABILITY_NAME_WORDS + G.ABILITY_TEXT_WORDS + \
        G.MOVE_NAME_WORDS + G.MOVE_TEXT_WORDS + G.Z_POWER_WORDS + G.MAX_POWER_WORDS
    if literals != expected:
        problems.append("%d literal words were repointed, %d expected" % (literals, expected))
    old_addresses = set(table_moves)
    for k, v in enumerate(struct.unpack_from("<%dI" % (len(b) // 4), b)):
        if v in old_addresses and SX.is_pointer(b, k * 4):
            problems.append("%08X still holds %08X, the old address of a table that moved" % (0x08000000 + k * 4, v))
    for off, was, how in SX.COUNT_SITES:
        got = b[off] << 3 if how == "imm8<<3" else u32(b, off) + (1 if how == "count-1" else 0)
        if got != SX.NEW_N:
            problems.append("count site %08X holds %d" % (0x08000000 + off, got))
    code = lambda v: G.SPACE <= (v & ~1) - 0x08000000 < G.SPACE_END and v & 1
    jumps = [u32(b, site + 4) for site in (G.ENTER, G.LOOKUP, G.SPEED) if b[site:site + 4] == bytes.fromhex("004b1847")]
    words = [u32(b, site) for site in (G.COMMAND_0, G.COMMAND_5, G.FIXED_DAMAGE)]
    untouched = all(b[site:site + 8] == a[site:site + 8] for site in (G.ENTER, G.LOOKUP, G.SPEED)) and \
        all(u32(b, site) == u32(a, site) for site in (G.COMMAND_0, G.COMMAND_5, G.FIXED_DAMAGE))
    hooked = len(jumps) == 3 and all(map(code, jumps)) and all(map(code, words))
    if not (untouched or hooked):
        problems.append("the six hook sites are neither the engine's own nor all gen9's: %s" % ", ".join(
            "%08X" % v for v in jumps + words))
    print("  hooks: %s" % ("the engine's own (a build without gen9.s)" if untouched else "all six lead into gen9's code"))
    for why, c in sorted(counts.items(), key=lambda kv: -kv[1]):
        print("  %8d bytes  %s" % (c, why))
    print("  %d literal words repointed" % literals)
    if problems:
        print("PROBLEMS:")
        for p in problems[:60]:
            print("  " + p)
        sys.exit(1)
    print("check_gen9: every difference is accounted for; species below 1200, abilities below 342 and moves "
          "below 938 read as before")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
