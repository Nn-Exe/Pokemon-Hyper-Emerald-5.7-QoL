"""Assemble the Gen 9 moves' animations: python build.py   (writes gen9anim.bin and gen9anim.sym)

anims.s holds the scripts in the battle animation language (defs.inc: its commands, the game's own 0x00..0x2F, and
the addresses of the game's scripts, sprite templates and tasks they use). They are assembled with xPack's
arm-none-eabi-as and linked at BASE; gen9anim.sym lists every script's address, the size and the sha1, which
gen9anim_patch.py checks. The assembler is found as gen9abil's build.py finds it (ARMGCC, or %LOCALAPPDATA%\\xpack-arm-gcc).
A machine without it patches from gen9anim.bin and gen9anim.sym as they are."""
import hashlib, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = 0x09E38000
BIN = os.environ.get("ARMGCC") or os.path.join(os.environ.get("LOCALAPPDATA", ""), "xpack-arm-gcc",
                                               "xpack-arm-none-eabi-gcc-12.2.1-1.2", "bin")


def tool(name):
    return os.path.join(BIN, "arm-none-eabi-" + name)


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=HERE)
    if r.returncode:
        sys.exit("%s\n%s%s" % (" ".join(cmd), r.stdout, r.stderr))
    return r.stdout


def main():
    build = os.path.join(HERE, "build")
    os.makedirs(build, exist_ok=True)
    obj, elf, out = (os.path.join(build, n) for n in ("anims.o", "gen9anim.elf", "gen9anim.bin"))
    ld = os.path.join(build, "gen9anim.ld")
    with open(ld, "w", newline="\n") as f:
        f.write("SECTIONS { . = 0x%08X; .rodata : { *(.rodata*) } /DISCARD/ : { *(.text*) *(.data*) *(.bss*) "
                "*(.ARM.attributes) } }\n" % BASE)
    run([tool("as"), "-mthumb", "-mcpu=arm7tdmi", "-I", HERE, "-o", obj, os.path.join(HERE, "anims.s")])
    run([tool("ld"), "-T", ld, "-o", elf, obj])
    run([tool("objcopy"), "-O", "binary", "-j", ".rodata", elf, out])
    data = open(out, "rb").read()
    syms = []
    for line in run([tool("nm"), elf]).splitlines():
        addr, kind, name = line.split()
        if kind in "TtRrDd" and name.endswith("_ANIM"):
            syms.append("%s %s" % (name, addr.upper()))
    syms.sort()
    syms += ["@size %d" % len(data), "@sha1 %s" % hashlib.sha1(data).hexdigest()]
    open(os.path.join(HERE, "gen9anim.bin"), "wb").write(data)
    with open(os.path.join(HERE, "gen9anim.sym"), "w", newline="\n") as f:
        f.write("\n".join(syms) + "\n")
    print("gen9anim.bin: %d bytes at %08X, sha1 %s" % (len(data), BASE, hashlib.sha1(data).hexdigest()))


if __name__ == "__main__":
    main()
