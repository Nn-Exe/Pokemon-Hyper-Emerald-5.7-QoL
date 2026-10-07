"""Chinese names inside struct tables: runs of >=2 clean hanzi ended by 0xFF, any byte before; hits that repeat at a
constant stride (a table) are reported.   python names_scan2.py <rom>"""
import sys, collections
import scan as S
import remain as R

rom = open(sys.argv[1], "rb").read()
n = len(rom)
hits = []
i = 0x100000
while i < n - 4:
    if rom[i] in S.LEADS and rom[i + 1] <= 0xF6:
        j, txt = i, ""
        while j < n - 1 and rom[j] in S.LEADS and rom[j + 1] <= 0xF6 and len(txt) < 8:
            o = S.adj(rom[j]) * 247 + rom[j + 1]
            if o >= len(S.GB) or S.GB[o] == "?":
                break
            txt += S.GB[o]; j += 2
        if len(txt) >= 2 and rom[j] == 0xFF and all(ch in R.GENUINE for ch in txt) and sum(ch not in R.NOISE for ch in txt) >= 2:
            hits.append((i, txt))
            i = j
    i += 1
print(len(hits), "hits")
# cluster: consecutive hits whose gaps share a small common stride
addrs = [a for a, _ in hits]
text = dict(hits)
used = set()
for stride in (8, 11, 12, 13, 14, 16, 20, 24, 28, 32, 36, 40, 44, 48, 52, 56, 64, 88, 100):
    by = collections.defaultdict(list)
    for a in addrs:
        by[a % stride].append(a)
    for r, lst in by.items():
        run = [lst[0]]
        for a in lst[1:]:
            if a - run[-1] <= stride * 6:
                run.append(a)
            else:
                if len(run) >= 5 and not used & set(run):
                    print("stride %3d  %08X..%08X  %3d hits: %s" % (stride, 0x08000000 + run[0], 0x08000000 + run[-1], len(run), " ".join(text[x] for x in run[:8])))
                    used |= set(run)
                run = [a]
        if len(run) >= 5 and not used & set(run):
            print("stride %3d  %08X..%08X  %3d hits: %s" % (stride, 0x08000000 + run[0], 0x08000000 + run[-1], len(run), " ".join(text[x] for x in run[:8])))
            used |= set(run)
rest = [a for a in addrs if a not in used]
blocks = collections.Counter(a >> 16 for a in rest)
print("unclustered by 64K block:", {("%04X" % (0x800 + b)): c for b, c in sorted(blocks.items()) if c >= 3})
