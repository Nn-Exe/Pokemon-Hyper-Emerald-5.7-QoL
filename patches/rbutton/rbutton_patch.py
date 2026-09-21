"""R opens the DexNav; Auto Run moves to the Option menu (Hyper Emerald v5.7). Apply after dexnavchain.

    python patches/rbutton/rbutton_patch.py in.gba out.gba

ROM changes:
  * the field-input chain (ProcessPlayerFieldInput's trampoline -> L quick repel -> auto-run's R toggle) now
    ends in r_hook: the L-repel stub's "next hook" literal is repointed, the trampoline itself is untouched;
  * auto-run's run decision reads optionsButtonMode (SaveBlock2+0x13, 4 = on) instead of SaveBlock1+0x31;
  * ButtonMode_ProcessInput (0x080BAFCC) and ButtonMode_DrawChoices (0x080BB028), used only by the Option
    menu, become trampolines to a two-state Off/On version;
  * the row's label "Button Mode" is rewritten in place as "Auto Run".
Every reader of optionsButtonMode was checked: they test for exactly 1 (LR) or 2 (L=A), or copy it, so 4
behaves as Normal. Auto-run's old byte at SaveBlock1+0x31 is left alone and no longer read.
"""
import struct, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "dexnavchain"))
import dexnavchain_patch as dnc

FREE = 0x00FDFC00                       # after the DexNav chain blob, which keeps ~2 KB to grow into
BASE = 0x08000000 + FREE

PFI_TRAMPOLINE = 0x09C014               # ldr r3,[pc,#0]; bx r3; .word  (auto-run's hook 2)
PFI_TARGET = 0x09C018
AUTORUN_FREE = 0xFD9960                 # auto-run's blob: toggle_hook sits at +2
BM_INPUT = 0x0BAFCC                     # ButtonMode_ProcessInput
BM_DRAW = 0x0BB028                      # ButtonMode_DrawChoices
TEXT_BUTTONMODE = 0x5EE5C8              # "Button Mode"


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    # the DexNav blob, rebuilt and compared: identical but for the one task pointer dexnavchain repointed
    code_, code_len, data, data_base, daddrs, funcs, menu_callback, caddrs = dnc.dexnav_patch.assemble_blob()
    dblob = bytes(code_) + bytes(code_len - len(code_)) + data
    here = bytes(rom[dnc.dexnav_patch.FREE:dnc.dexnav_patch.FREE + len(dblob)])
    diff = [i for i in range(0, len(dblob), 4) if here[i:i + 4] != dblob[i:i + 4]]
    assert len(diff) == 1 and dblob[diff[0]:diff[0] + 4] == struct.pack("<I", funcs[4] | 1), \
        "the DexNav blob is not dexnav's plus dexnavchain's task pointer"
    dn = {"menu_callback": funcs[0]}

    assert bytes(rom[PFI_TRAMPOLINE:PFI_TRAMPOLINE + 4]) == bytes.fromhex("004b1847")
    lrepel = struct.unpack_from("<I", rom, PFI_TARGET)[0] & ~1 & 0x01FFFFFF   # the L quick-repel stub
    toggle = struct.pack("<I", (0x08000000 + AUTORUN_FREE + 2) | 1)
    near = bytes(rom[lrepel:lrepel + 0x100])
    assert near.count(toggle) == 1, "the L-repel stub does not hand over to auto-run's toggle"
    next_hook = lrepel + near.index(toggle)

    # auto-run's run decision: ldr r1,[r1] / movs r2,#0x31 / ldrb r1,[r1,r2] after ldr r1,=gSaveBlock1Ptr
    old = bytes.fromhex("0968" "3122" "895c")
    blob = bytes(rom[AUTORUN_FREE:AUTORUN_FREE + 0x100])
    assert blob.count(old) == 1, "auto-run's flag read not found exactly once"
    at = AUTORUN_FREE + blob.index(old)
    new, _ = dnc.thumb("ldr r1, [r1, #4]\n ldrb r1, [r1, #0x13]\n lsrs r1, r1, #2", 0x08000000 + at)
    assert len(new) == 6                # gSaveBlock2Ptr sits right after gSaveBlock1Ptr: 4 -> 1, 0..3 -> 0

    assert bytes(rom[BM_INPUT:BM_INPUT + 6]) == bytes.fromhex("00b50006030e"), "ButtonMode_ProcessInput differs"
    assert bytes(rom[BM_DRAW:BM_DRAW + 6]) == bytes.fromhex("70b5464640b4"), "ButtonMode_DrawChoices differs"
    label = bytes(rom[TEXT_BUTTONMODE:TEXT_BUTTONMODE + 12])
    assert label == dnc.text("Button Mode"), "the Button Mode label differs"

    src = open(os.path.join(HERE, "rbutton.s"), encoding="ascii").read()

    def assemble(addrs):
        s = src
        for k, v in sorted(addrs.items(), key=lambda kv: -len(kv[0])):
            s = s.replace(k + "_ADDR", "0x%08X" % v)
        return dnc.thumb(s, BASE)

    fixed = {"STATE": dnc.STATE, "MENUCB": dn["menu_callback"] | 1, "TASK_OPEN": BASE | 1}
    code, dis = assemble(fixed)
    funcs = [i.address for i in dis if i.mnemonic == "push"]
    order = ("r_hook", "open_dexnav", "task_open", "opt_input", "opt_draw")
    assert len(funcs) == len(order), "unexpected function layout: %d pushes" % len(funcs)
    sym = dict(zip(order, funcs))
    fixed["TASK_OPEN"] = sym["task_open"] | 1
    code2, _ = assemble(fixed)
    assert len(code2) == len(code)
    code = code2

    end = FREE + ((len(code) + 3) & ~3)
    assert set(rom[FREE:end]) == {0xFF}, "target region not free"
    rom[FREE:FREE + len(code)] = code

    rom[at:at + 6] = new
    struct.pack_into("<I", rom, next_hook, sym["r_hook"] | 1)
    for site, fn in ((BM_INPUT, "opt_input"), (BM_DRAW, "opt_draw")):
        assert site % 4 == 0
        rom[site:site + 8] = bytes.fromhex("004b1847") + struct.pack("<I", sym[fn] | 1)
    newlabel = dnc.text("Auto Run")
    rom[TEXT_BUTTONMODE:TEXT_BUTTONMODE + len(newlabel)] = newlabel
    open(outp, "wb").write(rom)
    print("code %d bytes @%08X, end %08X; auto-run flag read patched @%08X; L-repel's next hook @%08X" % (
        len(code), BASE, 0x08000000 + end, 0x08000000 + at, 0x08000000 + next_hook))
    print("  " + ", ".join("%s %08X" % (k, v | 1) for k, v in sym.items()))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
