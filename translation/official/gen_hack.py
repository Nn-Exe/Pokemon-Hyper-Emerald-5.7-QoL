"""Build patches/zhtext/hack.json: the hack's own Chinese strings (not in Emerald) with their English.
python gen_hack.py <rom with official.json applied or not> <outdir>
INPLACE: the English fits where the Chinese is (n = the bytes that string owns). MOVE: a new copy in free space, with
the pointers that reach it (found here, each checked: an aligned table/literal word, or a script argument)."""
import glob, json, os, re, struct, sys
import scan as S
import scan2 as S2
import vanilla as V
import lines as L
import gen_tables as GT

TR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")      # translation/: the earlier passes' JSON
TYPES = ["Normal", "Fight", "Flying", "Poison", "Ground", "Rock", "Bug", "Ghost", "Steel", "???", "Fire", "Water", "Grass",
         "Electr", "Psychc", "Ice", "Dragon", "Dark"]
TYPE_MOVES = ["a Normal move", "a Fighting move", "a Flying move", "a Poison move", "a Ground move", "a Rock move",
              "a Bug move", "a Ghost move", "a Steel move", "a ??? move", "a Fire move", "a Water move", "a Grass move",
              "an Electric move", "a Psychic move", "an Ice move", "a Dragon move", "a Dark move"]
PRICE = "{CLEAR_TO 0x63}{FONT_SMALL}"

INPLACE = {  # address: English (written over the Chinese string; must fit its bytes)
    # Easy Chat words the hack moved out of Emerald's list (the interview / profile vocabulary is in capitals)
    0x089C1090: "GET", 0x089C10A0: "RUBY", 0x089C10B0: "BAG", 0x089C10C0: "ROCK", 0x089C10D0: "ICE", 0x089C10E0: "BUG",
    # battle
    0x089C1150: "Go! {B_PLAYER_MON1_NAME} and\\n{B_PLAYER_MON2_NAME}!",
    0x089C1190: "Wild ", 0x089C11A0: "Foe ", 0x089C11B0: "Foe", 0x089C11C0: "Ally", 0x089C11E0: "Ally",
    # the vitamin seller's list
    0x089C13D0: "Protein" + PRICE + "1,000", 0x089C13F0: "Iron" + PRICE + "1,000", 0x089C1410: "Carbos" + PRICE + "1,000",
    0x089C1430: "Calcium" + PRICE + "1,000", 0x089C1450: "Zinc" + PRICE + "1,000", 0x089C1470: "HP Up" + PRICE + "1,000",
    0x089C1490: "PP Up" + PRICE + "3,000",
    # Rotom's form menu
    0x0970084B: "Revert", 0x09700852: "Exit",
    # exchange list
    0x098C3798: "PP Up{CLEAR_TO 0x5E}x40", 0x098C37CA: "PP Max{CLEAR_TO 0x5E}x120",
    # an old version line
    0x09E0FF80: "{FONT_SMALL}{COLOR RED}{SHADOW LIGHT_RED}Ultra Emerald IV.5{FONT_NORMAL} Do not share",
    # gender words buffered into dialogue
    0x0988F021: "boy", 0x0988F028: "he", 0x0988F02D: "girl",
    # the hack's battle engine: these are reached as anchor + offset, so they can only be replaced where they stand
    # the old two-hanzi slots of the field-effect names (the patcher re-aims the code at full names)
    0x09D76FFE: "Mire", 0x09D77003: "Fire", 0x09D77008: "Rbow", 0x09D7700D: "Wfir", 0x09D77012: "Vine", 0x09D77017: "Cann",
    0x09D7701C: "Volc",
    0x09D749F2: "up",                                   # "higher" itself comes from the code detour (see the patcher)
    0x09D749FC: "Our team", 0x09D74A15: "won", 0x09D74A1A: "tied",
    0x09D74A35: "A wild {RIVAL}\\njumped out!",        # the placeholder is FD 06 there
    0x09D74A85: "Flames trapped them!", 0x09D74A9B: "Flames trapped them!",
    0x09D74AB1: "Sand trapped them!", 0x09D74AC7: "Sand trapped them!",
    0x09D74ADD: "{0xFD 0x0F}'s steel is gone!",
    0x09D74AF1: "Sharp steel surrounds\\nthe foe!",
    0x09D74B10: "Steel lies around\\n{0xFD 0x10}!",
    0x09D74B39: "G-Max damage lingers!", 0x09D74B51: "G-Max damage ended!", 0x09D74B67: "Hurt by the G-Max move!",
    0x09D74BE5: "Status was cured!", 0x09D74BF7: "Move power reset!", 0x09D74C09: "Victory Dance boosts power!",
    0x09D75E81: "Foe calls allies!", 0x09D75E93: "Calling help!",
    0x09D76078: "{0xFD 0x0B} can't break\\nfree!",
    0x09D7650C: "{0xFD 0x0F}'s spikes gone!",
    0x09D7669A: "{0xFD 0x10} gladly agreed!",
    0x09D76716: "{0xFD 0x0F}: too heavy\\nto fly!",
    0x09D76A5A: "Embargo blocks {0xFD 0x00}!",
}
MOVE = {  # address: English (None = take the translation an earlier pass made for the same Chinese, re-wrapped)
    0x098C37A8: "Gold Bottle Cap{CLEAR_TO 0x5E}x120", 0x098C37B9: "Ability Patch{CLEAR_TO 0x5E}x120",
    0x0982C060: "Original Cap Pikachu", 0x0982C070: "Hoenn Cap Pikachu", 0x0982C080: "Sinnoh Cap Pikachu",
    0x0982C090: "Unova Cap Pikachu", 0x0982C0A0: "Kalos Cap Pikachu", 0x0982C0B0: "Alola Cap Pikachu",
    0x0981E3CE: "Cosplay Pikachu", 0x0981E3D9: "Pikachu Libre", 0x0981E3E4: "Pikachu, Ph.D.",
    0x0981E3EF: "Pikachu Rock Star", 0x0981E3FA: "Pikachu Belle", 0x0981E405: "Basculegion",
    0x098BF5A1: "Magic Woods",
    0x09D301FD: "A strike that ignores\\nMax Guard.", 0x09D30211: "Consecutive strikes that\\nignore Max Guard.",
    0x0988F034: "she",
    0x09807F89: None, 0x098080AE: None, 0x09808357: None, 0x09810A10: None, 0x098110C2: None, 0x098111FB: None,
    0x0981B79B: None, 0x0982E95E: None, 0x0983A706: "{PLAYER} received Poipole.", 0x09845E34: None,
    0x09845E6C: None, 0x0984D5FF: None, 0x09881932: None, 0x0988380D: None,
    0x09896C44: None, 0x09896CAF: None, 0x098978D6: None, 0x0989D305: None, 0x0989D72E: None, 0x0989D799: None,
    0x098A046D: None, 0x098A27BF: None, 0x098A282A: None, 0x098AF4FD: None, 0x098BEF30: None,
}
WIDTH = 34
ALIGNED_OK = {0x0985DAD0}                                # a multichoice list entry
NAMEFIX = [("Suiyi Town", "Solaceon Town"), ("Suiyi", "Solaceon"), ("Toxel", "Poipole")]   # names an earlier pass got wrong

SIGH = ("Ginkgo Guild Member: Sigh… With Volo gone and Hisui struck by such disasters, our supplies have almost dried "
        "up…\pStill, friend, come and see what you'd like.")
RECOVER = ("Ginkgo Guild Member: The land of Hisui is slowly recovering, so we can gather people and trade with other "
           "regions.\pThis time, our goal is to import some other kinds of Poké Balls!\pFriend, come and see what "
           "you'd like.")
AGAIN = ("We meet again at last, [BUF01]…! I'm so glad to see you once more.\pBut… this is also the last time. Take a "
         "look at all the rare Poké Balls I have[F9D3]!")
HAND = {  # address: English to wrap (the earlier pass's wording or line breaks were off)
    0x09807F89: "Heh heh heh! Let's rock! Raise the roof! Yo yo yo! Rock! Rock! Rock! Everybody now!\p…Looks like you "
                "don't get rock at all… I'm a traveling DVD merchant.\pI'm passing through Solaceon Town on business. "
                "Want to buy some discs?\pTotally rocking tunes!",
    0x09810A10: "Hey… hey… you over there, friend. I've got rare Balls collected from all over the world.\pWant to "
                "take a look? Meeting like this must be fate. I travel the world all the time.",
    0x098110C2: AGAIN, 0x098111FB: AGAIN,
    0x0981B79B: "I'm so moved! To mark the occasion, let me give you something that shows off your achievement!",
    0x09845E6C: "Grandma always said: making something out of nothing was banned back on March 1, 2006. There's no "
                "[BUF02] in your Bag.",
    0x0984D5FF: "The next tournament is being prepared. Would you like to enter?",
    0x09881932: "Elder Koga: Ready to begin round [BUF02]? (If not, press B to go back.)",
    0x09896C44: SIGH, 0x0989D305: SIGH, 0x0989D72E: SIGH, 0x098A046D: SIGH, 0x098A27BF: SIGH,
    0x09896CAF: RECOVER, 0x098978D6: RECOVER, 0x0989D799: RECOVER, 0x098A282A: RECOVER,
}


def norm(s):
    return "".join(ch for ch in s if "\u4e00" <= ch <= "\u9fff" or ch.isalnum())


def old_translations():
    d = {}
    for f in sorted(glob.glob(os.path.join(TR, "**", "*.json"), recursive=True)):
        try:
            j = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        if isinstance(j, dict):
            for k, v in j.items():
                if isinstance(v, str) and v != "@@SKIP@@":
                    d.setdefault(norm(re.sub(r"\[[^\]]*\]|\\[nlp]", "", k)), v)
    return d


def to_source(en):
    """an earlier pass's English ([BUF02], [F9D3], [FC0105], \\p; spaces for line breaks) -> wrapped source syntax"""
    for x, y in NAMEFIX:
        en = en.replace(x, y)
    en = en.replace("—", "-").replace("–", "-").replace("’", "'")
    pages = []
    for pg in en.split("\\p"):
        words, lines, cur, n = pg.replace("\\n", " ").replace("\\l", " ").split(), [], "", 0
        for w in words:
            disp = len(re.sub(r"\[BUF..\]", "XXXXXXX", re.sub(r"\[F[9C][0-9A-Fa-f]+\]", "", w)))
            if cur and n + 1 + disp > WIDTH:
                lines.append(cur)
                cur, n = w, disp
            else:
                cur, n = (cur + " " + w, n + 1 + disp) if cur else (w, disp)
        if cur:
            lines.append(cur)
        out = lines[0] if lines else ""
        for i, ln in enumerate(lines[1:]):
            out += ("\\n" if i == 0 else "\\l") + ln
        pages.append(out)
    s = "\\p".join(pages)
    s = re.sub(r"\[BUF([0-9A-Fa-f]{2})\]", lambda m: "{0xFD 0x%s}" % m.group(1), s)
    s = re.sub(r"\[(F[9C])([0-9A-Fa-f]+)\]", lambda m: "{" + " ".join("0x" + (m.group(1) + m.group(2))[i:i + 2] for i in range(0, len(m.group(1) + m.group(2)), 2)) + "}", s)
    return s


NARG = {0: 2, 1: 2, 2: 2, 3: 1, 4: 3, 5: 2, 6: 3, 7: 3, 8: 3, 9: 1}      # text pointers per trainerbattle type


def trainer_arg(rom, w):
    """is the word at w a text argument of a trainerbattle (5C type id16 arg16 ptr [ptr [ptr]])?"""
    ptr = lambda o: struct.unpack_from("<I", rom, o)[0]
    for k in range(3):
        c = w - 6 - 4 * k
        if c >= 0 and rom[c] == 0x5C and rom[c + 1] in NARG and k < NARG[rom[c + 1]] and all(ptr(c + 6 + 4 * j) == 0 or 0x08000000 <= ptr(c + 6 + 4 * j) < 0x0A000000 for j in range(k)):
            return True
    c = w - 10              # the hack's partner battles: type 0, a non-zero arg16 and a non-pointer word before the text
    return c >= 0 and rom[c] == 0x5C and rom[c + 1] == 0 and rom[c + 4:c + 6] != bytes(2) and 0 < ptr(c + 6) < 0x08000000


def sites(rom, a):
    """structural pointers to address a: [(offset, kind)], and the rest"""
    pat, i, good, other = struct.pack("<I", a), 0, [], []
    while True:
        i = rom.find(pat, i)
        if i < 0:
            break
        b = rom[max(0, i - 3):i]
        if b[-2:] == b"\x0f\x00":
            good.append((i, "loadword"))
        elif b[-1:] == b"\x67":
            good.append((i, "message"))
        elif b[-2:-1] == b"\x85" and b[-1] < 4:
            good.append((i, "bufferstring"))
        elif trainer_arg(rom, i):
            good.append((i, "trainerbattle"))
        elif i % 4 == 0:
            good.append((i, "aligned"))
        else:
            other.append(i)
        i += 1
    return good, other


def main(rompath, outdir):
    rom = open(rompath, "rb").read()
    old = old_translations()
    arr = {e["name"]: e for e in V.load_arrays()}
    out, notes = [], []

    def cur(a):
        o = a - 0x08000000
        j = rom.find(b"\xff", o)
        return rom[o:j + 1]

    for i, t in enumerate(TYPES):
        e = arr["gTypeNames[%d]" % i]
        out.append({"a": "%08X" % e["addr"], "n": e["width"], "zh": cur(e["addr"]).hex(), "t": t})
    for i, t in enumerate(TYPE_MOVES):
        e = arr["sATypeMove_Table[%d]" % i]
        out.append({"a": "%08X" % e["addr"], "n": e["width"], "zh": cur(e["addr"]).hex(), "t": t})
    for a, t in INPLACE.items():
        z = cur(a)
        enc = V.encode(t + "$")
        if len(enc) > len(z):
            notes.append("%08X: %d bytes of English for a %d-byte slot: %r" % (a, len(enc), len(z), t))
            continue
        out.append({"a": "%08X" % a, "n": len(z), "zh": z.hex(), "t": t})
    for a, t in MOVE.items():
        z = cur(a)
        zh_text = S.dec(z[:-1])[0]
        if a in HAND:
            t = to_source(HAND[a])
        elif t is None:
            k = norm(re.sub(r"\{[^}]*\}|\\[nlp]", "", zh_text))
            if k not in old:
                notes.append("%08X: no earlier translation for %s" % (a, zh_text[:60]))
                continue
            t = to_source(old[k])
        good, other = sites(rom, a)
        if not good:
            notes.append("%08X: no structural pointer (%d others)" % (a, len(other)))
            continue
        V.encode(t + "$")
        out.append({"a": "%08X" % a, "zh": z.hex(), "t": t, "p": ["%08X" % (0x08000000 + w) for w, _ in good],
                    "kinds": sorted(set(k for _, k in good)), "was": zh_text})
    lines = [(a, to_source(t)) for group, t in L.LINES.items() for a in group] + list(L.RAW.items())
    for a, t in lines:                                   # trainer lines: in place when they fit, else a new copy
        z = cur(a)
        zh_text = S.dec(z[:-1])[0]
        enc = V.encode(t + "$")
        good, other = sites(rom, a)
        if a not in ALIGNED_OK:                          # a 4-aligned hit alone is not evidence for these
            other += [w for w, k in good if k == "aligned"]
            good = [(w, k) for w, k in good if k != "aligned"]
        if not good:
            notes.append("%08X: no structural pointer (%d others)" % (a, len(other)))
            continue
        if len(enc) <= len(z):
            out.append({"a": "%08X" % a, "n": len(z), "zh": z.hex(), "t": t, "was": zh_text})
        else:
            out.append({"a": "%08X" % a, "zh": z.hex(), "t": t, "p": ["%08X" % (0x08000000 + w) for w, _ in good],
                        "kinds": sorted(set(k for _, k in good)), "was": zh_text})
        if other:
            notes.append("%08X: %d unrecognised reference(s) left alone: %s" % (a, len(other), ["%08X" % (0x08000000 + w) for w in other]))
    more, more_notes = GT.entries(rom)
    out += more
    notes += more_notes
    with open(os.path.join(outdir, "hack.json"), "w", encoding="utf-8", newline="\n") as f:
        f.write("[\n" + ",\n".join(json.dumps(e, ensure_ascii=False) for e in out) + "\n]\n")
    print(len(out), "entries;", sum("p" in e for e in out), "moved;", "bytes to place:",
          sum(len(V.encode(t + "$")) for t in set(e["t"] for e in out if "p" in e)))
    for n in notes:
        print("  !", n)
    if "-v" in sys.argv:
        for e in out:
            if "was" in e:
                print("  %s %s %s\n      %s\n      %s" % (e["a"], e.get("kinds", "in place"), e.get("p", [])[:4], e["was"], e["t"]))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
