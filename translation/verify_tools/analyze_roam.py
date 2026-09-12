import glob, hashlib, re
from PIL import Image
sp = r"C:\Users\nonth\AppData\Local\Temp\claude\c--Users-nonth-Desktop-Works---Productivity-gba-trans\f184de21-699d-4c79-a35b-04f41a1fd6c9\scratchpad"
def fno(f): return int(re.findall(r'f0*(\d+)', f.split('\\')[-1])[0])
fs = sorted(glob.glob(sp + r"\shots_roam\*.png"), key=fno)
hashes = [(fno(f), hashlib.md5(Image.open(f).convert('RGB').tobytes()).hexdigest()) for f in fs]
# longest consecutive-identical run = freeze indicator
maxrun = 1; cur = 1; runstart = hashes[0][0]; beststart = None
for i in range(1, len(hashes)):
    if hashes[i][1] == hashes[i-1][1]:
        cur += 1
        if cur > maxrun: maxrun = cur; beststart = runstart
    else:
        cur = 1; runstart = hashes[i][0]
print("roam shots:", len(fs), "frame range", hashes[0][0], "-", hashes[-1][0])
print(f"longest identical run: {maxrun} shots ({maxrun*60} frames) starting near frame {beststart}")
print("distinct screens overall:", len(set(h for _,h in hashes)), "of", len(hashes))
# if longest run is short (<8 shots = <480 frames), no freeze
print("VERDICT:", "NO FREEZE (interactive throughout)" if maxrun < 8 else f"POSSIBLE FREEZE at frame {beststart}")
