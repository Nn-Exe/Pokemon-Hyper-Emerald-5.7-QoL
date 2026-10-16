"""Text encoding, a script assembler with labels, and a blob of symbolic pointers, for the Paldea area.

Copied from an earlier patch of this project (out of the build since 2026-10-07), where every command here
was used in play; the commands added for Paldea are marked below.

Everything here writes into one blob (Blob) that the patcher lays down in free space; pointers between the
blob's pieces (scripts, texts, movements, map data) are symbolic until Blob.link() resolves them.
"""
import json, os, struct

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "tools", "romdata", "out")
GLYPH_W = 0x006542E4                 # the normal font's glyph widths
MSG_W = 204                          # a field message box line, in pixels

CHARS = {c: 0xBB + i for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ")}
CHARS.update({c: 0xD5 + i for i, c in enumerate("abcdefghijklmnopqrstuvwxyz")})
CHARS.update({str(i): 0xA1 + i for i in range(10)})
CHARS.update({" ": 0x00, "!": 0xAB, "?": 0xAC, ".": 0xAD, "-": 0xAE, "'": 0xB4, ",": 0xB8, ":": 0xF0,
              "(": 0x5C, ")": 0x5D, "&": 0x2D, "é": 0x1B, "/": 0xBA, "…": 0xB0, '"': 0xB2})
PLAYER = b"\xFD\x01"


def enc(text):
    out = bytearray(); i = 0
    while i < len(text):
        if text.startswith("{PLAYER}", i):
            out += PLAYER; i += 8
        elif text[i] == '"':                             # opening quote after a space or at the start
            out.append(0xB1 if i == 0 or text[i - 1] in " (" else 0xB2); i += 1
        else:
            assert text[i] in CHARS, "character %r not in the game's charset: %r" % (text[i], text)
            out.append(CHARS[text[i]]); i += 1
    return bytes(out)


def width(rom, b):
    w, k = 0, 0
    while k < len(b):
        if b[k:k + 2] == PLAYER:
            w += 7 * 6; k += 2
        else:
            w += rom[GLYPH_W + b[k]]; k += 1
    return w


def box(rom, text):
    """One paragraph, wrapped to the message box: the first break a new line, every later one a scroll."""
    lines, cur = [], b""
    for word in text.split(" "):
        e = enc(word)
        trial = cur + b"\x00" + e if cur else e
        if cur and width(rom, trial) > MSG_W:
            lines.append(cur); cur = e
        else:
            cur = trial
    lines.append(cur)
    out = bytearray(lines[0])
    for k, line in enumerate(lines[1:]):
        out += (b"\xFE" if k == 0 else b"\xFA") + line
    return bytes(out) + b"\xFF"


def resolve(names_json, wanted, what):
    d = json.load(open(os.path.join(OUT, names_json), encoding="utf-8"))
    for k, v in d.items():
        name = v["name"] if isinstance(v, dict) else v
        if name == wanted:
            return int(k)
    raise AssertionError("%s %r does not exist in this ROM" % (what, wanted))


# ---- movement actions (vanilla Emerald's numbering - measured in this ROM, 2026-09-26: each code applied to the
# player, the step it made logged. An earlier table here had walk at 0x10 (the delays: nobody moved) and delay at
# 0x18-0x1C (a fast step right / turning right in place).)
FACE = {"down": 0x00, "up": 0x01, "left": 0x02, "right": 0x03}
SLOW = {"down": 0x04, "up": 0x05, "left": 0x06, "right": 0x07}
WALK = {"down": 0x08, "up": 0x09, "left": 0x0A, "right": 0x0B}
FAST = {"down": 0x15, "up": 0x16, "left": 0x17, "right": 0x18}
INPLACE = {"down": 0x1D, "up": 0x1E, "left": 0x1F, "right": 0x20}       # walk in place (normal speed)
DELAY = {1: 0x10, 2: 0x11, 4: 0x12, 8: 0x13, 16: 0x14}
EMOTE = {"!": 0x56, "?": 0x57, "!!": 0x59}      # as the game's own scripts use them (0x56 after SE_PIN, x327)
INVISIBLE, VISIBLE = 0x54, 0x55
DIRS = {"down": 1, "up": 2, "left": 3, "right": 4}                   # turnobject / object facing


def moves(spec):
    """'walk up*3, delay 16, face left, !, invisible' -> movement bytes (ended by 0xFE)."""
    out = bytearray()
    for part in [p.strip() for p in spec.split(",") if p.strip()]:
        n = 1
        if "*" in part:
            part, n = part.split("*"); part = part.strip(); n = int(n)
        words = part.split()
        if words[0] in EMOTE:
            out += bytes([EMOTE[words[0]]]) * n
        elif words[0] == "delay":
            d = int(words[1])
            for _ in range(n):
                while d > 0:
                    step = max(k for k in DELAY if k <= d); out.append(DELAY[step]); d -= step
        elif words[0] == "invisible":
            out.append(INVISIBLE)
        elif words[0] == "visible":
            out.append(VISIBLE)
        else:
            table = {"face": FACE, "slow": SLOW, "walk": WALK, "fast": FAST, "inplace": INPLACE}[words[0]]
            out += bytes([table[words[1]]]) * n
    return bytes(out) + b"\xFE"


class Script:
    """The game's script commands, assembled with labels. Pointer targets: a label (str), ("text", key),
    ("move", key), ("script", name) or an absolute address (int)."""

    def __init__(self, name):
        self.name = name; self.b = bytearray(); self.labels = {}; self.fix = []

    def here(self, label): self.labels[label] = len(self.b)
    def raw(self, *bs):
        for x in bs:
            self.b += x if isinstance(x, (bytes, bytearray)) else bytes([x])
    def ptr(self, target): self.fix.append((len(self.b), target)); self.b += b"\0\0\0\0"
    def h(self, *vals): self.raw(struct.pack("<%dH" % len(vals), *vals))

    # flow
    def end(self): self.raw(0x02)
    def ret(self): self.raw(0x03)
    def call(self, t): self.raw(0x04); self.ptr(t)
    def goto(self, t): self.raw(0x05); self.ptr(t)
    def goto_if(self, cond, t): self.raw(0x06, cond); self.ptr(t)
    def call_if(self, cond, t): self.raw(0x07, cond); self.ptr(t)
    def if_set(self, flag, t): self.checkflag(flag); self.goto_if(1, t)
    def if_unset(self, flag, t): self.checkflag(flag); self.goto_if(0, t)
    def if_var(self, var, val, t, cond=1): self.compare(var, val); self.goto_if(cond, t)
    def if_yes(self, t): self.compare(0x800D, 1); self.goto_if(1, t)
    # state
    def setvar(self, var, val): self.raw(0x16); self.h(var, val)
    def addvar(self, var, val): self.raw(0x17); self.h(var, val)
    def compare(self, var, val): self.raw(0x21); self.h(var, val)
    def setflag(self, f): self.raw(0x29); self.h(f)
    def clearflag(self, f): self.raw(0x2A); self.h(f)
    def checkflag(self, f): self.raw(0x2B); self.h(f)
    def special(self, n): self.raw(0x25); self.h(n)
    def heal(self): self.special(0)
    # locks, messages
    def lock(self): self.raw(0x6A)
    def lockall(self): self.raw(0x69)
    def release(self): self.raw(0x6C)
    def releaseall(self): self.raw(0x6B)
    def faceplayer(self): self.raw(0x5A)
    def closemessage(self): self.raw(0x68)
    def say(self, key): self.raw(0x0F, 0x00); self.ptr(("text", key)); self.raw(0x09, 0x04)
    def sign(self, key): self.raw(0x0F, 0x00); self.ptr(("text", key)); self.raw(0x09, 0x03)
    def ask(self, key): self.raw(0x0F, 0x00); self.ptr(("text", key)); self.raw(0x09, 0x05)
    # sound, screen
    def playse(self, se): self.raw(0x2F); self.h(se)
    def waitse(self): self.raw(0x30)
    def playbgm(self, song): self.raw(0x33); self.h(song); self.raw(0x00)
    def fadedefaultbgm(self): self.raw(0x35)
    def fadenewbgm(self, song): self.raw(0x36); self.h(song)
    def fadeoutbgm(self, speed=4): self.raw(0x37, speed)
    def fade(self, how): self.raw(0x97, how)                  # 0 from black, 1 to black, 2 from white, 3 to white
    def delay(self, frames): self.raw(0x28); self.h(frames)
    def cry(self, species): self.raw(0xA1); self.h(species, 0); self.raw(0xC5)
    def shake(self, hpan=0, vpan=4, times=8, speed=4):     # ShakeCamera (special 312)
        self.setvar(0x8004, hpan); self.setvar(0x8005, vpan); self.setvar(0x8006, times)
        self.setvar(0x8007, speed); self.playse(178); self.special(312); self.raw(0x27)   # rumble; waitstate
    def weather(self, w): self.raw(0xA4); self.h(w); self.raw(0xA5)            # setweather; doweather
    def resetweather(self): self.raw(0xA3, 0xA5)                              # (0xA6 is setstepcallback)
    def setflashlevel(self, n): self.raw(0x99); self.h(n)                     # the dark's radius, 0 lit .. 7 cave
    def animateflash(self, n): self.raw(0x9A, n)                              # grow the light to level n
    def checkgender(self): self.raw(0xA0)                                     # VAR_RESULT: 0 male, 1 female
    def setmetatile(self, x, y, block):
        self.raw(0xA2); self.h(x, y, block & 0x3FF, 1 if (block >> 10) & 3 else 0)
    def drawmap(self): self.special(145)
    # objects
    def move(self, local, key, wait=True):
        self.raw(0x4F); self.h(local); self.ptr(("move", key))
        if wait: self.raw(0x51); self.h(local)
    def waitmove(self, local=0): self.raw(0x51); self.h(local)
    def addobject(self, local): self.raw(0x55); self.h(local)
    def removeobject(self, local): self.raw(0x53); self.h(local)
    def setobjectxy(self, local, x, y): self.raw(0x57); self.h(local, x, y)
    def turn(self, local, d): self.raw(0x5B); self.h(local); self.raw(DIRS[d])
    # warps, battles, items
    def warp(self, g, n, x, y, kind=0x39): self.raw(kind, g, n, 0xFF); self.h(x, y)
    def warpsilent(self, g, n, x, y): self.warp(g, n, x, y, 0x3A)
    def warpteleport(self, g, n, x, y): self.warp(g, n, x, y, 0x3D)
    def setdynamicwarp(self, g, n, warp):                 # where a MAP_DYNAMIC way out leads: a map's warp
        self.raw(0x3F, g, n, warp); self.h(0, 0)       # (x, y: only used with no warp; plain numbers, not vars)
    def battle(self, trainer, defeat_key):                 # trainerbattle 3: no intro, never checks the flag
        self.raw(0x5C, 0x03); self.h(trainer, 0); self.ptr(("text", defeat_key))
    def additem(self, item, n=1): self.raw(0x44); self.h(item, n)
    # added for Paldea (vanilla Emerald's command numbers, as the hack's own scripts use them)
    def callstd(self, n): self.raw(0x09, n)
    def setorcopyvar(self, var, val): self.raw(0x1A); self.h(var, val)
    def callnative(self, addr): self.raw(0x23); self.raw(struct.pack("<I", addr))
    def specialvar(self, var, n): self.raw(0x26); self.h(var, n)
    def playfanfare(self, n): self.raw(0x31); self.h(n)
    def waitfanfare(self): self.raw(0x32)
    def showmonpic(self, species, x=10, y=3): self.raw(0x75); self.h(species); self.raw(x, y)
    def hidemonpic(self): self.raw(0x76)
    def bufferspecies(self, buf, species): self.raw(0x7D, buf); self.h(species)
    def wildbattle(self, species, level, item=0): self.raw(0xB6); self.h(species); self.raw(level); self.h(item)
    def dowildbattle(self): self.raw(0xB7)
    def getplayerxy(self, vx, vy): self.raw(0x42); self.h(vx, vy)
    def pokemart(self, key): self.raw(0x86); self.ptr(("mart", key))          # a 0-ended list of item ids
    def waitmessage(self): self.raw(0x66)
    def giveitem(self, item, n=1):                         # STD_OBTAIN_ITEM: "Obtained ...!", into the Bag
        self.setorcopyvar(0x8000, item); self.setorcopyvar(0x8001, n); self.callstd(0)


class Blob:
    """Pieces placed one after another from `base`; symbolic pointers resolved at link time."""

    def __init__(self, base):
        self.base = base; self.data = bytearray(); self.addr = {}; self.fixups = []

    def put(self, key, b, align=4):
        while len(self.data) % align:
            self.data.append(0)
        assert key not in self.addr, key
        self.addr[key] = self.base + len(self.data)
        self.data += b
        return self.addr[key]

    def put_script(self, s):
        a = self.put(("script", s.name), bytes(s.b), 1)
        for off, target in s.fix:
            self.fixups.append((a - self.base + off, target, s))
        return a

    def ref(self, key, off_in_blob):                      # a pointer word inside the data, filled at link
        self.fixups.append((off_in_blob, key, None))

    def link(self):
        for off, target, s in self.fixups:
            if isinstance(target, int):
                v = target
            elif isinstance(target, str) and s is not None:
                v = self.addr[("script", s.name)] + s.labels[target]
            else:
                v = self.addr[target]
            struct.pack_into("<I", self.data, off, v)
        return bytes(self.data)
