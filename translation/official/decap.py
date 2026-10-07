"""The casing the earlier "Modern" pass used, learned from the texts it already converted in place:
for every official text whose hack bytes are the same text in another case, each ALL-CAPS word is paired with what
it became. build(rom, scan.json) -> {WORD: most common replacement}; apply(text, table) rewrites a source text."""
import collections, json, re
import scan as S

WORD = re.compile(r"[A-Zé][A-Zé'.\-]*[A-Zé]|[A-Z]")


def plain(src):
    """a source text with {TOKENS} kept as written and escapes as written"""
    return src


def hack_text(rom, addr, n):
    o = addr - 0x08000000
    cur = rom[o:o + n]
    end = cur.find(b"\xff")
    return cur if end < 0 else cur[:end]


def letters(b):
    """bytes -> string of letters only where both sides can be aligned one to one (same length encodings)"""
    out = []
    for c in b:
        if 0xBB <= c <= 0xD4:
            out.append(chr(65 + c - 0xBB))
        elif 0xD5 <= c <= 0xEE:
            out.append(chr(97 + c - 0xD5))
        elif c == 0x1B:
            out.append("é")
        elif c == 0x06:
            out.append("É")
        else:
            out.append("\x00")
    return "".join(out)


def build(rom, scanpath):
    import vanilla as V
    table = collections.defaultdict(collections.Counter)
    for x in json.load(open(scanpath, encoding="utf-8")):
        if x["kind"] != "other" or not x.get("terminated"):
            continue
        raw = V.encode(x["en"] + "$")[:-1]
        cur = hack_text(rom, int(x["addr"], 16), len(raw) + 1)
        if len(cur) != len(raw):
            continue
        a, b = letters(raw), letters(cur)
        if a.lower() != b.lower():
            continue
        for m in re.finditer(r"[A-ZÉ][A-ZÉ]+", a.replace("é", "É").replace("\x00", " ")):
            w = a[m.start():m.end()]
            table[w][b[m.start():m.end()]] += 1
    return {w: c.most_common(1)[0][0] for w, c in table.items()}, table


KEEP = {"TM", "HM", "PC", "HP", "PP", "OK", "TV", "ID", "KO", "EXP", "PKMN", "LV", "TMS", "HMS", "II", "III", "IV", "VI", "VII",
        "VIII", "IX", "RS", "GBA", "AGB", "DMA", "EV", "IV", "SP", "ATK", "DEF", "UFO", "SOS", "EON", "DJ", "MC", "BP", "PK", "RPM"}


def apply(text, table):
    """ALL-CAPS words of a source text (outside {TOKENS} and escapes) -> the learned casing, else Title case"""
    out, i = [], 0
    for m in re.finditer(r"\{[^}]*\}|\\.|[A-Zé]{2,}", text):
        out.append(text[i:m.start()])
        w = m.group(0)
        if w[0] in "{\\":
            out.append(w)
        else:
            if w in KEEP or not re.search(r"[A-Z]", w):
                out.append(w)
            elif w in table:
                out.append(table[w])
            elif False:
                out.append(w)
            else:
                out.append(w[0] + w[1:].lower())
        i = m.end()
    out.append(text[i:])
    return "".join(out)


if __name__ == "__main__":
    import sys
    rom = open(sys.argv[1], "rb").read()
    t, full = build(rom, sys.argv[2])
    json.dump(t, open(sys.argv[3], "w", encoding="utf-8"), ensure_ascii=False, indent=0, sort_keys=True)
    amb = {w: dict(c) for w, c in full.items() if len(c) > 1}
    print(len(t), "words learned;", len(amb), "with more than one casing")
    for w in list(amb)[:25]:
        print("  ", w, amb[w])
