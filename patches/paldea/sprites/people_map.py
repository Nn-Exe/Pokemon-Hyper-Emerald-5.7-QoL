"""Area Zero's people on the map: Nemona, Arven, Penny, Jacq, AI Sada, AI Turo (approved by the user 2026-10-21:
"everything is great"; the mock-up sheet is gba-trans/hyper-emerald/_testrun/paldea/people).

Each is drawn over one of the game's own walking sprites (main table: Nemona 14, Arven 25, Penny 85, Jacq 96, AI
Sada 202, AI Turo 172), so they match the hack's style. A character is: a base, a recolouring rule (facing, x,
row, base colour -> colour; rows counted in the standing frame: a walking frame is the standing one moved down by
its step's bob), and drawn rows (a grid per facing that replaces rows of the head and body: '.' keeps the recoloured
base pixel, '_' clears it, a hex digit sets it). Heads keep still while walking (they only bob), so the drawn rows
go on every frame; arms and legs come from the base's own walking frames, recoloured by the rule.

Two people share one palette where they stand on one screen together (Mossdeep's ending: Arven, Penny, Nemona and
Jacq beside the hole, by the town's own people; the game draws at most six palettes a screen): A = Arven + Penny,
B = Nemona + Jacq. AI Sada and AI Turo have one each (the Zero Lab has room).
"""
import romgfx as RG

hexc = lambda s: (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))

PAL_A = ['70c0a0', 'f8d0b0', 'f0b088', 'd08868', '784048', 'ece4c4', 'c4b48c', '9c8448',
         'f8d848', '7060c0', '404058', '68a8f0', 'e85058', '808090', 'f8f8f8', '101018']
#         0 bg      1 skin    2 skin    3 skin sh 4 skin ol 5 hair lt 6 hair    7 ochre
#         8 yellow  9 purple  a slate   b blue    c red     d grey    e white   f black
PAL_B = ['70c0a0', 'e8b080', 'c88858', 'a06038', '5c3020', 'c8a8f0', '8058c8', '483078',
         '606070', '30303c', '48c890', 'f88838', 'c04828', 'b8c0d0', 'f8f8f8', '101018']
#         0 bg      1 tan lt  2 tan     3 tan sh  4 dark ol 5 lilac   6 purple  7 purp dk
#         8 hair gr 9 hair bk a green   b orange  c orng dk d lt grey e white   f black

FACING = [0, 1, 2, 0, 0, 1, 1, 2, 2]          # the standing frame each of the nine is a step of


def frames(gid):
    return RG.map_sprite(gid)


def top(px):
    for y, row in enumerate(px):
        if any(row):
            return y


def paint(base, rule, drawn):
    """the nine frames. drawn: {facing: (first row, [rows])}"""
    fr, _ = frames(base)
    out = []
    for k in range(9):
        s = FACING[k]
        px = fr[k]
        dy = top(px) - top(fr[s])                        # the step's bob
        o = [[0] * 16 for _ in range(32)]
        for y in range(32):
            for x in range(16):
                if px[y][x]:
                    o[y][x] = rule(s, x, y - dy, px[y][x])
        if s in drawn:
            y0, rows = drawn[s]
            for r, row in enumerate(rows):
                assert len(row) == 16, (s, r, row)
                y = y0 + r + dy
                for x, ch in enumerate(row):
                    if ch == '.':
                        continue
                    if 0 <= y < 32:
                        o[y][x] = 0 if ch == '_' else int(ch, 16)
        out.append(o)
    return out


# ------------------------------------------------------------------------------------------------ Nemona (m14)
# black hair in a high ponytail tied with green, a green streak by her face; tan skin; white short-sleeved shirt
# with an orange tie; orange shorts; black tights; red shoes
def nemona_rule(s, x, y, c):
    if c in (1, 2, 3, 4) and y < 24:
        return c                                          # face: tan (the palette's 1-4)
    if c in (0xe, 0xf):
        return c
    if y < 24:
        return {0xa: 0xf, 9: 9, 8: 8, 0xd: 0xa, 0xc: 0xa, 0xb: 9}.get(c, c)    # hair black, the tie green
    if c in (1, 2, 3, 4):                                 # skin below the head: arms, or legs in tights
        if s == 0 and y >= 27 and 5 <= x <= 10: return {1: 8, 2: 8, 3: 9, 4: 9}[c]
        if s == 0 and y == 28: return 9
        if s == 0 and y == 26 and x in (5, 10): return 0xd
        if s == 1 and y >= 26 and 5 <= x <= 10: return {1: 8, 2: 8, 3: 9, 4: 9}[c]
        if s == 1 and y == 28: return 9
        if s == 2 and y >= 27 and c in (3, 2): return 9
        return c
    if c == 9:
        return 0xc                                        # shoes
    if c == 0xa:
        return 9                                          # (dark bits of the legs: the tights)
    if y <= 25:                                           # the shirt, the tie down the middle
        if s == 0 and c == 0xc and 6 <= x <= 9: return 0xb
        if s == 0 and c == 0xc: return 0xe
        return {0xb: 0xe, 0xc: 0xe, 0xd: 0xd}.get(c, c)
    if y == 26 and s != 2:
        return {0xd: 0xb, 0xb: 0xb, 0xc: 0xc}.get(c, c)   # the shorts' waist
    return {0xb: 0xb, 0xc: 0xb, 0xd: 0xc}.get(c, c)       # the shorts


NEMONA = (14, nemona_rule, {
    0: (6, [
        '..........ff....',
        '.........f98f...',
        '........f989f...',
        '.......faa9f....',
        '......faaaf.....',
        '.....f99999f....',
        '....ff9999ff....',
        '...f99999999f...',
        '..f9988889999f..',
        '..f9999998899f..',
        '.f999999999999f.',
        '.f999999999999f.',
        '.f9999999999a9f.',
        '.f9991199119a9f.',
        '.f921e9119e129f.',
        '.f932ef11fe239f.',
        '..f9421111249f..',
        '...f42111124f...',
    ]),
    1: (8, [
        '......ffff......',
        '.....f9889f.....',
        '.....faaaaf.....',
        '....f998899f....',
        '...ff998899ff...',
        '..f99f9889f99f..',
        '..f99f9889f99f..',
        '.f999f9889f999f.',
        '.f999f9889f999f.',
        '.f999f9889f999f.',
        '.f9999f99f9999f.',
        '.f9999f99f9999f.',
        '..f999f99f999f..',
        '..f9999ff9999f..',
        '...ff999999ff...',
    ]),
})



# ------------------------------------------------------------------------------------------------ Arven (m25)
# ash-blond wavy hair to the shoulders, the fringe over his right eye; white shirt, long sleeves; yellow vest,
# purple tie, purple trousers, brown boots; the big olive backpack (seen from behind and the side)
def arven_rule(s, x, y, c):
    if c in (0xe, 0xf):
        return c
    if y < 24 and c in (0xb, 0xc, 0xd):
        return {0xb: 6, 0xc: 7, 0xd: 0xf}[c]                  # hair (the side view keeps the base's waves)
    if c in (1, 2, 3, 4):
        if y == 24 and s == 0 and (x <= 4 or x >= 11):
            return {1: 0xe, 2: 0xe, 3: 0xe, 4: 0xd}[c]         # shoulders: the shirt
        if y == 24 and s == 1 and (x <= 4 or x >= 11):
            return {1: 0xe, 2: 0xe, 3: 0xe, 4: 0xd}[c]
        return c
    if y >= 29:
        return {9: 7, 8: 7, 0xa: 0xa}.get(c, c)               # boots
    if s == 0:
        if y <= 26 and (x <= 3 or x >= 12):
            return {8: 0xe, 9: 0xd, 0xa: 0xd}.get(c, c)       # sleeves
        if y <= 26:
            if 7 <= x <= 8: return 9                          # the tie
            return {8: 8, 9: 8, 0xa: 7}.get(c, c)             # the vest
        return {8: 9, 9: 9, 0xa: 9}.get(c, c)                 # trousers
    if s == 1:
        if y <= 26 and (x <= 3 or x >= 12):
            return {8: 0xe, 9: 0xd, 0xa: 0xd}.get(c, c)
        if y <= 26:
            return {8: 8, 9: 8, 0xa: 7}.get(c, c)
        return {8: 9, 9: 9, 0xa: 0xa}.get(c, c)
    if y <= 26:                                               # side: sleeve, vest
        return {8: 0xe, 9: 8, 0xa: 7}.get(c, c)
    return {8: 9, 9: 9, 0xa: 0xa}.get(c, c)


ARVEN = (25, arven_rule, {
    0: (11, [
        '......ffff......',
        '....ff5556ff....',
        '...f65555556f...',
        '..f6555565566f..',
        '..f6556656666f..',
        '.f667666766766f.',
        'f66766676667666f',
        'f67766676677677f',
        'f67766672112776f',
        'f677666317e376f.',
        '.f7767721fe247f.',
        '.f774211112477f.',
        '.f7f42111124f7f.',
        '.f7feef4224feef.',
        '....8ee99ee8....',
        '....f8e99e8f....',
        '..ff7f8888f7ff..',
    ]),
    1: (11, [
        '......ffff......',
        '....ff5556ff....',
        '...f65555556f...',
        '..f6555565566f..',
        '..f6556656666f..',
        '.f667666766766f.',
        'f66766676667666f',
        'f67766676677677f',
        'f67766776677677f',
        'f77677767767767f',
        '.f7f88888888f7f.',
        '.f7f87777778f7f.',
        '...f77777777f...',
        '...f7f6666f7f...',
        '...f7f6556f7f...',
        '...f7ffffff7f...',
        '...ff777777ff...',
    ]),
    2: (19, [
        '................',
        '................',
        '..........6767f.',
        '..........77f88f',
        '..........7f877f',
        '.........f.f777f',
        '.........f.f767f',
        '..........ff777f',
        '...........f777f',
        '...........fffff',
    ]),
})



# ------------------------------------------------------------------------------------------------ Penny (m85)
# a bob, blue on her right and red on her left; round glasses; a dark grey hoodie with a Poke Ball on the chest;
# a grey skirt, dark boots; the Eevee bag on her back
def penny_rule(s, x, y, c):
    if c in (0xe, 0xf):
        return c
    if y < 24 and c in (8, 9, 0xa):
        if s == 2:
            return {8: 0xc, 9: 0xc, 0xa: 4}[c]                # the side shows her left: red
        return {8: 0xb, 9: 0xb, 0xa: 9}[c] if x <= 7 else {8: 0xc, 9: 0xc, 0xa: 4}[c]
    if c in (1, 2, 3, 4) and y < 24:
        return c
    if y >= 29:
        return {4: 0xa, 3: 0xa, 1: 0xa, 2: 0xa}.get(c, c)     # boots
    if c in (1, 2, 3, 4):
        return c                                          # hands
    return {5: 0xd, 6: 0xd, 7: 0xa, 8: 0xd, 9: 0xd, 0xa: 0xa}.get(c, c)     # the hoodie


PENNY = (85, penny_rule, {
    0: (11, [
        '......ffff......',
        '....ffbbccff....',
        '...fbbbbccccf...',
        '..fbbbbbcccccf..',
        '..fbbbbbcccccf..',
        '.fbbbbbbccccccf.',
        '.f9bbbbbccccc4f.',
        'f99bbbb94cccc44f',
        'f9b99b994c44c44f',
        'fb921aa11aa124cf',
        'fb91debddbed14cf',
        '.f931dd11dd134f.',
        '.f9f42111124f4f.',
        '.fadaf4224fadaf.',
        '...fdddccdddf...',
        '...ffddeeddff...',
        '..ffaaddddaaff..',
        '...fadaddadaf...',
    ]),
    1: (11, [
        '......ffff......',
        '....ffccbbff....',
        '...fccccbbbbf...',
        '..fcccccbbbbbf..',
        '..fcccccbbbbbf..',
        '.fccccccbbbbbbf.',
        '.f4cccccbbbbb9f.',
        'f44cccccbbbbb99f',
        'f44cccccbbbbb99f',
        'f44cccc49bbbb99f',
        'f444cc449bb9999f',
        '.f444c4cb9b999f.',
        '.ff4444499999ff.',
        '..f43fddddf34f..',
        '...f33333333f...',
        '...f34333343f...',
        '...f55555555f...',
        '....f555555f....',
    ]),
    2: (19, [
        '...aa...........',
        '..d.aaa.........',
        '..d.............',
    ]),
})



# ------------------------------------------------------------------------------------------------ Jacq (m96)
# messy dark purple hair with a lilac tuft on his left; dark skin; thick round black glasses; an open white lab
# coat over a purple shirt; purple trousers, purple sandals
def jacq_rule(s, x, y, c):
    if c in (0xe, 0xf) and y < 23:
        return c
    if y < 23 and c in (5, 6, 7):
        return {5: 7, 6: 9, 7: 0xf}[c]                        # hair: dark indigo
    if c in (1, 2, 3, 4):
        return {1: 3, 2: 3, 3: 4, 4: 4}[c]                    # skin
    if y >= 29:
        return {0xb: 6, 0xc: 7, 0xd: 7, 7: 7, 0xe: 0xe}.get(c, c)     # sandals
    if s == 0:
        if y == 28:
            return {0xc: 6, 0xd: 7, 0xe: 6, 7: 0xd, 0xb: 6}.get(c, c)   # trousers, the coat's tails at the side
        if 6 <= x <= 9 and y <= 26:
            return {7: 7, 0xd: 6, 0xc: 6, 0xe: 6, 0xb: 6}.get(c, c)    # the shirt
        if y == 27 and 5 <= x <= 10:
            return {7: 7, 0xb: 0xe, 0xd: 6, 0xc: 7}.get(c, c)
        return {0xc: 0xe, 0xd: 0xd, 0xb: 0xe, 7: 0xd, 0xe: 0xe}.get(c, c)   # the coat
    if s == 1:
        if y >= 28:
            return {0xc: 6, 0xd: 7, 0xe: 6, 7: 7, 0xb: 6}.get(c, c)
        return {0xc: 0xe, 0xd: 0xd, 0xb: 0xe, 7: 0xd, 0xe: 0xe}.get(c, c)
    if y >= 28:
        return {0xc: 6, 0xd: 7, 0xe: 6, 7: 7, 0xb: 6}.get(c, c)
    if x <= 5 and y <= 25:
        return {7: 7, 0xd: 6, 0xc: 6, 0xb: 0xe}.get(c, c)        # the shirt at the front
    return {0xc: 0xd, 0xd: 0xe, 0xb: 0xe, 7: 0xd, 0xe: 0xe}.get(c, c)


JACQ = (96, jacq_rule, {
    0: (9, [
        '..........ff....',
        '...f..f..f55f...',
        '..f9ff97f5555f..',
        '.f979f977f5555f.',
        '.f977977797559f.',
        '.f997779777799f.',
        'f99777977797799f',
        '................',
        '................',
        '................',
        '.....ff..ff.....',
        '....fe9ff9ef....',
        '.....ff..ff.....',
    ]),
    1: (9, [
        '....ff..........',
        '...f55f..f..f...',
        '..f5555f79ff9f..',
        '.f5555f779f979f.',
    ]),
    2: (9, [
        '.......ff.......',
        '......f55f......',
        '.....f5555f.....',
        '................',
        '................',
        '................',
        '................',
        '................',
        '................',
        '................',
        '....ff..........',
        '...f..ff........',
        '....ff..........',
    ]),
})



PAL_C = ['70c0a0', 'e8b088', 'c88860', 'a06040', '603028', 'd8c8b0', 'a89880', '706050',
         'e89040', 'b05828', 'f0a8c0', 'c06888', 'c8c8d8', '8c5c38', 'f8f8f8', '101018']
#         0 bg      1 skin lt 2 skin    3 skin sh 4 dark ol 5 hair lt 6 hair    7 hair dk
#         8 orange  9 orng dk a pink    b pink sh c coat sh d leather e white   f black
PAL_D = ['70c0a0', 'f8d0b0', 'e0a888', 'b87858', '704838', 'b8b0a8', '888078', '504840',
         'c8d0e0', '9098b0', '283050', '404878', '9878e8', '202028', 'f8f8f8', '101018']
#         0 bg      1 skin    2 skin    3 skin sh 4 skin ol 5 hair lt 6 hair    7 hair dk
#         8 coat sh 9 coat dk a navy    b navy lt c purple  d boots   e white   f black


# ------------------------------------------------------------------------------------------------ AI Sada (m202)
# long wild ash-brown hair with her orange horn ornaments; tan skin; a long white coat with a pink fur collar;
# the orange tribal top and skirt; leather leg wraps
def sada_rule(s, x, y, c):
    if c in (0xe, 0xf):
        return c
    if y < 23 and c in (5, 6):
        return {5: 6, 6: 7}[c]                                # hair
    if s == 2 and y <= 17 and c in (1, 3):
        return 6                                              # (the base's band round her head, seen from the side)
    if c in (1, 2, 3, 4):
        return {1: 1, 2: 1, 3: 2, 4: 4}[c] if y < 24 else {1: 1, 2: 2, 3: 3, 4: 4}[c]
    if y < 23:
        return {9: 0xf, 0xb: 0xe, 8: 0xa, 0xd: 7, 0xc: 7}.get(c, c)    # (the eyes' pink; grey strands)
    if y <= 24:
        return {8: 0xa, 9: 0xb, 0xd: 0xc, 0xb: 0xe, 0xa: 0xb}.get(c, c)    # the fur collar
    if s == 0 and y <= 27 and (x <= 3 or x >= 12):
        return {8: 0xe, 9: 0xc, 0xa: 0xc, 0xb: 0xe, 0xd: 0xc}.get(c, c)   # the coat's sleeves
    if y >= 30 or (y >= 28 and (x <= 3 or x >= 12)):
        return {0xb: 0xe, 8: 0xe, 9: 0xc, 0xa: 0xc}.get(c, c)   # the coat's tails
    return {8: 8, 9: 9, 0xa: 0xd, 0xb: 0xe, 0xd: 0xc}.get(c, c)  # top, skirt, wraps


SADA = (202, sada_rule, {
    0: (9, [
        '.....f....f.....',
        '....f5f..f5f....',
        '....f65ff56f..f.',
        '..ff5f6556f5ff8f',
        '..f6f665566f689f',
        'ff5f66655666f9ff',
        'f6f5666556665f6f',
        '.f657665566756f.',
        '.f5f76611667f5f.',
        '.65f76111167f56.',
        '................',
        '................',
        '................',
        '................',
        '7faaaf4224faaaf7',
        '7fabafe88efabaf7',
        '...cf899998fc...',
        '...ef211112fe...',
        '...f89898989f...',
    ]),
    1: (9, [
        '.....f....f.....',
        '....f5f..f5f....',
        '..f.f65ff56f....',
        '.f8.............',
        '.f98............',
        '..f9............',
    ]),
    2: (9, [
        '................',
        '................',
        '................',
        '................',
        '.........f8f....',
        '.........f98f...',
    ]),
})


# ------------------------------------------------------------------------------------------------ AI Turo (m172)
# short grey-brown hair combed back, a short beard; a long white coat open over a navy bodysuit with a purple
# line down it; dark boots
def turo_rule(s, x, y, c):
    if c in (0xe, 0xf) and y < 23:
        return c
    if c in (1, 2, 3, 4):
        if y >= 27 and s == 0 and 4 <= x <= 11:
            return 0xa                                        # (the base's hands in front: the bodysuit)
        return c
    if y >= 29 and c in (0xc, 0xd, 6, 7):
        return 0xd                                            # boots
    if s == 0 and 5 <= x <= 10 and y >= 24:
        return {0xe: 0xa, 0xb: 0xb, 0xc: 0xa, 5: 0xc, 6: 0xc, 0xd: 0xa}.get(c, c)   # the bodysuit
    if s == 2 and x <= 5 and 24 <= y <= 28:
        return {0xe: 0xa, 0xb: 0xb, 0xc: 0xa, 0xd: 0xa, 6: 0xc}.get(c, c)
    return {0xe: 0xe, 0xb: 8, 0xc: 9, 0xd: 9, 6: 9, 7: 0xf, 5: 0xc}.get(c, c)   # the coat


TURO = (172, turo_rule, {
    0: (9, [
        '________________',
        '________________',
        '______ffff______',
        '____ff5555ff____',
        '___f55555556f___',
        '__f6555555566f__',
        '__f6556655666f__',
        '__f7665566667f__',
        '__f7611111167f__',
        '__f7111111117f__',
        '__f7771111777f__',
        '__f71e7117e17f__',
        '__f71ef11fe17f__',
        '__f7721111277f__',
        '...f77744777f...',
    ]),
    1: (9, [
        '________________',
        '________________',
        '______ffff______',
        '____ff5555ff____',
        '___f55655556f___',
        '__f6556555566f__',
        '__f6665566667f__',
        '__f7666666667f__',
        '__f7766666677f__',
        '__f7776666777f__',
        '__f7777777777f__',
        '__f7777777777f__',
        '__f4777777774f__',
        '___f42222224f___',
    ]),
    2: (9, [
        '________________',
        '________________',
        '______ffff______',
        '____ff55556ff___',
        '___f555555667f__',
        '__f55555566677f_',
        '__f55556666777f_',
        '__f15566667777f_',
        '__f1156667777f__',
        '_f31117777777f__',
        '_f37711147777f__',
        '_f317e112477f___',
        '_f31fe1112477f__',
        '_f7211112777f___',
        '__f777777f......',
    ]),
})


CHARS = {'nemona': ('Nemona', NEMONA, PAL_B), 'arven': ('Arven', ARVEN, PAL_A), 'penny': ('Penny', PENNY, PAL_A), 'jacq': ('Jacq', JACQ, PAL_B), 'sada': ('AI Sada', SADA, PAL_C), 'turo': ('AI Turo', TURO, PAL_D)}

