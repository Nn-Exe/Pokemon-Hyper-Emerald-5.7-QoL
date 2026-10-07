// Questions and answers for the FAQ page and the search index. Answers are short HTML.

import { url } from '../lib/url';
import { REPO, ISSUES } from '../consts';

const link = (href: string, text: string) => `<a href="${url(href)}">${text}</a>`;
const ext = (href: string, text: string) => `<a href="${href}" target="_blank" rel="noopener noreferrer">${text}</a>`;

// answers are HTML: keep them short and factual
export const FAQ_GROUPS: { title: string; items: { q: string; a: string }[] }[] = [
  {
    title: 'Getting started',
    items: [
      {
        q: 'What is Hyper Emerald?',
        a: 'Hyper Emerald: Lost Artifacts (究极绿宝石) is a Chinese ROM hack of Pokémon Emerald by Destvol, Satochu, Popy, Potato, Hurricane, Feiyixiang and others. On top of the Hoenn story it adds the whole Sinnoh region as post-game, Mega Evolution, Z-Moves and Dynamax, every species through Sword and Shield, a trainer-level system, over a hundred side quests and a hard mode.',
      },
      {
        q: 'Is the hack complete?',
        a: 'Yes. v5.7 is a finished release with Hoenn, Sinnoh and the post-game. The English patch has been played through the areas its tests cover, not all forty-plus hours, so odd text is still possible in deep post-game screens.',
      },
      {
        q: 'What do I need to play?',
        a: `The “bugfix 2” build of Hyper Emerald: Lost Artifacts v5.7 (the Chinese hack itself, 32 MB), the patch file from the repository, Python 3 to apply it, and a GBA emulator. ${link('/guides/install/', 'Install & Play')} walks through it.`,
      },
      {
        q: 'Where do I get the ROM?',
        a: 'This site and the repository do not distribute ROMs. Get the hack from its original release thread and patch it yourself.',
      },
      {
        q: 'Which emulator is recommended?',
        a: 'mGBA. Everything in the patch was tested on it. RetroArch with the mGBA core, standalone mGBA on Android and mGBA 0.10.x on a homebrew Switch all run the hack.',
      },
      {
        q: 'How do I know which version I am on?',
        a: 'Open START → Option. The title reads “Ultra Emerald v5.7 +QoL1.8” followed by your difficulty when you are on the current build.',
      },
    ],
  },
  {
    title: 'ROM patching',
    items: [
      {
        q: 'The patcher says “this is not the expected original ROM”',
        a: `Your file is not the “bugfix 2” build of v5.7. Check its SHA-1 against <code>f785bed9d9e82e8da13ea4a5ad747e3ea4ec7ba9</code> (see ${link('/guides/install/#what-you-need', 'Install & Play')}). Vanilla Emerald is 16 MB; the hack is 32 MB. The older community English ROM is also refused: the patch already contains the full translation, so it has to start from the untouched Chinese ROM.`,
      },
      {
        q: 'Can I apply this on top of another patch or a cheat-modified ROM?',
        a: 'No. The patcher compares every byte it changes with what it expects, so any other modification makes it stop. Apply to a clean ROM and add cheats as emulator codes instead.',
      },
      {
        q: 'Does it need the translation-only build first?',
        a: 'No. The release patch goes from the Chinese ROM straight to the final build in one step.',
      },
      {
        q: 'The game crashes right after New Game, in the mountain cutscene',
        a: 'That was a bug in this patch’s own releases before 2026-09-14: a translation pass had overwritten a few of the hack’s movement scripts (the cutscene where the villains line up on the mountain, the Slateport Contest Hall reception and six later scenes). Re-apply the current patch to a clean Chinese ROM; your <code>.sav</code> keeps working.',
      },
    ],
  },
  {
    title: 'Saves',
    items: [
      {
        q: 'My save is gone after switching to the new ROM',
        a: 'Emulators match the <code>.sav</code> by file name. Rename either the ROM or the save so the base names match. The save data itself is compatible in both directions.',
      },
      {
        q: 'Can I use save states from the old ROM?',
        a: 'No. Save states capture the whole ROM image and memory, so they only work with the exact ROM they were made on. Save in-game, switch ROMs, then load the battery save.',
      },
      {
        q: 'My Items pocket looked empty after updating',
        a: 'That happened on v1.6 when the game carried on from an emulator save state made on an older version: the items had not yet been moved into the new 200-slot pocket. Nothing was lost, and the current build moves them in that case too.',
      },
      {
        q: 'Will future patch versions break my save?',
        a: 'Updates are designed to be save-compatible: the features keep their state in bytes the game never used. Keep a backup of the <code>.sav</code> anyway; it is a 128 KB file.',
      },
      {
        q: 'My save disappears after the League',
        a: 'Set the emulator’s save type to <strong>Flash 128K</strong>. The hack needs the full 128 KB save.',
      },
    ],
  },
  {
    title: 'Controls and features',
    items: [
      {
        q: 'R no longer toggles running',
        a: `Auto Run moved to START → Option (it replaces Button Mode); turn it on there once. R in the field now opens the DexNav. ${link('/guides/controls/', 'Every button is listed here')}.`,
      },
      {
        q: 'R does nothing in battle',
        a: 'Quick throw only works in wild single battles at the action menu, with at least one ball in the Poké Balls pocket and room in the party or PC. It is off in trainer, Safari, double, link and Battle Frontier battles.',
      },
      {
        q: 'L does nothing',
        a: 'Either a repel is already active or you carry none. The hack’s own “use another?” prompt still appears when a repel wears off.',
      },
      {
        q: 'The PC on the SELECT ring is crossed out in red',
        a: 'You are in Rainbow Castle, Allearth Forest, Giant Chasm, Spear Pillar, the Distortion World or Mt. Silver. The ring’s PC is switched off there to keep those dungeons a challenge. A PC that stands in the area still works, and so do your registered key items.',
      },
      {
        q: 'A Pokémon in the DexNav is a black shadow named “?????”',
        a: 'You have not seen that species yet, so it cannot be searched. Meet it once in any battle and it shows up normally.',
      },
      {
        q: 'The relearner returns me to the field',
        a: 'That is expected; the game’s Move Relearner exits to the field. Open the party menu again to continue.',
      },
      {
        q: 'Where did the Rare Candy NPC in Petalburg’s Poké Mart go?',
        a: 'He was removed in v1.7: 999 Rare Candies for a single “yes” made levelling pointless. Candies you already received stay in the Bag.',
      },
      {
        q: 'Where did the Sound option go?',
        a: 'That row never changed the sound in this hack: it was the hack’s experience switch with Emerald’s label left on it, and Stereo stopped every Pokémon gaining experience. From v1.8 it reads <strong>Exp. Gain: On / Off</strong>. A save that was on Stereo shows Off; switch it On.',
      },
      {
        q: 'Can I turn off the evening and night colours?',
        a: 'Yes: START → Option → <strong>Day/Night: Off</strong> keeps the daytime colours at any hour. Only the colours change; the clock keeps running, and evolutions and events that depend on the hour work as before.',
      },
      {
        q: 'The N-Solarizer says “Multiple fusions are not allowed!”',
        a: 'The game keeps one fused Necrozma at a time (and one Calyrex, one Kyurem), so split the one you have first. If nothing of yours is fused, it was a bug: a look at IVs on v1.5, or a new game started over a save that had a fusion, left the game thinking a fusion was stored. v1.8 puts that right when you use the item again; your save needs nothing else.',
      },
      {
        q: 'Soft-resetting keeps giving me the same nature and IVs',
        a: 'Fixed in v1.8. The game used to start its random numbers from the same point at every power-on, so a reset with the same timing met the same Pokémon. It now starts them from the clock. Loading an emulator save state still brings back the luck it was made with: reset the game instead.',
      },
      {
        q: 'A stat-boost message from an X item is not coloured',
        a: 'The hack draws that message inside the Bag window with its own routine, which ignores colour codes. Stat changes from moves and abilities are coloured.',
      },
    ],
  },
  {
    title: 'The hack’s own known issues',
    items: [
      {
        q: 'My Pokémon stopped gaining experience',
        a: `Two things do that. First, START → Option → <strong>Exp. Gain</strong> must be On (before v1.8 that row was labelled Sound, and Stereo was Off). Second, in every mode except Easy, Pokémon stop gaining experience at the current level cap, which rises with badges and league wins. After the Elite Four, keep progressing the post-game story. See ${link('/guides/mechanics/#level-caps-and-obedience', 'level caps and obedience')}.`,
      },
      {
        q: 'The game crashes when I catch certain Pokémon with a Master Ball',
        a: 'Use another ball on legendaries where possible, or save before throwing.',
      },
      {
        q: 'The Bag freezes when the cursor lands on one item',
        a: 'Press SELECT to skip over that item, then B to leave the Bag.',
      },
      {
        q: 'Evolving with a stone did not teach the new form’s move',
        a: 'Use the party menu’s Moves option (the patch’s relearner) to pick it up.',
      },
      {
        q: 'Sprites look wrong after a warp',
        a: 'An NPC in the game explains it: “If this happens, just switch screens and it will go back to normal.”',
      },
      {
        q: 'The post-game Xerneas encounter crashes',
        a: 'Fixed in the “bugfix” builds of v5.7. Make sure your base ROM is bugfix 2.',
      },
    ],
  },
  {
    title: 'Text and reporting',
    items: [
      {
        q: 'I still see a few Chinese lines',
        a: `From v1.8 the only Chinese left is text that is part of a picture: the title logo and a few other drawn screens. Every text the game can reach has been translated as far as our scans can tell. If you meet a Chinese line during play, report it with a screenshot on the ${ext(ISSUES, 'GitHub issues page')}.`,
      },
      {
        q: 'How do I report a bug?',
        a: `Open an issue on the ${ext(ISSUES, 'repository')} with a screenshot, what you were doing, your emulator, and the version from the Option screen. A copy of your <code>.sav</code> makes a crash much easier to reproduce.`,
      },
      {
        q: 'Can I contribute?',
        a: `Yes. Every feature is a standalone patcher with its own test, and pull requests are welcome on ${ext(REPO, 'GitHub')}. Corrections to this guide are welcome too.`,
      },
    ],
  },
];
