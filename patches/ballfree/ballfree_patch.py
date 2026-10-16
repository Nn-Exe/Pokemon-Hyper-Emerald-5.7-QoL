"""The hack's own Poke Balls are let go of like the game's twelve (Hyper Emerald v5.7). Apply anywhere before zhtext.
usage: python ballfree_patch.py <in.gba> <out.gba>

Found behind a report about the gold healthbox (2026-10-13: "more than that especially when heal in battle").
A bug of the original hack. It has 27 kinds of ball (ids 0-26; its tables hold 32 entries: sheets 0x09F097E4,
palettes 0x09F096E4, the opening sparkle's sheets 0x09F092E4 and palettes 0x09F091E4), but the two places where
the game lets a ball's graphics go after its animation still count to twelve:
  * HandleBallAnimEnd (0x08075FD4), when no battler has a ball in the air: FreeBallGfx(0..11)   - 0x080760DA
  * DestroyBallOpenAnimationParticle (0x08172944), when the last sparkle is gone: sheets and palettes 0..11
                                                                                                - 0x081729C6
So a Pokemon sent out of one of the hack's own balls (ids 12-26: tags 0xF100-0xF10E, sparkles 0xF120-0xF12E) left
that ball's 12 tiles and palette, and its sparkle's tiles and palette, loaded until the battle ended: two of the
sixteen sprite palette slots a battler. In a double battle with both of your Pokemon in such balls, four slots were
gone for good and move animations had two left (with our type badges). A heal or drain animation loads four
(Recover, Aqua Ring, Drain Punch, Horn Leech, Life Dew, Heal Order ...): it went without, or - since goldbox - took
the type badges' and the gold healthbox's slots, and the gold box turned plain while it ran.

Both counts go to 26 (two bytes: cmp r4, #11 and cmp r6, #11 become #26). FreeBallGfx frees by tag and does
nothing for a ball that is not loaded; LoadBallGfx and LoadBallParticleGfx load sheet and palette again whenever
the sheet's tag is not loaded, which is how the game's own twelve have always worked. The check before the second
loop ("is any sparkle task still running?", 0x08172998) needs no change: every one of the hack's balls uses the
first ball's sparkle task (0x08171E51, entry 0 of the task table 0x09F08E44).
"""
import struct, sys

SITES = (
    # address, bytes there, bytes after: the loop's test
    (0x080760DA, "0b2c", "1a2c", "HandleBallAnimEnd: cmp r4, #11 after adds r4, #1 (FreeBallGfx for every ball)"),
    (0x081729C6, "0b2e", "1a2e", "DestroyBallOpenAnimationParticle: cmp r6, #11 after adds r6, #1"),
)
LAST_BALL = 26
BALL_SHEETS, BALL_PALS = 0x09F097E4, 0x09F096E4
PART_SHEETS, PART_PALS = 0x09F092E4, 0x09F091E4
TASKS = 0x09F08E44                              # the sparkle task of each ball


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    o = lambda a: a - 0x08000000
    u16 = lambda a: struct.unpack_from("<H", rom, o(a))[0]
    u32 = lambda a: struct.unpack_from("<I", rom, o(a))[0]
    at = lambda a, hexs: bytes(rom[o(a):o(a) + len(bytes.fromhex(hexs))]) == bytes.fromhex(hexs)

    # the two loops, as the hack's own ROM has them
    assert at(0x080760CE, "00242006000e00f008fd0134"), "HandleBallAnimEnd's loop is not as expected"   # movs r4, #0; lsls; lsrs; bl FreeBallGfx; adds r4, #1
    assert at(0x080760DC, "f8dd"), "HandleBallAnimEnd's loop does not branch back"                     # ble
    assert at(0x081729B4, "e88895f6d7fda08895f646ff083508340136"), "the sparkle loop is not as expected"
    assert at(0x081729C8, "f4dd"), "the sparkle loop does not branch back"
    assert u32(0x081729D4) == PART_SHEETS and u32(0x081729D8) == PART_PALS, "the sparkle tables moved"
    assert u32(0x08076B0C) == BALL_SHEETS and u32(0x08076B10) == BALL_PALS, "FreeBallGfx's tables moved"
    assert u32(0x08172990) == TASKS, "the sparkle task table moved"
    # the tables: 32 entries each, one tag for a sheet and its palette, the hack's balls at 12-26
    assert BALL_SHEETS - BALL_PALS == 0x100 and PART_SHEETS - PART_PALS == 0x100
    for k in range(LAST_BALL + 1):
        want = 0xD6D8 + k if k < 12 else 0xF100 + k - 12
        assert u16(BALL_SHEETS + 8 * k + 6) == want and u16(BALL_PALS + 8 * k + 4) == want, "ball %d's tags" % k
        want = 0xD6EC + k if k < 12 else 0xF120 + k - 12
        assert u16(PART_SHEETS + 8 * k + 6) == want and u16(PART_PALS + 8 * k + 4) == want, "ball %d's sparkle tags" % k
    # every ball from 12 on uses the first ball's sparkle task, which the check before the loop already looks at
    assert all(u32(TASKS + 4 * k) == u32(TASKS) for k in range(12, LAST_BALL + 1)), "a ball has a sparkle task of its own"

    for addr, was, now, what in SITES:
        assert at(addr, was), "%08X is not %s (already applied?): %s" % (addr, was, what)
        rom[o(addr):o(addr) + 2] = bytes.fromhex(now)
    open(outp, "wb").write(rom)
    print("ballfree: the two loops that free a ball's graphics count to %d (0x080760DA, 0x081729C6)" % LAST_BALL)


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
