"""The GIF editor: make GIFs out of the website's pictures and clips, with the mouse.
python -I gif_editor.py [folder] [--no-browser]
       (the folder: gba-trans/hyper-emerald/showcase/gifs unless named; --no-browser: only serve)

The user: "I want to create GIFs, based on our pics on website, can u make a custom edit for me? like drag and
drop on this project" (the drag and drop they know is the Area Zero editor, patches/paldea/editor.py). This
serves one page to the browser on this PC only (127.0.0.1):

  The library   (left) every picture of docs/showcase with the caption the site's gallery gives it, the short
                GIFs, the gallery's clips (docs/showcase/clips) and your own files. Pictures, GIFs or videos
                dropped on the page from a folder are copied into "my pictures" and listed too.
  The timeline  (bottom) the GIF, scene after scene. Drag a picture from the library to where it belongs, drag
                a scene to another place; double-clicking a library picture adds it at the end.
  The picture   (middle) the GIF as it will be, and it plays. With a layout of several pictures each place
                takes the picture dropped on it, and a picture dragged onto another place swaps the two.
  The settings  (right) the layout (one picture, two side by side... nine), the size (the game's pixels x1,
                x2, x3), a title bar, captions under or on the pictures; how long a scene stays and how it
                comes in (straight away, fading, sliding, through dark); a picture's caption, whether it fits
                or fills its place, where a clip starts.

"Make the GIF" draws every frame in the page, exactly as the preview shows it, and sends the frames here:
write_gif() gives them their colours and writes <folder>/<name>.gif, and the project goes beside it in
projects/, so a GIF can be opened and changed later. What is on the page is kept as a draft all the time.

The page (PAGE below) is plain HTML and script, no library. It tests itself in a browser without a window:
?selftest, read from the <pre id="selftest"> of the page (gba-trans/hyper-emerald/_testrun/gifeditor/drive.mjs starts the
editor on a folder of its own and Edge without a window, and prints it). Close the console window to stop.
"""
import http.server, io, json, os, re, socket, subprocess, sys, threading, time, urllib.parse, webbrowser, zlib

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SHOW = os.path.join(REPO, "docs", "showcase")
SITE = os.path.join(REPO, "site", "src")
FOLDER = os.path.normpath(os.path.join(REPO, "..", "showcase", "gifs"))
PORTS = range(8776, 8786)
PICS, MOVING, VIDEOS = (".png", ".jpg", ".jpeg", ".webp"), (".gif",), (".mp4", ".webm")
KINDS = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp",
         ".gif": "image/gif", ".mp4": "video/mp4", ".webm": "video/webm"}
# A GIF used as a source is handed to the page as one sheet of all its frames: this many pixels of them at most.
# (The six README montages, 1476x1114 and 165 frames each, are far over it; the gallery's clips are their cells.)
SHEET_MAX = 60_000_000
BODY_MAX = 256 << 20


def safe(name):
    """A file name out of what was typed: Windows refuses \\ / : * ? " < > |, and a dot or a space at the end."""
    s = re.sub(r'[\\/:*?"<>|\x00-\x1f]+', "-", str(name or "")).strip(" .-_")[:80].strip(" .-_")
    if re.fullmatch(r"(?i)con|prn|aux|nul|com\d|lpt\d", s):
        s += "-gif"
    return s or "my-gif"


def write_gif(frames, size, path, loop):
    """frames: (hundredths of a second, stretch, zlib of the RGB bytes) each, in order.

    A GIF picture has 256 colours at most. Every stretch of the GIF (a picture standing still, a clip playing, a
    fade from one scene to the next) gets one palette for all its frames, so nothing flickers inside it: exactly
    its own colours when there are 255 or fewer (every screenshot of the site has under 200), the 255 that fit
    best otherwise. Nothing is dithered: it is pixel art. The one colour left over is what Pillow writes the part
    of a frame that did not change with, which is what keeps a GIF small."""
    def load(i):
        return Image.frombytes("RGB", size, zlib.decompress(frames[i][2]))

    runs = []                                               # [stretch, [frame numbers]]
    for i, f in enumerate(frames):
        if not runs or runs[-1][0] != f[1]:
            runs.append([f[1], []])
        runs[-1][1].append(i)
    out = [None] * len(frames)
    for _, idx in runs:
        colours = set()
        for i in idx:
            c = load(i).getcolors(255)
            if c is None:
                colours = None
                break
            colours.update(x[1] for x in c)
            if len(colours) > 255:
                colours = None
                break
        if colours is None:
            pick = idx[::max(1, len(idx) // 16)][:16]
            strip = Image.new("RGB", (size[0], size[1] * len(pick)))
            for n, i in enumerate(pick):
                strip.paste(load(i), (0, n * size[1]))
            pal = strip.quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        else:
            flat = [v for c in sorted(colours) for v in c]
            pal = Image.new("P", (1, 1))
            pal.putpalette(flat + flat[-3:] * (256 - len(colours)))
        for i in idx:
            out[i] = load(i).quantize(palette=pal, dither=Image.Dither.NONE)
    more = {"loop": 0} if loop else {}                      # no loop count at all: the GIF plays once
    part = path + ".part"
    out[0].save(part, "GIF", save_all=True, append_images=out[1:], duration=[f[0] * 10 for f in frames],
                disposal=1, optimize=False, **more)
    os.replace(part, path)


class Library:
    """The pictures a GIF can be made of, and the folder the GIFs and their projects go to."""

    def __init__(self, folder):
        self.folder = os.path.abspath(folder)
        self.mine = os.path.join(self.folder, "my pictures")
        self.saved = os.path.join(self.folder, "projects")
        for d in (self.folder, self.mine, self.saved):
            os.makedirs(d, exist_ok=True)
        self.items, self.paths, self.posters, self.sheets = {}, {}, {}, {}
        self.job = None
        self.site = self.scan()

    def add(self, id, path, caption="", note=""):
        """One file as the page gets it, or None when a GIF cannot be made of it."""
        ext = os.path.splitext(path)[1].lower()
        it = {"id": id, "name": os.path.basename(path), "caption": caption, "note": note}
        if ext in VIDEOS:
            it.update(kind="clip", w=0, h=0, poster=False)  # the page reads a video's size and length itself
        else:
            try:
                with Image.open(path) as im:
                    w, h = im.size
                    n = getattr(im, "n_frames", 1)
                    if n == 1:
                        it.update(kind="pic", w=w, h=h)
                    elif n * w * h > SHEET_MAX:
                        return None
                    else:
                        durs = []
                        for f in range(n):
                            im.seek(f)
                            cs = round(im.info.get("duration", 100) / 10)
                            durs.append(cs if cs >= 2 else 10)      # as browsers play a delay too short to show
                        it.update(kind="gif", w=w, h=h, durs=durs, total=sum(durs), cols=max(1, min(n, 8192 // w)))
            except Exception:
                return None
        self.items[id], self.paths[id] = it, path
        self.sheets.pop(id, None)
        return it

    def scan(self):
        """The site's pictures, in groups: the gallery's screenshots first, with its captions and in its order."""
        try:
            gallery = open(os.path.join(SITE, "data", "gallery.ts"), encoding="utf-8").read()
        except OSError:
            gallery = ""
        captions = dict((m[0], m[1]) for m in re.findall(
            r"src:\s*'([^']+)',\s*alt:\s*'(?:[^'\\]|\\.)*',\s*caption:\s*'((?:[^'\\]|\\.)*)'", gallery))
        shown = self.shown()
        files = sorted(os.listdir(SHOW), key=str.lower) if os.path.isdir(SHOW) else []
        first, more, gifs = [], [], []
        for f in list(captions) + [f for f in files if f not in captions]:
            ext, path = os.path.splitext(f)[1].lower(), os.path.join(SHOW, f)
            if ext not in PICS + MOVING or not os.path.isfile(path):
                continue
            note = "" if f in shown else "not shown on the website"
            if self.add("shot/" + f, path, captions.get(f, ""), note):
                (gifs if ext in MOVING else first if f in captions else more).append("shot/" + f)
        groups = [("Gallery screenshots", first), ("More pictures", more), ("Short GIFs", gifs)]
        try:
            clips = json.load(open(os.path.join(SITE, "data", "clips.json"), encoding="utf-8"))
        except (OSError, ValueError):
            clips = []
        for c in clips:
            path = os.path.join(SHOW, "clips", c["slug"] + ".mp4")
            if not os.path.isfile(path):
                continue
            id = "clip/" + c["slug"]
            self.items[id] = {"id": id, "name": c["slug"] + ".mp4", "caption": c["caption"], "note": "",
                              "kind": "clip", "w": c["width"], "h": c["height"], "poster": True}
            self.paths[id], self.posters[id] = path, path[:-4] + ".png"
            title = "Clips: " + c["group"]
            if not groups or groups[-1][0] != title:
                groups.append((title, []))
            groups[-1][1].append(id)
        return [g for g in groups if g[1]]

    def shown(self):
        """Everything the README and the site's pages say, to tell the pictures they show from the others."""
        text = []
        for top, _, names in [(REPO, 0, ["README.md"])] + list(os.walk(SITE)):
            for n in names:
                if n.endswith((".md", ".mdx", ".astro", ".ts")) and os.path.isfile(os.path.join(top, n)):
                    text.append(open(os.path.join(top, n), encoding="utf-8", errors="replace").read())
        return "\n".join(text)

    def state(self):
        groups = [{"title": t, "items": [self.items[i] for i in ids]} for t, ids in self.site]
        mine = [self.add("mine/" + f, os.path.join(self.mine, f)) for f in sorted(os.listdir(self.mine), key=str.lower)
                if os.path.splitext(f)[1].lower() in KINDS]
        groups.insert(0, {"title": "Your files", "items": [m for m in mine if m]})
        return {"groups": groups, "saved": self.names(), "draft": self.read("_draft"), "folder": self.folder}

    def sheet(self, id):
        """All frames of a GIF side by side, as the game of a clip is to a video: the page cuts its frame out."""
        if id not in self.sheets:
            it = self.items[id]
            n, cols, w, h = len(it["durs"]), it["cols"], it["w"], it["h"]
            sh = Image.new("RGBA", (cols * w, -(-n // cols) * h))
            with Image.open(self.paths[id]) as im:
                for f in range(n):
                    im.seek(f)
                    sh.paste(im.convert("RGBA"), (f % cols * w, f // cols * h))
            b = io.BytesIO()
            sh.save(b, "PNG")
            self.sheets[id] = b.getvalue()
        return self.sheets[id]

    def drop(self, name, body):
        """A file dropped on the page: kept in "my pictures", under its own name."""
        name = os.path.basename(name.replace("\\", "/"))
        stem, ext = os.path.splitext(name)
        ext = ext.lower()
        if ext not in KINDS:
            return {"ok": False, "error": "%s: only pictures (PNG, JPG, WebP), GIFs and videos (MP4, WebM) "
                                          "can go into a GIF." % name}
        stem, n, new = safe(stem), 1, False
        path = os.path.join(self.mine, stem + ext)
        while os.path.exists(path) and open(path, "rb").read() != body:
            n += 1
            path = os.path.join(self.mine, "%s (%d)%s" % (stem, n, ext))
        if not os.path.exists(path):
            open(path, "wb").write(body)
            new = True
        it = self.add("mine/" + os.path.basename(path), path)
        if it is None:
            if new:
                os.remove(path)
            return {"ok": False, "error": "%s could not be read as a picture, or is a GIF too long to use here "
                                          "(as a video it would work: GIF Studio converts it)." % name}
        return {"ok": True, "item": it}

    # the projects: one JSON file a GIF, and the draft of what is on the page
    def names(self):
        fs = [f for f in os.listdir(self.saved) if f.endswith(".json") and not f.startswith("_")]
        fs.sort(key=lambda f: -os.path.getmtime(os.path.join(self.saved, f)))
        return [f[:-5] for f in fs]

    def read(self, name):
        try:
            return json.load(open(os.path.join(self.saved, name + ".json"), encoding="utf-8"))
        except (OSError, ValueError):
            return None

    def write(self, name, project):
        with open(os.path.join(self.saved, name + ".json"), "w", encoding="utf-8") as f:
            json.dump(project, f, indent=1, ensure_ascii=False)

    def save(self, raw):
        name = safe(raw.get("name"))
        self.write(name, raw["project"])
        return {"ok": True, "name": name, "saved": self.names()}

    # making a GIF: the page starts a job, sends its frames one by one, and asks for the file
    def start(self, raw):
        self.job = {"id": "%x" % time.time_ns(), "size": (int(raw["w"]), int(raw["h"])), "frames": []}
        return {"ok": True, "job": self.job["id"]}

    def frame(self, q, body):
        j = self.job
        if not j or q.get("job") != j["id"]:
            return {"ok": False, "error": "Another page started a GIF meanwhile: only one is made at a time."}
        if len(body) != j["size"][0] * j["size"][1] * 4 or int(q.get("i", -1)) != len(j["frames"]):
            return {"ok": False, "error": "A frame got lost on its way to the editor."}
        rgb = Image.frombuffer("RGBA", j["size"], body, "raw", "RGBA", 0, 1).convert("RGB")
        j["frames"].append((max(2, int(q.get("cs", 10))), q.get("seg", ""), zlib.compress(rgb.tobytes(), 1)))
        return {"ok": True}

    def finish(self, raw):
        j, self.job = self.job, None
        if not j or raw.get("job") != j["id"] or not j["frames"]:
            return {"ok": False, "error": "There are no frames to make a GIF of."}
        name = safe(raw.get("name"))
        path = os.path.join(self.folder, name + ".gif")
        try:
            write_gif(j["frames"], j["size"], path, bool(raw.get("loop", True)))
        except PermissionError:
            return {"ok": False, "error": "Windows would not let %s.gif be replaced: is it open in another "
                                          "program? Close it there, or give this GIF another name." % name}
        self.write(name, raw["project"])
        with Image.open(path) as im:
            n = im.n_frames
        return {"ok": True, "name": name, "file": name + ".gif", "path": path, "bytes": os.path.getsize(path),
                "frames": n, "w": j["size"][0], "h": j["size"][1], "saved": self.names()}

    def reveal(self, raw):
        """Show a GIF in its folder (or just the folder)."""
        path = os.path.join(self.folder, os.path.basename(str(raw.get("file") or "")))
        if sys.platform == "win32":
            subprocess.Popen(["explorer", "/select,", path] if os.path.isfile(path) else ["explorer", self.folder])
        else:
            subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", self.folder])
        return {"ok": True}


def handler(lib, stop):
    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def send(self, body, kind="application/json", code=200, keep=False):
            if not isinstance(body, bytes):
                body = json.dumps(body).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "private, max-age=600" if keep else "no-store")
            self.end_headers()
            self.wfile.write(body)

        def file(self, path, keep=True):
            with open(path, "rb") as f:
                self.send(f.read(), KINDS.get(os.path.splitext(path)[1].lower(), "application/octet-stream"),
                          keep=keep)

        def do_GET(self):
            path, _, query = self.path.partition("?")
            path = urllib.parse.unquote(path)
            try:
                if path == "/":
                    self.send(PAGE.encode("utf-8"), "text/html; charset=utf-8")
                elif path == "/library":
                    self.send(lib.state())
                elif path.startswith("/file/") and path[6:] in lib.paths:
                    self.file(lib.paths[path[6:]])
                elif path.startswith("/poster/") and path[8:] in lib.posters:
                    self.file(lib.posters[path[8:]])
                elif path.startswith("/sheet/") and "durs" in lib.items.get(path[7:], ()):
                    self.send(lib.sheet(path[7:]), "image/png", keep=True)
                elif path.startswith("/out/") and os.path.isfile(os.path.join(lib.folder, safe(path[5:-4]) + ".gif")):
                    self.file(os.path.join(lib.folder, safe(path[5:-4]) + ".gif"), keep=False)
                elif path == "/project":
                    name = safe(urllib.parse.parse_qs(query).get("name", [""])[0])
                    p = lib.read(name)
                    self.send({"ok": p is not None, "project": p, "error": "%s was not found among the saved "
                                                                           "GIFs." % name})
                else:
                    self.send({"ok": False, "error": "not found"}, code=404)
            except Exception as e:
                self.send({"ok": False, "error": "The editor ran into an error: %r" % (e,)}, code=500)

        def do_POST(self):
            path, _, query = self.path.partition("?")
            q = {k: v[0] for k, v in urllib.parse.parse_qs(query).items()}
            n = int(self.headers.get("Content-Length") or 0)
            if n > BODY_MAX:
                self.send({"ok": False, "error": "That is too big for the editor (over %d MB)." % (BODY_MAX >> 20)})
                return
            try:
                body = self.rfile.read(n)
                if path == "/frame":
                    self.send(lib.frame(q, body))
                elif path == "/drop":
                    self.send(lib.drop(q.get("name", ""), body))
                elif path == "/job":
                    self.send(lib.start(json.loads(body)))
                elif path == "/finish":
                    self.send(lib.finish(json.loads(body)))
                elif path == "/save":
                    self.send(lib.save(json.loads(body)))
                elif path == "/draft":
                    lib.write("_draft", json.loads(body))
                    self.send({"ok": True})
                elif path == "/reveal":
                    self.send(lib.reveal(json.loads(body or b"{}")))
                elif path == "/quit":
                    self.send({"ok": True})
                    threading.Thread(target=stop, daemon=True).start()
                else:
                    self.send({"ok": False, "error": "not found"}, code=404)
            except Exception as e:                            # anything else: tell the page, keep serving
                self.send({"ok": False, "error": "The editor ran into an error: %r" % (e,)})
    return H


PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>GIF editor</title><link rel="icon" href="data:,">
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; }
  body { margin: 0; font: 14px/1.4 "Segoe UI", Arial, sans-serif; background: #14161c; color: #e6e8ee;
         display: grid; grid-template-rows: auto 1fr; height: 100vh; overflow: hidden; }
  header { padding: 8px 14px; background: #1d2029; border-bottom: 1px solid #333846; display: flex;
           gap: 8px; align-items: center; flex-wrap: wrap; }
  header h1 { font-size: 16px; margin: 0 10px 0 0; }
  header .fill { flex: 1; }
  main { display: grid; grid-template-columns: 292px minmax(0, 1fr) 326px; min-height: 0; }
  button.act { background: #2f6fed; border: 0; color: #fff; padding: 7px 12px; border-radius: 6px; cursor: pointer;
               font-weight: 600; }
  button.act.go { background: #23a55a; font-size: 15px; padding: 9px 14px; }
  button.plain { background: #2a2e3a; border: 1px solid #3a4052; color: #cfd3de; padding: 6px 10px;
                 border-radius: 6px; cursor: pointer; }
  button:disabled { opacity: .45; cursor: default; }
  select, input[type=text], input[type=number] { background: #101218; border: 1px solid #3a4052; color: #e6e8ee;
                 padding: 5px 8px; border-radius: 6px; font: inherit; font-size: 13px; min-width: 0; }
  .hint { color: #8b93a7; font-size: 12px; margin: 0; }

  #lib { background: #1a1d25; border-right: 1px solid #333846; display: flex; flex-direction: column; min-height: 0; }
  #lib > input { margin: 10px 10px 6px; }
  #lib > .hint { padding: 8px 10px; border-top: 1px solid #333846; }
  #groups { overflow: auto; flex: 1; padding: 0 10px 10px; }
  details { margin-top: 6px; }
  summary { cursor: pointer; font-size: 12px; color: #9aa3b8; text-transform: uppercase; letter-spacing: .04em;
            padding: 4px 0; user-select: none; }
  summary .n { color: #646c80; }
  .grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 6px; }
  .tile { background: #232733; border: 1px solid #333846; border-radius: 6px; padding: 3px; cursor: grab;
          position: relative; user-select: none; min-width: 0; }
  .tile:hover { border-color: #f0c63c; }
  .tile img { display: block; width: 100%; height: auto; aspect-ratio: 3 / 2; object-fit: contain; background: #10121c;
              border-radius: 3px; image-rendering: pixelated; pointer-events: none; }
  .tile .cap { display: block; font-size: 11px; line-height: 1.25; color: #cfd3de; padding: 3px 2px 1px;
               overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
  .tile .kind { position: absolute; left: 6px; top: 6px; background: #f0c63c; color: #1a1a1a; font-size: 10px;
                font-weight: 700; padding: 0 5px; border-radius: 3px; }
  .tile .off { position: absolute; right: 6px; top: 6px; background: #3a4052; color: #cfd3de; font-size: 10px;
               padding: 0 5px; border-radius: 3px; }

  #mid { display: grid; grid-template-rows: minmax(0, 1fr) auto auto; min-width: 0; min-height: 0; }
  #view { position: relative; overflow: hidden; background: #0c0d11; display: grid; place-items: center; }
  #stage { position: relative; box-shadow: 0 0 0 1px #333846; }
  #c { display: block; width: 100%; height: 100%; }
  #slots { position: absolute; inset: 0; }
  body.playing #slots { opacity: 0; }
  .slot { position: absolute; display: grid; place-items: center; color: #8b93a7; font-size: 13px;
          text-align: center; padding: 6px; cursor: pointer; }
  .slot.empty { outline: 2px dashed #3a4052; outline-offset: -2px; background: rgba(255, 255, 255, .03); }
  .slot.sel { outline: 2px solid #f0c63c; outline-offset: -2px; }
  .slot.over { outline: 3px solid #5dff8a; outline-offset: -3px; background: rgba(93, 255, 138, .14); }
  #busy { position: fixed; inset: 0; background: rgba(12, 13, 17, .78); display: none; place-items: center;
          z-index: 40; }
  body.busy #busy { display: grid; }
  #busy div { background: #1d2029; border: 1px solid #333846; border-radius: 8px; padding: 16px 20px;
              display: flex; flex-direction: column; gap: 10px; align-items: center; min-width: 260px; }
  progress { width: 220px; }
  #bar { display: flex; gap: 10px; align-items: center; padding: 8px 12px; background: #1d2029;
         border-top: 1px solid #333846; }
  #bar input { flex: 1; }
  #play { min-width: 70px; }
  #clock { font: 12px Consolas, monospace; color: #9aa3b8; min-width: 104px; text-align: right; }
  #tl { display: flex; gap: 8px; padding: 12px; overflow-x: auto; background: #1a1d25; border-top: 1px solid #333846;
        height: 150px; align-items: flex-start; position: relative; }
  #tl .none { margin: auto; color: #8b93a7; border: 2px dashed #3a4052; border-radius: 8px; padding: 26px 40px;
              pointer-events: none; }
  .card { flex: none; width: 136px; background: #232733; border: 2px solid transparent; border-radius: 8px;
          padding: 4px; cursor: grab; position: relative; user-select: none; }
  .card.now { background: #2c3140; }
  .card.sel { border-color: #f0c63c; }
  .card.into { border-color: #5dff8a; background: #24382c; }
  .card canvas { display: block; width: 100%; max-height: 84px; object-fit: contain; border-radius: 4px;
                 background: #10121c; pointer-events: none; }
  .card .meta { display: flex; justify-content: space-between; gap: 6px; font-size: 12px; color: #aab2c5;
                padding: 3px 2px 1px; white-space: nowrap; }
  .card .x { position: absolute; right: -7px; top: -7px; width: 20px; height: 20px; border-radius: 50%; border: 0;
             background: #c0392b; color: #fff; cursor: pointer; line-height: 18px; padding: 0; display: none; }
  .card:hover .x { display: block; }
  .card .run { position: absolute; left: 4px; bottom: 0; height: 2px; background: #f0c63c; width: 0;
               max-width: calc(100% - 8px); }
  #mark { position: absolute; top: 10px; height: 112px; width: 4px; background: #5dff8a; border-radius: 2px;
          display: none; pointer-events: none; }

  aside { background: #1a1d25; border-left: 1px solid #333846; padding: 12px; overflow: auto; display: flex;
          flex-direction: column; gap: 14px; }
  aside > * { flex-shrink: 0; }
  .panel { display: flex; flex-direction: column; gap: 7px; }
  .panel:empty { display: none; }
  aside h2 { font-size: 13px; margin: 0; color: #9aa3b8; text-transform: uppercase; letter-spacing: .04em; }
  label.f { display: grid; grid-template-columns: 104px minmax(0, 1fr); gap: 8px; align-items: center; font-size: 13px; }
  label.f > span:first-child { color: #aab2c5; }
  label.c { display: flex; gap: 6px; align-items: center; font-size: 13px; }
  .sec { display: flex; gap: 6px; align-items: center; }
  .sec input[type=number] { width: 74px; }
  .sec input[type=range] { flex: 1; min-width: 0; }
  .row { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; }
  #msg { white-space: pre-wrap; font-size: 13px; background: #101218; border: 1px solid #333846; border-radius: 6px;
         padding: 8px; }
  #msg:empty { display: none; }
  #msg.bad { border-color: #a33; } #msg.good { border-color: #2a7; }
  #made img { max-width: 100%; display: block; border-radius: 4px; background: #10121c; image-rendering: auto; }
  #made { display: flex; flex-direction: column; gap: 7px; }
  #made:empty { display: none; }
  kbd { background: #2a2e3a; border: 1px solid #3a4052; border-radius: 4px; padding: 0 4px; font: 12px Consolas, monospace; }
  #dropall { position: fixed; inset: 0; border: 4px dashed #5dff8a; background: rgba(93, 255, 138, .08);
             display: none; place-items: end center; padding: 24px; font-size: 18px; pointer-events: none;
             z-index: 50; }
  body.files #dropall { display: grid; }
</style></head>
<body>
<header>
  <h1>GIF editor</h1>
  <button class="plain" id="new" title="Start an empty GIF">New</button>
  <select id="open" title="Open a GIF made or saved before, to change it"></select>
  <button class="plain" id="save" title="Keep this GIF under its name, without making it">Save</button>
  <button class="plain" id="undo" title="Ctrl+Z">Undo</button>
  <button class="plain" id="redo" title="Ctrl+Y">Redo</button>
  <span class="fill"></span>
  <span class="hint"><kbd>Space</kbd> play &nbsp; <kbd>Del</kbd> remove &nbsp; <kbd>&larr;</kbd> <kbd>&rarr;</kbd> scenes</span>
  <button class="plain" id="quit">Close the editor</button>
</header>
<main>
  <section id="lib">
    <input type="text" id="find" placeholder="Find a picture...">
    <div id="groups"></div>
    <p class="hint">Drag a picture to the timeline, or double-click it. Your own pictures, GIFs and videos: drop
      them anywhere on this page.</p>
  </section>
  <section id="mid">
    <div id="view">
      <div id="stage"><canvas id="c"></canvas><div id="slots"></div></div>
      <div id="busy"><div><b id="busytext">Making the GIF...</b><progress id="prog" max="1" value="0"></progress>
        <button class="plain" id="stop">Stop</button></div></div>
    </div>
    <div id="bar"><button class="act" id="play">Play</button>
      <input type="range" id="seek" min="0" max="0" value="0"><span id="clock"></span></div>
    <div id="tl"><div id="mark"></div></div>
  </section>
  <aside>
    <div class="panel" id="pgif"></div>
    <div class="panel" id="pscene"></div>
    <div class="panel" id="ppic"></div>
    <div class="panel" id="pmake"></div>
    <div id="msg"></div>
    <div id="made"></div>
  </aside>
</main>
<div id="dropall">Drop them on the timeline or the picture to put them in the GIF, anywhere else to keep them in the library</div>
<script>
"use strict";
const $ = id => document.getElementById(id);
const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls;
                                 if (text != null) e.textContent = text; return e; };
const enc = id => id.split("/").map(encodeURIComponent).join("/");
const post = async (url, body) => (await fetch(url, {method: "POST", body: JSON.stringify(body)})).json();
const secs = cs => (cs / 100).toFixed(cs % 10 ? 2 : 1);
const int = (v, lo, hi, or) => { v = Math.round(Number(v)); return isFinite(v) ? Math.min(hi, Math.max(lo, v)) : or; };
const uid = () => Math.random().toString(36).slice(2, 10);
const BG = "#10121c", INK = "#eceef5";             // the montages' own background and lettering
const LAYOUTS = [[1, 1, "One picture"], [2, 1, "Two, side by side"], [1, 2, "Two, one above the other"],
                 [3, 1, "Three, side by side"], [2, 2, "Four (2 x 2)"], [3, 2, "Six (3 x 2)"], [3, 3, "Nine (3 x 3)"]];
const TRS = [["cut", "Straight away"], ["fade", "Fading in"], ["slide", "Sliding in"], ["dark", "Through dark"]];
const TRSHORT = {fade: "fade", slide: "slide", dark: "dark"};

let LIB = {}, GROUPS = [];                         // the library: id -> picture, and its groups
let P = null;                                      // the GIF being made (all times in hundredths of a second)
let sel = {scene: 0, cell: null};
let T = 0, playing = false, busy = false, halt = false, dirty = true, thumbs = true, thumbsAt = 0;
let hist = [], hpos = -1, DRAG = null, work = Promise.resolve();
const CLOSED = new Set();
const CTX = $("c").getContext("2d", {willReadFrequently: true});
const OFF = document.createElement("canvas"), LAYER = document.createElement("canvas"), TMP = document.createElement("canvas");

// ---------- the GIF as data ----------
const fresh = () => ({name: "my-gif", cols: 1, rows: 1, scale: 2, title: "", captions: "below", hold: 200, step: 6,
                      loop: true, scenes: []});
const places = () => P.cols * P.rows;
const pad = (cells, n) => { cells = cells.slice(0, n); while (cells.length < n) cells.push(null); return cells; };
const newCell = id => ({id: uid(), src: id, caption: LIB[id].caption || "", fit: "fit", start: 0});
const newScene = cells => ({id: uid(), dur: 0, tr: "cut", trDur: 30, cells: pad(cells || [], places())});
const item = c => c ? LIB[c.src] : null;

// a GIF from a file: only what this page understands, and only pictures that are still in the library
function clean(p) {
  const q = Object.assign(fresh(), p && typeof p === "object" ? p : {});
  let gone = 0;
  q.name = String(q.name || "my-gif"); q.title = String(q.title || ""); q.loop = !!q.loop;
  q.cols = int(q.cols, 1, 3, 1); q.rows = int(q.rows, 1, 3, 1); q.scale = int(q.scale, 1, 3, 2);
  q.hold = int(q.hold, 10, 6000, 200); q.step = [4, 6, 10].includes(q.step) ? q.step : 6;
  q.captions = ["below", "on", "off"].includes(q.captions) ? q.captions : "below";
  q.scenes = (Array.isArray(q.scenes) ? q.scenes : []).map(sc => ({
    id: sc.id || uid(), dur: int(sc.dur, 0, 60000, 0), tr: TRS.some(t => t[0] === sc.tr) ? sc.tr : "cut",
    trDur: int(sc.trDur, 4, 300, 30),
    cells: pad((Array.isArray(sc.cells) ? sc.cells : []).map(c => {
      if (!c) return null;
      if (!LIB[c.src]) { gone++; return null; }
      return {id: c.id || uid(), src: c.src, caption: String(c.caption || ""), fit: c.fit === "fill" ? "fill" : "fit",
              start: int(c.start, 0, 1e6, 0)};
    }), q.cols * q.rows)}));
  return [q, gone];
}

// ---------- time ----------
function gifFrame(it, cs) { let a = 0; for (let f = 0; f < it.durs.length; f++) { a += it.durs[f]; if (cs < a) return f; }
                            return it.durs.length - 1; }
// how long a place's picture moves for, from where it starts: nothing for a still
function runs(c) {
  const it = item(c);
  if (!it || it.kind === "pic") return 0;
  return Math.max(0, (it.kind === "gif" ? it.total : Math.round((it.len || 0) * 100)) - c.start);
}
// a scene stays as long as it was told to, or else as long as its longest clip, or else as a still picture does
const durOf = sc => sc.dur || Math.max(0, ...sc.cells.map(runs)) || P.hold;
const trOf = i => i > 0 && P.scenes[i].tr !== "cut" ? Math.min(P.scenes[i].trDur, Math.floor(durOf(P.scenes[i]) / 2)) : 0;
const total = () => P.scenes.reduce((a, sc) => a + durOf(sc), 0);
const startOf = i => P.scenes.slice(0, i).reduce((a, sc) => a + durOf(sc), 0);
function at(t) {                                   // the scene on show at a time, and how far into it
  let a = 0;
  for (let i = 0; i < P.scenes.length; i++) {
    const d = durOf(P.scenes[i]);
    if (t < a + d || i === P.scenes.length - 1) return {i: i, lt: Math.max(0, Math.min(t - a, d))};
    a += d;
  }
  return {i: -1, lt: 0};
}

// ---------- what is drawn where ----------
function geo() {
  const s = P.scale, cw = 240 * s, ch = 160 * s, many = places() > 1;
  const m = many ? 5 * s : 0, gap = many ? 4 * s : 0;                   // the montages' margins: 10 and 8 at x2
  const titleH = P.title.trim() ? Math.max(30, 22 * s) : 0;
  const capH = P.captions === "below" && P.scenes.some(sc => sc.cells.some(c => c && c.caption.trim()))
               ? Math.max(22, 14 * s) : 0;
  const top = titleH || m, cells = [];
  for (let r = 0; r < P.rows; r++) for (let c = 0; c < P.cols; c++)
    cells.push({x: m + c * (cw + gap), y: top + r * (ch + capH + gap), w: cw, h: ch});
  return {W: 2 * m + P.cols * cw + (P.cols - 1) * gap, H: top + P.rows * (ch + capH) + (P.rows - 1) * gap + m,
          s: s, m: m, capH: capH, titleH: titleH, cells: cells};
}

const PICS = new Map();                            // URL -> a picture and whether it has arrived
function pic(url) {                                // the picture of a URL, or null while it is on its way
  let p = PICS.get(url);
  if (!p) {
    p = {im: new Image(), ok: false};
    p.wait = new Promise(done => { p.im.onload = () => { p.ok = true; dirty = thumbs = true; done(); };
                                   p.im.onerror = () => done(); });
    p.im.src = url; PICS.set(url, p);
  }
  return p.ok ? p.im : null;
}
const picReady = url => { pic(url); return PICS.get(url).wait; };
const fileUrl = it => "/file/" + enc(it.id);
const posterUrl = it => it.poster ? "/poster/" + enc(it.id) : it.thumb;

// A clip is a <video> the page seeks. As a blob: a file being served cannot always be sought, a blob can.
const BLOBS = new Map(), VIDS = new Map();
function blobOf(id) {
  if (!BLOBS.has(id)) BLOBS.set(id, fetch("/file/" + enc(id)).then(r => r.blob()).then(b => URL.createObjectURL(b)));
  return BLOBS.get(id);
}
function seek(v, s) {
  return new Promise(done => {
    const end = () => { v.removeEventListener("seeked", end); clearTimeout(tm); done(); };
    const tm = setTimeout(end, 4000);
    v.addEventListener("seeked", end); v.currentTime = s;
  });
}
// what has to be known of a clip before it goes into a GIF: its length and size (and, for your own, a still of it)
async function need(id) {
  const it = LIB[id];
  if (!it || it.kind !== "clip" || it.len) return;
  if (!it.wait) it.wait = (async () => {
    const v = document.createElement("video"); v.muted = true; v.preload = "auto";
    try {
      v.src = await blobOf(id);
      await new Promise((ok, no) => { v.onloadeddata = ok;
                                      v.onerror = () => no(new Error(it.name + " is not a video this browser can play.")); });
      let len = v.duration;
      if (!isFinite(len)) { await seek(v, 1e7); len = v.currentTime; }
      if (!v.videoWidth || !(len > 0)) throw new Error(it.name + " has no picture to show.");
      it.w = v.videoWidth; it.h = v.videoHeight;
      if (!it.poster) {
        await seek(v, Math.min(1, len / 2));
        const c = document.createElement("canvas"); c.width = it.w; c.height = it.h;
        c.getContext("2d").drawImage(v, 0, 0); it.thumb = c.toDataURL("image/jpeg", .85);
      }
      it.len = len;
    } finally { v.removeAttribute("src"); v.load(); }
  })();
  try { await it.wait; } catch (e) { it.wait = null; throw e; }
}
// the <video> of one place: two places with the same clip each have their own, they show different moments
function vid(c) {
  let v = VIDS.get(c.id);
  if (!v || v.src !== c.src) {
    if (v) drop(v);
    const e = document.createElement("video"); e.muted = true; e.playsInline = true; e.preload = "auto";
    v = {src: c.src, el: e, has: false}; VIDS.set(c.id, v);
    e.addEventListener("loadeddata", () => { v.has = true; dirty = true; });
    e.addEventListener("seeked", () => { dirty = true; });
    blobOf(c.src).then(u => { if (VIDS.get(c.id) === v) e.src = u; });
    if (VIDS.size > 28) {                           // a browser only keeps so many videos open: let the idle ones go
      const old = [...VIDS].filter(x => x[1] !== v).sort((a, b) => a[1].used - b[1].used).slice(0, VIDS.size - 28);
      for (const [k, o] of old) { drop(o); VIDS.delete(k); }
    }
  }
  v.used = performance.now();
  return v;
}
function drop(v) { v.el.pause(); v.el.removeAttribute("src"); v.el.load(); }
const loaded = v => v.has ? Promise.resolve() : new Promise((ok, no) => {
  v.el.addEventListener("loadeddata", ok, {once: true});
  v.el.addEventListener("error", () => no(new Error("A clip would not load.")), {once: true});
});

// How many times a picture's pixels were enlarged: 2 for a GBA screen kept at 480x320, as most of the site's are.
// Found by looking at the picture. (A clip cannot be looked at like that, video blurs: drawSrc knows the site's.)
function blockOf(it, src) {
  if (it.px) return it.px;
  it.px = 1;
  const w = it.w, h = it.h, c = document.createElement("canvas"); c.width = w; c.height = h;
  const x = c.getContext("2d"); x.drawImage(src, 0, 0, w, h, 0, 0, w, h);
  const d = new Uint32Array(x.getImageData(0, 0, w, h).data.buffer);
  for (let g = 6; g > 1 && it.px === 1; g--) {
    if (w % g || h % g) continue;
    let same = true;
    for (let y = 0; y < h && same; y++) {
      const row = y * w, top = (y - y % g) * w;
      for (let X = 0; X < w; X++) if (d[row + X] !== d[top + X - X % g]) { same = false; break; }
    }
    if (same) it.px = g;
  }
  return it.px;
}
// Pixel art stays pixel art: whole multiples are copied pixel by pixel, a x2 screenshot going to x3 goes back to
// the game's own pixels first (so each comes out the same size), and only what fits no grid is smoothed.
function pixels(ctx, src, sx, sy, sw, sh, dx, dy, dw, dh, g) {
  const k = dw / sw, kg = dw / (sw / g);
  if (Number.isInteger(k) && dh === sh * k) {
    ctx.imageSmoothingEnabled = false; ctx.drawImage(src, sx, sy, sw, sh, dx, dy, dw, dh);
  } else if (g > 1 && Number.isInteger(kg) && dh === sh / g * kg) {
    TMP.width = sw / g; TMP.height = sh / g;
    const t = TMP.getContext("2d"); t.imageSmoothingEnabled = false;
    t.drawImage(src, sx, sy, sw, sh, 0, 0, TMP.width, TMP.height);
    ctx.imageSmoothingEnabled = false; ctx.drawImage(TMP, 0, 0, TMP.width, TMP.height, dx, dy, dw, dh);
  } else {
    ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = "high";
    ctx.drawImage(src, sx, sy, sw, sh, dx, dy, dw, dh);
  }
}
// one place's picture as it is lt into its scene; o.thumb: a still will do (the timeline's small pictures)
function drawSrc(ctx, c, lt, b, o) {
  const it = item(c);
  if (!it) return;
  let src = null, sx = 0, sy = 0, sw = it.w, sh = it.h;
  if (it.kind === "pic") src = pic(fileUrl(it));
  else if (it.kind === "gif") {
    src = pic("/sheet/" + enc(it.id));
    const f = gifFrame(it, c.start + lt); sx = f % it.cols * it.w; sy = Math.floor(f / it.cols) * it.h;
  } else {
    const v = o.thumb ? null : vid(c);
    if (v && v.has) { src = v.el; sw = src.videoWidth; sh = src.videoHeight; }
    else { const u = posterUrl(it); src = u ? pic(u) : null; if (src) { sw = src.naturalWidth; sh = src.naturalHeight; } }
  }
  if (!src || !sw || !sh) return;
  const k = c.fit === "fill" ? Math.max(b.w / sw, b.h / sh) : Math.min(b.w / sw, b.h / sh);
  const dw = Math.round(sw * k), dh = Math.round(sh * k);
  ctx.save(); ctx.beginPath(); ctx.rect(b.x, b.y, b.w, b.h); ctx.clip();
  pixels(ctx, src, sx, sy, sw, sh, b.x + Math.round((b.w - dw) / 2), b.y + Math.round((b.h - dh) / 2), dw, dh,
         it.kind !== "clip" ? blockOf(it, src) : it.poster && sw === 480 && sh === 320 ? 2 : 1);
  ctx.restore();
}
function label(ctx, text, x, y, w, h, align, inset) {
  let px = Math.round(h * .46), room = w - 2 * inset;
  ctx.textBaseline = "middle"; ctx.textAlign = align; ctx.fillStyle = INK;
  const font = () => { ctx.font = "700 " + px + "px 'Segoe UI', Arial, sans-serif"; };
  for (font(); ctx.measureText(text).width > room && px > Math.max(9, h * .32); font()) px--;
  while (text.length > 1 && ctx.measureText(text).width > room) text = text.slice(0, -2).trimEnd() + "…";
  ctx.fillText(text, align === "center" ? x + w / 2 : x + inset, y + h / 2 + 1);
}
function drawScene(ctx, G, sc, lt, o) {
  sc.cells.forEach((c, j) => {
    const b = G.cells[j];
    if (!c || !b) return;
    drawSrc(ctx, c, lt, b, o);
    const cap = P.captions === "off" ? "" : c.caption.trim();
    if (!cap) return;
    const h = Math.max(22, 14 * G.s);
    if (P.captions === "below") label(ctx, cap, b.x, b.y + b.h, b.w, G.capH, "center", h * .3);
    else { ctx.fillStyle = "rgba(16,18,28,.84)"; ctx.fillRect(b.x, b.y + b.h - h, b.w, h);
           label(ctx, cap, b.x, b.y + b.h - h, b.w, h, "center", h * .3); }
  });
}
// The GIF at a time. A scene that comes in over time does so during its own first moments, over the last look
// of the scene before it. o.bias: how far into a frame's time the fade is taken from (a GIF frame stands for a
// while: its middle, so a fade never starts on a copy of the scene before nor ends on a copy of the new one).
function drawAt(ctx, G, t, o) {
  ctx.globalAlpha = 1; ctx.fillStyle = BG; ctx.fillRect(0, 0, G.W, G.H);
  if (P.scenes.length) {
    const w = at(t), sc = P.scenes[w.i], tr = trOf(w.i);
    if (w.lt < tr) {
      const p = Math.min(1, (w.lt + (o.bias || 0)) / tr), prev = P.scenes[w.i - 1], end = durOf(prev);
      if (sc.tr === "fade") {
        drawScene(ctx, G, prev, end, o);
        if (LAYER.width !== G.W || LAYER.height !== G.H) { LAYER.width = G.W; LAYER.height = G.H; }
        const l = LAYER.getContext("2d"); l.fillStyle = BG; l.fillRect(0, 0, G.W, G.H); drawScene(l, G, sc, w.lt, o);
        ctx.globalAlpha = p; ctx.drawImage(LAYER, 0, 0); ctx.globalAlpha = 1;
      } else if (sc.tr === "slide") {
        const dx = Math.round((p < .5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2) * G.W);
        ctx.save(); ctx.translate(-dx, 0); drawScene(ctx, G, prev, end, o); ctx.restore();
        ctx.save(); ctx.translate(G.W - dx, 0); drawScene(ctx, G, sc, w.lt, o); ctx.restore();
      } else {
        if (p < .5) drawScene(ctx, G, prev, end, o); else drawScene(ctx, G, sc, w.lt, o);
        ctx.globalAlpha = p < .5 ? 2 * p : 2 - 2 * p; ctx.fillStyle = BG; ctx.fillRect(0, 0, G.W, G.H); ctx.globalAlpha = 1;
      }
    } else drawScene(ctx, G, sc, w.lt, o);
  }
  if (G.titleH) { ctx.fillStyle = BG; ctx.fillRect(0, 0, G.W, G.titleH);
                  label(ctx, P.title.trim(), 0, 0, G.W, G.titleH, "left", Math.max(G.m, G.titleH * .28)); }
}
// which clip has to show which of its moments at a time: [[place, seconds]]
function wants(t) {
  const out = [];
  if (!P.scenes.length) return out;
  const w = at(t);
  const add = (sc, lt) => sc.cells.forEach(c => { const it = item(c);
    if (it && it.kind === "clip" && it.len) out.push([c, Math.max(0, Math.min((c.start + lt) / 100, it.len - .02))]); });
  add(P.scenes[w.i], w.lt);
  if (w.lt < trOf(w.i)) add(P.scenes[w.i - 1], durOf(P.scenes[w.i - 1]));
  return out;
}
// the preview: clips of the scene on show play along, every other one stands still where it has to
function sync() {
  if (!P.scenes.length) return;
  const live = new Set(), now = P.scenes[at(T).i];
  for (const [c, s] of wants(T)) {
    const v = vid(c), e = v.el; live.add(e);
    if (!v.has) continue;
    if (playing && now.cells.includes(c) && s < LIB[c.src].len - .08) {
      if (e.paused) { e.currentTime = s; e.play().catch(() => {}); }
      else if (Math.abs(e.currentTime - s) > .3) e.currentTime = s;
    } else {
      if (!e.paused) e.pause();
      if (!e.seeking && Math.abs(e.currentTime - s - .001) > .01) e.currentTime = s + .001;
    }
  }
  for (const v of VIDS.values()) if (!live.has(v.el) && !v.el.paused) v.el.pause();
}
// making the GIF: every clip exactly on the moment a frame needs, before the frame is drawn
async function exact(t) {
  for (const [c, s] of wants(t)) {
    const v = vid(c); await loaded(v); v.el.pause();
    if (v.el.seeking || Math.abs(v.el.currentTime - s - .001) > .0005) await seek(v.el, s + .001);
  }
}
// The GIF's frames: [{t, cs, seg, bias}]. Time is walked in steps, and a frame lasts for as long as nothing on it
// changes: a still picture is one frame however long it stays. seg names the stretch a frame belongs to (one
// scene's fade, or the scene itself), which is what gets a palette of its own (write_gif in the editor).
function schedule() {
  const out = [];
  let a = 0;
  P.scenes.forEach((sc, i) => {
    const d = durOf(sc), tr = trOf(i);
    for (let lt = 0; lt < d; lt += P.step) {
      const cs = Math.min(P.step, d - lt), fading = lt < tr, last = out[out.length - 1];
      const sig = i + (fading ? "~" + lt : "") + "|" + sc.cells.map(c => {
        const it = item(c);
        return !it ? "" : it.kind === "pic" ? "p" : it.kind === "gif" ? gifFrame(it, c.start + lt)
               : Math.round(Math.min((c.start + lt) / 100, (it.len || 0) - .02) * 1000); }).join(",");
      if (last && (last.sig === sig || cs < 2)) last.cs += cs;
      else out.push({t: a + lt, cs: cs, sig: sig, seg: i + (fading ? "f" : "s"), bias: fading ? P.step / 2 : 0});
    }
    a += d;
  });
  return out;
}

// ---------- changing the GIF ----------
function commit() {
  const s = JSON.stringify(P);
  if (s === hist[hpos]) return;
  hist.length = hpos + 1; hist.push(s); hpos++;
  if (hist.length > 200) { hist.shift(); hpos--; }
}
function step(d) {                                 // undo (-1) and redo (+1)
  if (hpos + d < 0 || hpos + d >= hist.length) return;
  hpos += d; P = JSON.parse(hist[hpos]); sel.cell = null; refresh();
}
let keeping = 0;
function keep() { clearTimeout(keeping); keeping = setTimeout(() => post("/draft", P).catch(() => {}), 400); }
// after anything changed: o.typing while a text or a number is being typed (the settings are left as they are,
// so the box keeps the cursor, and the change goes into Undo when the box is left)
function changed(o) {
  if (!(o && o.typing)) { fix(); commit(); }
  refresh(o);
}
function fix() {
  for (const sc of P.scenes) sc.cells = pad(sc.cells, places());
  sel.scene = Math.max(0, Math.min(sel.scene, P.scenes.length - 1));
  if (sel.cell != null && sel.cell >= places()) sel.cell = null;
}
function refresh(o) {
  fix();
  if (!P.scenes.length) T = 0;
  else if (!playing) {                             // the picture shows the chosen scene, past the way it comes in
    const a = startOf(sel.scene), d = durOf(P.scenes[sel.scene]);
    if (!(T >= a && T < a + d)) T = a + trOf(sel.scene);
  }
  renderTimeline(); renderSlots();
  if (o && o.typing) touchSide(); else renderSide();
  $("undo").disabled = hpos <= 0; $("redo").disabled = hpos >= hist.length - 1;
  dirty = true; keep();
}
function select(i, cell) {
  setPlaying(false);
  sel = {scene: i, cell: cell}; T = startOf(i) + trOf(i); refresh();
  const card = document.querySelectorAll("#tl .card")[i];
  if (card) card.scrollIntoView({block: "nearest", inline: "nearest"});
}
// Pictures of the library into the GIF. spot: {at: i} as new scenes there, {into: i} that scene's free places,
// {cell: j} that place of the scene on show; nothing: at the end (a layout of several fills the chosen scene first).
async function place(ids, spot) {
  ids = (ids || []).filter(id => LIB[id]);
  if (!ids.length) return;
  try { await Promise.all(ids.map(need)); } catch (e) { say(String(e.message || e), "bad"); return; }
  const n = places(), cells = ids.map(newCell);
  let i, next, cell = null;
  if (!spot && n > 1 && P.scenes[sel.scene] && P.scenes[sel.scene].cells.includes(null)) spot = {into: sel.scene};
  if (spot && spot.cell != null) {
    if (!P.scenes.length) P.scenes.push(newScene());
    i = sel.scene; cell = spot.cell; P.scenes[i].cells[cell] = cells.shift();
  }
  if (spot && (spot.into != null || spot.cell != null)) {
    if (spot.into != null) i = spot.into;
    const sc = P.scenes[i];
    for (let j = 0; j < n && cells.length; j++) if (!sc.cells[j]) sc.cells[j] = cells.shift();
    next = i + 1;
  } else i = next = spot ? spot.at : P.scenes.length;
  while (cells.length) P.scenes.splice(next++, 0, newScene(cells.splice(0, n)));
  sel = {scene: i, cell: cell}; T = -1; changed();
}
function removeScene(i) { P.scenes.splice(i, 1); if (sel.scene > i || sel.scene >= P.scenes.length) sel.scene--;
                          sel.cell = null; T = -1; changed(); }
function copyScene(i) {
  const sc = JSON.parse(JSON.stringify(P.scenes[i])); sc.id = uid(); sc.cells.forEach(c => { if (c) c.id = uid(); });
  P.scenes.splice(i + 1, 0, sc); sel = {scene: i + 1, cell: null}; T = -1; changed();
}
function moveScene(from, to) {                     // to: the gap it goes into, counted before it is taken out
  if (to === from || to === from + 1) return;
  const sc = P.scenes.splice(from, 1)[0], i = to > from ? to - 1 : to;
  P.scenes.splice(i, 0, sc); sel = {scene: i, cell: null}; T = -1; changed();
}
function clearCell(i, j) {
  if (places() === 1) return removeScene(i);
  P.scenes[i].cells[j] = null; changed();
}
// another layout: the pictures stay in their order; a scene with more than the new layout holds goes on in
// scenes of its own after it, so none is lost
function relayout(cols, rows) {
  const n = cols * rows, out = [];
  for (const sc of P.scenes) {
    const full = sc.cells.filter(Boolean);
    out.push(Object.assign(sc, {cells: pad(full.splice(0, n), n)}));
    while (full.length) out.push({id: uid(), dur: sc.dur, tr: sc.tr, trDur: sc.trDur, cells: pad(full.splice(0, n), n)});
  }
  P.cols = cols; P.rows = rows; P.scenes = out; sel.cell = null;
}
async function use(p, note) {                      // another GIF onto the page: a saved one, the draft, a new one
  const r = clean(p);
  P = r[0]; sel = {scene: 0, cell: null}; T = 0; setPlaying(false);
  try { await Promise.all(P.scenes.flatMap(sc => sc.cells.filter(Boolean).map(c => need(c.src)))); }
  catch (e) { say(String(e.message || e), "bad"); }
  changed();
  if (r[1]) say(r[1] + (r[1] === 1 ? " picture of this GIF is" : " pictures of this GIF are") +
                " no longer in the library and left out.", "bad");
  else if (note) say(note, "");
}

// ---------- the library ----------
function renderLib() {
  const box = $("groups"), find = $("find").value.trim().toLowerCase();
  box.textContent = "";
  for (const g of GROUPS) {
    const items = g.items.filter(it => !find || (it.name + " " + it.caption + " " + g.title).toLowerCase().includes(find));
    if (!items.length) continue;
    const d = el("details"), s = el("summary", "", g.title + " ");
    d.open = !!find || !CLOSED.has(g.title);
    s.append(el("span", "n", String(items.length))); d.append(s);
    s.addEventListener("click", () => { if (!find) d.open ? CLOSED.add(g.title) : CLOSED.delete(g.title); });
    const grid = el("div", "grid");
    for (const it of items) grid.append(tile(it));
    d.append(grid); box.append(d);
  }
  if (!box.children.length) box.append(el("p", "hint", find ? "No picture is called that." : "The library is empty."));
}
function tile(it) {
  const t = el("div", "tile"), im = el("img");
  t.draggable = true; t.dataset.id = it.id;
  t.title = (it.caption ? it.caption + "\n" : "") + it.name + (it.w ? "  " + it.w + " x " + it.h : "") +
            (it.note ? "\n(" + it.note + ")" : "") + "\nDrag it to the timeline or onto the picture; a double-click adds it at the end.";
  im.loading = "lazy"; im.alt = "";
  const u = it.kind === "clip" ? posterUrl(it) : fileUrl(it);
  if (u) im.src = u;
  t.append(im, el("span", "cap", it.caption || it.name.replace(/\.\w+$/, "")));
  if (it.kind !== "pic") t.append(el("span", "kind", it.kind === "gif" ? "GIF" : "clip"));
  if (it.note) t.append(el("span", "off", "not on site"));
  t.addEventListener("dragstart", e => { DRAG = {lib: it.id}; e.dataTransfer.setData("text/plain", it.id);
                                         e.dataTransfer.effectAllowed = "copy"; });
  t.addEventListener("dragend", endDrag);
  t.addEventListener("dblclick", () => { work = place([it.id], null); });
  return t;
}
// files dropped from a folder: the editor copies them into "my pictures"; -> their library ids
async function upload(files) {
  const ids = [], bad = [];
  for (const f of [...files]) {
    let r;
    try { r = await (await fetch("/drop?name=" + encodeURIComponent(f.name), {method: "POST", body: f})).json(); }
    catch (e) { r = {ok: false, error: f.name + " did not reach the editor: is its window still open?"}; }
    if (!r.ok) { bad.push(r.error); continue; }
    const it = r.item, mine = GROUPS[0].items, was = mine.findIndex(x => x.id === it.id);
    LIB[it.id] = Object.assign(LIB[it.id] || {}, it);
    if (was < 0) mine.push(LIB[it.id]);
    ids.push(it.id);
    if (it.kind === "clip") try { await need(it.id); } catch (e) { bad.push(String(e.message || e)); ids.pop(); }
  }
  CLOSED.delete(GROUPS[0].title); renderLib();
  if (bad.length) say(bad.join("\n"), "bad");
  else if (ids.length) say(ids.length === 1 ? LIB[ids[0]].name + " is in the library now, under Your files."
                                            : ids.length + " files are in the library now, under Your files.", "good");
  return ids;
}

// ---------- the timeline ----------
function renderTimeline() {
  const tl = $("tl"), old = new Map();
  tl.querySelectorAll(".card").forEach(c => { old.set(c.dataset.id, c.querySelector("canvas")); c.remove(); });
  tl.querySelectorAll(".none").forEach(e => e.remove());
  if (!P.scenes.length) tl.append(el("div", "none", "Drag pictures here, in the order they should appear."));
  P.scenes.forEach((sc, i) => {
    const card = el("div", "card" + (i === sel.scene ? " sel" : "")), meta = el("div", "meta"), x = el("button", "x", "×");
    card.draggable = true; card.dataset.id = sc.id;
    card.title = "Scene " + (i + 1) + ": click to change it, drag it to move it.";
    meta.append(el("b", "", String(i + 1)),
                el("span", "", (trOf(i) ? TRSHORT[sc.tr] + " · " : "") + secs(durOf(sc)) + " s"));
    x.title = "Remove this scene"; x.addEventListener("click", e => { e.stopPropagation(); removeScene(i); });
    card.append(old.get(sc.id) || el("canvas"), meta, x, el("div", "run"));
    card.addEventListener("click", () => select(i, null));
    card.addEventListener("dragstart", e => { DRAG = {scene: i}; e.dataTransfer.setData("text/plain", "scene");
                                              e.dataTransfer.effectAllowed = "move"; });
    card.addEventListener("dragend", endDrag);
    tl.append(card);
  });
  thumbs = true;
}
function renderThumbs() {
  const G = geo(), cards = document.querySelectorAll("#tl .card");
  if (!cards.length) return;
  OFF.width = G.W; OFF.height = G.H;
  const o = OFF.getContext("2d");
  cards.forEach((card, i) => {
    const sc = P.scenes[i], cv = card.querySelector("canvas"), w = 256, h = Math.max(1, Math.round(w * G.H / G.W));
    if (!sc) return;
    if (cv.width !== w || cv.height !== h) { cv.width = w; cv.height = h; }
    o.fillStyle = BG; o.fillRect(0, 0, G.W, G.H); drawScene(o, G, sc, trOf(i), {thumb: true});
    const c = cv.getContext("2d"); c.imageSmoothingQuality = "high"; c.drawImage(OFF, 0, 0, w, h);
  });
}
const hasFiles = e => [...(e.dataTransfer ? e.dataTransfer.types : [])].includes("Files");
let spot = null;
// where on the timeline a drop would land: between two scenes, or (a layout of several pictures, over the middle
// of a scene that still has a free place) into that scene
function spotAt(x) {
  const cards = [...document.querySelectorAll("#tl .card")], moving = DRAG && DRAG.scene != null;
  for (let i = 0; i < cards.length; i++) {
    const r = cards[i].getBoundingClientRect();
    if (!moving && places() > 1 && x > r.left + r.width * .25 && x < r.right - r.width * .25 &&
        P.scenes[i].cells.includes(null)) return {into: i};
    if (x < r.left + r.width / 2) return {at: i};
  }
  return {at: cards.length};
}
function mark(s) {
  const tl = $("tl"), cards = [...tl.querySelectorAll(".card")], m = $("mark");
  cards.forEach(c => c.classList.remove("into")); m.style.display = "none";
  if (!s) return;
  if (s.into != null) { cards[s.into].classList.add("into"); return; }
  const t = tl.getBoundingClientRect(), r = cards.length ? cards[Math.min(s.at, cards.length - 1)].getBoundingClientRect() : null;
  m.style.left = (!r ? 14 : (s.at < cards.length ? r.left - 6 : r.right + 2) - t.left + tl.scrollLeft) + "px";
  m.style.display = "block";
}
function endDrag() { DRAG = null; spot = null; over = 0; mark(null); document.body.classList.remove("files");
                     document.querySelectorAll(".slot.over").forEach(s => s.classList.remove("over")); }
$("tl").addEventListener("dragover", e => {
  if (!(DRAG && (DRAG.lib || DRAG.scene != null)) && !hasFiles(e)) return;
  e.preventDefault(); e.dataTransfer.dropEffect = DRAG && DRAG.scene != null ? "move" : "copy";
  spot = spotAt(e.clientX); mark(spot);
});
$("tl").addEventListener("dragleave", e => { if (!$("tl").contains(e.relatedTarget)) mark(null); });
$("tl").addEventListener("drop", e => {
  e.preventDefault(); e.stopPropagation();
  const d = DRAG, s = spot || spotAt(e.clientX), files = e.dataTransfer.files;
  endDrag();
  if (d && d.scene != null) moveScene(d.scene, s.at);
  else work = (async () => place(d ? [d.lib] : await upload(files), s))();
});

// ---------- the picture in the middle ----------
function fit() {
  const G = geo(), v = $("view"), st = $("stage");
  const k = Math.min(P.scale === 1 ? 2 : 1, (v.clientWidth - 28) / G.W, (v.clientHeight - 28) / G.H);
  st.style.width = Math.max(60, Math.floor(G.W * k)) + "px"; st.style.height = Math.max(40, Math.floor(G.H * k)) + "px";
  $("c").style.imageRendering = k >= 1 ? "pixelated" : "auto";
}
function renderSlots() {
  const G = geo(), box = $("slots"), sc = P.scenes[sel.scene], many = places() > 1;
  box.textContent = "";
  G.cells.forEach((b, j) => {
    const c = sc && sc.cells[j], s = el("div", "slot" + (c ? "" : " empty") + (c && many && sel.cell === j ? " sel" : ""));
    s.style.cssText = "left:" + 100 * b.x / G.W + "%;top:" + 100 * b.y / G.H + "%;width:" + 100 * b.w / G.W +
                      "%;height:" + 100 * b.h / G.H + "%";
    if (!c) s.textContent = P.scenes.length ? "Drop a picture here" : "Drag a picture here from the library to begin";
    else if (many) { s.draggable = true; s.title = "Click to change this picture; drag it onto another place to swap the two."; }
    s.addEventListener("dragstart", e => { DRAG = {cell: j}; e.dataTransfer.setData("text/plain", "cell");
                                           e.dataTransfer.effectAllowed = "move"; });
    s.addEventListener("dragend", endDrag);
    s.addEventListener("dragover", e => {
      if (!(DRAG && (DRAG.lib || DRAG.cell != null)) && !hasFiles(e)) return;
      e.preventDefault(); e.dataTransfer.dropEffect = DRAG && DRAG.cell != null ? "move" : "copy"; s.classList.add("over");
    });
    s.addEventListener("dragleave", () => s.classList.remove("over"));
    s.addEventListener("drop", e => {
      e.preventDefault(); e.stopPropagation();
      const d = DRAG, files = e.dataTransfer.files;
      endDrag(); setPlaying(false);
      if (d && d.cell != null) {
        const cells = P.scenes[sel.scene].cells, a = cells[d.cell];
        if (d.cell !== j) { cells[d.cell] = cells[j]; cells[j] = a; sel.cell = j; changed(); }
      } else work = (async () => place(d ? [d.lib] : await upload(files), {cell: j}))();
    });
    s.addEventListener("click", () => { setPlaying(false); sel.cell = j; renderSlots(); renderSide(); });
    box.append(s);
  });
}
function paint() {
  const G = geo(), cv = $("c");
  if (cv.width !== G.W || cv.height !== G.H) { cv.width = G.W; cv.height = G.H; }
  fit(); drawAt(CTX, G, T, {});
  const tot = total(), s = $("seek"), now = P.scenes.length ? at(T) : null;
  s.max = Math.max(0, tot - 1); s.value = Math.floor(T);
  $("clock").textContent = (T / 100).toFixed(1) + " / " + (tot / 100).toFixed(1) + " s";
  document.querySelectorAll("#tl .card").forEach((card, i) => {
    const on = now && now.i === i;
    card.classList.toggle("now", !!on);
    card.querySelector(".run").style.width = on ? 100 * now.lt / durOf(P.scenes[i]) + "%" : "0";
  });
}
function setPlaying(on) {
  if (on === playing) return;
  playing = on && P.scenes.length > 0;
  if (playing && T >= total() - 1) T = 0;
  if (!playing && P.scenes.length) {               // stopped: the scene it stopped on is the one being changed
    const i = at(T).i;
    if (i !== sel.scene) { sel = {scene: i, cell: null}; renderTimeline(); renderSlots(); renderSide(); }
  }
  document.body.classList.toggle("playing", playing); $("play").textContent = playing ? "Pause" : "Play"; dirty = true;
}
let before = 0;
function tick(now) {
  requestAnimationFrame(tick);
  const dt = now - before; before = now;
  if (busy || !P) return;
  if (playing) {
    const tot = total(); T += dt / 10;
    if (T >= tot) { if (P.loop && tot > 0) T %= tot; else { T = Math.max(0, tot - 1); setPlaying(false); } }
    dirty = true;
  }
  sync();
  if (dirty) { dirty = false; paint(); }
  if (thumbs && now - thumbsAt > 150) { thumbs = false; thumbsAt = now; renderThumbs(); }
}

// ---------- the settings ----------
const field = (name, control) => { const f = el("label", "f"); f.append(el("span", "", name), control); return f; };
function choose(options, value, on) {
  const s = el("select");
  for (const [v, t] of options) { const o = el("option", "", t); o.value = v; s.append(o); }
  s.value = value; s.addEventListener("change", () => on(s.value));
  return s;
}
function text(value, hint, on) {
  const i = el("input"); i.type = "text"; i.value = value; i.placeholder = hint;
  i.addEventListener("input", () => on(i.value)); i.addEventListener("change", commit);
  return i;
}
// seconds in a box (and a slider beside it when there is a range worth sliding over)
function seconds(cs, lo, hi, on, slider) {
  const w = el("span", "sec"), i = el("input"), r = slider ? el("input") : null;
  const set = v => { v = int(v, lo, hi, cs); cs = v; on(v); };
  i.type = "number"; i.step = "0.1"; i.min = lo / 100; i.max = hi / 100; i.value = secs(cs);
  i.addEventListener("input", () => { const v = parseFloat(i.value) * 100; if (isFinite(v) && v >= lo && v <= hi) { set(v); if (r) r.value = cs; } });
  i.addEventListener("change", () => { i.value = secs(cs); commit(); });
  if (r) { r.type = "range"; r.min = lo; r.max = hi; r.step = 2; r.value = cs;
           r.addEventListener("input", () => { set(r.value); i.value = secs(cs); });
           r.addEventListener("change", commit); w.append(r); }
  w.append(i, "s"); w.box = i;
  return w;
}
function checkbox(name, value, on) {
  const l = el("label", "c"), i = el("input"); i.type = "checkbox"; i.checked = value;
  i.addEventListener("change", () => on(i.checked)); l.append(i, name);
  return l;
}
const button = (name, on, cls, tip) => { const b = el("button", cls || "plain", name); if (tip) b.title = tip;
                                         b.addEventListener("click", on); return b; };
let auto = null;                                   // the chosen scene's "stays for" box, while it follows its clip
function touchSide() {
  const G = geo(), d = $("dims");
  if (d) d.textContent = "The GIF will be " + G.W + " x " + G.H + " pixels, " + (total() / 100).toFixed(1) + " s long.";
  if (auto && P.scenes[sel.scene] && !P.scenes[sel.scene].dur) auto.value = secs(durOf(P.scenes[sel.scene]));
}
function renderSide() {
  const a = $("pgif"), b = $("pscene"), c = $("ppic"), m = $("pmake"), sc = P.scenes[sel.scene], many = places() > 1;
  for (const p of [a, b, c, m]) p.textContent = "";
  auto = null;
  a.append(el("h2", "", "The GIF"),
    field("Layout", choose(LAYOUTS.map(l => [l[0] + "x" + l[1], l[2]]), P.cols + "x" + P.rows, v => {
      const n = v.split("x").map(Number); relayout(n[0], n[1]); changed(); })),
    field("Size", choose([[1, "Small: game pixels x1"], [2, "Medium: x2 (the site's)"], [3, "Large: x3"]],
                         P.scale, v => { P.scale = +v; changed(); })),
    field("Title bar", text(P.title, "none", v => { P.title = v; changed({typing: true}); })),
    field("Captions", choose([["below", "Under the pictures"], ["on", "On the pictures"], ["off", "None"]],
                             P.captions, v => { P.captions = v; changed(); })),
    field("A still stays", seconds(P.hold, 10, 6000, v => { P.hold = v; changed({typing: true}); })),
    field("Movement", choose([[4, "Smooth: 25 a second"], [6, "The site's clips: 16.7"], [10, "Light: 10 a second"]],
                             P.step, v => { P.step = +v; changed(); })),
    checkbox("Plays over and over", P.loop, v => { P.loop = v; changed(); }));
  const dims = el("p", "hint"); dims.id = "dims"; a.append(dims);

  if (sc) {
    const i = sel.scene, follows = sc.cells.some(x => runs(x) > 0);
    const own = checkbox(follows ? "As long as its clip runs" : "As long as a still stays", !sc.dur,
                         v => { sc.dur = v ? 0 : durOf(sc); changed(); });
    const stays = seconds(durOf(sc), 10, 60000, v => { sc.dur = v; own.firstChild.checked = false; auto = null;
                                                       changed({typing: true}); });
    if (!sc.dur) auto = stays.box;
    b.append(el("h2", "", "Scene " + (i + 1) + " of " + P.scenes.length), field("Stays for", stays), own);
    if (i > 0) {
      b.append(field("Comes in", choose(TRS, sc.tr, v => { sc.tr = v; T = startOf(i); changed(); setPlaying(true); })));
      if (sc.tr !== "cut") b.append(field("Over", seconds(sc.trDur, 4, 300, v => { sc.trDur = v; changed({typing: true}); })));
    }
    b.append((() => { const r = el("div", "row"); r.append(
      button("Earlier", () => moveScene(i, i - 1), "", "Move this scene one place earlier"),
      button("Later", () => moveScene(i, i + 2), "", "Move this scene one place later"),
      button("Copy", () => copyScene(i), "", "A second scene just like this one, after it (Ctrl+D)"),
      button("Remove", () => removeScene(i), "", "Take this scene out of the GIF (Del)"));
      r.children[0].disabled = i === 0; r.children[1].disabled = i === P.scenes.length - 1; return r; })());

    const j = many ? sel.cell : 0, cell = j == null ? null : sc.cells[j], it = item(cell);
    if (many && j == null) c.append(el("h2", "", "Picture"), el("p", "hint", "Click a picture in the middle to change its caption, its fit or where its clip starts."));
    else if (!cell) c.append(el("h2", "", "Picture"), el("p", "hint", "This place is empty: drag a picture onto it."));
    else {
      c.append(el("h2", "", many ? "Picture " + (j + 1) : "Picture"),
        el("p", "hint", it.name + (it.kind === "clip" ? ", a clip of " + (it.len || 0).toFixed(1) + " s"
                                   : it.kind === "gif" ? ", a GIF of " + secs(it.total) + " s" : "")),
        field("Caption", text(cell.caption, "none", v => { cell.caption = v; changed({typing: true}); })),
        field("In its place", choose([["fit", "All of it fits"], ["fill", "Fills it (edges cut)"]], cell.fit,
                                     v => { cell.fit = v; changed(); })));
      const len = it.kind === "gif" ? it.total : it.kind === "clip" ? Math.round((it.len || 0) * 100) : 0;
      if (len > 20) c.append(field("Starts at", seconds(cell.start, 0, len - 10, v => {
        cell.start = v; T = startOf(i) + trOf(i); changed({typing: true}); }, true)));
      c.append((() => { const r = el("div", "row"); r.append(button("Remove the picture", () => clearCell(i, j))); return r; })());
    }
  } else b.append(el("h2", "", "Scene"), el("p", "hint", "Nothing yet: drag a picture from the library on the left to the timeline at the bottom."));

  m.append(el("h2", "", "Make it"), field("Name", text(P.name, "my-gif", v => { P.name = v; changed({typing: true}); })),
           button("Make the GIF", make, "act go"));
  touchSide();
}
function say(text, kind) { const m = $("msg"); m.textContent = text || ""; m.className = kind || ""; }

// ---------- making the GIF ----------
async function make() {
  if (busy) return null;
  if (!P.scenes.some(sc => sc.cells.some(Boolean))) { say("There is nothing to make a GIF of yet: drag a picture to the timeline first.", "bad"); return null; }
  setPlaying(false); commit();
  busy = true; halt = false; document.body.classList.add("busy"); say("", "");
  const bar = $("prog"), words = $("busytext");
  let done = null;
  try {
    words.textContent = "Getting the pictures ready..."; bar.removeAttribute("value");
    for (const sc of P.scenes) for (const c of sc.cells) {
      const it = item(c);
      if (!it) continue;
      if (it.kind === "clip") { await need(it.id); await loaded(vid(c)); }
      else await picReady(it.kind === "gif" ? "/sheet/" + enc(it.id) : fileUrl(it));
    }
    const G = geo(), plan = schedule(), cv = $("c");
    if (cv.width !== G.W || cv.height !== G.H) { cv.width = G.W; cv.height = G.H; }
    const job = await post("/job", {w: G.W, h: G.H});
    if (!job.ok) throw new Error(job.error);
    words.textContent = "Drawing the frames..."; bar.max = plan.length; bar.value = 0;
    for (let k = 0; k < plan.length; k++) {
      if (halt) throw new Error("Stopped: no GIF was written.");
      const f = plan[k];
      await exact(f.t); drawAt(CTX, G, f.t, {bias: f.bias});
      const r = await (await fetch("/frame?job=" + job.job + "&i=" + k + "&cs=" + f.cs + "&seg=" + f.seg,
                                   {method: "POST", body: CTX.getImageData(0, 0, G.W, G.H).data})).json();
      if (!r.ok) throw new Error(r.error);
      bar.value = k + 1;
    }
    words.textContent = "Writing the GIF..."; bar.removeAttribute("value");
    const r = await post("/finish", {job: job.job, name: P.name, loop: P.loop, project: P});
    if (!r.ok) throw new Error(r.error);
    done = r; made(r); listSaved(r.saved);
  } catch (e) {
    say(e instanceof TypeError ? "The editor's window does not answer: is it still open?" : String(e.message || e), "bad");
  }
  busy = false; document.body.classList.remove("busy"); dirty = true;
  return done;
}
function made(r) {
  const box = $("made"), im = el("img"), mb = r.bytes / 1048576;
  box.textContent = ""; im.src = "/out/" + encodeURIComponent(r.file) + "?" + Date.now(); im.alt = "The GIF that was made";
  const row = el("div", "row");
  row.append(button("Show it in its folder", () => post("/reveal", {file: r.file})));
  box.append(im, el("p", "hint", r.path), row);
  say(r.file + " is made: " + r.w + " x " + r.h + ", " + r.frames + (r.frames === 1 ? " frame, " : " frames, ") +
      (mb >= 1 ? mb.toFixed(1) + " MB" : Math.max(1, Math.round(r.bytes / 1024)) + " KB") + "." +
      (mb > 10 ? "\nOver 10 MB: Discord takes it only with Nitro. A smaller size, the light movement or shorter clips make it lighter." : ""),
      "good");
}
function listSaved(names) {
  const s = $("open"); s.textContent = "";
  const first = el("option", "", names.length ? "Open..." : "Open (nothing saved yet)"); first.value = ""; s.append(first);
  for (const n of names) { const o = el("option", "", n); o.value = n; s.append(o); }
  s.value = ""; s.disabled = !names.length;
}

// ---------- buttons and keys ----------
$("play").addEventListener("click", () => setPlaying(!playing));
$("seek").addEventListener("input", () => {
  setPlaying(false); T = +$("seek").value;
  const i = at(T).i;
  if (P.scenes.length && i !== sel.scene) { sel = {scene: i, cell: null}; renderTimeline(); renderSlots(); renderSide(); }
  dirty = true;
});
$("find").addEventListener("input", renderLib);
$("undo").addEventListener("click", () => step(-1));
$("redo").addEventListener("click", () => step(1));
$("stop").addEventListener("click", () => { halt = true; });
$("new").addEventListener("click", () => {
  if (P.scenes.length && !confirm("Start an empty GIF? (Undo brings this one back; Open has it if it was made or saved.)")) return;
  work = use(fresh(), ""); $("made").textContent = "";
});
$("open").addEventListener("change", async () => {
  const name = $("open").value; $("open").value = "";
  if (!name) return;
  const r = await (await fetch("/project?name=" + encodeURIComponent(name))).json();
  if (!r.ok) return say(r.error, "bad");
  work = use(r.project, name + " is open: change it and make it again."); $("made").textContent = "";
});
$("save").addEventListener("click", async () => {
  commit();
  const r = await post("/save", {name: P.name, project: P});
  if (r.ok) { listSaved(r.saved); say("Saved as " + r.name + ". Open brings it back.", "good"); } else say(r.error, "bad");
});
$("quit").addEventListener("click", async () => {
  await post("/draft", P).catch(() => {}); await post("/quit", {}).catch(() => {});
  P = null; document.body.innerHTML = "<p style='padding:24px'>The editor is closed. You can close this tab.</p>";
});
document.addEventListener("keydown", e => {
  if (busy || !P) return;
  const typing = /^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName) && e.target.type !== "range" && e.target.type !== "checkbox";
  const ctrl = e.ctrlKey || e.metaKey, k = e.key.toLowerCase();
  if (ctrl && k === "z" && !typing) { e.preventDefault(); step(e.shiftKey ? 1 : -1); }
  else if (ctrl && k === "y" && !typing) { e.preventDefault(); step(1); }
  else if (typing) return;
  else if (ctrl && k === "d" && P.scenes.length) { e.preventDefault(); copyScene(sel.scene); }
  else if (e.key === " ") { e.preventDefault(); setPlaying(!playing); }
  else if ((e.key === "Delete" || e.key === "Backspace") && P.scenes.length) {
    e.preventDefault();
    if (places() > 1 && sel.cell != null && P.scenes[sel.scene].cells[sel.cell]) clearCell(sel.scene, sel.cell);
    else removeScene(sel.scene);
  }
  else if (e.key === "ArrowLeft" && sel.scene > 0) { e.preventDefault(); select(sel.scene - 1, null); }
  else if (e.key === "ArrowRight" && sel.scene < P.scenes.length - 1) { e.preventDefault(); select(sel.scene + 1, null); }
});
// files from a folder may be dropped anywhere: on the timeline and on the picture they go into the GIF as well,
// anywhere else only into the library
let over = 0;
window.addEventListener("dragenter", e => { if (hasFiles(e)) { over++; document.body.classList.add("files"); } });
window.addEventListener("dragleave", e => { if (hasFiles(e) && --over <= 0) { over = 0; document.body.classList.remove("files"); } });
window.addEventListener("dragover", e => { if (hasFiles(e)) { e.preventDefault(); e.dataTransfer.dropEffect = "copy"; } });
window.addEventListener("drop", e => {
  over = 0; document.body.classList.remove("files");
  if (!hasFiles(e)) return;
  e.preventDefault(); work = upload(e.dataTransfer.files);
});
window.addEventListener("resize", () => { dirty = true; });

async function load() {
  const d = await (await fetch("/library")).json();
  GROUPS = d.groups; LIB = {};
  for (const g of GROUPS) for (const it of g.items) LIB[it.id] = it;
  listSaved(d.saved); renderLib();
  P = fresh();
  await use(d.draft || fresh(), "");
  hist = [JSON.stringify(P)]; hpos = 0; refresh();
  requestAnimationFrame(tick);
  // your own videos get the still the library shows them by
  for (const it of GROUPS[0].items) if (it.kind === "clip") try { await need(it.id); } catch (e) {}
  if (GROUPS[0].items.some(it => it.thumb)) renderLib();
}

// for trying the page out without a hand on the mouse: ?selftest drags pictures in, changes things and makes
// three GIFs (stills with a fade and a slide; a clip and a short GIF; a 2 x 2 with a title)
load().then(async () => {
  if (!location.search.includes("selftest")) return;
  const out = el("pre"); out.id = "selftest"; out.style.display = "none"; document.body.appendChild(out);
  const lines = [], log = s => { lines.push(s); out.textContent = lines.join("\n"); };
  const tileOf = id => document.querySelector('.tile[data-id="' + id + '"]');
  const drag = async (from, to, x, y) => {
    const dt = new DataTransfer(), o = {bubbles: true, cancelable: true, dataTransfer: dt, clientX: x, clientY: y};
    from.dispatchEvent(new DragEvent("dragstart", {bubbles: true, dataTransfer: dt}));
    to.dispatchEvent(new DragEvent("dragover", o)); to.dispatchEvent(new DragEvent("drop", o));
    from.dispatchEvent(new DragEvent("dragend", {bubbles: true, dataTransfer: dt}));
    await work;
  };
  const cards = () => [...document.querySelectorAll("#tl .card")];
  const order = () => P.scenes.map(sc => sc.cells.map(c => c ? c.src.split("/")[1].replace(/\.\w+$/, "") : "-").join("+")).join(" ");
  const gif = r => r ? r.file + " " + r.w + "x" + r.h + " " + r.frames + " frames " + r.bytes + " bytes" : "FAILED: " + $("msg").textContent;
  try {
    log("library " + GROUPS.map(g => g.title + " " + g.items.length).join(", "));
    await use(fresh(), ""); P.name = "selftest-stills";
    const tl = $("tl"), box = () => tl.getBoundingClientRect();
    await drag(tileOf("shot/dexnav-ui.png"), tl, box().left + 30, box().top + 40);
    await drag(tileOf("shot/key-ring.png"), tl, box().right - 10, box().top + 40);
    await drag(tileOf("shot/bag-999.png"), tl, box().left + 5, box().top + 40);
    log("dragged in: " + order());
    let r = cards()[0].getBoundingClientRect();
    await drag(cards()[0], tl, cards()[2].getBoundingClientRect().right + 4, r.top + 20);
    log("first dragged to the end: " + order() + " chosen " + (sel.scene + 1));
    tileOf("shot/both-bikes.png").dispatchEvent(new MouseEvent("dblclick", {bubbles: true})); await work;
    log("double-click: " + order());
    P.scenes[1].tr = "fade"; P.scenes[2].tr = "slide"; P.scenes[3].tr = "dark"; P.scenes[1].dur = 150; changed();
    log("captions: " + P.scenes.map(sc => sc.cells[0].caption).join(" | "));
    log("plan: " + schedule().map(f => f.seg + ":" + f.cs).join(" "));
    log(gif(await make()));
    step(-1); log("undo: " + P.scenes.map(sc => sc.tr).join(",")); step(1);
    log("redo: " + P.scenes.map(sc => sc.tr).join(","));

    await use(fresh(), ""); P.name = "selftest-clip"; P.captions = "on";
    await place(["clip/arceus", "shot/bag-sort.gif"], {at: 0});
    P.scenes[0].cells[0].start = 300; P.scenes[0].dur = 120; P.scenes[1].tr = "fade"; changed();
    log("clip: " + LIB["clip/arceus"].len.toFixed(2) + " s, scenes " + P.scenes.map(sc => secs(durOf(sc))).join(" + "));
    log(gif(await make()));

    await use(fresh(), ""); P.name = "selftest-grid"; relayout(2, 2); P.title = "Hyper Emerald v5.7 · English + QoL"; changed();
    await place(["shot/questlog-panel-legends.png", "clip/dexnav-screen", "shot/key-ring.png"], null);
    log("2 x 2, three in: " + order());
    const slot = n => document.querySelectorAll("#slots .slot")[n], mid = e => { const b = e.getBoundingClientRect(); return [b.left + b.width / 2, b.top + b.height / 2]; };
    await drag(tileOf("clip/fast-surf"), slot(3), ...mid(slot(3)));
    log("dropped on the fourth place: " + order());
    await drag(slot(0), slot(1), ...mid(slot(1)));
    log("first dragged onto the second: " + order());
    P.scenes[0].dur = 150; changed();
    await drag(tileOf("shot/journal.png"), tl, box().right - 10, box().top + 40);
    log("one more on the timeline: " + order());
    log(gif(await make()));
    relayout(1, 1); changed(); log("back to one picture: " + order());
    await new Promise(ok => setTimeout(ok, 400));
    log("done");
  } catch (e) { log("ERROR " + (e && e.stack || e)); }
  out.dataset.done = "1";
});
</script>
</body></html>
"""


class Server(http.server.ThreadingHTTPServer):
    """Listens on a port nobody else has. (Python's servers ask to "reuse" their address, and on Windows that
    lets two programs listen on one port, each getting some of the requests.)"""
    allow_reuse_address = False

    def server_bind(self):
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


def main(folder):
    print("GIF editor")
    print("Reading the website's pictures...")
    lib = Library(folder)
    print("%d pictures, GIFs and clips; the GIFs go to %s" % (len(lib.items), lib.folder))
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
    server.RequestHandlerClass = handler(lib, server.shutdown)
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
    sys.exit(main(args[0] if args else FOLDER))
