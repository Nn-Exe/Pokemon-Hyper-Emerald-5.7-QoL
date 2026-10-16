"""Looks at where everything stands (places.py) on the finished maps and says what is wrong, in plain words.

The positions can be edited by hand, so a build has to refuse the ones that would not work in the game:

  * off the map, in a wall, on a door, or two things on one tile at the same time;
  * on water, unless it is water all round (a thing on the water's edge can be faced from the bank, where A
    offers Surf instead of talking, and Surf then puts you on top of it);
  * where nobody can walk up to it;
  * where it closes off ground that could be walked to without it. The four people of the ending did exactly that
    in the Timeless Woods up to test 10 (the user: "those 4 standing blocking the way"; the way in is in
    Mossdeep City since test 16);
  * a tile that carries a door or a sign painted over (the ground can be painted too: ground.py), a way in or
    out that painting has shut off, a tile a script puts you on painted solid;
  * where the game would draw its reflection on dry land: a sprite is mirrored below itself when a reflective
    tile (pond water, ice) lies (width + 8) / 16 - 1 tiles either side of it and (height + 8) / 16 tiles down
    (0x08096A8C), whatever is in between. Koraidon by the lake had its feelers lying on the picnic. The
    reflection is a sprite drawn over the map's bottom layer and under its middle one, so it shows on a tile
    whose picture is on the bottom layer (layer type "covered" or "split": grass is) and is hidden by one whose
    picture is on the middle layer ("normal": a path, a cave's floor). Only the first kind is a problem.

Walking is the game's own rule (walk.lua has the same): a tile's collision bits stop you; height 1 is water (Surf:
got onto and off only at height 3); height 15 keeps the height you had; height 0 (stairs, doors) lets you on from
any height and off to any; otherwise the heights must match. Ledges are not jumped here: what only a ledge
reaches is unknown to this check both with and without our things, so it is never reported.

Ice (behaviour 0x20, the Sealed Vault's floor) is slid on: a step onto it goes on in the same direction until the
next tile cannot be entered (you stop where you are) or you come onto a tile that is not ice (you stop there).
The tiles slid over are not places you can stand. The vault's things come off the map as it is played (a stake
is pulled, and the crystal across its treasure's niche goes with it; a treasure is caught), and every one of
them stops a slide while it is there: check_puzzle() goes through every order of it.
"""
import struct

REFLECTIVE = {0x10, 0x14, 0x16, 0x1A, 0x20, 0x2B}     # pond water, Sootopolis water, puddle, ice, under a bridge
ICE = 0x20                                              # a tile you slide on
SHOWN = 15                                              # objects the game keeps at once, besides the player
SMALL = 4                                               # a closed-off bit of ground smaller than this is not worth a
                                                        # word (a tree's top row behind somebody), unless a door is in it
PALETTES = 6                                            # the kinds of thing (sprite palettes, by tag) that may stand
                                                        # within one screen and its margin at once. The hack has six
                                                        # slots for them; objpal.py gives a slot back once nothing on
                                                        # the map draws with it. The spare it had for a seventh is no
                                                        # good: something of the hack's writes it again (test 19,
                                                        # the user: Walking Wake in another's colours). Before
                                                        # objpal, no slot was given back until the map was left: at
                                                        # most 7 kinds a map (the vault's first build: Ting-Lu in
                                                        # Chi-Yu's colours)
KEPT = 64                                               # people and things a map can have: the save keeps a copy of
                                                        # that many, and the game copies them all without counting
STEPS = ((1, 0), (-1, 0), (0, 1), (0, -1))


class Problems(Exception):
    """What is wrong with the positions: .lines, one finding each."""

    def __init__(self, lines):
        Exception.__init__(self, "\n".join(lines))
        self.lines = lines


def layers(rom, layout, covered=()):
    """mid -> layer type (0 normal: its picture hides a reflection; 1 covered, 2 split: a reflection shows on it),
    for a layout (ROM offset). covered: metatiles the build draws wholly under people (tint.tileset)."""
    u32 = lambda o: struct.unpack_from("<I", rom, o)[0]
    prim, sec = u32(layout + 16) - 0x08000000, u32(layout + 20) - 0x08000000
    pa, sa = u32(prim + 16) - 0x08000000, u32(sec + 16) - 0x08000000
    covered = set(covered)
    return lambda mid: 1 if mid in covered else struct.unpack_from(
        "<H", rom, (pa + 2 * mid) if mid < 512 else (sa + 2 * (mid - 512)))[0] >> 12


def behaviours(rom, layout):
    """mid -> behaviour byte, for a layout (ROM offset): its two tilesets' attribute words."""
    u32 = lambda o: struct.unpack_from("<I", rom, o)[0]
    prim, sec = u32(layout + 16) - 0x08000000, u32(layout + 20) - 0x08000000
    pa, sa = u32(prim + 16) - 0x08000000, u32(sec + 16) - 0x08000000
    return lambda mid: struct.unpack_from("<H", rom, (pa + 2 * mid) if mid < 512 else (sa + 2 * (mid - 512)))[0] & 0xFF


class Ground:
    """A map's tiles as the walker sees them."""

    def __init__(self, blocks, beh, layer=None):
        self.b, self.beh = blocks, beh
        self.layer = layer or (lambda mid: 1)                # (not told: every tile shows a reflection)
        self.h, self.w = len(blocks), len(blocks[0])

    def inside(self, x, y): return 0 <= x < self.w and 0 <= y < self.h
    def solid(self, x, y): return (self.b[y][x] >> 10) & 3 != 0
    def z(self, x, y): return self.b[y][x] >> 12
    def water(self, x, y): return self.inside(x, y) and not self.solid(x, y) and self.z(x, y) == 1
    def floor(self, x, y): return self.inside(x, y) and not self.solid(x, y) and self.z(x, y) != 1
    def reflective(self, x, y): return self.inside(x, y) and self.beh(self.b[y][x] & 0x3FF) in REFLECTIVE
    def shows(self, x, y): return self.inside(x, y) and self.layer(self.b[y][x] & 0x3FF) != 0

    def ice(self, x, y): return self.inside(x, y) and self.beh(self.b[y][x] & 0x3FF) == ICE

    def step(self, x, y, e, dx, dy, blocked, surf):
        """One step from (x, y) at height e: (x, y, height) where it ends, or None if it cannot be taken."""
        nx, ny = x + dx, y + dy
        if not self.inside(nx, ny) or self.solid(nx, ny) or (nx, ny) in blocked:
            return None
        z = self.z(nx, ny)
        if z == 1:                                           # onto water: surfing already, or from height 3
            return (nx, ny, 1) if surf and e in (0, 1, 3) else None
        if e == 1:                                           # off the water: only onto height 3 (or a 0 / 15 tile)
            return (nx, ny, 3 if z == 15 else z) if z in (0, 3, 15) else None
        if z == 15:
            return (nx, ny, e)
        if z == 0 or e in (0, 15) or z == e:
            return (nx, ny, z)
        return None

    def go(self, x, y, e, dx, dy, blocked, surf):
        """Where pressing a direction leaves you: a step, and on ice as many more as can be taken."""
        at = self.step(x, y, e, dx, dy, blocked, surf)
        while at and self.ice(at[0], at[1]):
            more = self.step(at[0], at[1], at[2], dx, dy, blocked, surf)
            if more is None:
                break
            at = more
        return at

    def stand(self, x, y, blocked=(), surf=False):
        """The height you stand at on (x, y) when you are put there (a door), or None if you cannot be."""
        if not self.inside(x, y) or self.solid(x, y) or (x, y) in blocked or (not surf and self.z(x, y) == 1):
            return None
        z = self.z(x, y)
        return 0 if z in (0, 15) else z

    def reach(self, starts, blocked, surf):
        """{(x, y): heights you can stand there at} from the start tiles, round the blocked ones."""
        seen = {}
        todo = [(x, y, self.stand(x, y, blocked, surf)) for x, y in starts]
        todo = [t for t in todo if t[2] is not None]
        while todo:
            x, y, e = todo.pop()
            if e in seen.setdefault((x, y), set()):
                continue
            seen[x, y].add(e)
            for dx, dy in STEPS:
                at = self.go(x, y, e, dx, dy, blocked, surf)
                if at:
                    todo.append(at)
        return seen


def tiles(xy):
    return "%d,%d" % xy


def check_map(m):
    """Problems of one map. m: title, blocks, beh, starts [(x, y)], doors {(x, y)}, things [{name, xy, size, when,
    top}], fixed [{name, xy, when, open}] (not ours to move: in the way like the things, or, if open, a tile that
    has to stay free)."""
    g = Ground(m["blocks"], m["beh"], m.get("layer"))
    title = m["title"]
    out = []
    things = m["things"]
    # a tile that carries a door or a sign was painted over
    base = m.get("base")
    for (x, y), why in sorted((m.get("locked") or {}).items()):
        if base and g.inside(x, y) and m["blocks"][y][x] != base[y][x]:
            out.append("%s: the tile at %d,%d was painted over, but it is %s. That tile has to stay as it was: "
                       "paint the old one back there (Undo), or leave it alone." % (title, x, y, why))
    # a tile that has to stay free ground (where a script puts you) is no longer ground
    for f in m["fixed"]:
        x, y = f["xy"]
        if f.get("open") and g.inside(x, y) and not g.floor(x, y):
            out.append("%s: the tile at %d,%d has to stay ground you can stand on: it is %s." % (
                title, x, y, f["name"]))
    if out:                                                  # (first things first: with a door gone nothing below
        return out                                           # can be reached, and every thing would say so)
    for phase, when in (("story", "during the story"), ("after", "after the story"), ("finale", "in the finale"),
                        ("ending", "in the ending")):
        colours(g, [t for t in things if phase in t["when"] and t.get("tag") is not None], title, when, out)
    if m.get("objects", 0) > KEPT:
        out.append("%s has %d people and things on it. The game can keep %d on one map: take %d away (crystals "
                   "are the easiest)." % (title, m["objects"], KEPT, m["objects"] - KEPT))
    ok = []                                                  # the things that stand on a tile at all
    for t in things:
        x, y = t["xy"]
        who = "%s (%s) at %s" % (t["name"], title, tiles(t["xy"]))
        if not g.inside(x, y):
            out.append("%s is off the map, which is %d tiles wide and %d tall (x 0-%d, y 0-%d)." % (
                who, g.w, g.h, g.w - 1, g.h - 1))
            continue
        if (x, y) in m["doors"]:
            out.append("%s stands in a doorway." % who)
            continue
        if g.solid(x, y):
            if not t.get("top"):
                out.append("%s is inside something solid (a wall, a rock, a tree, a counter)." % who)
                continue
        elif g.water(x, y):
            if not all(g.water(x + dx, y + dy) for dx, dy in STEPS):
                out.append("%s is on water beside a bank. On water it must have water on all four sides, or A "
                           "from the bank offers Surf instead of talking to it." % who)
                continue
        ok.append(t)
    # two on one tile
    every = [(t["name"], t["xy"], t["when"], True) for t in ok]
    every += [(f["name"], f["xy"], f["when"], not f.get("open")) for f in m["fixed"]]
    seen = {}
    for name, xy, when, there in every:
        for other, owhen in seen.get(xy, []):
            if when & owhen:
                out.append("%s and %s (%s) are both at %s." % (name, other, title, tiles(xy)))
        seen.setdefault(xy, []).append((name, when))
    # a reflection on dry land
    for t in ok:
        x, y = t["xy"]
        if g.water(x, y):
            continue
        w, h = t["size"]
        side, down = (w + 8) // 16 - 1, (h + 8) // 16
        under = [(x + dx, y + dy) for dx in range(-side, side + 1) for dy in range(1, down + 1)]
        # Water's reflection is the problem, where it would lie on ground that shows it. Ice is let be: a room of
        # ice has its floor on the layer that hides a reflection and its boulders drawn over one, and the game's
        # own (the Snowpoint Temple, Regigigas on its island) stand things beside ice the same way.
        water = [c for c in under if g.reflective(*c) and not g.ice(*c)]
        dry = [c for c in under if not g.reflective(*c) and g.shows(*c)]
        if water and dry:
            near = "directly below it" if side == 0 else "within %d tile%s either side of it" % (side, "s" * (side > 1))
            out.append("%s (%s) at %s is too close to water: the game draws a sprite's reflection under it when "
                       "pond water lies %s and up to %d tiles down, and the reflection shows on the ground. Move "
                       "it further from the water." % (t["name"], title, tiles(t["xy"]), near, down))
    if m.get("puzzle"):                                      # its things come and go as it is played
        crowded(g, {t["xy"] for t in ok} | {f["xy"] for f in m["fixed"] if not f.get("open")}, title, "", out)
        check_puzzle(m, g, ok, out)
        return out
    # in the way, and out of reach: once for the story, once for afterwards
    met = set()
    lost_said = set()
    beside = lambda d, where: d in where or any((d[0] + dx, d[1] + dy) in where for dx, dy in STEPS)
    shut = set()
    for phase in ("story", "after"):
        # What is not ours to move stands there already: what it shuts off is meant so (the cavern's crystals) or
        # is the game's own business (Mossdeep City's people, some of whom stand across a path until an event
        # takes them away). Only what our things shut off besides is said.
        theirs = {f["xy"] for f in m["fixed"] if not f.get("open") and phase in f["when"]}
        # the ways in and out that could be reached on the map as it was drawn (with Surf): painting must not shut one
        drawn = Ground(base, m["beh"]).reach(m["starts"][:1], theirs, True) if base else {}
        block = {xy for name, xy, when, there in every if there and phase in when}
        byname = {}
        for name, xy, when, there in every:
            if there and phase in when:
                byname.setdefault(xy, name)
        crowded(g, block, title, "" if phase == "story" else " after the story", out)
        for surf, how in ((False, "on foot"), (True, "even with Surf")):
            free = g.reach(m["starts"][:1], theirs, surf)    # from the way in: the other doors must stay in reach
            got = g.reach(m["starts"][:1], block, surf)
            lost = {xy for xy in free if xy not in got and xy not in block and xy not in lost_said}
            while lost:                                      # one finding per closed-off patch of ground
                patch, todo = set(), [min(lost)]
                while todo:
                    c = todo.pop()
                    if c in patch or c not in lost:
                        continue
                    patch.add(c)
                    todo += [(c[0] + dx, c[1] + dy) for dx, dy in STEPS]
                lost -= patch
                lost_said |= patch
                if len(patch) < SMALL and not patch & m["doors"]:
                    continue
                # in the way: what stands between the closed-off ground and the ground still in reach
                between = {(x + dx, y + dy) for x, y in patch for dx, dy in STEPS if (x + dx, y + dy) in byname}
                edge = sorted({byname[x, y] for x, y in between
                               if any((x + dx, y + dy) in got for dx, dy in STEPS)} or
                              {byname[xy] for xy in between})
                out.append("%s: the ground at %s (%d tile%s) can no longer be reached %s%s. In the way: %s." % (
                    title, tiles(min(patch)), len(patch), "s" * (len(patch) > 1), how,
                    "" if phase == "story" else " after the story", ", ".join(edge) or "something further off"))
            if surf:
                gone = [d for d in sorted(m["doors"]) if beside(d, drawn) and not beside(d, got) and d not in shut]
                shut |= set(gone)
                if gone:
                    out.append("%s: the way%s in or out at %s can no longer be reached from where you come into "
                               "this map%s. Something painted, or something standing there, is in the way." % (
                                   title, "s" * (len(gone) > 1), " and ".join(tiles(d) for d in gone),
                                   "" if phase == "story" else " after the story"))
            for t in ok:
                if phase not in t["when"] or id(t) in met:
                    continue
                x, y = t["xy"]
                zt = None if g.solid(x, y) else g.z(x, y)
                for dx, dy in STEPS:
                    hs = got.get((x + dx, y + dy))
                    if hs and (zt in (None, 0, 15) or zt in hs or hs & {0, 15}):
                        met.add(id(t))
                        break
    alone = []
    for t in ok:
        x, y = t["xy"]
        shut_in = any((x + dx, y + dy) in lost_said for dx, dy in STEPS)      # (said already, as closed off)
        if t["when"] & {"story", "after"} and id(t) not in met and not shut_in:
            alone.append(t)
    if len(alone) > 3:                                       # a whole part of the map: one finding, not thirty
        out.append("%s: %s and %d more cannot be walked up to. The ground they stand on can no longer be reached "
                   "from where you come into this map: has painting closed a way through?" % (
                       title, ", ".join("%s at %s" % (t["name"], tiles(t["xy"])) for t in alone[:2]),
                       len(alone) - 2))
    else:
        for t in alone:
            out.append("%s (%s) at %s cannot be walked up to: no tile beside it can be reached at its height." % (
                t["name"], title, tiles(t["xy"])))
    return out


def colours(g, things, title, when, out):
    """More kinds of thing in sight than there are sprite palettes: whatever stands within one screen and its
    margin of you (as crowded(), below) has its sprite and its palette at once; PALETTES slots between them."""
    worst = None
    for py in range(g.h):
        for px in range(g.w):
            kinds = {}
            for t in things:
                bx, by = t["xy"]
                if px - 9 <= bx <= px + 10 and py - 7 <= by <= py + 9:
                    kinds.setdefault(t["tag"], t["name"])
            if len(kinds) > PALETTES and (worst is None or len(kinds) > len(worst[0])):
                worst = (kinds, (px, py))
    if worst:
        out.append("%s: %d kinds of thing stand within one screen of %s %s (%s). The game has %d sets of colours "
                   "for the people and things in sight at once; with more, one of them shows in another's colours. "
                   "Move one kind further away from the others, or take it away." % (
                       title, len(worst[0]), tiles(worst[1]), when, ", ".join(sorted(worst[0].values())), PALETTES))


def crowded(g, block, title, when, out):
    """More than the game can show: it keeps 16 people and things at once, you among them, and puts on the map
    whatever stands 9 tiles left to 10 right of you and 7 up to 9 down (TrySpawnObjectEvents)."""
    worst = max(((sum(1 for bx, by in block if px - 9 <= bx <= px + 10 and py - 7 <= by <= py + 9), (px, py))
                 for py in range(g.h) for px in range(g.w)), default=(0, None))
    if worst[0] > SHOWN:
        out.append("%s: %d things stand within one screen of %s%s. The game shows %d at once besides you; the "
                   "rest would not appear. Move some further apart or take some away (crystals are the easiest)."
                   % (title, worst[0], tiles(worst[1]), when, SHOWN))


def puzzle_parts(m, ok):
    """The Sealed Vault's treasures as the puzzle sees them: ([(stake, crystal, Pokemon)] as things, the tiles of
    everything else that stands there), or None if one of them is not on a tile it can stand on (said already)."""
    by_id = {t["id"]: t for t in ok if t.get("k") is None}
    sets = [tuple(by_id.get(tid) for tid in ids) for ids in m["puzzle"]]
    if any(t is None for st in sets for t in st):
        return None
    theirs = {id(t) for st in sets for t in st}
    rest = {t["xy"] for t in ok if id(t) not in theirs} | {f["xy"] for f in m["fixed"] if not f.get("open")}
    return sets, rest


def puzzle_states(m, g, sets, rest, treasures=None):
    """Every state the puzzle can be in, played from the way in: {state: [states one move on]}, a state being
    (x, y, height, stakes standing, treasures in their niches), the last two as bits. A move is a press of a
    direction (a step, or a slide), a stake pulled from beside it (its crystal goes too) or a treasure caught
    from beside it; after either of the last two you slide on if you stand on ice (on(), below). treasures: the
    bits to start with (None: every combination, for a save from an older build in which some were caught where
    they stood before)."""
    n = len(sets)
    stakes, seals, mons = ([st[k]["xy"] for st in sets] for k in range(3))
    full = (1 << n) - 1
    beside = lambda p, q: abs(p[0] - q[0]) + abs(p[1] - q[1]) == 1
    door = m["starts"][0]
    e0 = g.stand(*door)

    def on(x, y, e, thing, there):
        """Where you are once the thing you faced is gone. On ice the game goes on trying to slide you the way you
        face for as long as you stand there, and only the thing was stopping it: you slide on over its tile (seen
        in the game on the vault's first build: a stake pulled from 3,12 left you at 3,9)."""
        if not g.ice(x, y):
            return (x, y, e)
        return g.go(x, y, e, thing[0] - x, thing[1] - y, there, False) or (x, y, e)
    edges = {}
    todo = [(door[0], door[1], e0, full, lm) for lm in (range(full + 1) if treasures is None else [treasures])]
    while todo:
        st = todo.pop()
        if st in edges:
            continue
        x, y, e, sm, lm = st
        there = set(rest)
        for k in range(n):
            if sm >> k & 1:
                there |= {stakes[k], seals[k]}
            if lm >> k & 1:
                there.add(mons[k])
        nxt = []
        for dx, dy in STEPS:
            at = g.go(x, y, e, dx, dy, there, False)
            if at:
                nxt.append((at[0], at[1], at[2], sm, lm))
        for k in range(n):
            if sm >> k & 1 and beside((x, y), stakes[k]):
                nxt.append(on(x, y, e, stakes[k], there - {stakes[k], seals[k]}) + (sm & ~(1 << k), lm))
            if lm >> k & 1 and beside((x, y), mons[k]):
                nxt.append(on(x, y, e, mons[k], there - {mons[k]}) + (sm, lm & ~(1 << k)))
        edges[st] = nxt
        todo += nxt
    return edges


def check_puzzle(m, g, ok, out):
    """The Sealed Vault. From the way in, in whatever order things are done: every stake can still be pulled,
    the way out can always be come back to, a crystal closes its niche until its stake is pulled and the
    treasure can be walked up to after that; everything else that stands there can be walked up to."""
    title = m["title"]
    parts = puzzle_parts(m, ok)
    if parts is None or g.stand(*m["starts"][0]) is None:
        return
    sets, rest = parts
    n = len(sets)
    stakes, seals, mons = ([st[k] for st in sets] for k in range(3))
    full = (1 << n) - 1
    beside = lambda p, q: abs(p[0] - q[0]) + abs(p[1] - q[1]) == 1
    edges = puzzle_states(m, g, sets, rest)
    back = {}                                                # (not through a catch: a treasure may never be caught)
    for a, nxt in edges.items():
        for b in nxt:
            if b[4] == a[4]:
                back.setdefault(b, []).append(a)

    def from_which(goal):                                    # the states the goal states can be come to from
        seen, todo = set(goal), list(goal)
        while todo:
            for a in back.get(todo.pop(), ()):
                if a not in seen:
                    seen.add(a); todo.append(a)
        return seen
    door = m["starts"][0]
    pulled = lambda sm: ", ".join(stakes[k]["name"] for k in range(n) if not sm >> k & 1) or "none"
    # a place to get stuck: the way out cannot be come back to (with the same things standing: nothing more to pull
    # may be what is left)
    home = from_which([st for st in edges if st[:2] == door])
    stuck = sorted((st for st in edges if st not in home), key=lambda st: (bin(st[3]).count("1"), st))
    if stuck:
        st = stuck[-1]
        out.append("%s: you could get stuck. From %s there is no way back to the way out at %s: every slide from "
                   "there ends where no slide leads back (stakes pulled by then: %s). Put a boulder or a patch of "
                   "snow where it stops a slide that leads back." % (title, tiles(st[:2]), tiles(door), pulled(st[3])))
    # a stake that can never be pulled, or not any more once others are
    never = [k for k in range(n) if all(st[3] >> k & 1 for st in edges)]
    for k in never:
        out.append("%s: %s at %s can never be pulled: there is no way to come to a stop on a tile beside it." % (
            title, stakes[k]["name"], tiles(stakes[k]["xy"])))
    if not never:
        done = from_which([st for st in edges if st[3] == 0])
        late = sorted((st for st in edges if st not in done), key=lambda st: (-bin(st[3]).count("1"), st))
        if late:
            st = late[0]
            left = ", ".join(stakes[k]["name"] for k in range(n) if st[3] >> k & 1)
            out.append("%s: the stakes can be pulled in an order that leaves one out of reach for good. Once these "
                       "are pulled: %s, there is no way left to stop beside: %s." % (title, pulled(st[3]), left))
    for k in range(n):
        name, xy = mons[k]["name"], mons[k]["xy"]
        if any(st[3] >> k & 1 and st[4] >> k & 1 and beside(st[:2], xy) for st in edges):
            out.append("%s: %s at %s can be walked up to while %s still stands. The crystal has to close the way "
                       "to it." % (title, name, tiles(xy), seals[k]["name"]))
        elif k not in never and not any(not st[3] >> k & 1 and beside(st[:2], xy) for st in edges):
            out.append("%s: %s at %s cannot be walked up to even when %s is gone." % (
                title, name, tiles(xy), seals[k]["name"]))
    theirs = {id(t) for st in sets for t in st}
    for t in ok:
        if id(t) not in theirs and not any(beside(st[:2], t["xy"]) for st in edges):
            out.append("%s (%s) at %s cannot be walked up to: no tile beside it can be come to a stop on." % (
                t["name"], title, tiles(t["xy"])))
    for t in seals:
        if not any(beside(st[:2], t["xy"]) for st in edges):
            out.append("%s (%s) at %s cannot be walked up to." % (t["name"], title, tiles(t["xy"])))


def puzzle_way(m):
    """The shortest way through the Sealed Vault's puzzle as it is built: (slides, moves), a move being "U", "D",
    "L", "R" (a press of that direction: a step along floor counts for nothing, anything on ice for one) or
    ("pull", name of the stake). None if it cannot be done. For the READ ME, the editor and the tests."""
    from collections import deque
    g = Ground(m["blocks"], m["beh"])
    ok = [t for t in m["things"] if g.inside(*t["xy"])]
    parts = puzzle_parts(m, ok)
    if parts is None or g.stand(*m["starts"][0]) is None:
        return None
    sets, rest = parts
    n = len(sets)
    full = (1 << n) - 1
    edges = puzzle_states(m, g, sets, rest, full)
    start = (m["starts"][0][0], m["starts"][0][1], g.stand(*m["starts"][0]), full, full)
    names = {(0, -1): "U", (0, 1): "D", (-1, 0): "L", (1, 0): "R"}
    dist, prev, q = {start: 0}, {}, deque([start])
    while q:
        a = q.popleft()
        for b in edges[a]:
            if b[4] != a[4]:                                 # (catching is not part of the way through)
                continue
            if b[3] != a[3]:
                cost, how = 0, ("pull", sets[[k for k in range(n) if (a[3] ^ b[3]) >> k & 1][0]][0]["name"])
            else:
                d = (b[0] - a[0], b[1] - a[1])
                step = abs(d[0]) + abs(d[1])
                how = names[d[0] // step, d[1] // step]
                cost = 0 if step == 1 and not g.ice(a[0], a[1]) and not g.ice(b[0], b[1]) else 1
            if b not in dist or dist[a] + cost < dist[b]:
                dist[b], prev[b] = dist[a] + cost, (a, how)
                (q.appendleft if cost == 0 else q.append)(b)
    ends = [st for st in dist if st[3] == 0]
    if not ends:
        return None
    st = min(ends, key=dist.get)
    total, moves = dist[st], []
    while st in prev:
        st, how = prev[st]
        moves.append(how)
    return total, moves[::-1]


# maps that share their ground and most of what stands on it: their titles, and what to call them together
SHARED = ((("the crater in the past", "the crater in the future"), "the crater, both times"),
          (tuple("Research Station No. %d" % k for k in range(1, 5)), "the research stations"))


def merged(lines):
    """One line where every map of a set says the same thing (the two craters, the four stations)."""
    for titles, together in SHARED:
        said = {}                                            # the line without its title -> where it was said
        for i, line in enumerate(lines):
            for t in titles:
                if t in line:
                    said.setdefault(line.replace(t, "\0"), []).append(i)
        drop = set()
        for key, where in said.items():
            if len(where) == len(titles):
                lines[where[0]] = key.replace("\0", together)
                drop |= set(where[1:])
        lines = [line for i, line in enumerate(lines) if i not in drop]
    return lines


def check(maps):
    """Raises Problems if anything is wrong on any map."""
    lines = []
    for m in maps:
        lines += check_map(m)
    if lines:
        raise Problems(merged(lines))
