"""Mine the Pokédex out of the ROM for the guide site: every species and form with its types, base stats,
abilities (the hidden one too), breeding and training facts, Pokédex entry, evolutions, and what it learns.

usage: HE_ROM=<patched rom> python tools/build_pokedex.py
writes site/src/data/pokedex.json, moves.json, abilities.json

Where each table is (ROM header = the pointer block at 0x128-0x1D4, the layout Dynamic Pokémon Expansion uses):
  base stats        header 0x1BC   28 bytes a species. +0 HP Atk Def Spe SpA SpD, +6 types, +8 catch rate,
                                   +9 exp yield, +10 EV yield (2 bits a stat), +12/+14 held items, +16 gender,
                                   +17 egg cycles, +18 friendship, +19 growth, +20 egg groups. Its ability
                                   bytes (+22, +23, +26) are left over and NOT what the game reads.
  abilities         0x097A0000     three u16 a species: the two regular abilities, then THE HIDDEN ABILITY
                                   (Bulbasaur: Overgrow, Overgrow, Chlorophyll). GetAbilityBySpecies (0x0806B694)
                                   jumps to 0x09D73A80, which reads this table; ids run past 255 (Libero is 336).
  ability names     header 0x1C0   13 bytes; descriptions: pointers at header 0x1C4
  type names        0x09D382E8     7 bytes; Fairy is type 23
  moves             header 0x1CC   12 bytes: effect, power, type, accuracy, PP, effect chance, target, priority,
                                   flags, Z power, split (0 physical 1 special 2 status), Z effect
  move descriptions 0x09D2ACFC     a pointer a move (found from Low Sweep's line)
  level-up moves    0x09D89578     a pointer a species -> {u16 move, u8 level}..., level 0xFF ends, level 0 =
                                   learned on evolving (found from Bulbasaur's list; read by 0x0806930C...)
  TMs and HMs       0x09E0FE80     128 moves (TM01-TM120, HM01-HM08); who learns them: 0x08FCD8F4, 16 bytes a
                                   species, bit n = entry n (read by the hack's CanMonLearnTMHM, 0x08FD7D18)
  egg moves         0x09D78128     the vanilla list: species + 20000, then its moves
  evolutions        0x08F387C0     40 bytes a species, five {method, parameter, target, extra}; Eevee's ten are
                                   at 0x09F0B4A0. The methods are read as patches/questlog/evolutions.py reads them.
  National Dex no.  0x08F50370     u16, species - 1
  Pokédex entries   0x09250000     32 bytes a dex number: category, +12 height (dm), +14 weight (hg), +16 text
"""
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "romdata"))
import romlib as R  # noqa: E402
from species_display import FORMS, display_name  # noqa: E402
from display_names import item_name as item_display, move_name as move_display  # noqa: E402

OUT = os.path.join(HERE, "..", "site", "src", "data")
rom = R.rom
u8, u16, u32 = R.u8, R.u16, R.u32
N_SPECIES = 1200

BASE_STATS = u32(0x1BC) - 0x08000000
ABILITY_NAMES = u32(0x1C0) - 0x08000000
ABILITY_DESCS = u32(0x1C4) - 0x08000000
MOVES = u32(0x1CC) - 0x08000000
MOVE_NAMES = u32(0x148) - 0x08000000
SPECIES_NAMES = u32(0x144) - 0x08000000
ITEMS = u32(0x1C8) - 0x08000000
ABILITIES = 0x017A0000
N_ABILITIES = 400
TYPE_NAMES = 0x01D382E8
MOVE_DESCS = 0x01D2ACFC
LEARNSETS = 0x01D89578
TM_MOVES, N_TMHM, N_TM = 0x01E0FE80, 128, 120
TM_COMPAT = 0x00FCD8F4
EGG_MOVES = 0x01D78128
EVOS, EEVEE, EEVEE_EVOS = 0x00F387C0, 133, 0x01F0B4A0
NATDEX = 0x00F50370
DEX_ENTRIES = 0x01250000
REGION_MAP = 0x005A147C
HISUIAN_PILL, GMAX_ITEM = 753, 702

assert rom[BASE_STATS + 28:BASE_STATS + 34] == bytes([45, 49, 49, 45, 65, 65]), "base stats moved"
assert u16(u32(LEARNSETS + 4) - 0x08000000) == 33, "level-up table moved"       # Bulbasaur starts with Tackle
assert u32(0x06B698) == 0x09D73A81, "the ability lookup is not hooked where it was"
assert [u16(ABILITIES + 6 + 2 * k) for k in range(3)] == [65, 65, 34], "ability table moved"   # Bulbasaur

TYPES = {0: "Normal", 1: "Fighting", 2: "Flying", 3: "Poison", 4: "Ground", 5: "Rock", 6: "Bug", 7: "Ghost",
         8: "Steel", 10: "Fire", 11: "Water", 12: "Grass", 13: "Electric", 14: "Psychic", 15: "Ice", 16: "Dragon",
         17: "Dark", 23: "Fairy"}
GROWTH = ["Medium Fast", "Erratic", "Fluctuating", "Medium Slow", "Fast", "Slow"]
EGG_GROUPS = {1: "Monster", 2: "Water 1", 3: "Bug", 4: "Flying", 5: "Field", 6: "Fairy", 7: "Grass",
              8: "Human-Like", 9: "Water 3", 10: "Mineral", 11: "Amorphous", 12: "Water 2", 13: "Ditto",
              14: "Dragon", 15: "Undiscovered"}
STAT_NAMES = ["HP", "Attack", "Defense", "Speed", "Sp. Atk", "Sp. Def"]     # the struct's order
CATEGORY = ["Physical", "Special", "Status"]

# names the 13-character ability table cuts short
ABILITY_FULL = {
    "Compoundeyes": "Compound Eyes", "LightningRod": "Lightning Rod", "Daunt.Shield": "Dauntless Shield",
    "PsychicSurge": "Psychic Surge", "Propel. Tail": "Propeller Tail", "Intrep.Sword": "Intrepid Sword",
    "Elect. Surge": "Electric Surge", "StanceChange": "Stance Change", "MegaLauncher": "Mega Launcher",
    "ParentalBond": "Parental Bond", "Primord. Sea": "Primordial Sea", "DesolateLand": "Desolate Land",
    "W.Compaction": "Water Compaction", "P. Construct": "Power Construct", "Que. Majesty": "Queenly Majesty",
    "Cur.Medicine": "Curious Medicine", "HungerSwitch": "Hunger Switch", "F Metal Body": "Full Metal Body",
    "ShadowShield": "Shadow Shield", "Gor. Tactics": "Gorilla Tactics", "Neutral. Gas": "Neutralizing Gas",
    "Scr. Cleaner": "Screen Cleaner", "SteelySpirit": "Steely Spirit", "Wander. Soul": "Wandering Spirit",
    "Chill. Neigh": "Chilling Neigh", "TanglingHair": "Tangling Hair", "Emerg. Exit": "Emergency Exit",
    "AlchemyPower": "Power of Alchemy",
}


def text(off, maxlen=None):
    """a string from the ROM as one line of plain text"""
    s = R.decode(off, maxlen)[0]
    s = re.sub(r"\{[^}]*\}", " ", s.replace("\n", " "))
    s = re.sub(r"(?<=\d)&|(?<=the )&(?= of)", "%", s)       # romlib reads the percent glyph (0x5B) as "&"
    return re.sub(r"\s+([.,;])", r"\1", re.sub(r"\s+", " ", s)).strip()


def pointer(off):
    v = u32(off)
    return v - 0x08000000 if 0x08000000 <= v < 0x08000000 + len(rom) else None


def rom_name(sid):
    return R.decode(SPECIES_NAMES + 11 * sid, 11)[0]


def item(i):
    return item_display(i, R.decode(ITEMS + 44 * i, 14)[0])


def move(m):
    return move_display(R.decode(MOVE_NAMES + 13 * m, 13)[0])


places = {}
for i in range(213):
    p = pointer(REGION_MAP + 8 * i + 4)
    if p:
        places[i] = text(p)


def article(word):
    return "an" if word[:1].upper() in "AEIOU" else "a"


def evolution(lo, p, x):
    """(short label, full sentence) for one evolution; the cases follow patches/questlog/evolutions.py"""
    it = item(p) if p else ""
    lv = "Level %d" % p
    if lo == 1:
        return "High friendship", "Level it up while it is very friendly toward you."
    if lo == 2:
        return "High friendship, day", "Level it up while it is very friendly toward you, during the day."
    if lo == 3:
        return "High friendship, night", "Level it up while it is very friendly toward you, at night."
    if lo in (4, 13):
        return lv, "It evolves when it reaches level %d." % p
    if lo == 5:
        return "Trade", "Trade it (the trade-evolution NPCs in Fallarbor and Fortree count)."
    if lo == 6 and p == HISUIAN_PILL:
        return it, "Let it hold %s %s when it reaches the level it would normally evolve at." % (article(it), it)
    if lo == 6:
        return "Trade holding " + it, "Trade it while it holds %s %s." % (article(it), it)
    if lo == 7:
        return it, "Use %s %s on it." % (article(it), it)
    if lo in (8, 9, 10):
        how = {8: "higher than", 9: "equal to", 10: "lower than"}[lo]
        tag = {8: "Attack > Defense", 9: "Attack = Defense", 10: "Attack < Defense"}[lo]
        return "%s, %s" % (lv, tag), "It evolves at level %d when its Attack is %s its Defense." % (p, how)
    if lo in (11, 12):
        if p == 30:
            return lv + ", by nature", "It evolves at level %d. Its nature decides which form it takes." % p
        return lv + ", random", "It evolves at level %d. Which form it takes depends on the Pokémon itself." % p
    if lo == 14:
        return lv + ", free party slot", ("It appears when Nincada evolves at level %d, if the party has a free "
                                          "space and there is a Poké Ball in the Bag." % p)
    if lo == 15:
        return "High Beauty", "Level it up while its Beauty is high (feed it Pokéblocks)."
    if lo == 16:
        return "Knows " + move(p), "Level it up while it knows %s." % move(p)
    if lo == 17:
        where = places.get(p, "a special place")
        return "Level up at " + where, "Level it up at %s." % where
    if lo in (18, 19, 30):
        when = {18: ("day", "during the day"), 19: ("night", "at night"), 30: ("dusk", "in the evening")}[lo]
        return "%s, %s" % (lv, when[0]), "It evolves when it reaches level %d %s." % (p, when[1])
    if lo in (20, 21):
        when = ("day", "during the day") if lo == 20 else ("night", "at night")
        return "Hold %s, %s" % (it, when[0]), "Level it up %s while it holds %s %s." % (when[1], article(it), it)
    if lo in (22, 23):
        g = "male" if lo == 22 else "female"
        return "%s, %s" % (lv, g), "A %s one evolves when it reaches level %d." % (g, p)
    if lo == 24:
        return lv + ", in rain", "It evolves when it reaches level %d while it is raining." % p
    if lo == 25:
        mate = display_name(p, rom_name(p))
        return "With %s in party" % mate, "Level it up with %s %s in your party." % (article(mate), mate)
    if lo == 26:
        return lv + ", Dark type in party", "It evolves at level %d with a Dark-type Pokémon in your party." % p
    if lo == 29:
        t = TYPES.get(p, "a")
        return "Friendship + %s move" % t, ("Level it up while it is very friendly toward you and knows a "
                                           "%s-type move." % t)
    if lo == 33:
        where = places.get(x, "a special place")
        return "Level up at " + where, "Level it up at %s." % where
    if lo in (27, 28):
        g = "male" if lo == 27 else "female"
        return "%s, %s" % (it, g), "Use %s %s on a %s one." % (article(it), it, g)
    return "Special", "It evolves in a special way."


def form_change(lo, p):
    """how a Mega Evolution, Primal Reversion, Gigantamax or Ultra Burst is triggered"""
    if lo == 250:
        return "Ultra Burst"
    if lo == 252:
        return "Knows " + move(p)
    if p == GMAX_ITEM:
        return "Gigantamax (%s)" % item(p)
    return item(p)


# ---------------- moves and abilities ----------------
moves = {}
for m in range(1, 937):
    name = R.decode(MOVE_NAMES + 13 * m, 13)[0]
    if not name.strip() or "{" in name:
        continue
    b = rom[MOVES + 12 * m:MOVES + 12 * m + 12]
    d = pointer(MOVE_DESCS + 4 * m)
    moves[m] = {"id": m, "name": move_display(name), "type": TYPES.get(b[2], "Normal"),
                "cat": CATEGORY[b[10]] if b[10] < 3 else "Status", "power": b[1], "acc": b[3], "pp": b[4],
                "desc": text(d) if d else ""}

tm_moves = [u16(TM_MOVES + 2 * i) for i in range(N_TMHM)]
tm_label = ["TM%02d" % (i + 1) if i < N_TM else "HM%02d" % (i - N_TM + 1) for i in range(N_TMHM)]
for i, m in enumerate(tm_moves):
    if m in moves:
        moves[m].setdefault("tm", tm_label[i])

abilities = {}
for a in range(1, N_ABILITIES):
    name = R.decode(ABILITY_NAMES + 13 * a, 13)[0].strip()
    if not name or "{" in name:
        continue
    d = pointer(ABILITY_DESCS + 4 * a)
    abilities[a] = {"id": a, "name": ABILITY_FULL.get(name, name), "desc": text(d) if d else ""}

# ---------------- egg moves ----------------
egg = {}
o, cur = EGG_MOVES, None
while True:
    v = u16(o)
    o += 2
    if v == 0xFFFF:
        break
    if v > 20000:
        cur = v - 20000
        egg[cur] = []
    elif cur is not None:
        egg[cur].append(v)

# ---------------- species ----------------
natdex = {sid: u16(NATDEX + 2 * (sid - 1)) for sid in range(1, N_SPECIES)}
first = {}                                    # National Dex number -> the species that owns it
for sid in range(1, N_SPECIES):
    if natdex[sid]:
        first.setdefault(natdex[sid], sid)

SKIP = set(range(412, 440)) | {1199}          # the Egg, Unown's letter forms, a blank slot


def is_species(sid):
    if sid in SKIP or not 0 < sid < N_SPECIES:
        return False
    b = rom[BASE_STATS + 28 * sid:BASE_STATS + 28 * sid + 6]
    name = rom_name(sid)
    return sum(b) > 0 and name.strip() not in ("", "?") and (not name.startswith("{CN") or sid in FORMS)


def form_kind(sid, name):
    if name.startswith(("Mega ", "Primal ")):
        return "Mega"
    if name.startswith(("Gigantamax ", "Eternamax ")):
        return "Gigantamax"
    if name.startswith(("Alolan ", "Galarian ", "Hisuian ")):
        return "Regional"
    return "Form" if sid in FORMS else "Standard"


def learnset(sid):
    p = pointer(LEARNSETS + 4 * sid)
    out = []
    while p is not None and len(out) < 120:
        mv, lv = u16(p), rom[p + 2]
        if lv == 0xFF:
            break
        if mv in moves:
            out.append([lv, mv])
        p += 3
    return out


names = {sid: display_name(sid, rom_name(sid)) for sid in range(1, N_SPECIES)}
# the forms that share a printed name with another species get told apart here
for sid, extra in ((975, "Douse Drive"), (976, "Shock Drive"), (977, "Burn Drive"), (978, "Chill Drive"),
                   (275, "Amped"), (276, "Low Key"), (1007, "Single Strike"), (1008, "Rapid Strike")):
    names[sid] = "%s (%s)" % (names[sid].split(" (")[0], extra)
names[1151] = "Toxtricity (Low Key)"

species = []
slugs = {}
for sid in range(1, N_SPECIES):
    if not is_species(sid):
        continue
    b = rom[BASE_STATS + 28 * sid:BASE_STATS + 28 * sid + 28]
    own = [u16(ABILITIES + 6 * sid + 2 * k) for k in range(3)]
    name = names[sid]
    dex = natdex[sid]
    if not dex:                               # the Gigantamax slots carry no number: take the base species'
        base_name = re.sub(r"^(Gigantamax|Eternamax) | \(.*\)$", "", name)
        dex = next((natdex[s] for s in range(1, N_SPECIES) if rom_name(s) == rom_name(sid) and natdex[s]), 0)
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower().replace("♀", "-f").replace("♂", "-m").replace("é", "e")
                  .replace("'", "").replace("’", "").replace(".", "").replace(":", "").replace("%", "")).strip("-")
    if slug in slugs:
        slugs[slug] += 1
        slug = "%s-%d" % (slug, slugs[slug])
    else:
        slugs[slug] = 1
    ev = struct.unpack_from("<H", b, 10)[0]
    yields = [(STAT_NAMES[i], (ev >> (2 * i)) & 3) for i in range(6)]
    entry = {
        "sid": sid, "name": name, "slug": slug, "dex": dex, "form": form_kind(sid, name),
        "types": [TYPES.get(b[6], "Normal")] if b[6] == b[7] else [TYPES.get(b[6], "Normal"), TYPES.get(b[7], "Normal")],
        "stats": [b[0], b[1], b[2], b[4], b[5], b[3]],          # HP Atk Def SpA SpD Spe
        "abilities": [a for a in dict.fromkeys(own[:2]) if a in abilities],
        "hidden": own[2] if own[2] in abilities and own[2] not in own[:2] else 0,
        "catch": b[8], "exp": b[9],
        "ev": ["%d %s" % (n, s) for s, n in yields if n],
        "gender": b[16], "eggCycles": b[17], "friendship": b[18],
        "growth": GROWTH[b[19]] if b[19] < len(GROWTH) else "",
        "eggGroups": [EGG_GROUPS[g] for g in dict.fromkeys((b[20], b[21])) if g in EGG_GROUPS],
        "items": [it for it in (struct.unpack_from("<H", b, 12)[0], struct.unpack_from("<H", b, 14)[0])],
    }
    entry["items"] = [{"id": it, "name": item(it), "rate": rate}
                      for it, rate in zip(entry["items"], ("50%", "5%")) if 0 < it < 769]
    if dex:
        d = DEX_ENTRIES + 32 * dex
        category = R.decode(d, 12)[0]
        desc = pointer(d + 16)
        if category.strip() and "{CN" not in category:
            entry["category"] = category.strip()
            entry["height"] = u16(d + 12)
            entry["weight"] = u16(d + 14)
            if desc:
                entry["entry"] = text(desc)

    evos, forms = [], []
    o, n = (EEVEE_EVOS, 10) if sid == EEVEE else (EVOS + 40 * sid, 5)
    for k in range(n):
        m, p, t, x = struct.unpack_from("<HHHH", rom, o + 8 * k)
        lo = m & 0xFF
        if not m or not is_species(t) or lo == 255:
            continue
        if lo >= 250:
            forms.append({"to": t, "how": form_change(lo, p)})
            continue
        short, sentence = evolution(lo, p, x)
        if m >> 8 in (0x3F, 0xFF):
            sentence += " To get its Egg, a parent must hold %s %s." % (article(item(x)), item(x))
        evos.append({"to": t, "how": short, "text": sentence})
    if evos:
        entry["evo"] = evos
    if forms:
        entry["forms"] = forms
    entry["levelUp"] = learnset(sid)
    bits = int.from_bytes(rom[TM_COMPAT + 16 * sid:TM_COMPAT + 16 * sid + 16], "little")
    entry["tm"] = [i for i in range(N_TMHM) if bits >> i & 1 and tm_moves[i] in moves]
    entry["egg"] = [m for m in egg.get(sid, []) if m in moves]
    species.append(entry)

species.sort(key=lambda s: (s["dex"] or 9999, s["form"] != "Standard", s["sid"]))
learned = {m for s in species for _, m in s["levelUp"]} | {tm_moves[i] for s in species for i in s["tm"]} \
    | {m for s in species for m in s["egg"]}
used_abilities = {a for s in species for a in s["abilities"] + [s["hidden"]] if a}

os.makedirs(OUT, exist_ok=True)


def dump(name, obj):
    json.dump(obj, open(os.path.join(OUT, name), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))


dump("pokedex.json", {"tm": [{"label": tm_label[i], "move": tm_moves[i]} for i in range(N_TMHM)], "species": species})
dump("moves.json", [moves[m] for m in sorted(moves) if m in learned])
dump("abilities.json", [abilities[a] for a in sorted(abilities) if a in used_abilities])
print("species and forms: %d (%d standard) | moves learned by something: %d of %d | abilities in use: %d" % (
    len(species), sum(s["form"] == "Standard" for s in species), len(learned), len(moves), len(used_abilities)))
print("with a hidden ability: %d | with a dex entry: %d | with egg moves: %d" % (
    sum(1 for s in species if s["hidden"]), sum(1 for s in species if "entry" in s), sum(1 for s in species if s["egg"])))
