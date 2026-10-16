"""Run mGBA Lua test jobs in parallel (the Mac's way of running the tests the Windows PC runs from PowerShell).

    MGBA_HEADLESS=<mgba-headless> python runner.py jobs.json outdir [workers]

jobs.json: [{name, rom, sav (or null), lua, env, timeout, patch?, after_sav_of?}] (gen_jobs.py writes it). Each job
gets its own folder with copies of the ROM and the save; the test's Windows path to test_boot.lua is replaced by this
checkout's. `patch` = [[file offset, hex]] written into that copy only (test_wild.lua's slot is forced this way: the
headless mGBA built on the Mac does not call Lua breakpoints, which the Windows build does). Results:
outdir/results.json {name: {status, secs, log}}; jobs that need another's save (after_sav_of) run last."""
import json, os, shutil, subprocess, sys, time, glob, concurrent.futures as cf
MGBA = os.environ.get("MGBA_HEADLESS", "mgba-headless")
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BOOT = REPO + "/patches/dexnavchain/test_boot.lua"
WINBOOT = ["C:/Users/nonth/Desktop/Works & Productivity/gba-trans/hyper-emerald-en-qol/patches/dexnavchain/test_boot.lua"]


def one(job, out):
    d = os.path.join(os.path.abspath(out), job["name"]) + "/"
    shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    shutil.copy(job["rom"], d + "game.gba")
    if job.get("patch"):                         # test-only bytes in this run's copy of the ROM
        with open(d + "game.gba", "r+b") as f:
            for off, hx in job["patch"]:
                f.seek(off); f.write(bytes.fromhex(hx))
    sav = job.get("sav")
    if job.get("after_sav_of"):
        sav = os.path.join(out, job["after_sav_of"], "game.sav")
    if sav:
        shutil.copy(sav, d + "game.sav")
    src = open(job["lua"], encoding="utf-8").read()
    for w in WINBOOT:
        src = src.replace(w, BOOT)
    src = src.replace('dofile((HERE or DIR or "./") .. "../dexnavchain/test_boot.lua")', 'dofile("%s")' % BOOT)
    src = src.replace('dofile(DIR .. "../dexnavchain/test_boot.lua")', 'dofile("%s")' % BOOT)
    open(d + "t.lua", "w", encoding="utf-8").write(src)
    open(d + "run.lua", "w").write('DIR = "%s"; HERE = "%s"; dofile(DIR .. "t.lua")\n' % (d, d))
    env = dict(os.environ, GEN9_DIR=d, GEN9_BOOT=BOOT, **{k: str(v) for k, v in job.get("env", {}).items()})
    t0 = time.time()
    with open(d + "stdout.txt", "w") as so:
        p = subprocess.Popen([MGBA, "-l", "1", "--script", d + "run.lua", d + "game.gba"], cwd=d, env=env,
                             stdout=so, stderr=subprocess.STDOUT)
        status = "timeout"
        while time.time() - t0 < job.get("timeout", 300):
            if glob.glob(d + "*_done.txt"):
                status = "done"; time.sleep(0.5); break
            if p.poll() is not None:
                status = "exited %s" % p.returncode; break
            time.sleep(0.5)
        if p.poll() is None:
            p.kill(); p.wait()
    logs = "".join(open(f, encoding="utf-8", errors="replace").read() for f in sorted(glob.glob(d + "*_log.txt")))
    return job["name"], {"status": status, "secs": round(time.time() - t0), "log": logs}


def main(jobs_p, out, workers=10):
    jobs = json.load(open(jobs_p))
    os.makedirs(out, exist_ok=True)
    res_p = os.path.join(out, "results.json")
    res = json.load(open(res_p)) if os.path.exists(res_p) else {}
    first = [j for j in jobs if not j.get("after_sav_of")]
    later = [j for j in jobs if j.get("after_sav_of")]
    for batch in (first, later):
        with cf.ThreadPoolExecutor(int(workers)) as ex:
            for name, r in ex.map(lambda j: one(j, out), batch):
                res[name] = r
                print("%-40s %-10s %4ds" % (name, r["status"], r["secs"]), flush=True)
                json.dump(res, open(res_p, "w"), indent=1)


if __name__ == "__main__":
    main(*sys.argv[1:])
