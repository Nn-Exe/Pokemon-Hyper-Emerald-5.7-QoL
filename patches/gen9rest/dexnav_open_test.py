"""FOR TESTING ONLY - never for the working ROM or a release. The DexNav lets every Pokemon of an area be registered
and searched, seen or not. Asked for to test the 1-5% Pokemon of the whole Gen 9 test (2026-10-14: "can u bypass
the dexnav for testing?").
Both copies of is_seen answer "seen" at once: dexnavui's (0x09FD84F4, the Unbound-style screen R and START open:
icons, names, the SEARCH button) and dexnavseen's (0x08FF6BC0, the old list screen and dn_task, unused since
dexnavui but still in the ROM).
usage: python dexnav_open_test.py <in.gba> <out.gba>
"""
import sys

# push {r4,lr}; ldr r3,=SpeciesToNationalPokedexNum; bl callr3; cmp r0,#0; beq yes; movs r1,#0; ldr r3,=flag; bl;
# lsls r0,r0,#24; beq ret; yes: movs r0,#1; ret: pop {r4,pc}
SITES = {0x01FD84F4: "10b51a4b00f00af8002805d00021184b00f004f8000600d0012010bd",       # dexnavui
         0x00FF6BC0: "10b5074b00f00af8002805d00021054b00f004f8000600d0012010bd"}       # dexnavseen
OPEN = bytes.fromhex("01207047")                 # movs r0, #1; bx lr


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    for site, orig in SITES.items():
        orig = bytes.fromhex(orig)
        assert rom[site:site + len(orig)] == orig, "is_seen at %08X is not what it was (or already opened)" % (0x08000000 + site)
        rom[site:site + 4] = OPEN
    open(outp, "wb").write(rom)
    print("dexnav_open_test: is_seen at %s always answers seen" % ", ".join("%08X" % (0x08000000 + s) for s in SITES))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
