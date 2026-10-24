"""Every byte a Kitakami build changes against the game it was built on, accounted for (2026-10-17, before the
merge). python regions.py <rom/ game> <Kitakami build>: lists each kind of change with its count and stops on any
changed byte that none of them explains.

The kinds (the patch's own constants, not copies):
  blob        0x09E40000..0x09E80000, Kitakami's space (zero-filled before)
  code        kit_bgmask 0x08FEF540..0x08FEF580, kit_hour 0x08FEF580..0x08FEF600 (0xFF before)
  hooks       the two bl's into the day/night tint routine (0x08CFE3EA, 0x08CFE472)
  pointers    words that named a table Kitakami copies (trainer pictures, palettes, animations, coordinates; the
              wild table; the layout table; the field palette table) and now name the copy, in the blob
  sites       group 35's table pointer, Mossdeep's header (+4 events, +8 scripts), map section 187's name
  trainers    rows 1358-1360 and 1378
  sprites     the hack's sprite table entries Kitakami takes
  shop        the shop guard's bitmap bytes for the stalls' items
  journal     gen9journal's five Locked rows and row 0, their panes, the two counts
  stamp       Area Zero's stamp (var 0x40F9) in its scripts: the build's stamp now
"""
import os, struct, sys, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = next(p for p in (os.path.join(HERE, "..", ".."), os.path.join(HERE, "..", "..", "hyper-emerald-en-qol"))
            if os.path.exists(os.path.join(p, "patches", "kitakami", "kitakami_patch.py")))   # the patch folder's copy, or _testrun's
for sub in ("kitakami", "paldea"):
    sys.path.insert(0, os.path.join(REPO, "patches", sub))
import kitakami_patch as K, kasm as KA, ktrainers as KT, ksprites as KSP, kwild as KW, kpeople as KP, kjournal as KJ
import maps as M

B = 0x08000000


def u32(r, o): return struct.unpack_from("<I", r, o)[0]


def main(base_path, build_path):
    a, b = open(base_path, "rb").read(), open(build_path, "rb").read()
    assert len(a) == len(b) == 32 << 20
    print("game %s, build %s" % (hashlib.sha1(a).hexdigest()[:8], hashlib.sha1(b).hexdigest()[:8]))
    diff =[i for i, (x, y) in enumerate(zip(a, b)) if x != y]
    left = set(diff)
    count = {}

    def take(kind, lo, hi):
        got = {i for i in range(lo, hi) if i in left}
        left.difference_update(got)
        if got:
            count[kind] = count.get(kind, 0) + 1
        return got

    in_blob = lambda v: B + K.FREE <= v < B + K.FREE_END
    # the blob and the code
    take("blob", K.FREE, K.FREE_END)
    assert all(x == 0 for x in a[K.FREE:K.FREE_END]), "the blob's space was not empty in the game"
    for lo, hi in ((KA.BGMASK_AT, KA.BGMASK_END), (KA.HOUR_AT, KA.HOUR_END)):
        assert all(x == 0xFF for x in a[lo - B:hi - B])
        take("code", lo - B, hi - B)
    for site, was in ((KA.HOOK, KA.HOOK_WAS), (KA.HOOK2, KA.HOOK2_WAS)):
        assert a[site:site + 4] == was
        take("hooks", site, site + 4)
    # pointer words that now name a copy in the blob
    tables = {u32(a, KT.REF_AT["pics"]): "trainer pictures", u32(a, KT.REF_AT["pals"]): "trainer palettes",
              u32(a, KT.REF_AT["anims"]): "trainer animations", u32(a, KT.REF_AT["coords"]): "trainer coordinates",
              B + KW.TABLE: "wild table", u32(a, M.LAYOUT_REFS[0]): "layout table",
              u32(a, KSP.PAL_REFS[0]): "field palette table"}
    for i in sorted(left):
        w = i & ~3
        if w + 4 <= len(a) and u32(a, w) in tables and in_blob(u32(b, w)):
            take("pointers: " + tables[u32(a, w)], w, w + 4)
    # single sites
    take("sites: group 35's map table", M.MAP_GROUPS + 4 * K.GROUP, M.MAP_GROUPS + 4 * K.GROUP + 4)
    take("sites: Mossdeep's header (events, scripts)", KP.MOSSDEEP_HEADER + 4, KP.MOSSDEEP_HEADER + 12)
    for sec in K.MAPSECS.values():
        take("sites: map section %d's name" % sec[0], K.MAPSEC_TABLE + 8 * sec[0] + 4, K.MAPSEC_TABLE + 8 * sec[0] + 8)
    # trainer rows, sprite entries
    for key in KT.TRAINERS:
        r = KT.row(key)
        take("trainers", KT.TRAINERS_TABLE + 40 * r, KT.TRAINERS_TABLE + 40 * r + 40)
    entries = sorted({v[1] for d in (KSP.PEOPLE, KSP.STATUES, KSP.LIVE) for v in d.values()})
    for n in entries:
        take("sprites", KSP.EXT_TABLE - B + 0x24 * n, KSP.EXT_TABLE - B + 0x24 * (n + 1))
    # the shop guard's bitmap
    for i in sorted(left):
        if K.SHOP_BITS_TOP - 0x100 < i <= K.SHOP_BITS_TOP and (b[i] & a[i]) == a[i]:
            take("shop bitmap (bits only added)", i, i + 1)
    # the Quest Log
    leg, legp, n = KJ.rows(a)
    for i in [0] + list(range(1 + KJ.COUNTED, n)):
        take("journal rows", leg + 16 * i + 2, leg + 16 * i + 4)
        take("journal rows", leg + 16 * i + 8, leg + 16 * i + 16)
        take("journal panes", legp + 16 * i + 1, legp + 16 * i + 2)
        take("journal panes", legp + 16 * i + 8, legp + 16 * i + 16)
    take("journal counts", KJ.NLEG_CMP - B, KJ.NLEG_CMP - B + 1)
    take("journal counts", KJ.PAGES - B + 8 * KJ.LEG_PAGE + 2, KJ.PAGES - B + 8 * KJ.LEG_PAGE + 3)
    # Area Zero's stamp
    az, sites = KP.az_stamp(bytearray(a))
    for s in sites:
        take("stamp sites (Area Zero's %04X)" % az, s, s + 2)
    for kind in sorted(count):
        print("  %-48s %d" % (kind, count[kind]))
    print("%d changed bytes" % len(diff))
    if left:
        runs, prev = [], None
        for i in sorted(left):
            if prev is not None and i == prev + 1:
                runs[-1][1] = i + 1
            else:
                runs.append([i, i + 1])
            prev = i
        for lo, hi in runs[:40]:
            print("  NOT ACCOUNTED FOR: %08X..%08X  %s -> %s" % (B + lo, B + hi, a[lo:hi][:16].hex(), b[lo:hi][:16].hex()))
        print("%d bytes in %d runs not accounted for" % (len(left), len(runs)))
        sys.exit(1)
    print("every changed byte accounted for")


if __name__ == "__main__":
    main(*sys.argv[1:3])
