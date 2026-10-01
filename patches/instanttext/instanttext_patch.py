"""Instant text: a 4th Text Speed in the Option menu (Hyper Emerald v5.7). Apply last.
usage: python instanttext_patch.py <in.gba> <out.gba>

optionsTextSpeed is the low 3 bits of SaveBlock2+0x14 (0 Slow, 1 Mid, 2 Fast); Instant is 3. Every reader of the
field in the ROM was checked (the six `ldrb [.., #0x14]; lsls #29; lsrs #29`, the two callers of GetPlayerTextSpeed
and the recorded-battle copy) and each is made to take 3:
* GetPlayerTextSpeedDelay 0x08197990 reset anything above Fast to Mid and indexed {8, 4, 1} - now it keeps 3 and
  reads {8, 4, 1, 1}: Instant prints at Fast's delay (printer textSpeed 0), and the burst below does the rest.
* RenderText's scroll 0x08005CF6 and the braille font's 0x081BA5D4 index {1, 2, 4} by the option; their 4th
  byte is 0, which would scroll by 0 pixels forever. Both now read {1, 2, 4, 8}.
* Berry Crush's SetNamesAndTextSpeed 0x08021012 maps 0/1/2 to 8/4/1 and leaves anything else unset: `beq` -> `bge`,
  so 3 gets 1 too.
* The recorded-battle table 0x085CD668 already has a 4th entry (0: the whole message at once); left alone.
* RunTextPrinters 0x08004778 -> run_printers (instanttext.s): at Instant, a printer at textSpeed 0 prints until its
  next wait in one frame.
* Option menu: TextSpeed_ProcessInput 0x080BABDC wraps at 3 instead of 2 (two immediates), TextSpeed_DrawChoices
  0x080BAC38 -> draw_speed, which draws the four words. "Instant" is new text with the game's own colour prefix.
A save with Instant loaded by an older build falls back to Mid (the old GetPlayerTextSpeedDelay resets it).
"""
import os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "sinnohmap"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "translation"))
import sinnohmap_patch as SM                    # the Thumb check
from inserter import ENC

FREE = 0x00FF6900                               # in the unreferenced 0xFF run 0x08FF6600..0x08FFD5A0, clear of the
FREE_END = 0x00FF7700                           # data words that happen to read 0x08FF67FF and 0x08FF7703
BASE = 0x08000000 + FREE

RUN_PRINTERS = 0x08004778
DRAW_CHOICES = 0x080BAC38
INPUT_RIGHT = 0x080BABEE                        # cmp r3, #1 (selection <= 1: +1, else 0)
INPUT_LEFT = 0x080BAC24                         # movs r3, #2 (selection 0: wrap to the last)
DELAY_CLAMP = 0x0819799C                        # cmp r0, #2 (above Fast: reset to Mid)
DELAY_LIT, DELAYS = 0x081979C0, 0x0860F094
SCROLL_LIT, SCROLLS = 0x08005D1C, 0x082E9D10
BRAILLE_LIT, BRAILLE_SCROLLS = 0x081BA5FC, 0x08616124
CRUSH_BEQ = 0x08021036                          # cmp r0, #2; beq -> speed 1
TEXT_SLOW, TEXT_MID, TEXT_FAST = 0x085EE5D4, 0x085EE5DF, 0x085EE5E9
FONTW = 0x006542E4                              # the normal font's glyph widths (questlog_patch.FONTW)
ROW_X0, ROW_X1 = 76, 204                        # the row: after "Text Speed" (ends at 65) .. the window's edge (208)


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    o = lambda a: a - 0x08000000
    u32 = lambda a: struct.unpack_from("<I", rom, o(a))[0]
    at = lambda a, hexs: bytes(rom[o(a):o(a) + len(bytes.fromhex(hexs))]) == bytes.fromhex(hexs)
    enc = lambda s: bytes(ENC[c] for c in s)

    # every site as the game has it
    assert at(RUN_PRINTERS, "f0b5474680b40c480078002837d1"), "RunTextPrinters changed"
    assert at(DRAW_CHOICES, "70b5464640b481b0"), "TextSpeed_DrawChoices changed"
    assert at(INPUT_RIGHT, "012b06d8") and at(INPUT_LEFT, "0223"), "TextSpeed_ProcessInput changed"
    assert at(DELAY_CLAMP, "022805d9"), "GetPlayerTextSpeedDelay changed"
    assert u32(DELAY_LIT) == DELAYS and rom[o(DELAYS):o(DELAYS) + 3] == bytes([8, 4, 1])
    assert u32(SCROLL_LIT) == SCROLLS and rom[o(SCROLLS):o(SCROLLS) + 4] == bytes([1, 2, 4, 0])
    assert u32(BRAILLE_LIT) == BRAILLE_SCROLLS and rom[o(BRAILLE_SCROLLS):o(BRAILLE_SCROLLS) + 4] == bytes([1, 2, 4, 0])
    assert at(CRUSH_BEQ - 2, "022804d0"), "Berry Crush's text speed switch changed"
    for lit, table in ((DELAY_LIT, DELAYS), (SCROLL_LIT, SCROLLS), (BRAILLE_LIT, BRAILLE_SCROLLS)):
        refs = [k for k in range(0, len(rom), 4) if struct.unpack_from("<I", rom, k)[0] == table]
        assert refs == [o(lit)], "%08X has other readers: %s" % (table, refs)

    # the words: the game's three, and Instant with the same colour prefix
    prefix = bytes(rom[o(TEXT_SLOW):o(TEXT_SLOW) + 6])
    assert prefix == bytes.fromhex("fc0106fc0307")
    words = []
    for addr, word in ((TEXT_SLOW, "Slow"), (TEXT_MID, "Mid"), (TEXT_FAST, "Fast")):
        assert rom[o(addr):o(addr) + 7 + len(word)] == prefix + enc(word) + b"\xFF", "%08X is not %r" % (addr, word)
        words.append((addr, word))
    instant = prefix + enc("Instant") + b"\xFF"
    assert len(instant) <= 16                   # DrawOptionMenuChoice copies 15 bytes + EOS
    widths = [sum(rom[FONTW + c] for c in enc(w)) for _, w in words] + [sum(rom[FONTW + c] for c in enc("Instant"))]
    gap = (ROW_X1 - ROW_X0 - sum(widths)) / 3
    assert gap >= 6, "the four words do not fit: %s" % widths
    xs, x = [], ROW_X0
    for w in widths:
        xs.append(round(x))
        x += w + gap

    def assemble(names, xs_addr):
        src = open(os.path.join(HERE, "instanttext.s"), encoding="ascii").read()
        src = src.replace("NAMES_ADDR", "0x%08X" % names).replace("XS_ADDR", "0x%08X" % xs_addr)
        return SM.thumb(src, BASE)

    code, _ = assemble(BASE, BASE)
    data = BASE + ((len(code) + 3) & ~3)
    names, xs_addr, delays, scrolls, text = data, data + 16, data + 20, data + 24, data + 28
    code2, dis = assemble(names, xs_addr)
    assert len(code2) == len(code)
    funcs = [i.address | 1 for i in dis if i.mnemonic == "push" and "lr" in i.op_str]
    assert len(funcs) == 2, "expected run_printers and draw_speed, found %d" % len(funcs)
    run_printers, draw_speed = funcs
    blob = bytearray(code2) + b"\x00" * (data - BASE - len(code2))
    blob += struct.pack("<4I", TEXT_SLOW, TEXT_MID, TEXT_FAST, text)
    blob += bytes(xs) + bytes([8, 4, 1, 1]) + bytes([1, 2, 4, 8]) + instant
    end = FREE + len(blob)
    assert end <= FREE_END and set(rom[FREE:end]) == {0xFF}, "target region not free"
    for k in range(0, len(rom), 4):
        v = struct.unpack_from("<I", rom, k)[0]
        assert not BASE <= v < 0x08000000 + end, "%08X already points into the target (%08X)" % (0x08000000 + k, v)
    rom[FREE:end] = blob

    tramp = lambda target: bytes.fromhex("004b1847") + struct.pack("<I", target)
    rom[o(RUN_PRINTERS):o(RUN_PRINTERS) + 8] = tramp(run_printers)
    rom[o(DRAW_CHOICES):o(DRAW_CHOICES) + 8] = tramp(draw_speed)
    rom[o(INPUT_RIGHT)] = 2                     # cmp r3, #2: Slow, Mid, Fast step right, Instant wraps to Slow
    rom[o(INPUT_LEFT)] = 3                      # movs r3, #3: left from Slow wraps to Instant
    rom[o(DELAY_CLAMP)] = 3                     # cmp r0, #3: Instant is kept
    struct.pack_into("<I", rom, o(DELAY_LIT), delays)
    struct.pack_into("<I", rom, o(SCROLL_LIT), scrolls)
    struct.pack_into("<I", rom, o(BRAILLE_LIT), scrolls)
    rom[o(CRUSH_BEQ) + 1] = 0xDA                # beq -> bge
    open(outp, "wb").write(rom)
    print("run_printers %08X, draw_speed %08X, data %08X, end %08X; x %s (widths %s, gap %.1f)"
          % (run_printers, draw_speed, data, 0x08000000 + end, xs, widths, gap))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
