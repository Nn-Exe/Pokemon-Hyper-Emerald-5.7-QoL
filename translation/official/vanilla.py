"""Official Emerald texts by address, from the pret/pokeemerald source + symbol file.
load() -> list of entries {name, addr, raw (vanilla bytes incl. the 0xFF terminator), text (source text), src}.
Only labelled single strings (asm `Label: .string "...$"` and C `const u8 name[] = _("...")`)."""
import os, re, glob, collections

# a checkout of pret/pokeemerald with its pokeemerald.sym beside it; HE_PRET overrides the default place
PRET = os.environ.get("HE_PRET") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "_testrun", "pret_src")
SRC = os.path.join(PRET, "pokeemerald")


def charmap():
    chars, names = {}, {}
    for line in open(os.path.join(SRC, "charmap.txt"), encoding="utf-8"):
        line = line.split("@")[0].rstrip()
        m = re.match(r"^'(\\?.)'\s*=\s*([0-9A-Fa-f ]+)$", line)
        if m:
            chars[m.group(1)] = bytes(int(x, 16) for x in m.group(2).split())
            continue
        m = re.match(r"^(\w+)\s*=\s*([0-9A-Fa-f ]+)$", line)
        if m:
            names[m.group(1)] = bytes(int(x, 16) for x in m.group(2).split())
    return chars, names


CHARS, NAMES = charmap()
CHARS["'"] = bytes([0xB4])                         # the charmap writes it '\''
CHARS['"'] = bytes([0xB2])                         # a closing double quote, for \" in C strings


def encode(s):
    """A source string body (between the quotes, escapes as written) -> bytes. '$' is the terminator in asm."""
    out, i = bytearray(), 0
    while i < len(s):
        c = s[i]
        if c == "\\":
            key = s[i:i + 2]
            if key in CHARS:
                out += CHARS[key]
            elif key == '\\"':
                out += CHARS['"'] if '"' in CHARS else b"\xB1"
            elif key == "\\\\":
                out += CHARS["\\\\"] if "\\\\" in CHARS else b""
            else:
                raise ValueError("escape " + key)
            i += 2
        elif c == "{":
            j = s.index("}", i)
            for tok in s[i + 1:j].split():
                if tok in NAMES:
                    out += NAMES[tok]
                elif re.match(r"^(0x[0-9A-Fa-f]+|\d+)$", tok):
                    out.append(int(tok, 0))
                else:
                    raise ValueError("token " + tok)
            i = j + 1
        else:
            if c not in CHARS:
                raise ValueError("char %r" % c)
            out += CHARS[c]
            i += 1
    return bytes(out)


def symbols():
    by = collections.defaultdict(list)
    for l in open(os.path.join(PRET, "pokeemerald.sym")):
        p = l.split()
        if len(p) >= 4 and p[0].startswith("08"):
            by[p[3]].append((int(p[0], 16), int(p[2], 16)))
    return by


def asm_texts():
    """(label, [string bodies up to the first '$'], file) for labels directly followed by .string lines"""
    out = []
    files = glob.glob(os.path.join(SRC, "data", "**", "*.inc"), recursive=True) + glob.glob(os.path.join(SRC, "data", "*.s"))
    lab = re.compile(r"^(\w+):{1,2}\s*(?:@.*)?$")
    strg = re.compile(r'^\s*\.string\s+"((?:[^"\\]|\\.)*)"')
    for f in files:
        labels, body = [], None
        for line in open(f, encoding="utf-8"):
            m = lab.match(line.strip())
            if m:
                if body is None:
                    labels.append(m.group(1))
                else:
                    labels, body = [m.group(1)], None
                continue
            m = strg.match(line)
            if m and labels:
                body = (body or "") + m.group(1)
                if "$" in m.group(1):
                    out.append((labels, body[:body.index("$") + 1], f))
                    labels, body = [], None
                continue
            if line.strip() and not line.strip().startswith("@"):
                labels, body = [], None
    return out


def c_texts():
    out = []
    files = glob.glob(os.path.join(SRC, "src", "**", "*.c"), recursive=True) + glob.glob(os.path.join(SRC, "src", "**", "*.h"), recursive=True)
    rx = re.compile(r'const\s+u8\s+(\w+)\[\]\s*=\s*_\(\s*((?:"(?:[^"\\]|\\.)*"\s*)+)\)\s*;', re.S)
    lit = re.compile(r'"((?:[^"\\]|\\.)*)"')
    for f in files:
        t = open(f, encoding="utf-8").read()
        for m in rx.finditer(t):
            out.append(([m.group(1)], "".join(lit.findall(m.group(2))) + "$", f))
    return out


def load():
    sym = symbols()
    entries, problems = [], collections.Counter()
    texts = asm_texts() + c_texts()
    count = collections.Counter(name for labels, _, _ in texts for name in labels)
    for labels, body, f in texts:
        try:
            raw = encode(body)
        except ValueError as e:
            problems[str(e)] += 1
            continue
        for name in labels:
            for addr, size in sym.get(name, []):
                if count[name] > 1 and size != len(raw):       # a static name used in two files: the size tells which
                    continue
                entries.append({"name": name, "addr": addr, "raw": raw, "text": body[:-1], "src": os.path.relpath(f, SRC)})
            if name not in sym:
                problems["no symbol"] += 1
    return entries, problems


if __name__ == "__main__":
    e, p = load()
    print(len(e), "labelled texts;", dict(p))


def c_arrays():
    """fixed-width string arrays: const u8 name[...][W] = { _("..."), [IDX] = _("..."), ... } -> (name, [bodies], file)"""
    out = []
    files = glob.glob(os.path.join(SRC, "src", "**", "*.c"), recursive=True) + glob.glob(os.path.join(SRC, "src", "**", "*.h"), recursive=True)
    rx = re.compile(r'const\s+u8\s+(\w+)\[[^\]]*\]\[[^\]]*\]\s*=\s*\{(.*?)\};', re.S)
    ent = re.compile(r'_\(\s*((?:"(?:[^"\\]|\\.)*"\s*)+)\)')
    lit = re.compile(r'"((?:[^"\\]|\\.)*)"')
    for f in files:
        t = open(f, encoding="utf-8").read()
        for m in rx.finditer(t):
            body = re.sub(r"//.*", "", m.group(2))
            items = ["".join(lit.findall(e.group(1))) for e in ent.finditer(body)]
            if items:
                out.append((m.group(1), items, f))
    return out


def load_arrays():
    """entries for each element of a fixed-width array whose symbol size divides evenly: addr, width, raw, text"""
    sym = {}
    for l in open(os.path.join(PRET, "pokeemerald.sym")):
        p = l.split()
        if len(p) >= 4 and p[0].startswith("08"):
            sym.setdefault(p[3], []).append((int(p[0], 16), int(p[2], 16)))
    out = []
    for name, items, f in c_arrays():
        for addr, size in sym.get(name, []):
            if size == 0 or size % len(items):
                continue
            w = size // len(items)
            for i, body in enumerate(items):
                try:
                    raw = encode(body + "$")
                except ValueError:
                    continue
                if len(raw) <= w:
                    out.append({"name": "%s[%d]" % (name, i), "addr": addr + i * w, "width": w, "raw": raw, "text": body,
                                "src": os.path.relpath(f, SRC)})
    return out
