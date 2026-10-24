// What the English + QoL patch adds, grouped the way a player meets it. Text follows the repository README.

export type Media = { clip: string } | { shot: string; alt: string; caption?: string };
export type Card = { title: string; text: string; how?: string };
export type FeatureSection = {
  id: string;
  nav: string;
  eyebrow: string;
  title: string;
  intro: string;
  cards: Card[];
  media: Media[];
  links: { href: string; label: string }[];
};

export const FEATURE_STATS = [
  { value: '~6,000', label: 'strings translated', note: 'two passes over the whole game' },
  { value: '1,025', label: 'Pokédex entries', note: 'every species in the game, Gen 9 included, in English' },
  { value: '84', label: 'Journal objectives', note: 'from Prof. Birch to Cogita' },
  { value: '200', label: 'item slots', note: 'and 999 of each' },
];

export const FEATURES: FeatureSection[] = [
  {
    id: 'v20',
    nav: 'Kitakami & v2.0',
    eyebrow: 'New in v2.0',
    title: 'Kitakami, and Gen 9 that battles like Gen 9',
    intro:
      'After Area Zero, a bus from Mossdeep City to Kitakami for the Teal Mask story and Mochi Mayhem; the Gen 9 abilities and moves as they are in Scarlet and Violet; and a few everyday things: a clock on the Start menu, base stats in the Pokédex, egg moves in the Move Relearner.',
    cards: [
      {
        title: 'Kitakami',
        text: 'Once Area Zero’s story is over, Briar waits beside the black hole in Mossdeep City with a bus to Mossui Town: a valley of red maples with a festival market, Kitakami Hall and its Mask Hall, and Loyalty Plaza.',
        how: 'Mossdeep City, beside the black hole, after Area Zero',
      },
      {
        title: 'The Teal Mask',
        text: 'Eight chapters with Carmine and Kieran: the three signboards, the Festival of Masks at night, the Loyal Three waking and hunted down, Ogerpon in her four masks and then yours. Afterwards Kieran’s grandfather changes her mask, and the Loyal Three can be caught where they hide.',
      },
      {
        title: 'Mochi Mayhem',
        text: 'Briar has a letter from Kieran: Mossui at night under the mochi’s spell, Arven, Nemona and Penny, Nemona’s battle and Pecharunt (No. 1025), yours once beaten. The Quest Log’s Legends count all five of Kitakami’s legends: 124.',
      },
      {
        title: 'Gen 9 abilities and move animations',
        text: 'Every Gen 9 ability does what it does in Scarlet and Violet (Protosynthesis and Booster Energy, the Treasures of Ruin, Commander, Good as Gold, Tera Shell…; not Zero to Hero, as there is no Hero Form), and the Gen 9 moves play animations of their own.',
      },
      {
        title: 'Gen 9 teams for the key trainers',
        text: 'The Gym Leaders, the Elite Four, Wallace, Archie, Maxie and more, 42 trainers, use Gen 9 Pokémon, in teams made by Luciano Fire.',
      },
      {
        title: 'Area Zero’s people, drawn',
        text: 'Nemona, Arven, Penny, Jacq, AI Sada and AI Turo walk Area Zero in sprites of their own, and Nemona, AI Sada and AI Turo battle in pictures of their own.',
      },
      {
        title: 'A clock on the Start menu',
        text: 'A box beside the “R Journal” one shows the day and the time, e.g. “Thu 5:08 PM”, and keeps time while the menu is open.',
        how: 'START',
      },
      {
        title: 'Base stats in the Pokédex',
        text: 'R on a Pokémon’s INFO page shows its six base stats as numbers and coloured bars, with their total; R again brings the description back.',
        how: 'R on a Pokédex INFO page',
      },
      {
        title: 'Gigantamax mark',
        text: 'A Pokémon that has had the Max Soup shows the Max Mushroom’s icon at the end of its name on the summary screen, on every page.',
        how: 'Summary',
      },
      {
        title: 'Egg moves in the Move Relearner',
        text: 'The party menu’s Moves lists a Pokémon’s egg moves after its level-up moves: its own and those of every stage it evolved from.',
        how: 'Party menu → Moves',
      },
      {
        title: 'The Hisui map flies again',
        text: 'Once Rei and Cogita have told you the news after Volo, A on the Sinnoh Map in Hisui flies you there with Mingyao’s Braviary. Before that it only names the places, so nothing skips the story.',
      },
    ],
    media: [
      { clip: 'mossui-town' },
      { clip: 'carmine-bus-stop' },
      { clip: 'ogerpon-loyalty-plaza' },
      { clip: 'kieran-night-market' },
      { clip: 'mask-hall' },
      { clip: 'area-zero-people' },
      { clip: 'start-menu-clock' },
      { clip: 'dex-base-stats' },
      { clip: 'gmax-mark' },
    ],
    links: [
      { href: '/guides/kitakami/', label: 'Kitakami guide' },
      { href: '/guides/legendaries/#kitakami', label: 'Kitakami’s legends' },
      { href: '/wiki/pokedex/', label: 'Pokédex' },
    ],
  },
  {
    id: 'gen9',
    nav: 'Gen 9 & Area Zero',
    eyebrow: 'New in v1.9',
    title: 'The whole of Gen 9, and Area Zero to find it in',
    intro:
      'Every Gen 9 Pokémon at its official Pokédex number, the newer ones in the wild all over Hoenn, and an optional Paldea area behind a black hole in Mossdeep City with a story, the Paradox Pokémon and the Gen 9 legends.',
    cards: [
      {
        title: 'Every Gen 9 Pokémon',
        text: '127 new slots, Sprigatito No. 906 to Pecharunt No. 1025, with Paldean Wooper and the three Paldean Tauros. They live in the wild over Hoenn without pushing out any of the game’s own Pokémon, and older families gained their Gen 9 evolutions (Annihilape, Farigiraf, Dudunsparce, Kingambit, Hydrapple, Archaludon, Clodsire).',
      },
      {
        title: 'Area Zero',
        text: 'Once Team Rainbow Rocket is beaten, a black hole opens beside Jacq in Mossdeep City. Behind it: Paldea’s Great Crater in the past and in the future, joined by time rifts, and Arven, Nemona and Penny to find.',
        how: 'Mossdeep City, below the Space Center',
      },
      {
        title: 'Paradox Pokémon and legends',
        text: 'Twelve Paradox Pokémon in the craters’ tall grass, the Titans Great Tusk and Iron Treads, the Zero Lab’s finale, then Koraidon, Miraidon, eight more Paradox, the four Treasures of Ruin and Terapagos to catch, once each.',
      },
      {
        title: 'New moves and items',
        text: 'The legends’ seven signature moves and their abilities have code of their own; the other new moves and abilities work like ones the game already has. Six evolution items at the Lilycove Department Store, 4F, and Booster Energy in Area Zero.',
      },
      {
        title: 'The Quest Log knows Gen 9',
        text: 'Legends counts the twenty Paradox Pokémon, and since v2.0 Kitakami’s five: 124 in all. Side Content has Area Zero’s extras, Evolutions every Gen 9 family, and the Journal seven optional Area Zero steps.',
      },
      {
        title: 'One-way saves',
        text: 'v1.9 moves a save’s Gen 9 Pokédex marks to where the longer Pokédex keeps them. A save that has been opened in v1.9 must not go back to an older version.',
      },
    ],
    media: [
      { clip: 'area-zero-hole' },
      { clip: 'time-rift' },
      { clip: 'paradox-wild' },
      { clip: 'gen9-wild' },
      { clip: 'questlog-area-zero' },
      { clip: 'evolutions-gen9' },
    ],
    links: [
      { href: '/guides/area-zero/', label: 'Area Zero guide' },
      { href: '/guides/legendaries/#area-zero-paldea', label: 'Gen 9 legends' },
      { href: '/wiki/pokedex/', label: 'Pokédex' },
    ],
  },
  {
    id: 'english',
    nav: 'English text',
    eyebrow: 'Translation',
    title: 'The whole game, in English',
    intro:
      'The earlier community translation stopped at Champion Island. This patch finishes it: the post-game, Sinnoh and the Lost Artifacts story now read in English from the first line to the last.',
    cards: [
      {
        title: 'About 6,000 strings',
        text: 'Translated over two passes: the post-game and Lost Artifacts (Volo and Arceus) story, the Sinnoh region, items, abilities, moves, Battle Frontier text and trainer dialogue.',
      },
      {
        title: 'Every Pokédex entry',
        text: 'All 1,025 species have an English entry, wrapped to fit the page, Gen 9’s too. Thirty-five that ran into the frame were laid out again.',
      },
      {
        title: 'English trainer names',
        text: 'The last Chinese names in fixed-width tables are English: all 90 Battle Tent trainers, two Battle Frontier trainers, six post-game story trainers (Ash, Blue, Brendan…) and the partner-name words.',
      },
      {
        title: 'TM descriptions that match',
        text: 'All 128 TMs and HMs were read against their moves. No two share a description any more, and every number in them matches the move.',
      },
      {
        title: 'Small things, fixed',
        text: 'Enamorus has its name, the newer berries are numbered No44 onward instead of “No?2”, the Sinnoh League attendant speaks English, and the Option screen says v5.7.',
      },
      {
        title: 'The last 2,341',
        text: 'A final pass put the leftover texts and names into English: what bosses say when beaten, 227 of the hack’s trainer names, Trainer Hill, the Easy Chat screen, link and trade menus, and battle lines such as “can’t go higher!”.',
      },
      {
        title: 'English naming keyboard',
        text: 'Nicknames, your own name and PC box names are typed on three English pages (UPPER, lower, others) in place of the hack’s Chinese ones.',
      },
      {
        title: 'What stays Chinese',
        text: 'Only text that is part of a picture: the title art and a few other drawn screens. If you meet a Chinese line in play, send a screenshot.',
      },
    ],
    media: [{ clip: 'pokedex-english' }, { clip: 'english-trainer-names' }],
    links: [
      { href: '/guides/install/', label: 'Install & play' },
      { href: '/about/', label: 'Credits for the earlier translation' },
    ],
  },
  {
    id: 'bag',
    nav: 'Bag & key items',
    eyebrow: 'Bag and key items',
    title: 'A bag that keeps up with a 40-hour post-game',
    intro:
      'More room, a sort button, and your four favourite key items one press away, with the PC in the middle of them.',
    cards: [
      {
        title: 'The key-item ring',
        text: 'Register up to four key items. SELECT opens a ring around you, as in Brilliant Diamond and Shining Pearl: each item sits in a box above, right of, below or left of your character.',
        how: 'SELECT in the field, then a direction',
      },
      {
        title: 'PC anywhere',
        text: 'The PC sits in the middle of the ring: box storage, your own PC and the Hall of Fame, with no item needed. It is switched off in six late dungeons to keep them a challenge.',
        how: 'SELECT, then A',
      },
      {
        title: 'Bag sort',
        text: 'Cycles type → name → amount, with a message in the description box. The order is written to the Bag, so it stays sorted.',
        how: 'START in the Bag',
      },
      {
        title: '999 of each item',
        text: 'Every pocket holds up to 999 per item instead of 99. The shop still sells 99 at a time, so buy twice.',
      },
      {
        title: '200 item slots',
        text: 'The Items pocket holds 200 different items, up from 100. An existing save keeps every item: the first load moves them over.',
      },
      {
        title: 'Both bikes at once',
        text: 'Once you own either bike, the other is added to your Key Items. Use or register either to switch on the spot.',
      },
      {
        title: 'Exp. Share switch',
        text: 'Use the Exp. Share from the Bag to turn it off and on. While off, only the Pokémon that battled gain experience.',
      },
      {
        title: 'Oval Charm',
        text: 'A new Key Item from the Day-Care Man on Route 117 after the Hoenn League. With it the Day Care finds Eggs about twice as often.',
      },
    ],
    media: [{ clip: 'key-ring' }, { clip: 'pc-anywhere' }, { clip: 'bag-sort' }, { clip: 'bag-200-slots' }],
    links: [
      { href: '/guides/controls/', label: 'Controls at a glance' },
      { href: '/guides/mega-stones-key-items/', label: 'Mega Stones & key items' },
    ],
  },
  {
    id: 'field',
    nav: 'Field & travel',
    eyebrow: 'In the field',
    title: 'Less friction between you and the next town',
    intro:
      'Running, surfing, repels, HMs and text speed all lose a step. None of it skips the journey; it just stops asking you to hold a button.',
    cards: [
      {
        title: 'Auto Run',
        text: 'Run without holding B; hold B to walk. Saved with your options, and it respects the Running Shoes and maps where running is not allowed.',
        how: 'START → Option → Auto Run',
      },
      {
        title: 'Faster surfing',
        text: 'Hold B while surfing to go twice as fast, the Mach Bike’s top speed. With Auto Run on, fast is the default and B slows you down.',
        how: 'Hold B while surfing',
      },
      {
        title: 'L quick repel',
        text: 'Asks “Use the Max Repel?” and falls back to Super Repel, then Repel. Silent when one is active or you have none.',
        how: 'L in the field',
      },
      {
        title: 'HMs without the Pokémon',
        text: 'Own the HM and the badge, and Cut, Strength, Rock Smash, Surf, Waterfall and Dive work even if nobody in your party can learn them. Flash is offered in the party menu inside a dark cave.',
        how: 'Walk up to the obstacle as usual',
      },
      {
        title: 'Instant text',
        text: 'A fourth Text Speed. Each page of a message appears at once, in conversations and in battle. Slow, Mid and Fast are unchanged.',
        how: 'START → Option → Text Speed',
      },
      {
        title: 'Day/Night switch',
        text: 'The game tints the screen by the hour: orange in the evening, pink, then blue at night. Off keeps the daytime colours at any hour; the clock and everything timed by it carry on.',
        how: 'START → Option → Day/Night',
      },
      {
        title: 'Exp. Gain switch',
        text: 'The hack’s own switch for experience, now named for what it does. It was the row labelled “Sound”, where Stereo quietly stopped all experience. Off is there for level caps and challenge runs.',
        how: 'START → Option → Exp. Gain',
      },
      {
        title: 'In-party move relearner',
        text: 'A Moves option in the party menu opens the Move Relearner for that Pokémon, with the hack’s expanded move lists. No Heart Scale needed.',
        how: 'Party menu → Moves',
      },
      {
        title: 'Nature changer, no quiz',
        text: 'The Mint teacher in the Rustboro Trainer’s School opens his offer straight away instead of after a run of true/false questions, and the summary shows the new nature.',
        how: 'Talk to him in Rustboro',
      },
    ],
    media: [{ clip: 'fast-surf' }, { clip: 'hm-cut' }, { clip: 'instant-text' }, { clip: 'move-relearner' }],
    links: [
      { href: '/guides/controls/', label: 'Controls at a glance' },
      { href: '/guides/mechanics/', label: 'Game mechanics' },
    ],
  },
  {
    id: 'battle',
    nav: 'Battle',
    eyebrow: 'In battle',
    title: 'The information you used to look up',
    intro:
      'With every species through Generation 9 on the other side of the field, types and matchups are shown where you need them.',
    cards: [
      {
        title: 'Type badges',
        text: 'The opponent’s box gets one or two small type badges, for every opponent. Read live from the battle, so Soak, Protean and Transform show the current types.',
      },
      {
        title: 'Move effectiveness',
        text: 'The move list shows the highlighted move’s multiplier in front of the PP count: ×4 red, ×2 orange, ×1 green, ×½ and ×¼ yellow, ×0 black. In doubles it follows the target you are choosing.',
      },
      {
        title: 'Move info on L',
        text: 'Hold L while you choose a move and a panel slides in with its exact Power and Accuracy, Physical / Special / Status, whether it makes contact, its Priority and the chance of its extra effect. It follows the cursor, in doubles too. A small L key with a magnifying glass above the move box is the reminder.',
        how: 'Hold L in the move list',
      },
      {
        title: 'Gold box for shinies',
        text: 'Any shiny Pokémon in battle gets a gold box: a wild one, a trainer’s and your own, so you can tell before the sprite finishes appearing.',
      },
      {
        title: 'Quick ball throw',
        text: 'Throws the first ball in your Poké Balls pocket without opening the Bag. Hold R to see the ball and count; left and right pick another.',
        how: 'R in a wild battle',
      },
      {
        title: 'Coloured stat names',
        text: 'Attack red, Defense orange, Speed light green, Sp. Atk pink, Sp. Def blue, Accuracy and Evasiveness yellow in every “rose” and “fell” message.',
      },
    ],
    media: [
      { clip: 'type-badges' },
      { clip: 'move-effectiveness' },
      { clip: 'shiny-gold-box' },
      { clip: 'quick-ball' },
    ],
    links: [
      { href: '/wiki/trainers/', label: 'Boss teams' },
      { href: '/guides/mechanics/#battle-systems-added-by-the-hack', label: 'Mega, Z-Moves and Dynamax' },
    ],
  },
  {
    id: 'dexnav',
    nav: 'DexNav',
    eyebrow: 'DexNav',
    title: 'See what lives here, then hunt it',
    intro:
      'Every wild Pokémon of the map you are standing on, laid out like Pokémon Unbound’s DexNav, and a search that gets better the more you use it.',
    cards: [
      {
        title: 'The map’s real table',
        text: 'Water and Land on one screen, Rock Smash and Fishing on the other. It lists exactly the table the game uses on that map, in the Safari Zone too.',
        how: 'R in the field, L/R to switch screens',
      },
      {
        title: 'Shadows until seen',
        text: 'A species you have not met yet is a black shadow named “?????” and cannot be searched. Meet it once in any battle and it shows up normally.',
      },
      {
        title: 'Search and chain',
        text: 'Pick a species and a patch near you shakes: rustling grass, a ripple on water, dust in a cave. Step on it to meet the hunted Pokémon, even with a Repel on.',
        how: 'A on a species; A again to stop',
      },
      {
        title: 'Search Level',
        text: 'Every encounter raises that species’ Search Level (up to 999, never reset), which raises the odds of an egg move, a held item and perfect IVs, and adds shiny rolls.',
      },
      {
        title: 'The field bar',
        text: 'Shows the icon, a star rating for perfect IVs, the level and ability it will have, your chain, the Search Level and an arrow toward the patch.',
      },
      {
        title: 'Chains that break fairly',
        text: 'As in Omega Ruby and Alpha Sapphire: running, losing, the Pokémon fleeing, walking away from the patch, leaving the area or any other battle ends the chain.',
      },
    ],
    media: [
      { clip: 'dexnav-screen' },
      { clip: 'dexnav-unseen' },
      { clip: 'dexnav-hunting' },
      { clip: 'dexnav-patch' },
      { clip: 'dexnav-gold-stars' },
      { clip: 'dexnav-chain' },
    ],
    links: [
      { href: '/wiki/encounters/', label: 'Wild encounters' },
      { href: '/wiki/pokemon/', label: 'Pokémon finder' },
    ],
  },
  {
    id: 'maps',
    nav: 'Maps',
    eyebrow: 'Maps and flying',
    title: 'A map for every region you reach',
    intro:
      'The hack added Sinnoh and Hisui without a map of either. The patch draws both, and lets you fly from them.',
    cards: [
      {
        title: 'Sinnoh Map',
        text: 'A key item handed to you automatically. A blinking marker shows where you are; a red box moves freely over the map and names the town, route or lake under it.',
        how: 'Sinnoh Map in Key Items, or on the ring',
      },
      {
        title: 'Fly from the map',
        text: 'A flies you to any town whose courier you have already used. It runs that courier’s own script, so the rules are exactly the couriers’.',
        how: 'A on a town',
      },
      {
        title: 'Hisui too',
        text: 'Used anywhere in Hisui, the map shows Hisui, drawn in the same style, with the marker on where you are. It does not fly you there: that let you skip ahead of the story.',
      },
      {
        title: 'Every Fly spot on the Hoenn map',
        text: 'Steven’s Island, Champion Island, Strange Island and Southern Island could be flown to but showed nothing. Each now gets a red square once you can go there.',
      },
    ],
    media: [{ clip: 'sinnoh-map-fly' }, { clip: 'hisui-map' }, { clip: 'hoenn-fly-spots' }],
    links: [
      { href: '/guides/walkthrough-postgame/#chapter-3-sinnoh', label: 'Sinnoh walkthrough' },
      { href: '/guides/lost-artifacts/', label: 'Lost Artifacts questline' },
    ],
  },
  {
    id: 'journal',
    nav: 'Journal & Quest Log',
    eyebrow: 'Journal and Quest Log',
    title: 'Never wonder what to do next',
    intro:
      'The post-game is one long chain of missions with no mission list. The Journal reads the game’s own progress flags and tells you the next step, without spoiling who is waiting there.',
    cards: [
      {
        title: 'Journal',
        text: 'A key item, handed to you automatically, that names your next story objective from Prof. Birch to Volo, with Area Zero as an optional quest beside the story. It saves nothing of its own, so it never gets out of step.',
        how: 'Journal in Key Items, or R in the Start menu',
      },
      {
        title: 'Quest Log',
        text: 'A chapter grid, then a mission list in the style of Pokémon Unbound: a tick on what is done, an arrow on the current objective, and “???” for what is still ahead.',
      },
      {
        title: 'Legends',
        text: 'Every legendary and mythical Pokémon in National Dex order, Ultra Beasts, the twenty Paradox Pokémon and Kitakami’s five included, 124 in all: ticked once caught, named once seen, with where to find it.',
      },
      {
        title: 'Key Items and Side Content',
        text: 'The 54 key items in story order with where each comes from, and a checklist of 59 side quests: the Hisuian trades, gift Pokémon, hidden starters, side stories, Area Zero’s extras and the four cartridges of the console in your room.',
      },
      {
        title: 'Sinnoh badge case',
        text: 'The eight Sinnoh badges, in colour once earned and as a silhouette before, with who you won each from.',
      },
      {
        title: 'Evolutions',
        text: 'Every evolution family with each step’s method, Gen 9’s included, and every form with how you get it: Megas, all 34 Gigantamax forms, regional forms, and the forms an item, a move or an ability brings about. Families you have not seen show as shadows.',
      },
    ],
    media: [
      { clip: 'questlog-story' },
      { clip: 'questlog-legends' },
      { clip: 'questlog-key-items' },
      { clip: 'questlog-side-content' },
      { clip: 'sinnoh-badge-case' },
      { clip: 'evolutions-family' },
      { clip: 'questlog-area-zero' },
    ],
    links: [
      { href: '/guides/journal/', label: 'Every Journal objective' },
      { href: '/guides/side-content/', label: 'Side content & gift Pokémon' },
      { href: '/guides/legendaries/', label: 'Legendary locations' },
    ],
  },
  {
    id: 'fixes',
    nav: 'Fixes',
    eyebrow: 'Bug fixes',
    title: 'Things that were broken, fixed',
    intro:
      'Some came from the hack, some from earlier translation passes. Each fix has an emulator test that drives the game and checks the result.',
    cards: [
      {
        title: 'News Tracker freeze',
        text: 'The News Tracker key item froze the game. A stray byte swallowed the message’s terminator; it works now, in English.',
      },
      {
        title: 'Egg moves',
        text: 'A species’ list was read into room for 10 moves while up to 16 were copied. Every egg move can be passed on now, from either parent.',
      },
      {
        title: 'Hyper Training that shows',
        text: 'The EV-IV Display and the IV judges show 31 for a trained stat, and the stats go up the moment training finishes.',
      },
      {
        title: 'Fusions that were refused',
        text: '“Multiple fusions are not allowed!” with nothing fused, after a look at IVs on v1.5 or a new game started over a save with a fusion. The fusion items now put it right when used, and a fused Necrozma that could not be split can be again.',
      },
      {
        title: 'A fresh roll after every reset',
        text: 'Soft-resetting for a legendary kept giving the same few natures and IVs, because the game started its random numbers from the same point at every power-on. It now starts them from the clock.',
      },
      {
        title: 'Repel prompt',
        text: 'Answering No to “Use another?” left the people on screen frozen in place; answering Yes handed control back before the repel was on. Both fixed.',
      },
      {
        title: 'DexNav town tables',
        text: 'Seven cities listed Bulbasaur, Charmander and Squirtle lines that never appear there. The DexNav now reads only the table the game uses.',
      },
      {
        title: 'Sinnoh League fly',
        text: 'Flying to the League lands at the building’s door once you have come through Victory Road, not at the Pokémon Center by the entrance.',
      },
      {
        title: 'Hisui’s striped ground',
        text: 'The ground of a Hisui map turned to stripes, with people drawn as noise, until the next battle: seven wandering Pokémon had fewer pictures than their walk. They glide in their standing picture now.',
      },
      {
        title: 'Tornadus and Thundurus stay in Sinnoh',
        text: 'After a save and reset the two storms roamed Hoenn’s sea routes while the News Tracker, the Quest Log and the researcher said Sinnoh. They are Sinnoh roamers for good now.',
      },
      {
        title: 'Battle graphics that stay right',
        text: 'Move animations drawn as blocks late in a long battle, the gold box losing its colours to an animation or a fade, Pokémon from the newer balls holding on to palettes, wrong status-icon colours on a gold box: all fixed.',
      },
      {
        title: 'Colours that belong',
        text: 'People and Pokémon on busy maps drawn in another’s colours, the EV-IV Display keeping the last Pokémon’s colours, and the DexNav bar’s icons in the wrong palette for many Pokémon numbered above 412.',
      },
      {
        title: 'Text that fits',
        text: '56 pages whose line ran past the message box were broken again, the Regi tablet no longer runs on into the next text, and in mist the message box no longer turns the fog solid white.',
      },
      {
        title: 'Fainted stays fainted',
        text: 'HP Up on a fainted Pokémon brought it back with a few HP, and a Pomeg Berry could give a fainted one full HP. A fainted Pokémon now stays fainted when its stats change (v2.0).',
      },
      {
        title: 'EVs reach 510',
        text: 'EVs from battles stopped at 509 in all. They reach 510 now (v2.0).',
      },
      {
        title: 'Electro Shot in the rain',
        text: 'Electro Shot fires in its first turn when it rains, as in Scarlet and Violet (v2.0).',
      },
      {
        title: 'No more stuck in the rock',
        text: 'Falling through Granite Cave’s cracked floor could drop you inside the rock, and Continue could put you inside a tree in Petalburg Woods. Both fixed (v2.0).',
      },
      {
        title: 'The Rainbow Rocket castle lets you back in',
        text: 'Leaving the castle before its mission was done and coming back found the trap fence shut for good. It lets you in now (v2.0).',
      },
      {
        title: 'Smaller fixes in v2.0',
        text: 'A Pokémon a script gives an item to keeps it in battle; Paul no longer hands you a second EV-IV Display; Cheren’s Mint list has Quirky and fits the screen; the DexNav bar’s icon keeps its colours at night.',
      },
      {
        title: 'Side quests you could not finish',
        text: 'Blue’s Galar gift (she stood inside a wall), the demon soul’s Magikarp (it shared a flag with Dawn’s battle) and the summit, where a failed visit took Kitty’s nameless stone for good.',
      },
      {
        title: 'DexNav names the real ability',
        text: 'The bar read its ability from leftover bytes and showed “-------” or the wrong name for 184 species. It now names the ability the Pokémon will have.',
      },
      {
        title: 'Egg moves for Mime Jr.',
        text: 'Mr. Mime and Mime Jr. had no egg moves and Goldeen and Bonsly had theirs. Each has its own list now.',
      },
    ],
    media: [{ clip: 'questlog-next-objective' }, { clip: 'no-pc-dungeons' }],
    links: [
      { href: '/changelog/', label: 'Full changelog' },
      { href: '/faq/', label: 'FAQ & known issues' },
    ],
  },
];
