// Release history for players, condensed from the repository's CHANGELOG.md (which has the engineering detail).
// Newest first. The first entry is the current release.

export type Kind = 'Added' | 'Changed' | 'Fixed' | 'Removed';
export type Release = {
  version: string;
  date: string;
  summary: string;
  /** shown above the list, e.g. while the version's patch file is not out yet */
  note?: string;
  changes: [Kind, string][];
};

export const RELEASES: Release[] = [
  {
    version: 'v1.9',
    date: '2026-10-16',
    summary:
      'The whole of Generation 9 and Area Zero, a Paldea area behind a black hole in Mossdeep City, with the Quest Log following both; and fixes for bugs of the original hack, from Hisui’s striped ground and roaming storms to battle graphics, text that ran off the box and side quests that could not be finished.',
    changes: [
      ['Added', 'Every Gen 9 Pokémon: 127 new slots at their official Pokédex numbers, Sprigatito No. 906 to Pecharunt No. 1025, Paldean Wooper and the three Paldean Tauros included, each with its English Pokédex entry. The newer ones live in the wild all over Hoenn; none of the game’s own Pokémon were taken out to make room.'],
      ['Added', 'Gen 9 evolutions, older families’ too: Primeape → Annihilape, Girafarig → Farigiraf, Dunsparce → Dudunsparce, Bisharp → Kingambit, Applin → Dipplin → Hydrapple, Duraludon → Archaludon, Paldean Wooper → Clodsire. The six new evolution items are sold at the Lilycove Department Store, 4F. Gen 9 Pokémon that hatch from Eggs have their egg moves.'],
      ['Added', 'Gen 9 moves and abilities. The legends’ seven signature moves (Collision Course, Electro Drift, Ruination, Ivy Cudgel, Hydro Steam, Psyblade, Glaive Rush) and their abilities have code of their own; the other new moves and abilities work like ones the game already has, and a few do less than in Scarlet and Violet.'],
      ['Added', 'Area Zero. Jacq stands in Mossdeep City from the start; once Team Rainbow Rocket is beaten a black hole opens beside him. Behind it: Paldea’s Great Crater in the past and in the future, joined by time rifts; Penny, Arven and Nemona; the Titans Great Tusk and Iron Treads; four research logs; the Zero Lab’s finale against the professors’ AIs and the Paradise Protection Protocol.'],
      ['Added', 'After Area Zero’s story: Koraidon and Miraidon, eight more Paradox Pokémon, Wo-Chien, Chien-Pao, Ting-Lu, Chi-Yu (three of them behind a sliding-floor puzzle in the Sealed Vault) and Terapagos, once each. Twelve Paradox Pokémon roam the craters’ tall grass, Booster Energy lies in the craters and is sold in the Zero Lab, and Nemona battles again in Research Station No. 3.'],
      ['Added', 'Quest Log for Gen 9: Legends counts 119 with the twenty Paradox Pokémon (the five that live in Kitakami, which the game does not have, show as Locked and are not counted, and counts over 99 print properly); Side Content has ten Area Zero rows (55 in all); Evolutions has every Gen 9 family (400 pages); the Journal has seven optional Area Zero steps that never take the main story’s place.'],
      ['Changed', 'Move info’s tag above the move box is a small L key with a magnifying glass, half as wide, so it no longer covers the Pokémon. Holding L works as before.'],
      ['Changed', 'In Hisui the Sinnoh Map no longer flies you: it shows where you are and names every place. Flying from it let you skip ahead of the story.'],
      ['Changed', 'Quest Log Key Items: the Contest Pass is gone (nothing in the game hands it out). Side Content rows that said the wrong thing were rewritten from the scripts: Ash’s challenge, the Burning Soul, Meltan, the demon soul’s Magikarp, the Battle Frontier gifts and Blue’s Galar team.'],
      ['Changed', 'The Option screen’s title says +QoL1.9.'],
      ['Fixed', 'Hisui maps whose ground turned to stripes, with people drawn as noise, until the next battle (seven wandering Pokémon had fewer pictures than their walk).'],
      ['Fixed', 'Tornadus and Thundurus left Sinnoh for Hoenn’s sea routes after a save and reset. They stay Sinnoh roamers now.'],
      ['Fixed', 'Battle graphics: move animations drawn as blocks late in a long battle, the gold shiny box losing its colours to an animation or staying lit through a fade, Pokémon from the newer Poké Balls holding on to two palettes, and the wrong colours of a status icon on a gold box.'],
      ['Fixed', 'Colours: people and Pokémon drawn in another’s colours on busy maps, the EV-IV Display showing a Pokémon in the last one’s colours, and DexNav bar icons in the wrong palette for many Pokémon numbered above 412.'],
      ['Fixed', 'The DexNav bar named the wrong ability, or “-------”, for 184 species; it names the one the Pokémon will have.'],
      ['Fixed', 'Text: 56 pages whose line ran past the message box, the Regi tablet that ran on into the next text, and the fog turning solid white behind a message in mist.'],
      ['Fixed', 'Egg moves: Mr. Mime and Mime Jr. had none, and Goldeen and Bonsly had theirs.'],
      ['Fixed', 'Side quests that could not be finished: Blue’s Galar gift in the Lilycove Museum (she stood inside a wall), the demon soul’s Magikarp on Steven’s Island (it shared a flag with Dawn’s battle), and the summit, where one failed visit took Kitty’s nameless stone for good.'],
    ],
  },
  {
    version: 'v1.8',
    date: '2026-10-07',
    summary:
      'Move info in battle on L, Day/Night and Exp. Gain switches in the Option menu, an English keyboard on the naming screen, the last Chinese text in English, and fixes for fusions and soft resets.',
    changes: [
      ['Added', 'Move info in battle: hold L while you choose a move and a panel slides in with its exact Power and Accuracy, Physical / Special / Status, whether it makes contact, its Priority and the chance of its extra effect.'],
      ['Added', 'Day/Night: On / Off in the Option menu. Off shows the daytime colours at any hour; the clock and everything timed by it carry on.'],
      ['Changed', 'The Option menu’s “Sound: Mono / Stereo” row now reads Exp. Gain: On / Off. The hack had made that row its experience switch and left the old label on it, so Stereo stopped every Pokémon gaining experience. A save left on Stereo shows Off: switch it On.'],
      ['Changed', 'The naming screen has an English keyboard: UPPER, lower and others pages in place of the hack’s Chinese ones, with Emerald’s own buttons.'],
      ['Fixed', 'The last Chinese text is English, 2,341 texts and names: what bosses say when beaten, 227 trainer names, Trainer Hill, the Easy Chat screen, link and trade menus, battle lines such as “can’t go higher!”, and the building labels on the PokéNav’s zoomed city maps.'],
      ['Changed', 'Quest Log Evolutions: a family’s page shows every form and how you get it, as its Pokédex page on this site does. All 34 Gigantamax forms and the forms a held item, a move, an ability or a Bag item brings about; forms nobody can get are left out.'],
      ['Fixed', '“Multiple fusions are not allowed!” with nothing fused. Necrozma could not be fused, or split again, on a save that had looked at IVs on v1.5, and a new game started over a save with a fusion could never make that fusion. The N-Solarizer, N-Lunarizer, Unity Reins and DNA Splicers now put it right when used.'],
      ['Fixed', 'Soft-resetting for a legendary kept giving the same few natures and IVs. The game now starts its random numbers from the clock, so every reset rolls afresh.'],
    ],
  },
  {
    version: 'v1.7',
    date: '2026-10-01',
    summary:
      'The key-item ring with the PC in the middle, an Unbound-style DexNav screen, Instant text, faster surfing, HMs without the Pokémon, the Quest Log’s Evolutions pages and a free cursor on the Sinnoh Map.',
    changes: [
      ['Changed', 'SELECT’s key-item popup is now a ring around your character, like Brilliant Diamond and Shining Pearl’s: the registered items’ icons up, right, down and left, the PC in the middle with an A badge.'],
      ['Changed', 'No PC from the ring in Rainbow Castle, Allearth Forest, Giant Chasm, Spear Pillar, the Distortion World and Mt. Silver, to keep those dungeons a challenge. A PC that stands in the area still works.'],
      ['Changed', 'DexNav screen redrawn after Pokémon Unbound’s: Water and Land on one screen, Rock Smash and Fishing on the other, a red ring to pick a species and a panel with its type, Search Level, level range and chain.'],
      ['Changed', 'DexNav: a species you have not seen yet shows as a black shadow named “?????” and cannot be searched until you meet it once.'],
      ['Added', 'Instant text: a fourth Text Speed. Each page of a message appears at once, in conversations and in battle.'],
      ['Added', 'Faster surfing: hold B while surfing to go twice as fast. With Auto Run on, fast is the default and B slows you down.'],
      ['Added', 'HMs without the Pokémon: with the HM in the Bag and its badge, Cut, Strength, Rock Smash, Surf, Waterfall and Dive work even when nobody can learn the move; Flash from the party menu in a dark cave. Contributed by @anibalribeiro.'],
      ['Added', 'Quest Log Evolutions: every evolution family in one list, with each step’s method. Megas, Gigantamax and regional forms included; families you have not seen show as shadows.'],
      ['Changed', 'Quest Log chapter grid restyled to match the DexNav and the key-item ring; lists scroll over twice as fast and speed up while Up or Down is held.'],
      ['Changed', 'Sinnoh Map: a red box now moves freely over the map a square at a time, instead of hopping from place to place. Same in Hisui.'],
      ['Fixed', 'Journal: a new step, News of Faba, sends you to the Devon Scout before the Scorched Slab wormhole, which stays closed until he has reported.'],
      ['Fixed', 'TM descriptions: all 128 TMs and HMs read against their moves. Five texts were shared by different moves; no two TMs share a description any more.'],
      ['Fixed', '“The Repel ended… Use another?”: answering No left the people on screen frozen in place; answering Yes handed control back before the new repel was on.'],
      ['Fixed', 'DexNav: seven cities listed Land Pokémon that never appear there. It now lists exactly the table the game uses on that map.'],
      ['Fixed', 'After updating, the Items pocket could look empty when the game carried on from an older save state. The items now move over in that case too.'],
      ['Removed', 'The Rare Candy NPC in Petalburg City’s Poké Mart: 999 Rare Candies for a single “yes” made levelling pointless. Candies already received stay in the Bag.'],
    ],
  },
  {
    version: 'v1.6',
    date: '2026-09-29',
    summary:
      'A 200-slot Items pocket, the Sinnoh badge case, Hisui on the Sinnoh Map, the Oval Charm, an Exp. Share switch and an Unbound-style Quest Log.',
    changes: [
      ['Added', 'The Bag’s Items pocket holds 200 different items (was 100). Your save keeps every item: the first load copies them into the bigger pocket.'],
      ['Added', 'Quest Log Badges: a Sinnoh badge case like Platinum’s, with each badge in colour once earned and who you won it from.'],
      ['Added', 'Hisui on the Sinnoh Map: used anywhere in Hisui, the map shows Hisui, and A on a red square flies you there with Braviary.'],
      ['Added', 'Oval Charm, a new Key Item from the Day-Care Man on Route 117 after the Hoenn League: the Day Care finds Eggs about twice as often.'],
      ['Added', 'The Exp. Share can be switched off and on by using it from the Bag.'],
      ['Changed', 'Quest Log lists redesigned like Pokémon Unbound’s mission log: status tags and an info panel with a portrait, a location and a short text.'],
      ['Fixed', 'Hyper Training could change the species of a Pokémon kept by a fusion (the Solgaleo stored inside Dusk Mane Necrozma).'],
      ['Fixed', 'Egg moves: lists longer than ten moves spilled over other data, and anything past the sixteenth was never read. Either parent passes egg moves.'],
      ['Fixed', 'Hoenn Fly map: Steven’s Island, Champion Island, Strange Island and Southern Island now show the red square the Battle Frontier has.'],
      ['Fixed', 'Pokédex descriptions running into the frame: thirty-five entries laid out again.'],
      ['Fixed', 'Two destinations in the Hisui Braviary menu were still in Chinese: now Deertrack Heights and Snowfall Hot Spring.'],
    ],
  },
  {
    version: 'v1.5',
    date: '2026-09-23',
    summary:
      'The Journal and the Quest Log, Hyper Training that shows, the nature display fix and gold boxes for your own shinies.',
    changes: [
      ['Added', 'Journal key item: shows your next story objective across Hoenn, the post-game, Sinnoh and Lost Artifacts, with progress for the Sinnoh gyms, the Tapu trials and the Plates.'],
      ['Added', 'Quest Log: using the Journal opens a checklist of every objective, one chapter a page, with “???” for what is ahead. R in the Start menu opens it too.'],
      ['Added', 'Quest Log chapters for Legends (every legendary and mythical Pokémon, Ultra Beasts included), Key Items (55, in story order) and Side Content.'],
      ['Changed', 'The gold healthbox now also marks your own shiny Pokémon, not only wild and trainers’ ones.'],
      ['Added', 'A Rare Candy NPC in Petalburg City’s Poké Mart (taken back out in v1.7). Contributed by @anibalribeiro.'],
      ['Fixed', 'The summary’s Nature line now follows a Mint. Contributed by @anibalribeiro.'],
      ['Fixed', 'Hyper Training on Champion Island: the EV-IV Display and the IV judges show 31 for a trained stat, and the stats go up the moment he finishes.'],
      ['Fixed', 'Sinnoh League: the attendant who heals your team spoke Chinese, and so did her door menu.'],
      ['Fixed', 'Berries pocket numbers: the hack’s newer berries showed as “No?2”. They now continue after Enigma: Occa No44 … Maranga No67.'],
      ['Fixed', 'Enamorus’s name was still in Chinese.'],
      ['Fixed', 'Sinnoh Map: flying to the League lands at the building’s door once you have come through Victory Road.'],
      ['Added', 'The Option screen’s title names the patch version: “Ultra Emerald v5.7 +QoL1.5 (Standard)”.'],
    ],
  },
  {
    version: 'v1.4',
    date: '2026-09-21',
    summary: 'DexNav hunting, the Sinnoh Map with fly, and R opening the DexNav with Auto Run moved into the Option menu.',
    changes: [
      ['Added', 'DexNav search and chain: pick a species and a bar on the field shows its icon, star rating, level, ability and how many you have taken in a row.'],
      ['Added', 'A per-species Search Level sets the odds of an egg move, a held item and perfect IVs, and adds shiny rolls. It goes to 999 and never resets.'],
      ['Added', 'The shaking patch: while hunting a Land or Water species, a patch near you rustles, ripples or kicks up dust. Step on it for the hunted Pokémon.'],
      ['Added', 'DexNav jackpot: one hunted encounter in 500 has all six IVs perfect, shown as three gold stars.'],
      ['Added', 'Sinnoh Map key item with its own screen, a marker on your area and fly to any town whose courier you have used.'],
      ['Changed', 'R in the field opens the DexNav. Auto Run moved to the Option menu, replacing Button Mode.'],
      ['Fixed', 'The News Tracker key item froze the game.'],
    ],
  },
  {
    version: 'v1.3',
    date: '2026-09-20',
    summary: 'The DexNav screen, type badges, the move effectiveness multiplier, both bikes at once and English NPC names. v1.3.1 followed the same day.',
    changes: [
      ['Added', 'DexNav screen from the Start menu: the map’s wild Pokémon with icons, level ranges and habitat. Also on the Safari Zone menu.'],
      ['Added', 'Type badges beside the opponent’s healthbox in battle, in SoulGold’s badge art.'],
      ['Added', 'Move effectiveness multiplier on the PP line of the battle move list.'],
      ['Added', 'Gold healthbox for a shiny opponent, matching the game’s own shiny check.'],
      ['Added', 'Both bikes held at once: no more swapping at Rydel’s.'],
      ['Added', 'Leftover Chinese NPC names in English: 90 Battle Tent trainers, 2 Battle Frontier trainers, 6 story trainers and 6 partner-name words.'],
      ['Fixed', 'The Option screen and the Hall of Fame banner said version 5.5; they now say 5.7.'],
      ['Changed', 'v1.3.1: type badges and the effectiveness multiplier show for every opponent again, not only species you have caught.'],
    ],
  },
  {
    version: 'v1.2',
    date: '2026-09-16',
    summary:
      'PC anywhere, the Mint nature changer without the quiz, restored graphics in 58 maps and the new-game crash fix. Includes v1.1.',
    changes: [
      ['Added', 'PC anywhere: open the PC from the SELECT popup (box storage, your PC, Hall of Fame).'],
      ['Added', 'Mint nature changer without the quiz: the teacher in the Rustboro Trainer’s School offers Mints straight away.'],
      ['Fixed', 'New-game crash in the Mountain Top cutscene, plus eight other scenes, where earlier translation passes had overwritten movement scripts.'],
      ['Fixed', 'Garbled graphics in Rustboro and 57 other maps, where earlier translation passes had overwritten compressed tiles.'],
      ['Changed', 'Three Team Flare grunts in Allearth Forest that no script refers to are hidden.'],
      ['Added', 'The player’s guide website, and credits for the earlier translation team.'],
    ],
  },
  {
    version: 'v1.0',
    date: '2026-09-13',
    summary: 'The first public release: the full English translation and the first set of quality-of-life features.',
    changes: [
      ['Added', 'Full English text over two passes: about 4,000 strings (post-game, the Lost Artifacts story, Sinnoh, battle text), then 1,944 more including all 960 Pokédex entries and Battle Frontier dialogue.'],
      ['Added', 'Bag sort with START, and a stack cap of 999 per item.'],
      ['Added', 'Register up to four key items, with a SELECT popup.'],
      ['Added', 'Quick ball throw with R in wild battles, with an on-screen widget.'],
      ['Added', 'Auto-run and the L quick repel (Max → Super → Repel).'],
      ['Added', 'In-party move relearner (party menu → Moves).'],
      ['Added', 'Coloured stat names in battle messages.'],
      ['Fixed', 'A freeze in the Volo and Arceus cutscene.'],
    ],
  },
];
