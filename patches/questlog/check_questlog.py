"""Compare test_questlog.lua's log with the Journal's expected.json: python check_questlog.py questlog_log.txt

For every scenario: the Quest Log's current row must be the step the Journal names, the screen must open on
that step's chapter with it selected, and A on it must show the Journal's own text laid out for the pane.
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "journal"))
import steps as S

HEADS = [S.HOENN, S.POST, S.SINNOH, S.LOST]


def pane(msg):
    """The Journal's message as the Quest Log lays it out: no header line, plain line breaks, 8 lines a page."""
    assert msg.endswith(b"\xfc\x09")
    body = msg[:-2]
    body = body[body.index(0xFE) + 1:]
    out, lines = bytearray(), 1
    for b in body:
        if b in (0xFA, 0xFB, 0xFE):
            if lines == 8:
                out.append(0xFF)
                lines = 1
            else:
                out.append(0xFE)
                lines += 1
        else:
            out.append(b)
    out.append(0xFF)
    return bytes(out)


def main(log):
    want = json.load(open(os.path.join(HERE, "..", "journal", "expected.json")))
    first = {}
    for i, (h, _, _) in enumerate(S.STEPS):
        first.setdefault(h, i)
    got, det = {}, {}
    for line in open(log, encoding="utf-8"):
        if line.startswith("CASE ") and " | " in line:
            head, pos, st = line.rstrip("\n").split(" | ")
            p = pos.split()
            got[int(head.split()[1])] = (int(p[1]), int(p[3]), int(p[5]), st)
        elif line.startswith("DETAIL "):
            head, hexs = line.rstrip("\n").split(" | ", 1)
            det[int(head.split()[1])] = (int(head.split()[3]), hexs.strip())
    bad = 0
    for n, c in enumerate(want, 1):
        step = len(S.STEPS) if c["step"] is None else c["step"]   # None: everything is done
        errs = []
        if n not in got:
            errs.append("nothing logged")
        else:
            cur, page, sel, st = got[n]
            if cur != step:
                errs.append("current row %d, Journal says %d" % (cur, step))
            hp = HEADS.index(S.STEPS[step][0]) if step < len(S.STEPS) else 3
            if page != hp or first[HEADS[hp]] + sel != step:
                errs.append("opened on page %d row %d" % (page, sel))
            if st[step] != "2":
                errs.append("status of the current row is %s" % st[step])
            mode, hexs = det.get(n, (None, None))
            if mode != 1 or hexs != pane(bytes.fromhex(c["bytes"])).hex():
                errs.append("detail differs:\n     want %s\n     got  %s" % (pane(bytes.fromhex(c["bytes"])).hex(), hexs))
        if errs:
            bad += 1
            print("FAIL case %d (%s): %s" % (n, c["name"], "; ".join(errs)))
    print("%d of %d cases match" % (len(want) - bad, len(want)))
    return bad


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1]) else 0)
