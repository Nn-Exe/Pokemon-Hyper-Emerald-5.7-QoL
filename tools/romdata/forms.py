"""How a Pokémon gets into each of its other forms, read from the ROM: one list for the guide site's Pokédex
(tools/build_pokedex.py) and for the Quest Log's Evolutions pages (patches/questlog/evolutions.py).

    links(rom, item_name, move_name, ability_name, ability_text) -> [Link]

A Link is a dict: {"from": species, "to": species, "kind", "how", "short", "text", "battle"}.
  how     the label beside the arrow ("Venusaurite", "Hold Griseous Orb", "Uses Sunsteel Strike")
  short   the same when room is tight (the Quest Log's nine lines)
  text    one sentence
  battle  True when the form lasts only for the battle

Where each kind comes from (v5.7 bugfix 2; every address below is asserted, so a ROM that moved them stops here):

  mega / primal / ultra   the evolution table 0x08F387C0, methods 250-253 (see evolutions.py). The Wishing Piece
                          row (item 702, Charizard only) is a Gigantamax by held item.
  gmax                    the battle-form table 0x08C9A3B0: {u16 species, u16 form, u16 item}, 0xFEFE ends. The
                          routine 0x08FF1858 walks it for both parties when a battle is set up (called from
                          0x08FF1134): item 0xEFEF means "this Pokémon's Gigantamax bit is set" (byte +0x4E, bit
                          7), the bit the Max Soup man on Champion Island sets for 3 Max Mushrooms (script
                          0x098A7425); any other item must be held (Zacian, Zamazenta).
  held                    the held-item table 0x09E0FC70: {u16 form, u16 base, u16 item, u16 item or 0xFFF},
                          0xFFF ends. SetMonData's held-item case jumps to 0x0981E826, which swaps the species
                          the moment the item is given or taken: Arceus (a Plate or the Z-Crystal of that type),
                          Silvally, Genesect, Giratina, Dialga, Palkia, the two Armored Mewtwo. Shadow Lugia's
                          row is the odd one: the Dusk Stone turns Lugia, and only the item in the low 12 bits
                          of its last word (0x1063 -> 99) turns it back.
  move                    the battle routine 0x09D5D380 (literal pool 0x09D5D9A4): the attacker's species and
                          the move being used. Marshadow + Spectral Thief, Solgaleo + Sunsteel Strike, Lunala +
                          Moongeist Beam (or each one's own Z-Move), Xerneas + Geomancy, Keldeo + Secret Sword.
                          Meloetta + Relic Song is at 0x09D59922.
  ability                 the battle code swaps these by ability (Zen Mode 0x09D4CC84, Gulp Missile 0x09D59964,
                          Battle Bond 0x09D64CBC ...). Listed here by hand; each is checked against the game's
                          own list of battle forms and what they turn back into (0x09D77138, {u16, u16}, 0xFFFF
                          ends) and against the base species really having the ability.
  item / fusion           Bag items whose field-use routine starts a script: Gracidea 0x08FD6A84, Prison Bottle
                          0x08FD6500, Reveal Glass 0x08FD6B40 (its routine 0x09F0157C: the three genies and
                          Enamorus), the four Nectars 0x08FD6688.., Rotom Catalog 0x08FD6794, Deoxys Meteor
                          0x08FD6300 (routine 0x08FD7A04), Zygarde Cube 0x0988FFC1, DNA Splicers 0x08FD6554,
                          N-Solarizer / N-Lunarizer / Unity Reins 0x094A27C0.
  quest                   two forms a side quest hands out (patches/questlog/sidecontent.py has both).
"""
import struct

EVOS = 0x00F387C0
EEVEE, EEVEE_EVOS = 133, 0x01F0B4A0
BATTLE_FORMS, GMAX_MARK = 0x00C9A3B0, 0xEFEF
HELD_FORMS = 0x01E0FC70
REVERTS = 0x01D77138
ABILITIES = 0x017A0000
SPNAMES_PTR, ABNAMES_PTR = 0x144, 0x1C0
NSPECIES = 1200
WISHING_PIECE = 702
JUDGMENT, LEGEND_PLATE = 449, 751          # 0x09D5D8B4: Arceus, Judgment, the Legend Plate held

# ---- by hand, from the code (see the docstring); every species is checked against its ROM name below ----
MOVE_FORMS = [  # base, form, move, the Z-Move that also does it
    (855, 1058, 666, 717), (844, 1066, 667, 726), (845, 1067, 668, 727), (769, 1057, 601, 0), (700, 986, 548, 0),
    (701, 965, 547, 0),
]
ABILITY_FORMS = [  # base, form, ability, when (None: the game's own description says it)
    (474, 983, "Flower Gift", "It takes this form in harsh sunlight."),
    (734, 960, "Stance Change", None),
    (608, 961, "Zen Mode", None), (1197, 1198, "Zen Mode", None),
    (827, 971, "Shields Down", None),
    (799, 962, "Schooling", None),
    (1011, 963, "Battle Bond", None),
    (831, 997, "Disguise", "It takes this form once its disguise has taken a hit."),
    (1086, 1177, "Ice Face", "It takes this form once a physical hit has broken its ice."),
    (1077, 1146, "Gulp Missile", "It comes up with its catch after Surf or Dive, while above half HP."),
    (1077, 1078, "Gulp Missile", "It comes up with its catch after Surf or Dive, at half HP or less."),
    (1087, 1179, "Hunger Switch", None),
    (1009, 967, "Power Construct", None),
]
NOT_IN_REVERTS = {(1009, 967)}          # Zygarde's is restored by other code (0x09D58310)
ITEM_FORMS = [  # base, form, item
    (545, 897, 672), (773, 969, 673),
    (694, 899, 674), (695, 900, 674), (698, 901, 674), (1023, 1024, 674),
    (532, 955, 616), (532, 956, 616), (532, 957, 616), (532, 958, 616), (532, 959, 616),
    (410, 952, 543), (410, 953, 543), (410, 954, 543),
    (771, 968, 621),
]
ORICORIO = [(972, 618), (973, 619), (974, 620)]            # form, nectar (the Red Nectar turns it back)
ZYGARDE_BUILT = (771, 1009, 621, 100)                       # put together from 100 Zygarde Cells with the Cube
FUSIONS = [  # base, form, item, the other Pokémon
    (699, 995, 671, 696), (699, 996, 671, 697), (853, 1068, 641, 844), (853, 1069, 642, 845),
    (1098, 1099, 742, 1088), (1098, 1100, 742, 1089),
]
QUESTS = [  # base, form, label, sentence
    (157, 1091, "Burning Soul quest", "The reward of the Burning Soul side quest: the hidden cave at the foot of "
                                      "Mt. Chimney, Route 112."),
    (711, 1011, "Hero Greninja quest", "The reward of the Hero Greninja side quest: Elder Koga's trial in Koga's "
                                       "Village, through the Route 102 forest."),
]
EXPECT = {  # ROM name each id must carry, so a renumbered ROM cannot mislabel anything
    855: "Marshadow", 844: "Solgaleo", 845: "Lunala", 769: "Xerneas", 700: "Keldeo", 701: "Meloetta",
    474: "Cherrim", 734: "Aegislash", 608: "Darmanitan", 1197: "Darmanitan", 827: "Minior", 799: "Wishiwashi",
    1011: "Greninja", 831: "Mimikyu", 1086: "Eiscue", 1077: "Cramorant", 1087: "Morpeko", 1009: "Zygarde",
    545: "Shaymin", 773: "Hoopa", 694: "Tornadus", 695: "Thundurus", 698: "Landorus", 1023: "Enamorus",
    532: "Rotom", 410: "Deoxys", 771: "Zygarde", 699: "Kyurem", 853: "Necrozma", 1098: "Calyrex",
    696: "Reshiram", 697: "Zekrom", 1088: "Glastrier", 1089: "Spectrier", 157: "Typhlosion", 711: "Greninja",
    972: "Oricorio", 973: "Oricorio", 974: "Oricorio",
}


NATDEX = 0x00F50370
BASE_STATS_PTR = 0x1BC
SKIP = set(range(412, 440)) | {1199}    # the Egg, Unown's letter forms, a blank slot
NO_NUMBER = {990, 991, 992, 993}        # the hack's four restored fossil Pokémon: the table gives them Pikachu's 25
DEX_FIX = {1062: 215}                   # Hisuian Sneasel carries 586, Sawsbuck's: it belongs with Sneasel


def natdex(rom, sid):
    """A species' National Dex number as the guide uses it: the ROM's table with its five wrong slots put right.
    The Gigantamax slots (no number in the table) take their species' through the name they share."""
    if sid in NO_NUMBER:
        return 0
    return struct.unpack_from("<H", rom, NATDEX + 2 * (DEX_FIX.get(sid, sid) - 1))[0]


def is_species(rom, sid, named=()):
    """Does this slot hold a Pokémon: base stats, and a name in the Latin alphabet or one of `named` (the forms
    species_display names)."""
    if sid in SKIP or not 0 < sid < NSPECIES:
        return False
    stats = struct.unpack_from("<I", rom, BASE_STATS_PTR)[0] - 0x08000000 + 28 * sid
    names = struct.unpack_from("<I", rom, SPNAMES_PTR)[0] - 0x08000000 + 11 * sid
    first = rom[names]
    latin = 0xBB <= first <= 0xEE
    return sum(rom[stats:stats + 6]) > 0 and (latin or sid in named)


def article(word):
    return "an" if word[:1].upper() in "AEIOU" else "a"


def links(rom, species_name, item_name, move_name, ability_text):
    """Every form change the ROM knows. species_name(sid) / item_name(id) / move_name(id) give the names to
    print; ability_text(name) the game's description of an ability, or None."""
    def u16(o):
        return struct.unpack_from("<H", rom, o)[0]

    def u32(o):
        return struct.unpack_from("<I", rom, o)[0]

    def rom_name(sid):
        base = u32(SPNAMES_PTR) - 0x08000000
        out = []
        for b in rom[base + 11 * sid:base + 11 * sid + 11]:
            if b == 0xFF:
                break
            out.append(chr(b - 0xBB + 65) if 0xBB <= b <= 0xD4 else chr(b - 0xD5 + 97) if 0xD5 <= b <= 0xEE else "?")
        return "".join(out)

    def ability_names(sid):
        base = u32(ABNAMES_PTR) - 0x08000000
        out = []
        for k in range(3):
            a = u16(ABILITIES + 6 * sid + 2 * k)
            raw = rom[base + 13 * a:base + 13 * a + 13]
            out.append("".join(chr(b - 0xBB + 65) if 0xBB <= b <= 0xD4 else chr(b - 0xD5 + 97) if 0xD5 <= b <= 0xEE
                               else " " if b == 0 else "" for b in raw.split(b"\xff")[0]))
        return out

    assert (u16(BATTLE_FORMS + 24), u16(BATTLE_FORMS + 26), u16(BATTLE_FORMS + 28)) == (3, 254, GMAX_MARK), \
        "battle-form table moved"
    assert (u16(HELD_FORMS), u16(HELD_FORMS + 2)) == (874, 546), "held-item form table moved"
    assert (u16(REVERTS), u16(REVERTS + 2)) == (983, 474), "battle-form revert table moved"
    assert [u32(0x01D5D9A4 + 4 * k) for k in (0, 3, 6, 9, 10)] == [1058, 1066, 1067, 1057, 986], \
        "the move-triggered forms' literal pool moved"
    assert u32(0x01D59BFC) == 965, "Meloetta's literal moved"
    for sid, want in EXPECT.items():
        assert rom_name(sid).startswith(want[:8]), "species %d is %r, expected %s" % (sid, rom_name(sid), want)

    out = []

    def add(frm, to, kind, how, text, battle, short=None):
        out.append({"from": frm, "to": to, "kind": kind, "how": how, "short": short or how, "text": text,
                    "battle": battle})

    # ---- Mega Evolution, Primal Reversion, Ultra Burst: the evolution table's methods 250-253 ----
    reverting = set()                       # the Gigantamax slots carry a copy of their species' Mega rows
    rows = []
    for sp in range(1, NSPECIES):
        o, n = (EEVEE_EVOS, 10) if sp == EEVEE else (EVOS + 40 * sp, 5)
        for k in range(n):
            m, p, t, _ = struct.unpack_from("<HHHH", rom, o + 8 * k)
            lo = m & 0xFF
            if lo == 255:
                reverting.add(sp)
            elif m and 250 <= lo <= 253 and 0 < t < NSPECIES:
                rows.append((sp, lo, p, t))
    wishing = set()
    for sp, lo, p, t in rows:
        if sp in reverting:
            continue
        name = species_name(sp)
        if lo == 250:
            add(sp, t, "ultra", "Ultra Burst", "%s uses Ultra Burst in battle." % name, True)
        elif lo == 252:
            mv = move_name(p)
            add(sp, t, "mega", "Knows " + mv, "It Mega Evolves in battle when it knows %s." % mv, True)
        elif lo == 253:
            it = item_name(p)
            add(sp, t, "primal", it, "Primal Reversion: it enters battle holding the %s." % it, True)
        elif p == WISHING_PIECE:
            wishing.add((sp, t))
        else:
            it = item_name(p)
            add(sp, t, "mega", it, "It Mega Evolves in battle while holding the %s." % it, True)

    # ---- Gigantamax, and the two that change by held item when a battle starts ----
    o = BATTLE_FORMS
    seen = set()
    while u16(o) != 0xFEFE:
        sp, t, it = u16(o), u16(o + 2), u16(o + 4)
        o += 6
        seen.add((sp, t))
        if it == GMAX_MARK:
            soup = ("Give it Max Soup (Champion Island: the cook wants 3 Max Mushrooms and feeds the first "
                    "Pokémon in your party). It then takes this form when it Dynamaxes.")
            if (sp, t) in wishing:
                wp = item_name(WISHING_PIECE)
                add(sp, t, "gmax", "Max Soup or " + wp, soup + " Holding the %s does it too." % wp, True,
                    "Max Soup/" + wp)
            else:
                add(sp, t, "gmax", "Max Soup", soup, True)
        else:
            name = item_name(it)
            add(sp, t, "held", "Hold " + name, "It enters battle in this form while holding the %s." % name, True,
                name)
    for sp, t in sorted(wishing - seen):
        wp = item_name(WISHING_PIECE)
        add(sp, t, "gmax", wp, "It takes this form in battle while holding the %s." % wp, True)

    # ---- forms that come and go with a held item ----
    o = HELD_FORMS
    while u16(o) != 0xFFF:
        form, base, a, b = (u16(o + 2 * k) for k in range(4))
        o += 8
        first = item_name(a)
        if b >> 12 == 1:                    # Lugia: this item turns it, the one in the low bits turns it back
            back = item_name(b & 0xFFF)
            add(base, form, "held", "Hold " + first,
                "Give it the %s to hold and it changes. It stays that way until it is given the %s." % (first, back),
                False, first)
            continue
        if b != 0xFFF:                      # Arceus: the type's Z-Crystal is listed first, its Plate second
            plate = item_name(b)
            add(base, form, "held", "Hold " + plate,
                "It changes form while it holds the %s or the %s. In battle, %s used while holding the %s changes "
                "its form too." % (plate, first, move_name(JUDGMENT), item_name(LEGEND_PLATE)), False, plate)
        else:
            add(base, form, "held", "Hold " + first, "It changes form while it holds the %s." % first, False, first)

    # ---- by move ----
    for base, form, mv, z in MOVE_FORMS:
        m = move_name(mv)
        extra = " or its own Z-Move" if z else ""
        back = " The same move turns it back." if base == 701 else ""
        add(base, form, "move", "Uses " + m, "In battle it changes form when it uses %s%s.%s" % (m, extra, back),
            True, m)

    # ---- by ability ----
    pairs = set()
    o = REVERTS
    while u16(o) != 0xFFFF:
        pairs.add(frozenset((u16(o), u16(o + 2))))
        o += 4
    for base, form, ab, when in ABILITY_FORMS:
        assert (base, form) in NOT_IN_REVERTS or frozenset((base, form)) in pairs, \
            "%d -> %d is not in the game's battle-form table" % (base, form)
        key = ab.replace(" ", "").lower()
        assert any(n.replace(" ", "").replace(".", "").lower()[:8] == key[:8] or
                   (ab == "Power Construct" and n.startswith("P")) for n in ability_names(base)), \
            "%s does not have %s: %s" % (species_name(base), ab, ability_names(base))
        said = when or ability_text(ab) or ""
        add(base, form, "ability", ab + " (ability)", ("In battle, through its %s ability. %s" % (ab, said)).strip(),
            True, ab)

    # ---- by an item used from the Bag ----
    for base, form, it in ITEM_FORMS:
        name = item_name(it)
        if base == 532:
            text = "Use the %s from the Bag and pick an appliance for Rotom to enter." % name
        elif base == 410:
            text = "Use the %s from the Bag and pick the form." % name
        elif base == 771:
            text = ("Use the %s from the Bag: a Zygarde with Aura Break changes between this and its 50%% form."
                    % name)
        else:
            text = "Use the %s from the Bag on it. Using it again turns it back." % name
        add(base, form, "item", name, text, False)
    orig = next(sid for sid in range(1, NSPECIES) if rom_name(sid) == "Oricorio")
    for form, nectar in ORICORIO:
        name = item_name(nectar)
        add(orig, form, "item", name, "Use the %s from the Bag on it." % name, False)
    base, form, cube, cells = ZYGARDE_BUILT
    name = item_name(cube)
    add(base, form, "item", name, "Put together with the %s from %d Zygarde Cells: the one with Power Construct."
        % (name, cells), False)

    # ---- fusions ----
    for base, form, it, other in FUSIONS:
        name, partner = item_name(it), species_name(other)
        add(base, form, "fusion", "%s + %s" % (name, partner),
            "Use the %s from the Bag with %s in the party. Using it again splits them." % (name, partner), False,
            name)

    # ---- quest rewards ----
    for base, form, label, text in QUESTS:
        add(base, form, "quest", label, text, False)
    return out
