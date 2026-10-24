"""Cut the README montage GIFs (docs/showcase/showcase-*.gif, a 3x3 grid of captioned clips each) and the v1.9
montage (gba-trans/hyper-emerald/showcase/gifs/v1.9.gif, made with tools/gif_editor.py) into one small MP4 and one PNG poster
per clip, for the guide site.

usage: FFMPEG=<path to ffmpeg> python tools/build_clips.py
       python tools/build_clips.py --posters        (redo the poster frames only; no ffmpeg needed)
       python tools/build_clips.py --only v1.9      (one montage; the others' files and entries stay as they are)
writes docs/showcase/clips/<slug>.mp4 + <slug>.png and site/src/data/clips.json

The README montages are 1476x1114: a 44 px title bar, then three rows of three 480x320 cells (a GBA screen at 2x)
with a caption strip under each. The GIF editor's are 1464x1084, with narrower margins. A 27 MB set of GIFs
becomes about 5 MB of video the site can load on demand.
"""
import json
import os
import subprocess
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SHOW = os.path.join(HERE, "..", "docs", "showcase")
OUT = os.path.join(SHOW, "clips")
DATA = os.path.join(HERE, "..", "site", "src", "data")
FFMPEG = os.environ.get("FFMPEG") or "ffmpeg"

W, H = 480, 320
README = {"size": (1476, 1114), "xs": (10, 498, 986), "ys": (44, 400, 756)}       # the six README montages
EDITOR = {"size": (1464, 1084), "xs": (6, 492, 978), "ys": (34, 384, 734)}        # tools/gif_editor.py's

MONTAGES = [
    ("showcase-story-bosses", "Story & bosses", [
        ("opening-legends", "Opening: the legends on the mountain"),
        ("opening-heroes", "Opening: the heroes arrive"),
        ("sky-pillar-rayquaza", "Sky Pillar: Rayquaza descends"),
        ("giovanni-mewtwo", "Giovanni with Mewtwo"),
        ("volo-hoopa-eternatus", "Volo: Hoopa and Eternatus"),
        ("n-reshiram-zekrom", "N: Reshiram and Zekrom"),
        ("red-mt-silver", "Red on Mt. Silver"),
        ("giratina-distortion-world", "Giratina, Distortion World"),
        ("arceus", "Arceus"),
    ]),
    ("showcase-maps-travel", "Maps & travel", [
        ("sinnoh-map-fly", "Sinnoh Map: free cursor, fly"),
        ("hisui-map", "Hisui on the Sinnoh Map"),
        ("hoenn-fly-spots", "Hoenn: a red square for every Fly spot"),
        ("fast-surf", "Hold B: surf twice as fast"),
        ("auto-run", "Auto Run (Option menu)"),
        ("hm-cut", "Cut without a Pokémon that knows it"),
        ("hm-surf", "Surf without a Pokémon that knows it"),
        ("both-bikes", "Both bikes at once"),
        ("l-quick-repel", "L: quick repel"),
    ]),
    ("showcase-bag-menus", "Bag & menus", [
        ("key-ring", "SELECT: key items as a ring"),
        ("pc-anywhere", "PC anywhere: A in the ring"),
        ("no-pc-dungeons", "No PC in six late dungeons"),
        ("bag-sort", "Bag sort (START)"),
        ("bag-999", "999 per item"),
        ("bag-200-slots", "200 item slots"),
        ("instant-text", "Instant text speed"),
        ("move-relearner", "Move relearner in the party"),
        ("nature-changer", "Nature changer, no quiz"),
    ]),
    ("showcase-battle", "Battle", [
        ("type-badges", "Type badges on the foe"),
        ("move-effectiveness", "Move effectiveness"),
        ("shiny-gold-box", "Gold box on shinies"),
        ("quick-ball", "Quick ball throw (R)"),
        ("stat-colours", "Coloured stat changes"),
        ("instant-text-battle", "Instant text in battle"),
        ("english-trainer-names", "English trainer names"),
        ("pokedex-english", "Every Pokédex entry in English"),
        ("cynthia-champion", "Cynthia, Champion"),
    ]),
    ("showcase-dexnav", "DexNav", [
        ("dexnav-screen", "DexNav, Unbound style"),
        ("dexnav-unseen", "Unseen Pokémon are shadows"),
        ("dexnav-search", "A: SEARCH, back to the field"),
        ("dexnav-hunting", "Hunting: the bar and STOP"),
        ("dexnav-patch", "A shaking patch to step on"),
        ("dexnav-rock-fishing", "Rock Smash and Fishing"),
        ("dexnav-real-table", "Every map's real table"),
        ("dexnav-gold-stars", "Gold stars: all six IVs perfect"),
        ("dexnav-chain", "Chain and Search Level"),
    ]),
    ("showcase-questlog", "Quest Log & Journal", [
        ("evolutions-family", "Evolutions: every family"),
        ("evolutions-shadows", "Evolutions: shadows until seen"),
        ("questlog-story", "Quest Log: the story, step by step"),
        ("questlog-legends", "Every legendary tracked"),
        ("questlog-key-items", "Key Items: where to find them"),
        ("questlog-side-content", "Side content checklist"),
        ("sinnoh-badge-case", "Sinnoh badge case"),
        ("questlog-next-objective", "Next objective, with its location"),
        ("questlog-step-detail", "Every step explained"),
    ]),
    # (source, group, cells, layout): a path for a montage that is not in docs/showcase
    (os.path.join(HERE, "..", "..", "showcase", "gifs", "v1.9.gif"), "What's new in v1.9", [
        ("gen9-wild", "The whole of Gen 9, wild all over Hoenn"),
        ("area-zero-hole", "Area Zero: the black hole in Mossdeep City"),
        ("time-rift", "The time rift: the past and the future"),
        ("paradox-wild", "Paradox Pokémon in the crater's tall grass"),
        ("gen9-evolution-items", "New evolution items at the Lilycove Dept. Store"),
        ("move-info-tag", "Move info: hold L (the new magnifier tag)"),
        ("legends-119", "Legends: 119 to catch, Kitakami's locked"),
        ("evolutions-gen9", "Every Gen 9 evolution line"),
        ("questlog-area-zero", "Area Zero side quests in the Quest Log"),
    ], EDITOR),
    # v2.0's montage (the README's first; _testrun/showcase20b/montage.py, the GIF editor's layout)
    ("showcase-v2.0-kitakami", "What's new in v2.0", [
        ("mossui-town", "Mossui Town, Kitakami"),
        ("carmine-bus-stop", "Carmine stops you at the bus stop"),
        ("mask-hall", "Kitakami Hall's Mask Hall"),
        ("ogerpon-loyalty-plaza", "Ogerpon at Loyalty Plaza"),
        ("kieran-night-market", "Kieran at the night market (Mochi Mayhem)"),
        ("area-zero-people", "Area Zero's people, redrawn"),
        ("dex-base-stats", "Pokédex: base stats on R"),
        ("start-menu-clock", "A clock on the Start menu"),
        ("gmax-mark", "The Gigantamax mark on the summary"),
    ], EDITOR),
]

# clips whose mid-point frame is a washed-out transition
BUSIEST_POSTER = {"cynthia-champion", "dexnav-patch"}

os.makedirs(OUT, exist_ok=True)
os.makedirs(DATA, exist_ok=True)
ONLY = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
old_meta = json.load(open(os.path.join(DATA, "clips.json"), encoding="utf-8")) if ONLY else []
meta = []
for gif, group, cells, *layout in MONTAGES:
    layout = layout[0] if layout else README
    src = gif if os.path.isabs(gif) or os.sep in gif else os.path.join(SHOW, gif + ".gif")
    name = os.path.splitext(os.path.basename(src))[0]
    if ONLY and ONLY != name:
        meta += [m for m in old_meta if m["group"] == group]
        continue
    im = Image.open(src)
    assert im.size == layout["size"], "%s is not a %dx%d montage" % ((gif,) + layout["size"])
    XS, YS = layout["xs"], layout["ys"]
    # A clip's poster is the frame 3.6 s in, where each clip shows its subject - unless that frame is a
    # fade to black or a white flash, in which case the busiest frame of the clip is used instead.
    frames = []
    step = 6 if layout is README else 2         # (the editor's frames are 160 ms: every second one, 3.2 s at [10])
    for f in range(0, im.n_frames, step):
        im.seek(f)
        frames.append(im.convert("RGB"))
    parts, maps = ["[0:v]split=%d%s" % (len(cells), "".join("[s%d]" % i for i in range(len(cells))))], []
    for i, (slug, caption) in enumerate(cells):
        x, y = XS[i % 3], YS[i // 3]
        parts.append("[s%d]crop=%d:%d:%d:%d[o%d]" % (i, W, H, x, y, i))
        maps += ["-map", "[o%d]" % i, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23", "-preset", "slow",
                 "-movflags", "+faststart", "-an", os.path.join(OUT, slug + ".mp4")]
        crops = [fr.crop((x, y, x + W, y + H)) for fr in frames]
        busy = lambda c: len(c.resize((120, 80)).getcolors(maxcolors=9600))  # noqa: E731
        best = crops[min(10, len(crops) - 1)]
        if busy(best) < 60 or slug in BUSIEST_POSTER:
            best = max(crops, key=busy)
        best.quantize(colors=256, dither=Image.Dither.NONE).save(os.path.join(OUT, slug + ".png"), optimize=True)
        meta.append({"slug": slug, "caption": caption, "group": group, "width": W, "height": H})
    if "--posters" not in sys.argv:
        subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", src, "-filter_complex", ";".join(parts)] + maps,
                       check=True)
    print(name, "->", len(cells), "clips")

json.dump(meta, open(os.path.join(DATA, "clips.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
total = sum(os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT))
print("%d files, %.1f MB in %s" % (len(os.listdir(OUT)), total / 1e6, OUT))
