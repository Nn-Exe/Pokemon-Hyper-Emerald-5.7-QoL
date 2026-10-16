"""The search that found the Sealed Vault's puzzle (world.VAULT_ROCKS / VAULT_PATCHES, the stakes in places.py).
python -I vault_search.py search <seconds> [seed]     writes every usable layout to vault_layouts_<seed>.jsonl
python -I vault_search.py rank [files...]             prints the ten that play best, with their solutions

The room (17 x 18): a dais along the top (y 5), the mirror floor (x 2-14, y 6-14) and a strip of floor along the
bottom (y 15) with the door at 8,15. You slide on the floor until something stops you: a boulder, a stake or a
wall (you stop before it), a patch of snow or the floor (you stop on it). A stake is pulled from a tile beside
it, and then you slide on over where it stood (the game keeps trying to slide you while you stand on ice).

A layout is thrown together (three stakes, each with a boulder somewhere above and below it in its column so that
no straight slide from the dais or the strip runs into it, and a few more boulders and patches) and kept if: the
door's column is clear, no place traps you, every stake can still be pulled whatever was pulled before, and the
shortest way takes 11 to 20 slides. `rank` then plays every order of the three stakes and prefers layouts in
which no stake falls in a slide or two, each takes some doing, and the order matters.

This is a tool, not part of the build: check.py plays the built map through by the same rules (check_puzzle) and
is what a build has to pass.
"""
import glob, itertools, json, random, sys, time
from collections import deque

W, H = 17, 18
X0, X1, Y0, Y1 = 2, 14, 6, 14            # the field
DAIS, STRIP, DOOR = 5, 15, (8, 15)
NICHES = (2, 5, 11, 14)                   # the niche columns that hold something to walk up to (8 is the tablet's)
DIRS = ((0, -1), (0, 1), (-1, 0), (1, 0))


def cells(rocks, patches):
    """'i' ice, '.' floor you stop on, '#' solid, for every tile."""
    g = [["#"] * W for _ in range(H)]
    for x in range(X0, X1 + 1):
        g[DAIS][x] = "."
        g[STRIP][x] = "."
        for y in range(Y0, Y1 + 1):
            g[y][x] = "i"
    for x in (2, 5, 8, 11, 14):           # the niches: floor up to the back wall (their dwellers are not here)
        for y in (3, 4):
            g[y][x] = "."
    for x, y in rocks:
        g[y][x] = "#"
    for x, y in patches:
        g[y][x] = "."
    return g


def slide(g, p, d, there):
    x, y = p
    nx, ny = x + d[0], y + d[1]
    if g[ny][nx] == "#" or (nx, ny) in there:
        return p
    x, y = nx, ny
    while g[y][x] == "i":
        nx, ny = x + d[0], y + d[1]
        if g[ny][nx] == "#" or (nx, ny) in there:
            break
        x, y = nx, ny
    return (x, y)


def pulled(g, p, stake, there):
    """Where you are once the stake you faced is gone: on ice you slide on over its tile (the game does)."""
    if g[p[1]][p[0]] != "i":
        return p
    return slide(g, p, (stake[0] - p[0], stake[1] - p[1]), there)


def solve(g, stakes, seals=()):
    """Everything about the puzzle: None if it breaks a rule, else (slides to pull all three, the order, the
    slides to each first pull, how many stakes cannot be reached while another stands)."""
    n = len(stakes)
    full = (1 << n) - 1
    start = (DOOR, full)
    dist = {start: 0}
    prev = {}
    q = deque([start])
    while q:
        s = q.popleft()
        p, mask = s
        there = {stakes[k] for k in range(n) if mask >> k & 1} | {seals[k] for k in range(len(seals)) if mask >> k & 1}
        for d in DIRS:
            t = (slide(g, p, d, there), mask)
            if t[0] == p:
                continue
            c = 0 if g[p[1]][p[0]] == "." and g[t[0][1]][t[0][0]] == "." and abs(t[0][0] - p[0]) + abs(t[0][1] - p[1]) == 1 else 1
            if t not in dist or dist[s] + c < dist[t]:
                dist[t] = dist[s] + c; prev[t] = (s, d)
                (q.appendleft if c == 0 else q.append)(t)
        for k in range(n):
            if mask >> k & 1 and abs(stakes[k][0] - p[0]) + abs(stakes[k][1] - p[1]) == 1:
                t = (pulled(g, p, stakes[k], there - {stakes[k]}), mask & ~(1 << k))
                if t not in dist or dist[s] < dist[t]:
                    dist[t] = dist[s]; prev[t] = (s, ("pull", k)); q.appendleft(t)
    done = [s for s in dist if s[1] == 0]
    if not done:
        return None
    # no trap: from every state the door can be come back to with the same stakes standing, and every state can
    # still finish (reverse searches over the states reached)
    back = {}
    for s in dist:
        p, mask = s
        there = {stakes[k] for k in range(n) if mask >> k & 1} | {seals[k] for k in range(len(seals)) if mask >> k & 1}
        for d in DIRS:
            t = (slide(g, p, d, there), mask)
            if t[0] != p:
                back.setdefault(t, []).append(s)
    pulls_back = {}
    for s in dist:
        p, mask = s
        there = {stakes[k] for k in range(n) if mask >> k & 1} | {seals[k] for k in range(len(seals)) if mask >> k & 1}
        for k in range(n):
            if mask >> k & 1 and abs(stakes[k][0] - p[0]) + abs(stakes[k][1] - p[1]) == 1:
                pulls_back.setdefault((pulled(g, p, stakes[k], there - {stakes[k]}), mask & ~(1 << k)), []).append(s)
    home = {s for s in dist if s[0] == DOOR}
    todo = list(home)
    while todo:
        for s0 in back.get(todo.pop(), ()):
            if s0 not in home:
                home.add(s0); todo.append(s0)
    if len(home) != len(dist):
        return None
    fin = set(done)
    todo = list(fin)
    while todo:
        t = todo.pop()
        for s0 in back.get(t, []) + pulls_back.get(t, []):
            if s0 not in fin:
                fin.add(s0); todo.append(s0)
    if len(fin) != len(dist):
        return None
    best = min(done, key=dist.get)
    path = []
    s = best
    while s in prev:
        s0, how = prev[s]
        path.append(how); s = s0
    path.reverse()
    pulls = [h[1] for h in path if h[0] == "pull"]
    # the slides to each stake on its own, with all three standing
    alone = []
    for k in range(n):
        ds = [dist[s] for s in dist if s[1] == full and abs(stakes[k][0] - s[0][0]) + abs(stakes[k][1] - s[0][1]) == 1]
        alone.append(min(ds) if ds else None)
    return dist[best], pulls, alone, sum(1 for a in alone if a is None), path


def straight_hits(g, stakes):
    """Stakes that a single straight slide from the dais or the bottom strip runs into."""
    there = set(stakes)
    n = 0
    for x in range(X0, X1 + 1):
        for y, d in ((DAIS, (0, 1)), (STRIP, (0, -1))):
            p = slide(g, (x, y), d, there)
            if any(abs(s[0] - p[0]) + abs(s[1] - p[1]) == 1 for s in stakes) and p[1] not in (DAIS, STRIP):
                n += 1
    return n


def make(rng, n_rocks, n_patches):
    field = [(x, y) for x in range(X0, X1 + 1) for y in range(Y0, Y1 + 1) if x != 8]
    stakes, taken = [], set()
    tries = 0
    while len(stakes) < 3 and tries < 60:
        tries += 1
        x, y = rng.choice(field)
        if not (Y0 + 2 <= y <= Y1 - 3):                 # ice below it for its reflection, a rock below that
            continue
        if any(abs(x - sx) <= 1 and abs(y - sy) <= 3 or (x, y) in taken for sx, sy in stakes):
            continue
        up = [(x, yy) for yy in range(Y0, y - 1)]       # (the tile above a stake stays clear: its head is there)
        dn = [(x, yy) for yy in range(y + 3, Y1 + 1)]
        if not up or not dn:
            continue
        stakes.append((x, y))
        taken |= {(x, y), (x, y - 1), (x, y + 1), (x, y + 2)}
    if len(stakes) < 3:
        return None
    rocks, patches = [], []
    for x, y in stakes:
        for line in ([(x, yy) for yy in range(Y0, y - 1)], [(x, yy) for yy in range(y + 3, Y1 + 1)]):
            line = [c for c in line if c not in taken]
            if not line:
                return None
            c = rng.choice(line)
            (patches if rng.random() < 0.15 and c[1] not in (y - 1,) else rocks).append(c); taken.add(c)
    free = [c for c in field if c not in taken]
    rng.shuffle(free)
    for c in free[:max(0, n_rocks - len(rocks))]:
        rocks.append(c); taken.add(c)
    free = [c for c in free if c not in taken]
    for c in free[:n_patches]:
        patches.append(c)
    return rocks, patches, stakes


def score(rocks, patches, stakes):
    g = cells(rocks, patches)
    # the door's column is clear: straight up to the dais and straight back
    if slide(g, DOOR, (0, -1), set(stakes)) != (8, DAIS) or slide(g, (8, DAIS), (0, 1), set(stakes)) != DOOR:
        return None
    if straight_hits(g, stakes):
        return None
    r = solve(g, stakes)
    if r is None:
        return None
    total, pulls, alone, hidden, path = r
    if not (11 <= total <= 20):
        return None
    firsts = sorted(a for a in alone if a is not None)
    if not firsts or firsts[0] < 2:
        return None
    return (hidden >= 1) * 6 + total + min(firsts) - 0.8 * len(rocks) - 0.5 * len(patches), r


def show(rocks, patches, stakes):
    g = cells(rocks, patches)
    out = []
    for y in range(H):
        row = ""
        for x in range(W):
            c = g[y][x]
            if (x, y) in stakes:
                c = "ABC"[stakes.index((x, y))]
            elif (x, y) in rocks:
                c = "o"
            elif (x, y) in patches:
                c = "+"
            elif (x, y) == DOOR:
                c = "D"
            row += c
        out.append(row)
    return "\n".join(out)


def stages(g, stakes):
    """For every order the stakes can be pulled in: the slides before each pull (from the door, then from where
    the pull before left you). {order: [d1, d2, d3]}, shortest way for each order."""
    n = len(stakes)
    out = {}

    def reach(start, mask):
        there = {stakes[k] for k in range(n) if mask >> k & 1}
        dist, q = {start: 0}, deque([start])
        while q:
            p = q.popleft()
            for d in DIRS:
                t = slide(g, p, d, there)
                if t == p:
                    continue
                c = 0 if g[p[1]][p[0]] == "." and g[t[1]][t[0]] == "." and abs(t[0] - p[0]) + abs(t[1] - p[1]) == 1 else 1
                if t not in dist or dist[p] + c < dist[t]:
                    dist[t] = dist[p] + c
                    (q.appendleft if c == 0 else q.append)(t)
        return dist, there
    for order in itertools.permutations(range(n)):
        # dynamic programme over (position after the pull): keep every landing place with its cost so far
        front = {DOOR: (0, [])}
        mask = (1 << n) - 1
        ok = True
        for k in order:
            nxt = {}
            for start, (cost, ds) in front.items():
                dist, there = reach(start, mask)
                for p, d in dist.items():
                    if abs(stakes[k][0] - p[0]) + abs(stakes[k][1] - p[1]) == 1:
                        land = pulled(g, p, stakes[k], there - {stakes[k]})
                        if land not in nxt or cost + d < nxt[land][0]:
                            nxt[land] = (cost + d, ds + [d])
            if not nxt:
                ok = False
                break
            front = nxt
            mask &= ~(1 << k)
        if ok:
            best = min(front.values(), key=lambda v: v[0])
            out[order] = best[1]
    return out




def search(budget, seed):
    rng = random.Random(seed)
    t0, tried, ok = time.time(), 0, 0
    with open("vault_layouts_%d.jsonl" % seed, "w") as out:
        while time.time() - t0 < budget:
            tried += 1
            m = make(rng, rng.randint(8, 13), rng.randint(0, 2))
            if m is None:
                continue
            s = score(*m)
            if s is None:
                continue
            ok += 1
            out.write(json.dumps({"rocks": m[0], "patches": m[1], "stakes": m[2]}) + chr(10))
            out.flush()
    print("seed %d: tried %d, usable %d" % (seed, tried, ok))


def rank(files):
    rows = []
    for f in files:
        for line in open(f):
            c = json.loads(line)
            m = tuple([tuple(x) for x in c[k]] for k in ("rocks", "patches", "stakes"))
            st = stages(cells(m[0], m[1]), m[2])
            if st:
                best = min(st, key=lambda o: sum(st[o]))
                rows.append({"m": m, "st": st, "best": best, "ds": st[best], "total": sum(st[best]),
                             "first": min(v[0] for v in st.values())})

    def worth(r):
        return (min(r["first"], 5) * 3 + min(min(r["ds"]), 4) * 3 + min(r["total"], 16)
                + (4 if len(r["st"]) <= 2 else 2 if len(r["st"]) <= 3 else 0)
                - max(0, len(r["m"][0]) - 10) - 0.5 * len(r["m"][1]))
    rows.sort(key=worth, reverse=True)
    print("%d layouts" % len(rows))
    for r in rows[:10]:
        print()
        print("worth %.1f | orders that work %d | best order %s, slides before each pull %s, %d in all | boulders %d "
              "patches %d" % (worth(r), len(r["st"]), "".join("ABC"[k] for k in r["best"]), r["ds"], r["total"],
                              len(r["m"][0]), len(r["m"][1])))
        print("  every order:", {"".join("ABC"[k] for k in o): v for o, v in r["st"].items()})
        print("  boulders %s patches %s stakes %s" % (sorted(r["m"][0]), sorted(r["m"][1]), r["m"][2]))
        print(show(*r["m"]))


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "search":
        search(float(sys.argv[2]), int(sys.argv[3]) if len(sys.argv) > 3 else 1)
    elif len(sys.argv) > 1 and sys.argv[1] == "rank":
        rank(sys.argv[2:] or glob.glob("vault_layouts_*.jsonl"))
    else:
        print(__doc__.split(chr(10) + chr(10))[0])
