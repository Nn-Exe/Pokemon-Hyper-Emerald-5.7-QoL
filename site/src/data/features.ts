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
  { value: '960', label: 'Pokédex entries', note: 'every entry in the game, in English' },
  { value: '84', label: 'Journal objectives', note: 'from Prof. Birch to Cogita' },
  { value: '200', label: 'item slots', note: 'and 999 of each' },
];

export const FEATURES: FeatureSection[] = [
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
        text: 'All 960 species have an English entry, wrapped to fit the page. Thirty-five that ran into the frame were laid out again.',
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
        title: 'What stays Chinese',
        text: 'About 50 strings, on purpose: link-battle and Trainer Card messages whose control codes can hang the text engine, a few name-table entries with no context, and text baked into images such as the title art.',
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
      'With every species through Generation 8 on the other side of the field, types and matchups are shown where you need them.',
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
        text: 'Used anywhere in Hisui, the map shows Hisui, drawn in the same style. A on a red square flies you there with Braviary.',
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
        text: 'A key item, handed to you automatically, that names your next story objective from Prof. Birch to Volo. It saves nothing of its own, so it never gets out of step.',
        how: 'Journal in Key Items, or R in the Start menu',
      },
      {
        title: 'Quest Log',
        text: 'A chapter grid, then a mission list in the style of Pokémon Unbound: a tick on what is done, an arrow on the current objective, and “???” for what is still ahead.',
      },
      {
        title: 'Legends',
        text: 'Every legendary and mythical Pokémon in National Dex order, Ultra Beasts included: ticked once caught, named once seen, with where to find it.',
      },
      {
        title: 'Key Items and Side Content',
        text: 'The 55 key items in story order with where each comes from, and a checklist of the Hisuian trades, gift Pokémon, hidden starters and side stories.',
      },
      {
        title: 'Sinnoh badge case',
        text: 'The eight Sinnoh badges, in colour once earned and as a silhouette before, with who you won each from.',
      },
      {
        title: 'Evolutions',
        text: 'Every evolution family with each step’s method, Megas, Gigantamax and regional forms included. Families you have not seen show as shadows.',
      },
    ],
    media: [
      { clip: 'questlog-story' },
      { clip: 'questlog-legends' },
      { clip: 'questlog-key-items' },
      { clip: 'questlog-side-content' },
      { clip: 'sinnoh-badge-case' },
      { clip: 'evolutions-family' },
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
    ],
    media: [{ clip: 'questlog-next-objective' }, { clip: 'no-pc-dungeons' }],
    links: [
      { href: '/changelog/', label: 'Full changelog' },
      { href: '/faq/', label: 'FAQ & known issues' },
    ],
  },
];
