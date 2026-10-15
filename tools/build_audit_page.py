"""Build tools/romdata/out/content-audit.html: everything the game's scripts can switch on, and what the Journal covers.

    python tools/romdata/flag_audit.py       (needs out/script_index.json from scripts.py)
    python tools/build_audit_page.py

The curated part (side content outside the Journal) is written here by hand from reading the scripts; the
tables underneath are generated from tools/romdata/out/flag_audit.json. A local page for whoever works on the
Journal; the guide site shows the curated list as its Side Content guide (tools/build_site_content.py reads
CURATED from here).
"""
import collections, html, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIT = os.path.join(ROOT, "tools", "romdata", "out", "flag_audit.json")


def esc(s):
    return html.escape(s, quote=False)


def clean(t):
    t = t.replace("→", " ").replace("←", " ").replace("↓Y", "")
    t = re.sub(r"\{FC\d\d\}|\{FD05\}|\{5D\}|↓.", "", t)
    return t.replace("{PLAYER}", "you").replace("{STR_VAR_1}", "…").replace("{STR_VAR_2}", "…")


def area(m):
    return re.sub(r" \(\d+/\d+\)", "", m)


# Side content the Journal does not follow, by theme. (where, what, flags)
CURATED = [
    ("Hisuian trades", "Six people who slipped through time offer Hisuian forms in trade. None is in the Journal.", [
        ("Rustboro City", "Hisuian Zorua (a gift fox turned them into something else)", "0x0099"),
        ("Mauville City", "Hisuian Voltorb (\"a Poké Ball-like Pokémon\")", "0x4327"),
        ("Lavaridge Town", "Hisuian Growlithe (\"all I remember is living in Hisui\")", "0x4328"),
        ("Fortree City", "Hisuian Sneasel (\"this weasel is different\")", "0x009B"),
        ("Safari Zone", "Hisuian Qwilfish (\"thousand-needle fish\")", "0x009A"),
        ("Route 119", "White-Striped Basculin (\"feeding the Phantom Fish\")", "0x4329"),
    ]),
    ("Gift Pokémon", "Handed to you by a script.", [
        ("Littleroot Town", "Return the Mega Bracelet: a choice of Giratina Lv80, Kyurem, Xerneas or Yveltal Lv50", "0x4311"),
        ("Hearthome City", "Meloetta Lv50, after its stage performance", "0x4055"),
        ("Lilycove City (museum, 1F)", "Beat Blue: all nine of her Galar Pokémon Lv15 (Galarian Mr. Mime, Stunfisk, "
         "Weezing and Corsola, Indeedee, Eiscue, Morpeko, Glastrier, Spectrier); what the party cannot hold goes to "
         "the PC. Before the sidefix patch (2026-10-15) she stood inside the wall and could not be reached", "0x40B9"),
        ("Lilycove City (Cove Lily Motel)", "Meltan Lv5, from the Game Designer once every Hoenn Pokédex Pokémon "
         "is caught", "0x40CA"),
        ("Battle Frontier", "Beat Palmer (0x40F2), then: Rockruff Lv5 for a 35-win singles streak in the Battle "
         "Tower, Kubfu Lv5 (with the Dark and Water Scrolls) for a 35-win doubles streak, a second Kubfu for all "
         "seven Gold Symbols", "0x42DB, 0x42DC, 0x42DD"),
        ("Ultra Space", "Poipole Lv5", "0x41BD"),
        ("Timeless Woods", "Wimpod Lv10", "0x41B7"),
        ("Hearthome City / Bell Tower", "Let's Go Eevee or Pikachu Lv5", "0x4307, 0x40CB"),
        ("Lavaridge Town", "Pikachu Belle Lv5", "0x408F"),
        ("Rustboro City", "A fossil of your choice revived at Lv20", "0x010B"),
        ("Valley Windworks", "Drifloon Lv15", "0x42DE-0x42E1"),
        ("Steven's Island", "Magikarp Lv1: pay the demon soul in the top room of Steven's residence 1,996 and "
         "beat him (trainer 1161). Before the sidefix patch (2026-10-15) he shared his flag with Dawn's battle on Route 210",
         "0x4552"),
        ("Mossdeep City", "Beldum Lv5 (Steven's house)", "0x012A"),
    ]),
    ("Legendary and mythical battles outside the Journal", "Scripted one-off encounters.", [
        ("Abandoned Ship", "Dark Lugia Lv70", "0x4095"),
        ("Artisan Cave", "Jirachi Lv30", "0x413A"),
        ("Ultra Space", "Eternatus Lv50", "0x4085"),
        ("Desert Ruins / Island Cave / Ancient Tomb", "Regirock, Regice, Registeel Lv40", "0x01BB-0x01BD"),
        ("Regigigas Temple", "Regigigas Lv60", "0x4065, 0x413B"),
        ("Terra Cave / Marine Cave", "Groudon, Kyogre Lv70", "0x01BF, 0x01BE"),
        ("Navel Rock / Route 128", "Articuno, Zapdos, Moltres (Lv40, and Lv50 versions)", "0x4070-0x4072, 0x40A4-0x40A6, 0x40AC"),
        ("Ancient Retreat", "The God of Forms Lv70 (two more encounters)", "0x0276, 0x0278"),
        ("Celestic Town", "Dialga or Palkia Lv80 (a second encounter besides the Journal's)", "0x40B1"),
        ("Mountain Top", "Arceus Lv80 (the fight before the catch)", "0x4080, 0x42FA"),
        ("Faraway Island / Southern Island", "Mew; the Eon dream (\"All dreams are but another reality\")", "0x01C7, 0x00CE"),
        ("Old Chateau", "Gengar Lv66 in the cursed statue, Rotom Lv15 in the TV", "0x432D, 0x4269"),
    ]),
    ("Other regions' starters", "Hidden one-off battles: Lv5 first stages and Lv50 final stages.", [
        ("Lv5", "Snivy (Petalburg Woods), Oshawott (Abandoned Ship), Litten (Meteor Falls), Grookey (Mt. Silver), "
                "Scorbunny (Lake of Despair), Chespin (Remote Island), Chikorita (Timeless Woods), "
                "Cyndaquil (Bell Tower), Totodile (Whirl Islands)", ""),
        ("Lv50", "Greninja, Inteleon (Artisan Cave), Delphox (Couriway Town), Emboar (Cerulean Cave), "
                 "Decidueye, Venusaur (Giant Chasm), Primarina, Torterra, Blastoise (Remote Island), "
                 "Charizard (Mt. Silver), Infernape (Whirl Islands), Empoleon (Underwater)", ""),
    ]),
    ("Strong one-off Pokémon", "Scripted battles, mostly post-game.", [
        ("Sinnoh Victory Road", "Hydreigon, Salamence, Dragonite, Metagross Lv80", "0x4249, 0x424B, 0x424C, 0x424F"),
        ("Sinnoh routes", "Gyarados (203), Milotic (204), Haxorus (210), Aggron (211), Tyranitar (Oreburgh Gate), "
                          "Lucario (Iron Island), Gallade and Gardevoir (Mt. Coronet) Lv80", ""),
        ("Sinnoh", "Leafeon (Eterna Forest), Glaceon (Route 217), Rotom (Eterna City) Lv50", ""),
        ("Unova / Kalos areas", "Garchomp (Desert Ruins), Volcarona Lv70, Zoroark (Magic Woods), Flygon, Aerodactyl Lv50", ""),
        ("Secret Bases", "Alolan Totem Pokémon Lv80, one per base (part of the Z-Crystal hunt the Journal names)", "0x4003-0x4011, 0x4140, 0x413F, 0x432C"),
    ]),
    ("Hidden powers", "Two secret trials that give your Pokémon a power, and what follows them.", [
        ("Route 112 (foot of Mt. Chimney, west side)", "A hidden cave into a sealed part of the Magma Hideout. "
         "Take TM53, then read the sign with a Typhlosion as your only Pokémon (nothing happens otherwise). "
         "Asked whether to leave, say No: Yes collapses the cave for good (0x42E2). The Crimson Apostle (a "
         "Flareon serving the Crimson Nova) then runs three rounds of hologram battles (trainers 1155-1157) and "
         "awakens the Burning Soul (0x4301); the cave collapses after that too. A lost round only blacks you out: "
         "the cave stays open and you start again from round 1. Needed for Ash's challenge. Lore: a Typhlosion trainer passed the same trial on Stark Mountain; "
         "Flint (Test of Heart) remembers a Johto girl's very fast Typhlosion.", "0x4297, 0x42E2, 0x4301"),
        ("Champion Island", "Beat Koga (trainer 1160): he gives his mark and points to a hidden village through "
         "the forest of Route 102.", "0x42FF"),
        ("Koga's Village (hidden, via Route 102)", "Elder Koga's succession trial: only one Greninja, some items "
         "banned, two stages (trainers 1159, 1158). Your Greninja gains its hero form, like Ash's.", "0x4300"),
        ("Littleroot Town (Prof. Birch's lab) / Route 101", "With the Hero Greninja (0x4300), the Burning Soul "
         "(0x4301) and Team Rainbow Rocket beaten (0x41D5), say yes to your rival's battle in the lab: Ash walks in "
         "and you all go to Route 101 for a 2-vs-2, you and your rival against Ash and a red-haired passerby "
         "(-Echo-), who drops a cartridge and a note. Without all three it is the rival's usual battle.", "0x4302"),
        ("Steven's Island", "The northeast corner of Steven's residence (its top room): -Echo- / -Hibiki- (trainer "
         "1016), there only after Ash's challenge; talking to her counts, the battle is optional. A book there by "
         "Gengyi Xiang adds entries as you earn each power.", "0x4303"),
    ]),
    ("Side stories", "Short scripted scenes and quests the Journal does not name.", [
        ("Route 102", "Red and Blue corner Buzzwole at an Ultra Wormhole", "0x42A3-0x42A6"),
        ("Terra Cave / Marine Cave", "A familiar voice losing to someone who controls the weather", "0x41DF, 0x41DE, 0x40F8"),
        ("Shoal Cave", "Tate and Liza against the Shadow Triad: take the last one", "0x42B7"),
        ("New Mauville", "Someone behind the generator trouble", "0x42B3"),
        ("Petalburg Woods", "A mysterious mentor who teaches you about battles (\"you were chosen by it\")", "0x4165"),
        ("Couriway Town", "The hotel: a talisman, a suite for ¥10,000, the furnace", "0x40A8, 0x41AC, 0x4145"),
        ("Mauville City", "Save the lady's Skitty; the bike exam with Renli (Eterna City)", "0x42A7, 0x42A9, 0x4264, 0x4265"),
        ("Old Chateau", "The murder on the TV and the grudge in the statue (open-ended)", "0x4266-0x4269, 0x432D"),
        ("Meteor Temple / Meteor Falls", "Zinnia's grandmother on the Draconids; a former Dragon Tamer", "0x4139, 0x432A"),
        ("Sinnoh League", "Lucas and Barry greet you; Barry waits in Twinleaf Town for a battle", "0x40CE"),
        ("Route 110 / Desert Underpass", "A timed cycling run; a vibration in the depths", "0x40CC, 0x40CD"),
    ]),
    # v1.9: the Paldea area (patches/paldea, story.py); the Quest Log's ten Area Zero rows (patches/gen9journal)
    ("Area Zero", "Extras of the Paldea area behind Mossdeep City's black hole; each is a row of the Quest Log's "
     "Side Content chapter.", [
        ("Research Stations No. 1-4", "Play the professors' recorded log on the left counter of each station: No. 1 "
         "on the crater wall's middle ledge, No. 2 the house on the shelf below the stairs into the crater, No. 3 the "
         "house on the knoll in the east of the crater, No. 4 above the waterfall (surf across the pond and climb "
         "it). All four, then a word with Penny, unlock the Zero Lab's door", "0x43B8-0x43BB"),
        ("Arven's picnic, by the big lake", "Beat the Titans in the den on the crater's west side - Great Tusk in the "
         "past, Iron Treads in the future - and bring Arven both Sour Herba Mystica: his sandwiches get Koraidon "
         "and Miraidon up again", "0x43B5, 0x43B6"),
        ("Research Station No. 3", "After the story Nemona lives here: beat her in a rematch", "0x43E4"),
        ("The Sealed Vault", "After the story, behind the Crystal Cavern's second cave mouth: slide over the mirror "
         "floor and pull its three stakes, marked with a bundle of tablets (Wo-Chien), a vessel on three legs "
         "(Ting-Lu) and a string of curved beads (Chi-Yu); each frees the legend behind its crystal",
         "0x43D8-0x43DA"),
        ("The crater, past and future", "A Booster Energy in an item ball in each era's crater", "0x43DC, 0x43DD"),
    ]),
]


def page(a):
    flags = a["flags"]
    kinds = collections.Counter(f["kind"] for f in flags)
    inj = collections.Counter(f["kind"] for f in flags if f["journal"])
    body = []
    body.append('<h2 id="summary">In numbers</h2><table class="plain"><tr><th>Kind</th><th>Flags set by scripts</th>'
                '<th>Followed by the Journal</th></tr>')
    names = {"encounter": "Scripted battles (legendaries, set pieces)", "gift": "Gift Pokémon",
             "item": "Items given by script", "trainer": "Trainer battles", "event": "Story events and switches"}
    for k in ("encounter", "gift", "item", "trainer", "event"):
        body.append("<tr><td>%s</td><td>%d</td><td>%d</td></tr>" % (names[k], kinds[k], inj[k]))
    body.append("</table>")

    body.append('<h2 id="side">Side content outside the Journal</h2>')
    for title, blurb, rows in CURATED:
        body.append("<h3>%s</h3><p>%s</p><table class='plain'>" % (esc(title), esc(blurb)))
        for where, what, fl in rows:
            body.append("<tr><td>%s</td><td>%s</td><td class='src'>%s</td></tr>" % (esc(where), esc(what), esc(fl)))
        body.append("</table>")

    body.append('<h2 id="battles">Every scripted battle and gift</h2><p>From the scripts; "J" is the Journal '
                'objective that covers it.</p><table class="plain"><tr><th>Where</th><th>Kind</th><th>Pokémon</th>'
                '<th>Flag</th><th>J</th></tr>')
    for f in sorted((f for f in flags if f["kind"] in ("encounter", "gift")), key=lambda f: f["maps"][0]):
        body.append("<tr><td>%s</td><td>%s</td><td>%s</td><td class='src'>%s</td><td>%s</td></tr>" % (
            esc(area(f["maps"][0])), f["kind"], esc(clean(", ".join(f["wild"] + f["mons"]))[:160]), f["flag"],
            f["journal"] or ""))
    body.append("</table>")

    body.append('<h2 id="events">Every other story flag the Journal does not follow, by area</h2><p>Mostly the '
                'original Emerald: cutscenes that play once, NPCs who appear or leave, one-time gifts of items and '
                'TMs. The first line each script says is shown; flags with no text are switches (doors, hidden '
                'NPCs).</p>')
    ev = collections.defaultdict(list)
    for f in flags:
        if f["kind"] in ("event", "item") and not f["journal"]:
            ev[area(f["maps"][0])].append(f)
    for m in sorted(ev, key=lambda k: (-len(ev[k]), k)):
        body.append("<details><summary>%s <span class='src'>(%d)</span></summary><ul>" % (esc(m), len(ev[m])))
        for f in ev[m]:
            body.append("<li><span class='src'>%s</span> %s</li>" % (f["flag"], esc(clean(f["text"])[:160]) or "<em>switch</em>"))
        body.append("</ul></details>")

    body.append('<h2 id="unread">Scripts the tool could not read to the end</h2><table class="plain">')
    for p in a["problems"]:
        body.append("<tr><td>%s</td><td>%s</td><td class='src'>%s</td></tr>" % (
            esc(area(p["map"])), esc(p["source"][:50]), esc("; ".join(p["problem"]))))
    body.append("</table><p>Two are Battle Frontier move tutors, three point at data rather than a script "
                "(Distortion World, Ultra Alliance), three use commands this hack added, and one is a Terra Cave "
                "object whose Groudon battle is another script. None of them sets a flag of its own.</p>")
    return "\n".join(body)


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Content Audit — Hyper Emerald v5.7 Guide</title>
<meta name="description" content="Every flag the game's scripts set, sorted by what it does, and what the Journal covers.">
<style>
body { max-width: 70rem; margin: 2rem auto; padding: 0 1rem; font: 16px/1.5 system-ui, sans-serif; }
.src { color: #667; font-size: .9em; }
table.plain { border-collapse: collapse; width: 100%; margin: .5rem 0 1.25rem; }
table.plain td, table.plain th { text-align: left; vertical-align: top; padding: .3rem .5rem; border-bottom: 1px solid var(--line, rgba(127,127,127,.2)); }
details { margin: .25rem 0; }
details ul { margin: .25rem 0 .75rem; }
</style>
</head>
<body>
<div class="shell">
<main class="content">
<div class="prose wide">
<p class="eyebrow">Reference</p>
<h1>Content audit</h1>
<p class="lede">Every flag a script in the game sets - {COUNT} of them, over every map - sorted by what it does, with
what the Journal already follows. Read from the ROM's scripts, so it lists what the game can do, not what a
wiki says. Battle-engine behaviour (level caps, difficulty rules) is code, not script, and is not here.</p>
{BODY}
<p class="src">Generated by <code>tools/romdata/flag_audit.py</code> and <code>tools/build_audit_page.py</code>.</p>
</div>
</main>
</div>
</body>
</html>
"""

if __name__ == "__main__":
    a = json.load(open(AUDIT, encoding="utf-8"))
    out = os.path.join(ROOT, "tools", "romdata", "out", "content-audit.html")
    open(out, "w", encoding="utf-8").write(TEMPLATE.replace("{BODY}", page(a)).replace("{COUNT}", str(len(a["flags"]))))
    print("wrote %s" % os.path.relpath(out, ROOT))
