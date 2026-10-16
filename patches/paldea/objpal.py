"""Objects' palettes given back (test 19): patches/objpal for the Area Zero test build.

The user, with a screenshot of Walking Wake on the channel above the waterfall in washed-out colours: "sometimes
the static legen such as walking wake, koraidon, etc.. will have inveted visual graphical glitch". The hack's
allocator gives the seventh kind of thing on a map slot 10, which does not keep its colours; the crater after the
story has more kinds than six. patches/objpal/objpal_patch.py has the whole story and the code (objpal.s); it went
into the working ROM on 2026-10-10. The Gen 9 test build this is built on was made before that, so the allocator
goes into this build's second blob here, the same code; on a base that has it already, nothing is done.
"""
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "objpal"))
import objpal_patch as OPM

ALLOC = OPM.ALLOC


def install(rom, blob):
    """The allocator in `blob` (unless the ROM has it); -> apply(rom), which points the hack's at it."""
    have = OPM.applied(rom)
    if have:
        return lambda rom: {"at": have, "size": 0, "already": True}
    OPM.check_site(rom)
    base = blob.base + len(blob.data) + (-len(blob.data)) % 4
    code = OPM.assemble(base)
    at = blob.put(("objpal", "alloc"), code, 4)
    assert at == base

    def apply(rom):
        OPM.point(rom, at)
        assert OPM.applied(rom) == at
        return {"at": at, "size": len(code), "already": False}
    return apply
