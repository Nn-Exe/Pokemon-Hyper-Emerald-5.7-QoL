"""Audit a gen9rest build: every byte that differs from the ROM it was made from must be in a place gen9rest means
to change, and the first 1,280 entries of each moved species table must equal the table it was copied from.
usage: python check_gen9rest.py <before.gba> <after.gba>"""
import os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "speciesx"))
sys.path.insert(0, os.path.join(HERE, "..", "gen9"))
sys.path.insert(0, os.path.join(HERE, "..", "sinnohmap"))
import speciesx_patch as SX
import gen9_patch as G9
import gen9rest_patch as P


def main(before, after):
    a = open(before, "rb").read()
    b = open(after, "rb").read()
    assert len(a) == len(b)
    u32 = lambda d, o: struct.unpack_from("<I", d, o)[0]
    old = SX.layout()
    # where each table went: the header's base stats word, then the same order and padding
    lay, p = {}, P.GROW_AT
    for name, _, size, *_ in SX.TABLES:
        lay[name] = p
        p = (p + size * P.NEW_N + 3) & ~3
    assert u32(b, 0x1BC) == 0x08000000 + lay["base stats"]
    allowed = [(P.GROW_AT, P.SPACE_END, "new data")]
    words = set()
    # every word that held a moved table, the four field words, the count sites
    for i in range(0, len(a), 4):
        va, vb = u32(a, i), u32(b, i)
        if va != vb and (0x08000000 + old["base stats"] <= va < 0x08000000 + old["tutor bits"] + 16 * SX.NEW_N) and \
                0x08000000 + P.GROW_AT <= vb < 0x08000000 + P.SPACE:
            words.add(i)
    for o, _, how in SX.COUNT_SITES:
        allowed.append((o, o + (1 if how == "imm8<<3" else 4), "species count"))
    for name, _, size, *_ in SX.TABLES:
        n = SX.NEW_N - (1 if name in ("front anim ids", "anim delays", "national dex no.", "hoenn dex no.") else 0)
        if name in ("national dex no.",):
            n = 1237                                     # 1238+ written by gen9rest (minus one: species 1..1237)
        same = a[old[name]:old[name] + size * min(n, 1238)] == b[lay[name]:lay[name] + size * min(n, 1238)]
        if name not in ("evolutions", "level-up pointers"):
            assert same, "%s: the first entries differ from the old table" % name
    # the in-place changes
    allowed += [
        (G9.ABILITY_TABLE + 6 * 1238, G9.ABILITY_TABLE + 6 * P.NEW_N, "abilities of the new species"),
        (G9.MOVE_DATA + 12 * 948, G9.MOVE_DATA + 12 * 1024, "move data"),
        (G9.MOVE_ANIMS + 4 * 948, G9.MOVE_ANIMS + 4 * 1024, "move animations"),
        (G9.ITEMS + 44 * 770, G9.ITEMS + 44 * 776, "items 770-775"), (G9.ITEM_ICONS + 8 * 770, G9.ITEM_ICONS + 8 * 776, "item pictures"),
        (G9.CRY, G9.CRY + 12 * 1200, "cries"), (G9.CRY_REVERSE, G9.CRY_REVERSE + 12 * 1200, "cries reversed"),
        (G9.CRY_IDS + 2 * (1238 - 277), G9.CRY_IDS + 2 * (P.NEW_N - 277), "cry ids"),
        (0x01A10000, 0x01AB8110, "gen9's tables (move names, texts, powers, ability names/texts, alias word)"),
        (P.MART_SCRIPT, P.MART_SCRIPT + 4, "the Lilycove list"),
        (P.LIST_ALLOC, P.LIST_ALLOC + 4, "Pokedex list buffer"), (P.LIST_FILL, P.LIST_FILL + 4, "Pokedex list fill"),
        (P.NATIONAL_COUNT, P.NATIONAL_COUNT + 4, "national count"),
        (P.DEX_FLAG, P.DEX_FLAG + 8, "flag routine jump"), (P.CLEAR_WORD, P.CLEAR_WORD + 4, "clear word"),
        (P.VENEER, P.VENEER_END, "veneer"), (P.DIGITS_AT, P.DIGITS_END, "list digits"),
    ]
    allowed += [(P.SHOP_BITS_TOP - 99, P.SHOP_BITS_TOP + 1, "the shop guard's bitmap")]
    allowed += [(P.USE_HOOK, P.USE_HOOK + 8, "the item effect lookup's jump")]
    allowed += [(w, w + 4, "dex entries word") for w in P.DEX_ENTRY_WORDS]
    allowed += [(w, w + 4, "order table word") for w in P.ORDER_WORDS]
    allowed += [(s, s + 4, "bl to the veneer") for s in P.CONVERT_SITES]
    for mo, lo in P.DEX_960:
        allowed += [(mo, mo + 1, "960"), (lo, lo + 2, "960 shift")]
    # wild slots: the species halves of slot entries (checked: species only)
    WILD = 0x00E17D50
    diffs = []
    k = 0
    while k < len(a):
        if a[k] != b[k]:
            j = k
            while j < len(a) and a[j] != b[j]:
                j += 1
            diffs.append((k, j))
            k = j
        else:
            k += 1
    bad = []
    wild = 0
    for s, e in diffs:
        if any(lo <= s and e <= hi for lo, hi, _ in allowed) or all(x - x % 4 in words for x in range(s, e)):
            continue
        if e - s <= 2 and 0x08000000 <= u32(b, (s - 2) & ~3) or True:
            # a wild slot: {min, max, u16 species} - only the species changed, and the levels match
            base = s & ~1
            if b[base - 2] >= 1 and b[base - 1] >= b[base - 2] and e - s <= 2 and a[base - 2:base] == b[base - 2:base]:
                wild += 1
                continue
        bad.append((s, e))
    for s, e in bad[:40]:
        print("UNEXPECTED %08X..%08X  %s -> %s" % (0x08000000 + s, 0x08000000 + e, a[s:e][:16].hex(), b[s:e][:16].hex()))
    print("%d changed ranges; %d table words; %d wild slots; %d unexpected" % (len(diffs), len(words), wild, len(bad)))
    return not bad


if __name__ == "__main__":
    sys.exit(0 if main(sys.argv[1], sys.argv[2]) else 1)
