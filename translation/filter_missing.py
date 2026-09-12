import json, collections, sys
sys.stdout.reconfigure(encoding='utf-8')
sp = r"C:\Users\nonth\AppData\Local\Temp\claude\c--Users-nonth-Desktop-Works---Productivity-gba-trans\f184de21-699d-4c79-a35b-04f41a1fd6c9\scratchpad"
missing = json.load(open(sp + r"\lp_missing.json", encoding='utf-8'))

PART = set('的了是我你他她它们在有不就吗呢啊吧和与被给到要会能可这那什么没很才请谢对进出来去说想看知道让为着从但如果因所以还也都把等就已经再最好多少大小新旧前后上下里外中间东西南北左右开关门路山水火电风雨日月年天时分秒些个只条张片块传到区技术发现并没有力量希望世界')
PUNCT = set('。,!?、:…')
def lvl1(t):
    c1=tot=0
    for c in t:
        if '一'<=c<='鿿':
            tot+=1
            try:
                if 0xB0<=c.encode('gb2312')[0]<=0xD7: c1+=1
            except Exception: pass
    return (c1/tot if tot else 0), tot
def good(t):
    r,tot=lvl1(t)
    if tot<3: return False
    hz=[c for c in t if '一'<=c<='鿿']
    fr=collections.Counter(hz)
    if fr.most_common(1)[0][1]/len(hz)>0.30 and len(hz)>6: return False  # repetition = garbage
    has_p=any(c in PART for c in hz) or any(c in PUNCT for c in t)
    if not has_p: return False
    if r<0.80: return False  # mostly level-1 = real text
    return True

real = {a: t for a, t in missing.items() if good(t)}
print("missing total:", len(missing), "| REAL dialogue:", len(real))
hz = sum(sum(1 for c in t if '一'<=c<='鿿') for t in real.values())
print("real Chinese chars to translate:", hz)

# check for the user's Galar string
print("\n=== searching for Galar/Shadow-Clone string ===")
for a, t in missing.items():
    if any(k in t for k in ("伽勒尔","影分身","并没有传到","传到伽")):
        print(f"  FOUND {a} (real={good(t)}): {t[:70]}")

json.dump(real, open(sp + r"\lp_real_missing.json", 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print("\nsample real missing:")
for a, t in list(real.items())[:15]:
    print(f"  {a}: {t[:60]}")
