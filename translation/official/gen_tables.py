"""hack.json entries for names inside tables (tables.py), and for the Trainer Hill / apprentice names, which are
official Emerald data the hack translated inside the structs (restored from the pret source, in modern casing)."""
import os, re, struct
import scan as S
import vanilla as V
import tables as T

HILL = os.path.join(V.SRC, "src", "data", "battle_frontier", "trainer_hill.h")
APPR = os.path.join(V.SRC, "src", "data", "battle_frontier", "apprentice.h")
FLOOR, TRAINER, MON, NICK = 952, 328, 44, 32        # struct TrainerHillFloor / Trainer / BattleTowerPokemon, nickname at +32


def title(s):
    """ALL CAPS -> modern casing: the first letter of each word stays, the rest go lower-case"""
    out, new = "", True
    for ch in s:
        if ch.isalpha():
            out += ch if new else ch.lower()
            new = False
        else:
            out += ch
            new = ch in " -."
    return out


def field(rom, a, width, text, out, notes, what):
    """one fixed-width name: an in-place entry if the bytes there are not already `text`"""
    o = a - 0x08000000
    raw = rom[o:o + width]
    e = raw.find(b"\xff")
    z = raw if e < 0 else raw[:e + 1]
    enc = V.encode(text + "$")
    if len(enc) > width:
        notes.append("%s: %r does not fit %d bytes" % (what, text, width))
        return
    if raw[:len(enc)] == enc:
        return
    out.append({"a": "%08X" % a, "n": width, "zh": z.hex(), "t": text, "was": S.dec(z.rstrip(b"\xff"))[0], "table": what})


def hill_source():
    """{array name: [(trainer name, [6 nicknames])] * 8} for the four English Trainer Hill modes"""
    text = open(HILL, encoding="utf-8").read()
    res = {}
    for m in re.finditer(r"static const struct TrainerHillFloor (sFloors_\w+)\[\]\s*=\s*\{", text):
        nxt = text.find("static const struct", m.end())
        body = text[m.end():nxt if nxt > 0 else len(text)]
        trainers = []
        for blk in re.split(r"\.name = _+\(", body)[1:]:
            name = re.match(r'"([^"$]*)', blk).group(1)
            nicks = [x.split("$")[0] for x in re.findall(r'\.nickname = _+\("([^"]*)"\)', blk)]
            trainers.append((name, nicks))
        res[m.group(1)] = trainers
    return res


def entries(rom):
    out, notes = [], []
    # the hack's trainers
    missing = set()
    for i in range(T.TRAINER_FIRST, T.TRAINER_LAST + 1):
        a = T.TRAINER_TABLE + T.TRAINER_SIZE * i + 4
        raw = rom[a - 0x08000000:a - 0x08000000 + 12]
        e = raw.find(b"\xff")
        if e < 0 or not any(c in S.LEADS for c in raw[:e]):
            continue
        zh = S.dec(raw[:e])[0]
        if zh not in T.TRAINERS:
            missing.add(zh)
            continue
        field(rom, a, 12, T.TRAINERS[zh], out, notes, "trainer %04X" % i)
    if missing:
        notes.append("trainer names without a translation: " + " ".join(sorted(missing)))
    for table, size, names, width, what in ((T.ITEM_TABLE, T.ITEM_SIZE, T.ITEMS, 14, "item"),
                                            (T.SPECIES_TABLE, T.SPECIES_SIZE, T.SPECIES, 11, "species"),
                                            (T.MOVE_TABLE, T.MOVE_SIZE, T.MOVES, 13, "move")):
        for i, name in names.items():
            field(rom, table + size * i, width, name, out, notes, "%s %d" % (what, i))
    for i in range(T.DEX_FIRST, T.DEX_LAST + 1):
        a = T.DEX_TABLE + T.DEX_SIZE * i
        if any(c in S.LEADS for c in rom[a - 0x08000000:a - 0x08000000 + 12].split(b"\xff")[0]):
            field(rom, a, 12, T.DEX_CATEGORY, out, notes, "dex %d" % i)
    field(rom, T.TURNS_LEFT[0], 13, T.TURNS_LEFT[1], out, notes, "engine")
    # Trainer Hill
    sym = V.symbols()
    src = hill_source()
    for arr in ("sFloors_Normal", "sFloors_Variety", "sFloors_Unique", "sFloors_Expert"):
        base, size = sym[arr][0]
        trainers = src[arr]
        if size != 4 * FLOOR or len(trainers) != 8 or any(len(n) != 6 for _, n in trainers):
            notes.append("%s: unexpected shape (%d bytes, %d trainers)" % (arr, size, len(trainers)))
            continue
        for k, (name, nicks) in enumerate(trainers):
            tr = base + FLOOR * (k // 2) + 4 + TRAINER * (k % 2)
            field(rom, tr, 11, title(name), out, notes, "%s trainer %d" % (arr, k))
            for m, nick in enumerate(nicks):
                field(rom, tr + 64 + MON * m + NICK, 11, title(nick), out, notes, "%s trainer %d mon %d" % (arr, k, m))
    # apprentices: name[6 languages][8]; the hack translated every language's name except the Japanese one
    base, size = sym["gApprentices"][0]
    rows = re.findall(r"\.name = \{([^}]*)\}", open(APPR, encoding="utf-8").read())
    if size != 16 * 88 or len(rows) != 16:
        notes.append("gApprentices: unexpected shape")
    else:
        for i, row in enumerate(rows):
            names = re.findall(r'_\("([^"]*)"\)', row)
            for lang in range(1, 6):
                field(rom, base + 88 * i + 8 * lang, 8, title(names[lang]), out, notes, "apprentice %d language %d" % (i, lang))
    return out, notes
