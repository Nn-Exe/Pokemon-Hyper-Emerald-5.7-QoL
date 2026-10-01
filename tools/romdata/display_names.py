"""Item and move names as the guide site prints them.

The ROM's tables hold 12-13 characters a name, so long names are squeezed ("Scorch.Sands", "H. Duty Boots").
A reference site should print the name a player would search for. Items 754-767 are trainer-only copies of
ordinary held items whose names are still Chinese in the ROM (生命宝珠 = Life Orb ...).
"""

ITEMS = {
    "CharizarditeX": "Charizardite X", "CharizarditeY": "Charizardite Y", "Mewtownite Y": "Mewtwonite Y",
    "NeverMeltIce": "Never-Melt Ice", "SafetyGoggles": "Safety Goggles", "AdrenalineOrb": "Adrenaline Orb",
    "Terrain Ext.": "Terrain Extender", "Elect. Memory": "Electric Memory", "Psych Memory": "Psychic Memory",
    "AloraichiumZ": "Aloraichium Z", "PikashuniumZ": "Pikashunium Z", "GoldBottleCap": "Gold Bottle Cap",
    "RevengerArmor": "Revenger Armor", "H. Duty Boots": "Heavy-Duty Boots", "BlunderPolicy": "Blunder Policy",
    "Util Umbrella": "Utility Umbrella", "UnnamedStone": "Nameless Stone", "Adam.Crystal": "Adamant Crystal",
    "Black Augur.": "Black Augurite", "Weak Policy": "Weakness Policy", "EnergyPowder": "Energy Powder",
    "DeepSeaTooth": "Deep Sea Tooth", "DeepSeaScale": "Deep Sea Scale", "BlackGlasses": "Black Glasses",
    "MysticTicket": "Mystic Ticket", "AuroraTicket": "Aurora Ticket", "TwistedSpoon": "Twisted Spoon",
    "Lust. Globe": "Lustrous Globe",
}
ITEMS_BY_ID = {
    697: "Feraligatrite", 754: "Life Orb", 755: "Assault Vest", 756: "Eviolite", 757: "Rocky Helmet",
    758: "Light Ball", 759: "Leftovers", 760: "Scope Lens", 761: "Throat Spray", 762: "Mago Berry",
    763: "Wiki Berry", 764: "Aguav Berry", 765: "Tanga Berry", 766: "Weakness Policy", 767: "Focus Sash",
}

MOVES = {
    "Scorch.Sands": "Scorching Sands", "Surg.Strikes": "Surging Strikes", "Spring.Storm": "Springtide Storm",
    "MysticalFire": "Mystical Fire", "WaterShurikn": "Water Shuriken", "PhantomForce": "Phantom Force",
    "TrickorTreat": "Trick-or-Treat", "PetalBlizzrd": "Petal Blizzard", "DrainingKiss": "Draining Kiss",
    "CraftyShield": "Crafty Shield", "FlowerShield": "Flower Shield", "GrassTerrain": "Grassy Terrain",
    "MistyTerrain": "Misty Terrain", "Kings Shield": "King's Shield", "DiamondStorm": "Diamond Storm",
    "St. Eruption": "Steam Eruption", "H.Space Hole": "Hyperspace Hole", "AromaticMist": "Aromatic Mist",
    "EerieImpulse": "Eerie Impulse", "MagneticFlux": "Magnetic Flux", "Elec Terrain": "Electric Terrain",
    "Dazzle Gleam": "Dazzling Gleam", "BabyDollEyes": "Baby-Doll Eyes", "PowerUpPunch": "Power-Up Punch",
    "OblivionWing": "Oblivion Wing", "Prec. Blades": "Precipice Blades", "DragonAscent": "Dragon Ascent",
    "H.Space Fury": "Hyperspace Fury", "1st Impress.": "First Impression", "Baneful Bunk": "Baneful Bunker",
    "Spi. Shackle": "Spirit Shackle", "Sparkle Aria": "Sparkling Aria", "HiHorsepower": "High Horsepower",
    "CoreEnforcer": "Core Enforcer", "Clang Scales": "Clanging Scales", "DragonHammer": "Dragon Hammer",
    "Psychic Fang": "Psychic Fangs", "StompTantrum": "Stomping Tantrum", "Spect. Thief": "Spectral Thief",
    "Nat. Madness": "Nature's Madness", "PhotonGeyser": "Photon Geyser", "Spli. Splash": "Splishy Splash",
    "BouncyBubble": "Bouncy Bubble", "SparklySwirl": "Sparkly Swirl", "VeeveeVolley": "Veevee Volley",
    "D. Iron Bash": "Double Iron Bash", "DynamaxCanon": "Dynamax Cannon", "FishiousRend": "Fishious Rend",
    "Behem. Blade": "Behemoth Blade", "Break. Swipe": "Breaking Swipe", "StrangeSteam": "Strange Steam",
    "Met. Assault": "Meteor Assault", "Expand.Force": "Expanding Force", "ShellSideArm": "Shell Side Arm",
    "M. Explosion": "Misty Explosion", "Rising Volt.": "Rising Voltage", "TerrainPulse": "Terrain Pulse",
    "SkitterSmack": "Skitter Smack", "CorrosiveGas": "Corrosive Gas", "DualWingbeat": "Dual Wingbeat",
    "Jungle Heal.": "Jungle Healing", "DragonEnergy": "Dragon Energy", "Freeze Glare": "Freezing Glare",
    "Thunder.Kick": "Thunderous Kick", "GlacialLance": "Glacial Lance", "Ast. Barrage": "Astral Barrage",
    "Psyshi. Bash": "Psyshield Bash", "HeadlongRush": "Headlong Rush", "Mystic.Power": "Mystical Power",
    "MountainGale": "Mountain Gale", "VictoryDance": "Victory Dance", "BitterMalice": "Bitter Malice",
    "TripleArrows": "Triple Arrows", "Infer.Parade": "Infernal Parade", "Bleak. Storm": "Bleakwind Storm",
    "Wildb. Storm": "Wildbolt Storm", "Sands. Storm": "Sandsear Storm", "Lunar Bless.": "Lunar Blessing",
    "Hi Jump Kick": "High Jump Kick", "Selfdestruct": "Self-Destruct", "ThunderPunch": "Thunder Punch",
    "PoisonPowder": "Poison Powder", "ThunderShock": "Thunder Shock", "DynamicPunch": "Dynamic Punch",
    "DragonBreath": "Dragon Breath", "ExtremeSpeed": "Extreme Speed", "AncientPower": "Ancient Power",
    "SmellingSalt": "Smelling Salts", "FeatherDance": "Feather Dance", "Grasswhistle": "Grass Whistle",
    "B. Jealousy": "Burning Jealousy", "Cease. Edge": "Ceaseless Edge", "Clang. Soul": "Clangorous Soul",
    "False Surr.": "False Surrender", "LightOfRuin": "Light of Ruin", "Moon. Beam": "Moongeist Beam",
    "Sun. Strike": "Sunsteel Strike",
}


def item_name(item_id, rom_name):
    if item_id in ITEMS_BY_ID:
        return ITEMS_BY_ID[item_id]
    if rom_name.startswith("{CN"):
        return "Item #%d" % item_id
    return ITEMS.get(rom_name, rom_name)


def move_name(rom_name):
    return MOVES.get(rom_name, rom_name)
