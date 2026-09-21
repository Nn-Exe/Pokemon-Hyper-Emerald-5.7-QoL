"""Read story flags and vars straight out of a battery save (.sav / .srm), the way the game does.

    python tools/romdata/savefile.py <game.sav> 0x867 0x42B6 ...   -> each flag's state
    python tools/romdata/savefile.py <game.sav> var 0x4050          -> a var's value

    from savefile import Save;  s = Save(path);  s.flag(0x867);  s.var(0x405D)

The save is two slots of 14 sections (4 KB each: data, then id at +0xFF4 and counter at +0xFFC); the slot
with the higher counter is current. SaveBlock2 is section 0, SaveBlock1 is sections 1-4 (0xF80 bytes each).
Vanilla flags live at SaveBlock1 + 0x1270 and vars at + 0x139C. This hack also has 1,664 flags of its own,
0x4000-0x467F, which its GetFlagAddr (0x09F00CEC) keeps in four 52-byte runs of spare space:
flags 0x4000-0x419F at SB1+0x988, 0x41A0-0x433F at SB1+0x3B24, 0x4340-0x44DF at SB2+0x5C,
0x44E0-0x467F at SB2+0x28.
"""
import sys, struct


class Save:
    def __init__(self, path):
        d = open(path, "rb").read()
        slots = []
        for slot in (0, 1):
            secs, counter = {}, -1
            for i in range(14):
                s = d[(slot * 14 + i) * 0x1000:(slot * 14 + i + 1) * 0x1000]
                if len(s) < 0x1000: break
                sid = struct.unpack_from("<H", s, 0xFF4)[0]
                counter = max(counter, struct.unpack_from("<I", s, 0xFFC)[0])
                secs[sid] = s
            slots.append((counter, secs))
        counter, secs = max(slots, key=lambda x: x[0])
        self.sb2 = secs[0][:0xF80]
        self.sb1 = b"".join(secs[i][:0xF80] for i in (1, 2, 3, 4))

    def _byte(self, f):
        if f < 0x4000:
            return self.sb1[0x1270 + f // 8]
        i = (f - 0x4000) >> 3
        if i <= 0x33: return self.sb1[0x988 + i]
        if i <= 0x67: return self.sb1[0x3B24 + i - 0x34]
        if i <= 0x9B: return self.sb2[0x5C + i - 0x68]
        if i <= 0xCF: return self.sb2[0x28 + i - 0x9C]
        raise ValueError("flag %04X is outside every range the game knows" % f)

    def flag(self, f):
        return (self._byte(f) >> (f & 7)) & 1

    def var(self, v):
        assert 0x4000 <= v < 0x4100, "only saved vars (0x4000-0x40FF) live in the save"
        return struct.unpack_from("<H", self.sb1, 0x139C + (v - 0x4000) * 2)[0]

    def location(self):
        return self.sb1[4], self.sb1[5]


if __name__ == "__main__":
    s = Save(sys.argv[1])
    a = sys.argv[2:]
    if a and a[0] == "var":
        print("var %s = %d" % (a[1], s.var(int(a[1], 0))))
    else:
        for x in a:
            print("flag %s = %d" % (x, s.flag(int(x, 0))))
