"""Raise the per-stack bag limit from 99 to 999 for every pocket (berries already 999).
usage: python bagcap_patch.py <in.gba> <out.gba>
Sites: CheckBagHasSpace 0x080D685E and AddBagItem 0x080D69A8 (movs #99 after ldr =999 -> nop),
bag list quantity print 0x081AB628 (2 digits -> 3). Shop buy-quantity picker stays at 99 per purchase (u8 field)."""
import struct, sys
def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    for off, old, new in ((0xD685E, b"\x63\x27", b"\xc0\x46"), (0xD69A8, b"\x63\x22", b"\xc0\x46"), (0x1AB628, b"\x02\x23", b"\x03\x23")):
        assert rom[off:off+2] == old, "unexpected bytes at %x: %s" % (off, rom[off:off+2].hex())
        rom[off:off+2] = new
    open(outp, "wb").write(rom); print("bag cap 999 applied")
if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
