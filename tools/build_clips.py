"""Cut the six README montage GIFs (docs/showcase/showcase-*.gif, a 3x3 grid of captioned clips each) into
one small MP4 and one PNG poster per clip, for the guide site.

usage: FFMPEG=<path to ffmpeg> python tools/build_clips.py
       python tools/build_clips.py --posters        (redo the poster frames only; no ffmpeg needed)
writes docs/showcase/clips/<slug>.mp4 + <slug>.png and site/src/data/clips.json

The montages are 1476x1114: a 44 px title bar, then three rows of three 480x320 cells (a GBA screen at 2x) with
a caption strip under each. A 27 MB set of GIFs becomes about 5 MB of video the site can load on demand.
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

XS, YS, W, H = (10, 498, 986), (44, 400, 756), 480, 320

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
]

# clips whose mid-point frame is a washed-out transition
BUSIEST_POSTER = {"cynthia-champion", "dexnav-patch"}

os.makedirs(OUT, exist_ok=True)
os.makedirs(DATA, exist_ok=True)
meta = []
for gif, group, cells in MONTAGES:
    src = os.path.join(SHOW, gif + ".gif")
    im = Image.open(src)
    assert im.size == (1476, 1114), "%s is not a 1476x1114 montage" % gif
    # A clip's poster is the frame 3.6 s in, where each clip shows its subject - unless that frame is a
    # fade to black or a white flash, in which case the busiest frame of the clip is used instead.
    frames = []
    for f in range(0, im.n_frames, 6):
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
    print(gif, "->", len(cells), "clips")

json.dump(meta, open(os.path.join(DATA, "clips.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
total = sum(os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT))
print("%d files, %.1f MB in %s" % (len(os.listdir(OUT)), total / 1e6, OUT))
