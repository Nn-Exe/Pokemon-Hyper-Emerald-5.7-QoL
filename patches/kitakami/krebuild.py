"""Makes the Kitakami ROM again from the positions in a folder's placements.txt:
python -I krebuild.py [folder] [--here]   (the folder: gba-trans/hyper-emerald/roms/test-kitakami unless named)

This is what "rebuild.bat" beside the Kitakami test builds runs, and what the placement editor (editor.py) calls when
you press its button (the user, 2026-10-17: "I want to edit placement myself"). As Area Zero's rebuild.py, in the
folder it

  * reads placements.txt (and writes one from the built-in positions if there is none); a file written before
    something came new gets the new lines, with everything of the user's where they put it;
  * builds "Hyper Emerald - Kitakami (my placements N).gba" from the working game (rom/), N one more than the last.
    A new name every time on purpose: an emulator that loads its last save state when a ROM is opened would load
    one made on the older ROM, in which every script has moved, and crash;
  * gives the new ROM a save: a copy of the newest save with a game in it, of the Kitakami builds here or of the
    user's own Area Zero builds ("(my placements N)" in roms/test-paldea), beside the ROM only - never on the
    Desktop (the user, 2026-10-16);
  * says so if a save state is newer than that save (what a state holds never reaches a new ROM unless it is saved
    in the game first);
  * keeps its last two ROMs; the saves of the ones it throws away go to "old saves" in the folder;
  * when the folder has a "(Part 2 start)" save (a game with Part 1 done, at Briar: _testrun/kitakami/
    steps_p2save.lua), also makes "... (my placements N) (Part 2 start).gba", the same ROM, with a copy of the newest
    such save beside it: Part 2's places can be tried at once (the user, 2026-10-17: "I want to adjust placement of
    part2"). That save is never taken for the user's own game (SIDE).

If something in placements.txt would not work in the game it says what (kpeople.layout_report) and builds nothing.
--here: no save is looked for anywhere but in the folder itself (for trying this out).
"""
import glob, os, re, shutil, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "paldea"))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
# what every game in the workspace shares (the standalone mGBA): the folder above this game's own one
# (gba-trans/hyper-emerald/ since 2026-10-20, when gba-trans became one folder per game)
SHARED = os.path.dirname(ROOT)
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
GAME = os.path.join(REPO, "rom", "Pokemon Hyper Emerald v5.7 - Full English Modern.gba")
BEFORE = os.path.join(ROOT, "roms", "before-kitakami", "Hyper Emerald - the game before Kitakami.gba")
FOLDER = os.path.join(ROOT, "roms", "test-kitakami")
AREA_ZERO = os.path.join(ROOT, "roms", "test-paldea")
NAME = "Hyper Emerald - Kitakami (my placements %d)"
MINE = re.compile(r"Hyper Emerald - Kitakami \(my placements (\d+)\)\.gba$")
OURS = re.compile(r"Hyper Emerald - Kitakami \(my placements (\d+)\)\.(?:gba|sav|ss\d)$")
# the saves that can be the user's own game: their builds' ("(my placements N)", Kitakami's and Area Zero's) and the
# Kitakami tests from 5 on (test 4's is a side save of a test's, "before the door opens", made by me)
SAVES = ("Hyper Emerald - Kitakami (my placements *)", "Hyper Emerald - Area Zero (my placements *)",
         "Hyper Emerald - Kitakami test *")
SIDE = re.compile(r"Kitakami test [1-4]\.|\(before the door opens\)|\(Part 2 start\)")   # (side saves of tests)
KEEP = 2
MGBA = os.path.join(SHARED, "tools", "pc_mgba", "mGBA.exe")
P2 = " (Part 2 start)"


def p2_companion(folder, n, rom, say):
    """the "(Part 2 start)" copy of build n with the newest Part 2 start save, if the folder has one -> its path"""
    saves = glob.glob(os.path.join(folder, "Hyper Emerald - Kitakami*" + P2 + ".sav"))
    if not saves:
        return None
    src = max(saves, key=os.path.getmtime)
    crom, csav = (os.path.join(folder, NAME % n + P2 + ext) for ext in (".gba", ".sav"))
    shutil.copyfile(rom, crom)
    if not os.path.exists(csav):
        shutil.copyfile(src, csav)
    say("Also built: \"%s\" - the same ROM with your Part 2 start save (a copy of \"%s\"): Part 1 done, at "
        "Briar." % (os.path.basename(crom), os.path.basename(src)))
    return crom


def has_game(path):
    import rebuild as RB                                   # Area Zero's (patches/paldea)
    return RB.has_game(path)


def save_folders(emulators=True):
    """where a save of the user's may be: here, beside Area Zero's builds, and the folders the mGBAs on this PC keep
    their saves in (read only: nothing is put there)"""
    import rebuild as RB
    out = [FOLDER, AREA_ZERO]
    if emulators:
        out += RB.emulator_folders("savegamePath")
    return [d for d in dict.fromkeys(os.path.abspath(d) for d in out) if os.path.isdir(d)]


def playtime(path):
    """the game's play time in a save (hours, minutes, seconds of its newest copy), or None"""
    import struct
    d = open(path, "rb").read()
    best = None
    for slot in range(2):
        for k in range(14):
            o = slot * 14 * 4096 + k * 4096
            if len(d) >= o + 4096 and struct.unpack_from("<I", d, o + 0xFF8)[0] == 0x08012025 and                     struct.unpack_from("<H", d, o + 0xFF4)[0] == 0:
                cnt = struct.unpack_from("<I", d, o + 0xFFC)[0]
                if best is None or cnt > best[0]:
                    best = (cnt, struct.unpack_from("<HBB", d, o + 0x0E))
    return best[1] if best else None


def newest(folders, ext, test=lambda f: True):
    """the user's newest game: the save with the most play time (then the newest file); never a side save"""
    found = {f for d in folders for pat in SAVES for f in glob.glob(os.path.join(d, pat + ext))
             if test(f) and not SIDE.search(os.path.basename(f))}
    if ext != ".sav":
        return max(found, key=os.path.getmtime) if found else None
    return max(found, key=lambda f: (playtime(f) or (0, 0, 0), os.path.getmtime(f))) if found else None


def when(path):
    return time.strftime("%d %b, %H:%M", time.localtime(os.path.getmtime(path)))


def base_rom():
    """The game Kitakami is built on: rom/ while Kitakami is not in it; once it is (merged), the game before Kitakami
    that the merge keeps in roms/before-kitakami (the chain's stage before kitakami: wilditem since 2026-10-18). Kitakami's space must be empty."""
    import kitakami_patch as KT
    if not os.path.exists(GAME):
        return GAME
    with open(GAME, "rb") as f:
        f.seek(KT.FREE)
        merged = any(f.read(KT.FREE_END - KT.FREE))
    return BEFORE if merged else GAME


def rebuild(folder=FOLDER, say=print, emulators=True):
    """The new ROM's path if one was built, else None. `say` gets every line that is to be read."""
    import io, contextlib
    import kitakami_patch as KT
    import kplaces as KPL
    import rebuild as RB
    folder = os.path.abspath(folder)
    placements = os.path.join(folder, "placements.txt")
    fresh = not os.path.exists(placements)
    base = base_rom()
    if not os.path.exists(base):
        say("The game Kitakami is built on is not where it should be:\n  " + base)
        return None
    fd, tmp = tempfile.mkstemp(suffix=".gba", dir=folder)
    os.close(fd)
    try:
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                KT.build(base, tmp, placements)
        except KPL.PlacementError as e:
            say("placements.txt cannot be read:\n  " + str(e))
            return None
        except KT.Problems as e:
            say("Nothing was built. %d thing%s to put right:" % (len(e.lines), "s" * (len(e.lines) > 1)))
            for line in e.lines:
                say("  - " + line)
            return None
        if fresh:
            say("There was no placements.txt: one was written with everything where it is now.")
        made = sorted(int(MINE.search(f).group(1)) for f in os.listdir(folder) if MINE.search(f))
        seen = [0]
        for d in [folder] + (RB.emulator_folders("savegamePath") + RB.emulator_folders("savestatePath")
                             if emulators else []):
            try:
                seen += [int(OURS.search(f).group(1)) for f in os.listdir(d) if OURS.search(f)]
            except OSError:
                pass
        n = max(seen) + 1
        rom = os.path.join(folder, NAME % n + ".gba")
        os.replace(tmp, rom)
        tmp = None
    finally:
        if tmp and os.path.exists(tmp):
            os.remove(tmp)
    say("Built: " + os.path.basename(rom))
    if not fresh:
        values = KPL.load(placements)
        if values.notes:
            with open(placements, "w", encoding="utf-8", newline="\n") as f:
                f.write(KPL.text(values))
            say("placements.txt was written before some of what this build has; it now has the new lines:")
            for note in values.notes:
                say("  - " + note)
    # its save
    folders = save_folders(emulators) if emulators else [folder]
    src = newest(folders, ".sav", has_game)
    if src:
        dst = os.path.join(folder, NAME % n + ".sav")
        if not os.path.exists(dst):
            shutil.copyfile(src, dst)
        say("Its save is a copy of \"%s\" of %s, beside the ROM (not on the Desktop)." % (os.path.basename(src),
                                                                                       when(src)))
        say("Open the new ROM and choose Continue. If you saved inside Kitakami the screen fades once more right "
            "after that: the game is reading the new positions.")
        if emulators:
            states = [f for d in folders + RB.emulator_folders("savestatePath") for pat in SAVES
                      for f in glob.glob(os.path.join(d, pat + ".ss?"))]
            state = max(states, key=os.path.getmtime) if states else None
            if state and os.path.getmtime(state) > os.path.getmtime(src) + 60:
                say("")
                say("CAREFUL: your newest save state (\"%s\", %s) is newer than that save." % (
                    os.path.basename(state), when(state)))
                say("  What you did after the save is only in the save state, and a save state does not work on a")
                say("  new ROM. To keep it: open the ROM the state belongs to, load the state, save in the game")
                say("  (Start > Save), close it, and build again.")
    else:
        say("No save with a game in it was found to go with it: start it and choose New Game, or put a save beside "
            "it under its name.")
    p2_companion(folder, n, rom, say)
    # the older ROMs of ours (and their Part 2 start copies), and the saves that went with them
    for old in made[:max(0, len(made) + 1 - KEEP)]:
        for tail in ("", P2):
            try:
                os.remove(os.path.join(folder, NAME % old + tail + ".gba"))
            except OSError:
                continue                                     # open in an emulator: left where it is, save and all
            sav = os.path.join(folder, NAME % old + tail + ".sav")
            if os.path.exists(sav):
                keep = os.path.join(folder, "old saves")
                os.makedirs(keep, exist_ok=True)
                dst = os.path.join(keep, NAME % old + tail + ".sav")
                try:
                    if os.path.exists(dst):
                        os.remove(dst)
                    shutil.move(sav, dst)
                except OSError:
                    pass
    return rom


def play(rom):
    """open a built ROM in the standalone mGBA (tools/pc_mgba): it reads the save beside the ROM"""
    import subprocess
    if not os.path.exists(MGBA):
        return False
    subprocess.Popen([MGBA, rom], cwd=os.path.dirname(MGBA), close_fds=True)
    return True


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--here"]
    rom = rebuild(args[0] if args else FOLDER, emulators="--here" not in sys.argv)
    sys.exit(0 if rom else 1)
