"""Area Zero: an optional Paldea area after Team Rainbow Rocket, for the Gen 9 build (Hyper Emerald v5.7).
usage: python -I paldea_patch.py <in.gba> <out.gba> [placements.txt [ground.txt [tiles.txt]]]
       (in: a build with speciesx and gen9; this patch goes last. The third argument is the file that says
       where everything stands; without it, places.py's own positions. The fourth is the ground where the user
       has painted it: ground.py. The fifth names the tiles taken from other maps for the craters: tiles.py.)

The story is the one the user approved (revision 2; story.py says it in full). Built (2026-10-08):

  * Mossdeep City (0/6), on the strip of grass by the sea below the Space Center (the user, test 16: "change the
    entry of blackhole and Jacq to Mossdeep city instead at where I stand"; up to test 15 it was the Timeless
    Woods, 34/67): Jacq, a teacher from Paldea's academy, and a black hole, shown by our map scripts once Team
    Rainbow Rocket is beaten (0x41D5). The ending plays here; then Jacq and his students go back in. Mossdeep's
    own 29 objects are copied as they are and its own ON_TRANSITION script runs after ours (we jump to it). The
    Timeless Woods keep only map scripts that read the woods again for a save made there on an older build, so
    that nothing of ours is left standing in them.
  * The wall, 35/89 (drawn by world.py from the unused cliff 34/27's pieces, tinted grey-green): the hole's
    other end, Research Station No. 1 (Penny) and the icy cave on the middle ledge, the way down on the bottom one.
  * The crater, twice: 35/90 in the past and 35/91 in the future. A layout of its own (world.py: the Giant
    Chasm's tiles, the hack's Hisui terrace pieces, Route 119's waterfall, Petalburg's houses): cut-corner
    terraces on two levels, a waterfall into a pond (climbable: Research Station No. 4 at the top), a lake, woods.
    Different tints, music and wild Pokemon per era. Two time rifts (a pale "time crystal" up to 2026-10-11; since
    then a shimmering tear in the air, cold blue in the past, warm amber in the future: mons.py, sprites/rift.py)
    take you to the same spot in the other era.
    Arven's picnic with the worn-out legend (Koraidon then, Miraidon to come), the Quaking Earth Titan in the den
    (Great Tusk / Iron Treads), Nemona in the future, the Zero Lab's door: a shutter, shut until Penny has
    unlocked it AND Arven and Nemona have come to it, which they do by themselves once both legends are well and
    Nemona is beaten.
  * Where everybody and everything stands is not in this file: places.py reads it from placements.txt, which the
    user edits (by hand, or with editor.py's page; rebuild.py makes the ROM again), and check.py refuses a build
    in which something stands in a wall or in the way. A save made on one of these maps holds its own copy of
    the map; when that copy is from a build with other positions the map is read again (story.FRESH).
  * Sprites of its own (mons.py, sprites/): the seventeen Gen 9 Pokemon that stand on these maps, as overworld
    sprites from pokeemerald-expansion, and the stations' recorder, in the unused end of the hack's sprite table;
    the field's palette table is copied with their palettes added.
  * Rooms of the game's behind every door, their way out MAP_DYNAMIC: four research stations (35/92, 93, 97, 98:
    the unused lab room 35/13: a log, a note, a cot, the game's PC, and after the ending one of the four people
    each), the Crystal Cavern (35/94: a Mt. Coronet room, violet), the icy cave (35/95: an Iron Island room,
    white; the Frigibax line), the Zero Lab (35/96: the Rocket Hideout's lab, violet: the finale, a Booster Energy
    shop) and the Underdepths (35/100: a Mt. Coronet chamber, crystal light: Terapagos). 35/99 was the Sealed
    Shrine up to test 10 (the Ruinous four as stone stakes); they are in the caves now, as themselves, and the
    room is kept, empty and with no way in, only so that a save made inside it still loads: its way out leads to
    the wall.
  * The Sealed Vault (35/101, test 15) behind the Crystal Cavern's second mouth, which opens once the story is
    done: a room drawn by world.py from the Snowpoint Temple's pieces, tinted like the cavern, with a floor you
    slide on. Wo-Chien, Ting-Lu and Chi-Yu stand in niches behind crystals; a crystal bursts when its stake, out
    on the floor, is pulled (story.py). And a Booster Energy lying in each crater.
  * Trainers in four entries no script uses (952 Nemona, 943 AI Sada, 947 AI Turo, 958 the Paradise Protection
    Protocol, a double battle), two new trainer classes. Titans are wild battles with the Totem flags (0x272 no
    Poke Balls, 0x273 no white-out: you can try again); everything after the story can be caught.
  * Map section 186 ("Route 224", which no map uses) is renamed "Area Zero" for the new maps.
"""
import os, struct, sys, zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from lib import enc, box, moves, Script, Blob
import maps as M
import tint as T
import world as W
import story as ST
import mons as MN
import places as PL
import ground as GR
import check as CK
import journal_az as JAZ
import tiles as TL
import objpal as OP

FREE, FREE_END = 0x01FBC400, 0x01FD2A00   # in the 0xFF run 0x09FBC380..0x09FD2A00 (blank in the hack's own ROM)
JOURNAL_FREE, JOURNAL_END = 0x01FE1000, 0x01FE8000   # Area Zero in the Journal and the Legends (journal_az.py): in
                                                     # the ROM's free tail, before the sprites' block (13 KB used in
                                                     # 2026-10; from 0x01FE8000 on: gen9journal's, the last step)
SPRITE_FREE, SPRITE_END = 0x01FF1000, 0x01FFC000   # the sprites' block, in the ROM's free tail (0x09FDCE38 on)
GROUP = 35                                 # new maps go after group 35's last (89 maps: 35/89 on)
GROUP_COUNT = 89

WOODS = (34, 67)                                 # the way in up to test 15: map scripts only now (see above)
WOODS_HEADER = 0x00AD8918
WOODS_EVENTS = 0x00AEB258
WOODS_EVENTS_WAS = bytes.fromhex("08060201") + struct.pack("<IIII", 0x08AEB13C, 0x08AEB1FC, 0x08AEB22C, 0x08AEB24C)
MOSSDEEP = (0, 6)                                # the way in since test 16
MOSSDEEP_HEADER = 0x00482560
MOSSDEEP_EVENTS = 0x00B0C3C0
MOSSDEEP_OBJS, MOSSDEEP_NOBJ = 0x00B0BFA4, 29
MOSSDEEP_EVENTS_WAS = bytes.fromhex("1d0b0a09") + struct.pack("<IIII", 0x08B0BFA4, 0x08B0C25C, 0x08B0C2B4, 0x08B0C354)
MOSSDEEP_SCRIPTS = 0x009D0E58                    # its map scripts: ON_TRANSITION only, the hack's own
MOSSDEEP_ON_TRANSITION = 0x0980BFE2              # (clears 0x64-0x67, shows or hides the Space Center's people;
MOSSDEEP_ON_TRANSITION_WAS = bytes.fromhex("2a64002a65002a66002a6700")   # ends with `end` on every path)
CLIFF = (34, 27)
CLIFF_HEADER = 0x00DD5010
CLIFF_LAYOUT = 0x08DD6258
CHASM = (34, 79)
CHASM_HEADER = 0x00E1CE90
CHASM_LAYOUT = 0x08E1EF30
PETAL = (0, 0)                                   # Petalburg City: the research stations' house comes from it
PETAL_HEADER = 0x004824B8
PETAL_LAYOUT = 0x083E0524
# Rooms behind the new doors: (group, num), size, and the metatile on each tile a warp of ours goes on
ROOMS = {
    "station": ((35, 13), (12, 9), {(9, 8): 571, (10, 8): 572}),    # a lab room no warp leads to: its door mat
    "cavern": ((36, 82), (19, 14), {(3, 1): 774, (6, 11): 575}),     # Mt. Coronet: a cave mouth, a ladder down
    "icecave": ((36, 65), (13, 11), {(6, 8): 758}),                  # Iron Island: the way out
    "lab": ((34, 75), (15, 17), {(7, 14): 627}),                     # the Rocket Hideout's lab: its pad
    "shrine": ((36, 74), (17, 15), {(8, 12): 572}),                  # a Regigigas Temple room: its way out
    "underdepths": ((36, 94), (25, 25), {(12, 21): 734}),            # a Mt. Coronet chamber round a pool
}
DYNAMIC = (127, 127)                             # MAP_DYNAMIC: a warp back to the warp you came in by
MUS_HEAL, MUS_ITEM = 368, 370
ITEM_BALL = 59                                   # main sprite 59
# The parts of the rooms that are furniture, not placements: the station's cot (signs on the right counter, the
# back room's doorway behind it; its PC on the back wall, 5,1, is the game's own and needs no event of ours), the
# cavern's ladder down, the lab's machine (the glass cylinder, read from below), terminals and supply terminal.
STATION_COT = [(9, 3), (10, 3)]
CAVERN_LADDER = (6, 11)                          # a crystal grows on it until the story is done
CAVERN_MOUTH2 = (15, 1)                          # the cavern's second mouth: into the Sealed Vault, likewise
LAB_MACHINE_XY = (6, 3)
LAB_TERMINALS_XY = [(1, 7), (3, 7), (10, 7), (12, 7)]
LAB_SHOP_XY = (12, 11)
SHRINE_PLAQUE_XY = [(7, 5), (8, 5), (9, 5)]
# what lies on each station's table: Penny's tablet (a clipboard, ext 28), Arven's backpack (main 97), a drawing
# (ext 28), a field guide (an open book, ext 27)
NOTE_SPRITES = [(0x4E, 28), (97, 0), (0x4E, 28), (0x4E, 27)]
# the finale: the AIs appear either side of you at the machine; for the Protocol you step back (LAB_STEP_BACK)
# and its Koraidon and Miraidon come up behind you, in view above the message box's rows
LAB_CAST_FACE = {"sada": "down", "turo": "down", "lab_koraidon": "up", "lab_miraidon": "up"}
LAB_STEP_BACK = "walk down*2"
LAB_STAND = [(6, 4), (6, 5), (6, 6)]             # where you stand at the machine, and step back to

EXT_LIT, EXT_TABLE = 0x014A2C10, 0x0839CF00      # the hack's own sprite table, found through one literal
HOLE_EXT, TIME_EXT = 125, 126                    # blank entries that no map uses
BLANK_16x32 = {                                  # blank entries no map uses, as they are in the ROM
    125: "ffff0511ff110001100020001401000014955008a095500800915008a0234009a8c62e08",
    126: "ffff0a1102110001100020001401000014955008a095500800915008985f4009a8c62e08",
    127: "ffff0a11ff110001100020001401000014955008a09550080091500874d04009a8c62e08",
    212: "ffff0611ff110001100020001401000014955008a09550080091500880f74209a8c62e08",
    225: "ffff0a11ff110001100020001401000014955008a095500800915008003b4309a8c62e08",
    227: "ffff0a11ff110001100020001401000014955008a095500800915008005e4309a8c62e08",
}
SHARD_EXT, BLACK_SHARD_EXT, RED_SHARD_EXT = 20, 21, 22   # the hack's crystal shards (16x32): purple, black, red
# The Sealed Vault's things, all the hack's own sprites: a stone marker for a stake (it stood for the Ruinous four
# themselves up to test 10: "the statue"), a big wooden board for the tablet, a small sign for the Sword's slat,
# and a dark crystal across each niche. (sprite number: its size, as the build expects it)
# The crystals are all the dark one because it shares the marker's palette. The hack gives every object its
# palette by tag out of six slots (4-9) and gives none back until the map is left; a seventh tag goes to slot 10,
# and an eighth takes that slot from the seventh. The first build of the vault had a crystal of its own colour on
# each niche (purple, black, red: 8 tags with the tablet, the slat, the markers and the three Pokemon), and
# Ting-Lu stood there in Chi-Yu's colours. check.py counts them now (PALETTES).
STAKE_EXT, TABLET_EXT, SLAT_EXT = 23, 13, 12
VAULT_SPRITES = {STAKE_EXT: (16, 32), TABLET_EXT: (32, 32), SLAT_EXT: (16, 16)}
SEAL_EXT = BLACK_SHARD_EXT
SE_ICE_BREAK, SE_ICE_CRACK = 41, 42
TIME_PAL = 0x1111                                # the time crystal: pale and glassy. No map of this build has
                                                 # one (the rifts took its place), but entry 126 is still written:
                                                 # a save's copy of a crater from before shows it until it is read
                                                 # again (the stamp below)
# Area Zero's own sprites (mons.py; the pictures are in sprites/): key -> (file, slot in the hack's sprite table,
# palette tag). The first four keep the blank slots tests 1-9 gave them; the rest take the table's unused end
# (240-255: none is left). The tags follow the game's last (0x1123).
SPRITES = {
    "koraidon": ("koraidon", 127, 0x1124), "miraidon": ("miraidon", 212, 0x1125),
    "tusk": ("great_tusk", 225, 0x1126), "treads": ("iron_treads", 227, 0x1127),
    "walking_wake": ("walking_wake", 240, 0x1128), "gouging_fire": ("gouging_fire", 241, 0x1129),
    "raging_bolt": ("raging_bolt", 242, 0x112A), "iron_leaves": ("iron_leaves", 243, 0x112B),
    "iron_boulder": ("iron_boulder", 244, 0x112C), "iron_crown": ("iron_crown", 245, 0x112D),
    "roaring_moon": ("roaring_moon", 246, 0x112E), "iron_valiant": ("iron_valiant", 247, 0x112F),
    "terapagos": ("terapagos", 248, 0x1130), "recorder": ("recorder", 249, 0x1131),
    "wo_chien": ("wo_chien", 250, 0x1132), "chien_pao": ("chien_pao", 251, 0x1133),
    "ting_lu": ("ting_lu", 252, 0x1134), "chi_yu": ("chi_yu", 253, 0x1135),
    # the time rift: one set of pictures (four shimmering frames), the past's colours and the future's
    "rift_past": ("rift_cold", 254, 0x1136), "rift_future": ("rift_warm", 255, 0x1137),
}
MAIN_TABLE = 0x00505620
VORTEX = 168                                     # main sprite: the dark vortex (Hearthome 37/73, Hisui 37/104)
VORTEX_INFO = 0x0850B118
HOLE_PAL = 0x1119                                # deep indigo, one of the game's 35 (the vortex's own 0x1106 is pink)
JACQ_GFX = 9                                     # main sprite 9: dark hair, white lab coat
# stand-ins from the game's own people (main table)
ARVEN_GFX, NEMONA_GFX, PENNY_GFX, SADA_GFX, TURO_GFX = 37, 20, 58, 202, 46
RESIDENTS = [("penny", PENNY_GFX), ("arven_home", ARVEN_GFX), ("nemona_home", NEMONA_GFX), ("jacq_home", JACQ_GFX)]

# The Zero Lab's door in the crater wall: a shutter (Petalburg's 653) while it is shut, the cave mouth (167) once
# Arven and Nemona have lifted it. The map has the mouth; ON_LOAD puts the shutter on. The shutter must be a tile
# that is no door to the game: test 11's first build used 584, a nicer one, whose behaviour is "animated door"
# (0x69), and walking north into one of those warps whether the tile is solid or not (found by test_story7).
DOOR_SHUT_TILE = 653
DOOR_SHUT, DOOR_OPEN = W.blk(DOOR_SHUT_TILE, 1, 0), W.blk(167, 0, 0)

TRAINERS = 0x010019F8                            # 40 bytes a trainer
CLASS_NAMES = 0x0030FCD4                         # 13 bytes a class; 71 used, 0xFF after them
FLAG_NO_BALLS, FLAG_NO_WHITEOUT = 0x272, 0x273   # the Totems' (0x098C15E2): balls refused, a loss not a white-out
B_WON, B_CAUGHT = 1, 7                           # GetBattleOutcome (special 183)
GET_OUTCOME = 183
VAR_RESULT = 0x800D

MAPSEC_TABLE, MAPSEC = 0x005A147C, 186           # gRegionMapEntries; 186 is "Route 224", which no map uses
MAPSEC_NAME_WAS = 0x085A1369

WILD_END = 0x00E19128                            # gWildMonHeaders (0x08E17D50, 254 entries): its terminator, then
WILD_END_WAS = bytes.fromhex("ffff0000") + b"\x77" * 16 + b"\xff" * 68   # free space to 0x08E19180, nothing points in

SE_PIN, SE_DOOR = 21, 8
MUSIC_WALL, MUSIC_PAST, MUSIC_FUTURE = 479, 381, 501   # the Space-Time Rift's, the hack's mysterious-island
                                                       # theme, the Pokemon Mansion's (New Mauville)
VAR_X, VAR_Y = 0x8004, 0x8005
CAVE_WARP = 2                                    # each crater's warp to the Crystal Cavern
STAMP_SALT = 14                                  # part of the build's stamp (story.FRESH): one more whenever what
                                                 # Mossdeep (the woods up to test 15) gets from this patch changes
                                                 # other than in place

PLAYER = 0xFF                                    # the player, to the commands that move an object
JACQ_LOCAL, HOLE_LOCAL = 30, 31                  # Mossdeep's own objects are 1-29
HOME_LOCALS = {"end_arven": 32, "end_nemona": 33, "end_penny": 34}
TREE_BORDER = [W.blk(470, 1), W.blk(471, 1), W.blk(468, 1), W.blk(469, 1)]   # woods all round, past the map's edge
FACE_BORDER = [W.blk(W.FACE, 1)] * 4
TITLES = {"mossdeep": "Mossdeep City", "wall": "the wall", "past": "the crater in the past",
          "future": "the crater in the future", "station1": "Research Station No. 1",
          "station2": "Research Station No. 2", "station3": "Research Station No. 3",
          "station4": "Research Station No. 4", "cavern": "the Crystal Cavern", "icecave": "the icy cave",
          "lab": "the Zero Lab", "shrine": "the old Sealed Shrine", "underdepths": "the Underdepths",
          "vault": "the Sealed Vault"}


def u16(rom, o): return struct.unpack_from("<H", rom, o)[0]
def u32(rom, o): return struct.unpack_from("<I", rom, o)[0]


def header_of(rom, g, n):
    return u32(rom, u32(rom, M.MAP_GROUPS + 4 * g) - 0x08000000 + 4 * n) - 0x08000000


def name_id(rom, table, size, name, count, what):
    """The entry called `name` in one of the ROM's name tables (its pointer in the header at `table`)."""
    t = u32(rom, table) - 0x08000000
    want = enc(name)
    for i in range(count):
        e = rom[t + size * i:t + size * i + size]
        if e[:len(want)] == want and (len(want) == size or e[len(want)] == 0xFF):
            return i
    raise AssertionError("no %s %r in this ROM (is it the Gen 9 build?)" % (what, name))


def species_id(rom, name): return name_id(rom, 0x144, 11, name, 1280, "species")
def move_id(rom, name): return name_id(rom, 0x148, 13, name, 1024, "move")


def item_id(rom, name):
    """The item called `name` in the ROM's own item table (header 0x1C8, 44 bytes each, the name first)."""
    t = u32(rom, 0x1C8) - 0x08000000
    want = enc(name) + b"\xFF"
    for i in range(1000):
        if rom[t + 44 * i:t + 44 * i + len(want)] == want:
            return i
    raise AssertionError("no item %r in this ROM" % name)


def blocks_of(rom, layout):
    lo = layout - 0x08000000
    w, h, data = u32(rom, lo), u32(rom, lo + 4), u32(rom, lo + 12) - 0x08000000
    return [[struct.unpack_from("<H", rom, data + 2 * (y * w + x))[0] for x in range(w)] for y in range(h)]


def build(inp, outp, placements=None, told=None, ground=None, tiles=None):
    """Makes the ROM. placements: the positions' file (places.load). ground: the painted ground's file
    (ground.load). tiles: the file of tiles taken from other maps (tiles.load). told: a dict that is filled with
    what the picture tools want to know (the maps, and what stands where on each)."""
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    assert set(rom[FREE - 0x80:FREE_END]) == {0xFF}, "free space is not free"
    assert set(rom[SPRITE_FREE - 0x80:SPRITE_END]) == {0xFF}, "the sprites' space is not free"
    # what this patch changes still looks the way it did when it was written
    assert header_of(rom, *WOODS) == WOODS_HEADER, "the Timeless Woods' header moved"
    assert u32(rom, WOODS_HEADER + 4) == 0x08000000 + WOODS_EVENTS and u32(rom, WOODS_HEADER + 8) == 0, \
        "the Timeless Woods' events moved, or it has map scripts now"
    assert bytes(rom[WOODS_EVENTS:WOODS_EVENTS + 20]) == WOODS_EVENTS_WAS, "the Timeless Woods' events changed"
    assert header_of(rom, *MOSSDEEP) == MOSSDEEP_HEADER, "Mossdeep City's header moved"
    assert u32(rom, MOSSDEEP_HEADER + 4) == 0x08000000 + MOSSDEEP_EVENTS, "Mossdeep City's events moved"
    assert bytes(rom[MOSSDEEP_EVENTS:MOSSDEEP_EVENTS + 20]) == MOSSDEEP_EVENTS_WAS, "Mossdeep City's events changed"
    assert u32(rom, MOSSDEEP_HEADER + 8) == 0x08000000 + MOSSDEEP_SCRIPTS and \
        bytes(rom[MOSSDEEP_SCRIPTS:MOSSDEEP_SCRIPTS + 6]) == b"\x03" + struct.pack("<I", MOSSDEEP_ON_TRANSITION) + b"\0", \
        "Mossdeep City's map scripts are not ON_TRANSITION alone any more"
    on_tr = MOSSDEEP_ON_TRANSITION - 0x08000000
    assert bytes(rom[on_tr:on_tr + len(MOSSDEEP_ON_TRANSITION_WAS)]) == MOSSDEEP_ON_TRANSITION_WAS, \
        "Mossdeep City's ON_TRANSITION script changed"
    assert sorted(rom[MOSSDEEP_OBJS + 24 * i] for i in range(MOSSDEEP_NOBJ)) == list(range(1, MOSSDEEP_NOBJ + 1))
    assert header_of(rom, *CLIFF) == CLIFF_HEADER and u32(rom, CLIFF_HEADER) == CLIFF_LAYOUT
    assert u32(rom, CLIFF_HEADER + 4) == 0 and u32(rom, CLIFF_HEADER + 8) == 0, "34/27 is in use now"
    assert header_of(rom, *CHASM) == CHASM_HEADER and u32(rom, CHASM_HEADER) == CHASM_LAYOUT
    assert header_of(rom, *PETAL) == PETAL_HEADER and u32(rom, PETAL_HEADER) == PETAL_LAYOUT
    for key, (src, size, spots) in ROOMS.items():
        b = blocks_of(rom, u32(rom, header_of(rom, *src)))
        assert (len(b[0]), len(b)) == size, "room %s (%d/%d) is not the size it was" % ((key,) + src)
        for (x, y), mt in spots.items():
            assert b[y][x] & 0x3FF == mt and not (b[y][x] >> 10) & 3, "room %s: no way through at %d,%d" % (key, x, y)
    vault_lay = u32(rom, header_of(rom, *W.VAULT_SRC)) - 0x08000000
    vault_beh = CK.behaviours(rom, vault_lay)
    assert vault_beh(W.VP["ice"]) == W.ICE and vault_beh(W.VP["door"]) == 0x65, "the temple's ice or way out changed"
    assert not vault_beh(W.VP["patch"]) and vault_beh(W.VP["rock"]) != W.ICE, "the temple's snow patch is ice now"
    for ext, size in VAULT_SPRITES.items():
        assert struct.unpack_from("<hh", rom, EXT_TABLE - 0x08000000 + 0x24 * ext + 8) == size, "sprite %d" % ext
    assert M.group_count(rom, GROUP)[1] == GROUP_COUNT, "group %d does not end where it did" % GROUP
    assert u32(rom, EXT_LIT) == EXT_TABLE, "the hack's sprite table moved"
    for ext, was in BLANK_16x32.items():
        e = EXT_TABLE - 0x08000000 + 0x24 * ext
        assert rom[e:e + 0x24].hex() == was, "sprite %d is not the blank entry it was" % ext
    MN.check(rom, EXT_TABLE, SPRITES, set(BLANK_16x32))
    assert set(ST.LEGENDS) <= set(SPRITES) and set(ST.LEGENDS) <= set(PL.BY_ID)
    assert u32(rom, MAIN_TABLE + 4 * VORTEX) == VORTEX_INFO
    me = MAPSEC_TABLE + 8 * MAPSEC
    assert u32(rom, me + 4) == MAPSEC_NAME_WAS and rom[MAPSEC_NAME_WAS - 0x08000000:][:10] == enc("Route 224") + b"\xFF"
    assert sum(1 for i in range(213) if u32(rom, MAPSEC_TABLE + 8 * i + 4) == MAPSEC_NAME_WAS) == 1
    assert bytes(rom[WILD_END:WILD_END + len(WILD_END_WAS)]) == WILD_END_WAS, "the wild table's end changed"
    for cls in ST.NEW_CLASSES:
        assert set(rom[CLASS_NAMES + 13 * cls:CLASS_NAMES + 13 * cls + 13]) == {0xFF}, "class %d is in use" % cls
    species = {name: species_id(rom, rom_name) for name, rom_name in ST.SPECIES.items()}
    items = {name: item_id(rom, name) for name in [ST.CAVERN_ITEM, ST.ICE_ITEM, ST.REWARD] + ST.SHOP +
             [m[2] for t in ST.TRAINERS.values() for m in t[6]]}
    booster = u32(rom, 0x1C8) - 0x08000000 + 44 * items["BoosterEnergy"]
    assert u16(rom, booster + 16) in (0, ST.BOOSTER_PRICE), "Booster Energy has a price of its own now"

    at = PL.load(placements)                     # id -> (x, y), or a list of tiles for a group
    painted = GR.load(ground)                    # section -> {(x, y): block}: the ground where the user changed it
    taken = TL.load(tiles)                       # section -> [(our number, group, map, its metatile)]
    # (a second blob, in the ROM's free tail: the craters' own tileset when tiles are taken, and the Journal's rows)
    jblob = Blob(0x08000000 + JOURNAL_FREE)

    def pos(tid) -> "tuple[int, int]":
        x, y = at[tid]
        return x, y
    blob = Blob(0x08000000 + FREE)
    texts, scripts, mv = {}, [], {}

    def text(key, s):
        if key not in texts:
            texts[key] = box(rom, s)
        return key

    def say_all(s, prefix, lines):
        for k, line in enumerate(lines):
            s.say(text("%s_%d" % (prefix, k), line))

    def new(name):
        s = Script(name); scripts.append(s); return s

    def movement(key, spec):
        mv[key] = spec; return key

    def sign_script(name, lines):
        s = new(name)
        s.lockall(); say_all(s, name, lines); s.releaseall(); s.end()
        return name

    def talk_script(name, lines):
        s = new(name)
        s.lock(); s.faceplayer(); say_all(s, name, lines); s.release(); s.end()
        return name

    # What stands where, for check.py and the picture tools: map key -> [{id, k, name, xy, size, when, top, gfx,
    # ext}] (k: its place in a group, or None; gfx, ext: its sprite), and what is in the way without being ours
    # to move.
    placed, fixed = {}, {}

    own_tags = {slot: tag for name, slot, tag in SPRITES.values()}
    own_tags.update({HOLE_EXT: HOLE_PAL, TIME_EXT: TIME_PAL})

    def tag_of(gfx, ext=0):
        """The palette tag of an object's sprite: ours as this build writes them, the rest from the ROM's tables."""
        if gfx == 0x4E:
            return own_tags[ext] if ext in own_tags else u16(rom, EXT_TABLE - 0x08000000 + 0x24 * ext + 2)
        return u16(rom, u32(rom, MAIN_TABLE + 4 * gfx) - 0x08000000 + 2)

    def stands(mkey, tid, gfx, ext=0, xy=None, name=None, k=None):
        placed.setdefault(mkey, []).append({
            "id": tid, "k": k, "name": name or PL.NAME_OF[tid], "xy": tuple(xy or at[tid]),
            "kind": PL.KIND_OF[tid], "size": PL.SIZE[PL.KIND_OF[tid]], "when": PL.WHEN_OF[tid],
            "top": tid in PL.ON_SOLID, "gfx": gfx, "ext": ext, "tag": tag_of(gfx, ext)})

    def group(mkey, tid, what, gfx, ext=0):
        for k, xy in enumerate(at[tid]):
            stands(mkey, tid, gfx, ext, xy, "%s %d" % (what, k + 1), k)
        return at[tid]

    def in_the_way(mkey, name, xy, when=("story", "after"), open=False):
        """Not ours to move: something standing there, or (open) a tile that has to stay free."""
        fixed.setdefault(mkey, []).append({"name": name, "xy": tuple(xy), "when": set(when), "open": open})

    # ---------------------------------------------------------------------------------------- the maps
    wall_b, wm = W.wall(blocks_of(rom, CLIFF_LAYOUT))
    crater_b, cm = W.crater(blocks_of(rom, CHASM_LAYOUT), blocks_of(rom, PETAL_LAYOUT))
    wall = M.Map("wall", CLIFF, W.WALL_W, W.WALL_H, wall_b, border=FACE_BORDER, music=MUSIC_WALL, weather=0,
                 mapsec=MAPSEC, map_type=8, popup=True, tilesets=T.tilesets(rom, blob, CLIFF, "zero"))
    # The shutter's picture is on its tile's second layer, which the game draws over people: standing below the
    # shut door you had no head (the user's screenshot of test 11). In the craters' copy of the tileset the tile
    # is "covered": both its layers under people. No map of the game's sees that copy.
    under_people = (DOOR_SHUT_TILE,)
    past = M.Map("past", CHASM, W.CRATER_W, W.CRATER_H, crater_b, border=TREE_BORDER, music=MUSIC_PAST, weather=0,
                 mapsec=MAPSEC, map_type=8, tilesets=T.tilesets(rom, blob, CHASM, "past", under_people))
    future = M.Map("future", CHASM, W.CRATER_W, W.CRATER_H, [list(r) for r in crater_b], border=TREE_BORDER,
                   music=MUSIC_FUTURE, weather=0, mapsec=MAPSEC, map_type=8,
                   tilesets=T.tilesets(rom, blob, CHASM, "future", under_people))

    def room(key, kind, tint, music, map_type, covered=()):
        src, (w, h), _ = ROOMS[kind]
        sets = T.tilesets(rom, blob, src, tint, covered) if tint or covered else None
        return M.Map(key, src, w, h, blocks_of(rom, u32(rom, header_of(rom, *src))), music=music, weather=0,
                     mapsec=MAPSEC, map_type=map_type, tilesets=sets)

    # The recorder stands on a counter's front edge and is drawn up over the counter's top, and that tile's second
    # layer is drawn over people (for a clerk standing behind it): the recorder's reels were cut off (the user, on
    # test 11: "the top part got cut off"). The tile it stands on and the one above it are "covered" in the
    # stations' copy of the tileset, wherever placements.txt puts it.
    station_lay = u32(rom, header_of(rom, *ROOMS["station"][0])) - 0x08000000
    station_b = blocks_of(rom, station_lay + 0x08000000)
    rx, ry = at["recorder"]
    over = {painted.get("stations", {}).get((rx, y), station_b[y][rx]) & 0x3FF for y in (ry - 1, ry)
            if 0 <= rx < len(station_b[0]) and 0 <= y < len(station_b)}
    over = tuple(sorted(m for m in over if T.layer(rom, station_lay, m) == 0))
    stations = [room("station%d" % (k + 1), "station", None, MUSIC_WALL, 8, over) for k in range(4)]
    cavern = room("cavern", "cavern", "crystal", MUSIC_WALL, 4)
    icecave = room("icecave", "icecave", "ice", MUSIC_WALL, 4)
    lab = room("lab", "lab", "future", MUSIC_FUTURE, 8)
    shrine = room("shrine", "shrine", "past", MUSIC_WALL, 8)
    under = room("underdepths", "underdepths", "tera", MUSIC_WALL, 4)
    # the Sealed Vault: drawn new, in the temple's tilesets with the tint of the cavern it opens off
    vault_b, vm = W.vault()
    vault = M.Map("vault", W.VAULT_SRC, W.VAULT_W, W.VAULT_H, vault_b, music=MUSIC_WALL, weather=0, mapsec=MAPSEC,
                  map_type=4, tilesets=T.tilesets(rom, blob, W.VAULT_SRC, "crystal"))
    # every map keeps the number an older test build gave it: a save made in one loads into the same one
    maplist = [wall, past, future, stations[0], stations[1], cavern, icecave, lab, stations[2], stations[3],
               shrine, under, vault]
    eras = {"past": past, "future": future}
    # The ground as the user has painted it, laid over the maps as they are drawn (each map gets rows of its own
    # first). `drawn` keeps them as they were: the editor shows what was changed, and check.py holds the tiles
    # that must not be (doors, signs) against it.
    for m in maplist:
        m.blocks = [list(r) for r in m.blocks]
    drawn = {m.key: [list(r) for r in m.blocks] for m in maplist}
    GR.lay(painted, {m.key: m for m in maplist})
    # Tiles taken from other maps (tiles.py): the craters get a secondary tileset of their own, Petalburg's with
    # the taken metatiles after it. What of Petalburg's is on the ground (painted or built) stays as it is; the
    # shut door's tile always does. With nothing taken the craters keep the game's tileset, as before test 18.
    custom = None
    crater_ids = {v & 0x3FF for m in eras.values() for row in m.blocks for v in row}
    strays = sorted(i for i in crater_ids if i >= TL.FIRST and i not in {t[0] for t in taken["crater"]})
    if strays:
        raise TL.TilesError(
            "The craters' ground has %s painted on it, but %s not among the tiles taken from other maps (tiles.txt). "
            "Paint over %s, or put the ground back." % (
                "tile %d" % strays[0] if len(strays) == 1 else "tiles %s" % ", ".join(map(str, strays)),
                "it is" if len(strays) == 1 else "they are", "it" if len(strays) == 1 else "them"))
    if taken["crater"]:
        custom = TL.build(rom, taken["crater"], crater_ids | {DOOR_SHUT_TILE})
        for era, m in eras.items():
            m.tilesets = (m.tilesets[0], T.custom_secondary(blob, jblob, custom, era,
                                                            [k % T.HALF for k in under_people if k >= T.HALF]))
    # a rock behind each 64x64 Pokemon of the crater: its sprite covers whoever stands there
    for era, big in (("past", ("legend", "raging_bolt")), ("future", ("legend",))):
        for tid in big:
            x, y = at[tid]
            if 0 <= x < W.CRATER_W and 0 < y < W.CRATER_H:
                W.rock(eras[era].blocks, x, y - 1)
    # What the game draws past the crater's edges (world.beyond): strips that go on with whatever the map ends
    # in, painted ground too, joined to each crater as connections. They are maps nobody enters, numbered after
    # the others. One set serves both times while their edges are alike.
    strips = {}
    for era in ("past", "future"):
        for side, (rows, offset) in W.beyond(eras[era].blocks).items():
            look = (side, repr(rows))
            if look not in strips:
                key = "%s_%s" % (side, era) if any(k[0] == side for k in strips) else side
                strips[look] = M.Map(key, CHASM, len(rows[0]), len(rows), rows, border=TREE_BORDER)
            eras[era].connect(side, offset, strips[look].key)
    strips = list(strips.values())
    groups = {m.key: GROUP for m in maplist + strips}
    gn = M.numbers(rom, maplist + strips, groups)

    # ---------------------------------------------------------------------------------------- shared scripts
    READY = (ST.F_KORAIDON_UP, ST.F_MIRAIDON_UP, ST.F_BEAT_NEMONA)
    # (the Pokemon among our sprites: they turn to face you. Not the recorder and not the rifts, which are things: a
    # thing keeps movement type 0, and that matters to the rift - "face down" pauses a sprite's animation the
    # moment it has turned, and the rift would stand still on its first picture)
    mon_slots = {slot for key, (name, slot, tag) in SPRITES.items() if key != "recorder" and not key.startswith("rift_")}

    def unless_ready(s, label, flags=READY):
        for f in flags:
            s.if_unset(f, label)

    # Who is to be seen is worked out from the story's own flags every time one of these maps is come into or come
    # back to (ON_TRANSITION, and ON_RESUME: that one runs before the people are placed, on Continue too), not
    # kept in flags set once: tests 7-10 did that (F_INIT), and every later change to who appears when left the
    # saves of the build before it showing the wrong people.
    #  - Arven and Nemona hold the lab's door from the moment Koraidon and Miraidon are well, Nemona is beaten
    #    and Penny has unlocked it, until the finale is won. Whichever of those comes last sends them there:
    #    Arven's script, Nemona's (to_the_door), or this, on the way into the crater after Penny's. Test 9 sent
    #    them only from Arven's script; the user did the logs after talking to him and could not start the finale.
    #  - The legends are hidden until the finale is won; from then on their flags mean "caught".
    #  - The students stand in the Timeless Woods for the ending only; afterwards they are in the stations.
    s = new("state")
    s.setflag(ST.F_HIDE_GUARDS)
    s.if_set(ST.F_STORY_DONE, "people")
    for v in ST.LEGENDS.values():
        s.setflag(v[3])
    unless_ready(s, "people", READY + (ST.F_LAB_OPEN,))
    s.setflag(ST.F_GUARDS_UP); s.clearflag(ST.F_HIDE_GUARDS)
    s.here("people")
    s.setflag(ST.F_HIDE_HOME); s.setflag(ST.F_HIDE_RESIDENTS)
    s.if_var(ST.STAGE, ST.S_HOME, "ending")
    s.if_var(ST.STAGE, ST.S_DONE, "home")
    s.ret()
    s.here("ending"); s.clearflag(ST.F_HIDE_HOME); s.ret()
    s.here("home"); s.clearflag(ST.F_HIDE_RESIDENTS); s.ret()

    # A save keeps its own copy of the map it was made on: where every person and thing stood, and which of them
    # were in sight. Positions can be edited now (places.py), so a save made in Area Zero would go on showing the
    # old ones until you left the map. ST.FRESH holds the stamp of the build that copy was taken from: set on the
    # way into each of these maps; on resume any other stamp is turned into 0, and 0 is what each map's ON_FRAME
    # table waits for ("refresh_<map>": the same map again at the tile you stand on, read from the ROM). A save
    # from before test 11 has 0 there already. The stamp (a sum over every map's people, things and ground and
    # over the positions) is known only once the maps are made: stamp() notes where it goes.
    stamp_sites = []                                       # (script, offset of the value)

    def stamp(s):
        stamp_sites.append((s, len(s.b) - 2))

    def transition(name):
        s = new(name)
        s.call(("script", "state"))
        s.setvar(ST.FRESH, 0); stamp(s)
        return s

    def resumes(name):
        s = new(name)
        s.call(("script", "state"))
        s.compare(ST.FRESH, 0); stamp(s)
        s.goto_if(1, "fresh"); s.setvar(ST.FRESH, 0); s.here("fresh")
        return s

    def refreshes(key, g, n):
        """The map's ON_FRAME entry, and its script."""
        s = new("refresh_" + key)
        s.lockall(); s.setvar(ST.FRESH, 0); stamp(s)
        s.getplayerxy(VAR_X, VAR_Y); s.warpsilent(g, n, VAR_X, VAR_Y); s.raw(0x27)   # waitstate: the map loads
        s.releaseall(); s.end()
        return (ST.FRESH, 0, "refresh_" + key)

    resumes("resume").end()

    def battle_wild(s, species, level, item=0):
        s.wildbattle(species, level, item); s.dowildbattle(); s.specialvar(VAR_RESULT, GET_OUTCOME)

    def waiting_for(s, prefix, lines):
        """A line for each thing that still keeps them from the door."""
        for key, flag in zip(("koraidon", "miraidon", "nemona"), READY):
            s.if_set(flag, "%s_%s_done" % (prefix, key))
            s.say(text("%s_%s" % (prefix, key), lines[key]))
            s.here("%s_%s_done" % (prefix, key))

    # ---------------------------------------------------------------------------------------- Mossdeep City
    # The way in (the Timeless Woods up to test 15). Mossdeep's own people and things are in the way of ours, and
    # nothing of ours may stand in one of its doorways.
    md_blocks = blocks_of(rom, u32(rom, MOSSDEEP_HEADER))
    hole_xy = tuple(at["hole"])
    home_back = (hole_xy[0], hole_xy[1] + 1)     # where the way home puts you: in front of the hole
    md_warps = u32(rom, MOSSDEEP_EVENTS + 8) - 0x08000000
    md_doors = {struct.unpack_from("<hh", rom, md_warps + 8 * k) for k in range(rom[MOSSDEEP_EVENTS + 1])}
    for k in range(MOSSDEEP_NOBJ):
        o = MOSSDEEP_OBJS + 24 * k
        in_the_way("mossdeep", "one of Mossdeep's own people or things", struct.unpack_from("<hh", rom, o + 4))
    in_the_way("mossdeep", "the tile you come out of the hole on", home_back, ("story", "after", "ending"), open=True)
    stands("mossdeep", "jacq", JACQ_GFX); stands("mossdeep", "hole", 0x4E, HOLE_EXT)
    for tid, gfx in (("end_arven", ARVEN_GFX), ("end_nemona", NEMONA_GFX), ("end_penny", PENNY_GFX)):
        stands("mossdeep", tid, gfx)

    def toward(a, b):
        """The way to face from tile a to look at tile b."""
        dx, dy = b[0] - a[0], b[1] - a[1]
        if abs(dx) >= abs(dy):
            return "right" if dx > 0 else "left"
        return "down" if dy > 0 else "up"

    def height_at(xy):
        """The height of Mossdeep's ground under a person of ours (the woods' people stood at 3, the ground's)."""
        x, y = xy
        z = md_blocks[y][x] >> 12 if 0 <= y < len(md_blocks) and 0 <= x < len(md_blocks[0]) else 3
        return 3 if z in (0, 1, 15) else z

    s = new("mossdeep_state")                    # Jacq: from the start of the game (2026-10-11: before the hole he
    s.setflag(ST.F_WOODS_HIDE); s.setflag(ST.F_JACQ_HIDE)      # talks of his field trip) until the ending is over;
    s.if_var(ST.STAGE, ST.S_DONE, "hole")        # the hole: once Team Rainbow Rocket is beaten
    s.clearflag(ST.F_JACQ_HIDE)
    s.here("hole")
    s.if_unset(ST.F_RR_DONE, "out")
    s.clearflag(ST.F_WOODS_HIDE)
    s.here("out"); s.ret()
    # ours first, then Mossdeep's own ON_TRANSITION, which ends the script
    s = transition("mossdeep_transition"); s.call(("script", "mossdeep_state")); s.goto(MOSSDEEP_ON_TRANSITION)
    s = resumes("mossdeep_resume"); s.call(("script", "mossdeep_state")); s.end()
    refreshes("mossdeep", *MOSSDEEP)
    # The Timeless Woods: a save made there on an older build holds Jacq, the hole and the students in its copy of
    # the woods. Its stamp is not this build's, so the woods are read again from the ROM, where they are the
    # game's own again (the same refresh as on Area Zero's maps).
    transition("woods_transition").end()
    resumes("woods_resume").end()
    refreshes("woods", *WOODS)

    s = new("jacq")
    s.lock(); s.faceplayer()
    s.if_unset(ST.F_RR_DONE, "early")            # no hole yet: the field trip
    s.if_set(ST.F_MET_JACQ, "again")
    s.if_set(ST.F_MET_EARLY, "known")
    say_all(s, "jacq_intro", ST.JACQ_INTRO)
    s.here("met")
    s.setflag(ST.F_MET_JACQ); s.setvar(ST.STAGE, ST.S_MET)
    s.release(); s.end()
    s.here("known")                              # you met before the hole opened: he does not say who he is again
    say_all(s, "jacq_known", ST.JACQ_INTRO_KNOWN)
    for k in range(3, len(ST.JACQ_INTRO)):
        s.say(text("jacq_intro_%d" % k, ST.JACQ_INTRO[k]))
    s.goto("met")
    s.here("again"); say_all(s, "jacq_again", ST.JACQ_AGAIN); s.release(); s.end()
    s.here("early")
    s.if_set(ST.F_MET_EARLY, "early_again")
    say_all(s, "jacq_early", ST.JACQ_EARLY)
    s.setflag(ST.F_MET_EARLY)
    s.release(); s.end()
    s.here("early_again"); say_all(s, "jacq_early_again", ST.JACQ_EARLY_AGAIN); s.release(); s.end()

    s = new("hole")
    s.lockall()
    s.if_set(ST.F_MET_JACQ, "ask")
    s.say(text("hole_first_0", ST.HOLE_FIRST[0])); s.closemessage()
    s.playse(SE_PIN); s.move(JACQ_LOCAL, movement("jacq_alarm", "!, face " + toward(at["jacq"], hole_xy)))
    s.say(text("hole_first_1", ST.HOLE_FIRST[1]))
    s.releaseall(); s.end()
    s.here("ask")
    s.ask(text("hole_ask", ST.HOLE_ASK)); s.closemessage()
    s.if_yes("go"); s.releaseall(); s.end()
    s.here("go"); s.warpteleport(*gn["wall"], *wm["arrive"]); s.end()

    s = new("nothing"); s.end()                  # the students by the hole: there while the ending talks for them

    # The ending (Mossdeep's ON_FRAME, on arriving home). When the talk is over the four of them go back in: up to
    # test 10 they stayed, in a row across the only strip of ground by the hole in the woods.
    s = new("ending")
    s.lockall()
    say_all(s, "ending", ST.ENDING)
    s.giveitem(items[ST.REWARD])
    say_all(s, "ending_after", ST.ENDING_AFTER)
    s.closemessage()
    s.fade(1)
    s.removeobject(JACQ_LOCAL)                   # (each sets its own hide flag; "state" keeps them so)
    for local in HOME_LOCALS.values():
        s.removeobject(local)
    s.setvar(ST.STAGE, ST.S_DONE)
    s.fade(0)
    s.say(text("ending_gone", ST.ENDING_GONE))
    s.releaseall(); s.end()

    # ---------------------------------------------------------------------------------------- Area Zero: the wall
    hx, hy = wm["hole"]
    wall.objs.append(M.Obj(1, hx, hy, "wall_back", gfx=0x4E, ext=HOLE_EXT, face="none", elevation=0))
    wall.on_frame.append((ST.STAGE, ST.S_MET, "wall_intro"))
    wall.on_transition, wall.on_resume = "wall_transition", "resume"
    transition("wall_transition").end()
    in_the_way("wall", "where you land when you come through the hole", wm["arrive"], open=True)
    wall.warp(*wm["down"], "past", 0)                     # wall warp 0: the bottom ledge's mouth -> the crater
    wall.warp(*wm["station"], "station1", 0)              # 1: Research Station No. 1
    wall.warp(*wm["ice"], "icecave", 0)                   # 2: the icy cave

    s = new("wall_intro")
    s.lockall(); say_all(s, "wall_intro", ST.WALL_INTRO)
    s.setvar(ST.STAGE, ST.S_ARRIVED); s.releaseall(); s.end()

    s = new("wall_back")
    s.lockall(); s.ask(text("wall_back_ask", ST.WALL_BACK_ASK)); s.closemessage()
    s.if_yes("go"); s.releaseall(); s.end()
    s.here("go"); s.warpteleport(*MOSSDEEP, *home_back); s.end()

    # ---------------------------------------------------------------------------------------- the crater, twice
    lab_x, lab_y = cm["L"][0]
    # The Zero Lab's door. Penny unlocks it (F_LAB_OPEN); Arven and Nemona lift it when they get there
    # (F_GUARDS_UP), and until then nobody goes in: up to test 10 Penny alone opened it, and the user walked in to
    # a machine that asked for the other two ("the door should be prohibited to enter until those two are at the
    # door to not make confusion").
    s = new("crater_load")
    s.if_set(ST.F_GUARDS_UP, "open")
    s.setmetatile(lab_x, lab_y, DOOR_SHUT); s.end()
    s.here("open"); s.end()
    s = new("lab_door")                          # read from below; says what is still missing
    s.lockall()
    s.if_set(ST.F_GUARDS_UP, "lift")
    s.if_set(ST.F_LAB_OPEN, "unlocked")
    say_all(s, "lab_door", ST.LAB_DOOR_SHUT); s.releaseall(); s.end()
    s.here("unlocked")
    unless_ready(s, "wait")
    s.setflag(ST.F_GUARDS_UP); s.clearflag(ST.F_HIDE_GUARDS)   # all is done and nothing has sent them (a save or a
    s.here("lift")                                             # state from an older build, made on this map)
    s.setmetatile(lab_x, lab_y, DOOR_OPEN); s.drawmap()
    s.releaseall(); s.end()
    s.here("wait"); say_all(s, "lab_door_wait", ST.LAB_DOOR_WAIT)
    waiting_for(s, "lab_todo", ST.LAB_TODO); s.releaseall(); s.end()
    for era, m in eras.items():
        m.on_transition, m.on_resume = era + "_transition", era + "_resume"
        m.on_load = "crater_load"
        m.warp(*cm["mouth"][0], "wall", 0)                 # warp 0: the north cave mouth -> up to the wall
        m.warp(*cm["door2"][0], "station2", 0)             # 1: Research Station No. 2
        m.warp(*cm["cave"][0], "cavern", 0)                # 2: the Crystal Cavern (CAVE_WARP)
        assert len(m.warps) == CAVE_WARP + 1
        m.warp(lab_x, lab_y, "lab", 0)                     # 3: the Zero Lab
        m.warp(*cm["door3"][0], "station3", 0)             # 4: Research Station No. 3
        m.warp(*cm["door4"][0], "station4", 0)             # 5: Research Station No. 4, above the waterfall
        m.bg(lab_x, lab_y, "lab_door")
    # which crater you are in (the Crystal Cavern's way out wants to know): on the way in, and on resume, which is
    # what a save made here by an older build gets
    for era in eras:
        for s in (transition(era + "_transition"), resumes(era + "_resume")):
            (s.setflag if era == "future" else s.clearflag)(ST.F_IN_FUTURE)
            s.end()

    def to_the_door(s, lk):
        """They leave for the door and lift it: the flags (both eras read them), and this map's own people."""
        s.closemessage()
        s.fade(1)
        s.setflag(ST.F_GUARDS_UP); s.clearflag(ST.F_HIDE_GUARDS)
        s.removeobject(lk["arven"])                        # nothing happens to one who is out of sight: the flag
        if "nemona" in lk:                                 # keeps him from coming back
            s.removeobject(lk["nemona"])
        s.addobject(lk["guard_arven"]); s.addobject(lk["guard_nemona"])
        s.setmetatile(lab_x, lab_y, DOOR_OPEN); s.drawmap()
        s.fade(0)

    times = [at["time1"], at["time2"]]
    sign_script("crystal", ST.CRYSTAL)
    locals_ = {}
    for era, other, ask in (("past", "future", ST.TIME_CRYSTAL_TO_FUTURE), ("future", "past", ST.TIME_CRYSTAL_TO_PAST)):
        m = eras[era]
        objs = []                                          # (key, x, y, script, gfx, ext, flag)
        for k, tid in enumerate(("time1", "time2")):
            objs.append(("time%d" % k, *at[tid], "time_" + era, 0x4E, SPRITES["rift_" + era][1], 0))
            stands(era, tid, 0x4E, SPRITES["rift_" + era][1])
        shard = RED_SHARD_EXT if era == "past" else BLACK_SHARD_EXT    # red crystals then, dark ones to come
        for k, (x, y) in enumerate(group(era, "crystals", "crystal", 0x4E, shard)):
            objs.append(("crystal%d" % k, x, y, "crystal", 0x4E, shard, 0))
        legend, titan = ("koraidon", "tusk") if era == "past" else ("miraidon", "treads")
        caught = ST.F_KORAIDON_CAUGHT if era == "past" else ST.F_MIRAIDON_CAUGHT
        done = ST.F_TUSK_DONE if era == "past" else ST.F_TREADS_DONE
        objs += [("arven", *at["arven"], "arven_" + era, ARVEN_GFX, 0, ST.F_GUARDS_UP),
                 ("legend", *at["legend"], "legend_" + era, 0x4E, SPRITES[legend][1], caught),
                 ("titan", *at["titan"], "titan_" + era, 0x4E, SPRITES[titan][1], done),
                 ("guard_arven", *at["guard_arven"], "guard_arven", ARVEN_GFX, 0, ST.F_HIDE_GUARDS),
                 ("guard_nemona", *at["guard_nemona"], "guard_nemona", NEMONA_GFX, 0, ST.F_HIDE_GUARDS)]
        stands(era, "arven", ARVEN_GFX); stands(era, "titan", 0x4E, SPRITES[titan][1])
        stands(era, "guard_arven", ARVEN_GFX); stands(era, "guard_nemona", NEMONA_GFX)
        stands(era, "legend", 0x4E, SPRITES[legend][1], name="Koraidon" if era == "past" else "Miraidon")
        if era == "future":
            objs.append(("nemona", *at["nemona"], "nemona", NEMONA_GFX, 0, ST.F_GUARDS_UP))
            stands(era, "nemona", NEMONA_GFX)
        for key, (sp, level, where, flag) in ST.LEGENDS.items():
            if where == era:
                objs.append((key, *at[key], "legend_" + key, 0x4E, SPRITES[key][1], flag))
                stands(era, key, 0x4E, SPRITES[key][1])
        # an item ball of the crater's own, one in each time (the user, on test 14: "have more item ball booster
        # energy in the crater as well like 1-2 location")
        ball = "booster_" + era
        objs.append((ball, *at[ball], ball, ITEM_BALL, 0, ST.F_BOOSTER[era]))
        stands(era, ball, ITEM_BALL)
        s = new(ball)
        s.setorcopyvar(0x8000, items[ST.CAVERN_ITEM]); s.setorcopyvar(0x8001, 1); s.callstd(1); s.end()
        lk = {}
        for k, (key, x, y, script, gfx, ext, flag) in enumerate(objs):
            # people and Pokemon look at you; things keep still
            face = "down" if (gfx != 0x4E and gfx != ITEM_BALL) or ext in mon_slots else "none"
            m.objs.append(M.Obj(1 + k, x, y, script, gfx=gfx, ext=ext, face=face, flag=flag, elevation=0))
            lk[key] = 1 + k
        locals_[era] = lk

        s = new("time_" + era)
        s.lockall()
        s.if_set(ST.F_RIPPLE_SEEN, "ask")
        say_all(s, "time_first", ST.TIME_CRYSTAL_FIRST); s.setflag(ST.F_RIPPLE_SEEN)
        s.here("ask")
        s.ask(text("time_to_" + other, ask)); s.closemessage()
        s.if_yes("go"); s.releaseall(); s.end()
        s.here("go")
        s.getplayerxy(VAR_X, VAR_Y)                        # arrive where you stand, in the other era
        s.warpteleport(*gn[other], VAR_X, VAR_Y); s.end()

    talk_script("guard_arven", ST.GUARD_ARVEN)
    talk_script("guard_nemona", ST.GUARD_NEMONA)

    # Arven at his picnic, one script per era (the same flags)
    for era in ("past", "future"):
        legend_sp = "Koraidon" if era == "past" else "Miraidon"
        mine_up, other_up = (ST.F_KORAIDON_UP, ST.F_MIRAIDON_UP) if era == "past" else (ST.F_MIRAIDON_UP,
                                                                                         ST.F_KORAIDON_UP)
        titan_done = ST.F_TUSK_DONE if era == "past" else ST.F_TREADS_DONE
        lk = locals_[era]
        s = new("arven_" + era)
        s.lock(); s.faceplayer()
        s.if_set(ST.F_MET_ARVEN, "met")
        say_all(s, "arven_first_" + era, ST.ARVEN_FIRST[era]); s.setflag(ST.F_MET_ARVEN)
        s.release(); s.end()
        s.here("met")
        s.if_set(mine_up, "next")
        s.if_set(titan_done, "sandwich")
        say_all(s, "arven_wait_" + era, ST.ARVEN_WAIT[era]); s.release(); s.end()
        s.here("sandwich")
        lines = ST.ARVEN_SANDWICH[era]
        s.say(text("sandwich_%s_0" % era, lines[0])); s.closemessage()
        s.fade(1); s.playse(SE_DOOR); s.delay(60); s.fade(0)
        s.playfanfare(MUS_HEAL); s.say(text("sandwich_%s_1" % era, lines[1])); s.waitfanfare()
        s.say(text("sandwich_%s_2" % era, lines[2]))
        s.cry(species[legend_sp])
        s.say(text("sandwich_%s_3" % era, lines[3]))
        s.say(text("sandwich_%s_4" % era, lines[4]))
        s.setflag(mine_up)
        s.here("next")
        s.if_unset(other_up, "other")
        s.if_unset(ST.F_BEAT_NEMONA, "nemona")
        s.if_unset(ST.F_LAB_OPEN, "penny")
        say_all(s, "arven_go", ST.ARVEN_GO)
        to_the_door(s, lk)
        s.release(); s.end()
        s.here("other"); say_all(s, "arven_next_" + era, ST.ARVEN_NEXT[era]); s.release(); s.end()
        s.here("nemona"); say_all(s, "arven_nemona", ST.ARVEN_NEMONA); s.release(); s.end()
        s.here("penny"); say_all(s, "arven_penny", ST.ARVEN_PENNY); s.release(); s.end()

        # the legend by the picnic: worn out, then on its feet, then (after the story) yours to catch
        caught = ST.F_KORAIDON_CAUGHT if era == "past" else ST.F_MIRAIDON_CAUGHT
        s = new("legend_" + era)
        s.lock(); s.faceplayer()
        s.if_set(ST.F_STORY_DONE, "partner")
        s.if_set(mine_up, "up")
        say_all(s, "legend_weak_" + era, ST.LEGEND[era]["weak"]); s.release(); s.end()
        s.here("up"); s.cry(species[legend_sp]); say_all(s, "legend_up_" + era, ST.LEGEND[era]["up"])
        s.release(); s.end()
        s.here("partner")
        s.cry(species[legend_sp])
        s.ask(text("partner_ask_" + era, ST.PARTNER_ASK[era])); s.closemessage()
        s.if_yes("battle"); s.release(); s.end()
        s.here("battle")
        battle_wild(s, species[legend_sp], ST.PARTNER_LEVEL)
        # caught or knocked out, it is gone for good (the user, test 18: "when defeat the legendaries or capture
        # ... there should disappear not infinite reencounter"); run from it and it is still there. The fade is the
        # game's own way (Common_EventScript_RemoveStaticPokemon)
        s.if_var(VAR_RESULT, B_CAUGHT, "gone")
        s.if_var(VAR_RESULT, B_WON, "gone")
        say_all(s, "partner_stay_" + era, ST.PARTNER_STAY[era]); s.release(); s.end()
        s.here("gone"); s.fade(1); s.removeobject(lk["legend"]); s.fade(0); s.release(); s.end()

        # the Titan: two battles, the Totems' flags on (no Poke Balls; a loss heals you and you can come back)
        t = ST.TITAN[era]
        half = 0x43D2 if era == "past" else 0x43D3        # the first battle won
        s = new("titan_" + era)
        s.lock(); s.faceplayer()
        s.cry(species[t["species"]])
        s.if_set(half, "grown")
        say_all(s, "titan_meet_" + era, t["meet"])
        s.ask(text("titan_ask_" + era, t["ask"])); s.closemessage()
        s.if_yes("first"); s.release(); s.end()
        s.here("first")
        s.setflag(FLAG_NO_BALLS); s.setflag(FLAG_NO_WHITEOUT)
        battle_wild(s, species[t["species"]], t["levels"][0])
        s.clearflag(FLAG_NO_BALLS); s.clearflag(FLAG_NO_WHITEOUT)
        s.if_var(VAR_RESULT, B_WON, "lost", cond=5)
        s.setflag(half)
        s.shake()
        say_all(s, "titan_grow_" + era, t["grow"])
        s.goto("second")
        s.here("grown")
        say_all(s, "titan_grown_" + era, t["grow"][1:])
        s.ask(text("titan_ask_" + era, t["ask"])); s.closemessage()
        s.if_yes("second"); s.release(); s.end()
        s.here("second")
        s.closemessage()
        s.setflag(FLAG_NO_BALLS); s.setflag(FLAG_NO_WHITEOUT)
        battle_wild(s, species[t["species"]], t["levels"][1], items["Leftovers"])
        s.clearflag(FLAG_NO_BALLS); s.clearflag(FLAG_NO_WHITEOUT)
        s.if_var(VAR_RESULT, B_WON, "lost", cond=5)
        s.say(text("titan_done_%s_0" % era, t["done"][0])); s.closemessage()
        s.fade(1); s.removeobject(lk["titan"]); s.fade(0)
        s.say(text("titan_done_%s_1" % era, t["done"][1]))
        s.playfanfare(MUS_ITEM); s.say(text("herba_got", ST.HERBA_GOT)); s.waitfanfare()
        s.say(text("herba_back", ST.HERBA_BACK))
        s.release(); s.end()
        s.here("lost")
        s.heal()
        say_all(s, "titan_lost_" + era, t["lost"]); s.release(); s.end()

    # Nemona, in the future's tall grass south of the pond
    s = new("nemona")
    s.lock(); s.faceplayer()
    s.if_set(ST.F_BEAT_NEMONA, "again")
    say_all(s, "nemona_first", ST.NEMONA_FIRST)
    s.closemessage()
    s.battle(ST.TRAINERS["nemona"][0], text("nemona_defeat", ST.NEMONA_DEFEAT))
    s.setflag(ST.F_BEAT_NEMONA)
    say_all(s, "nemona_after", ST.NEMONA_AFTER)
    s.here("next")
    unless_ready(s, "wait", (ST.F_KORAIDON_UP, ST.F_MIRAIDON_UP, ST.F_LAB_OPEN))
    say_all(s, "nemona_go", ST.NEMONA_GO)
    to_the_door(s, locals_["future"])
    s.release(); s.end()
    s.here("wait"); say_all(s, "nemona_wait", ST.NEMONA_WAIT); s.release(); s.end()
    s.here("again"); say_all(s, "nemona_again", ST.NEMONA_AGAIN); s.goto("next")

    # the legends after the story, wherever they stand (the craters, the Crystal Cavern, the icy cave, the
    # Underdepths, the Sealed Vault): a cry, a line, a battle; caught or knocked out, it is gone for good (up to
    # test 17 one knocked out stayed, to be tried again); run from it and it stays
    for key, (sp_name, level, where, flag) in ST.LEGENDS.items():
        s = new("legend_" + key)
        s.lock(); s.faceplayer()
        s.cry(species[sp_name])
        s.say(text("legend_line_" + key, ST.LEGEND_LINES[key]))
        s.ask(text("legend_ask", ST.LEGEND_ASK)); s.closemessage()
        s.if_yes("battle"); s.release(); s.end()
        s.here("battle")
        battle_wild(s, species[sp_name], level)
        s.if_var(VAR_RESULT, B_CAUGHT, "gone")
        s.if_var(VAR_RESULT, B_WON, "gone"); s.release(); s.end()
        s.here("gone"); s.setflag(flag); s.fade(1); s.removeobject(0x800F); s.fade(0); s.release(); s.end()

    # ---------------------------------------------------------------------------------------- the stations
    s = new("rest")                                        # the stations' cot
    s.lockall(); s.ask(text("rest_ask", ST.REST_ASK)); s.closemessage()
    s.if_yes("go"); s.releaseall(); s.end()
    s.here("go")
    s.fade(1); s.heal(); s.playfanfare(MUS_HEAL); s.waitfanfare(); s.fade(0)
    s.say(text("rest_done", ST.REST_DONE)); s.releaseall(); s.end()
    for k, m in enumerate(stations):
        for xy in ROOMS["station"][2]:
            m.warp(*xy, "dynamic", 0)
        m.on_transition, m.on_resume = "station_transition", "resume"
        s = new("log%d" % (k + 1))
        s.lockall()
        s.say(text("log_intro", ST.LOG_INTRO))
        say_all(s, "log%d" % (k + 1), ST.LOGS[k])
        s.say(text("log_end", ST.LOG_END))
        s.setflag(ST.F_LOGS[k]); s.releaseall(); s.end()
        for xy in STATION_COT:
            m.bg(*xy, "rest")
        sign_script("note%d" % (k + 1), ST.NOTES[k])
        # who lives here: Penny from the start; the other three after the ending
        who, gfx = RESIDENTS[k]
        m.objs.append(M.Obj(1, *pos("resident"), who, gfx=gfx, face="down",
                            flag=0 if k == 0 else ST.F_HIDE_RESIDENTS, elevation=3))
        m.objs.append(M.Obj(2, *pos("recorder"), "log%d" % (k + 1), gfx=0x4E, ext=SPRITES["recorder"][1],
                            face="none", elevation=3))
        stands(m.key, "resident", gfx, name=("Penny", "Arven", "Nemona", "Jacq")[k])
        stands(m.key, "recorder", 0x4E, SPRITES["recorder"][1])
        gfx, ext = NOTE_SPRITES[k]
        m.objs.append(M.Obj(3, *pos("note"), "note%d" % (k + 1), gfx=gfx, ext=ext, face="none", elevation=3))
        stands(m.key, "note", gfx, ext)
    transition("station_transition").end()

    s = new("penny")
    s.lock(); s.faceplayer()
    s.if_var(ST.STAGE, ST.S_DONE, "home")
    s.if_set(ST.F_LAB_OPEN, "open")
    s.if_set(ST.F_MET_PENNY, "met")
    say_all(s, "penny_first", ST.PENNY_FIRST); s.setflag(ST.F_MET_PENNY); s.release(); s.end()
    s.here("met")
    for k, f in enumerate(ST.F_LOGS):
        s.if_unset(f, "hint%d" % k)
    say_all(s, "penny_open", ST.PENNY_OPEN); s.setflag(ST.F_LAB_OPEN)
    unless_ready(s, "not_yet")
    s.here("ready"); say_all(s, "penny_ready", ST.PENNY_READY); s.release(); s.end()
    s.here("not_yet"); say_all(s, "penny_not_yet", ST.PENNY_NOT_YET)
    s.here("todo"); waiting_for(s, "penny_todo", ST.PENNY_TODO); s.release(); s.end()
    for k in range(4):
        s.here("hint%d" % k); s.say(text("penny_hint%d" % k, ST.PENNY_HINTS[k])); s.release(); s.end()
    s.here("open")
    unless_ready(s, "after")
    s.goto("ready")
    s.here("after"); say_all(s, "penny_after", ST.PENNY_AFTER); s.goto("todo")
    s.here("home"); say_all(s, "penny_home", ST.PENNY_HOME); s.release(); s.end()

    # the other three, after the ending: Arven's sandwiches (they heal), Nemona's rematch, Jacq
    s = new("arven_home")
    s.lock(); s.faceplayer()
    s.if_unset(ST.F_KORAIDON_CAUGHT, "waiting"); s.if_unset(ST.F_MIRAIDON_CAUGHT, "waiting")
    say_all(s, "arven_home_both", ST.ARVEN_HOME_BOTH); s.goto("snack")
    s.here("waiting"); say_all(s, "arven_home", ST.ARVEN_HOME)
    s.here("snack")
    s.say(text("arven_snack", ST.ARVEN_SNACK)); s.closemessage()
    s.fade(1); s.heal(); s.playfanfare(MUS_HEAL); s.waitfanfare(); s.fade(0)
    s.say(text("arven_snack_done", ST.ARVEN_SNACK_DONE)); s.release(); s.end()

    s = new("nemona_home")
    s.lock(); s.faceplayer()
    s.ask(text("nemona_home_ask", ST.NEMONA_HOME_ASK)); s.closemessage()
    s.if_yes("battle")
    say_all(s, "nemona_home_no", ST.NEMONA_HOME_NO); s.release(); s.end()
    s.here("battle")
    s.battle(ST.TRAINERS["nemona"][0], text("nemona_defeat", ST.NEMONA_DEFEAT))
    s.setflag(ST.F_NEMONA_REMATCH)              # only reached by winning (a loss whites out): the Side Content row
    say_all(s, "nemona_home_after", ST.NEMONA_HOME_AFTER); s.release(); s.end()

    talk_script("jacq_home", ST.JACQ_HOME)

    # ---------------------------------------------------------------------------------------- the caves
    def item_ball(m, local, tid, name, item, flag):
        s = new(name)
        s.setorcopyvar(0x8000, items[item]); s.setorcopyvar(0x8001, 1); s.callstd(1); s.end()   # STD_FIND_ITEM
        m.objs.append(M.Obj(local, *pos(tid), name, gfx=ITEM_BALL, face="none", flag=flag, elevation=3))
        stands(m.key, tid, ITEM_BALL)

    def crystals(m, ext, spots, script="crystal", first=1, flag=0):
        for k, (x, y) in enumerate(spots):
            m.objs.append(M.Obj(first + k, x, y, script, gfx=0x4E, ext=ext, face="none", flag=flag, elevation=3))
        return first + len(spots)

    exits = {k: list(v[2]) for k, v in ROOMS.items()}
    cavern.warp(*exits["cavern"][0], "dynamic", 0)
    cavern.warp(*exits["cavern"][1], "underdepths", 0)     # the ladder: open after the story
    cavern.warp(*CAVERN_MOUTH2, "vault", 0)                # warp 2, the second mouth: the Sealed Vault, likewise
    k = crystals(cavern, SHARD_EXT, group("cavern", "cavern_crystals", "crystal", 0x4E, SHARD_EXT))
    k = crystals(cavern, SHARD_EXT, [CAVERN_LADDER], sign_script("cavern_ladder", ST.CAVERN_LADDER), k,
                 flag=ST.F_STORY_DONE)
    in_the_way("cavern", "the crystal on the ladder", CAVERN_LADDER, ("story",))
    k = crystals(cavern, SHARD_EXT, [CAVERN_MOUTH2], sign_script("vault_mouth", ST.VAULT_MOUTH), k,
                 flag=ST.F_STORY_DONE)
    in_the_way("cavern", "the crystal in the second mouth", CAVERN_MOUTH2, ("story",))
    item_ball(cavern, k, "cavern_item", "cavern_item", ST.CAVERN_ITEM, ST.F_CAVERN_ITEM)
    icecave.warp(*exits["icecave"][0], "dynamic", 0)
    k = crystals(icecave, SHARD_EXT, group("icecave", "ice_crystals", "crystal", 0x4E, SHARD_EXT))
    item_ball(icecave, k, "ice_item", "ice_item", ST.ICE_ITEM, ST.F_ICE_ITEM)
    # A room's way out is MAP_DYNAMIC: back to the warp you came in by, which the game notes when you take a warp
    # whose far end is such a way out. It keeps ONE such place. Up to test 11 the Underdepths' way out was dynamic
    # too, so going down the cavern's ladder made that place the ladder, and from then on the cavern's mouth led
    # to the cavern's own ladder (the user: "the crystal cavern right now it is loop cannot go out"). The
    # Underdepths are only ever reached by that ladder, so their way out simply leads to it; and the cavern says
    # where its mouth leads every time it is come into or back to, for a save or a state made in the loop.
    under.warp(*exits["underdepths"][0], "cavern", 1)
    shrine.warp(*exits["shrine"][0], "wall", 0)            # no way in: out to the wall's bottom ledge
    for xy in SHRINE_PLAQUE_XY:
        shrine.bg(*xy, sign_script("shrine_empty", ST.SHRINE_EMPTY) if xy == SHRINE_PLAQUE_XY[0] else "shrine_empty")
    transition("cave_transition").end()
    # The Sealed Vault. Its way out is a plain warp to the mouth it is entered by (a second MAP_DYNAMIC room would
    # take the cavern's own way out, as the Underdepths did on test 11). The tablet and the Sword's slat are read;
    # each treasure has a stake on the mirror floor and a crystal across its niche, both hidden by one flag, and
    # the stake's script takes both off the map. Nothing else keeps the puzzle's state: a stake that is gone is
    # gone for good, and check.py has played every order through.
    vault.warp(*vm["door"][0], "cavern", 2)
    for local, (tid, ext, lines) in enumerate((("vault_tablet", TABLET_EXT, ST.VAULT_TABLET),
                                               ("vault_sword", SLAT_EXT, ST.VAULT_SWORD)), 1):
        vault.objs.append(M.Obj(local, *pos(tid), sign_script(tid, lines), gfx=0x4E, ext=ext, face="none",
                                elevation=3))
        stands("vault", tid, 0x4E, ext)
    for k, (stake, seal, key) in enumerate(PL.VAULT_SEALS):
        mark, l_stake, l_seal = ST.VAULT_MARKS[key], 3 + 2 * k, 4 + 2 * k
        s = new(stake)
        s.lockall()
        s.say(text(stake + "_look", ST.STAKE_LOOK.replace("{MARK}", mark)))
        s.ask(text("stake_ask", ST.STAKE_ASK)); s.closemessage()
        s.if_yes("pull"); s.releaseall(); s.end()
        s.here("pull")
        s.playse(SE_ICE_CRACK)
        s.removeobject(l_stake)
        s.say(text("stake_pulled", ST.STAKE_PULLED)); s.closemessage()
        s.shake()
        s.playse(SE_ICE_BREAK)
        s.removeobject(l_seal)                             # (out of sight it is not on the map: its flag is set)
        s.cry(species[ST.LEGENDS[key][0]])
        s.say(text("seal_broken", ST.SEAL_BROKEN))
        s.releaseall(); s.end()
        sign_script(seal, [line.replace("{MARK}", mark) for line in ST.SEAL_LOOK])
        for local, tid, ext in ((l_stake, stake, STAKE_EXT), (l_seal, seal, SEAL_EXT)):
            vault.objs.append(M.Obj(local, *pos(tid), tid, gfx=0x4E, ext=ext, face="none", flag=ST.F_SEALS[key],
                                    elevation=3))
            stands("vault", tid, 0x4E, ext)
    rooms_by_key = {"cavern": cavern, "icecave": icecave, "underdepths": under, "vault": vault}
    for m in list(rooms_by_key.values()) + [shrine]:       # (the shrine: for a save made in it by tests 7-10)
        m.on_transition, m.on_resume = "cave_transition", "resume"
    cavern.on_transition, cavern.on_resume = "cavern_transition", "cavern_resume"
    for s in (transition("cavern_transition"), resumes("cavern_resume")):
        s.if_set(ST.F_IN_FUTURE, "future")
        s.setdynamicwarp(*gn["past"], CAVE_WARP); s.end()
        s.here("future"); s.setdynamicwarp(*gn["future"], CAVE_WARP); s.end()
    for key, (sp_name, level, where, flag) in ST.LEGENDS.items():
        if where in rooms_by_key:
            m, (x, y) = rooms_by_key[where], at[key]
            m.objs.append(M.Obj(len(m.objs) + 1, x, y, "legend_" + key, gfx=0x4E, ext=SPRITES[key][1], face="down",
                                flag=flag, elevation=3))
            stands(where, key, 0x4E, SPRITES[key][1])

    # ---------------------------------------------------------------------------------------- the Zero Lab
    lab.warp(*exits["lab"][0], "dynamic", 0)
    lab.on_transition, lab.on_resume = "lab_transition", "resume"
    s = transition("lab_transition")                       # the finale's cast is out of sight whenever you come in:
    s.setflag(ST.F_HIDE_LAB_CAST); s.end()                 # a white-out halfway through leaves their flag cleared
    cast_locals = {}
    for k, key in enumerate(LAB_CAST_FACE):
        gfx, ext = {"sada": (SADA_GFX, 0), "turo": (TURO_GFX, 0), "lab_koraidon": (0x4E, SPRITES["koraidon"][1]),
                    "lab_miraidon": (0x4E, SPRITES["miraidon"][1])}[key]
        lab.objs.append(M.Obj(1 + k, *pos(key), "", gfx=gfx, ext=ext, face=LAB_CAST_FACE[key],
                              flag=ST.F_HIDE_LAB_CAST, elevation=3))
        cast_locals[key] = 1 + k
        stands("lab", key, gfx, ext)
    for xy in LAB_STAND:
        in_the_way("lab", "the place you stand in at the machine", xy, ("finale",), open=True)
    lab.bg(*LAB_MACHINE_XY, "lab_machine")
    for k, (xy, lines) in enumerate(zip(LAB_TERMINALS_XY, ST.LAB_TERMINALS)):
        lab.bg(*xy, sign_script("lab_terminal_%d" % k, lines))
    s = new("lab_shop")
    s.lockall(); s.say(text("lab_shop", ST.LAB_SHOP)); s.closemessage()
    s.pokemart("lab"); s.releaseall(); s.end()
    lab.bg(*LAB_SHOP_XY, "lab_shop")

    s = new("lab_machine")
    s.lockall()
    s.if_set(ST.F_STORY_DONE, "off")
    unless_ready(s, "not_ready")                           # the door being open is how you got in here
    s.setflag(ST.F_GUARDS_UP); s.clearflag(ST.F_HIDE_GUARDS)   # they hold the door (set long since, unless the
    s.say(text("finale_0", ST.FINALE_START[0])); s.closemessage()   # save was made in here by an older build)
    s.playse(SE_PIN)
    s.clearflag(ST.F_HIDE_LAB_CAST)
    s.addobject(cast_locals["sada"]); s.addobject(cast_locals["turo"])
    for k, line in enumerate(ST.FINALE_START[1:]):
        s.say(text("finale_%d" % (k + 1), line))
    s.closemessage()
    s.heal()
    s.battle(ST.TRAINERS["sada"][0], text("sada_defeat", ST.SADA_DEFEAT))
    say_all(s, "sada_after", ST.SADA_AFTER); s.closemessage()
    s.heal()
    s.battle(ST.TRAINERS["turo"][0], text("turo_defeat", ST.TURO_DEFEAT))
    s.shake()
    say_all(s, "protocol", ST.PROTOCOL); s.closemessage()
    s.move(PLAYER, movement("lab_step_back", LAB_STEP_BACK))   # away from the machine, to face what comes
    s.addobject(cast_locals["lab_koraidon"]); s.addobject(cast_locals["lab_miraidon"])
    s.cry(species["Koraidon"]); s.cry(species["Miraidon"])
    s.heal()
    s.battle(ST.TRAINERS["protocol"][0], text("protocol_defeat", ST.PROTOCOL_DEFEAT))
    s.fade(1)
    s.removeobject(cast_locals["lab_koraidon"]); s.removeobject(cast_locals["lab_miraidon"])
    s.fade(0)
    s.move(PLAYER, movement("lab_turn_back", "face up"))
    say_all(s, "finale_end", ST.FINALE_END); s.closemessage()
    s.fade(3)                                              # a white flash: they step into the machine
    s.removeobject(cast_locals["sada"]); s.removeobject(cast_locals["turo"])
    s.fade(2)
    s.say(text("finale_gone", ST.FINALE_GONE))
    s.setflag(ST.F_STORY_DONE); s.setflag(ST.F_HIDE_GUARDS); s.clearflag(ST.F_HIDE_HOME)
    for key, v in ST.LEGENDS.items():
        s.clearflag(v[3])
    s.setvar(ST.STAGE, ST.S_HOME)
    say_all(s, "finale_home", ST.FINALE_HOME); s.closemessage()
    s.warpteleport(*MOSSDEEP, *home_back); s.end()
    s.here("not_ready"); say_all(s, "lab_not_ready", ST.LAB_NOT_READY)
    waiting_for(s, "lab_todo", ST.LAB_TODO); s.releaseall(); s.end()
    s.here("off"); say_all(s, "lab_off", ST.LAB_MACHINE_OFF); s.releaseall(); s.end()

    # ---------------------------------------------------------------------------------------- is it all in order?
    def grounds(m, src=None, extra_starts=()):
        doors = [(w[0], w[1]) for w in m.warps]            # the first is the way in
        # tiles the painter leaves alone: something of the map's is tied to the very tile
        locked = {(w[0], w[1]): "a way in or out" for w in m.warps}
        for b in m.bgs:
            locked.setdefault((b[0], b[1]), "something you read or use with A")
        for c in m.coords:
            locked.setdefault((c[0], c[1]), "a spot where something happens")
        beh = CK.behaviours(rom, u32(rom, header_of(rom, *m.source)) - 0x08000000)
        layer = CK.layers(rom, u32(rom, header_of(rom, *m.source)) - 0x08000000, covered_of.get(m.key, ()))
        if custom and m.key in eras:                       # a taken tile is what it was on its own map
            beh0, layer0 = beh, layer
            beh = lambda mid: custom.beh[mid] if mid in custom.beh else beh0(mid)
            layer = lambda mid: custom.layer[mid] if mid in custom.layer else layer0(mid)
        return {"key": m.key, "title": TITLES[m.key], "blocks": m.blocks, "w": m.w, "h": m.h,
                "beh": beh, "layer": layer,
                "starts": doors + list(extra_starts), "doors": set(doors), "objects": len(m.objs),
                "things": placed.get(m.key, []), "fixed": fixed.get(m.key, []), "map": (m.group, m.num),
                "base": drawn[m.key], "locked": locked, "source": m.source, "section": GR.SECTION_OF.get(m.key),
                "puzzle": PL.VAULT_SEALS if m.key == "vault" else None}

    for m, (key, g_n) in zip(maplist, gn.items()):
        m.group, m.num = g_n
    # the metatiles each map's own copy of its tilesets draws under people (tint.tileset): a reflection shows on them
    covered_of = {"past": under_people, "future": under_people}
    covered_of.update({m.key: over for m in stations})
    crater_beh = CK.behaviours(rom, u32(rom, CHASM_HEADER) - 0x08000000)
    assert crater_beh(DOOR_SHUT_TILE) == 0, "the shut door's tile does something when walked into"
    surveyed = [{"key": "mossdeep", "title": TITLES["mossdeep"], "blocks": md_blocks, "w": len(md_blocks[0]),
                 "h": len(md_blocks), "beh": CK.behaviours(rom, u32(rom, MOSSDEEP_HEADER) - 0x08000000),
                 "layer": CK.layers(rom, u32(rom, MOSSDEEP_HEADER) - 0x08000000),
                 "starts": [home_back] + sorted(md_doors), "doors": md_doors, "things": placed["mossdeep"],
                 "fixed": fixed["mossdeep"], "map": MOSSDEEP, "objects": MOSSDEEP_NOBJ + len(placed["mossdeep"]),
                 "base": md_blocks, "locked": {}, "source": MOSSDEEP, "section": None}]
    surveyed += [grounds(m) for m in maplist]
    if told is not None:
        strip_of = {m.key: m.blocks for m in strips}
        told.update(maps=surveyed, at=at, sprites=SPRITES, painted=painted, rock=(W.BOULDER, tuple(W.PLAIN)),
                    taken=taken, custom=custom,
                    beyond={era: {side: strip_of[key] for side, _, key in eras[era].connections} for era in eras})
    CK.check(surveyed)

    # every map reads itself again when a save's copy of it is from another build (see transition() above)
    for m in maplist:
        assert m.on_transition and m.on_resume, m.key
        m.on_frame.insert(0, refreshes(m.key, *gn[m.key]))
    made = [(m.key, m.blocks, [(o.local, o.gfx, o.ext, o.x, o.y, o.elevation, o.face, o.flag, o.script)
                               for o in m.objs], m.connections) for m in maplist + strips]
    build_stamp = zlib.crc32(repr((STAMP_SALT, made, sorted(at.items()))).encode()) & 0xFFFF or 1
    for s, off in stamp_sites:
        struct.pack_into("<H", s.b, off, build_stamp)
    if told is not None:
        told["stamp"] = build_stamp

    # ---------------------------------------------------------------------------------------- lay out
    for key, spec in mv.items():
        blob.put(("move", key), moves(spec), 1)
    for key, t in texts.items():
        blob.put(("text", key), t, 1)
    for s in scripts:
        blob.put_script(s)
    blob.put(("name", "area_zero"), enc(ST.PLACE_NAME) + b"\xFF", 1)
    blob.put(("mart", "lab"), b"".join(struct.pack("<H", items[n]) for n in ST.SHOP) + b"\0\0", 2)
    # wild Pokemon: a land table for the past, the future and the icy cave (slots, then the 8-byte info)
    lo, hi = ST.WILD_LEVELS
    wild = {}
    for key, names in (("past", ST.PAST_WILD), ("future", ST.FUTURE_WILD), ("icecave", ST.ICE_WILD)):
        assert len(names) == 12
        blob.put(("wild_slots", key), b"".join(struct.pack("<BBH", lo, hi, species[n]) for n in names))
        info = blob.put(("wild_land", key), struct.pack("<BBBBI", ST.WILD_RATE, 0, 0, 0, 0))
        blob.ref(("wild_slots", key), info - blob.base + 4)
        wild[key] = info
    # the sprites of our own, in their block: pictures, frames, palettes, the palette table with their rows
    sblob = Blob(0x08000000 + SPRITE_FREE)
    MN.put(rom, sblob, SPRITES)
    sdata = sblob.link()
    assert SPRITE_FREE + len(sdata) <= SPRITE_END, "the sprites outgrew their space (%d bytes)" % len(sdata)
    # trainers: parties
    entries = {}
    for key, (slot, cls, pic, female, name, double, team) in ST.TRAINERS.items():
        party = b"".join(struct.pack("<HHHH4H", ST.TRAINER_IV, level, species[sp], items[item],
                                     *[move_id(rom, mvn) for mvn in mvs]) for sp, level, item, mvs in team)
        pp = blob.put(("party", key), party)
        nm = enc(name) + b"\xFF"
        entry = bytearray(40)
        entry[0], entry[1], entry[2], entry[3] = 3, cls, 0x80 if female else 0, pic   # custom moves + items
        entry[4:4 + len(nm)] = nm
        struct.pack_into("<III", entry, 24, 1 if double else 0, 0xFF, len(team))
        entries[key] = (slot, entry, ("party", key))
    # Mossdeep: its 29 objects as they are, then Jacq, the hole and (for the ending) the students; map scripts
    # ON_TRANSITION and ON_RESUME (who is to be seen; the transition then goes on into Mossdeep's own) and
    # ON_FRAME (a save's copy from another build read again; the ending, on the way home)
    tpl = bytearray(rom[MOSSDEEP_OBJS:MOSSDEEP_OBJS + 24 * MOSSDEEP_NOBJ])
    extra = [(JACQ_LOCAL, JACQ_GFX, 0, at["jacq"], height_at(at["jacq"]), toward(at["jacq"], hole_xy),
              ST.F_JACQ_HIDE, "jacq"),
             (HOLE_LOCAL, 0x4E, HOLE_EXT, at["hole"], 0, "none", ST.F_WOODS_HIDE, "hole")]
    for tid, gfx in (("end_arven", ARVEN_GFX), ("end_nemona", NEMONA_GFX), ("end_penny", PENNY_GFX)):
        extra.append((HOME_LOCALS[tid], gfx, 0, at[tid], height_at(at[tid]), toward(at[tid], home_back),
                      ST.F_HIDE_HOME, "nothing"))
    assert [e[0] for e in extra] == list(range(MOSSDEEP_NOBJ + 1, MOSSDEEP_NOBJ + 1 + len(extra)))
    for local, gfx, ext, (x, y), elev, face, flag, script in extra:
        tpl += struct.pack("<BBBBhhBBBBHHIHH", local, gfx, 0, ext, x, y, elev, M.MT[face], 0, 0, 0, 0, 0, flag, 0)
    p_tpl = blob.put(("mossdeep", "objs"), bytes(tpl))
    for k, e in enumerate(extra):
        blob.ref(("script", e[-1]), p_tpl - blob.base + 24 * (MOSSDEEP_NOBJ + k) + 16)

    def map_scripts(key, transition_script, resume_script, frame):
        """A list of map scripts: ON_TRANSITION, ON_FRAME (frame: [(var, value, script)]), ON_RESUME."""
        p_frame = blob.put((key, "frametab"), b"".join(struct.pack("<HHI", v, val, 0) for v, val, sc in frame) + b"\0\0")
        for k, (v, val, sc) in enumerate(frame):
            blob.ref(("script", sc), p_frame - blob.base + 8 * k + 4)
        p_ms = blob.put((key, "mapscripts"), struct.pack("<BIBIBI", 3, 0, 2, 0, 5, 0) + b"\0", 1)
        blob.ref(("script", transition_script), p_ms - blob.base + 1)
        blob.ref((key, "frametab"), p_ms - blob.base + 6)
        blob.ref(("script", resume_script), p_ms - blob.base + 11)
        return p_ms
    p_md = map_scripts("mossdeep", "mossdeep_transition", "mossdeep_resume",
                       [(ST.FRESH, 0, "refresh_mossdeep"), (ST.STAGE, ST.S_HOME, "ending")])
    p_woods = map_scripts("woods", "woods_transition", "woods_resume", [(ST.FRESH, 0, "refresh_woods")])
    known = {"dynamic": DYNAMIC}
    lt, gas = M.install(rom, blob, maplist + strips, groups, known)
    assert all(known[m.key] == gn[m.key] for m in maplist + strips)

    data = blob.link()
    assert FREE + len(data) <= FREE_END, "the area outgrew its space (%d bytes)" % len(data)
    rom[FREE:FREE + len(data)] = data
    M.repoint_tables(rom, lt, gas)
    rom[MOSSDEEP_EVENTS] = MOSSDEEP_NOBJ + len(extra)
    struct.pack_into("<I", rom, MOSSDEEP_EVENTS + 4, p_tpl)
    struct.pack_into("<I", rom, MOSSDEEP_HEADER + 8, p_md)
    struct.pack_into("<I", rom, WOODS_HEADER + 8, p_woods)
    vortex = bytearray(rom[VORTEX_INFO - 0x08000000:VORTEX_INFO - 0x08000000 + 0x24])
    assert struct.unpack_from("<hh", vortex, 8) == (32, 32)
    struct.pack_into("<H", vortex, 2, HOLE_PAL)
    o = EXT_TABLE - 0x08000000 + 0x24 * HOLE_EXT
    rom[o:o + 0x24] = vortex
    so = EXT_TABLE - 0x08000000 + 0x24 * SHARD_EXT
    shard = bytearray(rom[so:so + 0x24])
    assert struct.unpack_from("<hh", shard, 8) == (16, 32)
    struct.pack_into("<H", shard, 2, TIME_PAL)             # the time crystal: the shard's picture, pale
    o = EXT_TABLE - 0x08000000 + 0x24 * TIME_EXT
    rom[o:o + 0x24] = shard
    rom[SPRITE_FREE:SPRITE_FREE + len(sdata)] = sdata
    MN.install(rom, sblob, EXT_TABLE, SPRITES)
    struct.pack_into("<I", rom, me + 4, blob.addr[("name", "area_zero")])
    # the wild table: our headers where its terminator was, then the terminator again
    heads = b"".join(struct.pack("<BBHIIII", g, n, 0, wild[k], 0, 0, 0) for k, (g, n) in
                     ((k, gn[k]) for k in ("past", "future", "icecave")))
    assert len(heads) + 20 <= len(WILD_END_WAS), "no room left at the wild table's end"
    rom[WILD_END:WILD_END + len(heads) + 20] = heads + WILD_END_WAS[:20]
    # trainers, their classes, Booster Energy's price
    for cls, cname in ST.NEW_CLASSES.items():
        ce = CLASS_NAMES + 13 * cls
        rom[ce:ce + 13] = (enc(cname) + b"\xFF").ljust(13, b"\0")
    for key, (slot, entry, pk) in entries.items():
        struct.pack_into("<I", entry, 36, blob.addr[pk])
        rom[TRAINERS + 40 * slot:TRAINERS + 40 * slot + 40] = entry
    struct.pack_into("<H", rom, booster + 16, ST.BOOSTER_PRICE)
    # Area Zero in the Journal as an optional quest, and its legends in the Legends chapter (journal_az.py)
    journal_apply = JAZ.install(rom, jblob, species)
    legends_apply = JAZ.install_legends(rom, jblob, species)
    # objects' palettes: a slot nobody draws with any more goes to the next kind of thing (objpal.py; the hack's
    # own allocator gave the seventh kind and every one after it the same spare slot)
    objpal_apply = OP.install(rom, jblob)
    jdata = jblob.link()
    assert JOURNAL_FREE + len(jdata) <= JOURNAL_END, "the second blob outgrew its space (%d bytes)" % len(jdata)
    assert set(rom[JOURNAL_FREE - 0x80:JOURNAL_FREE + len(jdata)]) == {0xFF}, "the Journal's space is not free"
    rom[JOURNAL_FREE:JOURNAL_FREE + len(jdata)] = jdata
    jinfo, linfo = journal_apply(rom), legends_apply(rom)
    oinfo = objpal_apply(rom)

    with open(outp, "wb") as f:
        f.write(rom)
    print("paldea @%08X..%08X (%d bytes); maps %s" % (
        blob.base, blob.base + len(data), len(data), ", ".join("%s %d/%d" % (m.key, m.group, m.num) for m in maplist)))
    print("  past the crater's edges: %s" % ", ".join(
        "%s %d/%d (%dx%d)" % (m.key, m.group, m.num, m.w, m.h) for m in strips))
    print("  sprites @%08X..%08X (%d bytes), palette table %08X: %s" % (
        sblob.base, sblob.base + len(sdata), len(sdata), sblob.addr[("paltable",)],
        ", ".join("%s %d" % (k, v[1]) for k, v in SPRITES.items())))
    print("  Mossdeep: Jacq %s, the hole %s; wall: arrive %s, down %s; crater: mouth %s, time rifts %s, lab door %s,"
          " stations %s %s %s, cave %s" % (at["jacq"], at["hole"], wm["arrive"], wm["down"], cm["mouth"][0], times,
                                          cm["L"][0], cm["door2"][0], cm["door3"][0], cm["door4"][0], cm["cave"][0]))
    print("  objects: past %s; future %s" % (locals_["past"], locals_["future"]))
    print("  trainers: %s" % ", ".join("%s %d" % (k, v[0]) for k, v in ST.TRAINERS.items()))
    print("  Journal @%08X..%08X (%d bytes): Area Zero's rows %d-%d in the step table %08X, compute %08X; "
          "Legends %08X, %d of them now (+%s)" % (
              jblob.base, jblob.base + len(jdata), len(jdata), jinfo["rows"][0], jinfo["rows"][1], jinfo["steps"],
              jinfo["compute2"], linfo["legends"], linfo["count"], ", ".join(n for d, n in linfo["added"])))
    print("  objects' palettes: the allocator %08X (%s), from %08X" % (
        oinfo["at"], "in the base ROM already" if oinfo["already"] else "%d bytes" % oinfo["size"], OP.ALLOC))


def main(argv):
    if len(argv) not in (3, 4, 5, 6):
        print(__doc__.split("\n\n")[0])
        return 2
    try:
        build(argv[1], argv[2], argv[3] if len(argv) > 3 else None, None, argv[4] if len(argv) > 4 else None,
              argv[5] if len(argv) > 5 else None)
    except TL.TilesError as e:
        print("The tiles taken from other maps do not work out:\n  " + "\n  ".join(e.lines))
        return 1
    except (PL.PlacementError, GR.GroundError) as e:
        print("The file cannot be read:\n  " + str(e))
        return 1
    except CK.Problems as e:
        print("Nothing was built. %d thing%s to put right in the placements:" % (
            len(e.lines), "s" * (len(e.lines) > 1)))
        for line in e.lines:
            print("  - " + line)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
