"""Scenarios for test_journal.lua, and what the Journal must say in each: python make_tests.py

Writes test_journal_cases.lua (flag writes per scenario) and expected.json (the exact message bytes). The
expected bytes come from a Python model of journal.s's selection rule, so a pass means the ROM code and
the model agree byte for byte. Separately from that, the "cut" scenarios pin the model to the table's intent:
for each step k, every earlier step is made done and every later one undone, so the answer must be step k.
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import steps as S
import journal_patch as J

ALLFLAGS = []
for _, st, _ in S.STEPS:
    for f in list(st["flags"]) + [m[0] for m in st.get("members", [])]:
        if f not in ALLFLAGS:
            ALLFLAGS.append(f)


def done(st, on):
    fl = st["flags"]
    if st["mode"] == 1:
        return all(f in on for f in fl)
    if any(f in on for f in fl):
        return True
    if st["mode"] == 2:
        return all(m[0] in on for m in st["members"])
    return False


def model(on):
    """journal.s's rule: last anchor done, then the first step after it that is not done."""
    start = 0
    for i, (_, st, _) in enumerate(S.STEPS):
        if st["anchor"] and done(st, on):
            start = i + 1
    for i in range(start, len(S.STEPS)):
        if not done(S.STEPS[i][1], on):
            return i
    return None


def expected_bytes(i, on):
    if i is None:
        return J.message(*S.FINAL)[:-1]
    header, st, body = S.STEPS[i]
    out = J.message(header, body)[:-1]
    if st["mode"] == 2:
        k = sum(w for f, w, _ in st["members"] if f in on)
        n = sum(w for _, w, _ in st["members"])
        out += b"\xfb" + J.enc(st["label"]) + b"\x00" + J.enc("%d" % k) + b"\xba" + J.enc("%d" % n)
        first = True
        for f, w, t in st["members"]:
            if f in on:
                continue
            out += (b"\xfe" if first else b"\xfa") + J.member(t)[:-1]
            first = False
            if not st["list_all"]:
                break
    return out


def satisfy(st):
    """Flags that make a step done the way play would: every member of a group, the first flag of ANY,
    all of ALL. A group's done_any flags are later events, so they are left alone."""
    if st["mode"] == 2:
        return [m[0] for m in st["members"]]
    if st["mode"] == 1:
        return list(st["flags"])
    return [st["flags"][0]]


cases = []


def case(name, on, want=None):
    on = set(on)
    i = model(on)
    if want is not None:
        assert i == want, "%s: model picks step %s, intent is %s" % (name, i, want)
    cases.append(dict(name=name, set=sorted(on), clear=sorted(set(ALLFLAGS) - on), step=i,
                      bytes=expected_bytes(i, on).hex()))


# 1. one cut per step. Before the Hall of Fame 0x40C3 is set in real play (it hides the Interpol agent),
# so the Hoenn cuts keep it set: the Interpol step must still not count as done.
HOF = next(i for i, (_, st, _) in enumerate(S.STEPS) if st["flags"] == (0x864,))
for k in range(len(S.STEPS) + 1):
    on = set()
    for _, st, _ in S.STEPS[:k]:
        on.update(satisfy(st))
    if k <= HOF:
        on.add(0x40C3)
    case("cut %d" % k, on, want=k if k < len(S.STEPS) else None)

# 2. things done out of order
idx = {st["flags"][0] if st["flags"] else st["members"][0][0]: i for i, (_, st, _) in enumerate(S.STEPS)}
def upto(flag):
    on = set()
    for _, st, _ in S.STEPS[:idx[flag]]:
        on.update(satisfy(st))
    return on

plates_step = next(i for i, (_, st, _) in enumerate(S.STEPS) if st.get("label") == "Plates found:")
gym_step = next(i for i, (_, st, _) in enumerate(S.STEPS) if st.get("label") == "Sinnoh Badges:")
tapu_step = next(i for i, (_, st, _) in enumerate(S.STEPS) if st.get("label", "").startswith("Tapus"))
PLATES = [m[0] for m in S.STEPS[plates_step][1]["members"]]
BADGES = [m[0] for m in S.STEPS[gym_step][1]["members"]]
TAPUS = [m[0] for m in S.STEPS[tapu_step][1]["members"]]

# Giratina battled back in the Hoenn post-game: the Journal still asks for the Sinnoh story first
on = upto(0x42D5) | {0x4081}
case("giratina early, league not done", on, want=idx[0x42D5])
# ... and once the Plates are in, it goes straight to Arceus, skipping the rift and Celestic
on = upto(0x42D5) | {0x42D5, 0x4081} | set(PLATES)
case("giratina early, all plates", on, want=next(i for i, (_, st, _) in enumerate(S.STEPS) if st["flags"] == (0x42FB,)))
# the Dialga/Palkia choice at the Unown Ruins (Hoenn) sets 0x42D8 early; plates still come first
on = upto(0x42D5) | {0x42D5, 0x42D8} | set(PLATES[:5])
case("42D8 early, some plates", on, want=plates_step)
# partial plates: 4 of 17 with the Iron+Dread pair counting two
on = upto(0x42D5) | {0x42D5, 0x4104, 0x4102, 0x4109}
case("plates 4/17", on, want=plates_step)
# gyms in any order
on = upto(0x42D5) - set(BADGES) | {BADGES[5], BADGES[0]}
case("badges 2/8", on, want=gym_step)
# Tapu trials in any order, two done
on = upto(0x41BC) - set(TAPUS) | {TAPUS[0], TAPUS[1]}
case("tapus 2/4", on, want=tapu_step)
# the Mossdeep Plasma flag done early (not an anchor): the Journal must not skip Mt. Pyre and the hideouts
on = upto(0x0D4) | {0x42B6, 0x40C3}
case("plasma early", on, want=idx[0x0D4])
# Lyra set 0x08E0 before Champion Island: the Rainbow Rocket steps still come first
on = upto(0x41D5) | {0x08E0}
case("lyra early", on, want=idx[0x41D5])
# a skipped optional step behind a later anchor is not asked for (Weather Institute skipped, Winona beaten)
on = upto(0x86C) - {0x097} | {0x86C, 0x40C3}
case("institute skipped", on, want=idx[0x0D4])

with open(os.path.join(HERE, "test_journal_cases.lua"), "w", encoding="ascii") as fh:
    fh.write("-- generated by make_tests.py: do not edit\nCASES = {\n")
    for c in cases:
        fh.write('  {name="%s", set={%s}, clear={%s}},\n' % (
            c["name"], ",".join("0x%X" % f for f in c["set"]), ",".join("0x%X" % f for f in c["clear"])))
    fh.write("}\n")
json.dump(cases, open(os.path.join(HERE, "expected.json"), "w"), indent=0)
print("%d cases" % len(cases))
