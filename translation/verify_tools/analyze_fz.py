import glob, hashlib, re, sys
from PIL import Image
sp = r"C:\Users\nonth\AppData\Local\Temp\claude\c--Users-nonth-Desktop-Works---Productivity-gba-trans\f184de21-699d-4c79-a35b-04f41a1fd6c9\scratchpad"
def fno(f): return int(re.findall(r'f0*(\d+)', f.split('\\')[-1])[0])
fs = sorted(glob.glob(sp + r"\fz_shots\*.png"))
post = [hashlib.md5(Image.open(f).convert('RGB').tobytes()).hexdigest() for f in fs if fno(f) >= 9600]
print("total shots:", len(fs), "| post-9600:", len(post), "| distinct:", len(set(post)))
try: print("last heartbeat:", open(sp + r"\fz_hb.txt").read().split()[-1])
except Exception: print("no heartbeat")
