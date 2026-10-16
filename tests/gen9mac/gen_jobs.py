"""The job list for a Gen 9 test pass: every case on a new build and on the build before it (the control).

    python gen_jobs.py <new.gba> <control.gba> <save> <jobs.json>

Suites: the wild (wild_results.txt's 45 placements, slot forced), a battle with each of the 89 new slots (SEED fixed:
the two builds must log the same), catch, give (summary), the Pokedex 906-1025, a TM screen, every level / move /
held-item evolution (test_evolve.lua) and Greavard's night one at every hour (test_evolve_clock.lua), every
item evolution (test_useitem.lua), the 38 new moves, buying the six new items at the Lilycove clerk and selling two,
New Game, the DexNav (seen / unseen), 12 double battles at Lv100, save + a fresh boot, Area Zero's three wild
tables, and sidefix's three cases. Logs of the two builds differ in what the power-on random seed decides (IVs,
levels, abilities) - the seeded battles must be the same."""
import json, re, struct, sys, os
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.dirname(os.path.abspath(__file__)) + "/"
G9 = REPO + "/patches/gen9rest/"
sys.path.insert(0, G9)
import gen9rest_data as D
ROMS = {"new": os.path.abspath(sys.argv[1]), "ctl": os.path.abspath(sys.argv[2])}
SAV = os.path.abspath(sys.argv[3])
OUTJ = sys.argv[4]
rom = open(ROMS["new"], "rb").read()
u32 = lambda o: struct.unpack_from("<I", rom, o)[0]
CH = {0xA1 + i: c for i, c in enumerate("0123456789!?.-・…“”‘’♂♀¥,×/ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")}
CH[0] = " "
def txt(o, n): return "".join(CH.get(b, "?") for b in rom[o:o + n].split(b"\xff")[0])
names = u32(0x144) - 0x08000000
items = u32(0x1C8) - 0x08000000
def sp_id(name):
    for i in range(1, 1408):
        if txt(names + 11 * i, 11) == name: return i
    raise KeyError(name)
def item_id(name):
    for i in range(1, 800):
        if txt(items + 44 * i, 14) == name: return i
    raise KeyError(name)
slot = {k: D.FIRST_SLOT + i for i, (k, *_r) in enumerate(D.SPECIES)}
OLD = {"primeape": "Primeape", "girafarig": "Girafarig", "dunsparce": "Dunsparce", "bisharp": "Bisharp",
       "applin": "Applin", "duraludon": "Duraludon"}
SPECIAL = {"duraludon": 1186}   # 274 is named Duraludon too: Gigantamax Duraludon
def sid(k): return slot[k] if k in slot else SPECIAL.get(k) or sp_id(OLD[k])
NEWOLD = {"annihilape": "Annihilape", "farigiraf": "Farigiraf", "dudunsparce": "Dudunsprce", "kingambit": "Kingambit",
          "dipplin": "Dipplin", "archaludon": "Archaludon"}
def tid(k): return slot[k] if k in slot else sp_id(NEWOLD[k])

cases = []      # (suite, name, lua, env, timeout, sav, after)
WILD = 0x00E17D50
for line in open(G9 + "wild_results.txt", encoding="utf-8-sig"):
    m = re.match(r"(\S+)\s+.*?table\s+(\d+)\s+(\w+)\s+slot\s+(\d+): MET species (\d+) lv \d+ \(want \d+ lv (\d+)-(\d+)\).*\[tile (\d+),(\d+)", line)
    if not m: continue
    key, h, kind, j, sp, lo, hi, x, y = m.groups()
    h, j = int(h), int(j)
    g, n = rom[WILD + 20 * h], rom[WILD + 20 * h + 1]
    rod = (0 if j < 2 else 1 if j < 5 else 2) if kind == "fish" else -1
    pick = {"land": 0x000B4AC8, "water": 0x000B4B84, "fish": 0x000B4BD8}[kind]
    cases.append(("wild", "wild_" + key, "test_wild.lua", dict(G=g, N=n, X=x, Y=y, KIND=kind, SLOT=j, ROD=rod, SP=sp, LO=lo, HI=hi), 240,
                  [[pick, "%02x207047" % j]]))
for k, s in slot.items():
    cases.append(("battle", "battle_" + k, "test_gen9rest.lua", dict(MODE="battle", SPECIES=s, LEVEL=50, SEED=12345), 240))
for k in ("sprigatito", "tinkaton", "wooper-paldea", "gholdengo", "kingambit" if "kingambit" in slot else "gimmighoul", list(slot)[-1]):
    cases.append(("catch", "catch_" + k, "test_gen9rest.lua", dict(MODE="catch", SPECIES=slot[k], LEVEL=30), 400))
for k in ("meowscarada", "palafin", "tatsugiri" if "tatsugiri" in slot else "glimmora", list(slot)[-2]):
    cases.append(("give", "give_" + k, "test_gen9rest.lua", dict(MODE="give", SPECIES=slot[k], LEVEL=40), 240))
cases.append(("dex", "dex_906_1025", "test_gen9rest.lua", dict(MODE="dex", FIRST=906, LAST=1025), 900))
cases.append(("tm", "tm_sprigatito", "test_gen9rest.lua", dict(MODE="tm", SPECIES=slot["sprigatito"]), 240))
for f, meth, what, to in D.EVOLUTIONS:
    if meth in (4, 19):
        env = dict(SPECIES=sid(f), LEVEL=what - 1, TARGET=tid(to))
    elif meth == 16:
        mv = D.FIRST_MOVE + [m[0] for m in D.NEW_MOVES].index(what)
        lv = {"primeape": 35, "girafarig": 32, "dunsparce": 32, "dipplin": 35}.get(f, 30)
        env = dict(SPECIES=sid(f), LEVEL=lv, TARGET=tid(to), KNOWS=mv)
    elif meth in (20, 21):
        env = dict(SPECIES=sid(f), LEVEL=60, TARGET=tid(to), HELD=D.ITEMS[what][0])
    else:
        continue
    cases.append(("evolve", "evolve_%s_%d" % (f, meth), "test_evolve.lua", env, 400))
for f, meth, what, to in D.EVOLUTIONS:
    if meth == 7:
        it = D.ITEMS[what][0] if what in D.ITEMS else item_id(what)
        cases.append(("useitem", "useitem_%s_%s" % (f, str(what).replace(" ", "")), "test_useitem.lua",
                      dict(SPECIES=sid(f), LEVEL=30, ITEM=it, TARGET=tid(to)), 400))
for i, mv in enumerate(D.NEW_MOVES):
    cases.append(("moves", "move_%s" % mv[0], "test_moves.lua", dict(MOVE=D.FIRST_MOVE + i, TURNS=2), 300))
for row in range(19, 25):
    cases.append(("martbuy", "martbuy_row%d" % row, HERE + "test_martbuy_count.lua", dict(ROW=row, NPC="13,19,7,4", FACE="down"), 300))
for it in (770, 775):
    cases.append(("martsell", "martsell_%d" % it, "test_martsell.lua", dict(ITEM=it), 300))
cases.append(("newgame", "newgame", "test_newgame.lua", {}, 600))
for see in (0, slot["nymble"], slot["fidough"]):        # SEE = the species met (and run from) first; 0 = none
    for col in (1, 2, 3, 4):
        cases.append(("dexnav", "dexnav_see%d_col%d" % (see, col), "test_dexnav.lua", dict(SEE=see, COL=col), 600))
PAIRS = [("tatsugiri", "dondozo"), ("meowscarada", "skeledirge"), ("garganacl", "kingambit"), ("palafin", "gholdengo"),
         ("tinkaton", "armarouge"), ("ceruledge", "lokix"), ("espathra", "farigiraf"), ("cetitan", "baxcalibur"),
         ("orthworm", "glimmora"), ("revavroom", "bombirdier"), ("kilowattrel", "bellibolt"), ("annihilape", "houndstone")]
for a, b in PAIRS:
    if a in slot or a in NEWOLD:
        try:
            cases.append(("double", "double_%s_%s" % (a, b), "test_gen9rest_doubles.lua",
                          dict(MODE="double", SPECIES=tid(a), LEVEL=100, SPECIES2=tid(b), LEVEL2=100, TURNS=3), 600))
        except KeyError:
            pass
cases.append(("save", "save", "test_gen9rest.lua", dict(MODE="save", SPECIES=slot["fidough"], LEVEL=20), 400))
for add in range(24):            # Greavard (method 19, night): the save's clock offset + add hours; the log says the hour
    cases.append(("clock", "greavard_add%02d" % add, HERE + "test_evolve_clock.lua",
                  dict(SPECIES=slot["greavard"], LEVEL=29, TARGET=slot["houndstone"], ADD=add), 400))
LAND_B = [0x02, 0x03, 0x24, 0x08, 0x0B, 0x06, 0x0C, 0x09]
def land_tile(g, n):
    h = u32(u32(0xA54698 + 4 * g) - 0x08000000 + 4 * n) - 0x08000000
    lay = u32(h) - 0x08000000
    w, ht, mp = u32(lay), u32(lay + 4), u32(lay + 12) - 0x08000000
    pa, sa = u32(u32(lay + 16) - 0x08000000 + 0x10) - 0x08000000, u32(u32(lay + 20) - 0x08000000 + 0x10) - 0x08000000
    for x, y in sorted(((x, y) for y in range(ht) for x in range(w)), key=lambda p: abs(p[0] - w // 2) + abs(p[1] - ht // 2)):
        blk = struct.unpack_from("<H", rom, mp + 2 * (y * w + x))[0]
        if (blk >> 10) & 3: continue
        mt = blk & 0x3FF
        attr = struct.unpack_from("<H", rom, pa + 2 * mt if mt < 512 else sa + 2 * (mt - 512))[0]
        if attr & 0xFF in LAND_B: return x, y
i = 0
while rom[WILD + 20 * i] != 0xFF:              # Area Zero: the three wild tables (35/90, 35/91, 35/95)
    o = WILD + 20 * i
    g, n = rom[o], rom[o + 1]
    if g == 35 and n in (90, 91, 95) and u32(o + 4):
        arr = u32(u32(o + 4) - 0x08000000 + 4) - 0x08000000
        x, y = land_tile(g, n)
        for j in (0, 5, 11):
            cases.append(("areazero", "az_%d_%d_s%d" % (g, n, j), "test_wild.lua",
                          dict(G=g, N=n, X=x, Y=y, KIND="land", SLOT=j, ROD=-1, SP=struct.unpack_from("<H", rom, arr + 4 * j + 2)[0],
                               LO=rom[arr + 4 * j], HI=rom[arr + 4 * j + 1]), 240, [[0x000B4AC8, "%02x207047" % j]]))
    i += 1
SF = REPO + "/patches/sidefix/test_sidefix.lua"
for scen in ("blue", "soul_dawn", "soul_done"):
    cases.append(("sidefix", "sidefix_" + scen, SF, dict(SCEN=scen), 600))

jobs = []
for tag, rp in ROMS.items():
    for c in cases:
        suite, name, lua, env, to = c[:5]
        jobs.append(dict(name="%s_%s" % (tag, name), suite=suite, rom=rp, sav=None if suite == "newgame" else SAV,
                         lua=lua if lua.startswith("/") else G9 + lua,
                         env=dict(env, TAG=name), timeout=to, patch=c[5] if len(c) > 5 else None))
    jobs.append(dict(name="%s_check" % tag, suite="save", rom=rp, sav=None, after_sav_of="%s_save" % tag,
                     lua=G9 + "test_gen9rest.lua", env=dict(MODE="check", SPECIES=slot["fidough"], TAG="check"), timeout=400))
json.dump(jobs, open(OUTJ, "w"), indent=1)
from collections import Counter
print(len(jobs), "jobs:", dict(Counter(j["suite"] for j in jobs)))
