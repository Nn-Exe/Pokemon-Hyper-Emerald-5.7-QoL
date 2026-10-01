"""Draw the guide site's icons and its social card.

    python tools/build_site_images.py

writes site/public/favicon.svg, favicon-32.png, apple-touch-icon.png and images/og.png (1200x630, the picture
a link to the site shows in chat apps), from three clip posters in docs/showcase/clips.
"""
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
PUBLIC = os.path.join(HERE, "..", "site", "public")
CLIPS = os.path.join(HERE, "..", "docs", "showcase", "clips")
os.makedirs(os.path.join(PUBLIC, "images"), exist_ok=True)

GREEN_A, GREEN_B = (63, 194, 136), (16, 96, 63)

SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#3fc288"/><stop offset="1" stop-color="#10603f"/></linearGradient></defs>
<rect width="64" height="64" rx="15" fill="url(#g)"/>
<g fill="none" stroke="#fff" stroke-width="5" stroke-linecap="round"><circle cx="32" cy="32" r="19"/><path d="M13 32h11m16 0h11"/></g>
<circle cx="32" cy="32" r="7" fill="#fff"/>
</svg>
"""
open(os.path.join(PUBLIC, "favicon.svg"), "w", encoding="utf-8").write(SVG)


def font(size, bold=True):
    for name in (("segoeuib.ttf", "arialbd.ttf") if bold else ("segoeui.ttf", "arial.ttf")):
        for folder in (r"C:\Windows\Fonts", "/usr/share/fonts/truetype/dejavu", "/Library/Fonts"):
            path = os.path.join(folder, name)
            if os.path.exists(path):
                return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def gradient(w, h, a, b):
    im = Image.new("RGB", (w, h))
    px = im.load()
    for y in range(h):
        for x in range(w):
            t = (x / w + y / h) / 2
            px[x, y] = tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))
    return im


def mark(size):
    """the brand mark, drawn at 4x and scaled down for clean edges"""
    s = size * 4
    im = gradient(s, s, GREEN_A, GREEN_B).convert("RGBA")
    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, s - 1, s - 1), radius=round(s * 0.235), fill=255)
    im.putalpha(mask)
    d = ImageDraw.Draw(im)
    c, r, w = s / 2, s * 0.297, round(s * 0.078)
    d.ellipse((c - r, c - r, c + r, c + r), outline="white", width=w)
    d.line((c - r, c, c - s * 0.125, c), fill="white", width=w)
    d.line((c + s * 0.125, c, c + r, c), fill="white", width=w)
    k = s * 0.11
    d.ellipse((c - k, c - k, c + k, c + k), fill="white")
    return im.resize((size, size), Image.LANCZOS)


mark(32).save(os.path.join(PUBLIC, "favicon-32.png"))
touch = Image.new("RGBA", (180, 180), (16, 96, 63, 255))
touch.alpha_composite(mark(180))
touch.convert("RGB").save(os.path.join(PUBLIC, "apple-touch-icon.png"))

# ---- social card ----
W, H = 1200, 630
card = gradient(W, H, (13, 30, 23), (10, 58, 40)).convert("RGBA")
d = ImageDraw.Draw(card)
for i, x in enumerate(range(-200, W, 34)):          # the faint diagonal rules the page heroes use
    d.line((x, H, x + 120, 0), fill=(255, 255, 255, 9), width=1)

shots = [("opening-legends", (660, 60), 2.0, -2), ("volo-hoopa-eternatus", (600, 330), 1.0, 2),
         ("dexnav-screen", (890, 380), 0.62, -1.5)]
for slug, (x, y), scale, angle in shots:
    shot = Image.open(os.path.join(CLIPS, slug + ".png")).convert("RGBA")
    w, h = round(240 * scale * 2), round(160 * scale * 2)
    shot = shot.resize((w, h), Image.NEAREST)
    frame = Image.new("RGBA", (w + 16, h + 16), (255, 255, 255, 255))
    frame.paste(shot, (8, 8))
    frame = frame.rotate(angle, expand=True, resample=Image.BICUBIC)
    card.alpha_composite(frame, (x, y))

shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ds = ImageDraw.Draw(shade)
for x in range(0, 700):                             # keep the text side dark so it reads over the screenshots
    ds.line((x, 0, x, H), fill=(10, 30, 22, round(235 * max(0, 1 - x / 700) ** 0.6)))
card.alpha_composite(shade)
d = ImageDraw.Draw(card)

card.alpha_composite(mark(84), (70, 70))
d.text((172, 84), "HYPER EMERALD GUIDE", font=font(30), fill=(127, 224, 177))
d.text((70, 210), "Two regions.", font=font(78), fill="white")
d.text((70, 300), "Sixteen gyms.", font=font(78), fill="white")
d.text((70, 390), "One guide.", font=font(78), fill=(127, 224, 177))
d.text((72, 510), "Walkthrough · Boss teams · Wild encounters", font=font(30, bold=False), fill=(214, 228, 220))
d.text((72, 552), "Lost Artifacts v5.7  ·  English + QoL patch", font=font(24, bold=False), fill=(160, 184, 172))
card.convert("RGB").save(os.path.join(PUBLIC, "images", "og.png"), optimize=True)
print("wrote favicon.svg, favicon-32.png, apple-touch-icon.png, images/og.png")
