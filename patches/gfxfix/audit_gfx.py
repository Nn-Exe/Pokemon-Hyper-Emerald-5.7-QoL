"""Audit: no LZ77-compressed blob in the build differs from the original ROM.
usage: python audit_gfx.py <build.gba> <original.gba>
Finds every LZ77 blob the original ROM references from an aligned pointer, decodes its compressed length, and
reports any blob whose bytes the build changed. A clean run means every tileset, sprite and menu graphic in the
build decompresses exactly as the original does. Run this after any translation pass."""
import struct, sys


def lz_clen(src, o):
    """compressed length of the LZ77 (type 0x10) blob at o, or None if it is not one"""
    if src[o] != 0x10:
        return None
    size = struct.unpack_from("<I", src, o)[0] >> 8
    if not (32 <= size <= 0x20000):
        return None
    out = 0
    i = o + 4
    try:
        while out < size:
            flags = src[i]; i += 1
            for b in range(8):
                if out >= size:
                    break
                if flags & (0x80 >> b):
                    v = (src[i] << 8) | src[i + 1]; i += 2
                    ln = (v >> 12) + 3; disp = (v & 0xFFF) + 1
                    if disp > out:
                        return None
                    out += ln
                else:
                    i += 1; out += 1
    except IndexError:
        return None
    return i - o


def main(build_path, orig_path):
    rom = open(build_path, "rb").read()
    orig = open(orig_path, "rb").read()
    n = len(orig)
    assert len(rom) == n, "size mismatch"
    cands = set()
    for o in range(0, n - 3, 4):
        v = struct.unpack_from("<I", orig, o)[0]
        if 0x08000000 < v < 0x08000000 + n and orig[v - 0x08000000] == 0x10:
            cands.add(v - 0x08000000)
    bad = 0
    checked = 0
    for t in sorted(cands):
        clen = lz_clen(orig, t)
        if not clen:
            continue
        checked += 1
        hits = [i for i in range(t, min(t + clen, n)) if rom[i] != orig[i]]
        if hits:
            bad += 1
            print("DAMAGED blob @%08X (%d bytes): %d changed at %s" % (
                0x08000000 + t, clen, len(hits), ", ".join("%08X" % (0x08000000 + h) for h in hits[:8])))
    print("checked %d compressed blobs; %s" % (checked, "ALL CLEAN" if not bad else "%d DAMAGED" % bad))
    return 1 if bad else 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__); sys.exit(1)
    sys.exit(main(sys.argv[1], sys.argv[2]))
