"""Area Zero in the Journal (the Quest Log's Journal pages), as an optional quest.

The user (test 16): "update the journey game log as optional quest, so player knows what to do next". The Journal
(item 363: "A notebook of your journey. Use it to see what to do next.") opens the Quest Log, whose four Journal
chapters are the Journal's step table (patches/journal/steps.py). Area Zero is only in this test build, so its
rows are added here, by the patch that goes last, and the Journal of the release stays as it is:

  * a new step table: the 84 rows of the ROM's as they are (their texts, flag lists and groups stay where they
    are), with Area Zero's rows after "Storm the castle" (Team Rainbow Rocket, 0x41D5); new title and info-panel
    tables likewise; the three literals that hold the table, the titles' literal and the Journal's panel table
    in PANES repointed; the Post-game chapter's rows and count in PAGES grown, and the later chapters' first rows
    moved on.
  * The Quest Log's own rule (compute, 0x08FEA31C) makes the first step not done after the last anchor that is the
    current objective. An optional quest must not take that place from the story, nor show "???" once it can be
    done, nor the grey "Side" tag that reads like done (NOTES, Journal 2026-09-28). So a step row's spare byte 3
    marks an optional row (1-based into OPTS, the flag that opens it), and compute is replaced (an 8-byte
    trampoline at its start; it is a whole function, so lr is the caller's) by the same rule with optional rows
    left out of the choice of the current objective, and their status worked out by themselves: "???" (4) until
    their flag opens them, Active (2: the red arrow) while not done, Done (1). Everything else gets exactly the
    status it got before (the test compares every row with the build without Area Zero).
  * The rows follow the story: each opens with the step before it, so the list itself says what to do next; the
    middle three (Arven's sandwiches, Nemona, the logs) are open together, as in the game. A group row's detail
    (A) says how far it is and the next thing missing (the Journal's own group_tail).
"""
import os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "journal"))
import journal_patch as J                       # enc / message / member / thumb, and steps.py's POST header
import steps as JS
import story as ST

STEPS = 0x08FE8588                              # the Journal's step table: 84 rows of 16 bytes, then mode 0xFF
STEP_LITS = (0x08FE563C, 0x08FEA3F4, 0x08FEAC7C)   # the Journal's build (unused since the Quest Log), compute,
                                                   # open_detail
TITLES, TITLES_LIT = 0x08FECC6C, 0x08FEB248     # 85 pointers (the steps and the closing row), rt_titles
PANES = 0x08FED35C                              # 4 words: the Journal's info-panel rows first
PANE_ROWS = 0x09FA0000                          # 16 bytes a row {kind, 0, id, location, text, hidden}
PAGES = 0x08FEC5EC                              # 9 chapters of 8 bytes {first, rows, objectives, type, name}
PAGES_WAS = [(0, 24, 24, 0), (24, 39, 39, 0), (63, 3, 3, 0), (66, 19, 18, 0)]
POST_PAGE = 1
COMPUTE = 0x08FEA31C
COMPUTE_WAS = bytes.fromhex("f0b5071c344c002500262078ff28")     # push; adds r7,r0; ldr r4,cp_steps; ...
STEP_DONE = 0x08FE54CB                          # the Journal's step_done (its literal in compute's pool)
STEP_DONE_LIT = 0x08FEA3F8
FLAG_GET = 0x0809D791
N_STEPS = 84
AFTER_TITLE = "Steven is waiting"               # the Area Zero rows go after this one (ANY(0x42F1)), which follows
                                                # "Storm the castle" (ANY(0x41D5)): the log opens on Steven right
                                                # after Team Rainbow Rocket, with Area Zero's first row under it
FONTW, FONTW_LIT = 0x006542E4, 0x0000691C       # GetGlyphWidth_Normal's table, and the literal that holds it
PANE_TEXT_W = 158


def u16(rom, a): return struct.unpack_from("<H", rom, a - 0x08000000 if a >= 0x08000000 else a)[0]
def u32(rom, a): return struct.unpack_from("<I", rom, a - 0x08000000 if a >= 0x08000000 else a)[0]


def rows(species):
    """Area Zero's rows: (title, flag that opens it, condition as steps.py writes them, location, picture, text).
    picture: ("t", trainer picture) or ("m", species) or None."""
    logs = ST.F_LOGS
    place = {"past": "in the crater, in the past", "future": "in the crater, in the future",
             "cavern": "in the Crystal Cavern",
             "vault": "in the Sealed Vault, behind the Crystal Cavern's second cave mouth: pull its stake",
             "icecave": "in the icy cave on the crater wall's middle ledge",
             "underdepths": "in the Underdepths, down the Crystal Cavern's ladder"}
    caught = [(ST.F_KORAIDON_CAUGHT, 1, "Koraidon waits at Arven's picnic spot, in the past."),
              (ST.F_MIRAIDON_CAUGHT, 1, "Miraidon waits at Arven's picnic spot, in the future.")]
    caught += [(flag, 1, "%s: %s." % (name, place[where])) for name, level, where, flag in ST.LEGENDS.values()]
    return [
        ("Area Zero: Jacq", ST.F_RR_DONE, JS.ANY(ST.F_MET_JACQ, anchor=False), "Mossdeep City", ("t", 31),
         "Optional: a teacher from Paldea stands by a black hole in Mossdeep City, down the little stairs below "
         "the Space Center. Talk to him."),
        ("Area Zero: Penny", ST.F_MET_JACQ, JS.ANY(ST.F_MET_PENNY, anchor=False), "Area Zero", None,
         "Step into the black hole. You land on the crater's wall: Penny hides in Research Station No. 1, on the "
         "middle ledge."),
        ("Area Zero: sandwiches", ST.F_MET_PENNY, JS.GROUP("Sandwiches:", [
            (ST.F_MET_ARVEN, 1, "Find Arven at his picnic by the big lake in the south of the crater."),
            (ST.F_TUSK_DONE, 1, "In the past, beat the Titan Great Tusk twice in the den on the crater's west "
                                "side."),
            (ST.F_KORAIDON_UP, 1, "Bring its Sour Herba Mystica to Arven: his sandwich gets Koraidon up again."),
            (ST.F_TREADS_DONE, 1, "Step through a time rift to the future, and beat the Titan Iron Treads twice "
                                  "in the same den."),
            (ST.F_MIRAIDON_UP, 1, "Bring that herb to Arven too: Miraidon gets up again.")], anchor=False),
         "Area Zero", ("m", species["Koraidon"]),
         "Arven's Koraidon and Miraidon are worn out. His sandwiches need Sour Herba Mystica from the two "
         "Titans."),
        ("Area Zero: Nemona", ST.F_MET_PENNY, JS.ANY(ST.F_BEAT_NEMONA, anchor=False), "Area Zero", ("t", 194),
         "Nemona is in the future, in the tall grass south of the waterfall's pond. Beat her in a battle."),
        ("Area Zero: the four logs", ST.F_MET_PENNY, JS.GROUP("Logs:", [
            (logs[0], 1, "Station No. 1, on the crater wall's middle ledge: play the recorder on the left "
                         "counter."),
            (logs[1], 1, "Station No. 2: the house on the shelf below the stairs into the crater."),
            (logs[2], 1, "Station No. 3: the house on the knoll in the east of the crater."),
            (logs[3], 1, "Station No. 4: above the waterfall. Surf across the pond and climb it."),
            (ST.F_LAB_OPEN, 1, "Talk to Penny in Station No. 1: she unlocks the Zero Lab's door.")],
            anchor=False),
         "Area Zero", None,
         "Each research station holds a recorded log from the professors. Play all four, then talk to Penny."),
        ("Area Zero: the Zero Lab", ST.F_GUARDS_UP, JS.ANY(ST.F_STORY_DONE, anchor=False), "Area Zero",
         ("t", 218),
         "Arven and Nemona have opened the shutter in the crater's north-east wall. Go in and talk to the "
         "machine."),
        # (each is met once: caught or knocked out, it is gone - test 18 - so the count is "Done", not "Caught")
        ("Area Zero: legends", ST.F_STORY_DONE, JS.GROUP("Done:", caught, anchor=False), "Area Zero",
         ("m", species["Miraidon"]),
         "Koraidon, Miraidon and the Paradox Pokémon can be caught now, once each: if one faints, it is gone for "
         "good. Jacq's class lives in the research stations."),
    ]


def px(rom, text):
    return sum(rom[FONTW + b] for b in J.enc(text))


def wrap_px(rom, text, width, lines):
    """questlog_patch.wrap_px: words into at most `lines` lines of `width` px; a cut text ends in an ellipsis."""
    out, cur = [], ""
    words = text.split()
    for word in words:
        cand = word if not cur else cur + " " + word
        if px(rom, cand) <= width:
            cur = cand
            continue
        out.append(cur)
        cur = word
        if len(out) == lines:
            break
    else:
        out.append(cur)
        return out
    last = out[-1]
    while px(rom, last + "…") > width:
        last = last.rsplit(" ", 1)[0] if " " in last else last[:-1]
    out[-1] = last + "…"
    return out


COMPUTE2 = r"""
compute2:
    push {r4, r5, r6, r7, lr}
    adds r7, r0, #0
    ldr r4, c2_steps
    movs r5, #0
    movs r6, #0
c2_p1:
    ldrb r0, [r4]
    cmp r0, #0xFF
    beq c2_p1done
    adds r0, r4, #0
    ldr r3, c2_stepdone
    bl c2_callr3
    adds r1, r7, r5
    adds r1, #0x40
    strb r0, [r1]
    cmp r0, #0
    beq c2_p1next
    ldrb r0, [r4, #1]
    cmp r0, #0
    beq c2_p1next
    adds r6, r5, #1
c2_p1next:
    adds r4, #16
    adds r5, #1
    b c2_p1
c2_p1done:
    adds r2, r6, #0
    lsls r0, r2, #4
    ldr r4, c2_steps
    adds r4, r4, r0
c2_p2:
    cmp r2, r5
    beq c2_p2done
    ldrb r0, [r4, #3]
    cmp r0, #0
    bne c2_p2skip
    adds r1, r7, r2
    adds r1, #0x40
    ldrb r0, [r1]
    cmp r0, #0
    beq c2_p2done
c2_p2skip:
    adds r2, #1
    adds r4, #16
    b c2_p2
c2_p2done:
    strb r2, [r7, #6]
    strb r6, [r7, #7]
    ldr r4, c2_steps
    movs r3, #0
c2_p3:
    cmp r3, r5
    beq c2_final
    adds r1, r7, r3
    adds r1, #0x40
    ldrb r0, [r4, #3]
    cmp r0, #0
    bne c2_opt
    ldrb r0, [r1]
    cmp r0, #0
    bne c2_next
    ldrb r0, [r4, #1]
    cmp r0, #0
    beq c2_na
    cmp r3, r6
    blo c2_w1
c2_na:
    cmp r3, r2
    beq c2_w2
    blo c2_w3
    cmp r0, #0
    beq c2_w4
    movs r0, #5
    b c2_w
c2_w4:
    movs r0, #4
    b c2_w
c2_w3:
    movs r0, #3
    b c2_w
c2_w2:
    movs r0, #2
    b c2_w
c2_w1:
    movs r0, #1
c2_w:
    strb r0, [r1]
c2_next:
    adds r4, #16
    adds r3, #1
    b c2_p3
c2_opt:
    push {r1, r2, r3}
    subs r0, #1
    lsls r0, r0, #1
    ldr r1, c2_opts
    ldrh r0, [r1, r0]
    ldr r3, c2_flagget
    bl c2_callr3
    pop {r1, r2, r3}
    cmp r0, #0
    beq c2_w4
    ldrb r0, [r1]
    cmp r0, #0
    bne c2_w1
    b c2_w2
c2_final:
    adds r1, r7, r5
    adds r1, #0x40
    movs r0, #5
    cmp r2, r5
    bne c2_fw
    movs r0, #2
c2_fw:
    strb r0, [r1]
    pop {r4, r5, r6, r7, pc}
c2_callr3:
    bx r3
%s
c2_steps:
    .word %s
c2_stepdone:
    .word %s
c2_flagget:
    .word %s
c2_opts:
    .word %s
"""


def check(rom):
    """What this changes still looks the way it did."""
    for a in STEP_LITS:
        assert u32(rom, a) == STEPS, "a literal of the Journal's step table moved (%08X)" % a
    assert u32(rom, TITLES_LIT) == TITLES and u32(rom, PANES) == PANE_ROWS, "the Quest Log's tables moved"
    for k, was in enumerate(PAGES_WAS):
        o = PAGES - 0x08000000 + 8 * k
        assert tuple(rom[o:o + 4]) == was, "the Quest Log's chapter %d is not what it was" % k
    c = COMPUTE - 0x08000000
    assert bytes(rom[c:c + len(COMPUTE_WAS)]) == COMPUTE_WAS and COMPUTE % 4 == 0, "the Quest Log's compute changed"
    assert u32(rom, STEP_DONE_LIT) == STEP_DONE
    assert u32(rom, FONTW_LIT) == 0x08000000 + FONTW
    n = 0
    while rom[STEPS - 0x08000000 + 16 * n] != 0xFF:
        n += 1
    assert n == N_STEPS, "the Journal has %d steps, not %d" % (n, N_STEPS)
    for k in range(N_STEPS):
        assert rom[STEPS - 0x08000000 + 16 * k + 3] == 0, "step %d already uses the spare byte" % k


def title_of(rom, k):
    p = u32(rom, TITLES + 4 * k) - 0x08000000
    return bytes(rom[p:p + 30]).split(b"\xff")[0]


def install(rom, blob, species):
    """Lays the rows, tables and compute2 into `blob` (lib.Blob, which hands out addresses as it goes) and returns
    a function that makes the ROM's own changes once the blob is written."""
    check(rom)
    after = next(k for k in range(N_STEPS) if title_of(rom, k) == J.enc(AFTER_TITLE))
    s = STEPS - 0x08000000 + 16 * after
    r = s - 16                                  # the row before it: Storm the castle
    assert rom[r] == 0 and rom[r + 2] == 1 and u16(rom, u32(rom, r + 4)) == ST.F_RR_DONE, "Storm the castle changed"
    assert rom[s] == 0 and rom[s + 1] == 1, "Steven is waiting is not an anchor any more"
    at = after + 1                              # where Area Zero's rows go
    az = rows(species)
    opts = blob.put(("journal_az", "opts"), b"".join(struct.pack("<H", r[1]) for r in az), 2)
    new_rows, new_titles, new_panes = [], [], []
    hidden = u32(rom, PANE_ROWS + 12)          # "???", as every row has it
    locw = PANE_TEXT_W - px(rom, "Location:") - 3
    for k, (title, unlock, st, where, pic, body) in enumerate(az):
        assert len(title) <= 24, title
        text = blob.put(("journal_az", "text", k), J.message(JS.POST, body), 1)
        flags = blob.put(("journal_az", "flags", k), b"".join(struct.pack("<H", f) for f in st["flags"]), 2) \
            if st["flags"] else 0
        group = 0
        if st["mode"] == 2:
            label = blob.put(("journal_az", "label", k), J.enc(st["label"]) + b"\xff", 1)
            mem = [(f, w, blob.put(("journal_az", "member", k, i), J.member(t), 1))
                   for i, (f, w, t) in enumerate(st["members"])]
            g = struct.pack("<IBBH", label, len(mem), 1 if st["list_all"] else 0, 0)
            g += b"".join(struct.pack("<HBBI", f, w, 0, t) for f, w, t in mem)
            group = blob.put(("journal_az", "group", k), g, 4)
        new_rows.append(struct.pack("<BBBBIII", st["mode"], 0, len(st["flags"]), k + 1, flags, text, group))
        new_titles.append(blob.put(("journal_az", "title", k), J.enc(title) + b"\xff", 1))
        assert px(rom, where) <= locw, "location too wide for the panel: %r" % where
        loc = blob.put(("journal_az", "loc", k), J.enc(where) + b"\xff", 1)
        ptext = blob.put(("journal_az", "pane", k),
                         b"\xfe".join(J.enc(l) for l in wrap_px(rom, body, PANE_TEXT_W, 3)) + b"\xff", 1)
        kind, pid = (0, 0) if pic is None else ((2 if pic[0] == "t" else 1), pic[1])
        new_panes.append(struct.pack("<BBHIII", kind, 0, pid, loc, ptext, hidden))
    old = lambda base, size, count: [bytes(rom[base - 0x08000000 + size * i:base - 0x08000000 + size * (i + 1)])
                                     for i in range(count)]
    steps_rows = old(STEPS, 16, N_STEPS + 1)                 # (the terminator, FINAL's text at +8, last)
    title_ptrs = old(TITLES, 4, N_STEPS + 1)
    pane_rows = old(PANE_ROWS, 16, N_STEPS + 1)
    steps_new = blob.put(("journal_az", "steps"), b"".join(steps_rows[:at] + new_rows + steps_rows[at:]), 4)
    titles_new = blob.put(("journal_az", "titles"),
                          b"".join(title_ptrs[:at] + [struct.pack("<I", a) for a in new_titles] + title_ptrs[at:]), 4)
    panes_new = blob.put(("journal_az", "panes"), b"".join(pane_rows[:at] + new_panes + pane_rows[at:]), 4)
    assert N_STEPS + len(az) + 1 <= 0x88, "more rows than the Quest Log keeps a status for"
    # compute2: the literal pool must start on a word; a mov r8, r8 in front of it if it would not
    while True:
        base = blob.base + len(blob.data) + (-len(blob.data)) % 4
        for pad in ("", "    mov r8, r8"):
            src = COMPUTE2 % (pad, hex(steps_new), hex(STEP_DONE), hex(FLAG_GET), hex(opts))
            code, dis = J.thumb(src, base)
            if (len(code) - 16) % 4 == 0:
                break
        else:
            raise AssertionError("compute2's pool")
        break
    code_at = blob.put(("journal_az", "compute2"), code, 4)
    assert code_at == base
    assert struct.unpack_from("<4I", code, len(code) - 16) == (steps_new, STEP_DONE, FLAG_GET, opts)

    def apply(rom):
        for a in STEP_LITS:
            struct.pack_into("<I", rom, a - 0x08000000, steps_new)
        struct.pack_into("<I", rom, TITLES_LIT - 0x08000000, titles_new)
        struct.pack_into("<I", rom, PANES - 0x08000000, panes_new)
        n = len(az)
        p = PAGES - 0x08000000
        rom[p + 8 * POST_PAGE + 1] += n                     # Post-game: its rows, and what counts in done/total
        rom[p + 8 * POST_PAGE + 2] += n
        for k in range(POST_PAGE + 1, len(PAGES_WAS)):       # the chapters after it start n rows later
            rom[p + 8 * k] += n
        c = COMPUTE - 0x08000000
        rom[c:c + 8] = bytes.fromhex("004b1847") + struct.pack("<I", code_at | 1)   # ldr r3, [pc]; bx r3
        return {"steps": steps_new, "rows": (at, at + n - 1), "compute2": code_at, "titles": titles_new,
                "panes": panes_new}
    return apply


# ---------------------------------------------------------------------------------------------------- Legends
# The Quest Log's Legends chapter (patches/questlog/legends.py): a row per legendary or mythical Pokemon, by National
# Dex number, ticked once the Pokedex has it caught (GetSetPokedexFlag; the Gen 9 numbers 906-940 are inside the
# hack's 960-number flag arrays). The user: "update the legendary checkbox as well". Area Zero's seven legendaries
# are added after the rest, in Dex order: Koraidon, Miraidon, the four Treasures of Ruin, Terapagos. Not the eight
# Paradox Pokemon (they are not legendary: the Journal's "Area Zero: legends" row has all fifteen), and not
# Ogerpon, the Loyal Three or Pecharunt while nothing hands them out (Part 2), or "Gotta catch 'em all!" could
# never be ticked. The chapter's done/total is printed with two digits (u8dec): 92 + 7 = 99 is as far as it goes
# (the first build added all fifteen and the header read "44/!7").
LEG = 0x09F90000                                # {dex u16, 0, name, hint, where} a row; row 0 "Gotta catch 'em all!"
LEG_LIT = 0x08FEB23C                            # rs_legends: the one literal that holds it
LEG_ROWS = 93
NLEG_CMP = 0x08FEB220                           # legend_all's "cmp r4, #NLEG" (92)
LEG_PANES = PANES + 4                           # PANES[1]: the Legends' info-panel rows
LEG_PANE_ROWS = 0x09FA0550
LEG_PAGE, LEG_PAGE_WAS = 4, (0, 93, 92, 1)
NATDEX_LIT = 0x0806D448                         # SpeciesToNationalPokedexNum's literal: its table (species - 1 ->
                                                # National Dex number), which speciesx moved and grew (0x096B5F00)
ALL_CAUGHT = ("Gotta catch 'em all!",           # questlog_patch.ALL_CAUGHT: row 0's texts, with the count in them
              "The Legends' final goal. Catch every legendary and mythical Pokémon below, all %d of them, "
              "to complete it.",
              "You caught every legendary and mythical Pokémon in the game, all %d of them! Gotta catch 'em all - "
              "and you did. A true Pokémon Master.")


def legends(species):
    """(species, name, hint, where): the hint is shown while it is not in the Pokedex yet (no names), where once
    it is seen or caught."""
    lv = {name: level for name, level, where, flag in ST.LEGENDS.values()}
    vault = "Area Zero: a sealed vault deep in a cave of crystals. Pull the stakes on its icy floor."
    vault_where = ("Area Zero, the Sealed Vault behind the Crystal Cavern's second cave mouth, Lv%d, after the "
                   "story: pull its stake on the icy floor.")
    rows = [
        ("Koraidon", "Paldea's Great Crater, long ago: a worn-out legend rests at a picnic by the lake.",
         "Area Zero, the crater in the past, Lv%d: it waits at Arven's picnic spot once the story is over. The way "
         "in: the black hole in Mossdeep City." % ST.PARTNER_LEVEL),
        ("Miraidon", "Paldea's Great Crater, far in the future: a worn-out legend rests at a picnic by the lake.",
         "Area Zero, the crater in the future, Lv%d: it waits at Arven's picnic spot once the story is over."
         % ST.PARTNER_LEVEL),
        ("Wo-Chien", vault, vault_where % lv["Wo-Chien"]),
        ("Chien-Pao", "Area Zero: an icy cave on the crater's wall, once the story is over.",
         "Area Zero, the icy cave on the crater wall's middle ledge, Lv%d, after the story." % lv["Chien-Pao"]),
        ("Ting-Lu", vault, vault_where % lv["Ting-Lu"]),
        ("Chi-Yu", vault, vault_where % lv["Chi-Yu"]),
        ("Terapagos", "Area Zero: the depths below the cave of crystals, once the story is over.",
         "Area Zero, the Underdepths below the Crystal Cavern, Lv%d, after the story." % lv["Terapagos"]),
    ]
    return [(species[name], name, hint, where) for name, hint, where in rows]


def pane(text):
    """questlog_patch.pane: a text laid out for the detail pane, lines joined by plain line breaks."""
    out = b"\xfe".join(J.enc(l) for l in J.wrap(text)) + b"\xff"
    assert out.count(b"\xfe") < 8, "too long for one page: %r" % text
    return out


def install_legends(rom, blob, species):
    """The Legends chapter with Area Zero's fifteen: a new table (the old rows as they are, row 0's texts with the
    new count, the new rows), a new info-panel table, the literal, the count in legend_all and the chapter's rows."""
    assert u32(rom, LEG_LIT) == LEG and u32(rom, LEG_PANES) == LEG_PANE_ROWS, "the Legends' tables moved"
    o = PAGES - 0x08000000 + 8 * LEG_PAGE
    assert tuple(rom[o:o + 4]) == LEG_PAGE_WAS, "the Legends chapter is not what it was"
    c = NLEG_CMP - 0x08000000
    assert rom[c:c + 2] == bytes((LEG_ROWS - 1, 0x2C)) and rom[c - 2:c] == b"\x01\x34", "legend_all changed"
    old = [bytes(rom[LEG - 0x08000000 + 16 * i:LEG - 0x08000000 + 16 * (i + 1)]) for i in range(LEG_ROWS)]
    natdex = u32(rom, NATDEX_LIT)
    assert u32(rom, NATDEX_LIT + 0x74) == natdex, "SpeciesToNationalPokedexNum's two literals differ"
    dex = lambda sp: u16(rom, natdex + 2 * (sp - 1))
    assert dex(species["Koraidon"]) in range(906, 960), "Koraidon's Dex number is not a Gen 9 one of this build"
    have = {struct.unpack_from("<H", r)[0] for r in old[1:]}
    new = sorted(legends(species), key=lambda r: dex(r[0]))
    assert not have & {dex(r[0]) for r in new}, "a Gen 9 legend is in the Legends already"
    n_all = LEG_ROWS - 1 + len(new)
    # row 0's texts as they are now (the count in them), then with the new count
    h0, w0 = (u32(rom, LEG + 8), u32(rom, LEG + 12))
    for ptr, text in ((h0, ALL_CAUGHT[1] % (LEG_ROWS - 1)), (w0, ALL_CAUGHT[2] % (LEG_ROWS - 1))):
        want = pane(text)
        assert bytes(rom[ptr - 0x08000000:ptr - 0x08000000 + len(want)]) == want, "row 0's text is not what it was"
    hint0 = blob.put(("legends_az", "hint0"), pane(ALL_CAUGHT[1] % n_all), 1)
    where0 = blob.put(("legends_az", "where0"), pane(ALL_CAUGHT[2] % n_all), 1)
    rows = [old[0][:8] + struct.pack("<II", hint0, where0)] + old[1:]
    pane_old = [bytes(rom[LEG_PANE_ROWS - 0x08000000 + 16 * i:LEG_PANE_ROWS - 0x08000000 + 16 * (i + 1)])
                for i in range(LEG_ROWS)]
    locw = PANE_TEXT_W - px(rom, "Location:") - 3

    def panel(key, text):
        return blob.put(("legends_az", "panel") + key,
                        b"\xfe".join(J.enc(l) for l in wrap_px(rom, text, PANE_TEXT_W, 3)) + b"\xff", 1)
    panes = [pane_old[0][:8] + struct.pack("<II", panel(("all", "w"), ALL_CAUGHT[2] % n_all),
                                           panel(("all", "h"), ALL_CAUGHT[1] % n_all))] + pane_old[1:]
    loc = blob.put(("legends_az", "loc"), J.enc("Area Zero") + b"\xff", 1)
    assert px(rom, "Area Zero") <= locw
    for k, (sp, name, hint, where) in enumerate(new):
        ptrs = [blob.put(("legends_az", k, i), t, 1) for i, t in enumerate((J.enc(name) + b"\xff", pane(hint),
                                                                            pane(where)))]
        rows.append(struct.pack("<HHIII", dex(sp), 0, *ptrs))
        panes.append(struct.pack("<BBHIII", 1, 0, sp, loc, panel((k, "w"), where), panel((k, "h"), hint)))
    table = blob.put(("legends_az", "rows"), b"".join(rows), 4)
    ptable = blob.put(("legends_az", "panes"), b"".join(panes), 4)
    assert n_all <= 99, "the Legends' done/total prints two digits: %d legends would read wrong" % n_all

    def apply(rom):
        struct.pack_into("<I", rom, LEG_LIT - 0x08000000, table)
        struct.pack_into("<I", rom, LEG_PANES - 0x08000000, ptable)
        rom[NLEG_CMP - 0x08000000] = n_all
        rom[o + 1] += len(new)
        rom[o + 2] += len(new)
        return {"legends": table, "added": [(dex(sp), name) for sp, name, h, w in new], "count": n_all}
    return apply
