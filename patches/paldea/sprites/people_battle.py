"""Area Zero's people in battle: Nemona, AI Sada and AI Turo (approved by the user 2026-10-21), each one of the
game's own trainer pictures repainted (colours by region) and partly drawn over (hair, horns, a tie, a beard: rows
of hex digits). Bases: Nemona over picture 114, AI Sada over 100, AI Turo over 187. Arven, Penny and Jacq do not
battle.
"""
import romgfx as RG

hexc = lambda s: (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


def put(out, x0, y0, rows):
    """rows of hex digits from (x0, y0); '.' leaves a pixel alone, '_' clears it"""
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch == '.':
                continue
            x, y = x0 + dx, y0 + dy
            if 0 <= x < 64 and 0 <= y < 64:
                out[y][x] = 0 if ch == '_' else int(ch, 16)


def remap(out, src, box, m):
    x0, y0, x1, y1 = box
    for y in range(y0, y1):
        for x in range(x0, x1):
            if src[y][x] in m:
                out[y][x] = m[src[y][x]]


# ------------------------------------------------------------------------------------------------ Nemona (t114)
NEMONA_PAL = ['60c888', '5c3020', 'e04838', 'b84020', 'f8f8f8', '48c890', '000000', '383840',
              'e8b080', 'a06040', 'c88858', '3c6870', '18181c', 'f0f4f8', 'c8d0e0', 'f88830']
#              0 bg      1 skin ol 2 red     3 orng dk 4 white   5 green   6 black   7 hair
#              8 tan lt  9 tan sh  a tan     b hair hl c hair dk d shirt   e shirt sh f orange


def nemona():
    px, _ = RG.trainer_pic(114)
    out = [row[:] for row in px]
    remap(out, px, (0, 0, 64, 64), {5: 0xe})                  # the grey goes: its slot is her green now
    remap(out, px, (8, 10, 23, 21), {5: 0xe})                 # the Poke Ball
    remap(out, px, (14, 28, 29, 41), {2: 7, 4: 0xe, 5: 0xc, 3: 0xc, 0xe: 7, 0xd: 0xe})   # the bag: dark
    remap(out, px, (0, 40, 64, 56), {8: 7, 0xa: 7, 9: 0xc, 1: 6})                     # black tights
    remap(out, px, (20, 36, 45, 42), {0xb: 3})                # the shorts' shade
    remap(out, px, (37, 8, 41, 13), {1: 0xc})                 # (the hat's band, in her hair)
    out[9][24] = 0xc
    # her hair instead of the beanie, and the high ponytail rising behind it (x 24-49)
    put(out, 24, 0, [
        '_________________6666_____',
        '________________6c7b76____',
        '_____66666666__6c77b76____',
        '___6677b777777bb6c77b76___',
        '_667777b777777bc66c77b76__',
        '67c77b7777777c77c6c77b76__',
        '6c7b77777777c7c7c6c7b776__',
        '6cc7b777777c77c7c6c7b776__',
        '.............ccc.6c77b76__',
        '.................6c7b76___',
        '.................6c77b6___',
        '..................6c7b6___',
        '..................6c7b6___',
        '..................6c776___',
        '...................6c76___',
        '...................6c6____',
        '....................6_____',
    ])
    # a green streak in the fringe
    for x, y in ((27, 9), (26, 10), (26, 11), (25, 12)):
        out[y][x] = 5
    # the collar's points, the orange tie down to the waist (the bag's strap stays over it)
    put(out, 30, 22, ['dffd'])
    for y in range(23, 31):
        for x, c in ((31, 0xf), (32, 3)):
            if px[y][x] != 0xc:
                out[y][x] = c
    put(out, 30, 30, ['ff33', '.f3.'])
    return out, [hexc(c) for c in NEMONA_PAL]



# ------------------------------------------------------------------------------------------------ AI Sada (t100)
SADA_PAL = ['60c888', 'a89880', '6c5c4c', '000000', 'a06040', '603028', '9098a8', 'd0d4dc',
            'f8f8f8', 'e88838', 'c88860', 'b05028', 'f8f8f8', 'e8b088', 'f0a0b8', 'd8ccb4']
#            0 bg      1 hair    2 hair dk 3 black   4 tan sh  5 leather 6 coat dk 7 coat sh
#            8 coat    9 orange  a tan     b orng dk c white   d tan lt  e pink    f hair lt


def sada():
    px, _ = RG.trainer_pic(100)
    out = [row[:] for row in px]
    remap(out, px, (18, 0, 46, 22), {6: 0xf, 0xf: 0xf})             # the hair's grey strands: light ash
    remap(out, px, (0, 22, 64, 64), {2: 9, 1: 0xb})                 # her top and skirt: orange
    remap(out, px, (0, 41, 64, 64), {7: 5, 8: 4, 6: 5, 0xe: 5, 0xf: 4, 9: 5})      # leather wraps on her legs
    remap(out, px, (0, 46, 64, 64), {1: 4, 2: 5, 0xf: 0xa})         # (the boot and its laces too)
    remap(out, px, (10, 14, 31, 25), {7: 0xe, 8: 0xe})              # the coat's collar: pink fur
    # her horn ornaments, on her left
    put(out, 40, 3, [
        '...33...',
        '..3993..',
        '..39b3..',
        '.39b3...',
        '39b3....',
    ])
    put(out, 41, 9, [
        '..333',
        '.399c3',
        '39bb3.',
        '333...',
    ])
    return out, [hexc(c) for c in SADA_PAL]


# ------------------------------------------------------------------------------------------------ AI Turo (t187)
TURO_PAL = ['509858', '9098b0', 'c8d0e0', '303858', '000000', 'd8a078', 'f8d0b8', '283050',
            'b87860', 'e8c080', 'f8f8f8', '504840', '888078', 'b8b0a8', '9878e8', '404878']
#            0 bg      1 coat sh 2 coat lt 3 navy dk 4 black   5 skin    6 skin lt 7 navy
#            8 skin sh 9 skin hl a white   b hair dk c hair    d hair lt e purple  f navy lt


def turo():
    px, _ = RG.trainer_pic(187)
    out = [row[:] for row in px]
    remap(out, px, (19, 20, 44, 31), {0xb: 3, 0xc: 7, 0xd: 0xf})     # the vest: the navy bodysuit
    remap(out, px, (19, 0, 44, 21), {1: 0xc, 2: 0xd, 3: 0xb})        # what is left of the hair: his colours
    remap(out, px, (15, 22, 26, 49), {3: 1})                        # the coat's pocket marks: shade, not navy
    remap(out, px, (35, 22, 46, 49), {3: 1})
    # the head: hair short and combed back, the ear, a short beard along the jaw (the face is the base's)
    put(out, 20, 4, [
        '_______________________',
        '______4444444__________',
        '____44ddddddcc44_______',
        '___4dddcddddcccc4______',
        '__4ddcddddcccccbc4_____',
        '__4dcdddcccccbcbcb4____',
        '__4cddccccbcbcbcbb4____',
        '__4cccccbcbbcbbbbb4____',
        '__4c.........5bcbbb4___',
        '__4b..........bcbb4____',
        '___4..........85bb4____',
        '___4..........865b4____',
        '____..........85bb4____',
        '____4.........4bb4_____',
        '____4b......5bb4_______',
        '_____4bc....cbb4_______',
        '______4bcbbcb4_________',
    ])
    # the purple line down the bodysuit
    for y in range(34, 48):
        if out[y][29] == 7:
            out[y][29] = 0xe
    return out, [hexc(c) for c in TURO_PAL]


PICS = {'nemona': ('Nemona', 114, nemona), 'sada': ('AI Sada', 100, sada), 'turo': ('AI Turo', 187, turo)}


