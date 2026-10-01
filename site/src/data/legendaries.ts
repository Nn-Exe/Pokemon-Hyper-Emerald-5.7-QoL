// Every legendary and mythical Pokémon: where it is and what gates it.
// source 'rom'       the encounter (species and level) was found in the map scripts of v5.7 bugfix 2
//        'community' the trigger or route comes from player guides for v5.5-5.6, not re-verified in v5.7

export type Legend = {
  name: string;
  /** species shown as icons; names from src/data/species.json */
  mons: string[];
  level: string;
  where: string;
  source: 'rom' | 'community';
};

export type LegendGroup = { key: string; legends: Legend[] };

export const LEGEND_GROUPS: LegendGroup[] = [
  {
    key: 'hoenn',
    legends: [
      {
        name: 'Regirock, Regice and Registeel',
        mons: ['Regirock', 'Regice', 'Registeel'],
        level: '40',
        where:
          'Desert Ruins, Island Cave and Ancient Tomb, after the Sealed Chamber puzzle (Wailord first, Relicanth last, as in vanilla). Volo sells goods in the Sealed Chamber later.',
        source: 'rom',
      },
      {
        name: 'Magearna',
        mons: ['Magearna'],
        level: '30 / 50',
        where:
          'Devon Corp, Rustboro: the door behind the receptionist (the “Basement” map). Serena’s Master Class battle is tied to it.',
        source: 'rom',
      },
      {
        name: 'Type: Null',
        mons: ['Type: Null'],
        level: '50',
        where: 'The same Devon basement lab as Magearna. Silvally’s memory discs are sold as items.',
        source: 'rom',
      },
      {
        name: 'Jirachi',
        mons: ['Jirachi'],
        level: '30',
        where: 'Artisan Cave (the Mossdeep script is the same event).',
        source: 'rom',
      },
      {
        name: 'Shaymin',
        mons: ['Shaymin'],
        level: '30',
        where:
          'Flower Paradise; a Route 101 script also spawns one. The Gracidea flower event in Floaroma is Sinnoh lore only.',
        source: 'rom',
      },
      { name: 'Victini', mons: ['Victini'], level: '30', where: 'Sootopolis City event.', source: 'rom' },
      {
        name: 'Diancie',
        mons: ['Diancie'],
        level: '30',
        where: 'Desert Underpass (the Fossil Maniac’s tunnel). A Diancie Doll item also exists.',
        source: 'rom',
      },
      { name: 'Marshadow', mons: ['Marshadow'], level: '30', where: 'Altering Cave.', source: 'rom' },
      {
        name: 'Hoopa',
        mons: ['Hoopa'],
        level: '50',
        where: 'Depths of the Abandoned Ship. Its rings later open the Sea Spirit’s Den.',
        source: 'rom',
      },
      {
        name: 'Keldeo',
        mons: ['Keldeo'],
        level: '30',
        where: 'Victory Road. A tutor teaches Secret Sword for the Resolute Form.',
        source: 'rom',
      },
      {
        name: 'Cobalion, Terrakion and Virizion',
        mons: ['Cobalion', 'Terrakion', 'Virizion'],
        level: '70',
        where: 'A Victory Road area; Blake says he “brought them here to train”.',
        source: 'rom',
      },
      {
        name: 'Rayquaza',
        mons: ['Rayquaza'],
        level: 'Story',
        where:
          'Sky Pillar during the Delta Episode (bring the Mach Bike). It joins you whether you catch it or knock it out. Dragon Ascent can be re-taught at the Meteor Falls shrine.',
        source: 'rom',
      },
    ],
  },
  {
    key: 'postgame',
    legends: [
      {
        name: 'Cosmog, Solgaleo and Lunala',
        mons: ['Cosmog', 'Solgaleo', 'Lunala'],
        level: '15',
        where:
          'Meteor Falls Draconid cave after the Delta Episode; a second from Ghetsis’s Giant Chasm. Evolves at 65: by day for Solgaleo, by night for Lunala. Needed for the Ultra gates until you get the Ultra Suit.',
        source: 'rom',
      },
      {
        name: 'Groudon',
        mons: ['Groudon'],
        level: '70',
        where: 'Terra Cave (Route 115) after Maxie’s Ultra League mission. Holds the Red Orb.',
        source: 'rom',
      },
      {
        name: 'Kyogre',
        mons: ['Kyogre'],
        level: '70',
        where: 'Marine Cave (Route 125) after Archie. Holds the Blue Orb.',
        source: 'rom',
      },
      { name: 'Cresselia', mons: ['Cresselia'], level: '50', where: 'Mt. Pyre Ultra Wormhole.', source: 'rom' },
      { name: 'Genesect', mons: ['Genesect'], level: '50', where: 'New Mauville.', source: 'rom' },
      {
        name: 'Mewtwo',
        mons: ['Mewtwo'],
        level: '50',
        where: 'Cerulean Cave, past the Rocket executives. An Armored Mewtwo event comes later.',
        source: 'rom',
      },
      {
        name: 'Giratina',
        mons: ['Giratina'],
        level: '80',
        where:
          'The Distortion World (holding a Griseous Orb), after Cyrus’s rental battle in the Hoenn post-game. If you leave it, go back in from the islet on Route 129, or through the passages that open at the Spear Pillar and Sendoff Spring during Lost Artifacts.',
        source: 'rom',
      },
      {
        name: 'Kyurem',
        mons: ['Kyurem'],
        level: '50',
        where: 'Giant Chasm after Ghetsis, who also hands over the DNA Splicers.',
        source: 'rom',
      },
      {
        name: 'Reshiram and Zekrom',
        mons: ['Reshiram', 'Zekrom'],
        level: '50',
        where: 'Dragonspiral Tower, reached through Icirrus City.',
        source: 'rom',
      },
      { name: 'Volcanion', mons: ['Volcanion'], level: '50', where: 'Nebel Cave (the Route 116 wormhole).', source: 'rom' },
      {
        name: 'Floette (Eternal Flower)',
        mons: ['Floette (Eternal Flower)'],
        level: '1',
        where: 'Timeless Woods, through the same Route 116 wormhole.',
        source: 'rom',
      },
      {
        name: 'Zygarde',
        mons: ['Zygarde'],
        level: '70',
        where: 'Terminus Cave. Zygarde Cells and Professor Sycamore’s shop handle its forms.',
        source: 'rom',
      },
      {
        name: 'Xerneas and Yveltal',
        mons: ['Xerneas', 'Yveltal'],
        level: '50',
        where:
          'Allearth Forest and Allearth Lake (the Kalos forest) after Lysandre. Earlier releases of the hack itself crashed here; use bugfix 2.',
        source: 'rom',
      },
      {
        name: 'Manaphy',
        mons: ['Manaphy'],
        level: '30',
        where: 'The Deep Sea map (the Lilycove lab and Dive quest that also leads to Shadow Lugia).',
        source: 'rom',
      },
      {
        name: 'Articuno, Zapdos and Moltres',
        mons: ['Articuno', 'Zapdos', 'Moltres'],
        level: '50',
        where:
          'The mysterious island (Lyra’s mis-given ticket). Articuno and Zapdos are scripted at Navel Rock; Moltres is in the same chain.',
        source: 'rom',
      },
      {
        name: 'Ho-Oh',
        mons: ['Ho-Oh'],
        level: '—',
        where: 'Summit of the island’s Bell Tower after the bird battles; Ethan entrusts it to you.',
        source: 'community',
      },
      {
        name: 'Shadow Lugia',
        mons: ['Shadow Lugia'],
        level: '70',
        where:
          'Attacks you on the island and flees, leaving a stone. Later: the Lilycove lab quest, Dive with a Grass type to find it, raise it to 40 with Ancient Power, then the Ultra maze event and the Silver Airship at Mossdeep. The scripted battle itself is in the Abandoned Ship.',
        source: 'community',
      },
      {
        name: 'Raikou, Entei and Suicune',
        mons: ['Raikou', 'Entei', 'Suicune'],
        level: '—',
        where: 'The Johto slice during the Ultra-cave story; needed before Ho-Oh.',
        source: 'community',
      },
      {
        name: 'Mew',
        mons: ['Mew'],
        level: '—',
        where: 'Old Sea Map from the villa NPC on Steven’s Island, then sail from Lilycove to Faraway Island.',
        source: 'community',
      },
      {
        name: 'The four Tapus',
        mons: ['Tapu Koko', 'Tapu Lele', 'Tapu Bulu', 'Tapu Fini'],
        level: '—',
        where:
          'The Tapu island trials: Tapu Bulu with Nanu, then Hala in Dewford (Tapu Koko), Hapu in Slateport (Tapu Fini) and Olivia in Mossdeep (Tapu Lele).',
        source: 'community',
      },
      {
        name: 'Necrozma',
        mons: ['Necrozma'],
        level: '50',
        where:
          'Ultra Space Zero, after all 18 Z-Crystals and Faba. The N-Solarizer and N-Lunarizer come from Faba’s research.',
        source: 'rom',
      },
      {
        name: 'Ultra Beasts',
        mons: ['Nihilego', 'Kartana', 'Xurkitree', 'Blacephalon', 'Guzzlord', 'Pheromosa', 'Celesteela', 'Buzzwole', 'Stakataka', 'Poipole'],
        level: '50–70',
        where:
          'Nihilego (EV Training Cave, Pacifidlog); Kartana, Xurkitree, Blacephalon, Guzzlord, Pheromosa, Celesteela and Buzzwole (Ultra Space maps); Stakataka (Meteor Falls Ultra Space, level 70); Poipole is a gift at Mt. Pyre. Bring Beast Balls.',
        source: 'rom',
      },
      {
        name: 'Eternatus',
        mons: ['Eternatus'],
        level: '50',
        where: 'Ultra Space, after Leon is found wounded (the World Championship Island chapter).',
        source: 'rom',
      },
      {
        name: 'Meltan and Melmetal',
        mons: ['Meltan', 'Melmetal'],
        level: '5',
        where:
          'Meltan is a level-5 gift in Lilycove City. Guides differ on the trigger: New Mauville per English players, the Lilycove hotel designer after completing the Hoenn Pokédex per Chinese guides.',
        source: 'community',
      },
      {
        name: 'Deoxys, Latias and Latios',
        mons: ['Deoxys', 'Latias', 'Latios'],
        level: '—',
        where:
          'Deoxys is faced in space at the end of the Delta Episode. For the Eon duo only Mystery Gift-style tickets are referenced in the text; community videos show them after the League.',
        source: 'community',
      },
    ],
  },
  {
    key: 'sinnoh',
    legends: [
      {
        name: 'Heatran',
        mons: ['Heatran'],
        level: '30',
        where: 'A Mt. Coronet opening reached from Snowpoint via Route 216, after the Sinnoh League.',
        source: 'rom',
      },
      {
        name: 'Uxie, Mesprit and Azelf',
        mons: ['Uxie', 'Mesprit', 'Azelf'],
        level: '50',
        where: 'The “Test of Heart” caves at the three lakes.',
        source: 'rom',
      },
      {
        name: 'Darkrai',
        mons: ['Darkrai'],
        level: '50',
        where:
          'Lost Tower, at the end of the Solaceon nightmare quest: Dawn’s Lunar Wing wakes the sleeping woman, and the presence blocking the tower lifts.',
        source: 'rom',
      },
      {
        name: 'Zeraora',
        mons: ['Zeraora'],
        level: '50',
        where: 'Scripted on Route 101 in the ROM; guides place its trigger in a Hearthome building.',
        source: 'rom',
      },
      { name: 'Zarude', mons: ['Zarude'], level: '50', where: 'Floaroma Town.', source: 'rom' },
      {
        name: 'Tornadus, Thundurus and Landorus',
        mons: ['Tornadus', 'Thundurus', 'Landorus'],
        level: '—',
        where:
          'The Valley Windworks researcher: track roaming rain (Tornadus) and storms (Thundurus) with the News Tracker, then pray at the Celestic shrine with both for Landorus.',
        source: 'rom',
      },
      {
        name: 'Enamorus',
        mons: ['Enamorus'],
        level: '50',
        where: 'Cogita on Firespit Island summons it once you have caught the other three.',
        source: 'rom',
      },
      {
        name: 'Meloetta',
        mons: ['Meloetta'],
        level: '50',
        where: 'Joins you after the Hearthome Contest Spectacular. A Relic Song tutor exists.',
        source: 'rom',
      },
      {
        name: 'Glastrier, Spectrier and Calyrex',
        mons: ['Glastrier', 'Spectrier', 'Calyrex'],
        level: '50',
        where: 'Crown Shrine (the radish field in the snow); the priest gives the bond rope.',
        source: 'rom',
      },
      {
        name: 'Zacian',
        mons: ['Zacian'],
        level: '50',
        where: 'Iron Island, after the gatekeeper and the two heroes.',
        source: 'rom',
      },
      {
        name: 'Zamazenta',
        mons: ['Zamazenta'],
        level: '—',
        where: 'Paired with Zacian’s story; not found as a separate script.',
        source: 'community',
      },
      {
        name: 'Regieleki and Regidrago',
        mons: ['Regieleki', 'Regidrago'],
        level: '50',
        where:
          'Ruins of Decision: Regieleki with an Electric type in the party (Route 209 ruins); Regidrago with a Flygon holding the Draco Plate in slot one (Lake Acuity ruins).',
        source: 'rom',
      },
      {
        name: 'Regigigas',
        mons: ['Regigigas'],
        level: '60',
        where: 'Snowpoint Temple, once the three golems light the statue.',
        source: 'community',
      },
      {
        name: 'Galarian Articuno, Zapdos and Moltres',
        mons: ['Galarian Articuno', 'Galarian Zapdos', 'Galarian Moltres'],
        level: '—',
        where: 'The Sea Spirit’s Den, through Hoopa’s ring with Professor Oak, after the Kanto birds.',
        source: 'rom',
      },
      {
        name: 'Kubfu and Urshifu',
        mons: ['Kubfu', 'Urshifu (Single Strike)', 'Urshifu (Rapid Strike)'],
        level: '5',
        where:
          'A level-5 gift at the Battle Frontier, where you choose Kubfu or Rockruff. Urshifu itself appears on Maylene’s and Crasher Wake’s teams.',
        source: 'rom',
      },
      {
        name: 'Dialga and Palkia',
        mons: ['Dialga', 'Palkia'],
        level: '50 / 80',
        where:
          'Both at once (level 50, a Double Battle) in the Space-Time Rift behind the Spear Pillar altar, with all 17 Plates. Or pick one (level 80) in the Unown Ruins, reached through the tablet wall of the hidden ruins off Route 210 with all 17 Plates; that choice is gone once you have entered the ruins in Celestic Town.',
        source: 'rom',
      },
      {
        name: 'Arceus',
        mons: ['Arceus'],
        level: '80',
        where:
          'The Mountain Top above Team Rainbow Rocket’s castle, once you have battled Giratina and hold all 17 Plates. It joins you whether you catch it or win.',
        source: 'rom',
      },
    ],
  },
];

export const LEGEND_COUNT = LEGEND_GROUPS.reduce((n, g) => n + g.legends.length, 0);
