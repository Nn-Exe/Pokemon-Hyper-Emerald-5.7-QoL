"""The Quest Log for the whole of Gen 9: the last step of the build (after gen9rest, gen9dex and gen9egg).

    python -I gen9journal_patch.py <in.gba> <out.gba>

The user (2026-10-15): "update the journey logs to include gen9 in terms of legendary and side quests". Their
choices: Legends - "The 20 Paradox" and "Kitakami ones as locked"; Side Content - "Area Zero extras".

  * Legends. paldea (journal_az.install_legends) gave the chapter Area Zero's seven legendaries; gen9dex gave them
    their official numbers. This adds the twenty Paradox Pokemon (all caught in Area Zero) and sorts the 27 Gen 9
    rows by number, after the 92 older legends: "Gotta catch 'em all!" now asks for 119. After those come
    Okidogi, Munkidori, Fezandipiti, Ogerpon and Pecharunt, which this game has as Pokemon but nowhere to meet
    them (Kitakami is not built): their row is "Locked" (a new status, 10), shown dimmed with its name, the
    picture a silhouette and the text "not in this version yet". They are not counted: legend_all stops at row 119,
    and the chapter's total is 119.
      - row_status (rs_legend) gets the lock: an 8-byte trampoline at 0x08FEB0F0 (its lsls / ldr / ldrh / adds:
        the row's entry), a row whose second halfword is 1 is status 10 and returns at once; any other goes on to
        the Pokedex flags at 0x08FEB0F8 as before.
      - the four tables indexed by status (the name's colour, the tag's colour, the tag, whether the title shows)
        are copied with an eleventh entry and their literals (one word each) repointed.
      - u8dec printed 0-99 ("119" came out as a broken tens digit): it now prints three digits from 100, the same
        text below. A 10-byte trampoline at its start (0x08FE55DE, not 4-aligned; r2, which u8dec used anyway).
        Every caller (the Journal, the Quest Log's header, grid and badge case) gets the same text as before for
        0-99.
  * Side Content: ten Area Zero rows after the 45 (the four station logs, Arven's sandwiches, Nemona's rematch
    (story.F_NEMONA_REMATCH, set by her rematch script when you win), the Sealed Vault's three stakes, the two
    Booster Energy balls). A row checks one flag and a second one at most (marks bits 1-15), so the vault is a row
    a stake. New Side table and info-panel table (Badges move 10 rows on), rs_sides and PANES[3] repointed,
    PAGES grown.
  * Evolutions (the user, after the above: "evolution line?"). questlog builds the chapter early in the chain, from
    1,200 species, so no Gen 9 family was in it and the families that gained a Gen 9 evolution (Primeape, Girafarig,
    Dunsparce, Bisharp, Applin, Duraludon, Paldean Wooper) did not show it. It is built again here, from this ROM,
    by the same code (questlog/evolutions.py and tools/romdata/forms.py) pointed at this build's tables (gen9rest's
    1,408-slot copies; the National Dex numbers gen9dex wrote), with a Paldea region and the Gen 9 names in full
    (the ROM's are cut to ten letters: "Meowscarda"), the six new items' and the new moves' names. Written over the
    old Evolutions data in place (0x09F82600; its first word is the table every literal reaches it by; the old data
    and the blank after it give 0xDA00 bytes up to the Legends' blob) and its row count in the three literals that
    hold it.

Space: 0x09FE8000..0x09FF0000, in the ROM's free tail after paldea's Journal block (0x09FE1000.., 13 KB in
2026-10; paldea's JOURNAL_END is 0x01FE8000 so the two cannot meet) and before paldea's sprite block (0x09FF1000).
Checked here: all 0xFF, and no word of the ROM header or literal that code loads points into it (the hack's own
ROM has 0xFF there too: its FF run goes from 0x09F82519 to the end of the ROM).
"""
import collections, json, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path[:0] = [os.path.join(REPO, "patches", "paldea"), os.path.join(REPO, "patches", "journal"),
                os.path.join(REPO, "patches", "speciesx")]
sys.path.append(os.path.join(REPO, "patches", "questlog"))      # (after paldea's: its names must not shadow them)
import journal_patch as J
import journal_az as JAZ
import story as ST
from lib import Blob
import speciesx_patch as SX

B = 0x08000000
FREE, FREE_END = 0x09FE8000, 0x09FF0000
PAGES = 0x08FEC5EC
PANES = 0x08FED35C                                      # 4 words: Journal, Legends, Key Items, Side Content panels
LEG_LIT, LEG_PAGE, NLEG_CMP = 0x08FEB23C, 4, 0x08FEB220
SIDES_LIT, SIDE_PAGE, BADGE_PAGE = 0x08FEB230, 6, 7
NATDEX_LIT = 0x0806D448
HOOK = 0x08FEB0F0                                       # rs_legend: lsls r1,#4; ldr r2,rs_legends; ldrh r4,[r2,r1];
HOOK_WAS = bytes.fromhex("0901524a545a201c")             # adds r0,r4,#0 - then movs r1,#1 (0x08FEB0F8)
U8DEC = 0x08FE55DE
U8DEC_WAS = bytes.fromhex("00b50a2906dba1220a3901320a29fbda02700130a1310170013002bc0847")
STATUS_LITS = {"namefg": (0x08FEA898, 1), "tagfg": (0x08FEA89C, 1), "tags": (0x08FEA8A0, 4),
               "stshow": (0x08FEB244, 1)}               # literal, entry size; 10 entries (statuses 0-9)
LOCKED = 10
LOCKED_ENTRY = {"namefg": 5, "tagfg": 5, "stshow": 1}  # dimmed name and tag (as "To do" / "???"), the title shown
WILD_HEADS = 0x08E19128                                 # paldea's three wild headers: past, future, icy cave
OLD_LEGENDS = 92                                        # the hack's legends, before any Gen 9
AREA_ZERO_DEX = [1001, 1002, 1003, 1004, 1007, 1008, 1024]    # paldea's seven, at gen9dex's numbers
PANE_TEXT_W = 158

EVO_AT, EVO_END = 0x09F82600, 0x09F90000            # questlog's Evolutions data, up to its Legends' blob
EVO_COUNT_LITS = (0x08FEBA68, 0x08FEBC94, 0x08FEBE10)  # eo_count, ed_count, ev_count: the chapter's row count
EVO_PAGE = 8
GROW_AT, NEW_N = 0x01AC0000, 1408                   # gen9rest's species tables (speciesx's 23, in its order)
GEN9_NAMES = {"wo-chien": "Wo-Chien", "chien-pao": "Chien-Pao", "ting-lu": "Ting-Lu", "chi-yu": "Chi-Yu",
              "terapagos-terastal": "Terapagos", "wooper-paldea": "Paldean Wooper",
              "tauros-paldea-combat-breed": "Paldean Tauros (Combat Breed)",
              "tauros-paldea-blaze-breed": "Paldean Tauros (Blaze Breed)",
              "tauros-paldea-aqua-breed": "Paldean Tauros (Aqua Breed)",
              "ogerpon-wellspring-mask": "Ogerpon (Wellspring Mask)",
              "ogerpon-hearthflame-mask": "Ogerpon (Hearthflame Mask)",
              "ogerpon-cornerstone-mask": "Ogerpon (Cornerstone Mask)"}
NEW_ITEMS = {770: "Auspicious Armor", 771: "Malicious Armor", 772: "Syrupy Apple", 773: "Metal Alloy",
             774: "Unremarkable Teacup", 775: "Leader's Crest"}

PARADOX = ["Great Tusk", "Scream Tail", "Brute Bonnet", "Flutter Mane", "Slither Wing", "Sandy Shocks",
           "Iron Treads", "Iron Bundle", "Iron Hands", "Iron Jugulis", "Iron Moth", "Iron Thorns",
           "Roaring Moon", "Iron Valiant", "Walking Wake", "Iron Leaves", "Gouging Fire", "Raging Bolt",
           "Iron Boulder", "Iron Crown"]
KITAKAMI = [("Okidogi", "Okidogi"), ("Munkidori", "Munkidori"), ("Fezandipiti", "Fezndipiti"),
            ("Ogerpon", "Ogerpon"), ("Pecharunt", "Pecharunt")]       # (shown, the ROM's species name)
LOCKED_TEXT = "Not in this version yet: it lives in Kitakami, a place this game does not have."


def u16(rom, a): return struct.unpack_from("<H", rom, a - B)[0]
def u32(rom, a): return struct.unpack_from("<I", rom, a - B)[0]


def species_named(rom, name):
    t = u32(rom, 0x08000144) - B
    want = J.enc(name) + b"\xff"
    hits = [s for s in range(1, 1280) if rom[t + 11 * s:t + 11 * s + len(want)] == want]
    assert hits, "no species %r" % name
    return hits[0]                                      # (Ogerpon: the Teal Mask, before its three other masks)


def item_named(rom, name):
    t = u32(rom, 0x080001C8) - B
    want = J.enc(name) + b"\xff"
    return next(i for i in range(1000) if rom[t + 44 * i:t + 44 * i + len(want)] == want)


def official_dex():
    o = json.load(open(os.path.join(REPO, "patches", "gen9", "official.json"), encoding="utf-8"))
    return {name: o[name.lower().replace(" ", "-")]["dex"] for name in PARADOX + [k for k, _ in KITAKAMI]}


def wild_areas(rom, names):
    """Area Zero's wild Pokemon as the ROM has them: {species: [(area, lo, hi)]}, from paldea's three headers."""
    out = {}
    for k, area in enumerate(("past", "future", "icecave")):
        h = WILD_HEADS + 20 * k
        assert rom[h - B] == 35 and u32(rom, h + 4), "paldea's wild header %d is not there" % k
        slots = u32(rom, u32(rom, h + 4) + 4)
        for i in range(12):
            lo, hi, sp = struct.unpack_from("<BBH", rom, slots - B + 4 * i)
            out.setdefault(sp, [])
            if not any(a == area for a, *_ in out[sp]):
                out[sp].append((area, lo, hi))
    # the areas really are the past, the future and the icy cave: each has its Titan's or its line's Pokemon
    have = lambda area, n: any(a == area for a, *_ in out.get(names[n], []))
    assert have("past", "Great Tusk") and have("future", "Iron Treads") and have("icecave", "Frigibax")
    return out


def paradox_texts(rom, species):
    """(hint, where) for each Paradox Pokemon: wild ones from the ROM's wild tables, the eight that stand on the
    map from story.LEGENDS (what paldea placed them by)."""
    wild = wild_areas(rom, species)
    static = {name: (level, where) for name, level, where, flag in ST.LEGENDS.values()}
    era = {"past": "the tall grass of the crater in the past", "future": "the tall grass of the crater in the future",
           "icecave": "the icy cave on the crater wall's middle ledge"}
    hint_wild = {"past": "Area Zero: an ancient Pokémon roams the tall grass of the crater in the past.",
                 "future": "Area Zero: a Pokémon of iron roams the tall grass of the crater in the future."}
    out = {}
    for name in PARADOX:
        sp = species[name]
        if name in static:
            assert sp not in wild, "%s is both wild and placed" % name
            level, where = static[name]
            place = {"past": "the crater in the past", "future": "the crater in the future",
                     "cavern": "the Crystal Cavern"}[where]
            out[name] = ("Area Zero: after the story, a legend waits in %s." % place,
                         "Area Zero, %s, Lv%d, after the story. Once only: if it faints, it is gone for good."
                         % (place, level))
            continue
        areas = wild[sp]
        assert {a for a, *_ in areas} <= set(era) and len({(lo, hi) for a, lo, hi in areas}) == 1
        lo, hi = areas[0][1:]
        first = areas[0][0]
        assert first in hint_wild, "%s: the first area is not a crater" % name
        where = " and in ".join(era[a] for a, *_ in areas)
        out[name] = (hint_wild[first], "Area Zero, in %s, Lv%d-%d. The way in: the black hole in Mossdeep City."
                     % (where, lo, hi) if len(areas) == 1 else "Area Zero: in %s, Lv%d-%d." % (where, lo, hi))
    return out


def side_rows(rom, species):
    """(flag, also, name, location, text, picture) - picture as questlog's portraits: ("m", species),
    ("t", trainer picture), ("i", item) or None. The text follows "Location: " on A (so a small letter where it
    is not a name), and starts the info panel with a capital."""
    logs = ["the crater wall's middle ledge", "the house on the shelf below the stairs into the crater",
            "the house on the knoll in the east of the crater", "above the waterfall: surf across the pond and "
            "climb it"]
    rows = []
    for k, (flag, place) in enumerate(zip(ST.F_LOGS, logs)):
        rows.append((flag, 0, "Station No. %d's log" % (k + 1), "Area Zero",
                     "Research Station No. %d, %s. Play the professor's recorded log on the left counter."
                     % (k + 1, place), None))
    rows.append((ST.F_KORAIDON_UP, ST.F_MIRAIDON_UP, "Arven's sandwiches", "Area Zero",
                 "Arven's picnic by the big lake. Beat the Titans in the den on the crater's west side - Great Tusk "
                 "in the past, Iron Treads in the future - and bring him both Sour Herba Mystica: his sandwiches get "
                 "Koraidon and Miraidon up again.", ("m", species["Koraidon"])))
    rows.append((ST.F_NEMONA_REMATCH, 0, "Nemona's rematch", "Area Zero",
                 "after the story, Nemona lives in Research Station No. 3, the house on the knoll in the east of "
                 "the crater. Beat her in a rematch.", ("t", ST.TRAINERS["nemona"][2])))
    for key, flag in ST.F_SEALS.items():
        rows.append((flag, 0, "Vault stake: %s" % {"wo_chien": "tablets", "ting_lu": "vessel",
                                                   "chi_yu": "beads"}[key], "Area Zero",
                     "after the story, the Sealed Vault behind the Crystal Cavern's second cave mouth. Slide over "
                     "the mirror floor to the stake marked with %s and pull it out." % ST.VAULT_MARKS[key], None))
    rows.append((ST.F_BOOSTER["past"], ST.F_BOOSTER["future"], "Booster Energy", "Area Zero",
                 "an item ball in the crater in the past, and another in the crater in the future. Take both.",
                 ("i", item_named(rom, ST.CAVERN_ITEM))))
    return rows


def panel(rom, blob, key, text):
    return blob.put(key, b"\xfe".join(J.enc(l) for l in JAZ.wrap_px(rom, text, PANE_TEXT_W, 3)) + b"\xff", 1)


def gen9_names():
    """species slot -> its full name, for gen9's 38 (1200-) and gen9rest's 89 (1238-)."""
    sys.path[:0] = [os.path.join(REPO, "patches", "gen9"), os.path.join(REPO, "patches", "gen9rest")]
    import gen9_data as A
    import gen9rest_data as D
    out = {}
    for first, keys in ((A.FIRST_SLOT, [t[0] for t in A.SPECIES]), (D.FIRST_SLOT, [t[0] for t in D.SPECIES])):
        for i, key in enumerate(keys):
            out[first + i] = GEN9_NAMES.get(key) or " ".join(w.capitalize() for w in key.split("-"))
    return out


def evolutions(rom):
    """The Evolutions chapter built again from this ROM (see the docstring). Returns (rows, families, bytes)."""
    import evolutions as EV
    import forms as F
    import species_display as SD
    import display_names as DN
    # this build's tables: gen9rest's layout, checked against the header words and literals that hold them
    lay, p = {}, GROW_AT
    for name, _, size, *_ in SX.TABLES:
        lay[name] = p
        p = (p + size * NEW_N + 3) & ~3
    for hdr, name in ((0x08000128, "front pictures"), (0x08000138, "icons"), (0x08000144, "names"),
                      (0x080001BC, "base stats")):
        assert u32(rom, hdr) == B + lay[name], "%s is not where gen9rest put it" % name
    assert u32(rom, NATDEX_LIT) == B + lay["national dex no."], "the National Dex table moved"
    evos = lay["evolutions"]
    assert struct.unpack_from("<HHH", rom, evos + 40 * 1) == (4, 16, 2), "Bulbasaur's evolution row"
    assert struct.unpack_from("<HHH", rom, evos + 40 * 1238) == (4, 16, 1239), "Sprigatito's evolution row"
    F.EVOS = EV.EVOS = evos
    F.NATDEX = EV.NATDEX = lay["national dex no."]
    F.NSPECIES = EV.NSPECIES = NEW_N
    SD.FORMS.update(gen9_names())                       # (the dict evolutions.py names NAMED_FORMS)
    DN.ITEMS_BY_ID.update(NEW_ITEMS)
    mv = u32(rom, 0x08000148) - B                       # the move names (13 bytes), for moves moves.json lacks
    EV.EXTRA_MOVES.update({m: DN.move_name(EV.text_of(bytes(rom[mv + 13 * m:mv + 13 * m + 13]).split(b"\xff")[0]))
                           for m in range(1, 1024)})
    plain = EV.families

    def families(r):
        # Bisharp -> Kingambit holding a Leader's Crest, by day and by night (gen9rest's two rows): one method
        out = plain(r)
        for _, fs in out:
            for f in fs:
                rows = f["rows"]
                for k, row in enumerate(rows):
                    for j, other in enumerate(rows):
                        if (j != k and row[:3] == other[:3] and row[3].endswith(", day")
                                and other[3] == row[3][:-5] + ", night"):
                            item = row[4]
                            rows[k] = row[:3] + (item, item) + row[5:]
                            rows[j] = other[:3] + (item, item) + other[5:]
        return out
    EV.families = EV.rows = families
    rows = EV.list_pages(rom)
    fams = EV.all_families(rom)
    methw = PANE_TEXT_W - JAZ.px(rom, "How it evolves") - 3
    data, one, chapters = EV.blob(EVO_AT, rom, JAZ.wrap_px, JAZ.pane, methw)
    assert chapters == [("Evolutions", len(rows))]
    pics = u32(rom, 0x08000128) - B                     # every picture decompresses to at most 0x2000 bytes
    for f in fams:
        pic = u32(rom, B + pics + 8 * f["pic"]) - B
        assert rom[pic] == 0x10 and u32(rom, B + pic) >> 8 <= 0x2000, "picture %d" % f["pic"]
    return rows, fams, data


CODE = r"""
lk_hook:
    lsls r1, r1, #4
    ldr r2, lk_legends
    ldr r2, [r2]
    adds r2, r2, r1
    ldrh r4, [r2]
    ldrh r0, [r2, #2]
    cmp r0, #0
    bne lk_locked
    adds r0, r4, #0
    ldr r3, lk_back
    bx r3
lk_locked:
    movs r0, #10
    pop {r4, pc}

u8dec3:
    push {lr}
    cmp r1, #100
    blt u3_two
    movs r2, #0xA1
u3_hund:
    subs r1, #100
    adds r2, #1
    cmp r1, #100
    bge u3_hund
    strb r2, [r0]
    adds r0, #1
    movs r2, #0xA1
    b u3_tens
u3_two:
    cmp r1, #10
    blt u3_one
    movs r2, #0xA1
u3_tens:
    cmp r1, #10
    blt u3_tdone
    subs r1, #10
    adds r2, #1
    b u3_tens
u3_tdone:
    strb r2, [r0]
    adds r0, #1
u3_one:
    adds r1, #0xA1
    strb r1, [r0]
    adds r0, #1
    pop {r1}
    bx r1
%s
lk_legends:
    .word 0x%08X
lk_back:
    .word 0x%08X
"""


def check(rom):
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    for k, was in ((LEG_PAGE, (0, 100, 99, 1)), (SIDE_PAGE, (0, 45, 45, 3)), (BADGE_PAGE, (45, 8, 8, 3))):
        o = PAGES - B + 8 * k
        assert tuple(rom[o:o + 4]) == was, "the Quest Log's chapter %d is %s, not %s" % (k, tuple(rom[o:o + 4]), was)
    assert rom[NLEG_CMP - B:NLEG_CMP - B + 2] == bytes((99, 0x2C)), "legend_all's count is not 99"
    assert bytes(rom[HOOK - B:HOOK - B + 8]) == HOOK_WAS and HOOK % 4 == 0, "rs_legend changed"
    assert bytes(rom[U8DEC - B:U8DEC - B + len(U8DEC_WAS)]) == U8DEC_WAS, "u8dec changed"
    assert u32(rom, SIDES_LIT) != 0 and u32(rom, PANES + 12) != 0
    words = struct.unpack_from("<%dI" % (len(rom) // 4), rom)
    count = collections.Counter(words)
    for name, (lit, size) in STATUS_LITS.items():
        t = u32(rom, lit)
        assert count[t] == 1, "%s (%08X) has another word pointing at it" % (name, t)
    tags = u32(rom, STATUS_LITS["tags"][0])
    assert bytes(rom[u32(rom, tags + 4) - B:u32(rom, tags + 4) - B + 5]) == J.enc("Done") + b"\xff", "TAGS[1]"
    assert bytes(rom[u32(rom, STATUS_LITS["stshow"][0]) - B:][:10]) == bytes((0, 1, 1, 1, 0, 0, 1, 0, 1, 1))
    for w in (LEG_LIT, SIDES_LIT):
        t = u32(rom, w)
        assert count[t] == 1, "a second word points at %08X" % t
    assert set(rom[FREE - B:FREE_END - B]) == {0xFF}, "the space is not free"
    # (about 130 words read as an address in there by chance - four bytes of a picture or a tune: none is a word
    # of the ROM header or a literal that code loads, speciesx's test, which the space checks of 2026-10-11 used)
    into = [4 * i for i, w in enumerate(words) if FREE <= w < FREE_END]
    real = [B + o for o in into if SX.is_pointer(rom, o)]
    assert not real, "pointers into the space: %s" % ["%08X" % a for a in real[:8]]
    return words


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    check(rom)
    natdex = u32(rom, NATDEX_LIT)
    dex = lambda sp: u16(rom, natdex + 2 * (sp - 1))
    official = official_dex()
    species = {n: species_named(rom, r) for n, r in ST.SPECIES.items() if n in PARADOX + ["Koraidon", "Frigibax",
                                                                                            "Miraidon"]}
    for n in PARADOX:
        assert dex(species[n]) == official[n], "%s is No. %d here, not %d: gen9dex has not run" % (
            n, dex(species[n]), official[n])
    locked = [(shown, species_named(rom, rn)) for shown, rn in KITAKAMI]
    for shown, sp in locked:
        assert dex(sp) == official[shown], shown

    blob = Blob(FREE)
    # ------------------------------------------------------------------------------------------- code
    for pad in ("", "    mov r8, r8"):
        code, dis = J.thumb(CODE % (pad, LEG_LIT, HOOK + 9), FREE)
        if (len(code) - 8) % 4 == 0:
            break
    assert struct.unpack_from("<2I", code, len(code) - 8) == (LEG_LIT, HOOK + 9)
    at = blob.put("code", code, 4)
    assert at == FREE
    u8dec3 = FREE + code.index(bytes.fromhex("00b56429"))      # push {lr}; cmp r1, #100
    assert u8dec3 % 2 == 0

    # ------------------------------------------------------------------------------------------- status 10
    tables = {}
    locked_tag = blob.put("tag_locked", J.enc("Locked") + b"\xff", 1)
    for name, (lit, size) in STATUS_LITS.items():
        old = bytes(rom[u32(rom, lit) - B:u32(rom, lit) - B + 10 * size])
        extra = struct.pack("<I", locked_tag) if name == "tags" else bytes((LOCKED_ENTRY[name],))
        tables[name] = blob.put(("status", name), old + extra, size)

    # ------------------------------------------------------------------------------------------- Legends
    leg, legp = u32(rom, LEG_LIT), u32(rom, PANES + 4)
    old = [bytes(rom[leg - B + 16 * i:leg - B + 16 * (i + 1)]) for i in range(100)]
    oldp = [bytes(rom[legp - B + 16 * i:legp - B + 16 * (i + 1)]) for i in range(100)]
    have = [struct.unpack_from("<H", r)[0] for r in old]
    OLDP = OLD_LEGENDS + 1
    assert have[0] == 0 and have[OLDP:] == AREA_ZERO_DEX, have[OLDP:]
    assert all(struct.unpack_from("<H", r, 2)[0] == 0 for r in old), "a Legends row is marked already"
    gen9 = [(have[i], old[i], oldp[i]) for i in range(OLDP, 100)]
    texts = paradox_texts(rom, species)
    loc = blob.put(("leg", "loc"), J.enc("Area Zero") + b"\xff", 1)
    for k, n in enumerate(PARADOX):
        hint, where = texts[n]
        name_p = blob.put(("leg", k, "name"), J.enc(n) + b"\xff", 1)
        hint_p = blob.put(("leg", k, "hint"), JAZ.pane(hint), 1)
        where_p = blob.put(("leg", k, "where"), JAZ.pane(where), 1)
        sp = species[n]
        gen9.append((dex(sp), struct.pack("<HHIII", dex(sp), 0, name_p, hint_p, where_p),
                     struct.pack("<BBHIII", 1, 0, sp, loc, panel(rom, blob, ("leg", k, "pw"), where),
                                 panel(rom, blob, ("leg", k, "ph"), hint))))
    gen9.sort(key=lambda r: r[0])
    assert len({d for d, *_ in gen9}) == len(gen9) == 27
    n_all = OLD_LEGENDS + len(gen9)
    # row 0: its texts say how many
    h0, w0 = u32(rom, leg + 8), u32(rom, leg + 12)
    for ptr, text in ((h0, JAZ.ALL_CAUGHT[1] % 99), (w0, JAZ.ALL_CAUGHT[2] % 99)):
        want = JAZ.pane(text)
        assert bytes(rom[ptr - B:ptr - B + len(want)]) == want, "row 0's text is not the 99 one"
    row0 = old[0][:8] + struct.pack("<II", blob.put(("leg", "h0"), JAZ.pane(JAZ.ALL_CAUGHT[1] % n_all), 1),
                                    blob.put(("leg", "w0"), JAZ.pane(JAZ.ALL_CAUGHT[2] % n_all), 1))
    pane0 = oldp[0][:8] + struct.pack("<II", panel(rom, blob, ("leg", "pw0"), JAZ.ALL_CAUGHT[2] % n_all),
                                      panel(rom, blob, ("leg", "ph0"), JAZ.ALL_CAUGHT[1] % n_all))
    kloc = blob.put(("leg", "kloc"), J.enc("Kitakami") + b"\xff", 1)
    ktext = blob.put(("leg", "ktext"), JAZ.pane(LOCKED_TEXT), 1)
    kpanel = panel(rom, blob, ("leg", "kpanel"), LOCKED_TEXT)
    lrows, lpanes = [], []
    for shown, sp in sorted(locked, key=lambda r: dex(r[1])):
        name_p = blob.put(("leg", shown), J.enc(shown) + b"\xff", 1)
        lrows.append(struct.pack("<HHIII", dex(sp), 1, name_p, ktext, ktext))      # 1: locked
        lpanes.append(struct.pack("<BBHIII", 1, 1, sp, kloc, kpanel, kpanel))      # always a silhouette
    rows = [row0] + old[1:OLDP] + [r for d, r, p in gen9] + lrows
    panes = [pane0] + oldp[1:OLDP] + [p for d, r, p in gen9] + lpanes
    assert len(rows) == 1 + n_all + len(lrows) <= 255
    leg_new = blob.put(("leg", "rows"), b"".join(rows), 4)
    legp_new = blob.put(("leg", "panes"), b"".join(panes), 4)

    # ------------------------------------------------------------------------------------------- Side Content
    sides, sidep = u32(rom, SIDES_LIT), u32(rom, PANES + 12)
    sold = [bytes(rom[sides - B + 16 * i:sides - B + 16 * (i + 1)]) for i in range(53)]
    spold = [bytes(rom[sidep - B + 16 * i:sidep - B + 16 * (i + 1)]) for i in range(53)]
    flags_now = {struct.unpack_from("<H", r, 2)[0] for r in sold}
    new_s, new_p = [], []
    locw = PANE_TEXT_W - JAZ.px(rom, "Location:") - 3
    sloc = blob.put(("side", "loc"), J.enc("Area Zero") + b"\xff", 1)
    assert JAZ.px(rom, "Area Zero") <= locw and JAZ.px(rom, "Kitakami") <= locw
    for k, (flag, also, name, where, text, pic) in enumerate(side_rows(rom, species)):
        assert flag not in flags_now and len(name) <= 24 and 0 <= also < 0x8000, name
        name_p = blob.put(("side", k, "name"), J.enc(name) + b"\xff", 1)
        text_p = blob.put(("side", k, "text"), JAZ.pane("%s: %s" % (where, text)), 1)
        new_s.append(struct.pack("<HHIII", also << 1, flag, name_p, text_p, text_p))
        kind, pid = (0, 0) if pic is None else ({"m": 1, "t": 2, "i": 3}[pic[0]], pic[1])
        ptext = panel(rom, blob, ("side", k, "panel"), text[:1].upper() + text[1:])
        new_p.append(struct.pack("<BBHIII", kind, 0, pid, sloc, ptext, ptext))
    n_side = len(new_s)
    sides_new = blob.put(("side", "rows"), b"".join(sold[:45] + new_s + sold[45:]), 4)
    sidep_new = blob.put(("side", "panes"), b"".join(spold[:45] + new_p + spold[45:]), 4)

    data = blob.link()
    assert FREE + len(data) <= FREE_END, "%d bytes: more than the space" % len(data)
    rom[FREE - B:FREE - B + len(data)] = data
    # ------------------------------------------------------------------------------------------- the ROM's own
    rom[HOOK - B:HOOK - B + 8] = bytes.fromhex("004b1847") + struct.pack("<I", FREE | 1)     # lk_hook
    rom[U8DEC - B:U8DEC - B + 10] = bytes.fromhex("014a1047c046") + struct.pack("<I", u8dec3 | 1)
    for name, (lit, size) in STATUS_LITS.items():
        struct.pack_into("<I", rom, lit - B, tables[name])
    struct.pack_into("<I", rom, LEG_LIT - B, leg_new)
    struct.pack_into("<I", rom, PANES + 4 - B, legp_new)
    rom[NLEG_CMP - B] = n_all
    p = PAGES - B
    rom[p + 8 * LEG_PAGE + 1] = len(rows)
    rom[p + 8 * LEG_PAGE + 2] = n_all
    struct.pack_into("<I", rom, SIDES_LIT - B, sides_new)
    struct.pack_into("<I", rom, PANES + 12 - B, sidep_new)
    rom[p + 8 * SIDE_PAGE + 1] += n_side
    rom[p + 8 * SIDE_PAGE + 2] += n_side
    rom[p + 8 * BADGE_PAGE] += n_side

    # ------------------------------------------------------------------------------------------- Evolutions
    old_n = u32(rom, EVO_COUNT_LITS[0])
    assert all(u32(rom, a) == old_n for a in EVO_COUNT_LITS), "the Evolutions count's literals"
    assert tuple(rom[p + 8 * EVO_PAGE:p + 8 * EVO_PAGE + 4]) == (0, min(old_n, 255), min(old_n, 255), 4)
    old_table = u32(rom, EVO_AT)
    assert EVO_AT < old_table < EVO_END, "the Evolutions data does not start with its table's pointer"
    used = EVO_END - B
    while rom[used - 1] == 0xFF:
        used -= 1
    assert set(rom[used:EVO_END - B]) == {0xFF} and used - (EVO_AT - B) > 30000, "the Evolutions data's end"
    words = struct.unpack_from("<%dI" % (len(rom) // 4), rom)
    inside = [4 * i for i, w in enumerate(words) if EVO_AT < w < EVO_END and not EVO_AT <= B + 4 * i < EVO_END]
    real = [B + o for o in inside if SX.is_pointer(rom, o)]
    assert not real, "pointers into the Evolutions data: %s" % ["%08X" % a for a in real[:8]]
    erows, efams, edata = evolutions(rom)
    assert len(edata) <= EVO_END - EVO_AT, "the Evolutions data: %d bytes, %d fit" % (len(edata), EVO_END - EVO_AT)
    assert len(erows) <= 0xFFFF
    rom[EVO_AT - B:EVO_END - B] = b"\xff" * (EVO_END - EVO_AT)
    rom[EVO_AT - B:EVO_AT - B + len(edata)] = edata
    for a in EVO_COUNT_LITS:
        struct.pack_into("<I", rom, a - B, len(erows))
    paldea = [f for f in efams if f["dex"] >= 906]

    open(outp, "wb").write(rom)
    print("gen9journal: Legends %d rows (%d counted, %d locked) @%08X, Side Content +%d @%08X, code @%08X "
          "(hook %08X, u8dec3 %08X), %d bytes @%08X..%08X; Evolutions %d rows (was %d), %d families (%d of Gen 9), "
          "%d bytes @%08X (was %d)" % (len(rows), n_all, len(lrows), leg_new, n_side, sides_new, FREE, HOOK, u8dec3,
                                       len(data), FREE, FREE + len(data), len(erows), old_n, len(efams), len(paldea),
                                       len(edata), EVO_AT, used - (EVO_AT - B)))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
