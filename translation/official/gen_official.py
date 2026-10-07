"""Build patches/zhtext/official.json + charmap.json: every official Emerald text the hack still holds in Chinese at
its original address, with the official English in the modern casing.   python gen_official.py <rom> <outdir>
Each entry: a = address, n = the official text's length (its slot), zh = the bytes there now (the Chinese string and
its terminator), t = the English (pokeemerald source syntax), ref = something in the ROM still points at it."""
import json, os, sys
import vanilla as V
import scan as S
import decap as D

SKIP = ("gJPText", "gText_NamingScreenKeyboard")
D.KEEP |= {"RTC", "NY"}
OVERRIDE = {  # where the hack's text means something else than the official one, or the casing rule is wrong
    "sLightningRodDescription": "Draws Elec, ups Sp. Atk",          # the hack's: absorbs Electric moves, raises Sp. Atk
    "sHugePowerDescription": "Doubles Attack",                      # the hack's: Attack doubled
    "sPurePowerDescription": "Doubles Attack",
    "gText_EnergyPowder50": "EnergyPowder{CLEAR_TO 114}{FONT_SMALL}50",
    "sText_BattleTowerLv50": "Battle Tower Lv. 50",
    "sText_NameWantedOfferLv": "Name{CLEAR_TO 60}Wanted{CLEAR_TO 110}Offer{CLEAR_TO 198}Lv.",
}
FIX = [("Trainer(S)", "Trainer(s)"), ("“Give Me\\nAwesome Trainer”", "“GIVE ME\\nAWESOME TRAINER”")]


def main(rompath, outdir):
    rom = open(rompath, "rb").read()
    table = json.load(open("decap.json", encoding="utf-8"))
    scan = json.load(open("scan_now.json", encoding="utf-8"))
    out, skipped, seen = [], [], set()
    for x in scan:
        if x["kind"] != "zh" or x["name"].startswith(SKIP):
            continue
        a = int(x["addr"], 16)
        if a in seen:
            continue
        seen.add(a)
        o, n, k = a - 0x08000000, x["len"], x["zhlen"]
        tail = rom[o + k:o + n]
        if tail and set(tail) - {0x00, 0xFF}:
            skipped.append((x["addr"], x["name"], "tail in use"))
            continue
        text = OVERRIDE.get(x["name"]) or D.apply(x["en"], table)
        for p, q in FIX:
            text = text.replace(p, q)
        enc = V.encode(text + "$")
        if len(enc) > n:
            skipped.append((x["addr"], x["name"], "too long"))
            continue
        out.append({"a": x["addr"], "n": n, "zh": rom[o:o + k].hex(), "t": text, "ref": x["ref"], "name": x["name"]})
    out.sort(key=lambda e: e["a"])
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "official.json"), "w", encoding="utf-8", newline="\n") as f:
        f.write("[\n" + ",\n".join(json.dumps(e, ensure_ascii=False) for e in out) + "\n]\n")
    cm = {"chars": {k: list(v) for k, v in V.CHARS.items()},
          "names": {k: list(v) for k, v in V.NAMES.items()}}
    json.dump(cm, open(os.path.join(outdir, "charmap.json"), "w", encoding="utf-8", newline="\n"), ensure_ascii=False, sort_keys=True)
    print(len(out), "entries (%d still referenced);" % sum(e["ref"] for e in out), len(skipped), "skipped:", skipped[:12])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
