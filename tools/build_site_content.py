"""Export the two hand-written tables the guide site shares with the game's tools.

    python tools/build_site_content.py

site/src/data/journal.json       every Journal objective, from patches/journal/steps.py (the table the ROM's
                                 Journal is built from), so the page always matches the game; since v1.9 with
                                 Area Zero's optional rows, which patches/paldea/journal_az.py adds after
                                 "Steven is waiting"
site/src/data/side-content.json  the side content outside the Journal, from tools/build_audit_page.py's curated
                                 list (written from reading the scripts); the flag numbers stay in the tool
"""
import collections
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "patches", "journal"))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(1, os.path.join(ROOT, "patches", "paldea"))
import steps as S  # noqa: E402
import journal_az as AZ  # noqa: E402
from build_audit_page import CURATED  # noqa: E402

OUT = os.path.join(ROOT, "site", "src", "data")
PARTS = [
    (S.HOENN, "hoenn", "Hoenn", "From Littleroot Town to the Champion."),
    (S.POST, "post-game", "Post-game", "Interpol, the Delta Episode, the Ultra Wormholes and the Tapus."),
    (S.SINNOH, "sinnoh", "Sinnoh", "The eight Sinnoh gyms and the League."),
    (S.LOST, "lost-artifacts", "Lost Artifacts", "Waji, the Plates, Giratina, Arceus and Volo."),
]

AREA_ZERO = AZ.rows(collections.defaultdict(int))      # (title, flag that opens it, step, place, picture, text)


def entry(n, title, st, text, optional=False):
    step = {"n": n, "title": title, "text": text, "anyOrder": not st["anchor"] and not optional}
    if optional:
        step["optional"] = True
    if st["mode"] == 2:
        step["group"] = {"label": st["label"].rstrip(":"), "all": bool(st["list_all"]),
                         "members": [{"text": member, "twice": weight > 1} for _, weight, member in st["members"]]}
    return step


chapters, n, optional = [], 0, 0
for header, key, title, blurb in PARTS:
    steps = []
    for i, (h, st, text) in enumerate(S.STEPS):
        if h != header:
            continue
        n += 1
        steps.append(entry(n, S.TITLES[i], st, text))
        if S.TITLES[i] == AZ.AFTER_TITLE:
            for az_title, _, az_step, _, _, az_text in AREA_ZERO:
                n += 1
                optional += 1
                steps.append(entry(n, az_title, az_step, az_text, optional=True))
    chapters.append({"key": key, "title": title, "blurb": blurb, "steps": steps})
assert optional == len(AREA_ZERO), "the Journal has no step titled %r for Area Zero to follow" % AZ.AFTER_TITLE

os.makedirs(OUT, exist_ok=True)
json.dump({"count": n - optional, "optional": optional, "chapters": chapters, "final": {"title": S.FINAL_TITLE, "text": S.FINAL[1]}},
          open(os.path.join(OUT, "journal.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump([{"title": title, "blurb": blurb, "rows": [{"where": where, "what": what} for where, what, _ in rows]}
           for title, blurb, rows in CURATED],
          open(os.path.join(OUT, "side-content.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("journal: %d objectives and %d optional ones in %d chapters | side content: %d groups" % (
    n - optional, optional, len(chapters), len(CURATED)))
