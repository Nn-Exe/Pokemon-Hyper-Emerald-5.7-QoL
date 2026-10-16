"""Text fixes in place (Hyper Emerald v5.7): same-length word swaps, re-laid-out lines, and lines too wide for the box.
usage: python textfix_patch.py <in.gba> <out.gba>

Each fix replaces a word inside one of the game's own texts with another of exactly the same length, so nothing
moves and no pointer changes. The patcher checks the old bytes at the address and that the word occurs nowhere else.

BREAKS are the translated lines wider than the 216-px message box (the translation wrapped at 34 letters, not at a
width): past the edge a line wraps round and draws over its own start. Each is one page of a text, its line breaks
moved: only spaces and breaks swap places (0x00, 0xFE new line, 0xFA scroll), so the text keeps its length and its
address. A page's first break is \\n and the later ones \\l, as in the game's own texts. Lines with {PLAYER} fit the
widest 7-letter name. The page must occur once in the text at the address (from there up to the 0xFF).
REWRITE pages may be shorter; the bytes left over become 0xFF.
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "translation"))
from inserter import ENC

FIXES = [
    # (address, old, new, where)
    (0x098208B4, "emmited", "emitted", "Sky Pillar summit, the meteorite reacting to Rayquaza (script 0x0982060F)"),
]

# Texts laid out again in place: the same words, new line breaks, never longer than before (the rest of the old
# text's bytes become 0xFF). Each is (address, its lines now, its lines after, where); a line is (text, the break
# after it: 0xFE new line, 0xFA scroll, 0xFB new page, 0xFF end).
RELAYOUT = [
    (0x0983D5AE,
     [("This icy rock is emanating energy.", 0xFE), ("Certain Pokémon may react to it.  We have been chosen and gathered", 0xFE),
      ("together to change the world.", 0xFA), ("We cannot lose!", 0xFF)],
     [("This icy rock is emanating energy.", 0xFE), ("Certain Pokémon may react to it.", 0xFB),
      ("We have been chosen and gathered", 0xFE), ("together to change the world.", 0xFB), ("We cannot lose!", 0xFF)],
     "Shoal Cave's icy rock sign: two sentences ran into one line too long for the box"),
]

# (address of the text, the page now, the page after, where). Found and measured by tools/text_overflow.py: every
# text a script shows with msgbox, message or trainerbattle, measured with the game's font widths (0x086542E4).
BREAKS = [
    (0x0820D08E, "You should visit the Weather Institute and ask around!",
     "You should visit the Weather Institute\\nand ask around!",
     "Slateport Harbor, the sailor by Captain Stern (288 px)"),
    (0x0832A5D8, "3. Every party Pokémon must be different.\\n4. Legendaries can’t be used.",
     "3. Every party Pokémon must be\\ndifferent.\\l4. Legendaries can’t be used.",
     "Petalburg Gym, Dad's Gym rules"),
    (0x08B77F84, "4. If you still receive no help\\nafter waiting, you may {F9E6}{F9E6}{F9E6}{F9E6} and reach {F9E6}{F9E6}\\lvia the trail, where {F9E6}{F9E6} staff will\\lhelp you.",
     "4. If you still receive no help\\nafter waiting, you may {F9E6}{F9E6}{F9E6}{F9E6} and reach\\l{F9E6}{F9E6} via the trail, where {F9E6}{F9E6} staff will\\lhelp you.",
     "the Mt. Coronet trail notice, rule 4 (map 35/10)"),
    (0x08F9BE66, "Or if you have news, they are to be\\nreported to the Chief Inspector of Devon\\lstanding in the lobby, for the time being.",
     "Or if you have news, they are to be\\nreported to the Chief Inspector\\lof Devon standing in the lobby,\\lfor the time being.",
     "a police officer, Anabel and Nanu in a meeting (map 35/40)"),
    (0x08F9C370, "Nanu: Oh, we meet again, {PLAYER}.\\nI knew you were special when we first met.",
     "Nanu: Oh, we meet again, {PLAYER}.\\nI knew you were special when we\\lfirst met.",
     "Nanu in Littleroot Town"),
    (0x08F9D15A, "“Remake” refers to an old gen of Pokémon\\ngames that was redone for a new platform.",
     "“Remake” refers to an old gen of Pokémon\\ngames that was redone\\lfor a new platform.",
     "what a remake is (map 36/87)"),
    (0x08F9E4CD, "These fluctuations appear and disappear,\\nand they’re still moving.",
     "These fluctuations appear and\\ndisappear, and they’re still moving.",
     "Route 119 house, the fluctuations"),
    (0x09813939, "The Interpol has gathered on this island…\\nthe situation seems very serious…",
     "The Interpol has gathered on\\nthis island…\\lthe situation seems very serious…",
     "the Interpol on the island (map 35/5)"),
    (0x09815DC0, "Sandgem Town\\n“The sandy town connected to the ocean.”",
     "Sandgem Town\\n“The sandy town connected\\lto the ocean.”",
     "Sandgem Town sign (map 36/1)"),
    (0x09821394, "{PLAYER} doesn’t have enough preparation…",
     "{PLAYER} doesn’t have enough\\npreparation…",
     "not prepared for Rayquaza (map 35/22)"),
    (0x09821444, "{PLAYER} used Rayquaza to explore freely!",
     "{PLAYER} used Rayquaza\\nto explore freely!",
     "exploring with Rayquaza (Mossdeep, map 35/41)"),
    (0x09822126, "Finally -\\nwith the efforts of {PLAYER} and Rayquaza,\\lHoenn’s Meteor crisis came to an end!",
     "Finally - with\\nthe efforts of {PLAYER} and Rayquaza,\\lHoenn’s Meteor crisis came to an end!",
     "the end of the Meteor crisis (map 35/51)"),
    (0x09825DE6, "Floaroma Town\\n“The town that smells vividly of flowers.”",
     "Floaroma Town\\n“The town that smells vividly\\lof flowers.”",
     "Floaroma Town sign (map 36/4)"),
    (0x09829842, "Cyrus: He’s good, not inferior to your son.",
     "Cyrus: He’s good,\\nnot inferior to your son.",
     "Cyrus (maps 35/9, 35/35)"),
    (0x0982B319, "Nurse Joy: Have a good rest{F9D3} Miss Lillie{F9D3}.",
     "Nurse Joy: Have a good rest{F9D3}\\nMiss Lillie{F9D3}.",
     "Nurse Joy and Lillie (map 35/48)"),
    (0x0982BE48, "{PLAYER} should ask Lillie about Cosmog… …",
     "{PLAYER} should ask Lillie\\nabout Cosmog… …",
     "ask Lillie about Cosmog (map 35/48)"),
    (0x0982C236, "Ash: Let’s battle again sometime, {PLAYER}!",
     "Ash: Let’s battle again sometime,\\n{PLAYER}!",
     "Ash after a battle (Ranking Hall, maps 34/24, 35/56)"),
    (0x0982DA44, "{FC0105}???: Hahaha! Yes!\\nRelease your Pokémon and obey the orders\\lof Aether’s new President, Lord Faba!",
     "{FC0105}???: Hahaha! Yes!\\nRelease your Pokémon and obey the\\lorders of Aether’s new President,\\lLord Faba!",
     "Faba's grunt on Route 107"),
    (0x0982E323, "Maybe you really are the Trainer engraved\\non the ancient stone tablet!",
     "Maybe you really are the Trainer\\nengraved on the ancient stone tablet!",
     "the Trainer on the stone tablet (map 35/49)"),
    (0x0982F7A0, "This cave’s full of debris and fossils…\\nbut we’re worried about the Pokémon here…",
     "This cave’s full of debris and fossils…\\nbut we’re worried about\\lthe Pokémon here…",
     "the cave full of fossils (map 35/61)"),
    (0x0982FDDF, "Stop blocking my path! I need to chase it!",
     "Stop blocking my path!\\nI need to chase it!",
     "Stop blocking my path (map 35/70)"),
    (0x09834E5B, "Speaking of which, I haven’t told you yet…\\nI am the Kahuna of the Ula’ula island,\\lin the region of Alola.",
     "Speaking of which,\\nI haven’t told you yet…\\lI am the Kahuna of the Ula’ula island,\\lin the region of Alola.",
     "Nanu, Kahuna of Ula'ula, Route 111"),
    (0x098352F0, "Nanu: It’s just up ahead…{PLAYER}…\\nyou should also come and see…\\lThe posture of an Alolan Island Guardian…",
     "Nanu: It’s just up ahead…{PLAYER}…\\nyou should also come and see…\\lThe posture of an Alolan Island\\lGuardian…",
     "Nanu, the Island Guardian (map 35/43)"),
    (0x09835582, "Now the Guardian Deity may recognize you,\\nthe next step is the most important\\land final ceremony…",
     "Now the Guardian Deity\\nmay recognize you,\\lthe next step is the most important\\land final ceremony…",
     "the Guardian Deity ceremony (map 35/43)"),
    (0x0983C70A, "Kanto’s former Champions - Red and Green,\\nhave found clues that seem to indicate\\lthat Faba is working with Team Rocket…",
     "Kanto’s former Champions -\\nRed and Green, have found clues\\lthat seem to indicate that Faba\\lis working with Team Rocket…",
     "Red and Green's clues (map 34/26)"),
    (0x0983F6EA, "However, those Pokémon didn’t fight back,\\nbut they were deeply hurt by the actions\\lof Humans, and left this land… …",
     "However, those Pokémon didn’t fight\\nback, but they were deeply hurt by the\\lactions of Humans, and left this land… …",
     "the Ecruteak story (map 35/75)"),
    (0x0983F6EA, "This is a story that has been passed down\\nbetween generations of Ecruteak City\\lfrom ancient times to the present day.",
     "This is a story that has been\\npassed down between generations\\lof Ecruteak City from ancient times\\lto the present day.",
     "the Ecruteak story (map 35/75)"),
    (0x09850871, "Steven: {PLAYER}…I have been looking forward\\nto the day when I can stand here again\\land see you…",
     "Steven: {PLAYER}…I have been looking\\nforward to the day when I can stand\\lhere again and see you…",
     "Steven (Battle Frontier Lounge 9, map 36/9)"),
    (0x0985459F, "September 3rd,\\nMewtwo’s power is beyond our imagination…\\lIf only we could control it…",
     "September 3rd,\\nMewtwo’s power is beyond\\lour imagination…\\lIf only we could control it…",
     "the Mewtwo diary, September 3rd (map 36/11)"),
    (0x09855C21, "Shadow Triad: That depends on your power.\\nOur Dark-type Pokémon are strong\\lagainst the type you use.",
     "Shadow Triad:\\nThat depends on your power.\\lOur Dark-type Pokémon are strong\\lagainst the type you use.",
     "the Shadow Triad, Shoal Cave ice room"),
    (0x098593CB, "Right, {PLAYER}, constantly going for more\\nPokémon combat power, but, as a person,\\lhow much progress have you made?",
     "Right, {PLAYER}, constantly going for\\nmore Pokémon combat power, but,\\las a person, how much progress\\lhave you made?",
     "Right, {PLAYER}, constantly going for more..."),
    (0x0985DC7A, "I thought Faba only wanted Necrozma, but…\\nnow that he’s united with Team Rocket,\\lyou need to be more careful.",
     "I thought Faba only wanted\\nNecrozma, but…\\lnow that he’s united with Team Rocket,\\lyou need to be more careful.",
     "Anabel on Faba and Team Rocket (map 35/54; the end of 0985DB6F, Ever Grande, too)"),
    (0x0985E3E8, "Anabel: Thanks for your hard work.\\nWhile we were busy with the Ultra\\lWormholes, something unrelated happened.",
     "Anabel: Thanks for your hard work.\\nWhile we were busy with the\\lUltra Wormholes, something\\lunrelated happened.",
     "Anabel, the Ultra Wormholes (map 35/21)"),
    (0x09860052, "He united evil organizations from all over\\nthe world and formed a huge force called\\lTeam Rainbow Rocket.",
     "He united evil organizations from all\\nover the world and formed a huge force\\lcalled Team Rainbow Rocket.",
     "Team Rainbow Rocket (map 36/91)"),
    (0x0986092B, "Anabel: {PLAYER}, you should also get ready.\\nHave you collected all 18 Z-Crystals?",
     "Anabel: {PLAYER},\\nyou should also get ready.\\lHave you collected all 18 Z-Crystals?",
     "Anabel, the 18 Z-Crystals (maps 36/91, 37/13, Magma Hideout)"),
    (0x09860F2D, "This time, the fluctuations are happening\\nin the icy room inside the Shoal Cave.",
     "This time, the fluctuations are\\nhappening in the icy room\\linside the Shoal Cave.",
     "the fluctuations in Shoal Cave (map 35/54)"),
    (0x098636A9, "Even Nebby got very close to you.\\nYou taught me that Pokémon battles don’t\\lnecessarily harm your Pokémon.",
     "Even Nebby got very close to you.\\nYou taught me that Pokémon battles\\ldon’t necessarily harm your Pokémon.",
     "Lillie and Nebby (map 36/80)"),
    (0x09866055, "Colress: It’s you, {PLAYER}, you’ve noticed\\nthis strange wall, haven’t you?",
     "Colress: It’s you, {PLAYER}, you’ve\\nnoticed this strange wall, haven’t you?",
     "Colress at the strange wall (map 35/49)"),
    (0x098672A2, "Maxie: Of course, we won’t make the same\\nmistakes again, and we have more help now.\\lBy the way, what about our invaders?",
     "Maxie: Of course, we won’t make the same\\nmistakes again, and we have more\\lhelp now.\\lBy the way, what about our invaders?",
     "Maxie and Matt (map 35/5)"),
    (0x098672A2, "Matt: Hehehe, {PLAYER} was led into our trap,\\nand won’t get out for a while, hehehe.",
     "Matt: Hehehe, {PLAYER} was led\\ninto our trap, and won’t get out\\lfor a while, hehehe.",
     "Maxie and Matt (map 35/5)"),
    (0x0986A98C, "What comes next won’t be so easy.\\nOur Boss has gained unprecedented power.\\lI can’t even judge how strong he is now.",
     "What comes next won’t be so easy.\\nOur Boss has gained\\lunprecedented power.\\lI can’t even judge how strong he is now.",
     "our Boss's unprecedented power"),
    (0x0986DE2D, "Mr. Steven said this battle is very\\nimportant. These potions won’t be enough.\\lYou must be fully prepared.",
     "Mr. Steven said this battle is very\\nimportant. These potions won’t be\\lenough. You must be fully prepared.",
     "Mr. Steven's potions (map 35/49)"),
    (0x098775F7, "The event, called the “Great Destruction”\\nwas caused by a Legendary Pokémon, who\\lcaused the forest to be full of death…",
     "The event, called\\nthe “Great Destruction” was caused\\lby a Legendary Pokémon, who caused\\lthe forest to be full of death…",
     "the Great Destruction (map 35/1)"),
    (0x098778AF, "Once you leave, the charm becomes invalid,\\nand you’ll have to do the check-in\\lceremo-…I mean, procedure again...",
     "Once you leave,\\nthe charm becomes invalid,\\land you’ll have to do the check-in\\lceremo-…I mean, procedure again...",
     "the check-in charm"),
    (0x0987BAEB, "After a fierce battle, Red got the Ultra\\nWormhole coordinates, and returned home...",
     "After a fierce battle, Red got the Ultra\\nWormhole coordinates,\\land returned home...",
     "Red's Ultra Wormhole coordinates (map 36/91)"),
    (0x09880930, "You may discover new things…\\nthings that you may have missed before……",
     "You may discover new things… things\\nthat you may have missed before……",
     "You may discover new things (map 36/22)"),
    (0x0988944D, "Van: I’ve heard two braves arrived here,\\nit will be a challenge among the two and me.",
     "Van: I’ve heard two braves arrived here,\\nit will be a challenge among\\lthe two and me.",
     "Van and the two braves (map 36/68)"),
    (0x098A3485, "Purple Sea? How do you know that…\\nthat name’s buried in the dust of history.",
     "Purple Sea? How do you know that… that\\nname’s buried in the dust of history.",
     "Abandoned Ship, Captain's Office scientist"),
    (0x098A3485, "This ship was once part of a great project,\\nnamed “Purple Sea”.",
     "This ship was once part of a great\\nproject, named “Purple Sea”.",
     "Abandoned Ship, Captain's Office scientist"),
    (0x098A3485, "Hmm? Spirits of Pokémon that passed away?\\nBut the project didn’t even start…\\lHow could Pokémon pass away from it?",
     "Hmm?\\nSpirits of Pokémon that passed away?\\lBut the project didn’t even start…\\lHow could Pokémon pass away from it?",
     "Abandoned Ship, Captain's Office scientist"),
    (0x098A6D39, "I’m sure you can use the power of Dynamax\\ncorrectly, so this is for you!",
     "I’m sure you can use the power of\\nDynamax correctly, so this is for you!",
     "the Dynamax gift (map 35/87)"),
    (0x098C4F01, "I put a lot of effort in getting them from\\nthe uncle in Slateport City.",
     "I put a lot of effort in getting them\\nfrom the uncle in Slateport City.",
     "the uncle in Slateport City (map 35/17)"),
    (0x09F7D710, "Faba still hasn’t appeared, but this time…\\nwell it’s different from the past events.",
     "Faba still hasn’t appeared,\\nbut this time… well it’s different\\lfrom the past events.",
     "Faba hasn't appeared"),
    (0x09F7E3E8, "{PLAYER}, you don’t have to put everything\\non your shoulders. Ah, it’s starting!",
     "{PLAYER}, you don’t have to put\\neverything on your shoulders.\\lAh, it’s starting!",
     "Ah, it's starting! (map 36/80)"),
    (0x09F7E6C2, "Lillie: I’ll take good care of my Mother.\\n{PLAYER}, keep working hard on your mission\\lto find Mr. Red.",
     "Lillie: I’ll take good care of my Mother.\\n{PLAYER}, keep working hard on your\\lmission to find Mr. Red.",
     "Lillie and her Mother (map 36/80)"),
    (0x09F7E75F, "This time, we must solve another incident.\\nNo matter how powerful our opponent is,\\lwe will not lose!",
     "This time, we must solve\\nanother incident.\\lNo matter how powerful our opponent is,\\lwe will not lose!",
     "we will not lose! (map 36/91)"),
]
REWRITE = [
    (0x08BBF100, "When gathers the three Pokémon,\\nthe king shall appear.",
     "When the three Pokémon gather,\\nthe king shall appear.{FF}",
     "the Regi statue's tablet"),
    (0x09837591, "{FC0104}-------------GAME OVER----------------",
     "{FC0104}-------------GAME OVER-------------",
     "GAME OVER (Lilycove Department Store rooftop)"),
]

CODES = {"{PLAYER}": b"\xFD\x01", "\\n": b"\xFE", "\\l": b"\xFA", "\\p": b"\xFB"}


def enc_text(s):
    """a page in this file's syntax: \\n \\l \\p, {PLAYER}, raw bytes as {FC0104} / {F9D3} / {FF}"""
    out, i = bytearray(), 0
    while i < len(s):
        if s[i] == "\\":
            out += CODES[s[i:i + 2]]; i += 2
        elif s[i] == "{":
            j = s.index("}", i) + 1
            out += CODES[s[i:j]] if s[i:j] in CODES else bytes.fromhex(s[i + 1:j - 1]); i = j
        else:
            out.append(ENC[s[i]]); i += 1
    return bytes(out)


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    enc = lambda s: bytes(ENC[c] for c in s)
    for addr, old, new, where in FIXES:
        a, b = enc(old), enc(new)
        assert len(a) == len(b), "%r -> %r changes the length" % (old, new)
        o = addr - 0x08000000
        assert bytes(rom[o:o + len(a)]) == a, "%08X does not read %r" % (addr, old)
        assert rom.count(a) == 1, "%r occurs more than once" % old
        rom[o:o + len(b)] = b
        print("%08X %r -> %r  (%s)" % (addr, old, new, where))
    for addr, old, new, where in RELAYOUT:
        a = b"".join(enc(t) + bytes([sep]) for t, sep in old)
        b = b"".join(enc(t) + bytes([sep]) for t, sep in new)
        assert len(b) <= len(a), "%08X: the new layout is longer" % addr
        o = addr - 0x08000000
        assert bytes(rom[o:o + len(a)]) == a, "%08X is not the text expected" % addr
        rom[o:o + len(a)] = b + bytes([0xFF]) * (len(a) - len(b))
        print("%08X laid out again  (%s)" % (addr, where))
    for same, lst in ((True, BREAKS), (False, REWRITE)):
        for addr, old, new, where in lst:
            a, b = enc_text(old), enc_text(new)
            o = addr - 0x08000000
            text = bytes(rom[o:rom.index(0xFF, o)])
            assert text.count(a) == 1, "%08X: the page %r is not in the text once" % (addr, old[:40])
            if same:
                assert len(a) == len(b) and all(x == y or (x in (0, 0xFE, 0xFA) and y in (0, 0xFE, 0xFA))
                                                for x, y in zip(a, b)), "%08X: more than the breaks change" % addr
            assert len(b) <= len(a), "%08X: the new page is longer" % addr
            p = o + text.index(a)
            rom[p:p + len(a)] = b + bytes([0xFF]) * (len(a) - len(b))
        print("%d pages %s" % (len(lst), "re-broken to fit the box" if same else "rewritten shorter"))
    open(outp, "wb").write(rom)


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
