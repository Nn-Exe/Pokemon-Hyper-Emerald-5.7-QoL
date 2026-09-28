"""Print a script as a sorted listing with opcode names and texts: python dis.py 0x098C202D [...]"""
import struct, sys
import scripts as S
NAMES = {0x02: "end", 0x03: "return", 0x04: "call", 0x05: "goto", 0x06: "goto_if", 0x07: "call_if", 0x09: "callstd",
         0x0F: "loadword", 0x16: "setvar", 0x17: "addvar", 0x19: "copyvar", 0x21: "compare", 0x23: "callasm",
         0x25: "special", 0x26: "specialvar", 0x27: "waitstate", 0x28: "delay", 0x29: "setflag", 0x2A: "clearflag",
         0x2B: "checkflag", 0x2F: "playse", 0x30: "waitse", 0x31: "playfanfare", 0x32: "waitfanfare",
         0x33: "playbgm", 0x35: "fadedefaultbgm", 0x36: "fadenewbgm", 0x37: "fadeoutbgm", 0x39: "warp",
         0x3A: "warpsilent", 0x3C: "warpteleport", 0x44: "additem", 0x4F: "applymovement", 0x51: "waitmovement",
         0x53: "removeobject", 0x55: "addobject", 0x57: "setobjectxy", 0x5A: "faceplayer", 0x5B: "turnobject",
         0x5C: "trainerbattle", 0x5D: "dotrainerbattle", 0x66: "waitmessage", 0x67: "message", 0x68: "closemessage",
         0x69: "lockall", 0x6A: "lock", 0x6B: "releaseall", 0x6C: "release", 0x6D: "waitbuttonpress",
         0x6E: "yesnobox", 0x79: "givemon", 0x86: "pokemart", 0x97: "fadescreen", 0x98: "fadescreenspeed",
         0x99: "setflashlevel", 0x9A: "animateflash", 0x9C: "dofieldeffect", 0xA1: "playmoncry", 0xA2: "setmetatile",
         0xA4: "setweather", 0xA5: "resetweather", 0xA6: "doweather", 0xB6: "setwildbattle", 0xB7: "dowildbattle",
         0xC5: "waitmoncry", 0x7D: "bufferspeciesname", 0x80: "bufferitemname", 0x6F: "multichoice",
         0x96: "getpartysize", 0x5E: "gotopostbattlescript", 0xB1: "setescapewarp", 0xC4: "setrespawn",
         0xCB: "goto_if_questlog", 0x9D: "setfieldeffectargument", 0x9E: "waitfieldeffect", 0x52: "showobjectat"}
def show(entry):
    out, probs = S.walk(entry)
    for a, op, args in sorted(out):
        extra = ""
        if op == 0x0F and len(args) >= 5:
            extra = " " + repr(S.text_at(struct.unpack_from("<I", args, 1)[0], 400))
        print("%08X %-15s %s%s" % (a, NAMES.get(op, "op%02X" % op), args.hex(), extra))
    for p in probs: print("!!", p)
if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    for x in sys.argv[1:]:
        print("=====", x); show(int(x, 0))
