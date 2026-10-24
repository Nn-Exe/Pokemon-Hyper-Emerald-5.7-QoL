"""Writes keytrainers.json from two ROMs: the game the edits were made on and the edited copy.
usage: python -I make_data.py <base.gba> <edited.gba>

For every trainer of gTrainers (0x090019F8, 40 bytes each) whose struct or party differs: the struct bytes that
differ, and every party entry that differs, as raw bytes (old and new) with the fields read out for people to read.
It stops on any difference that is not inside a trainer's struct or party (the edited ROM must be the base plus
trainer edits and nothing else) and on a party that was moved or resized.
"""
import hashlib, json, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools", "romdata"))
import tables

TRAINERS, COUNT, SIZE = 0x010019F8, 1459, 40
ITEMS = 0x00FC2C7C                               # 44 bytes an item, the name first
CHARS = {0xA1 + i: c for i, c in enumerate("0123456789!?.-")}
CHARS.update({0xBB + i: chr(65 + i) for i in range(26)})
CHARS.update({0xD5 + i: chr(97 + i) for i in range(26)})
CHARS.update({0x00: " ", 0xB4: "'", 0xB5: "(m)", 0xB6: "(f)", 0xAD: ".", 0xAE: "-", 0xB8: ","})


def text(rom, o, n):
    out = []
    for b in rom[o:o + n]:
        if b == 0xFF:
            break
        out.append(CHARS.get(b, "?"))
    return "".join(out).strip()


def main(base_path, edited_path):
    a, b = open(base_path, "rb").read(), open(edited_path, "rb").read()
    assert len(a) == len(b) == 0x2000000
    T = tables.of(b)
    u16 = lambda rom, o: struct.unpack_from("<H", rom, o)[0]
    u32 = lambda rom, o: struct.unpack_from("<I", rom, o)[0]
    sp = lambda i: text(b, T.table["names"] + 11 * i, 11)
    mv = lambda i: text(b, T.move_names + 13 * i, 13) if i else ""
    it = lambda i: text(b, ITEMS + 44 * i, 14) if i else ""

    owned = set()
    out = []
    for t in range(COUNT):
        e = TRAINERS + SIZE * t
        owned.update(range(e, e + SIZE))
        flags, psize, pptr = a[e], a[e + 32], u32(a, e + 36)
        if not (0x08000000 <= pptr < 0x0A000000) or psize > 6:
            continue
        esz = 16 if flags & 1 else 8
        p = pptr - 0x08000000
        owned.update(range(p, p + esz * psize))
        if a[e:e + SIZE] == b[e:e + SIZE] and a[p:p + esz * psize] == b[p:p + esz * psize]:
            continue
        assert (b[e], b[e + 32], u32(b, e + 36)) == (flags, psize, pptr), "trainer %d: its party was moved or resized" % t
        entry = {"id": t, "name": text(b, e + 4, 12), "struct": [], "party": []}
        for k in range(SIZE):
            if a[e + k] != b[e + k]:
                entry["struct"].append({"offset": k, "old": a[e + k], "new": b[e + k]})
        for k in range(psize):
            o = p + esz * k
            if a[o:o + esz] == b[o:o + esz]:
                continue

            def read(rom):
                d = {"iv": u16(rom, o), "level": u16(rom, o + 2), "species": u16(rom, o + 4)}
                d["species_name"] = sp(d["species"])
                if flags & 2:
                    d["item"] = u16(rom, o + 6)
                    d["item_name"] = it(d["item"])
                if flags & 1:
                    d["moves"] = [u16(rom, o + 8 + 2 * j) for j in range(4)]
                    d["move_names"] = [mv(m) for m in d["moves"]]
                return d
            entry["party"].append({"slot": k + 1, "offset": "0x%08X" % (0x08000000 + o), "old_bytes": a[o:o + esz].hex(),
                                   "new_bytes": b[o:o + esz].hex(), "old": read(a), "new": read(b)})
        out.append(entry)

    stray = [i for i in range(len(a)) if a[i] != b[i] and i not in owned]
    assert not stray, "differences outside the trainers: %s" % [hex(0x08000000 + i) for i in stray[:10]]
    data = {"base_sha1": hashlib.sha1(a).hexdigest(), "edited_sha1": hashlib.sha1(b).hexdigest(), "trainers": out}
    with open(os.path.join(HERE, "keytrainers.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print("keytrainers.json: %d trainers, %d party entries, %d struct bytes" % (
        len(out), sum(len(x["party"]) for x in out), sum(len(x["struct"]) for x in out)))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
