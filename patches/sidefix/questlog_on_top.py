"""Put a Quest Log text change into the finished game without rebuilding it (the Mac cannot run `gen9`).

    python questlog_on_top.py <main old> <main new> <game in> <game out>

<main old> / <main new>: the main chain (v1.4 archive + shinybox + every patch to `zhtext`) built with the Quest
Log's data as it was and as it is now. The bytes the two differ in must all be Quest Log data, and the finished game
must hold <main old>'s bytes there (nothing after the chain wrote them); they are copied over.

One thing the copy alone would get wrong: `paldea` (journal_az.py) made its own copies of the Journal's and the
Legends' info-panel tables (PANES[0] and PANES[1] point at them), and their rows point at strings in the Quest Log's
panel block, which move when any of its tables grows or shrinks. Each of those pointers is moved to where the same
string is in the new block - which is what `paldea` itself writes when the whole chain is run again, because it
copies the rows from the table as it then is. Every pointer of the game into the panel block from anywhere else is
checked to be one of those rows (or the same as in <main old>, where it is a chance match in other data).
"""
import struct, sys
import numpy as np

B = 0x08000000
PANES = 0x08FED35C                      # 4 words: the info-panel tables of Journal, Legends, Key Items, Side Content
PAGES = 0x08FEC5EC                      # 9 chapters of 8 bytes {first, rows, objectives, type, name}
PANE_LO, PANE_HI = 0x09FA0000, 0x09FB0000   # questlog_patch.PANE_FREE..PANE_END
ROW = 16                                # {kind, 0, id u16, location, text, hidden}


def u32(r, a): return struct.unpack_from("<I", r, a - B)[0]


def string(r, a):
    o = a - B
    return bytes(r[o:r.index(b"\xff", o) + 1])


def pane_strings(r):
    """content -> address of every string the main build's four panel tables point at."""
    out = {}
    counts = [sum(r[PAGES - B + 8 * k + 1] for k in range(4)) + 1,       # the Journal's steps and its closing row
              r[PAGES - B + 8 * 4 + 1], r[PAGES - B + 8 * 5 + 1],         # Legends, Key Items
              r[PAGES - B + 8 * 6 + 1] + r[PAGES - B + 8 * 7 + 1]]       # Side Content, then the Badges
    for t, n in zip(range(4), counts):
        base = u32(r, PANES + 4 * t)
        for i in range(n):
            for k in (4, 8, 12):
                p = u32(r, base + ROW * i + k)
                if PANE_LO <= p < PANE_HI:
                    s = string(r, p)
                    assert out.setdefault(s, p) == p, "one string at two places"
    return out


def main(old_p, new_p, game_p, out_p):
    old, new, game = (bytearray(open(p, "rb").read()) for p in (old_p, new_p, game_p))
    for r in (old, new, game):
        assert r[0xAC:0xB0] == b"BPEE" and len(r) == 0x2000000
    a, b, g = (np.frombuffer(bytes(x), dtype=np.uint8) for x in (old, new, game))
    diff = np.nonzero(a != b)[0]
    assert len(diff), "the two main builds are the same"
    lo, hi = int(diff.min()) + B, int(diff.max()) + B
    for k in diff:                                          # all inside the Quest Log's own blocks
        x = int(k) + B
        assert 0x08FEA000 <= x < 0x08FED3C8 or 0x09F9A000 <= x < 0x09F9E000 or PANE_LO <= x < PANE_HI, "%08X" % x
    bad = np.nonzero(g[diff] != a[diff])[0]
    assert not len(bad), "the game changed the Quest Log data after the chain: %s" % [
        "%08X" % (int(diff[i]) + B) for i in bad[:8]]
    old_s = {p: s for s, p in pane_strings(old).items()}
    new_s = pane_strings(new)
    o = np.frombuffer(bytes(game), dtype=np.uint8).copy()
    o[diff] = b[diff]
    out = bytearray(o.tobytes())
    # paldea's copies of the Journal's and the Legends' panel tables
    moved = 0
    rows_j = sum(game[PAGES - B + 8 * k + 1] for k in range(4)) + 1
    rows_l = game[PAGES - B + 8 * 4 + 1]
    copies = []
    for t, n in ((0, rows_j), (1, rows_l)):
        base = u32(game, PANES + 4 * t)
        assert not (PANE_LO <= base < PANE_HI), "PANES[%d] is the Quest Log's own table: no copy to fix" % t
        copies.append((base, base + ROW * n))
        for i in range(n):
            for k in (4, 8, 12):
                at = base + ROW * i + k
                p = u32(game, at)
                if PANE_LO <= p < PANE_HI:
                    s = old_s.get(p)
                    assert s is not None, "%08X -> %08X is not a string of the old panel tables" % (at, p)
                    assert s in new_s, "%r is not in the new panel tables" % s
                    struct.pack_into("<I", out, at - B, new_s[s])
                    moved += 1
    # nothing else of the game may point into the panel block, other than where <main old> has the same word
    w = np.frombuffer(bytes(game), dtype="<u4")
    wo = np.frombuffer(bytes(old), dtype="<u4")
    for i in np.nonzero((w >= PANE_LO) & (w < PANE_HI))[0]:
        at = int(i) * 4 + B
        if PANE_LO <= at < PANE_HI or any(c0 <= at < c1 for c0, c1 in copies):
            continue
        assert wo[i] == w[i], "%08X points into the panel block and is not one of the known rows" % at
    open(out_p, "wb").write(out)
    print("%d bytes copied (%08X..%08X), %d pointers in paldea's panel tables moved" % (len(diff), lo, hi, moved))


if __name__ == "__main__":
    main(*sys.argv[1:5])
