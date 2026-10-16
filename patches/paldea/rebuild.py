"""Makes the Area Zero ROM again from the positions in a folder's placements.txt:
python -I rebuild.py [folder] [--here]   (the folder: gba-trans/roms/test-paldea unless named)

This is what "rebuild.bat" beside the test builds runs, and what the placement editor (editor.py) calls when you
press its button. In the folder it

  * reads placements.txt (and writes one from the built-in positions if there is none) and, if there is one,
    ground.txt (the tiles painted with the editor). A placements.txt from before something came new or moved
    (places.py: MOVED, GIVEN_UP) is written afresh with the same positions and the new lines, and the file as
    it was is kept beside it;
  * builds "Hyper Emerald - Area Zero (my placements N).gba" from the Gen 9 test build, N one more than the last,
    and since 2026-10-15 puts the whole of Gen 9 on it with the steps the chain ends with (gen9rest, gen9dex,
    gen9egg, gen9journal: the user, "patch to my current rom, including every fix and whole gen9").
    A new name every time on purpose: an emulator that loads its last save state when a ROM is opened would load
    one made on the older ROM, in which every script has moved, and crash. A new name has no save state; and the
    older ROM can still be open in the emulator while this runs;
  * gives the new ROM a save: a copy of the newest save with a game in it of the user's own builds ("(my
    placements N)"; else of any Area Zero build, never a second save "(before the door opens)"), beside the ROM
    and in every folder an installed mGBA keeps its saves in (its config's savegamePath). The user's own emulator
    keeps them on the Desktop, and makes an empty one there for every ROM it opens: those are passed over;
  * says so if a save state is newer than that save: the user plays from save states, and what a state holds
    never reaches a new ROM unless it is saved in the game first;
  * draws the map guide again, from the new ROM;
  * keeps its last two ROMs; the saves of the ones it throws away go to "old saves" in the folder.

If something in placements.txt would not work in the game it says what (check.py) and changes nothing.
--here: no save is looked for or put anywhere but in the folder itself (for trying this out).
"""
import glob, os, re, shutil, struct, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
BASE_ROM = os.path.join(ROOT, "roms", "test-gen9", "Hyper Emerald - Gen 9 test.gba")
FOLDER = os.path.join(ROOT, "roms", "test-paldea")
NAME = "Hyper Emerald - Area Zero (my placements %d)"
MINE = re.compile(r"Hyper Emerald - Area Zero \(my placements (\d+)\)\.gba$")
OURS = re.compile(r"Hyper Emerald - Area Zero \(my placements (\d+)\)\.(?:gba|sav|ss\d)$")
ANY = "Hyper Emerald - Area Zero*"
KEEP = 2
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
CREST = os.path.join(ROOT, "pokemon crest", "Crest_v1.0.F.gba")      # gen9rest's donor, as gen9's
TAIL = [("gen9rest", [CREST]), ("gen9dex", []), ("gen9egg", []), ("gen9journal", [])]


def whole_gen9(path, say):
    """The steps after paldea (_testrun/full/rebuild_chain.py's tail), on `path` in place. False if one fails."""
    import subprocess
    if not os.path.exists(CREST):
        say("Nothing was built: the whole of Gen 9 needs the Crest ROM, and it is not here:\n  " + CREST)
        return False
    cur = path
    for name, more in TAIL:
        nxt = "%s.%s.gba" % (path, name)
        r = subprocess.run([sys.executable, "-I", os.path.join(REPO, "patches", name, name + "_patch.py"), cur, nxt]
                           + more, cwd=REPO, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        if cur != path:
            os.remove(cur)
        if r.returncode != 0 or not os.path.exists(nxt):
            say("Nothing was built: the step %s failed.\n%s" % (name, (r.stdout + r.stderr)[-1500:]))
            if os.path.exists(nxt):
                os.remove(nxt)
            return False
        cur = nxt
    os.replace(cur, path)
    return True


def emulator_folders(key):
    """Where the mGBAs on this PC keep their saves ("savegamePath") or save states ("savestatePath"), when that
    is not next to the ROM."""
    out = []
    appdata = os.environ.get("APPDATA", "")
    for cfg in (os.path.join(appdata, "emudeck", "Emulators", "mgba", "config.ini"),
                os.path.join(appdata, "mGBA", "config.ini"), os.path.join(ROOT, "tools", "pc_mgba", "config.ini")):
        try:
            for line in open(cfg, encoding="utf-8", errors="replace"):
                if line.startswith(key + "="):
                    d = line.split("=", 1)[1].strip()
                    if d and os.path.isdir(d) and os.path.abspath(d) not in out:
                        out.append(os.path.abspath(d))
        except OSError:
            pass
    return out


def has_game(path):
    """Is there a saved game in this .sav? (An emulator makes the file, all 0xFF, as soon as a ROM is opened.)"""
    try:
        d = open(path, "rb").read()
    except OSError:
        return False
    for slot in range(2):
        if all(len(d) >= o + 0x1000 and struct.unpack_from("<I", d, o + 0xFF8)[0] == 0x08012025
               for o in range(slot * 14 * 4096, (slot + 1) * 14 * 4096, 4096)):
            return True
    return False


SIDE = "(before the door opens)"                 # the second saves beside the test builds: a game made for a test,
                                                 # not the user's own


def newest(folders, ext, test=lambda f: True):
    """The newest file of that kind: of the user's own builds ("(my placements N)") if there is one, else of any
    Area Zero build, never of a second save. (Test 15's first rebuild took the newest save of all, the copy of the
    second save that test 14 had put on the Desktop, and gave the user's new ROM a game that was not theirs.)"""
    found = [f for d in folders for f in glob.glob(os.path.join(d, ANY + ext))
             if test(f) and SIDE not in os.path.basename(f)]
    mine = [f for f in found if OURS.search(os.path.basename(f))]
    found = mine or found
    return max(found, key=os.path.getmtime) if found else None


def when(path):
    return time.strftime("%d %b, %H:%M", time.localtime(os.path.getmtime(path)))


def rebuild(folder=FOLDER, say=print, guide=True, emulators=True):
    """True if a ROM was built. `say` gets every line that is to be read. emulators=False: no save is looked for
    or put anywhere but in the folder itself (for trying this out)."""
    import paldea_patch as P
    import places as PL
    import ground as GR
    import check as CK
    import tiles as TL
    folder = os.path.abspath(folder)
    placements = os.path.join(folder, "placements.txt")
    ground = os.path.join(folder, GR.NAME)       # (only there once something has been painted)
    taken = os.path.join(folder, TL.NAME)        # (only there once tiles were taken from another map)
    fresh = not os.path.exists(placements)
    if not os.path.exists(BASE_ROM):
        say("The Gen 9 test build is not where it should be:\n  " + BASE_ROM)
        return False
    others = emulator_folders("savegamePath") if emulators else []
    states = emulator_folders("savestatePath") if emulators else []
    fd, tmp = tempfile.mkstemp(suffix=".gba", dir=folder)
    os.close(fd)
    try:
        try:
            import io, contextlib
            with contextlib.redirect_stdout(io.StringIO()):
                P.build(BASE_ROM, tmp, placements, None, ground, taken)
        except (PL.PlacementError, GR.GroundError) as e:
            say("A file cannot be read:\n  " + str(e))
            return False
        except TL.TilesError as e:
            say("Nothing was built. The tiles taken from other maps (%s) do not work out:" % TL.NAME)
            for line in e.lines:
                say("  - " + line)
            return False
        except CK.Problems as e:
            say("Nothing was built. %d thing%s to put right:" % (len(e.lines), "s" * (len(e.lines) > 1)))
            for line in e.lines:
                say("  - " + line)
            return False
        if not whole_gen9(tmp, say):
            return False
        if fresh:
            say("There was no placements.txt: one was written with everything where it is now.")
        made = sorted(int(MINE.search(f).group(1)) for f in os.listdir(folder) if MINE.search(f))
        # the next number: past every ROM of ours here, and past every save or save state of that name anywhere
        # (one left behind by a ROM since deleted would be taken for the new ROM's)
        seen = [0]
        for d in [folder] + others + states:
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
    # a placements.txt from before this build's new things: the same positions, written afresh with the new lines
    if not fresh:
        values = PL.load(placements)
        if values.notes:
            kept = os.path.join(folder, "placements - as it was before build %d.txt" % n)
            shutil.copyfile(placements, kept)
            with open(placements, "w", encoding="utf-8", newline="\n") as f:
                f.write(PL.text(values))
            say("")
            say("placements.txt was written before some of what this build has. It now has the new lines, with")
            say("everything of yours where you put it (the file as it was: \"%s\"):" % os.path.basename(kept))
            for note in values.notes:
                say("  - " + note)
            say("")
    # its save
    src = newest([folder] + others, ".sav", has_game)
    if src:
        for d in [folder] + others:
            dst = os.path.join(d, NAME % n + ".sav")
            if not os.path.exists(dst):
                shutil.copyfile(src, dst)
        say("Its save is a copy of \"%s\" of %s%s." % (
            os.path.basename(src), when(src),
            " (also put in " + ", ".join(others) + ", where your emulator keeps its saves)" if others else ""))
        say("Open the new ROM and choose Continue. If you saved inside Area Zero the screen fades once more right "
            "after that: the game is reading the new positions.")
        state = newest([folder] + states, ".ss?")
        if state and os.path.getmtime(state) > os.path.getmtime(src) + 60:
            say("")
            say("CAREFUL: your newest save state (\"%s\", %s) is newer than that save." % (
                os.path.basename(state), when(state)))
            say("  What you did after the save is only in the save state, and a save state does not work on a new")
            say("  ROM. To keep it: open the ROM the state belongs to, load the state, save in the game")
            say("  (Start > Save), close it, and run this again.")
    else:
        say("No Area Zero save with a game in it was found to go with it.")
    if guide:
        import map_guide as MG
        MG.main(rom, os.path.join(folder, "map guide"), placements)
        say("The pictures in \"map guide\" are drawn again.")
    # the older ROMs of ours, and the saves that went with them
    for old in made[:max(0, len(made) + 1 - KEEP)]:
        try:
            os.remove(os.path.join(folder, NAME % old + ".gba"))
        except OSError:
            continue                                         # open in an emulator: left where it is, save and all
        for k, d in enumerate([folder] + others):
            sav = os.path.join(d, NAME % old + ".sav")
            if os.path.exists(sav):
                keep = os.path.join(folder, "old saves")
                os.makedirs(keep, exist_ok=True)
                dst = os.path.join(keep, NAME % old + (".sav" if k == 0 else " (from %s).sav" % os.path.basename(d)))
                try:
                    if os.path.exists(dst):
                        os.remove(dst)
                    shutil.move(sav, dst)
                except OSError:
                    pass
    return True


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--here"]
    ok = rebuild(args[0] if args else FOLDER, emulators="--here" not in sys.argv)
    sys.exit(0 if ok else 1)
