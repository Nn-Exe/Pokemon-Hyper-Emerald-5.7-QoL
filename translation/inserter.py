"""Encode English translations to Gen3 text and repoint strings."""
import re, struct

# --- encoder ---
ENC = {' ':0x00, 'é':0x1B, 'É':0x06, ':':0xF0, '(':0x5C, ')':0x5D, '%':0x5B,
       '!':0xAB, '?':0xAC, '.':0xAD, '-':0xAE, ',':0xB8, '…':0xB0,
       '“':0xB1, '”':0xB2, '‘':0xB3, "'":0xB4, '’':0xB4, '/':0xBA, '·':0xAF,
       '$':0xB7, '×':0xB9, '♂':0xB5, '♀':0xB6, '&':0x2D, '+':0x2E, '=':0x35, ';':0x36}
for i in range(10): ENC[chr(48+i)] = 0xA1+i
for i in range(26): ENC[chr(65+i)] = 0xBB+i
for i in range(26): ENC[chr(97+i)] = 0xD5+i

NORMALIZE = {'—':'-', '–':'-', '~':'-', '"':'”', '。':'.', '！':'!', '？':'?',
             '，':',', '、':',', '：':':', '‘':"'", '’':"'",
             '“':'“', '”':'”', '[Lv]':'Lv.', ' ':' ', '…':'…', 'è':'e', 'à':'a',
             'ü':'u', 'ö':'o', 'ä':'a', 'ê':'e', 'î':'i', 'ô':'o', 'û':'u', 'ç':'c', 'ñ':'n', '`':"'"}

TOKEN_RE = re.compile(r'\[(BUF[0-9A-Fa-f]{2}|FC[0-9A-Fa-f]+|F8[0-9A-Fa-f]{2}|F9[0-9A-Fa-f]{2}|F7|S[0-9A-Fa-f]{2}|Lv|\?[0-9A-Fa-f]{2}(?:[0-9A-Fa-f]{2})?)\]|\\p|\\n|\\l')

def encode_token(tok):
    if tok == '\\p': return b'\xfb'
    if tok == '\\n': return b'\xfe'
    if tok == '\\l': return b'\xfa'
    inner = tok[1:-1]
    if inner.startswith('BUF'): return bytes([0xFD, int(inner[3:], 16)])
    if inner.startswith('FC'): return b'\xfc' + bytes.fromhex(inner[2:])
    if inner.startswith('F8'): return bytes([0xF8, int(inner[2:], 16)])
    if inner.startswith('F9'): return bytes([0xF9, int(inner[2:], 16)])
    if inner == 'F7': return b'\xf7'
    if inner == 'Lv': return bytes([0x34])
    if inner.startswith('?'): return bytes.fromhex(inner[1:])   # raw control byte(s) round-trip
    if inner.startswith('S'): return bytes([int(inner[1:], 16)])
    raise ValueError(tok)

def wrap_page(words, width=34):
    """words: list of (display_len, encoded_bytes, is_space). Returns list of lines (bytes)."""
    lines = []
    cur = b''; cur_len = 0
    for wlen, wbytes in words:
        if cur_len == 0:
            cur = wbytes; cur_len = wlen
        elif cur_len + 1 + wlen <= width:
            cur += b'\x00' + wbytes; cur_len += 1 + wlen
        else:
            lines.append(cur); cur = wbytes; cur_len = wlen
    if cur_len: lines.append(cur)
    return lines

def encode_string(text, width=34):
    """Full pipeline: normalize, tokenize, wrap. Returns bytes WITHOUT trailing 0xFF."""
    for k, v in NORMALIZE.items():
        text = text.replace(k, v)
    # split into pages on \p
    pages = text.split('\\p')
    out_pages = []
    for pg in pages:
        # tokenize into words; tokens count as ~6 display chars for BUF (name lengths)
        parts = []
        pos = 0
        for m in TOKEN_RE.finditer(pg):
            if m.start() > pos: parts.append(('T', pg[pos:m.start()]))
            parts.append(('K', m.group(0)))
            pos = m.end()
        if pos < len(pg): parts.append(('T', pg[pos:]))
        # build word list
        words = []  # (display_len, bytes)
        wbuf = b''; wlen = 0
        def flush():
            nonlocal wbuf, wlen
            if wlen or wbuf: words.append((wlen, wbuf)); wbuf = b''; wlen = 0
        for kind, val in parts:
            if kind == 'K':
                if val in ('\\n', '\\l'):  # translators shouldn't emit these; treat as space
                    flush(); continue
                enc = encode_token(val)
                disp = 7 if val.startswith('[BUF') else 0
                wbuf += enc; wlen += disp
            else:
                for ch in val:
                    if ch == ' ':
                        flush()
                    else:
                        b = ENC.get(ch)
                        if b is None:
                            b = ENC.get(ch.lower(), 0x00)
                        wbuf += bytes([b]); wlen += 1
        flush()
        lines = wrap_page(words, width)
        # join: first two lines with \n, subsequent with \l
        if not lines:
            out_pages.append(b'')
            continue
        pgb = lines[0]
        for i, ln in enumerate(lines[1:]):
            pgb += (b'\xfe' if i == 0 else b'\xfa') + ln
        out_pages.append(pgb)
    return b'\xfb'.join(out_pages)

def find_all_occurrences(data, value):
    pat = struct.pack('<I', value)
    out = []
    i = data.find(pat)
    while i != -1:
        out.append(i)
        i = data.find(pat, i+1)
    return out

if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    t = "Hello! I'm the Battle Tower attendant. Would you like to challenge?\\pIt costs [BUF02] points, okay?"
    b = encode_string(t)
    print(b.hex(' '))
