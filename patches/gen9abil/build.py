"""Build gen9abil's code: python build.py   (writes gen9abil.bin, gen9abil.sym, strings.h, strings.inc, strings.s)

The C files and scripts.s are compiled for the GBA (Thumb, ARM7TDMI) and linked at BASE against Hyper Emerald's
addresses (he.ld). The patcher writes the .bin at BASE and reads the .sym for the wrappers it points calls at, so a
build is needed only after the sources change; the two files are kept with the sources.
Needs arm-none-eabi-gcc (any recent one; this was built with xPack GNU Arm Embedded GCC 12.2.1): set ARMGCC to its
bin folder, or it is looked for in %LOCALAPPDATA%\\xpack-arm-gcc\\xpack-arm-none-eabi-gcc-12.2.1-1.2\\bin.
"""
import hashlib, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen9abil_data as D

BASE = 0x09E33000
SOURCES = ["g9.c", "calc.c", "hit.c", "moves.c", "entry.c", "state.c", "commander.c"]
ASM = ["scripts.s", "strings.s", "he_syms.s"]
BIN = os.environ.get("ARMGCC") or os.path.join(os.environ.get("LOCALAPPDATA", ""), "xpack-arm-gcc",
                                               "xpack-arm-none-eabi-gcc-12.2.1-1.2", "bin")
CFLAGS = ["-mthumb", "-mcpu=arm7tdmi", "-mno-thumb-interwork", "-Os", "-std=gnu11", "-ffreestanding",
          "-fno-builtin", "-fno-common", "-fno-strict-aliasing", "-ffunction-sections", "-Wall", "-Wextra", "-Wno-unused-parameter",
          "-Werror", "-I", HERE]

# the game's text: the international charset, the battle placeholders (0xFD n)
CHARS = {" ": 0x00, "é": 0x1B, "!": 0xAB, "?": 0xAC, ".": 0xAD, "-": 0xAE, "'": 0xB4, ",": 0xB8, "/": 0xBA,
         ":": 0xF0, "\n": 0xFE}
CHARS.update({str(i): 0xA1 + i for i in range(10)})
CHARS.update({chr(ord("A") + i): 0xBB + i for i in range(26)})
CHARS.update({chr(ord("a") + i): 0xD5 + i for i in range(26)})
PLACEHOLDERS = {"BUFF1": 0x00, "ATK": 0x0F, "DEF": 0x10, "SCR": 0x13, "MOVE": 0x14, "ATK_ABIL": 0x18,
                "DEF_ABIL": 0x19, "SCR_ABIL": 0x1A}


def encode(text):
    out, i = bytearray(), 0
    while i < len(text):
        if text[i] == "{":
            j = text.index("}", i)
            out += bytes([0xFD, PLACEHOLDERS[text[i + 1:j]]])
            i = j + 1
            continue
        out.append(CHARS[text[i]])
        i += 1
    return bytes(out) + b"\xff"


def tool(name):
    return os.path.join(BIN, "arm-none-eabi-" + name)


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=HERE)
    if r.returncode:
        sys.exit("%s\n%s%s" % (" ".join(cmd), r.stdout, r.stderr))
    return r.stdout


def write(name, text):
    with open(os.path.join(HERE, name), "w", encoding="ascii", newline="\n") as f:
        f.write(text)


def thumb1_check(elf, data):
    """Every stretch of code ($t mapping symbols, up to the next $d / $a) must be Thumb-1: on the GBA a Thumb-2
    encoding does not run. The ARM stretches are the linker's long-branch veneers."""
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
    marks = []
    for line in run([tool("readelf"), "-sW", elf]).splitlines():
        p = line.split()
        if len(p) >= 8 and p[7] in ("$t", "$d", "$a") and int(p[1], 16) >= BASE:
            marks.append((int(p[1], 16), p[7]))
    marks = sorted(set(marks))
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    n = 0
    for k, (a, kind) in enumerate(marks):
        if kind != "$t":
            continue
        end = marks[k + 1][0] if k + 1 < len(marks) else BASE + len(data)
        code = data[a - BASE:end - BASE]
        got = list(md.disasm(code, a))
        assert sum(i.size for i in got) == len(code), "code at %08X does not disassemble to its end" % a
        bad = [(hex(i.address), i.mnemonic) for i in got if i.size == 4 and i.mnemonic != "bl"]
        assert not bad, "Thumb-2 instructions: %s" % bad
        n += len(got)
    return n


def main():
    ids = {name: D.FIRST_STRING + k for k, (name, _) in enumerate(D.STRINGS)}
    write("strings.h", "/* made by build.py from gen9abil_data.py */\n" +
          "".join("#define %s 0x%X\n" % (n, i) for n, i in ids.items()))
    write("strings.inc", "@ made by build.py from gen9abil_data.py\n" +
          "".join("    .equ %s, 0x%X\n" % (n, i) for n, i in ids.items()))
    write("callasm.inc", "@ made by build.py from gen9abil_data.py\n" +
          "".join("    .equ G9_ASM_%s, %d\n" % (n[len("g9_asm_"):].upper(), D.CALLASM_FIRST + k)
                  for k, n in enumerate(D.CALLASM)))
    forbid = ["/* made by build.py from gen9abil_data.py (FORBIDDEN): the Gen 9 abilities each of the engine's lists of",
              " * untouchable abilities gets */"]
    for k, (at, first, count, keys) in enumerate(D.FORBIDDEN):
        forbid.append("static const u16 g9_forbid_%d[] = {%s, 0xFFFF};" % (
            k, ", ".join("0x%X" % D.ABILITIES[key][0] for key in keys)))
    forbid.append("static const struct { const u16 *list, *extra; } g9_forbid[] = {")
    forbid += ["    {(const u16 *)0x%08X, g9_forbid_%d}," % (at, k) for k, (at, _, _, _) in enumerate(D.FORBIDDEN)]
    forbid.append("};")
    write("forbid.h", "\n".join(forbid) + "\n")
    lines = ["@ made by build.py from gen9abil_data.py: the battle messages, in the game's charset",
             '    .section .rodata.strings, "a"']
    for k, (name, text) in enumerate(D.STRINGS):
        lines += ["    .global g9_string_%d" % k, "g9_string_%d:   @ %s" % (k, name),
                  "    .byte " + ", ".join("0x%02X" % b for b in encode(text))]
    write("strings.s", "\n".join(lines) + "\n")

    build = os.path.join(HERE, "build")
    os.makedirs(build, exist_ok=True)
    objs = []
    for src in SOURCES:
        o = os.path.join(build, src + ".o")
        run([tool("gcc")] + CFLAGS + ["-c", src, "-o", o])
        objs.append(o)
    for src in ASM:
        o = os.path.join(build, src + ".o")
        run([tool("as"), "-mthumb", "-mcpu=arm7tdmi", "-I", HERE, src, "-o", o])
        objs.append(o)
    libgcc = run([tool("gcc"), "-mthumb", "-mcpu=arm7tdmi", "-print-libgcc-file-name"]).strip()
    elf = os.path.join(build, "gen9abil.elf")
    run([tool("ld"), "--defsym", "BASE=0x%X" % BASE, "-T", "he.ld", "--gc-sections", "-e", "0",
         "-Map", os.path.join(build, "gen9abil.map"), "-o", elf] + objs + [libgcc])
    sections = run([tool("readelf"), "-SW", elf])
    for line in sections.splitlines():
        p = line.split()
        if len(p) > 6 and p[1] == ".data" and int(p[5], 16):
            sys.exit("gen9abil has writable data (.data/.bss): keep all state in G9")
    binpath = os.path.join(HERE, "gen9abil.bin")
    run([tool("objcopy"), "-O", "binary", "-j", ".text", elf, binpath])
    thumb1_check(elf, open(binpath, "rb").read())
    syms = []
    for line in run([tool("nm"), "-n", elf]).splitlines():
        p = line.split()
        if len(p) == 3 and p[1] in "TtRrDd" and int(p[0], 16) >= BASE:
            syms.append("%s %s" % (p[2], p[0].upper()[-8:]))
    data = open(binpath, "rb").read()
    syms.append("@size %X" % len(data))
    syms.append("@sha1 %s" % hashlib.sha1(data).hexdigest())
    write("gen9abil.sym", "\n".join(syms) + "\n")
    print("gen9abil.bin: %d bytes at %08X, sha1 %s" % (len(data), BASE, hashlib.sha1(data).hexdigest()))


if __name__ == "__main__":
    main()
