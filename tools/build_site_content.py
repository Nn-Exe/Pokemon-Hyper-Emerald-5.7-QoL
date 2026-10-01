"""Export the two hand-written tables the guide site shares with the game's tools.

    python tools/build_site_content.py

site/src/data/journal.json       every Journal objective, from patches/journal/steps.py (the table the ROM's
                                 Journal is built from), so the page always matches the game
site/src/data/side-content.json  the side content outside the Journal, from tools/build_audit_page.py's curated
                                 list (written from reading the scripts); the flag numbers stay in the tool
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "patches", "journal"))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import steps as S  # noqa: E402
from build_audit_page import CURATED  # noqa: E402

OUT = os.path.join(ROOT, "site", "src", "data")
PARTS = [
    (S.HOENN, "hoenn", "Hoenn", "From Littleroot Town to the Champion."),
    (S.POST, "post-game", "Post-game", "Interpol, the Delta Episode, the Ultra Wormholes and the Tapus."),
    (S.SINNOH, "sinnoh", "Sinnoh", "The eight Sinnoh gyms and the League."),
    (S.LOST, "lost-artifacts", "Lost Artifacts", "Waji, the Plates, Giratina, Arceus and Volo."),
]

chapters, n = [], 0
for header, key, title, blurb in PARTS:
    steps = []
    for h, st, text in S.STEPS:
        if h != header:
            continue
        n += 1
        step = {"n": n, "title": S.TITLES[n - 1], "text": text, "anyOrder": not st["anchor"]}
        if st["mode"] == 2:
            step["group"] = {"label": st["label"].rstrip(":"), "all": bool(st["list_all"]),
                             "members": [{"text": member, "twice": weight > 1} for _, weight, member in st["members"]]}
        steps.append(step)
    chapters.append({"key": key, "title": title, "blurb": blurb, "steps": steps})

os.makedirs(OUT, exist_ok=True)
json.dump({"count": n, "chapters": chapters, "final": {"title": S.FINAL_TITLE, "text": S.FINAL[1]}},
          open(os.path.join(OUT, "journal.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump([{"title": title, "blurb": blurb, "rows": [{"where": where, "what": what} for where, what, _ in rows]}
           for title, blurb, rows in CURATED],
          open(os.path.join(OUT, "side-content.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("journal: %d objectives in %d chapters | side content: %d groups" % (n, len(chapters), len(CURATED)))
