"""text_overflow.py <rom> [max=216] [--json out.json] - lines of text wider than the message box.

Every English text a script shows in the field message box (msgbox: loadword 0 + callstd, message + waitmessage,
trainerbattle intro / not-enough texts) is measured with the game's normal font widths (0x086542E4). A line wider
than the 216-px box wraps round and draws over its own start. For each page with such a line this prints the page
as it is and a way to break it that fits: the last words of a too-wide line pushed down to the next line, or its
first words pulled up - only spaces and line breaks swap places (0x00 <-> 0xFE / 0xFA), so the text keeps its
length and its address. The first break of a page is 0xFE (second line), the later ones 0xFA (scroll). {PLAYER}
counts as the widest 7-letter name. Trainer defeat texts (shown in battle) are listed apart.

The fixes themselves are written by hand in patches/textfix/textfix_patch.py (BREAKS): this only finds the pages
and suggests. Run it on a new build after any change to the translation; it should report 0 texts."""
import json, struct, sys
sys.stdout.reconfigure(encoding="utf-8")
rom = open(sys.argv[1], "rb").read()
OUT = sys.argv[sys.argv.index("--json") + 1] if "--json" in sys.argv else None
MAXW = int(dict(a.split("=") for a in sys.argv[2:] if "=" in a).get("max", 216))
W = rom[0x006542E4:0x006542E4 + 0x200]
ok = lambda v: 0x08000000 <= v < 0x0A000000
NAMECH = [0xBB + i for i in range(26)] + [0xD5 + i for i in range(26)] + [0xA1 + i for i in range(10)]
NAME_W = 7 * max(W[c] for c in NAMECH)                     # the widest 7-letter name
RIVAL_W = NAME_W
EN = {}
for i, c in enumerate("0123456789!?.-・…“”‘’♂♀¥,×/ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"): EN[0xA1 + i] = c
EN.update({0x00: " ", 0xB4: "’", 0xB0: "…", 0x1B: "é", 0x06: "É", 0xF0: ":", 0x53: "{PK}", 0x54: "{MN}", 0x5C: "(",
           0x5D: ")", 0x5B: "%", 0x2D: "&", 0x2E: "+", 0x35: "=", 0x36: ";", 0xB7: "$", 0x34: "{LV}"})
FC_EXTRA = {0x01: 1, 0x02: 1, 0x03: 1, 0x04: 3, 0x05: 1, 0x06: 1, 0x08: 1, 0x0B: 2, 0x0C: 1, 0x0D: 1, 0x0E: 1, 0x10: 2,
            0x11: 1, 0x12: 1, 0x13: 1, 0x14: 1}
FD_NAME = {0x01: "{PLAYER}", 0x02: "{STR_VAR_1}", 0x03: "{STR_VAR_2}", 0x04: "{STR_VAR_3}", 0x05: "{KUN}", 0x06: "{RIVAL}"}


def tokens(a):
    """[(kind, offset, text, width)] up to the 0xFF; kind: c char, s space, n/l/p break, v unknown-width buffer, x code.
    None if it is not English text (Chinese lead bytes, unknown bytes, no end within 1500 bytes)."""
    o = a - 0x08000000
    out = []
    while o < len(rom) and len(out) < 1500:
        c = rom[o]
        if c == 0xFF:
            return out
        if c == 0x00:
            out.append(("s", o, " ", W[0])); o += 1
        elif c in (0xFE, 0xFA, 0xFB):
            out.append(({0xFE: "n", 0xFA: "l", 0xFB: "p"}[c], o, {0xFE: "\\n", 0xFA: "\\l", 0xFB: "\\p"}[c], 0)); o += 1
        elif c == 0xFC:
            k = 2 + FC_EXTRA.get(rom[o + 1], 0)
            if rom[o + 1] in (0x0C, 0x12, 0x13):                 # escape / skip / clear-to: positions we cannot see
                out.append(("v", o, "{FC%02X}" % rom[o + 1], 0))
            else:
                out.append(("x", o, "{FC%s}" % rom[o + 1:o + k].hex().upper(), 0))
            o += k
        elif c == 0xFD:
            code = rom[o + 1]
            if code == 0x01:
                out.append(("c", o, "{PLAYER}", NAME_W))
            elif code == 0x06:
                out.append(("c", o, "{RIVAL}", RIVAL_W))
            elif code == 0x05:
                out.append(("x", o, "{KUN}", 0))
            else:
                out.append(("v", o, FD_NAME.get(code, "{FD%02X}" % code), 0))
            o += 2
        elif c in (0xF8, 0xF9):
            out.append(("c", o, "{%02X%02X}" % (c, rom[o + 1]), W[0x100 + rom[o + 1]] if c == 0xF9 else 12)); o += 2
        elif c in EN:
            out.append(("c", o, EN[c], W[c])); o += 1
        elif 0x01 <= c <= 0x1E:                                  # a Chinese lead byte: not English text
            return None
        else:                                                    # a glyph this table has no name for: its own width
            out.append(("c", o, "{%02X}" % c, W[c])); o += 1
    return None


def pages(tk):
    """split at \\p: [(tokens of the page)]"""
    out, cur = [], []
    for t in tk:
        if t[0] == "p":
            out.append(cur); cur = []
        else:
            cur.append(t)
    out.append(cur)
    return out


def units(pg):
    """a page as words and the separators between them: words[i] = (text, width, has_var), seps[i] = token between
    words[i] and words[i+1] (a space, \\n or \\l)"""
    words, seps, cur, wd, var = [], [], "", 0, False
    for t in pg:
        if t[0] in "snl":
            words.append((cur, wd, var)); seps.append(t); cur, wd, var = "", 0, False
        else:
            cur += t[2]; wd += t[3]; var = var or t[0] == "v"
    words.append((cur, wd, var))
    return words, seps


def line_w(words, i, j):
    """width of words i..j-1 on one line (no trailing spaces: empty words at the end count nothing)"""
    k = j
    while k > i + 1 and words[k - 1][0] == "":
        k -= 1
    return sum(w for _, w, _ in words[i:k]) + W[0] * (k - i - 1)


def layout(words, seps):
    """new breaks for a page that has a line too wide, the way a person would: push the last words of each line that
    is too wide down to the next line (a new line after the last one if need be). If that adds a line, try instead
    pulling the first words of the too-wide line up onto the line before. Returns (cost, [separator index of each
    break]) or None."""
    n = len(words)
    was = [s[0] in "nl" for s in seps]
    starts = [0] + [k + 1 for k in range(len(seps)) if was[k]]
    nl0 = len(starts)

    def ends(st):
        return [st[i + 1] if i + 1 < len(st) else n for i in range(len(st))]

    def fits(st):
        return all(line_w(words, a, b) <= MAXW for a, b in zip(st, ends(st)))

    # push down
    st = list(starts)
    i = 0
    while i < len(st):
        e = ends(st)[i]
        while line_w(words, st[i], e) > MAXW and e - st[i] > 1:
            e -= 1
        if line_w(words, st[i], e) > MAXW:
            return None
        if e < (ends(st)[i]):
            if i + 1 < len(st):
                st[i + 1] = e
            else:
                st.append(e)
        i += 1
    down = st
    best = down
    if len(down) > nl0:
        # pull up: the too-wide line gives its first words to the line before
        st = list(starts)
        good = True
        for i in range(1, len(st)):
            while line_w(words, st[i], ends(st)[i]) > MAXW:
                if line_w(words, st[i - 1], st[i] + 1) > MAXW or st[i] + 1 >= ends(st)[i]:
                    good = False; break
                st[i] += 1
            if not good:
                break
        if good and fits(st):
            best = st
    brks = [x - 1 for x in best[1:]]
    cost = sum(1 for k in range(len(seps)) if was[k] != (k in brks))
    return cost, brks


def scan_sites():
    """{text address: [how it is shown]}"""
    found = {}
    def add(v, how):
        if ok(v):
            found.setdefault(v, []).append(how)
    b = rom
    i = 0
    while True:
        i = b.find(b"\x0F\x00", i + 1)
        if i < 0 or i + 7 >= len(b): break
        if b[i + 6] == 0x09 and b[i + 7] <= 6:
            add(struct.unpack_from("<I", b, i + 2)[0], "msgbox %d at %08X" % (b[i + 7], 0x08000000 + i))
    i = 0
    while True:
        i = b.find(b"\x67", i + 1)
        if i < 0 or i + 5 >= len(b): break
        if b[i + 5] == 0x66:
            add(struct.unpack_from("<I", b, i + 1)[0], "message at %08X" % (0x08000000 + i))
    defeat = {}
    i = 0
    while True:
        i = b.find(b"\x5C", i + 1)
        if i < 0 or i + 20 >= len(b): break
        t = b[i + 1]
        if t > 9: continue
        p = [struct.unpack_from("<I", b, i + 6 + 4 * k)[0] for k in range(4)]
        if t == 3:
            if ok(p[0]): defeat.setdefault(p[0], []).append("trainerbattle 3 at %08X" % (0x08000000 + i))
            continue
        if not (ok(p[0]) and ok(p[1])): continue
        add(p[0], "trainerbattle %d intro at %08X" % (t, 0x08000000 + i))
        defeat.setdefault(p[1], []).append("trainerbattle %d at %08X" % (t, 0x08000000 + i))
        if t in (4, 6, 7, 8) and ok(p[2]):
            add(p[2], "trainerbattle %d not-enough at %08X" % (t, 0x08000000 + i))
    return found, defeat


def show(tk):
    return "".join(t[2] for t in tk)


def check(sites, label):
    fixes, unfixable, nvar = [], [], 0
    for a in sorted(sites):
        tk = tokens(a)
        if not tk:
            continue
        changes = []
        bad = False
        for pg in pages(tk):
            words, seps = units(pg)
            was = [s[0] in "nl" for s in seps]
            ls, st = [], 0
            for k in range(len(seps) + 1):
                if k == len(seps) or was[k]:
                    ls.append((st, k + 1)); st = k + 1
            over = [(i, j) for i, j in ls if line_w(words, i, j) > MAXW]
            if not over:
                continue
            if any(any(words[x][2] for x in range(i, j)) for i, j in over):
                nvar += 1
            r = layout(words, seps)
            if r is None:
                bad = True; continue
            cost, brks = r
            new = {}
            for k, s in enumerate(seps):
                want = 0x00
                if k in brks:
                    want = 0xFE if brks.index(k) == 0 else 0xFA
                if rom[s[1]] != want:
                    new[s[1]] = (rom[s[1]], want)
            # the old page's own break kinds: first \n, then \l
            kinds = [rom[s[1]] for k, s in enumerate(seps) if was[k]]
            odd = kinds and (kinds[0] != 0xFE or any(x != 0xFA for x in kinds[1:]))
            changes.append({"before": [show_line(words, i, j) for i, j in ls], "after": lines_of(words, seps, brks),
                            "bytes": {"%08X" % (0x08000000 + o): "%02X>%02X" % ab for o, ab in new.items()},
                            "odd_breaks": bool(odd), "added_lines": max(0, len(brks) + 1 - len(ls))})
        if changes or bad:
            e = {"addr": "%08X" % a, "how": sites[a][:3], "pages": changes, "unfixable": bad, "text": show(tk)}
            (unfixable if bad else fixes).append(e)
    print("%s: %d texts to re-break, %d that cannot (a word wider than the box), %d pages with an unknown-width "
          "buffer" % (label, len(fixes), len(unfixable), nvar))
    return fixes, unfixable


def show_line(words, i, j):
    return "%3d px  %s" % (line_w(words, i, j), " ".join(w for w, _, _ in words[i:j]).rstrip())


def lines_of(words, seps, brks):
    out, st = [], 0
    for b in brks + [len(words) - 1]:
        out.append(show_line(words, st, b + 1)); st = b + 1
    return out


if __name__ == "__main__":
    field, defeat = scan_sites()
    print("texts found: %d field, %d defeat; widest name %d px" % (len(field), len(defeat), NAME_W))
    f1, u1 = check(field, "field (%d px)" % MAXW)
    f2, u2 = check(defeat, "defeat (%d px)" % MAXW)
    for e in f1 + u1:
        print("\n%s %s%s" % (e["addr"], "; ".join(e["how"]), "  UNFIXABLE" if e["unfixable"] else ""))
        for p in e["pages"]:
            for l in p["before"]: print("   was " + l)
            for l in p["after"]: print("   now " + l)
            print("   bytes %s%s%s" % (p["bytes"], "  ODD BREAKS" if p["odd_breaks"] else "",
                                       "  +%d line" % p["added_lines"] if p["added_lines"] else ""))
    print("\n--- defeat texts over %d px ---" % MAXW)
    for e in f2 + u2:
        print("%s %s: %s" % (e["addr"], e["how"][0], e["text"][:150]))
    if OUT:
        json.dump({"field": f1, "field_unfixable": u1, "defeat": f2, "defeat_unfixable": u2}, open(OUT, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
