"""Tiny ROM patch tool (no external deps). Produces/applies a compact binary diff between two same-size ROMs.
  create: python romdiff.py create <original.gba> <modified.gba> <out.hpatch>
  apply : python romdiff.py apply  <original.gba> <in.hpatch>   <out.gba>
Format: magic "HPATCH1", u32 rom size, u32 sha1-prefix of original, then records {u32 offset, u32 length, bytes}."""
import sys, struct, hashlib

MAGIC = b"HPATCH1\0"

def create(orig_path, mod_path, out_path):
    a = open(orig_path, "rb").read(); b = open(mod_path, "rb").read()
    assert len(a) == len(b), "ROM sizes differ"
    out = bytearray(MAGIC + struct.pack("<I", len(a)) + hashlib.sha1(a).digest()[:4])
    i, n, runs = 0, len(a), 0
    while i < n:
        if a[i] == b[i]:
            i += 1; continue
        j = i
        while j < n and (a[j] != b[j] or (j + 16 < n and any(a[k] != b[k] for k in range(j, min(n, j + 16))))):
            j += 1
        out += struct.pack("<II", i, j - i) + b[i:j]; runs += 1
        i = j
    open(out_path, "wb").write(out)
    print("wrote %s: %d runs, %d bytes" % (out_path, runs, len(out)))

def apply(orig_path, patch_path, out_path):
    a = bytearray(open(orig_path, "rb").read()); p = open(patch_path, "rb").read()
    assert p[:8] == MAGIC, "not an HPATCH1 file"
    size, = struct.unpack_from("<I", p, 8)
    assert len(a) == size, "original ROM size mismatch"
    assert p[12:16] == hashlib.sha1(a).digest()[:4], "this is not the expected original ROM (need Hyper EMR LA v5.7 bugfix 2.gba, the Chinese hack, NOT vanilla Emerald; see README)"
    o = 16
    while o < len(p):
        off, ln = struct.unpack_from("<II", p, o); o += 8
        a[off:off + ln] = p[o:o + ln]; o += ln
    open(out_path, "wb").write(a)
    print("wrote %s (sha1 %s)" % (out_path, hashlib.sha1(a).hexdigest()))

if __name__ == "__main__":
    if len(sys.argv) == 5 and sys.argv[1] == "create": create(*sys.argv[2:])
    elif len(sys.argv) == 5 and sys.argv[1] == "apply": apply(*sys.argv[2:])
    else: print(__doc__)
