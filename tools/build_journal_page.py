"""Build docs/journal.html: every Journal objective in the order the game gives them, from
patches/journal/steps.py (the table the ROM's Journal is built from), so the page always matches the game.

    python tools/build_journal_page.py

The page uses the guide's own stylesheet and script. It is not linked from the site's navigation.
"""
import html, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "patches", "journal"))
import steps as S

PARTS = [
    (S.HOENN, "hoenn", "Hoenn", "From Littleroot Town to the Champion."),
    (S.POST, "postgame", "Post-game", "Interpol, the Delta Episode, the Ultra Wormholes and the Tapus."),
    (S.SINNOH, "sinnoh", "Sinnoh", "The eight Sinnoh gyms and the League."),
    (S.LOST, "lost", "Lost Artifacts", "Waji, the Plates, Giratina, Arceus and Volo."),
]


def esc(s):
    return html.escape(s, quote=False)


def step_html(n, header, st, text):
    tags = []
    if not st["anchor"]:
        tags.append('<span class="tag warn" title="Can be done early or out of order; the Journal never '
                    'skips ahead because of it">any order</span>')
    out = ['<li class="step" id="step-%d"><span class="num">%d</span><div>' % (n, n)]
    out.append('<p class="title">%s</p>' % esc(S.TITLES[n - 1]))
    out.append("<p>%s %s</p>" % (esc(text), " ".join(tags)))
    if st["mode"] == 2:
        how = ("all of these" if st["list_all"] else
               "in this order: the Journal shows the first one you are missing")
        out.append('<p class="group-label">%s <span class="src">(%s)</span></p><ul class="members">'
                   % (esc(st["label"].rstrip(":")), how))
        for _, weight, member in st["members"]:
            out.append("<li>%s%s</li>" % (esc(member), " <span class='src'>(counts twice)</span>" if weight > 1 else ""))
        out.append("</ul>")
    out.append("</div></li>")
    return "".join(out)


def build():
    body = []
    n = 0
    for header, anchor_id, title, blurb in PARTS:
        items = [(h, st, t) for h, st, t in S.STEPS if h == header]
        body.append('<h2 id="%s">%s <span class="src">%d objectives</span></h2>' % (anchor_id, esc(title), len(items)))
        body.append('<p>%s</p><ol class="journal">' % esc(blurb))
        for h, st, t in items:
            n += 1
            body.append(step_html(n, h, st, t))
        body.append("</ol>")
    body.append('<h2 id="done">When everything is done</h2><div class="callout plain"><p class="title">%s</p><p>%s</p></div>'
                % (esc(S.FINAL_TITLE), esc(S.FINAL[1])))

    toc = "".join('<a href="#%s">%s</a>' % (a, esc(t)) for _, a, t, _ in PARTS)
    page = TEMPLATE.replace("{BODY}", "\n".join(body)).replace("{TOC}", toc).replace("{COUNT}", str(n))
    out = os.path.join(ROOT, "docs", "journal.html")
    open(out, "w", encoding="utf-8").write(page)
    print("wrote %s: %d objectives" % (os.path.relpath(out, ROOT), n))


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Journal Objectives — Hyper Emerald v5.7 Guide</title>
<meta name="description" content="Every objective the Journal key item gives, in order, from the table the game's Journal is built from.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@100,700;100,800;100,900&family=Source+Sans+3:ital,wght@0,400;0,600;0,700;1,400&family=Silkscreen&display=swap">
<link rel="stylesheet" href="assets/site.css">
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<style>
ol.journal { list-style: none; padding: 0; margin: 0 0 1.5rem; }
ol.journal > li.step { display: flex; gap: .85rem; align-items: flex-start; padding: .7rem 0; border-bottom: 1px solid var(--line, rgba(127,127,127,.2)); }
ol.journal > li.step > div { flex: 1; min-width: 0; }
ol.journal > li.step p { margin: 0; }
.num { flex: none; min-width: 2.2rem; text-align: right; font-variant-numeric: tabular-nums; font-weight: 700; opacity: .55; }
.title { font-weight: 700; }
.group-label { margin-top: .45rem !important; font-weight: 650; }
ul.members { margin: .3rem 0 0; padding-left: 1.2rem; }
ul.members li { margin: .15rem 0; }
.jump { display: flex; flex-wrap: wrap; gap: .5rem 1rem; margin: 1rem 0 1.5rem; }
</style>
</head>
<body>
<div class="shell">
<main class="content">
<div class="prose wide">
<p class="eyebrow">Reference</p>
<h1>Journal objectives</h1>
<p class="lede">Every objective the <strong>Journal</strong> key item can give — {COUNT} of them, in the order the game gives them. Use the Journal from the Bag (or register it to SELECT) and its Quest Log lists them by chapter, with the titles below, and marks the first one you have not done.</p>
<div class="callout plain">
<span class="title">How the Journal picks one</span>
<p>It finds the last objective you finished that can only happen in order, then shows the first unfinished one after it. Objectives tagged <span class="tag warn">any order</span> can be done early or skipped for a while; doing one early never makes the Journal jump ahead. For groups (badges, Tapu trials, Plates) it also shows your progress and what is still missing.</p>
</div>
<p class="jump">{TOC}<a href="#done">When everything is done</a></p>
{BODY}
<p class="src">Generated from <code>patches/journal/steps.py</code> by <code>tools/build_journal_page.py</code>.</p>
</div>
</main>
<aside class="toc-rail"></aside>
</div>
<script src="assets/site.js"></script>
</body>
</html>
"""

if __name__ == "__main__":
    build()
