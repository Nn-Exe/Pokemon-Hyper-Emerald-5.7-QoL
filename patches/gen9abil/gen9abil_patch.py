"""The Gen 9 abilities, working (Hyper Emerald v5.7). Apply after iconnight, before kitakami.
usage: python -I gen9abil_patch.py <in.gba> <out.gba>

Until now the Gen 9 abilities were stand-ins: gen9 and gen9rest gave each an id of 256 + an ability the engine has
(Orichalcum Pulse = 256 + Drought), handed to the engine as that ability (gen9.s's alias list), plus a few rules of
their own in gen9.s's damage and speed hooks. In battle they did what their stand-in did ("Oinkologne's Mummy!").

What this does:
 1. The abilities get ids of their own, the engine's free ones from 0x101 (gen9abil_data.ABILITIES), with names and
    texts; every Gen 9 species' row of the ability table (0x097A0000, three ids a species) is renumbered, the old
    id found by its name in the name table. Their old ids stay as they are, unused.
 2. gen9.s's alias list is emptied (its first pair zeroed), so the engine is handed every ability as it is. gen9.s's
    own ability rules (Ruin, Paradox, Orichalcum Pulse, Hadron Engine) key on the old ids and so do nothing now;
    its move rules (Hydro Steam, Glaive Rush...) and Booster Energy's item stay.
 3. The code (build.py: the C files and scripts.s, linked at gen9abil.sym's addresses) goes to BASE; the engine
    routines it stands in front of (WRAP) have every call pointed at it: each bl in the code regions, each pointer
    word in the ROM. Their counts are fixed (WRAP) and checked.
 4. Its battle messages: the engine's string table (0x17C on, one word at 0x09D4A204 holds it) gets a longer copy.
 5. The engine's battle state is allocated 0x40 bytes longer (0x09D49230), for gen9abil's own state (g9.h: G9).
 6. Booster Energy (item 769) gets a hold effect of its own (gen9abil_data.BOOSTER_EFFECT).
Space: 0x09E33000..0x09E38000, in the zero run 0x09E10044..0x09E40000 (free and watched: NOTES, *Free space left
after Kitakami*; gen9anim has 0x09E38000..0x09E3C000, Kitakami 0x09E40000..): all zero, and no aligned word anywhere
in the ROM holds an address in it (both checked here; the run's other stretches have chance values in pictures
pointing in).
"""
import os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen9abil_data as D

B = 0x08000000
BASE, SPACE_END = 0x09E33000, 0x09E38000
# engine routine -> (gen9abil's wrapper, the bl sites and pointer words that reach it today)
WRAP = {
    0x09D45F8C: ("w_ability_battle_effects", None),
    0x09D5F8A0: ("w_get_attack_stat", None),
    0x09D5FCA8: ("w_get_def_stat", None),
    0x09D5F0CC: ("w_apply_base_power_modifiers", None),
    0x09D5FF3C: ("w_damage_calc", None),
    0x09D5E3F0: ("w_get_speed", None),
    0x09D4B950: ("w_cant_poison", None),
    0x09D4BC04: ("w_cant_become_burned", None),
    0x09D4BA44: ("w_cant_fall_asleep", None),
    0x09D4BB54: ("w_cant_become_paralyzed", None),
    0x09D4BCB8: ("w_cant_become_freezed", None),
    0x09D58438: ("w_moveeffect_set_status", None),
    0x09D54074: ("w_atk84_jumpifcannotsleep", None),       # command 0x84: its word in the command table
    0x0805385C: ("w_atkB2_set_perishsong", None),          # command 0xB2, the game's own Cmd_trysetperishsong
    0x09D459B4: ("w_check_field_for_ability", None),
    0x09D61934: ("w_check_ability_with_mold", None),
    0x09D45A0C: ("w_has_ability_effect_inalternate", None),
    0x09D499F4: ("w_get_first_to_strike", None),
    0x09D57E9C: ("w_atk6A_remove_item", None),             # command 0x6A: its word in the command table
    0x09D6C698: ("w_change_stats", None),
    0x09D4B6D4: ("w_type_effectiveness_calc", None),
    0x09D6A3F8: ("w_atk07_final_dmg_calc", None),          # command 7: its word in the command table
    0x09D4F308: ("w_can_switch", None),
    0x0805112C: ("w_atk8F_forcerandomswitch", None),       # command 0x8F, the game's own Cmd_forcerandomswitch
    0x09D66EE0: ("w_findability_in_table", None),
}
# battle scripts of the engine's whose one call is pointed at one of ours: (address of the word, what it holds now,
# our script)
SCRIPT_WORDS = [
    (0x09D06CA8, 0x09D06E08, "BS_G9_INTIMIDATE_STAT"),     # Intimidate's loop: the stat change for each target
    (0x09D05563, 0x082D8A4E, "BS_G9_TAILWIND"),            # Tailwind's script (effect 140): its last goto
]
# the engine's table of routines scripts call by number (callasm, 0x83): 220 entries; the command reads entry n at
# [literal] + 12 + 4n, the literal at CALLASM_WORD
CALLASM_WORD, CALLASM_TABLE, CALLASM_COUNT = 0x09D686F0, 0x09D79EAC, 220
PLEDGE_WORD = 0x09D68524
# where a bl into the engine can come from: the game's code and the upper ROM's code (the hack's, ours)
CODE = [(0x08000000, 0x08200000), (0x08D00000, 0x0A000000)]
STRINGS_WORD, STRINGS_TABLE, STRINGS_COUNT = 0x09D4A204, 0x09D744E4, 315
ALLOC_AT, ALLOC_WAS = 0x09D49230, bytes.fromhex("8c204000")      # movs r0, #0x8c; lsls r0, r0, #1 (0x118 bytes)
SHARPNESS_LITERAL, SHARPNESS_TABLE = 0x09D5F368, 0x09D743F2      # apply_base_power_modifiers' literal, the list
# gen9abil_data.FORBIDDEN's lists: how many literals outside our code hold each (the engine's, and two in the
# hack's own code just before it, 0x09D35D3C and 0x09D37854)
FORBIDDEN_HELD = {0x09D79E36: 1, 0x09D79E1A: 3, 0x09D79E74: 4, 0x09D79E58: 3}
ALIAS_WORD = 0x09AB7EB8                                         # gen9.s's literal naming its alias list
ABILITY_TABLE_LITERAL = 0x09D73A94                               # the species' ability table, in the engine's lookup
NAME_BLANK = bytes.fromhex("144511001445110014451100ff")         # an unused id's name and text pointer
DESC_BLANK = 0x00114514
ITEMS_HEADER, ITEM_SIZE = 0x1C8, 44
SPECIES = 1408                                                   # gen9rest's slots
# the engine routines gen9abil calls or stands in front of: their first bytes (he_syms.s, he.ld)
EXPECT = [
    (0x09D45F8C, "f0b51500ea228bb01e0010ab1b88"),      # ability_battle_effects
    (0x09D45AEC, "37b5074c0d004100095b"),              # has_ability_effect
    (0x09D459B4, "f7b506000f0000240192114b"),          # check_field_for_ability
    (0x09D497E8, "70b50d0000210400fcf77cf9"),          # check_ability
    (0x09D5F8A0, "f0b514000c2242438bb00593"),          # get_attack_stat
    (0x09D5FCA8, "f0b514000c224243874b87b0"),          # get_def_stat
    (0x09D5F0CC, "f0b589b004930eab1b8806930c23"),      # apply_base_power_modifiers
    (0x09D5FF3C, "f0b51500002289b01e000eab1f88"),      # damage_calc
    (0x09D5E3F0, "004b1847"),                          # get_speed: gen9.s's jump to g9_speed
    (0x09D6199C, "104af8b5031e934203d0"),              # photon_geyser_special
    (0x09D67CF4, "1e22837893438370054b"),              # reset_terrains
    (0x09D67D1A, "feff10b50121"),                      # terrains_get_turns (from 0x09D67D1C)
    (0x09D73AB0, "014b4000c1527047"),                  # RecordAbilityBattle
    (0x09D4B0A4, "10b5fff7e1ff0248"),                  # bs_execute
    (0x09D68700, "5822424370b5224b"),                  # get_item_effect
    (0x09D5B0D4, "094a127802410300"),                  # is_bank_present
    (0x09D45B84, "002210b503210d20"),                  # weather_abilities_effect
    (0x09D458E8, "f7b52e4b1d780400"),                  # mimicry_change
    (0x09D5E2E2, "002806d080234143"),                  # apply_modifier
    (0x09D5E32C, "054b4900ca5c5918"),                  # apply_statboost
    (0x09D4B164, "10b5124b1b68dc7c"),                  # get_attacking_move_type
    (0x09D4B950, "f8b5170058224a43"),                  # cant_poison
    (0x09D4BC04, "58224243274b9b18"),                  # cant_become_burned
    (0x09D4BA44, "58234343f7b53d4a"),                  # cant_fall_asleep
    (0x09D4BB54, "58224243264b9b18"),                  # cant_become_paralyzed
    (0x09D4BCB8, "58224243304b9b18"),                  # cant_become_freezed
    (0x09D58438, "f0b585b003925822"),                  # moveeffect_set_status
    (0x09D54074, "f7b5354d28680130"),                  # atk84_jumpifcannotsleep
    (0x09D6A330, "5822424370b5134b"),                  # affected_by_substitute
    (0x09D66EE0, "054a0b88934204d0"),                  # findability_in_table
    (0x09D6224C, "1d4b1a68aa2370b5"),                  # check_weather_trio
    (0x09D5A300, "5822424370b51b4b"),                  # cant_become_confused
    (0x09D5F094, "0c2343430b4ad018"),                  # does_move_make_contact
    (0x09D4B1C4, "10b5582444430c4a"),                  # is_of_type
    (0x09D499F4, "f7b50e008e490b5c"),                  # get_first_to_strike
    (0x09D61934, "f8b50a4f3c783970"),                  # check_ability_with_mold
    (0x09D45A0C, "f0b585b001930aab"),                  # has_ability_effect_inalternate
    (0x0805385C, None),                                # Cmd_trysetperishsong (the game's)
    (0x09D4AFD8, "10b50f282ad8"),                      # get_battle_bank
    (0x09D57E9C, "f7b5224d2b685878"),                  # atk6A_remove_item
    (0x09D6C698, "f0b585b0ae4f0191"),                  # change_stats
    (0x09D4B6D4, "f0b51d0087b00cab"),                  # type_effectiveness_calc
    (0x09D6A3F8, "f0b5b84b1b6885b0"),                  # atk07_final_dmg_calc
    (0x09D65488, "0c220a4b10b51c88"),                  # callasm 117: bug_bite_set_berry_eaten
    (0x09D6A004, "7fb50c22844b1888"),                  # callasm 158: the Berry's effect, as Bug Bite eats it
    (0x09D06DD0, "89415f60d009"),                      # BS_CHANGE_ATK_STAT_SELFINFLICTED
    (0x09D4F308, "f0b5424d85b00822"),                  # can_switch
    (0x0805112C, "f0b557464e464546"),                  # Cmd_forcerandomswitch (the game's)
    (0x09D6593C, None),                                # callasm 153: several stats, prepared
    (0x09D676AC, None),                                # callasm 154: ... and changed
    (0x09D06C7E, "839600b76cd009392000"),              # BS_INTIMIDATE
    (0x09D06E08, "89005f60d009"),                      # BS_CHANGE_DEF_STAT
    (0x09D06D73, "1095011240003c"),                    # BS_PRINT_DEF_ABILITY
    (0x09D06D7A, "1032021240003c"),                    # BS_PRINT_SCR_ACTIVE_ABILITY
    (0x09D06DEC, "3a41736dd00989405f60d009"),                # BS_DEF_ABILITY_CHANGES_DEF_STAT, then the self-inflicted one
    (0x09D0700C, "392000417a6dd00983c100"),                          # BS_GRASSY_SURGE
    (0x09D070FF, "3a41816dd009173c"),                  # BS_ATK_ABILITY_STATUS
    (0x09D0711E, "3a41736dd0091094011240"),            # BS_MUMMY
    (0x09D074E1, "030239100041ec6dd009"),             # BS_IMMUNE_STAT_RAISE
    (0x09D074F0, "0302391000830900108f01"),            # BS_IMMUNE
    (0x09D06FE8, "83c1000a10fd0112400083"),            # Electric Surge's script after its ability line
    (0x09D07274, "10f000450a0b000000000a41"),          # Drought's script after its ability line
]


def u16(rom, a):
    return struct.unpack_from("<H", rom, a - B)[0]


def u32(rom, a):
    return struct.unpack_from("<I", rom, a - B)[0]


def bl_target(rom, a):
    h1, h2 = u16(rom, a), u16(rom, a + 2)
    if (h1 & 0xF800) != 0xF000 or (h2 & 0xF800) != 0xF800:
        return None
    off = ((h1 & 0x7FF) << 12) | ((h2 & 0x7FF) << 1)
    if off & 0x400000:
        off -= 0x800000
    return a + 4 + off


def bl_encode(at, to):
    off = to - (at + 4)
    assert -0x400000 <= off < 0x400000 and not off & 1, "bl from %08X cannot reach %08X" % (at, to)
    off = (off >> 1) & 0x3FFFFF
    return struct.pack("<HH", 0xF000 | (off >> 11), 0xF800 | (off & 0x7FF))


def encode_text(text):
    import build
    return build.encode(text)


def read_sym():
    syms, meta = {}, {}
    for line in open(os.path.join(HERE, "gen9abil.sym")):
        p = line.split()
        if p[0].startswith("@"):
            meta[p[0][1:]] = p[1]
        else:
            syms[p[0]] = int(p[1], 16)
    return syms, meta


def calls_to(rom, target):
    """every bl in the code regions that lands on target, and every word in the ROM that holds target | 1"""
    bls = []
    for lo, hi in CODE:
        for a in range(lo, hi - 4, 2):
            if (rom[a - B + 1] & 0xF8) == 0xF0 and bl_target(rom, a) == target:
                bls.append(a)
    word = struct.pack("<I", target | 1)
    words = [B + m.start() for m in re.finditer(re.escape(word), bytes(rom)) if m.start() % 4 == 0]
    return bls, words


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    syms, meta = read_sym()
    blob = open(os.path.join(HERE, "gen9abil.bin"), "rb").read()
    import hashlib
    assert hashlib.sha1(blob).hexdigest() == meta["sha1"], "gen9abil.bin is not the build gen9abil.sym describes"
    assert syms["w_ability_battle_effects"] == BASE, "the build is not linked at BASE"

    for a, hexs in EXPECT:
        if hexs:
            want = bytes.fromhex(hexs)
            assert bytes(rom[a - B:a - B + len(want)]) == want, "the engine at %08X is not as expected" % a
    assert bytes(rom[ALLOC_AT - B:ALLOC_AT - B + 4]) == ALLOC_WAS, "the battle state's allocation (already applied?)"
    assert u32(rom, STRINGS_WORD) == STRINGS_TABLE, "the engine's string table has moved"
    for k in range(STRINGS_COUNT):
        assert B <= u32(rom, STRINGS_TABLE + 4 * k) < B + len(rom), "string %X" % (0x17C + k)
    assert not B <= u32(rom, STRINGS_TABLE + 4 * STRINGS_COUNT) < B + len(rom), "the string table is longer"

    # ---- the space
    assert set(rom[BASE - B:SPACE_END - B]) == {0}, "gen9abil's space is not blank"
    held = [B + o for o in range(0, len(rom), 4) if BASE <= struct.unpack_from("<I", rom, o)[0] < SPACE_END]
    assert not held, "words point into gen9abil's space: %s" % ["%08X" % a for a in held]

    calls = {t: calls_to(rom, t) for t in WRAP}       # before anything is written

    # ---- 1. ids, names, texts
    names, descs = u32(rom, B + 0x1C0) - B, u32(rom, B + 0x1C4) - B
    count = 1793
    def name_at(i):
        return bytes(rom[names + 13 * i:names + 13 * i + 13])
    table = u32(rom, ABILITY_TABLE_LITERAL) - B
    renumber = {}
    for key, (new, name, text) in D.ABILITIES.items():
        assert new in D.FREE_IDS, "%s: %X is not one of the free ids" % (key, new)
        nm = encode_text(name)[:-1]
        assert len(nm) <= 12, "%s: name too long" % key
        entry = nm + b"\xff" + bytes(12 - len(nm))
        old = [i for i in range(0x100, count) if i != new and name_at(i) == entry]
        assert len(old) <= 1, "%s: the name is at %s" % (key, old)
        if old:
            renumber[old[0]] = new
    # the ids taken must be blank now, or hold a stand-in that moves away (Guard Dog 0x127, ThermalExch. 0x129)
    for key, (new, name, text) in D.ABILITIES.items():
        assert name_at(new) == NAME_BLANK or new in renumber, "%s: id %X is not free" % (key, new)
    species = SPECIES
    changed_rows = 0
    for s in range(species):
        row = list(struct.unpack_from("<HHH", rom, table + 6 * s))
        new_row = [renumber.get(a, a) for a in row]
        if new_row != row:
            assert s >= 1200, "species %d has a Gen 9 stand-in id" % s
            struct.pack_into("<HHH", rom, table + 6 * s, *new_row)
            changed_rows += 1
    left = [s for s in range(species) for a in struct.unpack_from("<HHH", rom, table + 6 * s) if a in renumber]
    assert not left, "stand-in ids left in rows %s" % left[:5]

    # the code, then the texts and the string table after it
    end = BASE + len(blob)
    rom[BASE - B:end - B] = blob
    def put(data, align=4):
        nonlocal end
        end = (end + align - 1) & ~(align - 1)
        at = end
        rom[at - B:at - B + len(data)] = data
        end = at + len(data)
        assert end <= SPACE_END, "gen9abil's space is full"
        return at
    for key, (new, name, text) in D.ABILITIES.items():
        nm = encode_text(name)[:-1]
        rom[names + 13 * new:names + 13 * new + 13] = nm + b"\xff" + bytes(12 - len(nm))
        struct.pack_into("<I", rom, descs + 4 * new, put(encode_text(text), 1))

    # ---- 2. the stand-ins off
    alias = u32(rom, ALIAS_WORD)
    assert u16(rom, alias) == 295 and u16(rom, alias + 2) == 39, "gen9's alias list is not where gen9.s names it"
    struct.pack_into("<HH", rom, alias - B, 0, 0)

    # ---- 4. the messages
    words = [u32(rom, STRINGS_TABLE + 4 * k) for k in range(STRINGS_COUNT)]
    for k, (name, text) in enumerate(D.STRINGS):
        words.append(syms["g9_string_%d" % k])
    assert len(words) == D.FIRST_STRING - 0x17C + len(D.STRINGS)
    new_table = put(b"".join(struct.pack("<I", w) for w in words))
    struct.pack_into("<I", rom, STRINGS_WORD - B, new_table)

    # ---- the routines scripts call by number: a longer copy, ours from CALLASM_FIRST on
    assert u32(rom, CALLASM_WORD) == CALLASM_TABLE - 12, "the callasm table is not where the command reads it"
    # the same word also sits in get_move_from_pledge's pool, which reads the three Pledge moves just before the
    # table (+4..+9): that one stays
    held = [B + m.start() for m in re.finditer(re.escape(struct.pack("<I", CALLASM_TABLE - 12)), bytes(rom))]
    assert held == [PLEDGE_WORD, CALLASM_WORD], "the callasm table is held elsewhere too: %s" % ["%08X" % a for a in held]
    routines = [u32(rom, CALLASM_TABLE + 4 * k) for k in range(CALLASM_COUNT)]
    assert all(B <= r < B + len(rom) for r in routines) and D.CALLASM_FIRST == CALLASM_COUNT
    routines += [syms[n] | 1 for n in D.CALLASM]
    calltable = put(b"".join(struct.pack("<I", w) for w in routines))
    struct.pack_into("<I", rom, CALLASM_WORD - B, calltable - 12)

    # ---- the lists of abilities moves cannot touch: longer copies with the Gen 9 ones. Every word outside our code
    # holding a list's address points at its copy. Ours keep the lists' own addresses: w_findability_in_table knows
    # a list by it (some routines reach one from another address plus an offset, which no word holds)
    for at, first, count, keys in D.FORBIDDEN:
        old = [u16(rom, at + 2 * k) for k in range(count + 1)]
        assert tuple(old[:len(first)]) == first and old[count] == 0xFFFF, "the ability list at %08X" % at
        new = old[:count] + [D.ABILITIES[k][0] for k in keys]
        assert len(set(new)) == len(new)
        copy = put(b"".join(struct.pack("<H", a) for a in new + [0xFFFF]), 2)
        held = [m.start() for m in re.finditer(re.escape(struct.pack("<I", at)), bytes(rom))
                if m.start() % 4 == 0 and not BASE <= B + m.start() < BASE + len(blob)]
        assert len(held) == FORBIDDEN_HELD[at], "the ability list at %08X is held at %s" % (
            at, ["%08X" % (B + o) for o in held])
        for o in held:
            struct.pack_into("<I", rom, o, copy)

    # ---- Sharpness's slicing moves: a longer copy with the Gen 9 ones
    assert u32(rom, SHARPNESS_LITERAL) == SHARPNESS_TABLE, "Sharpness's move list is not where the engine reads it"
    held = [B + m.start() for m in re.finditer(re.escape(struct.pack("<I", SHARPNESS_TABLE)), bytes(rom))]
    assert held == [SHARPNESS_LITERAL], "Sharpness's move list is held elsewhere too"
    slicing = []
    while u16(rom, SHARPNESS_TABLE + 2 * len(slicing)) != 0xFFFF:
        slicing.append(u16(rom, SHARPNESS_TABLE + 2 * len(slicing)))
    assert len(slicing) == 19, "Sharpness's move list is not the engine's own"
    move_names = u32(rom, B + 0x148) - B
    for name in D.SLICING_NEW:
        nm = encode_text(name)
        ids = [i for i in range(1024) if bytes(rom[move_names + 13 * i:move_names + 13 * i + len(nm)]) == nm]
        assert len(ids) == 1 and ids[0] not in slicing, "slicing move %s: %s" % (name, ids)
        slicing.append(ids[0])
    struct.pack_into("<I", rom, SHARPNESS_LITERAL - B,
                     put(b"".join(struct.pack("<H", m) for m in slicing + [0xFFFF]), 2))

    # ---- 5. the battle state 0x40 bytes longer: movs r0, #0xac (0x158 = 0xac << 1)
    rom[ALLOC_AT - B:ALLOC_AT - B + 2] = bytes([0xAC, 0x20])

    # ---- 6. Booster Energy's hold effect
    items = u32(rom, B + ITEMS_HEADER) - B
    he = items + ITEM_SIZE * D.BOOSTER_ENERGY + 0x12
    assert rom[he] == 0, "Booster Energy already has a hold effect"
    assert all(rom[items + ITEM_SIZE * i + 0x12] != D.BOOSTER_EFFECT for i in range(800)), "hold effect in use"
    rom[he] = D.BOOSTER_EFFECT

    # ---- 3. the calls (found on the input, before our own code was there)
    report = []
    for target, (wrapper, expect) in WRAP.items():
        to = syms[wrapper]
        bls, wrds = calls[target]
        for a in bls:
            rom[a - B:a - B + 4] = bl_encode(a, to)
        for a in wrds:
            struct.pack_into("<I", rom, a - B, to | 1)
        report.append("%08X -> %s: %d bl, %d words" % (target, wrapper, len(bls), len(wrds)))
        if expect is not None:
            assert (len(bls), len(wrds)) == expect, "%08X: %d bl, %d words, expected %s" % (
                target, len(bls), len(wrds), expect)
    for at, was, script in SCRIPT_WORDS:
        assert u32(rom, at) == was, "the script word at %08X is %08X" % (at, u32(rom, at))
        struct.pack_into("<I", rom, at - B, syms[script])
    open(outp, "wb").write(rom)
    print("gen9abil: code %08X..%08X, %d ability rows renumbered (%d stand-in ids), strings from %X" % (
        BASE, end, changed_rows, len(renumber), D.FIRST_STRING))
    for line in report:
        print("  " + line)


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
