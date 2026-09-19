"""Leftover Chinese NPC names -> English (Hyper Emerald v5.7). Apply after the bothbikes build.
usage: python npcnames_patch.py <in.gba> <out.gba>

Names that live inside fixed-width struct fields were invisible to the pointer-based text passes, so they
stayed Chinese. This rewrites them in place, inside the same bytes:
  - gTrainers (0x090019F8, 40-byte entries, name at +4, 12 bytes): 6 story trainers.
  - Battle Frontier trainers (0x085D5ACC, 0x34-byte entries {class u32, name[8], speech, monSet*}): 2 names.
  - The three Battle Tents (0x085DDA14 / 0x085DE610 / 0x085DF084, same struct, 30 each): all 90 names.
    Their class sequence is vanilla's tent order, so each slot gets its official English name.
  - Six honorific words the battle-tower code uses as a link partner's name (0x083397A8..), pointer
    table at 0x083397D0. Two of them need their 2 spare padding bytes, so those pointers move back by 2.
Every site is checked against the bytes it is expected to hold before anything is written, and every new
name must fit its field with its terminator. No free space is used.
"""
import json, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ENC = {' ': 0x00, '.': 0xAD, "'": 0xB4, '-': 0xAE}
for i in range(26): ENC[chr(65 + i)] = 0xBB + i
for i in range(26): ENC[chr(97 + i)] = 0xD5 + i


def encode(text):
    return bytes(ENC[c] for c in text) + b"\xff"


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    data = json.load(open(os.path.join(HERE, "npcnames_data.json"), encoding="utf-8"))
    for e in data["entries"]:
        a, w = e["addr"], e["width"]
        assert rom[a:a + w].hex() == e["expect"], "%s: bytes at %08X differ (%s)" % (e["note"], 0x08000000 + a, rom[a:a + w].hex())
        enc = encode(e["text"])
        assert len(enc) <= w, "%r does not fit in %d bytes" % (e["text"], w)
        rom[a:a + len(enc)] = enc
        for i in range(a + len(enc), a + w):
            rom[i] = 0x00                      # the rest of the field, never read past the terminator
    for p in data["pointers"]:
        a = p["addr"]
        cur = struct.unpack_from("<I", rom, a)[0]
        assert cur == p["expect"], "pointer at %08X is %08X, expected %08X" % (0x08000000 + a, cur, p["expect"])
        struct.pack_into("<I", rom, a, p["new"])
    open(outp, "wb").write(rom)
    print("%d names rewritten in place, %d pointers adjusted" % (len(data["entries"]), len(data["pointers"])))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
