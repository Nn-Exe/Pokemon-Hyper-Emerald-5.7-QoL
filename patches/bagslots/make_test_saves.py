"""Two synthetic 'other player' saves for test_bagslots_saves.lua, made from any old-layout save.
usage: python make_test_saves.py <game.gba (patched)> <old-layout.sav> <outdir>
  full_junk.sav - a full 100-item Items pocket, and random bytes over the whole free tail 0x0203D908..0x0203DE00
                  (a real cartridge's EWRAM is not cleared at power-on, so another player's tail may hold junk);
  already.sav   - MARKER set, 150 items in the new area and a different, stale old area (someone updating twice).
  expect.lua    - what the loader must leave in both areas.
The hack's save sectors carry checksum 0x0001 (it no longer checks them), so edited sectors load as they are.
"""
import os, random, struct, sys

SIZES = [0xF2C, 0xF80, 0xF80, 0xF80, 0xF08] + [0xF80] * 8 + [0x7D0]
STREAM, OLD, NEW, MARKER = 0x0203CF64, 0x0203D030, 0x0203DAE0, 0x0203DADC
ITEMS = 0x00FC2C7C


def slot_secs(buf):
    slot = max((0, 1), key=lambda s: struct.unpack_from("<I", buf, s * 14 * 0x1000 + 0xFFC)[0])
    return {struct.unpack_from("<H", buf, (slot * 14 + k) * 0x1000 + 0xFF4)[0]: (slot * 14 + k) * 0x1000 for k in range(14)}


def get_stream(buf):
    secs = slot_secs(buf)
    return bytearray(b"".join(buf[secs[i] + SIZES[i]:secs[i] + 0xFF0] for i in range(14)))


def put_stream(buf, st):
    secs, o = slot_secs(buf), 0
    for i in range(14):
        n = 0xFF0 - SIZES[i]
        buf[secs[i] + SIZES[i]:secs[i] + 0xFF0] = st[o:o + n]
        o += n


def main(rom_path, sav_path, out):
    rom = open(rom_path, "rb").read()
    ids = [i for i in range(1, 1200) if rom[ITEMS + 44 * i + 26] == 1
           and struct.unpack_from("<H", rom, ITEMS + 44 * i + 14)[0] == i and 0xBB <= rom[ITEMS + 44 * i] <= 0xEE]
    save = bytearray(open(sav_path, "rb").read())
    os.makedirs(out, exist_ok=True)
    random.seed(7)
    st = get_stream(save)
    old = [(ids[99 - i], i % 99 + 1) for i in range(100)]
    for i, (x, q) in enumerate(old):
        struct.pack_into("<HH", st, OLD - STREAM + 4 * i, x, q)
    for a in range(0x0203D908, 0x0203DE00):
        st[a - STREAM] = random.randrange(256)
    assert struct.unpack_from("<I", st, MARKER - STREAM)[0] != 0x32474142
    a = bytearray(save); put_stream(a, st); open(os.path.join(out, "full_junk.sav"), "wb").write(a)
    st = get_stream(save)
    new = [(ids[i], 7) for i in range(150)] + [(0, 0)] * 50
    stale = [(ids[200 + i], 3) for i in range(100)]
    for i, (x, q) in enumerate(new):
        struct.pack_into("<HH", st, NEW - STREAM + 4 * i, x, q)
    for i, (x, q) in enumerate(stale):
        struct.pack_into("<HH", st, OLD - STREAM + 4 * i, x, q)
    struct.pack_into("<I", st, MARKER - STREAM, 0x32474142)
    b = bytearray(save); put_stream(b, st); open(os.path.join(out, "already.sav"), "wb").write(b)
    lua = lambda t: "{" + ",".join(str(x | q << 16) for x, q in t) + "}"
    open(os.path.join(out, "expect.lua"), "w").write(
        "EXP_A_OLD = %s\nEXP_B_NEW = %s\nEXP_B_OLD = %s\n" % (lua(old), lua(new), lua(stale)))
    print("full_junk.sav, already.sav and expect.lua in", out)


if __name__ == "__main__":
    main(*sys.argv[1:4])
