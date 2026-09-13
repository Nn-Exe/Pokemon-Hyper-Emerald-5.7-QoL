"""Build docs/data/search.json for the guide site's client-side search.

usage: python tools/build_search_index.py
Scans every docs/*.html page, splits <main> by h2/h3 headings and writes one
record per section: {url, page, title, text}.  Re-run after editing any page.
"""
import glob
import json
import os
import re
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(HERE, "..", "docs")


class Extractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_main = False
        self.depth = 0
        self.page_title = ""
        self.in_title = False
        self.sections = []  # [id, title, text]
        self.cur_head = None  # (tag, id)
        self.head_text = ""
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title":
            self.in_title = True
        if tag == "main":
            self.in_main = True
            self.sections.append(["", "", ""])
            return
        if not self.in_main:
            return
        if tag in ("script", "style", "template"):
            self.skip += 1
        if tag in ("h1", "h2", "h3"):
            self.cur_head = (tag, a.get("id", ""))
            self.head_text = ""

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        if tag == "main":
            self.in_main = False
        if not self.in_main:
            return
        if tag in ("script", "style", "template") and self.skip:
            self.skip -= 1
        if self.cur_head and tag == self.cur_head[0]:
            title = re.sub(r"\s+", " ", self.head_text).strip().rstrip("#").strip()
            sid = self.cur_head[1] or slug(title)
            if tag == "h1":
                self.sections[0][1] = title
            else:
                self.sections.append([sid, title, ""])
            self.cur_head = None

    def handle_data(self, data):
        if self.in_title:
            self.page_title += data
        if not self.in_main or self.skip:
            return
        if self.cur_head:
            self.head_text += data
        else:
            self.sections[-1][2] += data + " "


def slug(s):
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s[:60] or "s"


def main():
    out = []
    for path in sorted(glob.glob(os.path.join(DOCS, "*.html"))):
        name = os.path.basename(path)
        p = Extractor()
        p.feed(open(path, encoding="utf-8").read())
        page = p.page_title.split("—")[0].strip() or name
        used = {}
        for sid, title, text in p.sections:
            text = re.sub(r"\s+", " ", text).strip()
            if not text and not title:
                continue
            if sid:
                base, i = sid, 2
                while sid in used:
                    sid = f"{base}-{i}"
                    i += 1
                used[sid] = True
            url = name + (f"#{sid}" if sid else "")
            out.append({"url": url, "page": page, "title": title or page, "text": text[:1200]})
    os.makedirs(os.path.join(DOCS, "data"), exist_ok=True)
    dst = os.path.join(DOCS, "data", "search.json")
    json.dump(out, open(dst, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"wrote {len(out)} sections to {os.path.relpath(dst)}")


if __name__ == "__main__":
    main()
