"""The Kitakami editor: move its people, signs and the story's places with the mouse.
python -I editor.py [folder] [--here] [--no-browser]
       (the folder: gba-trans/hyper-emerald/roms/test-kitakami unless named; --here: krebuild's; --no-browser: only serve)

The user, 2026-10-17, on Kitakami test 6: "I want to edit placement myself". placements.txt (kplaces.py) is the
answer in text; this is that file with a mouse, as Area Zero's editor (patches/paldea/editor.py) is for Area Zero.
It serves one page to the browser on this PC only (127.0.0.1): every Kitakami map drawn from its tiles as the game
draws it, everything of placements.txt on it as its own sprite.

  Move things     drag a person, a sign or a place, or pick it (on the map or in the list) and use the arrow keys;
                  R turns a person round. The list says where each thing is, and which are not where they were saved.
  Who is there    "Show who is there at" picks a moment of the story: only what is there then is drawn. Carmine
                  and Kieran stand somewhere else at every step of the story; each place is a line of its own.
  Check           builds the game in a temporary folder and runs every check a build runs (kpeople.layout_report):
                  nobody in a wall, in a doorway, on someone else, in the way, out of reach, and the scenes' walks
                  on open ground.
  Save and        writes placements.txt and makes "Hyper Emerald - Kitakami (my placements N).gba" with its save
  rebuild         (krebuild.py). "Play it" opens it in tools/pc_mgba.

Nothing is written before "Save and rebuild". Close the console window to stop.
"""
import base64, http.server, io, json, os, socket, struct, sys, tempfile, threading, urllib.parse, webbrowser

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "paldea"))
import kplaces as KPL
import krebuild as KR
import kitakami_patch as KT
import kstory as KS
import ksprites as KSP
import kchapters as KC
import kart

PORTS = range(8766, 8776)                               # (Area Zero's editor takes 8756-8765)
TABS = [("mossui", "Mossui Town"), ("hall", "Kitakami Hall"), ("family", "Carmine and Kieran's house"),
        ("home1", "the old woman's house"), ("home2", "the old couple's house")]


def png(arr):
    from PIL import Image
    b = io.BytesIO()
    Image.fromarray(arr).save(b, "PNG")
    return b.getvalue()


def sprite_of(tid):
    """(gfx, ext, animation frames) a thing is drawn with in the game, or None (a sign, a board, a place)"""
    kind = KPL.KIND_OF[tid]
    if kind in ("sign", "board", "spot"):
        return None
    who = tid
    main = {"p2_arven": 67, "p2_penny": 70, "p2_grandpa": 29, "p2_grandma": 22}   # Part 2's in the game's own sprites
    for pre, gfx in main.items():
        if tid.startswith(pre):
            return gfx, 0
    az = {"p2_nemona": "az_nemona"}                                                 # in Area Zero's own
    for pre, key in az.items():
        if tid.startswith(pre):
            return KS.EXT, KSP.slot(key)
    if tid.startswith("p2_kieran"):
        who = "kieran"
    elif tid.startswith("p2_carmine"):
        who = "carmine"
    elif tid.startswith("p2_pech"):
        who = "pecharunt"
    elif tid.startswith("carmine_") or tid == "home_carmine":
        who = "carmine"
    elif tid.startswith("kieran_"):
        who = "kieran"
    elif tid in ("ogerpon", "ogerpon_fest"):
        who = "ogerpon"
    if who in ("briar", "carmine", "kieran") or who in KSP.STATUES or who in KSP.LIVE:
        return KS.EXT, KSP.slot(who)
    return KS.GFX[who], 0


def frames(rom, gfx, ext):
    """The pictures of an object facing down, up and left (right is left turned over), RGBA; frames the sprite does
    not have are its first one."""
    import numpy as np
    R = rom
    info = (R.u32(0x014A2C10) - 0x08000000 + 0x24 * ext) if gfx == 0x4E else R.u32(0x00505620 + 4 * gfx) - 0x08000000
    tag = R.u16(info + 2)
    w, h = struct.unpack_from("<hh", R.rom, info + 8)
    table = R.u32(info + 0x1C) - 0x08000000
    pal = R.pals.get(tag)
    size = w * h // 2

    def pic(k):
        ptr, n = struct.unpack_from("<II", R.rom, table + 8 * k)
        if not (0x08000000 <= ptr < 0x0A000000 and n == size):
            ptr = R.u32(table)
        fp = ptr - 0x08000000
        px = np.zeros((h, w, 4), np.uint8)
        for t in range((w // 8) * (h // 8)):
            tx, ty = t % (w // 8), t // (w // 8)
            for yy in range(8):
                for xx in range(8):
                    b = R.rom[fp + t * 32 + yy * 4 + xx // 2]
                    c = (b >> 4) if xx & 1 else (b & 15)
                    if c and pal:
                        v = pal[c]
                        px[ty * 8 + yy, tx * 8 + xx] = ((v & 31) * 8, (v >> 5 & 31) * 8, (v >> 10 & 31) * 8, 255)
        return px
    down, up, left = pic(0), pic(1), pic(2)
    return {"down": down, "up": up, "left": left, "right": left[:, ::-1].copy()}, w, h


def kart_picture(pic):
    import numpy as np
    h, w = len(pic), len(pic[0])
    out = np.zeros((h, w, 4), np.uint8)
    for y in range(h):
        for x in range(w):
            c = pic[y][x]
            if c:
                out[y, x] = kart.COLOURS[c] + (255,)
    return out


class Editor:
    def __init__(self, folder, emulators=True):
        self.folder = os.path.abspath(folder)
        self.emulators = emulators
        self.file = os.path.join(self.folder, "placements.txt")
        self.lock = threading.Lock()
        self.tmp = tempfile.mkdtemp(prefix="kitakami_editor_")
        self.images, self.data, self.last_rom = {}, {}, None
        self.start_problems = []
        try:
            self.saved = KPL.load(self.file) if os.path.exists(self.file) else KPL.Values(KPL.DEFAULTS)
            self.start_notes = list(self.saved.notes)
        except KPL.PlacementError as e:
            self.start_problems = [str(e)]
            self.saved, self.start_notes = KPL.Values(KPL.DEFAULTS), []
        self.survey()
        if not self.start_problems:
            self.start_problems = self.check({"placements": self.as_raw(self.saved)})["problems"]

    def as_raw(self, values):
        return {k: list(v) for k, v in values.items()}

    def values_from(self, raw):
        """The page's positions, checked for shape: {id: (x, y) or (x, y, facing)}."""
        out = KPL.Values(KPL.DEFAULTS)
        for tid, v in (raw or {}).items():
            if tid not in KPL.DEFAULTS:
                continue
            x, y = int(v[0]), int(v[1])
            if tid in KPL.FACES:
                face = v[2] if len(v) > 2 and v[2] in KPL.FACINGS else KPL.DEFAULTS[tid][2]
                out[tid] = (x, y, face)
            else:
                out[tid] = (x, y)
        return out

    def build(self, values, signs=True, name="check"):
        """A ROM in the temporary folder from these positions; what kitakami_patch told."""
        import contextlib
        f = os.path.join(self.tmp, name + ".txt")
        with open(f, "w", encoding="utf-8", newline="\n") as h:
            h.write(KPL.text(values))
        rom, told = os.path.join(self.tmp, name + ".gba"), {}
        with contextlib.redirect_stdout(io.StringIO()):
            KT.build(KR.base_rom(), rom, f, told, signs)
        return rom, told

    def survey(self):
        """The page's pictures: every map's ground (without the town's signs, which are drawn as things), every
        sprite in every facing, the sign and the signboard."""
        import map_guide as MG
        rom_path, told = self.build(KPL.Values(KPL.DEFAULTS), signs=False, name="view")
        rom = MG.Rom(rom_path)
        images, maps = {}, []
        for key, title in TABS:
            m = told["maps"][key]
            g, n = m["map"]
            images["ground_" + key] = png(rom.ground(g, n))
            maps.append({"key": key, "title": title, "w": m["w"], "h": m["h"], "img": "ground_" + key,
                         "things": [t[0] for t in KPL.THINGS if KPL.MAP_OF[t[1]] == key]})
        lay = rom.R.Layout(rom.R.ptr(rom.R.header(*told["maps"]["mossui"]["map"])))
        import numpy as np
        sign = np.zeros((16, 16, 4), np.uint8)
        sign[:, :, :3] = lay.metatile(KT.WD.SIGN)
        sign[:, :, 3] = 255
        images["sign"] = png(sign)
        images["board"] = png(kart_picture(kart.legend_board()))
        things, drawn = {}, {}
        for tid, sec, name, kind, when, default, note in KPL.THINGS:
            e = {"id": tid, "map": KPL.MAP_OF[sec], "section": sec, "sectionTitle": KPL.TITLE_OF[sec], "name": name,
                 "kind": kind, "when": list(when), "note": note, "faces": tid in KPL.FACES, "sprite": None,
                 "sw": 16, "sh": 16}
            sp = sprite_of(tid)
            if sp:
                if sp not in drawn:
                    pics, w, h = frames(rom, *sp)
                    for face, arr in pics.items():
                        images["s_%d_%d_%s" % (sp[0], sp[1], face)] = png(arr)
                    drawn[sp] = (w, h)
                e["sprite"] = "s_%d_%d" % sp
                e["sw"], e["sh"] = drawn[sp]
            elif kind == "board":
                e["sprite"], e["sw"], e["sh"] = "board", 16, 32
            elif kind == "sign":
                e["sprite"] = "sign"
            things[tid] = e
        self.images = images
        self.data = {"maps": maps, "things": things, "order": [t[0] for t in KPL.THINGS],
                     "moments": KPL.MOMENTS, "folder": self.folder, "facings": list(KPL.FACINGS)}

    def check(self, raw):
        with self.lock:
            try:
                values = self.values_from(raw.get("placements"))
                self.build(values)
                return {"problems": []}
            except KT.Problems as e:
                return {"problems": e.lines}

    def apply(self, raw):
        with self.lock:
            values = self.values_from(raw.get("placements"))
            try:
                self.build(values)
            except KT.Problems as e:
                return {"ok": False, "problems": e.lines, "lines": []}
            with open(self.file, "w", encoding="utf-8", newline="\n") as h:
                h.write(KPL.text(values))
            lines = []
            rom = KR.rebuild(self.folder, say=lines.append, emulators=self.emulators)
            if rom:
                self.saved = values
                self.last_rom = rom
            return {"ok": bool(rom), "problems": [], "lines": lines, "rom": os.path.basename(rom) if rom else None}

    def play(self, which=None):
        rom = self.last_rom
        if not rom:
            import glob
            mine = [f for f in glob.glob(os.path.join(self.folder, "*.gba")) if KR.MINE.search(os.path.basename(f))]
            rom = max(mine, key=os.path.getmtime) if mine else None
        if not rom:
            return {"ok": False, "lines": ["Nothing has been built yet: press \"Save and rebuild\" first."]}
        if which == "p2":                                   # the same build from the Part 2 start save
            rom = rom[:-4] + KR.P2 + ".gba"
            if not os.path.exists(rom):
                return {"ok": False, "lines": ["This build has no Part 2 start copy (there is no \"(Part 2 start)\" "
                                               "save in the folder)."]}
        ok = KR.play(rom)
        return {"ok": ok, "lines": ["Opened %s in mGBA (tools/pc_mgba)." % os.path.basename(rom) if ok else
                                    "tools/pc_mgba/mGBA.exe is not there: open %s yourself." % os.path.basename(rom)]}

    def state(self):
        d = dict(self.data)
        d["saved"] = self.as_raw(self.saved)
        d["defaults"] = self.as_raw(KPL.DEFAULTS)
        d["start_problems"] = self.start_problems
        d["start_notes"] = self.start_notes
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
            elif path.startswith("/img/") and path[5:-4] in ed.images:
                self.send(ed.images[path[5:-4]], "image/png")
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
                elif self.path == "/play":
                    self.send(ed.play(raw.get("which")))
                elif self.path == "/quit":
                    self.send({"ok": True})
                    threading.Thread(target=stop, daemon=True).start()
                else:
                    self.send({"error": "not found"}, code=404)
            except Exception as e:                            # anything else: tell the page, keep serving
                self.send({"ok": False, "problems": ["The editor ran into an error: %r" % (e,)], "lines": []})
    return H


PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Kitakami editor</title>
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; }
  body { margin: 0; font: 14px/1.4 "Segoe UI", Arial, sans-serif; background: #14161c; color: #e6e8ee;
         display: grid; grid-template-rows: auto auto 1fr; height: 100vh; }
  header { padding: 8px 14px; background: #1d2029; border-bottom: 1px solid #333846; display: flex; gap: 10px;
           align-items: center; flex-wrap: wrap; }
  header h1 { font-size: 16px; margin: 0 8px 0 0; color: #7fe0c8; }
  button { background: #2b3040; color: #e6e8ee; border: 1px solid #454b5e; border-radius: 6px; padding: 5px 12px;
           font: inherit; cursor: pointer; }
  button:hover { background: #363c50; }
  button.main { background: #1f6f5c; border-color: #2c9c80; }
  button.main:hover { background: #26876f; }
  button:disabled { opacity: .5; cursor: default; }
  select { background: #2b3040; color: #e6e8ee; border: 1px solid #454b5e; border-radius: 6px; padding: 4px 6px;
           font: inherit; }
  #status { color: #aab0c0; }
  nav { display: flex; gap: 2px; padding: 6px 14px 0; background: #1d2029; border-bottom: 1px solid #333846; }
  nav button { border-radius: 6px 6px 0 0; border-bottom: none; background: #232734; }
  nav button.on { background: #14161c; color: #7fe0c8; }
  main { display: grid; grid-template-columns: 1fr 380px; min-height: 0; }
  #view { overflow: auto; position: relative; background: #0b0c10; }
  #map { position: relative; image-rendering: pixelated; background-repeat: no-repeat; background-size: 100% 100%;
         margin: 12px; }
  .thing { position: absolute; image-rendering: pixelated; cursor: grab; }
  .thing.sel { outline: 2px solid #ffd257; outline-offset: 1px; z-index: 5; }
  .thing.faded { opacity: .12; pointer-events: none; }
  .spot { border: 2px dashed #ffd257; background: rgba(255, 210, 87, .25); color: #ffd257; font-size: 10px;
          font-weight: bold; display: flex; align-items: center; justify-content: center; }
  .tag { position: absolute; font-size: 10px; background: rgba(0, 0, 0, .7); color: #fff; padding: 0 3px;
         border-radius: 3px; pointer-events: none; white-space: nowrap; z-index: 6; }
  #hover { position: absolute; border: 1px solid rgba(255, 255, 255, .6); pointer-events: none; z-index: 4; }
  aside { border-left: 1px solid #333846; overflow: auto; padding: 10px 12px; background: #181a22; }
  aside h2 { font-size: 13px; text-transform: uppercase; letter-spacing: .04em; color: #8a91a6; margin: 14px 0 6px; }
  .row { display: grid; grid-template-columns: 1fr auto; gap: 6px; padding: 3px 6px; border-radius: 5px;
         cursor: pointer; }
  .row:hover { background: #232734; }
  .row.sel { background: #2c3346; }
  .row.gone { color: #5d6377; }
  .row .xy { color: #9aa2b6; font-variant-numeric: tabular-nums; }
  .row.moved .xy { color: #ffd257; }
  #detail { background: #20242f; border: 1px solid #333846; border-radius: 8px; padding: 10px; margin-bottom: 8px; }
  #detail .name { font-weight: bold; font-size: 15px; }
  #detail .note { color: #aab0c0; margin: 4px 0; }
  #detail label { margin-right: 10px; }
  #detail input { width: 56px; background: #2b3040; color: #e6e8ee; border: 1px solid #454b5e; border-radius: 5px;
                  padding: 3px 5px; font: inherit; }
  #out { white-space: pre-wrap; background: #101218; border: 1px solid #333846; border-radius: 8px; padding: 8px;
         font-size: 13px; max-height: 260px; overflow: auto; }
  #out .bad { color: #ff9a8a; }
  #out .good { color: #8ee0a8; }
  .help { color: #8a91a6; font-size: 12px; }
</style></head><body>
<header>
  <h1>Kitakami editor</h1>
  <button id="check">Check</button>
  <button id="apply" class="main">Save and rebuild</button>
  <button id="play">Play it</button>
  <button id="play2">Play from Part 2 start</button>
  <button id="revert">Back to what is saved</button>
  <button id="builtin">The built-in places</button>
  <label>Show who is there at <select id="moment"></select></label>
  <label>Size <select id="zoom"><option>1</option><option selected>2</option><option>3</option><option>4</option></select></label>
  <span id="status"></span>
</header>
<nav id="tabs"></nav>
<main>
  <div id="view"><div id="map"><div id="hover"></div></div></div>
  <aside>
    <div id="detail">Pick something on the map or in the list.</div>
    <div class="help">Drag a thing to move it, or pick it and use the arrow keys. R turns a person round.
      Nothing is written until "Save and rebuild".</div>
    <h2>What the checks say</h2>
    <div id="out">...</div>
    <h2>On this map</h2>
    <div id="list"></div>
  </aside>
</main>
<pre id="selftest" style="display:none"></pre>
<script>
"use strict";
let D = null, pos = {}, saved = {}, tab = "mossui", sel = null, zoom = 2, moment = "", drag = null, busy = false;
const $ = id => document.getElementById(id);
const T = 16;
function say(lines, cls) {
  const out = $("out"); out.innerHTML = "";
  for (const l of lines) { const d = document.createElement("div"); if (cls) d.className = cls; d.textContent = l; out.appendChild(d); }
}
function status(s) { $("status").textContent = s; }
function there(t) { return !moment || D.things[t].when.includes(moment); }
function same(a, b) { return a && b && a.length === b.length && a.every((v, i) => v === b[i]); }
async function load() {
  D = await (await fetch("/data")).json();
  saved = JSON.parse(JSON.stringify(D.saved)); pos = JSON.parse(JSON.stringify(D.saved));
  $("moment").innerHTML = '<option value="">everything at once</option>' +
    D.moments.map(m => '<option value="' + m[0] + '">' + m[1] + '</option>').join("");
  $("tabs").innerHTML = "";
  for (const m of D.maps) {
    const b = document.createElement("button"); b.textContent = m.title; b.dataset.key = m.key;
    b.onclick = () => { tab = m.key; sel = null; draw(); }; $("tabs").appendChild(b);
  }
  const lines = [];
  for (const n of D.start_notes) lines.push(n);
  if (D.start_problems.length) {
    say(["placements.txt as it is now would not work:"].concat(D.start_problems.map(p => "  - " + p)), "bad");
  } else say(lines.concat(["Everything where it is saved works in the game."]), "good");
  draw();
}
function mapOf(key) { return D.maps.find(m => m.key === key); }
function box(t) {
  const e = D.things[t], p = pos[t];
  if (e.kind === "board") return [p[0] * T, (p[1] - 1) * T, 16, 32];
  if (e.kind === "sign" || e.kind === "spot") return [p[0] * T, p[1] * T, 16, 16];
  return [p[0] * T + 8 - e.sw / 2, p[1] * T + 16 - e.sh, e.sw, e.sh];
}
function draw() {
  for (const b of $("tabs").children) b.classList.toggle("on", b.dataset.key === tab);
  const m = mapOf(tab), map = $("map");
  map.style.width = m.w * T * zoom + "px"; map.style.height = m.h * T * zoom + "px";
  map.style.backgroundImage = "url(/img/" + m.img + ".png)";
  for (const el of [...map.querySelectorAll(".thing,.tag")]) el.remove();
  const order = m.things.slice().sort((a, b) => pos[a][1] - pos[b][1]);
  for (const t of order) {
    const e = D.things[t], [x, y, w, h] = box(t);
    let el;
    if (e.kind === "spot") {
      el = document.createElement("div"); el.className = "thing spot"; el.textContent = "⚑";
    } else {
      el = document.createElement("img");
      const face = e.faces ? pos[t][2] : "down";
      el.src = "/img/" + (e.kind === "sign" || e.kind === "board" ? e.sprite : e.sprite + "_" + face) + ".png";
      el.className = "thing"; el.draggable = false;
    }
    el.style.left = x * zoom + "px"; el.style.top = y * zoom + "px";
    el.style.width = w * zoom + "px"; el.style.height = h * zoom + "px";
    if (!there(t)) el.classList.add("faded");
    if (t === sel) el.classList.add("sel");
    el.title = e.name + " (" + pos[t][0] + ", " + pos[t][1] + ")";
    el.onpointerdown = ev => { ev.preventDefault(); pick(t); drag = {t: t}; map.setPointerCapture(ev.pointerId); };
    map.appendChild(el);
    if (t === sel || (moment && there(t))) {
      const tag = document.createElement("div"); tag.className = "tag"; tag.textContent = e.name;
      tag.style.left = x * zoom + "px"; tag.style.top = (y * zoom - 14) + "px"; map.appendChild(tag);
    }
  }
  list(); detail();
}
function list() {
  const m = mapOf(tab); let html = "", sec = null;
  for (const t of m.things) {
    const e = D.things[t];
    if (e.sectionTitle !== sec) { sec = e.sectionTitle; html += "<h2>" + sec + "</h2>"; }
    const p = pos[t], moved = !same(p, saved[t]);
    html += '<div class="row' + (t === sel ? " sel" : "") + (there(t) ? "" : " gone") + (moved ? " moved" : "") +
      '" data-t="' + t + '"><span>' + e.name + '</span><span class="xy">' + p[0] + ", " + p[1] +
      (e.faces ? ", " + p[2] : "") + (moved ? " •" : "") + "</span></div>";
  }
  $("list").innerHTML = html;
  for (const r of $("list").querySelectorAll(".row")) r.onclick = () => { pick(r.dataset.t); scrollTo(r.dataset.t); };
}
function detail() {
  const d = $("detail");
  if (!sel) { d.textContent = "Pick something on the map or in the list."; return; }
  const e = D.things[sel], p = pos[sel];
  const names = Object.fromEntries(D.moments);
  const when = e.when.length === D.moments.length ? "the whole story" : e.when.map(w => names[w]).join("; ");
  d.innerHTML = '<div class="name"></div><div class="note"></div><div class="note when"></div>' +
    '<label>x <input id="dx" type="number"></label><label>y <input id="dy" type="number"></label>' +
    (e.faces ? '<label>facing <select id="df">' + D.facings.map(f => "<option>" + f + "</option>").join("") +
      "</select></label>" : "") + ' <button id="dback">As saved</button>';
  d.querySelector(".name").textContent = e.name;
  d.querySelector(".note").textContent = e.note || "";
  d.querySelector(".when").textContent = "There at: " + when;
  $("dx").value = p[0]; $("dy").value = p[1];
  $("dx").onchange = () => set(sel, +$("dx").value, p[1]);
  $("dy").onchange = () => set(sel, p[0], +$("dy").value);
  if (e.faces) { $("df").value = p[2]; $("df").onchange = () => { pos[sel][2] = $("df").value; draw(); }; }
  $("dback").onclick = () => { pos[sel] = saved[sel].slice(); draw(); };
}
function pick(t) {
  sel = t; const e = D.things[t];
  if (e.map !== tab) tab = e.map;
  if (moment && !there(t)) moment = "";
  $("moment").value = moment; draw();
}
function scrollTo(t) {
  const [x, y] = box(t), v = $("view");
  v.scrollLeft = x * zoom - v.clientWidth / 2; v.scrollTop = y * zoom - v.clientHeight / 2;
}
function set(t, x, y) {
  const m = mapOf(D.things[t].map);
  x = Math.max(0, Math.min(m.w - 1, x)); y = Math.max(0, Math.min(m.h - 1, y));
  if (pos[t][0] === x && pos[t][1] === y) return;
  pos[t][0] = x; pos[t][1] = y; draw();
}
function tileAt(ev) {
  const r = $("map").getBoundingClientRect();
  return [Math.floor((ev.clientX - r.left) / (T * zoom)), Math.floor((ev.clientY - r.top) / (T * zoom))];
}
$("map").onpointermove = ev => {
  const [x, y] = tileAt(ev), h = $("hover"), m = mapOf(tab);
  if (x >= 0 && y >= 0 && x < m.w && y < m.h) {
    h.style.display = "block"; h.style.left = x * T * zoom + "px"; h.style.top = y * T * zoom + "px";
    h.style.width = h.style.height = T * zoom + "px"; status("tile " + x + ", " + y);
  } else h.style.display = "none";
  if (drag) set(drag.t, x, y);
};
$("map").onpointerup = () => { drag = null; };
document.onkeydown = ev => {
  if (!sel || ev.target.tagName === "INPUT" || ev.target.tagName === "SELECT") return;
  const p = pos[sel], k = ev.key;
  const step = {ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1]}[k];
  if (step) { ev.preventDefault(); set(sel, p[0] + step[0], p[1] + step[1]); }
  else if ((k === "r" || k === "R") && D.things[sel].faces) {
    const f = ["down", "left", "up", "right"]; p[2] = f[(f.indexOf(p[2]) + 1) % 4]; draw();
  }
};
$("moment").onchange = () => { moment = $("moment").value; draw(); };
$("zoom").onchange = () => { zoom = +$("zoom").value; draw(); };
$("revert").onclick = () => { pos = JSON.parse(JSON.stringify(saved)); draw(); say(["Everything is back where it is saved."]); };
$("builtin").onclick = () => {
  pos = JSON.parse(JSON.stringify(D.defaults)); draw();
  say(["Everything is where the build puts it when there is no placements.txt. Nothing is written until \"Save and rebuild\"."]);
};
async function post(url, body) {
  const r = await fetch(url, {method: "POST", body: JSON.stringify(body || {})}); return r.json();
}
function lock(on, what) { busy = on; for (const b of ["check", "apply", "play", "play2"]) $(b).disabled = on; status(on ? what : ""); }
$("check").onclick = async () => {
  if (busy) return; lock(true, "Checking...");
  const r = await post("/check", {placements: pos}); lock(false);
  if (r.problems.length) say(["Not yet: " + r.problems.length + " thing" + (r.problems.length > 1 ? "s" : "") +
    " to put right."].concat(r.problems.map(p => "  - " + p)), "bad");
  else say(["Everything works: nobody in a wall, a doorway or the way, at any moment of the story."], "good");
};
$("apply").onclick = async () => {
  if (busy) return; lock(true, "Saving and building...");
  const r = await post("/apply", {placements: pos}); lock(false);
  if (r.ok) { saved = JSON.parse(JSON.stringify(pos)); draw(); say(r.lines.concat(["", "Press \"Play it\" to open it."]), "good"); }
  else say((r.problems.length ? ["Nothing was written or built. " + r.problems.length + " thing" +
    (r.problems.length > 1 ? "s" : "") + " to put right:"].concat(r.problems.map(p => "  - " + p)) : []).concat(r.lines), "bad");
};
$("play").onclick = async () => { const r = await post("/play"); say(r.lines, r.ok ? "good" : "bad"); };
$("play2").onclick = async () => { const r = await post("/play", {which: "p2"}); say(r.lines, r.ok ? "good" : "bad"); };
window.onbeforeunload = () => Object.keys(pos).some(t => !same(pos[t], saved[t])) ? "Not saved" : undefined;
async function selftest() {          // ?selftest: the page tries itself (read from <pre id="selftest">)
  const r = [], ok = (c, m) => r.push((c ? "ok   " : "FAIL ") + m);
  const key = k => document.onkeydown({key: k, preventDefault() {}, target: document.body});
  ok(D.maps.length === 5, "five maps: " + D.maps.map(m => m.key).join(", "));
  ok(document.querySelectorAll("#map .thing").length === mapOf("mossui").things.length, "every Mossui thing drawn");
  pick("hiker"); const before = pos.hiker.slice();
  key("ArrowRight"); ok(pos.hiker[0] === before[0] + 1, "an arrow key moves the one picked");
  key("r"); ok(pos.hiker[2] !== before[2], "R turns a person");
  ok(document.querySelector(".row.moved") !== null, "the list marks what is not where it is saved");
  $("moment").value = "s2"; $("moment").onchange();
  ok(document.querySelectorAll("#map .thing.faded").length > 0, "a moment of the story fades who is not there");
  $("moment").value = ""; $("moment").onchange();
  let res = await post("/check", {placements: pos});
  ok(res.problems.length === 0, "check: the hiker one tile on is fine (" + res.problems.join("; ") + ")");
  pos.farmer = [8, 34, "left"]; res = await post("/check", {placements: pos});
  ok(res.problems.some(p => p.includes("apple farmer")), "check refuses the farmer in a rice paddy");
  for (const m of D.maps) { tab = m.key; draw(); ok(document.querySelectorAll("#map .thing").length === m.things.length, m.title + ": " + m.things.length + " drawn"); }
  tab = "mossui"; pos = JSON.parse(JSON.stringify(saved)); draw();
  const imgs = [...document.querySelectorAll("#map img")];
  await new Promise(res => setTimeout(res, 800));
  ok(imgs.every(i => i.complete && i.naturalWidth > 0), "every sprite picture loads (" + imgs.length + ")");
  $("selftest").textContent = r.join("\n");
}
load().then(() => { if (location.search.includes("selftest")) selftest(); });
</script></body></html>
"""


class Server(http.server.ThreadingHTTPServer):
    daemon_threads = True

    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
        http.server.ThreadingHTTPServer.server_bind(self)


def main(folder, emulators=True, browser=True):
    print("Kitakami editor: drawing the maps...", flush=True)
    ed = Editor(folder, emulators)
    srv = None
    for port in PORTS:
        try:
            srv = Server(("127.0.0.1", port), None)
            break
        except OSError:
            continue
    if srv is None:
        print("No free port between %d and %d." % (PORTS[0], PORTS[-1]), flush=True)
        return
    srv.RequestHandlerClass = handler(ed, srv.shutdown)
    url = "http://127.0.0.1:%d/" % srv.server_address[1]
    print("The editor is at " + url)
    print("placements.txt and the new ROMs are in: " + ed.folder)
    print("Leave this window open while you use it; close it to stop.", flush=True)
    if browser:
        webbrowser.open(url)
    srv.serve_forever()


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    main(args[0] if args else KR.FOLDER, emulators="--here" not in sys.argv, browser="--no-browser" not in sys.argv)
