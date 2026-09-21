"""Compare test_journal.lua's log with expected.json: python check_journal.py journal_log.txt

Every case must show exactly the bytes make_tests.py predicted. Prints the chosen step's text for a mismatch.
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "translation"))
from inserter import ENC

DEC = {v: k for k, v in ENC.items()}
DEC.update({0xFE: "\\n", 0xFA: "\\l", 0xFB: "\\p", 0x00: " "})


def show(b):
    return "".join(DEC.get(x, "{%02X}" % x) for x in b)


def main(log):
    want = json.load(open(os.path.join(HERE, "expected.json")))
    got = {}
    for line in open(log, encoding="utf-8"):
        if line.startswith("CASE ") and " | " in line:
            head, hexs = line.rstrip("\n").split(" | ", 1)
            got[int(head.split()[1])] = hexs.strip()
    bad = 0
    for n, c in enumerate(want, 1):
        g = got.get(n)
        if g == c["bytes"]:
            continue
        bad += 1
        print("FAIL case %d (%s), step %s" % (n, c["name"], c["step"]))
        print("   want: " + show(bytes.fromhex(c["bytes"]))[:300])
        print("   got:  " + (show(bytes.fromhex(g))[:300] if g is not None else "(nothing logged)"))
    print("%d of %d cases match" % (len(want) - bad, len(want)))
    return bad


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1]) else 0)
