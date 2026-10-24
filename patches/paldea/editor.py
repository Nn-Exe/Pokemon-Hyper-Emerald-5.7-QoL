"""The Area Zero editor: move its people, Pokemon and crystals, and paint its ground, with the mouse.
python -I editor.py [folder] [--here] [--no-browser]
       (the folder: gba-trans/hyper-emerald/roms/test-paldea unless named; --here: as rebuild.py's; --no-browser: only serve)

The user, on test 10: "actually can I edit the placement myself???", and on test 11: "apart from placement, can I
change tiles layout everything myself? like Hex app. I cannot use Hex app" (Hex Maniac Advance does not open this
ROM). placements.txt (places.py) and ground.txt (ground.py) are the answer in text; this is both files with a
mouse. It serves one page to the browser on this PC only (127.0.0.1): every map drawn from its tiles as the game
draws it, everything of placements.txt on it as its own sprite.

  Move things       drag a person, a Pokemon, a crystal or an item, or pick it and use the arrow keys.
  Tidy the edges    (the crater) puts the piece that fits on every terrace corner, path border and puddle rim
                    of what is painted: tidy.py.
  Paint the ground  left-click or drag paints with the brush; right-click picks the tile under the mouse as the
                    brush, right-drag a whole area (a tree, a house), as Hex Maniac Advance does; Shift and drag
                    fills a box; Ctrl+Z takes a stroke back. The brush is a tile from the map (with the map's own
                    "can you walk here" and height) or one from the list: every tile the game itself uses from
                    this map's two tilesets, with the walking and height the game most often gives it. Tiles that
                    carry a door or a sign are marked and stay as they are.
  Past the edge     the two crater maps have a dim band round them: what the game draws past the map's edge
                    (world.beyond: every row and column goes on with its last two tiles). It follows what is
                    painted on the edge and cannot be painted itself.
  Take from         (the craters; the user on test 18: "I need more tiles as well") "Take from another map..."
  another map       opens any place of the game that is drawn with the craters' basic tileset, as the game shows
                    it: drag a box over a house, a tree, a hot spring, and "Take what is in the box" makes it
                    the brush. The tiles that are that place's own get numbers of ours (656 on) and are listed
                    under "Taken from other maps"; tiles.py puts their pictures and colours into a tileset of
                    the craters' own, and says how much room is left (picture cells and colours).

"Check" asks check.py whether the game could use it all; "Save and rebuild" writes the files (placements.txt,
ground.txt, and tiles.txt once tiles are taken) and runs rebuild.py (a new ROM, its save, the map guide's
pictures). Nothing is written before that button.

The page tests itself in a browser without a window: ?selftest (and &apply for the save and the rebuild; on a copy
of the folder, with --here), read from the <pre id="selftest"> of the page; &shot=lib and &shot=paint leave the
page as a screenshot of "Take from another map" wants it (the place open with a box on it; its house put down).

The pictures come from a ROM built in a temporary folder; the page itself (PAGE below) is plain HTML and script,
no library. Close the console window to stop.
"""
import base64, http.server, io, json, os, socket, struct, sys, tempfile, threading, urllib.parse, webbrowser

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import paldea_patch as P
import places as PL
import ground as GR
import check as CK
import rebuild as RB
import map_guide as MG
import tiles as TL
import maps as M
import tidy as TD
import world as W

PORTS = range(8756, 8766)
# the page's tabs: (map key, title); the four stations are one room
TABS = [("mossdeep", "Mossdeep City"), ("wall", "The wall"), ("past", "Crater, past"), ("future", "Crater, future"),
        ("station1", "Research stations"), ("cavern", "Crystal Cavern"), ("vault", "Sealed Vault"),
        ("icecave", "Icy cave"),
        ("lab", "Zero Lab"), ("underdepths", "Underdepths")]
NOTES = {t[0]: t[6] for t in PL.THINGS}
GROUPS = [t[0] for t in PL.THINGS if isinstance(t[5], list)]      # the lists: any number of crystals
# what a tile does, for the list's hints (the behaviour byte of its metatile)
DOES = {0x20: "ice: you slide on it until something stops you",
        0x02: "tall grass: wild Pokemon", 0x03: "long grass: wild Pokemon", 0x10: "pond water", 0x11: "water",
        0x12: "deep water", 0x13: "a waterfall", 0x15: "sea water", 0x38: "a ledge: jump east",
        0x39: "a ledge: jump west", 0x3A: "a ledge: jump north", 0x3B: "a ledge: jump south", 0x60: "a cave mouth",
        0x61: "a ladder", 0x62: "a way out: east", 0x63: "a way out: west", 0x64: "a way out: north",
        0x65: "a way out: south", 0x69: "a door", 0x83: "a PC", 0x21: "sand", 0x24: "ash", 0x06: "deep sand",
        0x08: "cave floor: wild Pokemon as you walk", 0x0B: "cave floor: wild Pokemon as you walk",
        0x17: "shallow water", 0x16: "a puddle", 0x28: "a hot spring", 0x44: "pushes you east",
        0x45: "pushes you west", 0x46: "pushes you north", 0x47: "pushes you south", 0x50: "a current: east",
        0x51: "a current: west", 0x52: "a current: north", 0x53: "a current: south"}


def png(arr):
    from PIL import Image
    b = io.BytesIO()
    Image.fromarray(arr).save(b, "PNG")
    return b.getvalue()


def u32(rom, o): return struct.unpack_from("<I", rom, o)[0]


def usage(rom):
    """Tileset (ROM offset) -> {metatile: {collision and height bits: how often}}, from every map layout of the
    game: which tiles each tileset really has, and how the game itself lets you walk on them."""
    import numpy as np
    out = {}
    for k in range(M.LAYOUT_COUNT):
        lay = u32(rom, M.LAYOUTS + 4 * k) - 0x08000000
        if not 0 <= lay < len(rom) - 24:
            continue
        w, h, data = u32(rom, lay), u32(rom, lay + 4), u32(rom, lay + 12) - 0x08000000
        if not (0 < w <= 256 and 0 < h <= 256 and 0 <= data <= len(rom) - 2 * w * h):
            continue
        arr = np.frombuffer(rom, "<u2", w * h, data)
        for half in (0, 1):
            ts = u32(rom, lay + 16 + 4 * half) - 0x08000000
            part = arr[((arr & 0x3FF) >= 512) == bool(half)]
            if not len(part) or not 0 <= ts < len(rom):
                continue
            d = out.setdefault(ts, {})
            for v, c in zip(*np.unique(part, return_counts=True)):
                e = d.setdefault(int(v) & 0x3FF, {})
                e[int(v) & 0xFC00] = e.get(int(v) & 0xFC00, 0) + int(c)
    return out


class Editor:
    def __init__(self, folder, emulators=True):
        self.folder = os.path.abspath(folder)
        self.emulators = emulators                           # False: saves are not put in the emulators' folders
        self.file = os.path.join(self.folder, "placements.txt")
        self.gfile = os.path.join(self.folder, GR.NAME)
        self.tfile = os.path.join(self.folder, TL.NAME)       # tiles taken from other maps (tiles.py)
        self.src_images, self.src_list = {}, None            # pictures of the maps tiles are taken from
        self.lock = threading.Lock()
        self.tmp = tempfile.mkdtemp(prefix="areazero_editor_")
        self.images, self.data, self.version = {}, {}, 0
        self.group_sprite = {}                               # (map key, list id) -> (gfx, ext): a list of crystals
        self.start_problems = []                             # may be empty, and its picture is still wanted
        self.start_notes = []
        self.base_rom = open(RB.BASE_ROM, "rb").read()
        self.usage = usage(self.base_rom)
        self.levels, self.dirt = W.crater_levels(), W.crater_dirt()     # what tidy.py reads the crater's shape from
        try:
            values, painted, taken = PL.load(self.file), GR.load(self.gfile), TL.load(self.tfile)
            self.start_notes = list(values.notes)            # what a file from an older build had (places.py)
            self.survey(values, painted, taken)
        except (PL.PlacementError, GR.GroundError, CK.Problems, TL.TilesError) as e:
            self.start_problems = getattr(e, "lines", [str(e)])        # the files as they are cannot be used: show
            values, painted, taken = dict(PL.DEFAULTS), {}, TL.load(None)   # the built-in map, and say why
            self.survey(values, painted, taken)
        self.saved, self.saved_ground, self.saved_tiles = values, painted, taken

    def build(self, values, painted, taken=None, name="check"):
        """A ROM in the temporary folder from these positions, this ground and these taken tiles; what
        paldea_patch.py told."""
        import contextlib
        f, gf, tf = (os.path.join(self.tmp, name + ext) for ext in (".txt", "_ground.txt", "_tiles.txt"))
        with open(f, "w", encoding="utf-8", newline="\n") as h:
            h.write(PL.text(values))
        with open(gf, "w", encoding="utf-8", newline="\n") as h:
            h.write(GR.text(painted))
        with open(tf, "w", encoding="utf-8", newline="\n") as h:
            h.write(TL.text(taken or {}))
        rom, told = os.path.join(self.tmp, name + ".gba"), {}
        with contextlib.redirect_stdout(io.StringIO()):
            P.build(RB.BASE_ROM, rom, f, told, gf, tf)
        return rom, told

    def usual(self, g, n, mid):
        """The walking and height bits the game most often gives metatile mid of map g/n's secondary set."""
        how = self.usage.get(TL.tilesets_of(self.base_rom, g, n)[1] - 0x08000000, {}).get(mid)
        return max(how, key=how.get) if how else 3 << 12

    def tiles(self, m, told=None):
        """What can be painted on a map: {metatile: its usual collision and height bits}, from the map as it is
        drawn and from every map of the game with the same tilesets (the map's own way with a tile comes first).
        On the craters also the tiles taken from other maps, and not what of Petalburg's was given up for them."""
        g, n = m["source"]
        lay = u32(self.base_rom, P.header_of(self.base_rom, g, n)) - 0x08000000
        seen = {}
        for half in (0, 1):
            for mid, how in self.usage.get(u32(self.base_rom, lay + 16 + 4 * half) - 0x08000000, {}).items():
                seen[mid] = dict(how)
        own = {}
        for row in m["base"]:
            for v in row:
                e = own.setdefault(v & 0x3FF, {})
                e[v & 0xFC00] = e.get(v & 0xFC00, 0) + 1
        props = {mid: max(how, key=how.get) for mid, how in seen.items()}
        props.update({mid: max(how, key=how.get) for mid, how in own.items()})
        walked = {mid: sum(n for bits, n in how.items() if not bits & 0x0C00) for mid, how in own.items()}
        if told and m["key"] in TL.SECTIONS["crater"]:
            for mid in (told["custom"].given_up if told.get("custom") else ()):
                props.pop(mid, None)
            for ours, g, n, mid in told["taken"]["crater"]:
                props[ours] = self.usual(g, n, mid)
        return props, sorted(own), max(walked, key=walked.get)       # (the last: the floor, to start painting with)

    def survey(self, values, painted, taken=None):
        """The page's data and pictures for these positions, this ground and these taken tiles (which must pass
        the check)."""
        rom_path, told = self.build(values, painted, taken, "view")
        rom = MG.Rom(rom_path)
        by_key = {m["key"]: m for m in told["maps"]}
        self.crater = by_key["past"]["base"]                  # the crater as built (both times: one ground)
        images, maps, base = {}, [], {}
        for key, title in TABS:
            m = by_key[key]
            g, n = m["map"]
            ground = m["section"] or key                      # the ground's name: shared by maps with one ground
            base.setdefault(ground, m["base"])
            props, onmap, floor = self.tiles(m, told)
            ids = sorted(set(props) | {v & 0x3FF for row in m["blocks"] for v in row})
            take = key in TL.SECTIONS["crater"]
            images["atlas_" + key] = png(rom.atlas(g, n, ids))

            def picture(gfx, ext):
                s = "s_%d_%d" % (gfx, ext)
                if s not in images:
                    images[s] = png(rom.sprite(gfx, ext))
                return s

            def entry(tid, label, gfx, ext):
                w, h = PL.SIZE[PL.KIND_OF[tid]]
                return {"id": tid, "k": None, "label": label, "sprite": picture(gfx, ext), "sw": w, "sh": h,
                        "when": sorted(PL.WHEN_OF[tid]), "solid": tid in PL.ON_SOLID, "note": NOTES.get(tid, ""),
                        "section": PL.TITLE_OF[PL.SECTION_OF[tid]]}

            things = []
            for t in m["things"]:
                if t["k"] is None:                           # (one position serves all four stations)
                    name = PL.NAME_OF[t["id"]] if PL.SECTION_OF[t["id"]] == "stations" else t["name"]
                    things.append(entry(t["id"], name, t["gfx"], t["ext"]))
                else:
                    self.group_sprite[key, t["id"]] = (t["gfx"], t["ext"])
            groups = []
            for tid in GROUPS:
                if key in PL.MAPS_OF[PL.SECTION_OF[tid]]:
                    if (key, tid) not in self.group_sprite:      # no crystal left in the file: ask the built-in
                        told0 = self.build(dict(PL.DEFAULTS), {}, None, "builtin")[1]    # positions what one looks like
                        for m0 in told0["maps"]:
                            for t in m0["things"]:
                                if t["k"] is not None:
                                    self.group_sprite.setdefault((m0["key"], t["id"]), (t["gfx"], t["ext"]))
                    groups.append(entry(tid, "crystal", *self.group_sprite[key, tid]))
            does = {mid: DOES[m["beh"](mid)] for mid in ids if m["beh"](mid) in DOES}
            maps.append({"key": key, "title": title, "w": m["w"], "h": m["h"], "things": things, "groups": groups,
                         "ground": ground, "paint": m["section"] is not None, "rocks": key in ("past", "future"),
                         "tidy": m["section"] == "crater", "beyond": told.get("beyond", {}).get(key),
                         "doors": sorted(m["doors"]), "locked": [[x, y, why] for (x, y), why in
                                                                 sorted(m["locked"].items())],
                         "tiles": ids, "onmap": onmap, "floor": floor, "take": take,
                         "taken": [t[0] for t in told["taken"]["crater"]] if take else [],
                         "props": {str(k): v for k, v in props.items()},
                         "does": {str(k): v for k, v in does.items()}})
        self.version += 1
        self.images = images
        custom = told.get("custom") or TL.build(self.base_rom, [], {
            v & 0x3FF for row in by_key["past"]["blocks"] for v in row} | {P.DOOR_SHUT_TILE})
        self.data = {"maps": maps, "version": self.version, "folder": self.folder, "ground_base": base,
                     "room": TL.room(custom), "first_taken": TL.FIRST,
                     "rock": {"tile": told["rock"][0], "plain": list(told["rock"][1])},
                     "ground_titles": dict(GR.TITLE_OF)}

    def values_from(self, raw):
        """The page's positions, checked for shape: {id: [x, y]} or {id: [[x, y], ...]}."""
        out = {}
        for tid, default in PL.DEFAULTS.items():
            v = raw.get(tid, default)
            if isinstance(default, list):
                out[tid] = [(int(a), int(b)) for a, b in v]
            else:
                out[tid] = (int(v[0]), int(v[1]))
        return out

    def ground_from(self, raw):
        """The page's painted tiles, checked for shape: {section: {"x,y": block}}."""
        out = {}
        for sec, cells in (raw or {}).items():
            if sec not in GR.MAPS_OF:
                continue
            d = {}
            for k, v in cells.items():
                x, y = k.split(",")
                d[int(x), int(y)] = int(v) & 0xFFFF
            if d:
                out[sec] = d
        return out

    def tiles_from(self, raw):
        """The page's taken tiles, checked for shape: {section: [[our number, group, map, its metatile], ...]}."""
        out = {sec: [] for sec in TL.SECTIONS}
        for sec, rows in (raw or {}).items():
            if sec in out:
                out[sec] = sorted({(int(a), int(b), int(c), int(d)) for a, b, c, d in rows})
        return out

    def sources(self):
        """The maps tiles can be taken from, for the page's list: [{g, n, name, w, h}], by name."""
        if self.src_list is None:
            sys.path.insert(0, os.path.join(HERE, "..", "..", "translation"))
            from inserter import ENC
            dec = {v: k for k, v in ENC.items()}
            names = {}
            for i in range(213):
                p = u32(self.base_rom, P.MAPSEC_TABLE + 8 * i + 4) - 0x08000000
                if 0 <= p < len(self.base_rom):
                    raw = bytes(self.base_rom[p:p + 40]).split(b"\xff")[0]
                    names[i] = "".join(dec.get(b, "'") for b in raw).replace("\u2019", "'").strip()
            rows = TL.sources(self.base_rom, names)
            self.src_list = [{"g": g, "n": n, "name": name or "(no name)", "w": w, "h": h}
                             for g, n, name, w, h, sec in sorted(rows, key=lambda r: (r[2] == "", r[2], r[0], r[1]))]
        return self.src_list

    def source(self, g, n):
        """One of those maps: its blocks, and its picture (as the game has it: its own colours)."""
        with self.lock:
            if TL.tilesets_of(self.base_rom, g, n)[0] != TL.GENERAL:
                return {"ok": False, "problems": ["That map is not drawn with the General set the craters have."]}
            key = "src_%d_%d" % (g, n)
            if key not in self.src_images:
                self.src_images[key] = png(MG.Rom(RB.BASE_ROM).ground(g, n))
            blocks = P.blocks_of(self.base_rom, u32(self.base_rom, P.header_of(self.base_rom, g, n)))
            return {"ok": True, "g": g, "n": n, "w": len(blocks[0]), "h": len(blocks), "blocks": blocks, "img": key}

    def take(self, raw):
        """An area of another map, to paint the craters with: the tiles of it that are that map's own get numbers of
        ours (the ones taken before keep theirs), if they fit beside what is taken and painted already. The page
        gets the area as a brush, the new tiles' pictures (in their own map's colours until the next build tints
        them) and how much room is left."""
        import numpy as np
        with self.lock:
            g, n = int(raw["g"]), int(raw["n"])
            rom = self.base_rom
            prim, sec = TL.tilesets_of(rom, g, n)
            if prim != TL.GENERAL:
                return {"ok": False, "problems": ["That map is not drawn with the General set the craters have."]}
            blocks = P.blocks_of(rom, u32(rom, P.header_of(rom, g, n)))
            x0, x1 = sorted((int(raw["x0"]), int(raw["x1"])))
            y0, y1 = sorted((int(raw["y0"]), int(raw["y1"])))
            if not (0 <= x0 <= x1 < len(blocks[0]) and 0 <= y0 <= y1 < len(blocks)):
                return {"ok": False, "problems": ["That area is not on the map."]}
            taken = self.tiles_from(raw.get("tiles"))
            have = {(TL.tilesets_of(rom, a, b)[1], mid): ours for ours, a, b, mid in taken["crater"]}
            used = {t[0] for t in taken["crater"]}
            new, cells = [], []
            for y in range(y0, y1 + 1):
                row = []
                for x in range(x0, x1 + 1):
                    v = blocks[y][x]
                    mid = v & 0x3FF
                    if mid >= 512:
                        if (sec, mid) not in have:
                            ours = next((i for i in range(TL.FIRST, TL.LAST + 1) if i not in used), None)
                            if ours is None:
                                return {"ok": False, "problems": [
                                    "Every number a taken tile can have (%d to %d) is in use. Remove taken tiles "
                                    "you have not painted with." % (TL.FIRST, TL.LAST)]}
                            used.add(ours)
                            have[sec, mid] = ours
                            new.append((ours, g, n, mid))
                        mid = have[sec, mid]
                    row.append({"id": mid, "exact": mid | (v & 0xFC00)})
                cells.append(row)
            every = sorted(taken["crater"] + new)
            painted = self.ground_from(raw.get("ground"))
            needed = {v & 0x3FF for row in self.painted_crater(painted) for v in row} | {P.DOOR_SHUT_TILE}
            try:
                custom = TL.build(rom, every, needed)
            except TL.TilesError as e:
                return {"ok": False, "problems": e.lines}
            strip = np.zeros((16, 16 * max(1, len(new)), 3), np.uint8)
            if new:
                r = MG.Rom(RB.BASE_ROM).R
                lay = r.Layout(r.ptr(r.header(g, n)))
                for k, (ours, a, b, mid) in enumerate(new):
                    strip[:, 16 * k:16 * k + 16] = lay.metatile(mid)
            beh = CK.behaviours(rom, u32(rom, P.header_of(rom, g, n)) - 0x08000000)
            # the pictures as each crater will show them: the tint the build lays over the palettes, colour by colour
            import tint as TN
            strips = {}
            for era in TL.SECTIONS["crater"]:
                seen, out = {}, strip.copy()
                for yy in range(strip.shape[0]):
                    for xx in range(strip.shape[1]):
                        c = tuple(int(v) for v in strip[yy, xx])
                        if c not in seen:
                            v = TN.recolour(c[0] >> 3 | (c[1] >> 3) << 5 | (c[2] >> 3) << 10, era)
                            seen[c] = tuple((k << 3 | k >> 2) for k in (v & 31, v >> 5 & 31, v >> 10 & 31))
                        out[yy, xx] = seen[c]
                strips[era] = base64.b64encode(png(out)).decode("ascii")
            return {"ok": True, "cells": cells, "tiles": {"crater": [list(t) for t in every]},
                    "new": [t[0] for t in new], "strips": strips,
                    "props": {str(ours): self.usual(a, b, mid) for ours, a, b, mid in new},
                    "does": {str(ours): DOES[beh(mid)] for ours, a, b, mid in new if beh(mid) in DOES},
                    "room": TL.room(custom), "given_up": custom.given_up}

    def painted_crater(self, painted):
        """The crater's ground with this paint on."""
        blocks = [list(r) for r in self.crater]
        for (x, y), v in painted.get("crater", {}).items():
            if 0 <= y < len(blocks) and 0 <= x < len(blocks[0]):
                blocks[y][x] = v
        return blocks

    def untidy(self, painted):
        """How many of the crater's edge tiles do not fit their neighbours (tidy.py would change them), and how
        many tiles of trees painting has left without the rest of their tree."""
        blocks = self.painted_crater(painted)
        return [TD.count(blocks, self.crater, self.levels, self.dirt), len(TD.cut_trees(blocks, self.crater))]

    def tidy(self, raw):
        """The crater's edges put right: [[x, y, block], ...] for the page to paint."""
        with self.lock:
            ch = TD.crater(self.painted_crater(self.ground_from(raw.get("ground"))), self.crater, self.levels,
                           self.dirt)
            return {"changes": [[x, y, new] for x, y, old, new in ch]}

    def notes(self, told):
        """Worth knowing once a check has found nothing wrong: how many slides the Sealed Vault takes."""
        out = []
        for m in told["maps"]:
            way = CK.puzzle_way(m) if m.get("puzzle") else None
            if way:
                out.append("%s: every stake can be pulled, with %d slide%s at the least." % (
                    m["title"][0].upper() + m["title"][1:], way[0], "s" * (way[0] != 1)))
        return out

    def check(self, raw):
        with self.lock:
            painted, taken = self.ground_from(raw.get("ground")), self.tiles_from(raw.get("tiles"))
            try:
                told = self.build(self.values_from(raw.get("placements", {})), painted, taken)[1]
                notes = self.notes(told) + ([TL.room(told["custom"])] if told.get("custom") else [])
                return {"problems": [], "untidy": self.untidy(painted), "notes": notes}
            except (CK.Problems, TL.TilesError) as e:
                return {"problems": e.lines, "untidy": self.untidy(painted), "notes": []}

    def apply(self, raw):
        with self.lock:
            values, painted = self.values_from(raw.get("placements", {})), self.ground_from(raw.get("ground"))
            taken = self.tiles_from(raw.get("tiles"))
            try:
                self.build(values, painted, taken)
            except (CK.Problems, TL.TilesError) as e:
                return {"ok": False, "problems": e.lines, "lines": []}
            with open(self.file, "w", encoding="utf-8", newline="\n") as h:
                h.write(PL.text(values))
            if painted or os.path.exists(self.gfile):
                with open(self.gfile, "w", encoding="utf-8", newline="\n") as h:
                    h.write(GR.text(painted))
            if any(taken.values()) or os.path.exists(self.tfile):
                with open(self.tfile, "w", encoding="utf-8", newline="\n") as h:
                    h.write(TL.text(taken))
            lines = []
            ok = RB.rebuild(self.folder, say=lines.append, emulators=self.emulators)
            if ok:
                self.saved, self.saved_ground, self.saved_tiles = values, painted, taken
                self.survey(values, painted, taken)
            return {"ok": ok, "problems": [], "lines": lines, "untidy": self.untidy(painted)}

    def state(self):
        d = dict(self.data)
        d["saved"] = {k: (list(map(list, v)) if isinstance(v, list) else list(v)) for k, v in self.saved.items()}
        d["defaults"] = {k: (list(map(list, v)) if isinstance(v, list) else list(v)) for k, v in PL.DEFAULTS.items()}
        d["saved_ground"] = {sec: {"%d,%d" % xy: v for xy, v in cells.items()}
                             for sec, cells in self.saved_ground.items()}
        d["saved_tiles"] = {sec: [list(t) for t in rows] for sec, rows in self.saved_tiles.items()}
        d["start_problems"] = self.start_problems
        d["start_notes"] = self.start_notes
        d["untidy"] = self.untidy(self.saved_ground)
        return d


def handler(ed, stop):
    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def send(self, body, kind="application/json", code=200):
            if not isinstance(body, bytes):
                body = json.dumps(body).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            path = self.path.split("?")[0]
            if path == "/":
                self.send(PAGE.encode("utf-8"), "text/html; charset=utf-8")
            elif path == "/data":
                self.send(ed.state())
            elif path == "/sources":
                self.send(ed.sources())
            elif path == "/source":
                q = urllib.parse.parse_qs(self.path.partition("?")[2])
                self.send(ed.source(int(q["g"][0]), int(q["n"][0])))
            elif path.startswith("/img/") and path[5:-4] in ed.images:
                self.send(ed.images[path[5:-4]], "image/png")
            elif path.startswith("/img/") and path[5:-4] in ed.src_images:
                self.send(ed.src_images[path[5:-4]], "image/png")
            else:
                self.send({"error": "not found"}, code=404)

        def do_POST(self):
            n = int(self.headers.get("Content-Length") or 0)
            try:
                raw = json.loads(self.rfile.read(n) or b"{}")
                if self.path == "/check":
                    self.send(ed.check(raw))
                elif self.path == "/apply":
                    self.send(ed.apply(raw))
                elif self.path == "/tidy":
                    self.send(ed.tidy(raw))
                elif self.path == "/take":
                    self.send(ed.take(raw))
                elif self.path == "/quit":
                    self.send({"ok": True})
                    threading.Thread(target=stop, daemon=True).start()
                else:
                    self.send({"error": "not found"}, code=404)
            except Exception as e:                            # anything else: tell the page, keep serving
                self.send({"ok": False, "problems": ["The editor ran into an error: %r" % (e,)], "lines": []})
    return H


PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Area Zero editor</title>
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; }
  body { margin: 0; font: 14px/1.4 "Segoe UI", Arial, sans-serif; background: #14161c; color: #e6e8ee;
         display: grid; grid-template-rows: auto 1fr; height: 100vh; }
  header { padding: 8px 14px; background: #1d2029; border-bottom: 1px solid #333846; display: flex;
           gap: 14px; align-items: center; flex-wrap: wrap; }
  header h1 { font-size: 16px; margin: 0 8px 0 0; }
  .tabs { display: flex; gap: 4px; flex-wrap: wrap; }
  .tabs button, .modes button { background: #2a2e3a; border: 1px solid #3a4052; color: #cfd3de; padding: 5px 10px;
                 border-radius: 6px; cursor: pointer; }
  .tabs button.on, .modes button.on { background: #f0c63c; color: #1a1a1a; border-color: #f0c63c; font-weight: 600; }
  .modes { display: flex; gap: 4px; }
  .modes button { flex: 1; padding: 7px 6px; }
  main { display: grid; grid-template-columns: 1fr 352px; min-height: 0; }
  #view { overflow: auto; background: #0c0d11; position: relative; }
  #stage { position: relative; margin: 16px; }
  #stage canvas { position: absolute; left: 0; top: 0; image-rendering: pixelated; }
  #beyond { pointer-events: none; opacity: .5; display: none; }
  #over { z-index: 200000; display: none; cursor: crosshair; touch-action: none; }
  body.ground #over { display: block; }
  .thing { position: absolute; image-rendering: pixelated; cursor: grab; user-select: none; touch-action: none; }
  .thing.sel { filter: drop-shadow(0 0 3px #fff) drop-shadow(0 0 6px #f0c63c); }
  .thing.bad { filter: drop-shadow(0 0 3px #ff4d4d) drop-shadow(0 0 6px #ff4d4d); }
  .thing.dim { opacity: .28; }
  body.ground .thing { pointer-events: none; opacity: .5; }
  #tile, #box { position: absolute; pointer-events: none; display: none; z-index: 300000; }
  #tile { border: 2px solid #5dff8a; }
  #tile.bad { border-color: #ff4d4d; background: rgba(255, 77, 77, .25); }
  #box { border: 2px dashed #ffe45c; background: rgba(255, 228, 92, .12); }
  #where { position: sticky; left: 0; bottom: 0; background: rgba(20, 22, 28, .92); padding: 3px 10px;
           font: 12px Consolas, monospace; display: inline-block; z-index: 400000; }
  aside { background: #1a1d25; border-left: 1px solid #333846; padding: 12px; overflow: auto; display: flex;
          flex-direction: column; gap: 10px; }
  aside > * { flex-shrink: 0; }
  aside h2 { font-size: 13px; margin: 0; color: #9aa3b8; text-transform: uppercase; letter-spacing: .04em; }
  .row { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; }
  button.act { background: #2f6fed; border: 0; color: #fff; padding: 7px 12px; border-radius: 6px; cursor: pointer;
               font-weight: 600; }
  button.act.go { background: #23a55a; }
  button.plain { background: #2a2e3a; border: 1px solid #3a4052; color: #cfd3de; padding: 6px 10px;
                 border-radius: 6px; cursor: pointer; }
  button:disabled { opacity: .45; cursor: default; }
  #list { display: flex; flex-direction: column; gap: 2px; }
  #list div { padding: 3px 6px; border-radius: 4px; cursor: pointer; display: flex; justify-content: space-between;
              gap: 8px; }
  #list div:hover { background: #262a35; }
  #list div.sel { background: #3a3220; outline: 1px solid #f0c63c; }
  #list div.bad span:first-child { color: #ff8a8a; }
  #list span.xy { font: 12px Consolas, monospace; color: #9aa3b8; white-space: nowrap; }
  #msg { white-space: pre-wrap; font-size: 13px; background: #101218; border: 1px solid #333846; border-radius: 6px;
         padding: 8px; min-height: 60px; }
  #msg.bad { border-color: #a33; } #msg.good { border-color: #2a7; }
  #pick { font-size: 13px; color: #cfd3de; min-height: 54px; white-space: pre-wrap; }
  select, label { font-size: 13px; }
  .hint { color: #8b93a7; font-size: 12px; white-space: pre-wrap; }
  #dirty { color: #f0c63c; font-weight: 600; }
  .panel { display: flex; flex-direction: column; gap: 10px; }
  body.ground #pthings, body:not(.ground) #pground { display: none; }
  #brushbox { display: flex; gap: 10px; align-items: center; background: #101218; border: 1px solid #333846;
              border-radius: 6px; padding: 8px; }
  #brush { image-rendering: pixelated; background: #000; border: 1px solid #3a4052; flex: none; }
  #brushtext { font-size: 13px; white-space: pre-wrap; }
  .pal { image-rendering: pixelated; cursor: pointer; display: block; }
  #palwrap { max-height: 46vh; overflow: auto; background: #101218; border: 1px solid #333846; border-radius: 6px;
             padding: 6px; display: flex; flex-direction: column; gap: 6px; }
  kbd { background: #2a2e3a; border: 1px solid #3a4052; border-radius: 4px; padding: 0 4px; font: 12px Consolas, monospace; }
  #lib { position: fixed; inset: 0; background: #14161c; z-index: 900000; display: none; grid-template-rows: auto auto 1fr; }
  #lib.on { display: grid; }
  #libbar { padding: 8px 14px; background: #1d2029; border-bottom: 1px solid #333846; display: flex; gap: 12px;
            align-items: center; flex-wrap: wrap; }
  #libbar b { font-size: 16px; }
  #libhint { padding: 6px 14px; white-space: pre-wrap; height: 76px; box-sizing: border-box; overflow-y: auto; }
  #libhint.bad { color: #ff8a8a; }
  #libview { overflow: auto; }
  #libstage { position: relative; margin: 16px; display: inline-block; }
  #libc { image-rendering: pixelated; display: block; cursor: crosshair; }
  #libbox { position: absolute; border: 2px dashed #ffe45c; background: rgba(255, 228, 92, .14);
            pointer-events: none; display: none; }
  #libsel { max-width: 440px; }
  input[type=text] { background: #101218; border: 1px solid #3a4052; color: #e6e8ee; padding: 5px 8px;
                     border-radius: 6px; font-size: 13px; }
</style></head>
<body>
<header>
  <h1>Area Zero editor</h1>
  <div class="tabs" id="tabs"></div>
  <span id="dirty"></span>
</header>
<main>
  <div id="view"><div id="stage"><canvas id="beyond"></canvas><canvas id="ground"></canvas><canvas id="over"></canvas><div id="tile"></div><div id="box"></div></div><div id="where">&nbsp;</div></div>
  <aside>
    <div class="row">
      <button class="act" id="check">Check</button>
      <button class="act go" id="apply">Save and rebuild</button>
    </div>
    <div class="row">
      <button class="plain" id="revert">Undo my changes</button>
      <button class="plain" id="defaults">Put everything back</button>
    </div>
    <div id="msg"></div>
    <div class="modes">
      <button id="mthings" class="on">Move things</button>
      <button id="mground">Paint the ground</button>
    </div>
    <div class="row">
      <label>Zoom <select id="zoom"><option>1</option><option selected>2</option><option>3</option><option>4</option></select></label>
      <label id="whenlabel">Show <select id="when">
        <option value="all">everything</option>
        <option value="story">what is there during the story</option>
        <option value="after">what is there after the story</option>
      </select></label>
    </div>

    <div class="panel" id="pthings">
      <h2>Picked</h2>
      <div id="pick" class="hint">Nothing picked.</div>
      <div class="row">
        <button class="plain" id="add">Add a crystal</button>
        <button class="plain" id="remove" disabled>Remove this crystal</button>
      </div>
      <h2>On this map</h2>
      <div id="list"></div>
    </div>

    <div class="panel" id="pground">
      <div id="nopaint" class="hint"></div>
      <div id="paintui" class="panel">
        <h2>Brush</h2>
        <div id="brushbox"><canvas id="brush" width="48" height="48"></canvas><div id="brushtext"></div></div>
        <div class="row">
          <label>Walk <select id="walk">
            <option value="auto">as the tile is</option>
            <option value="0">can walk on it</option>
            <option value="1">solid</option>
          </select></label>
          <label>Height <select id="height"></select></label>
        </div>
        <div class="row">
          <label><input type="checkbox" id="showwalk"> show walls and water</label>
          <label><input type="checkbox" id="showheight"> show heights</label>
        </div>
        <div class="row">
          <button class="plain" id="undo" disabled>Undo (Ctrl+Z)</button>
          <button class="plain" id="redo" disabled>Redo</button>
          <button class="plain" id="resetmap">Put this map's ground back</button>
        </div>
        <div class="row" id="tidyrow">
          <button class="act" id="tidy">Tidy the edges</button>
          <span class="hint">corners of terraces, borders of paths, rims of puddles</span>
        </div>
        <div class="row" id="takerow">
          <button class="act" id="libopen">Take from another map...</button>
          <button class="plain" id="libprune">Remove taken tiles I have not painted</button>
        </div>
        <div class="hint" id="room"></div>
        <div class="hint" id="beyondhint">The dim band round the map is what the game draws past its edge: every row and column goes on with its last two tiles. It cannot be painted; it follows what you paint on the edge.</div>
        <div class="hint"><kbd>click / drag</kbd> paint    <kbd>right-click</kbd> pick the tile under the mouse
<kbd>right-drag</kbd> pick an area, then click where it goes    <kbd>Shift + drag</kbd> fill a box</div>
        <h2>Tiles</h2>
        <div id="palwrap">
          <div class="hint" id="pal3head">Taken from other maps</div><canvas class="pal" id="pal3"></canvas>
          <div class="hint">On this map</div><canvas class="pal" id="pal1"></canvas>
          <div class="hint">More from the same tilesets</div><canvas class="pal" id="pal2"></canvas>
        </div>
      </div>
    </div>
    <div class="hint" id="folder"></div>
    <div class="row"><button class="plain" id="quit">Close the editor</button></div>
  </aside>
</main>
<div id="lib">
  <div id="libbar">
    <b>Take from another map</b>
    <input type="text" id="libq" placeholder="type part of a place's name: koga, fortree, route 119..." size="40">
    <select id="libsel"></select>
    <label>Zoom <select id="libzoom"><option>1</option><option selected>2</option><option>3</option></select></label>
    <button class="act go" id="libtake" disabled>Take what is in the box</button>
    <button class="plain" id="libclose">Close</button>
  </div>
  <div id="libhint" class="hint"></div>
  <div id="libview"><div id="libstage"><canvas id="libc"></canvas><div id="libbox"></div></div></div>
</div>
<script>
"use strict";
let D = null, pos = {}, G = {}, tab = 0, sel = null, Z = 2, busy = false, mode = "things";
let brush = null, undo = [], redo = [], stroke = null, drag = null, locked = new Set();
let T = [];                               // the tiles taken from other maps for the craters: [our number, group, map, its tile]
const LIB = {list: null, map: null, img: null, sel: null, drag: false};
const atlas = {};
const $ = id => document.getElementById(id);
const stage = $("stage"), tile = $("tile"), box = $("box"), view = $("view"), gc = $("ground"), oc = $("over");
const bc = $("beyond");
const clone = o => JSON.parse(JSON.stringify(o));
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
const HINTS = {
  things: "Drag a person, a Pokemon, a crystal or an item to move it, or click it and use the arrow keys.\n" +
          "Nothing is saved until you press \"Save and rebuild\".",
  ground: "Paint with the left button. Right-click a tile on the map to paint with that one; right-drag over a " +
          "tree or a house to copy the whole thing, then click where it should go.\nOn the craters, \"Take from " +
          "another map\" brings in a house, a fence or anything else from another place of the game.\nDoors and " +
          "signs (marked in yellow) stay as they are. Nothing is saved until you press \"Save and rebuild\"."};

function xyOf(t) { return t.k === null ? pos[t.id] : pos[t.id][t.k]; }
function setXY(t, x, y) { if (t.k === null) pos[t.id] = [x, y]; else pos[t.id][t.k] = [x, y]; }
function map() { return D.maps[tab]; }
function inside(m, x, y) { return x >= 0 && y >= 0 && x < m.w && y < m.h; }

// ---------------------------------------------------------------- the ground
function rocks(m) {                       // a boulder behind each big Pokemon of the crater: "x,y" -> block
  const out = {};
  if (!m.rocks) return out;
  for (const t of m.things) {
    if (t.sw < 64) continue;
    const [x, y] = xyOf(t), g = G[m.ground];
    if (!inside(m, x, y - 1)) continue;
    const v = g[y - 1][x];
    if (D.rock.plain.includes(v & 0x3FF) && !((v >> 10) & 3)) out[x + "," + (y - 1)] = D.rock.tile | 1 << 10 | (v >> 12) << 12;
  }
  return out;
}
let rockNow = {};
function blockAt(m, x, y) {               // the block the game will have there
  const r = rockNow[x + "," + y];
  return r !== undefined ? r : G[m.ground][y][x];
}
function cell(m, x, y) {                  // " " off the map, D a door, # solid, ~ water, . ground
  if (!inside(m, x, y)) return " ";
  if (m.doorset.has(x + "," + y)) return "D";
  const v = blockAt(m, x, y);
  return (v >> 10) & 3 ? "#" : v >> 12 === 1 ? "~" : ".";
}
function drawCell(ctx, m, x, y) {
  const id = blockAt(m, x, y) & 0x3FF;
  ctx.drawImage(atlas[m.key], (id % 32) * 16, (id >> 5) * 16, 16, 16, x * 16, y * 16, 16, 16);
}
function drawGround() {
  const m = map();
  rockNow = rocks(m);
  gc.width = m.w * 16; gc.height = m.h * 16;
  for (const c of [gc, oc]) { c.style.width = m.w * 16 * Z + "px"; c.style.height = m.h * 16 * Z + "px"; }
  stage.style.width = m.w * 16 * Z + "px"; stage.style.height = m.h * 16 * Z + "px";
  const ctx = gc.getContext("2d");
  ctx.imageSmoothingEnabled = false;
  for (let y = 0; y < m.h; y++) for (let x = 0; x < m.w; x++) drawCell(ctx, m, x, y);
  drawBeyond();
  drawOver();
}
// Past the edge of a map that has strips joined to it (the craters): the game goes on with the map's last two
// tiles, row by row and column by column (world.beyond). BEYOND tiles of that are shown round the map, dimmed;
// in the game up to 3 come on screen.
const BEYOND = 4;
function beyondBlock(m, x, y) {
  const sx = x < 0 ? x & 1 : x >= m.w ? m.w - 2 + (x & 1) : x;
  const sy = y < 0 ? y & 1 : y >= m.h ? m.h - 2 + (y & 1) : y;
  return blockAt(m, sx, sy);
}
function drawBeyond() {
  const m = map(), n = m.beyond ? BEYOND : 0;
  stage.style.margin = (16 + n * 16 * Z) + "px";
  bc.style.display = n ? "block" : "none";
  if (!n) return;
  bc.width = (m.w + 2 * n) * 16; bc.height = (m.h + 2 * n) * 16;
  bc.style.width = bc.width * Z + "px"; bc.style.height = bc.height * Z + "px";
  bc.style.left = bc.style.top = -n * 16 * Z + "px";
  const ctx = bc.getContext("2d");
  ctx.imageSmoothingEnabled = false;
  for (let y = -n; y < m.h + n; y++) for (let x = -n; x < m.w + n; x++) {
    if (inside(m, x, y)) continue;
    const id = beyondBlock(m, x, y) & 0x3FF;
    ctx.drawImage(atlas[m.key], (id % 32) * 16, (id >> 5) * 16, 16, 16, (x + n) * 16, (y + n) * 16, 16, 16);
  }
}
function overCell(ctx, m, x, y) {          // the marks over one tile, at the screen's own sharpness
  const s = 16 * Z, v = blockAt(m, x, y);
  ctx.clearRect(x * s, y * s, s, s);
  if ($("showwalk").checked) {
    const c = cell(m, x, y);
    if (c === "#") {                        // solid: a red corner to corner, the tile's own colours kept
      ctx.fillStyle = "rgba(255,40,40,.16)"; ctx.fillRect(x * s, y * s, s, s);
      ctx.strokeStyle = "rgba(255,60,60,.75)"; ctx.lineWidth = Math.max(1, Z - 1);
      ctx.beginPath(); ctx.moveTo(x * s + 3, y * s + 3); ctx.lineTo(x * s + s - 3, y * s + s - 3); ctx.stroke();
    } else if (c === "~") { ctx.fillStyle = "rgba(70,150,255,.30)"; ctx.fillRect(x * s, y * s, s, s); }
  }
  if ($("showheight").checked && !((v >> 10) & 3)) {
    ctx.font = "bold " + Math.round(s * .42) + "px Consolas, monospace"; ctx.textAlign = "center"; ctx.textBaseline = "middle";
    ctx.lineWidth = 3; ctx.strokeStyle = "rgba(0,0,0,.8)"; ctx.fillStyle = "#fff";
    ctx.strokeText(String(v >> 12), x * s + s / 2, y * s + s / 2); ctx.fillText(String(v >> 12), x * s + s / 2, y * s + s / 2);
  }
  if (locked.has(x + "," + y)) {
    ctx.strokeStyle = "#ffe45c"; ctx.lineWidth = 2; ctx.strokeRect(x * s + 2, y * s + 2, s - 4, s - 4);
    ctx.fillStyle = "#ffe45c"; ctx.fillRect(x * s + 2, y * s + 2, s * .28, s * .28);
  }
}
function drawOver() {
  const m = map();
  oc.width = m.w * 16 * Z; oc.height = m.h * 16 * Z;
  if (mode !== "ground") return;
  const ctx = oc.getContext("2d");
  for (let y = 0; y < m.h; y++) for (let x = 0; x < m.w; x++) overCell(ctx, m, x, y);
}
function redrawCell(m, x, y) {
  drawCell(gc.getContext("2d"), m, x, y);
  if (mode === "ground") overCell(oc.getContext("2d"), m, x, y);
  if (m.beyond && (x < 2 || y < 2 || x >= m.w - 2 || y >= m.h - 2)) drawBeyond();   // the band follows the edge
}
function diffs() {                        // what is painted: ground name -> {"x,y": block}, against the map as drawn
  const out = {};
  for (const m of D.maps) {
    if (!m.paint || out[m.ground]) continue;
    const g = G[m.ground], b = D.ground_base[m.ground], d = {};
    for (let y = 0; y < m.h; y++) for (let x = 0; x < m.w; x++) if (g[y][x] !== b[y][x]) d[x + "," + y] = g[y][x];
    if (Object.keys(d).length) out[m.ground] = d;
  }
  return out;
}
function groundFrom(saved) {
  const g = clone(D.ground_base);
  for (const name in saved) for (const k in saved[name]) {
    const [x, y] = k.split(",").map(Number);
    if (g[name] && g[name][y] && x < g[name][y].length) g[name][y][x] = saved[name][k];
  }
  return g;
}
function dirty() { return !same(pos, D.saved) || !same(diffs(), D.saved_ground) || !same(T, D.saved_tiles.crater || []); }
function showDirty() { $("dirty").textContent = dirty() ? "Changes not saved yet" : ""; }

// ---------------------------------------------------------------- the brush
function props(m, id) { const p = m.props[id]; return p === undefined ? 3 << 12 : p; }
function describe(v) {
  return ((v >> 10) & 3 ? "solid" : "can walk") + ", height " + (v >> 12);
}
function setBrush(b) {
  brush = b;
  const m = map(), c = $("brush"), ctx = c.getContext("2d");
  const wide = b.w === 1 && b.h === 1 ? 48 : Math.min(120, b.w * 24, 120 * b.w / b.h);   // its picture: 120 px at most
  c.width = b.w * 16; c.height = b.h * 16;
  c.style.width = wide + "px"; c.style.height = wide * b.h / b.w + "px";
  ctx.imageSmoothingEnabled = false;
  for (let j = 0; j < b.h; j++) for (let i = 0; i < b.w; i++) {
    const id = b.cells[j][i].id;
    ctx.drawImage(atlas[m.key], (id % 32) * 16, (id >> 5) * 16, 16, 16, i * 16, j * 16, 16, 16);
  }
  const one = b.w === 1 && b.h === 1 ? b.cells[0][0] : null;
  let text;
  if (!one) text = "An area of " + b.w + " x " + b.h + " tiles, copied as it is on the map.";
  else {
    const does = m.does[one.id] ? "\n" + m.does[one.id] : "";
    text = "Tile " + one.id + does + "\n" + (one.exact !== null ? "as on the map: " + describe(one.exact)
      : "usually: " + describe(props(m, one.id)));
  }
  $("brushtext").textContent = text;
  drawPalettes();
}
function blockFor(m, c, x, y) {             // the block a brush tile becomes on (x, y)
  const g = G[m.ground];
  let coll, elev;
  if (c.exact !== null) { coll = (c.exact >> 10) & 3; elev = c.exact >> 12; }
  else {
    const p = props(m, c.id), usual = p >> 12, here = g[y][x] >> 12;
    coll = (p >> 10) & 3;
    // a tile from the list takes the height of what it is painted on, unless it has one of its own (water is
    // 1, stairs and doors 0, a bridge 15) or what it is painted on has
    elev = [0, 1, 15].includes(usual) || [0, 1, 15].includes(here) ? usual : here;
  }
  if ($("walk").value !== "auto") coll = Number($("walk").value);
  if ($("height").value !== "auto") elev = Number($("height").value);
  return c.id | coll << 10 | elev << 12;
}
function put(m, x, y, v) {                  // one tile of a stroke
  if (!inside(m, x, y) || locked.has(x + "," + y)) return;
  const g = G[m.ground];
  if (g[y][x] === v) return;
  stroke.push([m.ground, x, y, g[y][x], v]);
  g[y][x] = v;
  redrawCell(m, x, y);
}
function stamp(m, x, y) {                   // the brush with its top left corner on (x, y)
  for (let j = 0; j < brush.h; j++) for (let i = 0; i < brush.w; i++)
    if (inside(m, x + i, y + j)) put(m, x + i, y + j, blockFor(m, brush.cells[j][i], x + i, y + j));
}
function endStroke() {
  if (stroke && stroke.length) { undo.push(stroke); redo = []; }
  stroke = null;
  const m = map(), was = JSON.stringify(rockNow);
  rockNow = rocks(m);
  if (JSON.stringify(rockNow) !== was) drawGround();
  drawThings(); showDirty(); buttons();
}
function replay(list, back) {
  const m = map();
  for (const [name, x, y, old, now] of back ? list.slice().reverse() : list) G[name][y][x] = back ? old : now;
  drawGround(); drawThings(); showDirty(); buttons();
}
function buttons() { $("undo").disabled = !undo.length; $("redo").disabled = !redo.length; }
function doUndo() { if (undo.length) { const s = undo.pop(); redo.push(s); replay(s, true); } }
function doRedo() { if (redo.length) { const s = redo.pop(); undo.push(s); replay(s, false); } }

function drawPalette(c, ids) {
  const m = map(), per = 9, s = 34;
  c.width = per * s; c.height = Math.max(1, Math.ceil(ids.length / per)) * s;
  c.style.width = c.width + "px"; c.style.height = c.height + "px";
  const ctx = c.getContext("2d");
  ctx.imageSmoothingEnabled = false;
  ids.forEach((id, k) => {
    const x = (k % per) * s, y = Math.floor(k / per) * s;
    ctx.drawImage(atlas[m.key], (id % 32) * 16, (id >> 5) * 16, 16, 16, x + 1, y + 1, 32, 32);
    if (brush && brush.w === 1 && brush.h === 1 && brush.cells[0][0].id === id) {
      ctx.strokeStyle = "#f0c63c"; ctx.lineWidth = 2; ctx.strokeRect(x + 1, y + 1, 32, 32);
    }
  });
  c.ids = ids;
}
function drawPalettes() {
  const m = map(), on = new Set(m.onmap), mine = new Set(m.take ? T.map(t => t[0]) : []), gone = m.gone || new Set();
  $("pal3head").style.display = $("pal3").style.display = mine.size ? "" : "none";
  drawPalette($("pal3"), [...mine].sort((a, b) => a - b));
  drawPalette($("pal1"), m.onmap);
  // (not what was taken, which has its own list; nor what of the map's own set was given up for the taken tiles;
  // nor a taken tile that has been removed since)
  drawPalette($("pal2"), m.tiles.filter(id => !on.has(id) && !mine.has(id) && !gone.has(id) && !(m.take && id >= D.first_taken)));
}
function palId(c, ev) {
  const r = c.getBoundingClientRect(), k = Math.floor((ev.clientY - r.top) / 34) * 9 + Math.floor((ev.clientX - r.left) / 34);
  return c.ids && k >= 0 && k < c.ids.length && ev.clientX - r.left < 9 * 34 ? c.ids[k] : null;
}
for (const id of ["pal1", "pal2", "pal3"]) {
  $(id).addEventListener("click", ev => {
    const t = palId($(id), ev);
    if (t !== null) setBrush({w: 1, h: 1, cells: [[{id: t, exact: null}]]});
  });
  $(id).addEventListener("mousemove", ev => {
    const t = palId($(id), ev), m = map();
    $(id).title = t === null ? "" : "tile " + t + ": " + describe(props(m, t)) + (m.does[t] ? " (" + m.does[t] + ")" : "");
  });
}

// ---------------------------------------------------------------- painting with the mouse
function line(x0, y0, x1, y1, f) {          // every tile from one to the other
  const dx = Math.abs(x1 - x0), dy = Math.abs(y1 - y0), sx = x0 < x1 ? 1 : -1, sy = y0 < y1 ? 1 : -1;
  let e = dx - dy;
  for (;;) {
    f(x0, y0);
    if (x0 === x1 && y0 === y1) return;
    const e2 = 2 * e;
    if (e2 > -dy) { e -= dy; x0 += sx; }
    if (e2 < dx) { e += dx; y0 += sy; }
  }
}
function showBox(x0, y0, x1, y1) {
  const ax = Math.min(x0, x1), ay = Math.min(y0, y1), s = 16 * Z;
  box.style.display = "block"; box.style.left = ax * s + "px"; box.style.top = ay * s + "px";
  box.style.width = (Math.abs(x1 - x0) + 1) * s + "px"; box.style.height = (Math.abs(y1 - y0) + 1) * s + "px";
}
function hover(x, y) {
  const m = map(), s = 16 * Z;
  if (!inside(m, x, y)) { tile.style.display = "none"; $("where").textContent = " "; return; }
  const v = blockAt(m, x, y), why = m.lockwhy[x + "," + y];
  $("where").textContent = x + ", " + y + "  tile " + (v & 0x3FF) + "  " + describe(v) +
    (m.does[v & 0x3FF] ? "  (" + m.does[v & 0x3FF] + ")" : "") + (why ? "  -- stays as it is: " + why : "");
  if (!brush || !m.paint) { tile.style.display = "none"; return; }
  tile.style.display = "block"; tile.className = why && brush.w === 1 && brush.h === 1 ? "bad" : "";
  tile.style.left = x * s + "px"; tile.style.top = y * s + "px";
  tile.style.width = Math.min(brush.w, m.w - x) * s + "px"; tile.style.height = Math.min(brush.h, m.h - y) * s + "px";
}
oc.addEventListener("contextmenu", ev => ev.preventDefault());
oc.addEventListener("pointerdown", ev => {
  const m = map(), [x, y] = tileAt(ev);
  if (!m.paint || !inside(m, x, y) || drag) return;
  ev.preventDefault();
  try { oc.setPointerCapture(ev.pointerId); } catch (err) {}
  if (ev.button === 2) drag = {kind: "pick", x0: x, y0: y, x1: x, y1: y};
  else if (ev.button === 0 && brush && ev.shiftKey) drag = {kind: "fill", x0: x, y0: y, x1: x, y1: y};
  else if (ev.button === 0 && brush) { drag = {kind: "paint", x0: x, y0: y, x1: x, y1: y}; stroke = []; stamp(m, x, y); }
  else return;
  if (drag.kind !== "paint") { showBox(x, y, x, y); tile.style.display = "none"; }
});
oc.addEventListener("pointermove", ev => {
  const m = map();
  let [x, y] = tileAt(ev);
  if (!drag) { hover(x, y); return; }
  x = Math.max(0, Math.min(m.w - 1, x)); y = Math.max(0, Math.min(m.h - 1, y));
  if (drag.kind === "paint") {
    if (brush.w === 1 && brush.h === 1) line(drag.x1, drag.y1, x, y, (a, b) => stamp(m, a, b));
    else {                                  // an area is laid side by side with the first one
      const ax = drag.x0 + Math.floor((x - drag.x0) / brush.w) * brush.w;
      const ay = drag.y0 + Math.floor((y - drag.y0) / brush.h) * brush.h;
      if (ax !== drag.ax || ay !== drag.ay) { stamp(m, ax, ay); drag.ax = ax; drag.ay = ay; }
    }
    hover(x, y);
  } else showBox(drag.x0, drag.y0, x, y);
  drag.x1 = x; drag.y1 = y;
});
function drop(ev) {
  if (!drag) return;
  const m = map(), d = drag;
  drag = null; box.style.display = "none";
  const ax = Math.min(d.x0, d.x1), ay = Math.min(d.y0, d.y1), bx = Math.max(d.x0, d.x1), by = Math.max(d.y0, d.y1);
  if (d.kind === "pick") {
    const cells = [];
    for (let y = ay; y <= by; y++) { const row = []; for (let x = ax; x <= bx; x++) { const v = G[m.ground][y][x]; row.push({id: v & 0x3FF, exact: v}); } cells.push(row); }
    setBrush({w: bx - ax + 1, h: by - ay + 1, cells: cells});
    say(cells.length * cells[0].length === 1 ? "Painting with tile " + cells[0][0].id + ", as it is on the map."
      : "Copied " + (bx - ax + 1) + " x " + (by - ay + 1) + " tiles. Click where its top left corner should go.");
  } else if (d.kind === "fill") {
    stroke = [];
    for (let y = ay; y <= by; y++) for (let x = ax; x <= bx; x++)
      put(m, x, y, blockFor(m, brush.cells[(y - ay) % brush.h][(x - ax) % brush.w], x, y));
    endStroke();
  } else endStroke();
}
oc.addEventListener("pointerup", drop);
oc.addEventListener("pointercancel", drop);
oc.addEventListener("pointerleave", () => { if (!drag) { tile.style.display = "none"; } });

// ---------------------------------------------------------------- the things
// the quick look the page takes at a tile; "Check" asks the real rules
function fits(t, x, y) {
  const m = map(), c = cell(m, x, y);
  if (c === " " || c === "D") return false;
  if (c === "#") return t.solid;
  if (c === "~") return [[1, 0], [-1, 0], [0, 1], [0, -1]].every(d => cell(m, x + d[0], y + d[1]) === "~");
  return true;
}
function shown(t) {
  const w = $("when").value;
  return w === "all" || t.when.includes(w) || t.when.includes("finale") || t.when.includes("ending");
}
function things() {                       // this map's things; a list has as many crystals as pos says
  const out = map().things.slice();
  for (const g of map().groups)
    pos[g.id].forEach((xy, k) => out.push(Object.assign({}, g, {k: k, label: g.label + " " + (k + 1)})));
  return out;
}
function key(t) { return t.id + (t.k === null ? "" : "#" + t.k); }

function drawThings() {
  const m = map();
  for (const e of [...stage.querySelectorAll(".thing")]) e.remove();
  const list = $("list"); list.innerHTML = "";
  for (const t of things()) {
    const [x, y] = xyOf(t), ok = fits(t, x, y);
    const e = document.createElement("img");
    e.className = "thing" + (sel === key(t) ? " sel" : "") + (ok ? "" : " bad") + (shown(t) ? "" : " dim");
    e.src = "/img/" + t.sprite + ".png?v=" + D.version; e.draggable = false; e.title = t.label;
    e.style.width = t.sw * Z + "px"; e.style.height = t.sh * Z + "px";
    e.style.left = (x * 16 + 8 - t.sw / 2) * Z + "px"; e.style.top = (y * 16 + 16 - t.sh) * Z + "px";
    e.style.zIndex = String(1000 + y * 100 + x + (sel === key(t) ? 50000 : 0));
    e.dataset.key = key(t);
    e.addEventListener("pointerdown", ev => grab(ev, t, e));
    stage.appendChild(e);
    const row = document.createElement("div");
    row.className = (sel === key(t) ? "sel" : "") + (ok ? "" : " bad");
    row.innerHTML = "<span></span><span class='xy'></span>";
    row.children[0].textContent = t.label; row.children[1].textContent = x + ", " + y;
    row.addEventListener("click", () => { pick(t); reveal(t); });
    list.appendChild(row);
  }
  const t = things().find(t => key(t) === sel);
  $("pick").textContent = t ? t.label + "  at " + xyOf(t).join(", ") + "\n[" + t.section + "]" +
    (t.note ? "\n" + t.note : "") : "Nothing picked.";
  $("remove").disabled = !(t && t.k !== null);
  $("add").style.display = $("remove").style.display = groupOf() ? "" : "none";
  showDirty();
}
function draw() { drawGround(); drawThings(); }
function groupOf() {                        // this map's list of crystals, if it has one
  return map().groups.length ? map().groups[0] : null;
}
function pick(t) { sel = t ? key(t) : null; drawThings(); }
function reveal(t) {
  const [x, y] = xyOf(t);
  view.scrollTo({left: stage.offsetLeft + x * 16 * Z - view.clientWidth / 2,
                 top: stage.offsetTop + y * 16 * Z - view.clientHeight / 2, behavior: "smooth"});
}
function tileAt(ev) {
  const r = stage.getBoundingClientRect();
  return [Math.floor((ev.clientX - r.left) / (16 * Z)), Math.floor((ev.clientY - r.top) / (16 * Z))];
}
function showTile(x, y, ok) {
  tile.style.display = "block"; tile.className = ok ? "" : "bad";
  tile.style.left = x * 16 * Z + "px"; tile.style.top = y * 16 * Z + "px";
  tile.style.width = tile.style.height = 16 * Z + "px";
}
function grab(ev, t, e) {
  ev.preventDefault();
  sel = key(t);
  for (const o of stage.querySelectorAll(".thing.sel")) o.classList.remove("sel");
  e.classList.add("sel");
  try { e.setPointerCapture(ev.pointerId); } catch (err) {}   // (not every pointer can be captured)
  const m = map();
  const [gx, gy] = tileAt(ev), [ox, oy] = xyOf(t);        // it follows the pointer from where it was taken hold of
  const move = ev2 => {
    let [x, y] = tileAt(ev2);
    x = Math.max(0, Math.min(m.w - 1, x + ox - gx)); y = Math.max(0, Math.min(m.h - 1, y + oy - gy));
    setXY(t, x, y);
    e.style.left = (x * 16 + 8 - t.sw / 2) * Z + "px"; e.style.top = (y * 16 + 16 - t.sh) * Z + "px";
    showTile(x, y, fits(t, x, y));
    $("where").textContent = t.label + "  " + x + ", " + y;
  };
  const drop = () => {
    e.removeEventListener("pointermove", move); e.removeEventListener("pointerup", drop);
    e.removeEventListener("pointercancel", drop);
    tile.style.display = "none"; draw();
  };
  e.addEventListener("pointermove", move); e.addEventListener("pointerup", drop);
  e.addEventListener("pointercancel", drop);
  move(ev);
}
stage.addEventListener("pointermove", ev => {
  if (ev.buttons || mode !== "things") return;
  const [x, y] = tileAt(ev), c = cell(map(), x, y);
  $("where").textContent = c === " " ? " " : x + ", " + y +
    (c === "#" ? "  solid" : c === "~" ? "  water" : c === "D" ? "  a door" : "");
});
stage.addEventListener("pointerdown", ev => { if (mode === "things" && (ev.target === stage || ev.target === gc)) pick(null); });
document.addEventListener("keydown", ev => {
  if (["SELECT", "INPUT"].includes(document.activeElement.tagName)) return;
  if (mode === "ground") {
    const k = ev.key.toLowerCase();
    if ((ev.ctrlKey || ev.metaKey) && k === "z") { ev.preventDefault(); if (ev.shiftKey) doRedo(); else doUndo(); }
    else if ((ev.ctrlKey || ev.metaKey) && k === "y") { ev.preventDefault(); doRedo(); }
    return;
  }
  const step = {ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1]}[ev.key];
  const t = sel && things().find(t => key(t) === sel);
  if (!step || !t) return;
  ev.preventDefault();
  const m = map(), [x, y] = xyOf(t);
  setXY(t, Math.max(0, Math.min(m.w - 1, x + step[0])), Math.max(0, Math.min(m.h - 1, y + step[1])));
  draw();
});

// ---------------------------------------------------------------- the buttons
function say(text, kind) { const m = $("msg"); m.textContent = text; m.className = kind || ""; }
async function post(path, body) {
  const r = await fetch(path, {method: "POST", headers: {"Content-Type": "application/json"},
                               body: JSON.stringify(body)});
  return r.json();
}
function lock(on) { busy = on; for (const id of ["check", "apply", "revert", "defaults"]) $(id).disabled = on; }
function problems(list) {
  return list.length + " thing" + (list.length > 1 ? "s" : "") + " to put right:\n\n" +
    list.map(p => "• " + p).join("\n\n");
}
function all() { return {placements: pos, ground: diffs(), tiles: {crater: T}}; }

// ---------------------------------------------------------------- tiles taken from another map
function canvasOf(img) {                    // (a canvas, so that taken tiles can be drawn into the map's tile sheet)
  const c = document.createElement("canvas"); c.width = img.width; c.height = img.height;
  c.getContext("2d").drawImage(img, 0, 0);
  return c;
}
function libSay(text, bad) { const h = $("libhint"); h.textContent = text; h.className = "hint" + (bad ? " bad" : ""); }
const LIBHINT = "Pick a place, then drag a box over what you want: a house, a fence, a flower bed, a rock. \"Take " +
  "what is in the box\" brings it to the crater as a brush: click where its top left corner should go.\nOnly places " +
  "drawn with the same basic set as the craters are listed (most of the game's outdoors and caves).";
function fillLib() {
  const s = $("libsel"), words = $("libq").value.toLowerCase().split(/\s+/).filter(Boolean), was = s.value;
  s.innerHTML = "";
  for (const e of LIB.list) {
    const label = e.name + "   (" + e.g + "/" + e.n + ", " + e.w + " x " + e.h + ")";
    if (words.length && !words.every(w => label.toLowerCase().includes(w))) continue;
    const o = document.createElement("option"); o.value = e.g + "/" + e.n; o.textContent = label; s.appendChild(o);
  }
  if ([...s.options].some(o => o.value === was)) s.value = was;
  return s.value !== was;
}
async function pickLib() {
  const v = $("libsel").value;
  if (!v) { libSay("No place of that name. Type less of it."); return; }
  const [g, n] = v.split("/").map(Number);
  libSay("Drawing the map...");
  const r = await (await fetch("/source?g=" + g + "&n=" + n)).json();
  if (!r.ok) { libSay(r.problems.join("\n"), true); return; }
  LIB.map = r; LIB.sel = null; LIB.img = await image("/img/" + r.img + ".png");
  libSay(LIBHINT);
  drawLib();
  $("libview").scrollTo(0, 0);
}
function drawLib() {
  const m = LIB.map, c = $("libc"), z = Number($("libzoom").value);
  if (!m) return;
  c.width = m.w * 16; c.height = m.h * 16;
  c.style.width = m.w * 16 * z + "px"; c.style.height = m.h * 16 * z + "px";
  const ctx = c.getContext("2d");
  ctx.imageSmoothingEnabled = false; ctx.drawImage(LIB.img, 0, 0);
  showLibBox();
}
function showLibBox() {
  const b = $("libbox"), q = LIB.sel, z = Number($("libzoom").value) * 16;
  $("libtake").disabled = !q;
  if (!q) { b.style.display = "none"; return; }
  const ax = Math.min(q.x0, q.x1), ay = Math.min(q.y0, q.y1), w = Math.abs(q.x1 - q.x0) + 1, h = Math.abs(q.y1 - q.y0) + 1;
  b.style.display = "block"; b.style.left = ax * z + "px"; b.style.top = ay * z + "px";
  b.style.width = w * z + "px"; b.style.height = h * z + "px";
  libSay(w + " x " + h + " tiles from " + ax + ", " + ay + ". \"Take what is in the box\" brings them to the crater.");
}
function libTile(ev) {
  const r = $("libc").getBoundingClientRect(), z = Number($("libzoom").value) * 16, m = LIB.map;
  return [Math.max(0, Math.min(m.w - 1, Math.floor((ev.clientX - r.left) / z))),
          Math.max(0, Math.min(m.h - 1, Math.floor((ev.clientY - r.top) / z)))];
}
async function openLib() {
  if (!map().take) return;
  $("lib").classList.add("on");
  if (!LIB.list) {
    libSay("Reading the game's maps...");
    LIB.list = await (await fetch("/sources")).json();
    fillLib();
    libSay(LIBHINT);
  }
  $("libq").focus();
  if (!LIB.map) await pickLib();
}
async function takeLib(sel) {                // the box of the open map (or the one given: for the page's own test)
  const q = sel || LIB.sel, m = LIB.map;
  if (!q || !m) return null;
  $("libtake").disabled = true;
  const r = await post("/take", {g: m.g, n: m.n, x0: q.x0, y0: q.y0, x1: q.x1, y1: q.y1, tiles: {crater: T},
                                 ground: diffs()});
  if (!r.ok) { libSay(problems(r.problems), true); $("libtake").disabled = false; return r; }
  T = r.tiles.crater;
  for (const cm of D.maps) {
    if (!cm.take) continue;
    const strip = await image("data:image/png;base64," + r.strips[cm.key]);   // (tinted as that crater is)
    const ctx = atlas[cm.key].getContext("2d");
    r.new.forEach((id, k) => ctx.drawImage(strip, k * 16, 0, 16, 16, (id % 32) * 16, (id >> 5) * 16, 16, 16));
    for (const id of r.new) if (!cm.tiles.includes(id)) cm.tiles.push(id);
    Object.assign(cm.props, r.props); Object.assign(cm.does, r.does);
    cm.gone = new Set(r.given_up);
  }
  $("room").textContent = r.room;
  $("lib").classList.remove("on");
  setBrush({w: r.cells[0].length, h: r.cells.length, cells: r.cells});
  brush.map = map().key;
  say((r.new.length ? r.new.length + " new tile" + (r.new.length > 1 ? "s were" : " was") + " taken." :
       "Nothing new had to be taken: you have these tiles already.") +
      " The brush is the area you chose: click on the crater where its top left corner should go.\n\n" + r.room +
      "\n\nNothing is saved until you press \"Save and rebuild\".", "good");
  showDirty();
  return r;
}
$("libopen").addEventListener("click", openLib);
$("libclose").addEventListener("click", () => $("lib").classList.remove("on"));
$("libtake").addEventListener("click", () => takeLib());
$("libq").addEventListener("input", () => { if (LIB.list && fillLib()) pickLib(); });
$("libsel").addEventListener("change", pickLib);
$("libzoom").addEventListener("change", drawLib);
$("libc").addEventListener("pointerdown", ev => {
  if (!LIB.map || ev.button !== 0) return;
  ev.preventDefault();
  try { $("libc").setPointerCapture(ev.pointerId); } catch (err) {}
  const [x, y] = libTile(ev);
  LIB.drag = true; LIB.sel = {x0: x, y0: y, x1: x, y1: y};
  showLibBox();
});
$("libc").addEventListener("pointermove", ev => {
  if (!LIB.drag) return;
  const [x, y] = libTile(ev);
  LIB.sel.x1 = x; LIB.sel.y1 = y;
  showLibBox();
});
for (const type of ["pointerup", "pointercancel"]) $("libc").addEventListener(type, () => { LIB.drag = false; });
$("libprune").addEventListener("click", () => {
  const used = new Set();
  for (const row of G.crater) for (const v of row) used.add(v & 0x3FF);
  if (brush) for (const row of brush.cells) for (const c of row) used.add(c.id);
  const before = T.length;
  T = T.filter(t => used.has(t[0]));
  drawPalettes(); showDirty();
  say(before - T.length ? (before - T.length) + " taken tile" + (before - T.length > 1 ? "s" : "") + " that " +
      "you had not painted with " + (before - T.length > 1 ? "are" : "is") + " gone from the list. \"Check\" says " +
      "how much room that leaves." : "Every taken tile is painted somewhere on the crater (or is in the brush).");
});
function notes(list) { return list && list.length ? "\n\n" + list.join("\n") : ""; }
function untidy(u) {                          // a word after a check when edges do not fit or a tree is cut
  const [n, trees] = u || [0, 0];
  return (n ? "\n\n" + n + " edge tile" + (n > 1 ? "s do" : " does") + " not fit the tiles beside " +
    (n > 1 ? "them" : "it") + " (a corner, a path's border, a puddle's rim). \"Tidy the edges\", under " +
    "\"Paint the ground\" on a crater map, puts the right pieces there." : "") +
    (trees ? "\n\n" + trees + " tile" + (trees > 1 ? "s" : "") + " of a tree in the crater " +
    (trees > 1 ? "have" : "has") + " lost the rest of the tree. A tree is two tiles wide and three tall: copy a " +
    "whole one over it with right-drag, or paint grass over what is left." : "");
}
async function tidy() {
  const m = map();
  if (!m.tidy) return;
  lock(true);
  try {
    const r = await post("/tidy", all());
    stroke = [];
    for (const [x, y, v] of r.changes) put(m, x, y, v);
    const n = stroke.length;
    endStroke(); drawGround();
    say(n ? "Tidied " + n + " tile" + (n > 1 ? "s" : "") + ": every corner, border and rim has the piece that fits " +
            "its neighbours now. Ctrl+Z takes it back." : "Nothing to tidy: every edge already fits.", n ? "good" : "");
  } finally { lock(false); }
}
async function check() {
  lock(true); say("Checking...");
  try {
    const r = await post("/check", all());
    if (r.problems.length) say(problems(r.problems) + untidy(r.untidy), "bad");
    else say("Everything is in order. \"Save and rebuild\" makes the ROM." + untidy(r.untidy) + notes(r.notes), "good");
    return r.problems;
  } finally { lock(false); }
}
async function apply() {
  lock(true); say("Building the ROM and drawing the pictures. This takes a little while...");
  try {
    const r = await post("/apply", all());
    if (r.problems.length) { say("Nothing was saved.  " + problems(r.problems), "bad"); return r; }
    if (!r.ok) { say(r.lines.join("\n"), "bad"); return r; }
    await load(true);
    say(r.lines.join("\n") + untidy(r.untidy), "good");
    return r;
  } finally { lock(false); }
}
function image(src) {
  return new Promise((ok, bad) => { const i = new Image(); i.onload = () => ok(i); i.onerror = bad; i.src = src; });
}
async function load(keep) {
  D = await (await fetch("/data")).json();
  T = clone(D.saved_tiles.crater || []);
  $("room").textContent = D.room;
  for (const m of D.maps) {
    atlas[m.key] = canvasOf(await image("/img/atlas_" + m.key + ".png?v=" + D.version));
    m.doorset = new Set(m.doors.map(d => d[0] + "," + d[1]));
    m.lockwhy = {};
    for (const [x, y, why] of m.locked) m.lockwhy[x + "," + y] = why;
  }
  pos = clone(D.saved);
  G = groundFrom(D.saved_ground);
  undo = []; redo = []; buttons();
  if (!keep) {
    const want = new URLSearchParams(location.search).get("tab");
    tab = Math.max(0, D.maps.findIndex(m => m.key === want));
    const tabs = $("tabs"); tabs.innerHTML = "";
    D.maps.forEach((m, i) => {
      const b = document.createElement("button"); b.textContent = m.title;
      b.addEventListener("click", () => { tab = i; sel = null; view.scrollTo(0, 0); fitZoom(); openMap(); });
      tabs.appendChild(b);
    });
    $("folder").textContent = "placements.txt, ground.txt, the ROMs and the map guide are in:\n" + D.folder;
    const h = $("height");
    h.innerHTML = "<option value='auto'>automatic</option>";
    for (let e = 0; e < 16; e++) {
      const o = document.createElement("option"); o.value = String(e);
      o.textContent = e + ({0: " (stairs: joins any height)", 1: " (water)", 3: " (the ground)", 5: " (a terrace)",
                            7: " (a higher terrace)", 15: " (a bridge)"}[e] || "");
      h.appendChild(o);
    }
    if (D.start_problems.length)
      say("The files as they are cannot be used, so the map is shown as it was built.\n\n" +
          problems(D.start_problems), "bad");
    else say(HINTS[mode] + untidy(D.untidy) + (D.start_notes.length ? notes(
      ["placements.txt is from an older build. \"Save and rebuild\" writes it afresh with the new things in it:"]
        .concat(D.start_notes.map(n => "• " + n))) : ""));
    fitZoom();
  }
  openMap();
  if (!keep) {                              // (the address can ask for a mode and the marks: for pictures of the page)
    const q = new URLSearchParams(location.search);
    $("showwalk").checked = q.has("walls"); $("showheight").checked = q.has("heights");
    if (q.get("mode") === "ground") setMode("ground");
    if (q.get("demo")) {                    // ...and for an area copied and put down: demo=x0,y0,x1,y1,x,y
      const [x0, y0, x1, y1, x, y] = q.get("demo").split(",").map(Number), m = map(), cells = [];
      for (let j = y0; j <= y1; j++) cells.push(G[m.ground][j].slice(x0, x1 + 1).map(v => ({id: v & 0x3FF, exact: v})));
      setBrush({w: x1 - x0 + 1, h: y1 - y0 + 1, cells: cells});
      stroke = []; stamp(m, x, y); endStroke();
      view.scrollTo(x * 16 * Z - view.clientWidth / 2, y * 16 * Z - view.clientHeight / 2);
    }
  }
}
function openMap() {                        // the tab's map, afresh
  const m = map();
  locked = new Set(Object.keys(m.lockwhy));
  marks();
  $("paintui").style.display = m.paint ? "" : "none";
  $("tidyrow").style.display = m.tidy ? "" : "none";
  $("takerow").style.display = $("room").style.display = m.take ? "" : "none";
  $("beyondhint").style.display = m.beyond ? "" : "none";
  $("nopaint").textContent = m.paint ? "" : "Mossdeep City is the game's own map: its ground stays as it is. " +
    "Everything else can be painted.";
  if (m.paint && (!brush || brush.map !== m.key)) {
    setBrush({w: 1, h: 1, cells: [[{id: m.floor, exact: null}]]});
    brush.map = m.key;
  } else if (m.paint) drawPalettes();
  tile.style.display = "none"; box.style.display = "none";
  draw();
}
function fitZoom() {                        // the rooms are small: shown larger
  Z = map().w <= 27 ? 3 : 2; $("zoom").value = String(Z);
}
function marks() { [...$("tabs").children].forEach((b, i) => b.classList.toggle("on", i === tab)); }
function setMode(to) {
  mode = to;
  document.body.classList.toggle("ground", to === "ground");
  $("mthings").classList.toggle("on", to === "things"); $("mground").classList.toggle("on", to === "ground");
  $("whenlabel").style.display = to === "things" ? "" : "none";
  tile.style.display = "none"; box.style.display = "none";
  say(HINTS[to]);
  drawOver();
}
$("mthings").addEventListener("click", () => setMode("things"));
$("mground").addEventListener("click", () => setMode("ground"));
$("check").addEventListener("click", check);
$("apply").addEventListener("click", apply);
$("revert").addEventListener("click", () => {
  pos = clone(D.saved); G = groundFrom(D.saved_ground); T = clone(D.saved_tiles.crater || []);
  sel = null; undo = []; redo = []; buttons(); draw(); if (map().paint) drawPalettes();
  say("Back to what is saved.");
});
$("defaults").addEventListener("click", () => {
  pos = clone(D.defaults); G = groundFrom({}); T = [];
  sel = null; undo = []; redo = []; buttons(); draw(); if (map().paint) drawPalettes();
  say("Everything is back as the build first had it: where things stand, and the ground. Not saved until you " +
      "press \"Save and rebuild\".");
});
$("when").addEventListener("change", drawThings);
$("zoom").addEventListener("change", () => { Z = Number($("zoom").value); draw(); });
$("showwalk").addEventListener("change", drawOver);
$("showheight").addEventListener("change", drawOver);
$("walk").addEventListener("change", () => {});
$("undo").addEventListener("click", doUndo);
$("tidy").addEventListener("click", tidy);
$("redo").addEventListener("click", doRedo);
$("resetmap").addEventListener("click", () => {
  const m = map();
  if (!m.paint) return;
  stroke = [];
  const b = D.ground_base[m.ground], g = G[m.ground];
  for (let y = 0; y < m.h; y++) for (let x = 0; x < m.w; x++)
    if (g[y][x] !== b[y][x]) { stroke.push([m.ground, x, y, g[y][x], b[y][x]]); g[y][x] = b[y][x]; }
  const n = stroke.length;
  endStroke(); drawGround();
  say(n ? "This map's ground is as it was built again (" + n + " tiles). Ctrl+Z brings your painting back."
        : "Nothing is painted on this map.");
});
$("add").addEventListener("click", () => {
  const g = groupOf();
  if (!g) return;
  const m = map();
  const cx = Math.floor((view.scrollLeft + view.clientWidth / 2) / (16 * Z));
  const cy = Math.floor((view.scrollTop + view.clientHeight / 2) / (16 * Z));
  const taken = new Set(things().map(t => xyOf(t).join(",")));
  let best = null;
  for (let y = 0; y < m.h; y++) for (let x = 0; x < m.w; x++) {
    if (cell(m, x, y) !== "." || taken.has(x + "," + y)) continue;
    const d = Math.abs(x - cx) + Math.abs(y - cy);
    if (!best || d < best[0]) best = [d, x, y];
  }
  if (!best) return;
  pos[g.id].push([best[1], best[2]]);
  sel = g.id + "#" + (pos[g.id].length - 1); drawThings();
  say("A crystal was added at " + best[1] + ", " + best[2] + ". Drag it where you want it.");
});
$("remove").addEventListener("click", () => {
  const t = things().find(t => key(t) === sel);
  if (!t || t.k === null) return;
  pos[t.id].splice(t.k, 1); sel = null; drawThings();
});
$("quit").addEventListener("click", async () => {
  if (dirty() && !confirm("Your changes are not saved. Close anyway?")) return;
  await post("/quit", {});
  D = null;
  document.body.innerHTML = "<p style='padding:24px'>The editor is closed. You can close this tab.</p>";
});
window.addEventListener("beforeunload", ev => { if (D && dirty()) { ev.preventDefault(); ev.returnValue = ""; } });

// for trying the page out without a hand on the mouse: ?selftest moves a thing, paints and asks the server
const cell3 = (x, y) => G[map().ground][y][x] & 0x3FF;
window.__test = {move: (id, x, y) => { pos[id] = [x, y]; draw(); }, check: check, apply: apply, pos: () => pos,
                 diffs: diffs, tidy: tidy, taken: () => T,
                 // take an area of another map and put it down on the map that is open: for trying it without a mouse
                 take: async (g, n, x0, y0, x1, y1, x, y) => {
                   const m = await (await fetch("/source?g=" + g + "&n=" + n)).json();
                   if (!m.ok) return m;
                   LIB.map = m;
                   const r = await takeLib({x0: x0, y0: y0, x1: x1, y1: y1});
                   if (r && r.ok && x !== undefined) { stroke = []; stamp(map(), x, y); endStroke(); }
                   return r;
                 }};
load(false).then(async () => {
  if (!location.search.includes("selftest")) return;
  const out = document.createElement("pre"); out.id = "selftest"; document.body.appendChild(out);
  const lines = [];
  const go = k => { tab = D.maps.findIndex(m => m.key === k); fitZoom(); openMap(); };
  const pe = (el, type, x, y, more) => el.dispatchEvent(new PointerEvent(type, Object.assign(
    {bubbles: true, pointerId: 1, button: 0, buttons: 1, clientX: x, clientY: y}, more || {})));
  const at = (x, y) => { const r = stage.getBoundingClientRect(); return [r.left + (x + .5) * 16 * Z, r.top + (y + .5) * 16 * Z]; };
  try {
    lines.push("maps " + D.maps.length + " things " + D.maps.map(m => m.things.length + "+" +
      m.groups.map(g => pos[g.id].length).join("+")).join(","));
    lines.push("tiles " + D.maps.map(m => m.key + " " + m.onmap.length + "/" + m.tiles.length).join(", "));
    const before = clone(pos.walking_wake);
    window.__test.move("walking_wake", 32, 7);
    lines.push("bad: " + (await check()).length);
    window.__test.move("walking_wake", before[0], before[1]);
    lines.push("good: " + (await check()).length);
    // the mouse: take the first thing of the crater by its foot, let go two tiles right and one down
    go("past");
    const el = stage.querySelector(".thing"), r = el.getBoundingClientRect();
    const t0 = things().find(t => key(t) === el.dataset.key), was = xyOf(t0).slice();
    const cx = r.left + r.width / 2, cy = r.bottom - 4;
    pe(el, "pointerdown", cx, cy); pe(el, "pointermove", cx + 2 * 16 * Z, cy + 16 * Z); pe(el, "pointerup", cx + 2 * 16 * Z, cy + 16 * Z);
    lines.push("drag " + t0.label + " " + was + " -> " + xyOf(t0) + " picked " + sel);
    document.dispatchEvent(new KeyboardEvent("keydown", {key: "ArrowLeft"}));
    lines.push("arrow -> " + xyOf(t0));
    const n0 = pos.crystals.length;
    $("add").click(); const n1 = pos.crystals.length; $("remove").click();
    lines.push("crystals " + n0 + " +1 " + n1 + " -1 " + pos.crystals.length);
    $("revert").click();
    lines.push("undo -> " + xyOf(t0) + " unsaved: " + ($("dirty").textContent || "none"));
    // the ground: pick the boulder's kind of tile off the map, paint three tiles with it, take one stroke back
    setMode("ground");
    const m = map(), g = G[m.ground];
    let rock = null, grass = [];
    for (let y = 30; y < 46 && grass.length < 4; y++) for (let x = 36; x < 46 && grass.length < 4; x++)
      if (cell(m, x, y) === "." && cell(m, x + 1, y) === "." && !locked.has(x + "," + y)) grass.push([x, y]);
    for (let y = 0; y < m.h && !rock; y++) for (let x = 0; x < m.w && !rock; x++)
      if ((g[y][x] & 0x3FF) === D.rock.tile) rock = [x, y];
    lines.push("a boulder at " + rock + ", grass at " + grass.join(" "));
    let [px, py] = at(rock[0], rock[1]);
    pe(oc, "pointerdown", px, py, {button: 2, buttons: 2}); pe(oc, "pointerup", px, py, {button: 2, buttons: 0});
    lines.push("picked: " + $("brushtext").textContent.replace(/\n/g, " | "));
    [px, py] = at(grass[0][0], grass[0][1]);
    pe(oc, "pointerdown", px, py); pe(oc, "pointerup", px, py, {buttons: 0});
    [px, py] = at(grass[1][0], grass[1][1]);
    pe(oc, "pointerdown", px, py); pe(oc, "pointerup", px, py, {buttons: 0});
    lines.push("painted: " + JSON.stringify(diffs()) + " dirty: " + ($("dirty").textContent || "none"));
    document.dispatchEvent(new KeyboardEvent("keydown", {key: "z", ctrlKey: true}));
    lines.push("after Ctrl+Z: " + JSON.stringify(diffs()));
    lines.push("check with a rock on the grass: " + (await check()).length);
    // an area: copy 2 x 2 from the map and stamp it; a box filled with a tile from the list
    [px, py] = at(rock[0], rock[1]);
    const [qx, qy] = at(rock[0] + 1, rock[1] + 1);
    pe(oc, "pointerdown", px, py, {button: 2, buttons: 2}); pe(oc, "pointermove", qx, qy, {button: 2, buttons: 2});
    pe(oc, "pointerup", qx, qy, {button: 2, buttons: 0});
    lines.push("area: " + brush.w + "x" + brush.h + " " + $("brushtext").textContent);
    const c1 = $("pal1"), cr = c1.getBoundingClientRect();
    c1.dispatchEvent(new MouseEvent("click", {bubbles: true, clientX: cr.left + 5, clientY: cr.top + 5}));
    lines.push("from the list: " + $("brushtext").textContent.replace(/\n/g, " | "));
    [px, py] = at(grass[2][0], grass[2][1]);
    const [fx, fy] = at(grass[2][0] + 1, grass[2][1]);
    pe(oc, "pointerdown", px, py, {shiftKey: true}); pe(oc, "pointermove", fx, fy, {shiftKey: true});
    pe(oc, "pointerup", fx, fy, {buttons: 0, shiftKey: true});
    lines.push("box: " + JSON.stringify(diffs()));
    // a door stays as it is
    const d = m.doors[0];
    [px, py] = at(d[0], d[1]);
    const n = undo.length;
    pe(oc, "pointerdown", px, py); pe(oc, "pointerup", px, py, {buttons: 0});
    lines.push("a door at " + d + " painted? " + (undo.length > n));
    $("revert").click();
    lines.push("back to saved: " + JSON.stringify(diffs()));
    // edges that do not fit: an old corner piece on a terrace's corner, a path's border in its middle
    let corner = null, path = null;
    const now = G[m.ground];
    for (let y = 0; y < m.h && !(corner && path); y++) for (let x = 0; x < m.w; x++) {
      if (!corner && (now[y][x] & 0x3FF) === 108) corner = [x, y];
      if (!path && (now[y][x] & 0x3FF) === 473) path = [x, y];
    }
    stroke = [];
    put(m, corner[0], corner[1], 136 | 1 << 10 | 1 << 12); put(m, path[0], path[1], now[path[1]][path[0]] & 0xFC00 | 481);
    endStroke();
    const said = await check();
    lines.push("a wrong corner at " + corner + " and a wrong border at " + path + ": problems " + said.length +
               ", told: " + /do not fit/.test($("msg").textContent));
    await tidy();
    lines.push("after Tidy the edges: " + JSON.stringify(diffs()) + " | " + $("msg").textContent.slice(0, 40));
    $("revert").click();
    // tiles of another map: the list, a place by its name, a box dragged on its picture, the button; the brush
    // put down on the crater; the taken tiles in the list; the ones not painted with removed again
    go("past"); setMode("ground");
    await openLib();
    lines.push("take: " + LIB.list.length + " places, open " + $("lib").classList.contains("on") + ", shown " +
               LIB.map.g + "/" + LIB.map.n);
    $("libq").value = "koga"; fillLib(); await pickLib();
    lines.push("\"koga\": " + $("libsel").options.length + " place(s), " + LIB.map.g + "/" + LIB.map.n + " " +
               LIB.map.w + "x" + LIB.map.h + ", picture " + $("libc").width + "x" + $("libc").height);
    const lc = $("libc"), lr = lc.getBoundingClientRect(), lz = Number($("libzoom").value) * 16;
    pe(lc, "pointerdown", lr.left + 13.5 * lz, lr.top + 1.5 * lz);
    pe(lc, "pointermove", lr.left + 17.5 * lz, lr.top + 4.5 * lz);
    pe(lc, "pointerup", lr.left + 17.5 * lz, lr.top + 4.5 * lz, {buttons: 0});
    lines.push("the box: " + JSON.stringify(LIB.sel) + ", the button on: " + !$("libtake").disabled);
    const tk = await takeLib();
    lines.push("taken: ok " + tk.ok + ", new " + tk.new.length + ", in all " + T.length + ", brush " + brush.w + "x" +
               brush.h + ", closed " + !$("lib").classList.contains("on") + ", list shown " +
               ($("pal3").style.display !== "none") + " | " + $("room").textContent);
    const spot = location.search.match(/spot=(\d+),(\d+)/), sx = spot ? +spot[1] : 24, sy = spot ? +spot[2] : 24;
    [px, py] = at(sx, sy);
    pe(oc, "pointerdown", px, py); pe(oc, "pointerup", px, py, {buttons: 0});
    const put1 = Object.keys(diffs().crater || {}).length;
    lines.push("put down at " + sx + "," + sy + ": " + put1 + " tiles painted in all, the tile there " +
               (cell3(sx, sy)) + ", check: " + (await check()).length + " problem(s)");
    const again = await window.__test.take(35, 45, 13, 1, 17, 4);
    lines.push("the same box again: new " + again.new.length + ", in all " + T.length);
    const more = await window.__test.take(0, 4, 0, 0, 10, 8);
    lines.push("a corner of Fortree: ok " + more.ok + ", new " + (more.new || []).length + ", in all " + T.length +
               " | " + $("room").textContent);
    $("libprune").click();
    lines.push("not painted with, removed: in all " + T.length + " | " + $("msg").textContent.slice(0, 60));
    if (!location.search.includes("apply")) {
      $("revert").click();
      lines.push("back to saved: taken " + T.length + ", painted " + JSON.stringify(diffs()) + ", unsaved: " +
                 ($("dirty").textContent || "none"));
    }
    if (location.search.includes("apply")) {
      [px, py] = at(grass[0][0], grass[0][1]);
      pe(oc, "pointerdown", rock[0] * 0 + at(rock[0], rock[1])[0], at(rock[0], rock[1])[1], {button: 2, buttons: 2});
      pe(oc, "pointerup", at(rock[0], rock[1])[0], at(rock[0], rock[1])[1], {button: 2, buttons: 0});
      pe(oc, "pointerdown", px, py); pe(oc, "pointerup", px, py, {buttons: 0});
      setMode("things");
      const a0 = D.saved.arven.slice();           // (a step west, if he can stand there as the ground is now)
      window.__test.move("arven", a0[0] - 1, a0[1]);
      if ((await check()).length) window.__test.move("arven", a0[0], a0[1]);
      const r2 = await apply();
      lines.push("apply ok " + r2.ok + " | " + r2.lines.join(" / ") +
                 (r2.problems.length ? " | refused: " + r2.problems.join(" / ") : ""));
      lines.push("saved arven " + D.saved.arven.join(",") + " ground " +
                 Object.keys(D.saved_ground.crater || {}).length + " tile(s), taken " + D.saved_tiles.crater.length +
                 " | " + D.room + " | in the list: " + D.maps.filter(m => m.take).map(m => m.taken.length).join(","));
    }
    // past the edge: the page's rule gives the tiles of the strips the build made, in both craters; painting
    // the map's corner changes the band
    for (const k of ["past", "future"]) {
      go(k);
      const m2 = map(), b = m2.beyond;
      let n2 = 0, wrong = 0;
      const hold = (rows, x0, y0) => rows.forEach((row, j) => row.forEach((v, i) => {
        n2++; if ((v & 0x3FF) !== (beyondBlock(m2, x0 + i, y0 + j) & 0x3FF)) wrong++; }));
      hold(b.north, -7, -7); hold(b.south, -7, m2.h); hold(b.west, -7, 0); hold(b.east, m2.w, 0);
      lines.push("past the edge, " + k + ": " + n2 + " tiles, " + wrong + " differ; band " + bc.style.display +
                 " " + bc.width + "x" + bc.height + " at " + bc.style.left);
    }
    setMode("ground");
    const m3 = map(), was3 = beyondBlock(m3, -1, -1);
    stroke = []; put(m3, 1, 1, D.rock.tile | 1 << 10 | 3 << 12); endStroke();
    lines.push("the corner painted: the band's corner " + was3 + " -> " + beyondBlock(m3, -1, -1));
    $("revert").click();
    go("wall");
    lines.push("the wall has no band: " + bc.style.display + ", margin " + stage.style.margin);
    // for a picture of the page (&shot=lib: the other map open with a box on it; &shot=paint: its house put down)
    const shot = (location.search.match(/shot=(\w+)/) || [])[1];
    if (shot) {
      go("past"); setMode("ground");
      await openLib();
      $("libq").value = "koga"; fillLib(); await pickLib();
      LIB.sel = {x0: 13, y0: 1, x1: 17, y1: 4}; showLibBox();
      if (shot === "paint") {
        await takeLib(); stroke = []; stamp(map(), 24, 24); endStroke();
        out.style.display = "none";
        view.scrollTo(24 * 16 * Z - view.clientWidth / 2, 26 * 16 * Z - view.clientHeight / 2);
      }
    }
    lines.push("SELFTEST DONE");
  } catch (e) { lines.push("SELFTEST ERROR " + e + " " + (e.stack || "")); }
  out.textContent = lines.join("\n");
  document.title = lines[lines.length - 1];
});
</script>
</body></html>
"""


class Server(http.server.ThreadingHTTPServer):
    """Listens on a port nobody else has. (Python's servers ask to "reuse" their address, and on Windows that
    lets two programs listen on one port, each getting some of the requests: an editor started while another was
    open answered the first one's page with its own folder's map.)"""
    allow_reuse_address = False

    def server_bind(self):
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


def main(folder, emulators=True):
    print("Area Zero editor")
    print("Reading the positions and the ground, and drawing the maps...")
    ed = Editor(folder, emulators)
    server = None
    for port in PORTS:
        try:
            server = Server(("127.0.0.1", port), None)
            break
        except OSError:
            continue
    if server is None:
        print("No free port between %d and %d." % (PORTS[0], PORTS[-1]))
        return 1
    server.RequestHandlerClass = handler(ed, server.shutdown)
    url = "http://127.0.0.1:%d/" % server.server_address[1]
    print("The editor is open at %s" % url)
    print("Leave this window open while you use it; close it (or press \"Close the editor\") when you are done.")
    if "--no-browser" not in sys.argv:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    sys.exit(main(args[0] if args else RB.FOLDER, "--here" not in sys.argv))
