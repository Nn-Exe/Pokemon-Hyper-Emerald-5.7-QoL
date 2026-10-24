"""The Quest Log's Legends rows for Kitakami's five (2026-10-17, getting Kitakami ready to go into the game: the user,
"do everything needed before merging").

gen9journal lists Okidogi, Munkidori, Fezandipiti, Ogerpon and Pecharunt after the 119 legends it counts, "Locked":
dimmed, a silhouette, "Not in this version yet: it lives in Kitakami, a place this game does not have", and left out
of "Gotta catch 'em all!". With Kitakami in the game all five can be caught (Part 1: Ogerpon at the end of the story,
the Loyal Three where they hide after it; Part 2: Pecharunt), so here they become counted rows as gen9journal's
Paradox rows are:

  * each row (the Legends table, 16 bytes: dex, lock, name, hint, where): lock 0, a hint and a where of its own;
  * each pane (16 bytes: kind, silhouette, species, location, two panels): no forced silhouette, its two panels;
  * the count: legend_all's compare (0x08FEB220) and the chapter's counted rows (its page entry +2) 119 -> 124, and
    row 0's texts ("all 119 of them") again with 124.

The rows stay where gen9journal put them (after the 119: their order is the order they are listed in). The texts go
into Kitakami's blob; the tables are gen9journal's, changed in place, and check() asserts they are as it left them.
"""
import os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
B = 0x08000000
LEG_LIT, NLEG_CMP, PAGES, LEG_PAGE, PANES = 0x08FEB23C, 0x08FEB220, 0x08FEC5EC, 4, 0x08FED35C
PANE_TEXT_W = 158
COUNTED, LOCKED_ROWS = 119, 5
DEX = {"Okidogi": 1014, "Munkidori": 1015, "Fezandipiti": 1016, "Ogerpon": 1017, "Pecharunt": 1025}


def u16(rom, o): return struct.unpack_from("<H", rom, o)[0]
def u32(rom, o): return struct.unpack_from("<I", rom, o)[0]


def _libs():
    for sub in ("paldea", "journal"):
        p = os.path.join(REPO, "patches", sub)
        if p not in sys.path:
            sys.path.append(p)
    import journal_patch as J
    import journal_az as JAZ
    return J, JAZ


def texts(level, p2_level):
    """name -> (hint, where): what the row says (from this build: the levels are kstory's)"""
    hide = ("Mossui Town, Lv%d, where it hides after the Teal Mask story. Once only: if it faints, it is gone for "
            "good." % level)
    return {
        "Okidogi": ("Kitakami: after the Teal Mask story, one of the Loyal Three hides in Mossui Town.", hide),
        "Munkidori": ("Kitakami: after the Teal Mask story, one of the Loyal Three hides in Mossui Town.", hide),
        "Fezandipiti": ("Kitakami: after the Teal Mask story, one of the Loyal Three hides in Mossui Town.", hide),
        "Ogerpon": ("Kitakami: the heart of the Teal Mask story in Mossui Town.",
                    "Mossui Town, Lv%d: Loyalty Plaza at the end of the Teal Mask story. Kieran's grandfather changes "
                    "its mask." % level),
        "Pecharunt": ("Kitakami: after the Teal Mask story, Briar has a letter from Kieran.",
                      "Mossui Town, Lv%d: Loyalty Plaza at the end of Mochi Mayhem. It is yours once it is beaten."
                      % p2_level),
    }


def rows(rom):
    leg, legp = u32(rom, LEG_LIT - B) - B, u32(rom, PANES + 4 - B) - B
    n = rom[PAGES - B + 8 * LEG_PAGE + 1]
    return leg, legp, n


def check(rom):
    """the Legends chapter as gen9journal left it: 1 + 119 counted rows, then the five Locked"""
    leg, legp, n = rows(rom)
    assert rom[NLEG_CMP - B] == COUNTED and rom[PAGES - B + 8 * LEG_PAGE + 2] == COUNTED, "legend_all's count"
    assert n == 1 + COUNTED + LOCKED_ROWS, "the Legends chapter has %d rows" % n
    locked = [(u16(rom, leg + 16 * i), u16(rom, leg + 16 * i + 2)) for i in range(1 + COUNTED, n)]
    assert locked == [(d, 1) for d in sorted(DEX.values())], "the Locked rows are %s" % locked
    assert all(u16(rom, leg + 16 * i + 2) == 0 for i in range(1 + COUNTED)), "a counted row is marked"
    J, JAZ = _libs()
    for k, off in ((1, 8), (2, 12)):
        want = JAZ.pane(JAZ.ALL_CAUGHT[k] % COUNTED)
        p = u32(rom, leg + off) - B
        assert bytes(rom[p:p + len(want)]) == want, "row 0's text %d is not the 119 one" % k


def put(rom, blob, level, p2_level):
    """the new texts into blob; -> a function that writes the rows (after the blob is in the ROM)"""
    J, JAZ = _libs()
    leg, legp, n = rows(rom)
    total = COUNTED + LOCKED_ROWS

    def panel(key, text):
        return blob.put(key, b"\xfe".join(J.enc(l) for l in JAZ.wrap_px(rom, text, PANE_TEXT_W, 3)) + b"\xff", 1)

    say = texts(level, p2_level)
    by_dex = {d: name for name, d in DEX.items()}
    new = {}
    for i in range(1 + COUNTED, n):
        name = by_dex[u16(rom, leg + 16 * i)]
        hint, where = say[name]
        new[i] = (blob.put(("kj", name, "hint"), JAZ.pane(hint), 1), blob.put(("kj", name, "where"), JAZ.pane(where), 1),
                  panel(("kj", name, "pw"), where), panel(("kj", name, "ph"), hint))
    h0 = blob.put(("kj", "h0"), JAZ.pane(JAZ.ALL_CAUGHT[1] % total), 1)
    w0 = blob.put(("kj", "w0"), JAZ.pane(JAZ.ALL_CAUGHT[2] % total), 1)
    pw0 = panel(("kj", "pw0"), JAZ.ALL_CAUGHT[2] % total)
    ph0 = panel(("kj", "ph0"), JAZ.ALL_CAUGHT[1] % total)

    def finish(rom):
        for i, (hp, wp, pwp, php) in new.items():
            struct.pack_into("<H", rom, leg + 16 * i + 2, 0)                      # unlocked (+4 its name stays)
            struct.pack_into("<II", rom, leg + 16 * i + 8, hp, wp)                # its hint and where
            rom[legp + 16 * i + 1] = 0                                            # no forced silhouette
            struct.pack_into("<II", rom, legp + 16 * i + 8, pwp, php)
        struct.pack_into("<II", rom, leg + 8, h0, w0)
        struct.pack_into("<II", rom, legp + 8, pw0, ph0)
        rom[NLEG_CMP - B] = total
        rom[PAGES - B + 8 * LEG_PAGE + 2] = total
        return total
    return finish
