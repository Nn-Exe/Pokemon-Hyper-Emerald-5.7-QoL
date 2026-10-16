"""The summit (the God of Forms, the Lv 70 Enamorus): a lost attempt no longer ends the quest (Hyper Emerald v5.7).
usage: python summitfix_patch.py <in.gba> <out.gba>          in the chain: after sprframe, before zhtext

Reported: "I battled the girl on top of the highland, I didn't understand what to do so I just defeated her every
time until I was brought back; now my nameless stone is gone" - and the Journal's "The summit" stays Active.

How the hack's script goes (Moonbow Dome 35/10, object 0, 0x098C5E66; reached from the guard in Hisui 37/106,
0x098B201D, who wants the stone, item 745, flag 0x4319 and not 0x4323):
1. two battles with her creations (trainer 1304): lose one and you are carried down the mountain (0x098C5F06);
2. the stone glows and the clay figure crumbles;
3. she fights herself (trainer 1340, flag 0x278). Each win she starts over ("the Hourai Elixir"); the THIRD win
   in a visit (VAR 0x4002) is "I'm getting a bit bored... Fine, I'll let you go" (0x098C6143) -> carried down.
   The story only goes on when she WINS (outcome > 1; no black-out, flag 0x273): "I, having defeated you,
   naturally claimed the rainbow's power" -> her last team (trainer 1341), which must be beaten -> she joins as
   a wild Lv 70 Enamorus (species 1025) -> flag 0x4323.
Every way down the mountain ran `removeitem 745` (0x098C5F19), and the game has one stone: Kitty (35/8,
0x098B1F85) gives it for the Dried Fish (item 744), a single item ball (hide flag 0x4322). So one failed visit -
a lost battle, or winning three times, which is what a strong team does - locked the summit for good.

The patch (script bytes only):
* the way down keeps the stone: that `removeitem` is five nops. Come back and try again.
* Kitty gives the stone again to a save that is already locked: no Dried Fish, the fish taken (0x4322), no stone,
  the summit not done (0x4323 clear) -> a line and `additem 745`. Her `checkitem 744` is a `goto` to that script
  (free space), which does her own check first; every other case falls back into her script.
* a hint where it is needed: "I'm getting a bit bored..." now says she never stops until she wins.
The success path still takes the stone, as the hack does.
"""
import os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "translation"))
from inserter import ENC

FREE, FREE_END = 0x00FF8B40, 0x00FF9400         # itemdesc's window (it ends at 0x08FF8B06): a stretch of the 0xFF
BASE = 0x08000000 + FREE                        # run 0x08FF6600.. that no word in the ROM points into
FONTW, MAXW = 0x006542E4, 216                   # the normal font's widths; the message box
STONE, FISH = 745, 744
FLAG_FISH, FLAG_DONE = 0x4322, 0x4323

DOWN = (0x098C5F06, "97010f00517ab70809032a73022a76022a780245e9020100970025000039256aff0b0006")
DOWN_REMOVE = 0x098C5F19                        # removeitem 745, 1
KITTY = (0x098B1F85, "6a5a47e8020100210d8001000601fa1f8b090f00")
KITTY_CHECK, KITTY_TRADE, KITTY_HELLO = 0x098B1F87, 0x098B1FFA, 0x098B1F97
BORED = (0x098C6143, "0f0073f1b708090305065f8c09")
BORED_OLD_TEXT = (0x08B7F173, "c7e3e3adadad00c3")   # "Moo... I"
NOTE = "\x00"                                   # the "~" Kitty ends her lines with: the hack's two-byte glyph F9 D3

KITTY_TEXT = ["Kitty: Mrow? You lost the stone", "from the dried fish?",
              None,
              "Lucky you! That old fish had two", "of them in its belly. Here, take", "this one, and hold on tight" + NOTE]
BORED_TEXT = ["Moo... I’m getting a bit bored of", "playing...",
              None,
              "You still don’t get it? I never", "stop until I win. Beat me a", "thousand times and I’ll just", "start over.",
              None,
              "Fine, I’ll let you go. Come back", "when you’ve worked out how this", "ends."]


def text(rom, lines):
    """pages (None between them) of lines -> game text; the first break of a page is \\n, the rest \\l"""
    out, first = bytearray(), True
    for i, l in enumerate(lines):
        if l is None:
            out.append(0xFB); first = True
            continue
        if i and lines[i - 1] is not None:
            out.append(0xFE if first else 0xFA); first = False
        w = 0
        for ch in l:
            if ch == NOTE:
                out += b"\xf9\xd3"; w += 12
            else:
                out.append(ENC[ch]); w += rom[FONTW + ENC[ch]]
        assert w <= MAXW, "%r is %d px, wider than the message box" % (l, w)
    return bytes(out) + b"\xff"


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    o = lambda a: a - 0x08000000
    at = lambda a, hexs: bytes(rom[o(a):o(a) + len(bytes.fromhex(hexs))]) == bytes.fromhex(hexs)
    p32 = lambda v: struct.pack("<I", v)
    u16 = lambda v: struct.pack("<H", v)

    assert at(*DOWN), "the way down the mountain is not the script expected"
    assert at(DOWN_REMOVE, "45" + u16(STONE).hex() + "0100")
    assert at(*KITTY) and at(KITTY_CHECK, "47" + u16(FISH).hex() + "0100"), "Kitty's script is not the one expected"
    assert at(KITTY_TRADE, "0f00") and at(KITTY_HELLO, "0f00")
    assert at(*BORED) and at(*BORED_OLD_TEXT), "the 'bored' line is not the one expected"

    kitty_text, bored_text = text(rom, KITTY_TEXT), text(rom, BORED_TEXT)
    checkitem = lambda item: b"\x47" + u16(item) + u16(1) + b"\x21\x0d\x80\x01\x00"     # ...; compare VAR_RESULT, 1
    script = b"".join((
        checkitem(FISH), b"\x06\x01" + p32(KITTY_TRADE),             # a Dried Fish: her trade, as before
        b"\x2b" + u16(FLAG_DONE), b"\x06\x01" + p32(KITTY_HELLO),    # the summit is done
        b"\x2b" + u16(FLAG_FISH), b"\x06\x00" + p32(KITTY_HELLO),    # the fish was never picked up
        checkitem(STONE), b"\x06\x01" + p32(KITTY_HELLO),            # the stone is in the Bag
    ))
    text_at = BASE + len(script) + 6 + 2 + 5 + 2
    script += b"\x0f\x00" + p32(text_at) + b"\x09\x04"               # msgbox (std 4)
    script += b"\x44" + u16(STONE) + u16(1) + b"\x6c\x02"            # additem; release; end
    assert BASE + len(script) == text_at
    blob = script + kitty_text
    bored_at = BASE + len(blob)
    blob += bored_text
    end = FREE + len(blob)
    assert end <= FREE_END and set(rom[FREE:end]) == {0xFF}, "target region not free"
    for k in range(0, len(rom), 4):
        v = struct.unpack_from("<I", rom, k)[0]
        assert not BASE <= v < 0x08000000 + end, "%08X already points into the target" % (0x08000000 + k)
    rom[FREE:end] = blob

    rom[o(DOWN_REMOVE):o(DOWN_REMOVE) + 5] = b"\x00" * 5                                 # nop x5: keep the stone
    rom[o(KITTY_CHECK):o(KITTY_CHECK) + 5] = b"\x05" + p32(BASE)                         # goto the new check
    rom[o(BORED[0]) + 2:o(BORED[0]) + 6] = p32(bored_at)
    open(outp, "wb").write(rom)
    print("script %08X, Kitty's line %08X, the 'bored' line %08X, end %08X; removeitem at %08X is nops" % (
        BASE, text_at, bored_at, 0x08000000 + end, DOWN_REMOVE))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
