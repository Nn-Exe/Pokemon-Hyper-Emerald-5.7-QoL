"""Display names for the guide site.

The ROM's species-name table holds 10 characters a name and gives every alternate form its base species' name
(Alolan Raichu is "Raichu", Mega Charizard X is "Charizard"), so the site cannot tell them apart from the table
alone. This maps a species id to the name a player would use. Forms were identified from their menu icons
(tools/build_sprites.py) and, where two looked alike, from the teams that use them (Maylene's Urshifu knows
Wicked Blow, Wake's Surging Strikes; Giovanni's two Mewtwo hold "Mewtwo Armor" and "RevengerArmor").

display_name(sid, rom_name) falls back to the ROM's own name.
"""

TYPES = ["Fighting", "Flying", "Poison", "Ground", "Rock", "Bug", "Ghost", "Steel", "Fire", "Water", "Grass",
         "Electric", "Psychic", "Ice", "Dragon", "Dark", "Fairy"]

# names the 10-character table cuts short
FULL = {
    "Corvknight": "Corviknight", "Corvsquire": "Corvisquire", "Centskorch": "Centiskorch",
    "Basclegion": "Basculegion", "Blacphalon": "Blacephalon", "Stonjournr": "Stonjourner",
    "Poltegeist": "Polteageist", "Baraskewda": "Barraskewda", "Fletchindr": "Fletchinder",
    "Crabminble": "Crabominable", "Dark Lugia": "Shadow Lugia", "Pika Belle": "Pikachu Belle",
    "Pikachu-LG": "Let's Go Pikachu", "Eevee-LG": "Let's Go Eevee", "Kyurem-W": "White Kyurem",
    "Kyurem-B": "Black Kyurem", "Floette-E": "Floette (Eternal Flower)", "Dusk Mane": "Dusk Mane Necrozma",
    "Dawn Wings": "Dawn Wings Necrozma", "U-Necrozma": "Ultra Necrozma", "Calyrex-IR": "Calyrex (Ice Rider)",
    "Calyrex-SR": "Calyrex (Shadow Rider)",
}

FORMS = {
    # 252-276: the unused slots between Celebi and Treecko hold the Gigantamax forms
    252: "Gigantamax Charizard", 253: "Gigantamax Blastoise", 254: "Gigantamax Venusaur",
    255: "Gigantamax Pikachu", 256: "Gigantamax Machamp", 257: "Gigantamax Kingler", 258: "Gigantamax Lapras",
    259: "Gigantamax Butterfree", 260: "Gigantamax Meowth", 261: "Gigantamax Eevee", 262: "Gigantamax Snorlax",
    263: "Gigantamax Gengar", 264: "Gigantamax Orbeetle", 265: "Gigantamax Corviknight",
    266: "Gigantamax Coalossal", 267: "Gigantamax Hatterene", 268: "Gigantamax Grimmsnarl",
    269: "Gigantamax Flapple", 270: "Gigantamax Appletun", 271: "Gigantamax Melmetal",
    272: "Gigantamax Sandaconda", 273: "Gigantamax Copperajah", 274: "Gigantamax Duraludon",
    275: "Gigantamax Toxtricity", 276: "Gigantamax Toxtricity",
    # Alolan forms
    856: "Alolan Rattata", 857: "Alolan Raticate", 858: "Alolan Raichu", 859: "Alolan Sandshrew",
    860: "Alolan Sandslash", 861: "Alolan Vulpix", 862: "Alolan Ninetales", 863: "Alolan Diglett",
    864: "Alolan Dugtrio", 865: "Alolan Meowth", 866: "Alolan Persian", 867: "Alolan Geodude",
    868: "Alolan Graveler", 869: "Alolan Golem", 870: "Alolan Grimer", 871: "Alolan Muk",
    872: "Alolan Exeggutor", 873: "Alolan Marowak",
    # Hisuian forms and other Legends: Arceus species
    891: "Basculegion ♂", 892: "Basculegion ♀", 893: "Hisuian Goodra", 894: "Hisuian Decidueye",
    895: "Hisuian Typhlosion", 896: "Hisuian Samurott", 897: "Shaymin (Sky Forme)",
    898: "Giratina (Origin Forme)", 899: "Tornadus (Therian)", 900: "Thundurus (Therian)",
    901: "Landorus (Therian)",
    # Mega Evolutions and Primal Reversions
    902: "Mega Venusaur", 903: "Mega Charizard X", 904: "Mega Charizard Y", 905: "Mega Blastoise",
    906: "Mega Beedrill", 907: "Mega Pidgeot", 908: "Mega Alakazam", 909: "Mega Slowbro", 910: "Mega Gengar",
    911: "Mega Kangaskhan", 912: "Mega Pinsir", 913: "Mega Gyarados", 914: "Mega Aerodactyl",
    915: "Mega Mewtwo X", 916: "Mega Mewtwo Y", 917: "Mega Ampharos", 918: "Mega Steelix", 919: "Mega Scizor",
    920: "Mega Heracross", 921: "Mega Houndoom", 922: "Mega Tyranitar", 923: "Mega Sceptile",
    924: "Mega Blaziken", 925: "Mega Swampert", 926: "Mega Gardevoir", 927: "Mega Sableye", 928: "Mega Mawile",
    929: "Mega Aggron", 930: "Mega Medicham", 931: "Mega Manectric", 932: "Mega Sharpedo",
    933: "Mega Camerupt", 934: "Mega Altaria", 935: "Mega Banette", 936: "Mega Absol", 937: "Mega Glalie",
    938: "Mega Salamence", 939: "Mega Metagross", 940: "Mega Latias", 941: "Mega Latios",
    942: "Primal Kyogre", 943: "Primal Groudon", 944: "Mega Rayquaza", 945: "Mega Lopunny",
    946: "Mega Garchomp", 947: "Mega Lucario", 948: "Mega Abomasnow", 949: "Mega Gallade",
    950: "Mega Audino", 951: "Mega Diancie",
    # other alternate forms
    952: "Deoxys (Attack)", 953: "Deoxys (Defense)", 954: "Deoxys (Speed)",
    955: "Rotom (Heat)", 956: "Rotom (Wash)", 957: "Rotom (Frost)", 958: "Rotom (Fan)", 959: "Rotom (Mow)",
    960: "Aegislash (Blade)", 961: "Darmanitan (Zen Mode)", 962: "Wishiwashi (School)",
    963: "Greninja (Battle Bond)", 964: "Meowstic ♀", 965: "Meloetta (Pirouette)",
    966: "Basculin (Blue-Striped)", 967: "Zygarde (Complete)", 968: "Zygarde (10%)", 969: "Hoopa (Unbound)",
    970: "Lycanroc (Midnight)", 971: "Minior (Core)", 972: "Oricorio (Pom-Pom)", 973: "Oricorio (Pa'u)",
    974: "Oricorio (Sensu)", 975: "Genesect (Drive)", 976: "Genesect (Drive)", 977: "Genesect (Drive)",
    978: "Genesect (Drive)", 979: "Burmy (Sandy Cloak)", 980: "Burmy (Trash Cloak)",
    981: "Wormadam (Sandy Cloak)", 982: "Wormadam (Trash Cloak)", 983: "Cherrim (Sunshine)",
    984: "Shellos (East Sea)", 985: "Gastrodon (East Sea)", 986: "Keldeo (Resolute)", 987: "Frillish ♀",
    988: "Jellicent ♀", 989: "Basculin (White-Striped)",
    # 990-993: the half fossils of Galar, still named in Chinese in the ROM (化石雷鸟 / 巨龙 / 鳃鱼 / 海兽)
    990: "Fossilized Bird", 991: "Fossilized Drake", 992: "Fossilized Fish", 993: "Fossilized Dino",
    997: "Mimikyu (Busted)", 998: "Lycanroc (Dusk)", 999: "Pyroar ♀", 1000: "Magearna (Original Color)",
    1002: "Hisuian Sliggoo", 1003: "Gigantamax Rillaboom", 1004: "Gigantamax Cinderace",
    1005: "Gigantamax Inteleon", 1006: "Gigantamax Drednaw", 1007: "Gigantamax Urshifu",
    1008: "Gigantamax Urshifu", 1009: "Zygarde (Power Construct)", 1010: "Rockruff (Own Tempo)",
    1011: "Ash-Greninja", 1012: "Gigantamax Garbodor", 1013: "Gigantamax Alcremie",
    1014: "Gigantamax Centiskorch", 1015: "Hisuian Qwilfish", 1017: "Hisuian Zorua", 1018: "Hisuian Zoroark",
    1019: "Hisuian Growlithe", 1020: "Hisuian Arcanine", 1021: "Hisuian Voltorb", 1022: "Hisuian Electrode",
    1024: "Enamorus (Therian)", 1026: "Dialga (Origin Forme)", 1027: "Palkia (Origin Forme)",
    1028: "Galarian Slowpoke", 1029: "Galarian Slowbro", 1030: "Galarian Slowking", 1031: "Galarian Moltres",
    1032: "Galarian Zapdos", 1033: "Galarian Articuno", 1035: "Urshifu (Single Strike)",
    1036: "Urshifu (Rapid Strike)", 1057: "Xerneas (Active Mode)", 1058: "Marshadow (Zenith)",
    1062: "Hisuian Sneasel", 1064: "Hisuian Braviary", 1065: "Unfezant ♀",
    1066: "Solgaleo (Radiant Sun)", 1067: "Lunala (Full Moon)", 1076: "Ash's Pikachu",
    1077: "Cramorant (Gulping)", 1078: "Cramorant (Gorging)", 1080: "Galarian Yamask",
    1081: "Galarian Mr. Mime", 1082: "Galarian Stunfisk", 1083: "Galarian Weezing", 1084: "Galarian Corsola",
    1085: "Indeedee ♂", 1086: "Eiscue (Noice Face)", 1096: "Hisuian Avalugg", 1097: "Armored Mewtwo",
    1101: "Galarian Zigzagoon", 1102: "Galarian Linoone", 1104: "Galarian Ponyta", 1105: "Galarian Rapidash",
    1107: "Galarian Meowth", 1108: "Galarian Farfetch'd", 1118: "Armored Mewtwo (Revenger)",
    1175: "Hisuian Lilligant", 1178: "Indeedee ♀", 1179: "Morpeko (Hangry)",
    1193: "Zacian (Crowned Sword)", 1194: "Zamazenta (Crowned Shield)", 1195: "Eternamax Eternatus",
    1196: "Galarian Darumaka", 1197: "Galarian Darmanitan", 1198: "Galarian Darmanitan (Zen Mode)",
}
for _i, _t in enumerate(TYPES):
    FORMS[874 + _i] = "Arceus (%s)" % _t
    FORMS[1040 + _i] = "Silvally (%s)" % _t

# forms that could not be told apart from their icon keep the ROM's name with this note
UNSURE = {1091, 1106}


def display_name(sid, rom_name):
    if sid in FORMS:
        return FORMS[sid]
    if rom_name.startswith("{CN") or not rom_name or rom_name == "?":
        return "Species #%d" % sid
    name = FULL.get(rom_name, rom_name)
    if sid in UNSURE:
        return name + " (alt. form)"
    return name
