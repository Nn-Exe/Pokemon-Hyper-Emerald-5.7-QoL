"""The second job list: breeding, Rare Candy, the owned-Pokemon screens and the new Pokemon fighting with their own
moves (test_breed.lua, test_candy.lua, test_screens.lua, test_fight2.lua) - on a new build and on a control.

    python gen_jobs_owned.py <new.gba> <control.gba> <save> <jobs.json>

The screens are made on the new build only (they are for looking at); the rest on both."""
import json, os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__)) + "/"
REPO = os.path.dirname(os.path.dirname(HERE.rstrip("/")))
sys.path.insert(0, REPO + "/patches/gen9rest")
import gen9rest_data as D
ROMS = {"new": os.path.abspath(sys.argv[1]), "ctl": os.path.abspath(sys.argv[2])}
SAV, OUTJ = os.path.abspath(sys.argv[3]), sys.argv[4]
rom = open(ROMS["new"], "rb").read()
u32 = lambda o: struct.unpack_from("<I", rom, o)[0]
CH = {0xA1 + i: c for i, c in enumerate("0123456789!?.-・…“”‘’♂♀¥,×/ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")}
names = u32(0x144) - 0x08000000
def nm(i): return "".join(CH.get(b, "?") for b in rom[names + 11 * i:names + 11 * i + 11].split(b"\xff")[0])
def sp_id(name, skip=()):
    for i in range(1, 1408):
        if i not in skip and nm(i) == name: return i
    raise KeyError(name)
slot = {k: D.FIRST_SLOT + i for i, (k, *_r) in enumerate(D.SPECIES)}
OLD = {"primeape": sp_id("Primeape"), "girafarig": sp_id("Girafarig"), "dunsparce": sp_id("Dunsparce"),
       "bisharp": sp_id("Bisharp"), "applin": sp_id("Applin"), "duraludon": 1186, "mankey": sp_id("Mankey"),
       "pawniard": sp_id("Pawniard")}
OLD_PRE = {"primeape": "mankey", "bisharp": "pawniard"}          # the game's own evolutions before those
def sid(k): return slot.get(k) or OLD[k]
pre = {}
for f, meth, what, to in D.EVOLUTIONS:
    pre.setdefault(to, f)
def base(k):
    while k in pre: k = pre[k]
    return OLD_PRE.get(k, k)
NO_EGGS = {"gimmighoul", "gholdengo"}                             # Undiscovered egg group (Scarlet/Violet)
cases = []                                                        # (suite, name, lua, env, timeout, both builds?)
for k, s in slot.items():
    want = 0 if k in NO_EGGS else sid(base(k))
    cases.append(("breed", "breed_" + k, "test_breed.lua", dict(PARENT=s, WANT=want), 400, True))
for f, meth, what, to in D.EVOLUTIONS:
    env = None
    if meth == 4:
        env = dict(SPECIES=sid(f), LEVEL=what - 1, TARGET=sid(to))
    elif meth == 19:
        for hr, tag in ((22, "night"), (12, "day")):
            cases.append(("candy", "candy_%s_%s" % (f, tag), "test_candy.lua",
                          dict(SPECIES=sid(f), LEVEL=what - 1, TARGET=sid(to), HOUR=hr), 400, True))
        continue
    elif meth == 16:
        mv = D.FIRST_MOVE + [m[0] for m in D.NEW_MOVES].index(what)
        lv = {"primeape": 35, "girafarig": 32, "dunsparce": 32, "dipplin": 35}.get(f, 30)
        env = dict(SPECIES=sid(f), LEVEL=lv, TARGET=sid(to), KNOWS=mv)
    elif meth in (20, 21):
        env = dict(SPECIES=sid(f), LEVEL=60, TARGET=sid(to), HELD=D.ITEMS[what][0], HOUR=12 if meth == 20 else 22)
    if env:
        cases.append(("candy", "candy_%s_%d" % (f, meth), "test_candy.lua", env, 400, True))
ids = list(slot.values())
for i in range(0, len(ids), 6):
    lst = ",".join(map(str, ids[i:i + 6]))
    cases.append(("screens", "party_%02d" % (i // 6), "test_screens.lua", dict(MODE="party", LIST=lst), 400, False))
    cases.append(("screens", "shiny_%02d" % (i // 6), "test_screens.lua", dict(MODE="party", LIST=lst, SHINY=1), 400, False))
for i in range(0, len(ids), 30):
    cases.append(("screens", "pc_%d" % (i // 30), "test_screens.lua",
                  dict(MODE="pc", LIST=",".join(map(str, ids[i:i + 30])), BOX=12), 400, False))
for k, s in slot.items():
    cases.append(("own", "own_" + k, "test_fight2.lua", dict(MODE="own", SPECIES=s), 400, True))
    cases.append(("foe", "foe_" + k, "test_fight2.lua", dict(MODE="foe", SPECIES=s), 400, True))
jobs = []
for tag, rp in ROMS.items():
    for suite, name, lua, env, to, both in cases:
        if tag == "ctl" and not both: continue
        jobs.append(dict(name="%s_%s" % (tag, name), suite=suite, rom=rp, sav=SAV, lua=HERE + lua,
                         env=dict(env, TAG=name), timeout=to))
json.dump(jobs, open(OUTJ, "w"), indent=1)
from collections import Counter
print(len(jobs), "jobs:", dict(Counter(j["suite"] for j in jobs)))
