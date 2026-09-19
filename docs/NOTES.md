# Hyper Emerald v5.7 — Project Checklist

## MOVEMENT SCRIPTS OVERWRITTEN BY THE TEXT PASSES — FIXED 2026-09-14 (`patches/movefix/`)
- Symptom: new game -> Unown Ruins 34/12 (Arceus "want to watch it?") -> Temple of the End 35/35 -> Mountain Top 34/66
  (Rainbow Rocket lineup, script 0x09828797) crashes with mGBA "Jumped to invalid address 101C0CB4" at
  `applymovement 000f @08B14EB1` (0x09828AEC). The movement pointer had been redirected to relocated English text
  ("???: Wait…!"); the object-event code indexed its movement-action table with text bytes (0xAC...) and jumped to garbage.
- Root cause: `applymovement 0x000F, ptr` = `4F 0F 00 <ptr>` is byte-identical to `loadword 0, ptr` after a 4F. The
  text passes found dialogue by scanning for `0F 00 <ptr>`, so every applymovement on local object 15 became a "text
  load"; movement bytes (0x01-0x1E) decode as hanzi, the junk filter let "junk prefix + real text" entries through.
  patch_conv's in-place path then overwrote movement bytes (extent = until the next 0xFF, which lies after the following
  text), and the relocation path redirected the applymovement pointers. Same trap in patch_remaining via aligned occurrences
  (Slateport 9/3, 0x208ED0) — its `structural()` check does not distinguish data from text either.
- Audit (`patches/movefix/audit_moves.py <patched> <original>`): for every `4F/50 xx xx <ptr>` in the ORIGINAL whose target is a
  movement script (bytes < 0xA0 ending in FE within 64), the patched ROM must keep the pointer and the bytes. Result before
  the fix: 9 pointers redirected (8 scripts: 0x08209068, 0x0829082B, 0x09829105 x2 refs, 0x09883DFA, 0x09883EEB,
  0x09883F59, 0x09884244, 0x0989A14D) and 4 movement scripts overwritten (0x0981865C `18 15 FE`, 0x09818B5E 12 bytes,
  0x0989A6D1 `56 03 FE`, 0x0989A6D5 `56 01 FE`; 4/4/4/4 refs). Two text loads then pointed into the middle of an
  in-place English string (Prof. Cozmo 0x09818B6B, "Would you like to battle with Treecko?" 0x09810B7F) -> clean copies at
  0x08FD9D60 (feature area, after the statcolor palette) and the loadwords repointed. After the fix: 4,234 refs, 0 problems.
  A general "original pointer whose target bytes changed (non-pointer bytes)" sweep found nothing else harmful: the
  remaining hits are pointer rewrites inside scripts/tables (by design) or a dead script at 0x0989A6D8 (unreferenced).
- Pipeline guard added: build_corpus.py (`meaningful`, `occ_kind`), patch_conv.py and patch_story.py skip `0F 00` when the
  byte before is 4F/50. Lesson: a loadpointer scan must check the opcode context, and "junk hanzi + real text" entries are
  a red flag for a pointer that targets data in front of the text.
- Verified in mGBA 0.11 dev (`--script`; the 0.10.5 release has no CLI script option): `patches/movefix/test_intro.lua` drives
  new game -> 34/12 -> 35/35 -> 34/66 (waypoints from the layout collision map, Gold NPC blocks x=16) -> truck 25/40 ->
  Littleroot 0/9 -> house 1/0. Release rebuilt: `Hyper Emerald v5.7 EN+QoL.gba` sha1 cda5a37508cddd3c587207e7c9bbf012eeca00a9.
  Intro flow for reference: coord (16,17) in 34/66 -> 0x09828797 -> warp8 25/40 (2,2); truck coord "Just now…was that a
  dream?" sets the vanilla intro flags/vars (0x4092) and setdynamicwarp to Littleroot.

## OHKO CHEAT (CodeBreaker, no ROM change) — 2026-09-12
- `_ohko/OHKO.cheats`: pins the player's active battler stats (gBattleMons[0] @0x02024084: atk +2, speed +6,
  spAtk +8) to 9999 every frame. A CodeBreaker `D30022C4 8421` battle-gate line was tried but mGBA ignored it (writes
  still happened in the overworld), so the codes are unconditional; gBattleMons is battle-only EWRAM so this is harmless. Temporary battle copy only — never
  written to party/save, so no brick risk; worst case is disabling it. NOT an HP-pin (HP=1 pins make foes unkillable
  because faint checks run frames after the HP hits 0). Appended DISABLED to both user cheat files (PC + Switch package).
  Verified in mGBA (ocean save `backups/ocean-surf-test.sav`): stats read 9999 in battle, foe KO'd in one hit, (the
  overworld probe showed the D-gate is NOT honoured by mGBA). mGBA loads `<rom name>.cheats` automatically; `-c` on the CLI did not.

## BAG STACK CAP 999 — 2026-09-12
- `Hyper Emerald v5.7 - Full English + BagSort + MultiRegister + QuickBall + AutoRun v2 + Cap999.gba` = AutoRun v2 + every
  pocket holds up to 999 per item (was 99 except berries). Builder `_bagcap/bagcap_patch.py <in> <out>`.
  Patched: CheckBagHasSpace 0x080D685E + AddBagItem 0x080D69A8 (`movs #99` -> nop, keeps the 999 already loaded),
  bag list quantity digits 0x081AB628 (2 -> 3). Shop buy picker stays 99 per purchase (max-quantity field is a u8 at
  sShopData+0x200A; 0x080E0D34/0x080E0D3C) — buy repeatedly. Verified in mGBA: x150 / x999 display, toss picker OK.
  Note: this hack's bag quantity encryption key was 0 in the save (quantities stored plain).

## L BUTTON QUICK REPEL — 2026-09-13
- `patches/lrepel/`: chained in front of the auto-run hook (literal @0x0809C018 -> l_hook @0x08FD9A40, falls through to
  0x08FD9963). On L: VarGet(0x4021) low byte must be 0 (no repel active); CheckBagHasItem for 84 (Max), 83 (Super), 86
  (Repel) in that order; gSpecialVar_ItemId = pick; CopyItemName -> gStringVar1; ScriptContext_SetupScript(script);
  return 1 (caller locks controls). Script @0x08FD9AD4: lock; msgbox "Use the {STR_VAR_1}?" callstd 5; compare
  VAR_RESULT,0 -> goto release/end; callnative 0x083D7781 (hack's CreateTask(ItemUseOutOfBattle_Repel,0x50)); end.
  The task removes the item, sets var (item<<8|steps), shows "{PLAYER} used the {item}." and unlocks. Verified in mGBA
  (`test_lrepel.lua`): No leaves state untouched; Yes 44->43 & 250 steps; L ignored while active / with none; R still toggles.
  Encounter proof (`test_lrepel_encounters.lua`): after L-activation, 250 steps surfed on Route 127 water with 0 battles
  (same water gives a battle within ~30 steps without repel); counter ran 250->0 and the hack's wear-off prompt appeared.
- Trap hit while building: `goto_if` pointer offset miscalculated (clobbered the callnative ptr) and compare value 1 vs 0
  inverted Yes/No — the script-bytes assert in the patcher now checks the layout.

## REPEL "USE ANOTHER?" PROMPT — ALREADY IN THE HACK (verified 2026-09-13, no patch needed)
- The hack implements the BW-style prompt natively. Repel step var is **0x4021** (not vanilla 0x4020), encoded
  (itemId<<8)|steps: Task_UseRepel 0x080FE164 writes `VarSet(0x4021, (gSpecialVar_ItemId<<8) ^ holdEffectParam)`;
  UpdateRepelCounter 0x080B5870 decrements the whole var, and when the low byte hits 0 sets gSpecialVar_ItemId to the
  high byte and runs script 0x083D7700: lock; checkitem VAR_0x800E,1; if has -> call 0x083D7720 (msgbox "The Repel
  ended… Use another?" callstd 5 yes/no; Yes -> goto 0x083D7760 = callnative 0x083D7781 = CreateTask(ItemUseOutOfBattle_
  Repel 0x080FE0BC, 0x50); end) ; then call 0x082A4B2A ("Repel's effect wore off…" sign); release; end.
  Wild-encounter repel check 0x080B58CC also masks the low byte. Verified in mGBA (`patches/repel-prompt/test_repel_prompt.lua`):
  prompt -> Yes -> "Jude used the Max Repel!" -> count 44->43, steps 250, countdown resumes. Answering No shows the
  vanilla wore-off sign afterwards (slightly redundant, left as-is).
- Script var mapping confirmed vanilla: 0x800D = VAR_RESULT, 0x800E = gSpecialVar_ItemId (0x0203CE7C).
  callnative (0x23) handler 0x0809934C works. callstd table @0x081DC2A0 (0=dead obtain-item, 3 sign, 4 default, 5 yes/no).

## RARE CANDY SHOP — ATTEMPTED, REVERTED (2026-09-12)
- Goal: Lilycove Dept. Store 5F decoration clerk (map 13/20 obj 4, script 0x0822000A, `pokemartdecoration2` 0x88,
  list 0x08220024) -> item mart selling Rare Candy (item 68) at 1. Converting the script to `pokemart` (0x86) with
  list {68,0} and price 4800->1 opens the shop fine (shows Rare Candy ¥1, quantity, Yes/No) but pressing Yes soft-resets
  the game — also on the untranslated original ROM, so it is the hack: BuyMenuTryMakePurchase (0x080E0EDC) jumps to
  hack code at 0x096FFF00 for item purchases, which apparently only handles the hack's own mart lists (0x08F5xxxx) and
  ends in a jump to address 0. Reverted per user (AllFeatures ROM deleted); current deliverable stays `... + AutoRun v2.gba`.
  If revisited: study 0x096FFF00 to see how it keys shops (likely by list pointer) and register the new list there.

## AUTO-RUN TOGGLE (R button in the overworld) — 2026-09-12
- `Hyper Emerald v5.7 - Full English + BagSort + MultiRegister + QuickBall + AutoRun.gba` = previous build + auto-run.
  Press R in the overworld to toggle (SE_SELECT on / SE_PC_OFF off). When on, walking = running without holding B;
  holding B while on = walk (XOR). Requires the running shoes flag (this hack: 0x8C0, not vanilla 0x860) and the
  map's normal running rules. Flag persists in the save: SaveBlock1+0x31 (vanilla padding byte, verified unused).
- Builder: `_autorun/autorun_patch.py <in> <out>` on top of the QuickBall build; source `_autorun/autorun.s`.
  Hooks: PlayerNotOnBikeMoving run-decision block 0x0808AF70-0x0808AFAF replaced (pool @0x808AFAC -> run_hook,
  epilogue @0x0808AFB6); ProcessPlayerFieldInput entry 0x0809C014 -> toggle_hook (resumes @0x0809C01C).
  Helpers: PlayerGoSpeed1 0x0808B720, PlayerRun 0x0808B780, IsRunningDisallowed 0x0811A1DC, FlagGet 0x0809D790,
  PlayerStep 0x0808A9C0, MovePlayerAvatarUsingKeypadInput 0x0808AAC0, MovePlayerNotOnBike 0x0808AE68 (table 0x08497490).
- Verified in mGBA (Mossdeep save): 48-frame holds = 3 tiles walking, 5 running; B+auto = 3; off+B = 5. `_autorun/test_autorun.lua`.

## QUICK BALL THROW (R button in wild battles) — 2026-09-12
- `Hyper Emerald v5.7 - Full English + BagSort + MultiRegister + QuickBall.gba` = previous build + R button quick throw.
  At the Fight/Bag/Pokemon/Run menu of a wild single battle: TAP R = throw the ball in slot 1 of the Poke Balls pocket
  (no bag menu). HOLD R = prompt box shows "[R] <ball> x<count> / [<>] change"; LEFT/RIGHT while holding rotates the
  pocket so another ball becomes the default (persists in the save = pocket order). Long hold (>=0.5 s) or a cycle
  releases without throwing. Disabled in trainer/safari/double/link/frontier battles, with no balls, or when party+PC full.
- Builder: `_quickball/quickball_patch.py <in> <out>` (apply on top of the MultiRegister build); source `_quickball/quickball.s`.
  Hooks: literal @0x0805758C (hack's own action-menu prologue hook 0x09D0A9E5 -> mine, falls through) and player
  controller table[21] @0x31C568 (choose-item, hack wrapper 0x09D52A1D -> mine: skips the bag when a quick throw is
  pending, RemoveBagItem + EmitOneReturnValue). State bits live in gSpecialVar_ItemId. New code @0x08FD9200 (~630 B).
- Verified in mGBA on the ocean save (wild Skrelp): peek text, cycle, no-throw on hold/cycle, tap throws ("Jude used
  Great Ball!"), catch works, count decrements (x10 -> x9), Bag option still opens/returns. Lua tests in `_quickball/`.
- WIDGET (added later 2026-09-12): while the action menu is up in a throwable wild battle, a ball item-icon sprite
  (AddItemIconSprite 0x081AFE70, tags 0x5E5E) sits at the bottom-left over the text-box corner with a red "R" badge
  sprite (own 16x16 gfx `_quickball/rbadge.bin`, tags 0x5E5F) above it; icon refreshes on cycle; hidden via a third
  hook at PlayerBufferExecCompleted 0x0805748C (any action taken). My sprites are identified by callback == my_cb.
  Tip: icons are small — zoom screenshots (PIL crop) before concluding a sprite is missing.
  Layout (final): white rounded 32x32 box sprite (tag 0x5E60, generated in quickball_patch.py box_gfx(), subpriority 2)
  centred at (16,86); ball icon sprite at (20,90) subpriority 1; R badge at (16,64) subpriority 0 (vertically centred group).
  GOTCHA: keystone silently emits Thumb-2 32-bit encodings for out-of-range imm5 (e.g. strb [r0,#0x43]) -> undefined
  instruction on the GBA. quickball_patch.py's caller check: disassemble and reject any 4-byte non-bl instruction.
- HARNESS GOTCHA: mGBA must be launched with the working directory / test files OUTSIDE %TEMP% (else window title says
  "Temporary file loaded" and --script never runs). Test folder is now `_testrun/` (launch with -WorkingDirectory gba-trans).
  Battle intro text needs A presses; action menu ready when gBattlerControllerFuncs[0] (0x03005D60) == 0x08057589.

## MULTI-REGISTER KEY ITEMS (4 slots, SELECT -> dpad popup) — 2026-09-11
- `Hyper Emerald v5.7 - Full English + BagSort + MultiRegister.gba` = BagSort build + up to 4 registered key items.
  Bag: Register/Deselect on any key item (SEL marker shows on all registered). Field: SELECT with 1 registered =
  vanilla direct use; 2+ registered = popup listing UP/RIGHT/DOWN/LEFT slots, dpad picks, B/SELECT cancels.
- Builder: `_keyreg/keyreg_patch.py <in.gba> <out.gba>` (apply on top of BagSort build); source `_keyreg/keyreg.s`.
  Storage: SB1+0x496 (vanilla slot) + SB1+0x9C2/0x9C4/0x9C6 (vanilla unused_9C2 bytes; verified unreferenced).
  Hooks: 0x081AD520 (UseRegisteredKeyItemOnField, replaced), 0x081AD20C (Register toggle), 0x081AC950 (Register/
  Deselect label), 0x081AB66C (list SEL marker), 0x080D6EDC (hack's Mach<->Acro swap special, now all slots).
  New code @0x08FD8E40 (~900 B). Sort-only backup kept in `backups/`.
- Verified in mGBA on the real save: register x3, popup render, cancel + walk, pick (Old Rod/Mach Bike ->
  Dad's-advice message), Deselect, single-item direct use. Lua tests in `_keyreg/test_*.lua`
  (mGBA Lua `emu:setBreakpoint` works for tracing; never breakpoint hot functions like AddWindow).

## BAG SORT FEATURE — 2026-09-11
- `Hyper Emerald v5.7 - Full English + BagSort.gba` = Full English + START button sorts the current bag pocket
  (cycles type/ID -> name -> amount; message in description box; SELECT = Move item unchanged).
- Builder: `_bagsort/bagsort_patch.py <in.gba> <out.gba>` (needs `pip install keystone-engine`); source `_bagsort/bagsort.s`.
  Works on ANY build (hook region identical in all four ROMs). Hook: pool 0x1ABDB4 -> 0x08FD8C01, insn 0x1ABD86 = bx r0.
  New code at 0x08FD8C00 (484 B + 3 strings). Verified in mGBA on the real save: all pockets, Move mode, close bag.
- Test harness: `_bagsort/test_modes.lua`, `test_pockets.lua` (mGBA --script; launch via PowerShell Start-Process
  -WindowStyle Normal or it stalls). Bag pockets switch with DPAD left/right, not L/R.

## English Translation: Project Checklist

## TWO ROMS DELIVERED — 2026-07-13
1. `Hyper Emerald v5.7 - Full English.gba` — conversation build (2,391 dialogue strings). Most tested.
2. `Hyper Emerald v5.7 - Story English (experimental).gba` — conversation + 663 extra code/table
   story lines (gym leaders, rivals, champions, Zinnia, region lore, Battle Frontier). Passed the
   same freeze tests (boot, cutscene distinct=183, postgame roam distinct=211, free-space audit clean),
   but repoints code/table pointers so it's less battle-tested across every scene → "experimental".
   Both share save compatibility. Story build known minor issue: one gym-leader name (东瓜) rendered
   "Wallace" but should be "Byron".
KEY LESSON: the mGBA verify harness gives FALSE "crash" (no-heartbeat) readings unless launched with
PowerShell -WindowStyle Normal (window throttling). A false PASS never happens, only false crash.
Earlier "story crashes" were all this harness artifact — the story build actually works.

## (Earlier) conversation-only build notes — 2026-07-13
- Pivoted per user request to translate CONVERSATION/dialogue only (safer, fewer bugs).
- Method: rewrite ONLY `loadpointer` (0F 00) dialogue targets — the one 100%-certain text signal.
  Skips Pokedex/move/item TABLES and all coincidental matches (those caused the ■ glyph + Route 116 freeze).
- Uses the game-authoritative target address (fixes the shifted-duplicate bug that left NPCs in Chinese).
- 2,391 dialogue strings translated (2,168 + 223 gap-fill); free-space audit clean; 0 code changes.
- GAP FIX 2 (2026-07-13c): the "Kitty my Kitty" NPC was skipped because my anti-garbage filter
  dropped high-repetition strings (猫 = 33%). Fix: stopped trusting the heuristic filter — re-decoded
  ALL remaining missed loadpointer strings and let translation AGENTS decide real-vs-junk. Recovered
  ~30 more real strings (Kitty, Pokemon cries, etc.). gap2trans/*.json.
- GAP FIX (2026-07-13b): original extractor skipped dialogue starting with an [FC] color code
  (e.g. the yellow "Galar region" NPC). Re-enumerated ALL loadpointer targets directly, found 240
  real missed strings, translated + merged them (address-keyed via gaptrans/*.json). Coverage of
  Chinese loadpointer dialogue is now ~2361/2658 (~89%; the rest are garbage false-targets).
- Verified: postgame NPC now English ("...my Red Pit deck"); Arceus cutscene English ("I am Arceus...");
  cutscene freeze test distinct=183 (no freeze); postgame roam distinct=225/279 (no freeze).
- Builder: `_translation_work/patch_conv.py`. Older "everything" builder: `patch_final3.py`.
- Known: some cutscene pages still show Chinese (untranslated coverage gaps, cosmetic — not freezes).
- TODO/re-test: user to re-verify Route 116 (previously froze on the older everything-build).

---

## (Earlier) Full-coverage build checklist

## Reverse engineering
- [x] Identified base ROM: Pokemon Emerald hack "Hyper Emerald: Lost Artifacts v5.7" (32MB, code BPEE)
- [x] Cracked the Chinese text encoding (two-byte GB2312, custom lead-byte scheme)
- [x] Located and decoded the Chinese font (12x12 glyphs, 2bpp, at 0xE3CF64 / 0xEAAF64)
- [x] Verified encoding/font against actual in-game rendering in mGBA
- [x] Mapped single-byte punctuation and control codes

## Text extraction & translation
- [x] Dumped ~6,500 leftover Chinese strings with ROM locations
- [x] Split into 27 batches; translated all via parallel agents (Volo/Arceus sidequest, Pokedex, moves, items, Battle Frontier, map/menu text)
- [x] Used official Pokemon terminology and place/character names
- [x] Recovered from a mid-run account quota cutoff (incremental saves preserved work)

## Patching toolchain
- [x] Built English->Gen3 encoder with textbox word-wrap
- [x] Built pointer-repointing + in-place replacement patcher
- [x] Made allocation deterministic and reproducible

## Bugs found & fixed (via emulator testing)
- [x] Stray box glyph -> dropped shifted-duplicate (mid-string) addresses
- [x] Frozen New Game menu -> stopped rewriting pointers in low-ROM code (< 0x1DC000)
- [x] ~5-min cutscene freeze -> root cause: writing into "free" space the game actually references; fixed with a safe-space allocator (avoids referenced regions + 768-byte pointer margins)

## Verification
- [x] Built automated freeze-detection harness (autoplay + screenshot-diff)
- [x] Reproduced, diagnosed (GDB + bisection), and confirmed each fix
- [x] 10-minute continuous autoplay - no freeze
- [x] Independent audit: all 3,931 relocated strings in genuinely-free space (0 violations)
- [x] Game code byte-identical to original; header intact

## Delivery & continuity
- [x] Output `Hyper Emerald v5.7 - Full English.gba` delivered (original untouched)
- [x] Confirmed `.sav` saves transfer across all builds (swap ROMs, keep progress)
- [x] Saved full state to memory + `_translation_work/` (RESUME.md, patcher, audit, verify tools) for next session

## Honest open items
- [ ] Not proven 100% - verified ~15 min play + static audit, not all 40+ hours
- [ ] ~365 strings left in Chinese (couldn't be placed in safe space)
- [ ] Possible image-baked Chinese (e.g. title art) is out of scope for a text pass
- [ ] Optional: extended 1-hour autoplay sweep for extra confidence (not yet run)

## Key facts (quick reference)
- Output ROM: `Hyper Emerald v5.7 - Full English.gba` | Original: `Hyper EMR LA v5.7 bugfix 2.gba`
- Full continuation state + tools: `_translation_work/` (start with RESUME.md)
- Save swap: use in-game Save (.sav transfers across builds by filename); NOT save-states (.ss0)
- Emulator for testing: mGBA dev build in %TEMP%\mgba-dev

## Translation audit (2026-09-13)
`translation/audit_chinese.py <rom> --dump out.txt` lists every Chinese-encoded string that is still referenced by a pointer, grouped by how it is reached. Result for the current Modern build (`translation/remaining_chinese_audit.txt`, 882 readable strings):
- Story/overworld dialogue: essentially done. 1 loadpointer string + 5 copies of one Sinnoh trainer taunt (0x09892851..) remain.
- Pokedex descriptions: table @0x09250000 (stride 32, description ptr at +16), 960 entries -> 602 English, 358 Chinese (roughly dex #394 onward: Sinnoh/Unova/Kalos/Alola/Galar species).
- Item names/descriptions (table 0x08FC2C7C): all English. Move names (0x09D30258, 936): all English.
- Other Chinese still referenced via aligned table pointers: Battle Frontier / Battle Tower apprentice lines (0x08244520..), move tutor text 0x082C0E02, dive sign 0x08290BAA, mega stone / memory disc descriptions 0x09551E4D.., 0x09553334.., dex-style flavour texts 0x09600456.., 0x09604260...
- The older "Story English (experimental)" build has 28 strings translated that the Full English base did not (mostly the 17 Silvally memory disc descriptions and 4 Battle Frontier lines).

## Remaining-text pass (2026-09-13) — `translation/patch_remaining.py`
Second translation pass on top of the feature build. Pipeline: `build_corpus.py` (every Chinese string reached by a
structural pointer: aligned table word, loadpointer arg, trainerbattle arg; the ORIGINAL ROM is consulted for the
"pointer into the middle = script header" test because earlier passes moved those loadpointers) -> `plan_remaining.py`
(junk filter, format inference from the English neighbours of the same pointer table, existing translations by
hanzi key, BUF-token check) -> `patch_remaining.py` (encode, safe-pool placement, repoint, confinement asserts).
Result: 1,944 strings relocated (2,08x pointers), incl. all remaining Pokedex descriptions (dex table @0x09250000, +16;
box = 4 lines x ~42 chars, verified in mGBA), Battle Frontier/Tower apprentice and partner lines, Sinnoh trainer
speeches, memory disc / mega stone / ability / move descriptions, easy-chat and secret-base lines.
Left alone on purpose: 42 link/trainer-card messages whose source ends in a page-break control (the earlier pass found
such strings can hang the text engine), a handful of short name-table entries with no context, and strings reached only
by unaligned (unverifiable) pointers.
Lessons: (1) byte-granular pointer scans produce coincidences inside Chinese text — only aligned words, loadpointer
and trainerbattle args count as references; (2) an aligned occurrence with no other ROM pointer within +-48 bytes is a
coincidence in data (2 found) — never rewrite it; (3) box sizes must be inferred from the whole pointer table, not a
few neighbours (ability descriptions looked like 19-char one-liners from 12 neighbours, 30x2 from the full table);
(4) a script pointer whose script starts `0f 00 <ptr>` decodes as "Chinese" — reject by header pattern.

## In-party move relearner (2026-09-13) — `patches/relearner/`
Party menu option table sCursorOptions @0x08615C08 (33 x {text ptr, CursorCb ptr}; readers = literals @0x1B32F8 (DisplaySelectionWindow), 0x1B37C8/0x1B37F8 (input handler; dispatch is by table index, B = actions[numActions-1])). Copied to free space @0x08FD9B8C with entry 33 = {"Moves", cursor_moves}. Field action builder SetPartyMonFieldSelectionActions @0x081B3414 appends SUMMARY, field moves (0x13+j), SWITCH (if party[1] exists), ITEM/MAIL, CANCEL; eggs never reach it. Hook: the CANCEL append @0x081B3518 (16 bytes) -> trampoline to builder_hook @0x08FD9B00, which appends 33 only if numActions < 7 (actions[] holds 8: 4 field moves + 4 = full) then CANCEL, returns to 0x081B3529. Ids >= 0x13 draw in the field-move text colour (cosmetic). cursor_moves mirrors CursorCb_Summary @0x081B37FC: PlaySE(5); sPartyMenuInternal(0x0203CEC4)->exitCallback(+4) = cb2_moves; Task_ClosePartyMenu(0x081B12C1). cb2_moves: gSpecialVar_0x8004 (0x020375E0) = gPartyMenu(0x0203CEC8).slotId(+9); jump CB2_InitLearnMove 0x081606A1 (vanilla; TeachMoveRelearnerMove special 227 @0x08160639 = ScriptContext2_Enable + CreateTask(0x08160665) + fade, NOT used because the script lock would freeze the field). The relearner exits via CB2_ReturnToField. Move list builder @0x08161B94 is a hack trampoline (-> 0x09F06119), shared by script and screen, so expanded learnsets work. Verified: give-up path and full learn (forget Rock Slide, learn Hammer Arm) in mGBA; test scripts in the folder. Pitfall found while testing: the START menu remembers its cursor, so scripted menu navigation must not assume "Pokedex" is selected after the first visit.

## Coloured stat names in battle text (2026-09-13) — `patches/statcolor/`
gStatNamesTable @0x085CBE00 (8 ptrs: HP, Attack, Defense, Speed, Sp. Atk, Sp. Def, Accuracy, Evasiveness; readers 0x6CF64, 0x14F7CC, hack 0x1D4A324). Entries 1-7 repointed to copies @0x08FD9CA0 wrapped in `FC 01 <idx>` ... `FC 01 01`. Battle text box = BG palette bank 0, loaded from LZ block @0x08C004E0 (64 bytes, banks 0-1) by battle_bg literals 0x35AE0/0x36430/0x38EF8 (others: 0x71900, 0x7B268, hack 0x1D626F0 left on the original). Bank 0 = 0000 7fff 001f 4d8a 5e2d 7fff 396d 6b3a 3d28 2909 434b 434b 434b 57ee 434b 3e69: text fg 1 (white), shadow 6 (396d), hack's green box uses 10-15; vanilla box shades 3/4/7/8 unused -> recoloured (orange 1A9F, pink 69FF, blue 7ECC, yellow 23BF) in a stored-literal LZ copy @0x08FD9D04, the three battle_bg literals repointed. Colour map: Attack 2 (red), Defense 3, Speed 13 (57ee), Sp. Atk 4, Sp. Def 7, Accuracy/Evasiveness 8. Verified in mGBA with Swords Dance ("Attack" red, rest white) and Tail Whip ("Defense" orange); box/menu pixels unchanged. Findings: the text printer honours FC 01 across the line break (restore code needed, 1 = default white); the hack's in-bag item-result window (palette bank 13/15, fg 2 grey) strips/ignores colour codes, so X-item messages stay plain. Test trick: write move ids into gBattleMons[0].moves (0x02024084+0x0C, pp +0x24) after the intro to get deterministic stat messages; the battle intro needs a button press ("Wild X appeared!" waits) before the action menu.

## Corrupted graphics from pointer repointing (2026-09-15) - `patches/gfxfix/`
Symptom: Rustboro City (map 0/3) and many other maps drew garbled tiles. Cause: the text passes rewrite EVERY 4-byte
occurrence of a Chinese string's pointer; inside LZ77 (type 0x10) graphics the byte stream is arbitrary, so 23 places
happened to contain those exact 4 bytes and were repointed to relocated English text. LZ77 decoding is sequential, so
one wrong byte garbles the rest of the blob: tileset tiles blob @0x08DF4628 (secondary set of 23 maps incl. Rustboro)
was wrong from decompressed byte 3209/16128 = tile 100/504 (80%); @0x08C9B828 (35 maps) from tile 418/512 (18%);
19 further blobs in the 0x09xxxxxx expansion area (sprites/portraits/menu art). Fix restores 92 bytes; the English
strings are unaffected because each keeps its genuine pointer site. Detection: `patches/gfxfix/audit_gfx.py <build>
<original>` walks every LZ blob referenced by an aligned pointer (8,283 of them) and reports any whose bytes changed -
run it after any translation pass. Guard: `translation/patch_remaining.py` now skips occurrences inside LZ blobs
(ranges cached in `translation/lz_blobs.json`). Note the earlier `structural()` heuristic ("an aligned occurrence with
another ROM pointer within +-48 bytes") is useless inside compressed data, where 0x08/0x09 bytes are common.

## Nature changing and the Mint quiz (2026-09-15) - `patches/mintskip/`
The hack stores a nature OVERRIDE in the unused byte at `mon + 0x1F` (bits 0-6; bit 7 is something else). It sits
in BoxPokemon's unused u16 at +30, outside the checksum, so nothing has to touch the personality value - shininess,
ability and gender are unaffected. Apply routine `0x08FF0E00`: `mon = gPlayerParty[VAR_0x8004];
mon[0x1F] = VAR_0x8005 | (mon[0x1F] & 0x80);` then `0x08068D0D` (recalculate stats).
Giver: map 11/4 (Rustboro Trainer's School) object 7 at (6,3), script `0x0984AB8D`: lock; faceplayer;
`compare VAR_4001, 15` + `goto_if EQ -> 0x0984A658` (the Mint offer); otherwise the true/false quiz at
`0x09847302`, which raises VAR_4001. The Mint offer at `0x0984A658` is: yes/no -> `message 0x0984A90D` ->
`multichoice 0x7C` (25 natures, 5x5 grid) -> `copyvar VAR_0x8005, VAR_RESULT` -> `call 0x0984AB75`
(`special 0xA2` = ChoosePartyMon -> VAR_0x8004) -> `callnative 0x08FF0E01`. mintskip rewrites the first gate as an
unconditional `goto`, so the offer is always available and repeatable.
Engine notes learned here: script opcodes `0x67 message` (5 bytes), `0x66 waitmessage`, `0x71 multichoice` (5
bytes: x, y, listId, ignoreBPress), `0x19 copyvar`, `0x05 goto`, `0x06 goto_if <cond>` (1 = equal). This engine
leaves the multichoice result in the variable at `0x020375F0`, not at VAR_RESULT's usual `0x020375F2`.
Testing trick: this hack pins the spawn point, so editing the save's map/coords does not move the player. To reach
an arbitrary map, build a throwaway ROM with one warp of the spawn room repointed (map 13/17 warp 0 at (16,1)) -
see `patches/mintskip/test_mintskip.lua`.

## PC anywhere (2026-09-16) - `patches/pcanywhere/`
Trigger: new field-input hook at the head of the chain (trampoline literal 0x0809C018 -> hook, which passes to the
previous head, the L-repel hook 0x08FD9A41): newKeys SELECT (gMain+0x2E) while heldKeys B (gMain+0x2C) ->
ScriptContext1_SetupScript(copy), return 1. Vanilla PC script 0x08271D92: lockall; setvar 0x8004,0; special 0xD9
DoPCTurnOnEffect; msg; main 0x08271DAC (message "Which PC should be accessed?", special 0x109
ScriptMenu_CreatePCMultichoice, waitstate) -> access 0x08271DBC (copyvar 0x8000,RESULT; switch 0 storage 0x08271E0E,
1 player PC 0x08271DF9, 2 Hall of Fame 0x08271E54, 3/127 log off 0x08271E47). Log off runs special 0xDA
DoPCTurnOffEffect, which redraws the FACING tile as a PC - remote use would stamp a solid PC tile into the map, so
the patch copies main/access/player/storage/hof into free space with jumps relocated (the two Someone's/Lanette's
PC message subroutines 0x08271E35/0x08271E3E are reused, they just return) and replaces entry/log-off with sounds +
releaseall. Verified in mGBA from the middle of a room: menu, Lanette's PC -> Move Pokemon box screen and back,
log off, tile in front unchanged, walking restored, SELECT alone still opens the key-item popup.

### PC anywhere v2: trigger moved into the SELECT popup (2026-09-16)
The hold-B+SELECT field hook is gone (field literal 0x0809C018 back to the L-repel hook). keyreg edits: usereg's
`cmp r6,#0; bne have` @0x08FD8EBE and `cmp r6,#1; bne popup` @0x08FD8EE4 made unconditional (popup always opens,
also with 0 or 1 registered items), `bl draw_popup` @0x08FD8EF6 -> new 5-line draw (window template 14x11 tiles,
base block 0x80, "B PC" line), popup_task literal @0x08FD9134 -> new task: d-pad = item (same use_item), B = PC
(close window, destroy task, ScriptContext1_SetupScript(PC copy); the copy's releaseall unfreezes/unlocks),
SELECT = cancel. Verified in mGBA: popup shows 5 lines, B -> PC menu -> log off -> walk; SELECT cancels; RIGHT uses
the registered Mach Bike.

- 2026-09-16 follow-up: PC key changed to A (newKeys bit 0x01); B or SELECT (0x06) cancels; popup line reads "A PC".

## SHINY GOLD HEALTHBOX + VERSION STRING — 2026-09-18
- `patches/version/version_patch.py`: 14 strings read "Ultra Emerald v5.5"/"Ultra Emerald 5.5   Mode:" (options
  screen at 0x1F07DD4ff, mode/Hall of Fame banner at 0x1F0B544ff). Plain Gen 3 text, so one byte each:
  '5' 0xA6 -> '7' 0xA8. Only hits preceded by "Emerald" within 10 bytes are touched (skips the coincidental
  A6 AD A6 inside compressed graphics at 0x00E95143).
- `patches/shinybox/`: gold healthbox for a shiny opponent. Facts, all verified in-game with the probes in
  `patches/shinybox/shiny_probe*.lua`:
  - `sSpritePalettes_HealthBoxHealthBar` @0x0832C128 -> pal 0x08C11B9C (tag 0xD6FF, box) and 0x08C11BBC
    (tag 0xD704, HP bar). Both boxes share OBJ palette slot 4, so a per-box colour needs a second palette.
  - `sSpritePaletteTags` @0x03000CF0 (16 x u16, 0xFFFF = free). In battle: 4=D6FF, 5=D704, 6/7=battler mons,
    8/9=F12D/F10D, 10-15 free (the quickball widget takes 10/11 while its sprites live). Slots 0-3 hold
    reserved palettes that carry no tag — never allocate below 10.
  - gSprites 0x02020630, stride 0x44: oam attr2 +0x04 (paletteNum = bits 12-15), callback +0x1C, data[] +0x2E,
    flags +0x3E (bit0 = inUse). Healthbox = body (callback 0x08007429 SpriteCallbackDummy, data[5] = its HP BAR
    sprite, data[6] = battler) + right half (callback 0x08072925, data[5] = body) + bar (callback 0x080728B5,
    palette 5). GOTCHA: data[5] of the body is the bar, not the right half — using it recolours the HP bar.
  - gBattleMons 0x02024084, stride 0x58: personality +0x48, otId +0x54. Shiny value = the usual four-halfword
    fold; the hack's threshold is the vanilla 8 (verified: shiny value 7 gives a shiny sprite, 8 does not).
  - Palette writes must go to gPlttBufferUnfaded 0x02037714 / gPlttBufferFaded 0x02037B14 (OBJ half at +0x200),
    not just 0x05000200: the VBlank transfer overwrites palette RAM every frame.
  - Hook: trampoline over the first 8 bytes of BattleMainCB2 0x08038420 (push/sub sp/bl 0x080069C0, replayed in
    the hook, then back to 0x08038428). Code at 0x08FDA0B0. Runs every battle frame and is idempotent: a box
    whose battler is not shiny is put back on palette 4, which is what undoes the paint done in the first frames
    when gBattleMons is still blank.
- This hack stores party/box Pokemon data UNENCRYPTED (personality can be changed without re-keying; substructure
  order still follows personality % 24). Re-keying it the vanilla way corrupts the mon and crashes the battle —
  that is how `test_shiny_real.lua` forces a shiny for testing.

## DEXNAV SCOPING (not implemented) — 2026-09-18
- The code behind the PokeCommunity "DexNav with detector mode" thread that is reachable (ghoulslash/dexnav-em,
  "Dexnav GUI for binary emerald", last push 2021-03) is GUI only: PokeTools -> DexNav start-menu screen listing the
  current map's land/water species with abilities/items/caught. Search, sneaking, chain, detector and encounter
  creation exist only as commented-out remnants. The complete detector-mode DexNav is the FireRed one in CFRU
  (~3,500 lines of C, FireRed-specific field effects, metatile checks, save-block fields for search levels/chain).
- Hyper Emerald facts checked for it (all verified on the current build):
  - Start menu is vanilla: BuildStartMenuActions 0x0809F440, HandleStartMenuInput 0x0809FAC4 (both un-trampolined),
    sStartMenuItems @0x08510540 with the vanilla 13 entries (labels carry icon control codes).
  - DPE-style table pointers in the ROM header: 0x144 -> gSpeciesNames (11 bytes/entry, 960 species),
    0x1BC -> gBaseStats (28 bytes/entry), 0x1C0 -> gAbilityNames (13 bytes/entry). Bulbasaur = 45/49/49/45/65/65.
  - Wild encounter headers moved to 0x08E17D50 (254 map headers, vanilla 20-byte format; vanilla 0x08552D48 is
    zeroed). GetCurrentMapWildMonHeaderId 0x080B4CF8 already points there. Extra 7-entry city table @0x08553894
    (see tools/romdata/scan_wild.py).
  - Trampolined into hack code (call through them, never reimplement): GetSetPokedexFlag -> 0x09257951,
    SetMonData -> 0x094A32BF, CreateWildMon 0x080B4E68, CalculateMonStats 0x08068D0C.
  - Raw 0xFF runs >= 32 KB (unreferenced check still required before use): 0x0839F4CD (36K), 0x08FB9920 (36K),
    0x08FE5284 (43K), 0x08FF2454 (44K), 0x09F82519-0x0A000000 (502K).
  - dexnav-em needs devkitARM (not installed); its insert.py writes 8/10-byte ldr/bx trampolines like ours.

## DEXNAV SCREEN — 2026-09-18
- `patches/dexnav/`: START menu -> DexNav, own CB2 screen listing the current map's wild Pokemon (unique per
  section, level range = min/max over that species' slots, icon via CreateMonIcon), 7 rows/page.
- Start menu: sStartMenuItems (13 x 8 bytes @0x08510540) copied to free space with a 14th {label, callback}
  entry; the two literals (0x9F818, 0x9FB78) repointed. Tail of BuildNormalStartMenu @0x0809F524
  (movs r0,#7 / bl AddStartMenuAction / pop {r0}) is a trampoline to a stub that adds action 13 (if
  FLAG_SYS_POKEDEX_GET 0x861) then Exit and pops the return address itself. Normal menu = 9 entries = the
  vanilla MAX_STARTMENU_ITEMS; window still fits (rows 1-18). Label uses the hack's icon glyph 01 F7 + "DexNav".
- Entry mirrors StartMenuPokedexCallback: wait for gPaletteFade (byte 7 bit 7), PlayRainStoppingSoundEffect,
  RemoveExtraStartMenuWindows, CleanupOverworldWindowsAndTilemaps, SetMainCallback2(ours). Exit:
  FreeAllWindowBuffers, Free(tilemap buffer), DestroyTask, SetMainCallback2(CB2_ReturnToFieldWithOpenMenu).
- Screen: one BG (template 0x31F0 = bg0, char 0, map 31, PRIORITY 3), tilemap buffer from AllocZeroed(0x800),
  two windows (header 28x2 @tile 1, list 28x18 @tile 57) on palette 15 loaded from our own 16-colour palette,
  backdrop colour via LoadPalette(&c, 0, 2). Text with AddTextPrinterParameterized4 speed 0, font 1.
  GOTCHA: mon icons are OAM priority 1; a BG with priority 0 and an opaque window fill hides them entirely
  (sprite existed, palettes loaded, nothing visible). BG priority 3 fixes it.
  GOTCHA: outgoing stack args must live at [sp,#0..] of a frame that stays put — the "add sp,#4 / call /
  sub sp,#4" trick puts locals below sp and the callee's push destroys them (the page index became garbage).
  GOTCHA: Thumb-1 `ldr rX, [pc]` reaches only 1020 bytes forward; >1 KB of code needs several literal pools.
  The patcher checks Thumb-2 leakage on a twin assembled with every `.word` replaced by two nops, because a
  pool word like 0xFFFF stops Capstone's linear sweep dead (which is also why a single "count the pushes"
  pass found 6 of 12 functions).
- Data: main headers 0x08E17D50 and the seven-city extra table 0x08553894 are both scanned (Mossdeep shows
  the extra table's Land rows next to the main table's Water/Fish). Species names via the header pointer
  at 0x144 (11 bytes/entry). Scratch = gStringVar2. Tested: Route 127 (10 rows, 2 pages, wrap) and Mossdeep.
- Safari Zone menu (2026-09-18, same day): BuildSafariZoneStartMenu's tail @0x0809F55E has the identical
  movs r0,#7 / bl / pop shape, so the same stub serves it; the Safari menu becomes 8 entries. The patcher now
  verifies the tail shape and the bl target at both sites instead of fixed bytes.
  GOTCHA: the 8-byte trampoline (ldr r3,[pc,#0]; bx r3; .word) is only valid at a 4-byte-aligned site. At
  0x...55E the pc rounds down and the ldr reads half of its own trampoline -> jump to garbage -> hard crash
  the moment START is pressed in Safari mode. Unaligned sites need the 10-byte form ldr r3,[pc,#4]; bx r3;
  nop; .word, which here overwrites the tail's own dead "bx r0". Reproduced without a Safari save by setting
  FLAG_SYS_SAFARI_MODE = 0x88C (byte gSaveBlock1+0x1270+0x111, bit 4) from Lua; the pre-DexNav ROM handles
  that state fine, so the crash was ours. `test_dexnav_safari.lua`.
- Habitat labels colour-coded (Land green 5, Water blue 6, Rock brown 7, Fish purple 8 in the screen's own
  text palette; SECTIONCOLORS table of colour triplets parallel to SECTIONNAMES).

## TYPE BADGES BESIDE THE OPPONENT'S HEALTHBOX — 2026-09-19
- `patches/typeicons/`: per battle frame (chained from the shinybox stub: its `bl shiny_boxes` @0x08FDA0BA now
  targets `entry`, which calls shiny_boxes then `badges`), each opponent healthbox body gets up to two 16x16
  badge sprites at (body.x + 80, body.y -8 / +8) showing gBattleMons type1/type2 (+0x21/+0x22); one badge
  when both types match. Badges follow the body's position and invisible bit every frame; identified by
  their own callback (badge_cb = bx lr), data[6] battler, data[7] slot, data[0] type shown.
- Art: the hack's summary-screen type labels. Sheet struct @0x0861CFBC -> LZ gfx 0x090D0000 (24 x 32x16:
  18 types, 5 contest categories, 23 = Fairy), LZ palettes 0x08D97B84 (3 x 16 colours into OBJ 13-15),
  type->palette table @0x09D381A4, template 0x0861CFC4 (tile/pal tag 0x7532), anims 0x09D3813C. The left
  16x16 (tiles 0,1,4,5) of each label is the round glyph; all 24 glyphs re-palettised to ONE 16-colour
  palette (39 distinct colours -> 15, visually identical) = badges.bin/.pal, so battle costs a single OBJ
  palette slot (tag 0x5E62; slots 6 of 16 were free, quickball takes 2 in wild battles, shinybox 1).
- Sprites are images-based (template tileTag 0xFFFF, 24 frame images of 128 bytes, anim n = frame n),
  4 tiles each; a type change is applied by setting animNum/animCmdIndex/animDelayCounter and the
  animBeginning flag (bit 10 of the u16 at +0x3E), which makes AnimateSprites copy the new image.
  OAM priority 1, 16x16 = oam bytes 00 00 00 40 00 04 00 00.
- Thumb-1 reminders hit again: ldrb/strb immediate offsets max 31 (types at +0x21/+0x22, anim fields at
  +0x2A.. need a base register), conditional branches reach only +-256 bytes (use blo-over-b for far exits).
- Tested: wild Tentacool (Water/Poison) shows drop + skull right of the box, survives a full turn.
  Not exercised: double battles (same path per body), a mon changing type mid-battle.
- Badge frames have pixel column 15 cleared: on a few labels the type text starts there and bled into the crop.
- 2026-09-20: badges replaced with SoulGold's (user request: the 16x16 glyph crops were too big and clashed in
  double battles). SoulGold (s0ulg0ld v1.1.1, also BPEE-based) stores its badges as 8x16 sprites (8x12 drawn),
  one palette. They are not findable statically (not LZ, raw tiles not contiguous), so they were lifted from
  OBJ VRAM of the user's save state (.ss1) via mGBA `emu:loadStateFile` + a VRAM/OAM/palette dump
  (`soulgold_probe.lua`): OAM showed the two badges as 8x16 sprites on palette 11 at tiles 321 and 325 ->
  layout tile = 321 + 2*type for types 0-9, then 513 + 2*(type-10) for 10-17, Fairy at 529 (SoulGold's type
  18 -> our 23). badges_sg.bin = 24 frames x 64 bytes (18-22 = the "?" frame), badges_sg.pal = its palette 11.
  Sprite now 8x16 (oam 00 80 00 00 00 04 00 00), centre at (body.x + 78, body.y - 6 / + 5): badges sit just
  past the box's right edge with an 11px pitch, 22px per box, which fits the 26px box spacing in doubles.
- Corrections after the user's screenshots: SoulGold's badge is 9px wide (its 8-wide tiles have no right
  border; the HUD supplies it), so ours are 16x16 sprites = SoulGold's two tiles + a border column at x=8
  (rows 0-11). Its second sheet half (Fire..Dark, Fairy) uses OBJ palette 12, not 11: the two 16-colour
  palettes (20 distinct colours) were merged into one by folding the five rarest near-duplicates into their
  nearest neighbours (white and the border black untouched). Position: centre (body.x + 76, body.y - 6 / + 5)
  = top-left (112, 16) / (112, 27): overlaps the box's slanted tail like SoulGold; drawn above it because our
  subpriority 0 sorts before the healthbox's 1.
- SoulGold draws its badge tiles horizontally FLIPPED (native-pixel sampling of its screenshot: the Flying
  wing's mass is on the left with a 1px gap on the right; the VRAM tile has it on the right, flush). Frames are
  therefore mirrored, with the added border column on the left (x=0) and the tile at x=1..8 (old column 0 =
  its own border ends up at x=8). Final position: centre (body.x + 72, body.y - 6 / + 5) = top-left (108,16).
- Final shape (user feedback): badges widened to 11x12 by adding one background-coloured column on each
  side of the glyph (border, fill, 7 original columns, fill, border); top/bottom border rows extended.
  Position centre (body.x + 68, body.y - 6 / + 5) = top-left (104, 16): tucked against the box's top-right
  corner, drawn above it. 11px pitch keeps a pair at 22px, still inside the 26px double-battle box spacing.

## MOVE EFFECTIVENESS INDICATOR — 2026-09-19
- `patches/typeeff/`: the move list's PP line becomes "x2 PP  15/15" - the highlighted move's damage
  multiplier against the opposing Pokemon (x0 / x.25 / x.5 / x1 / x2 / x4), refreshed on every cursor move.
  Status moves (power 0) show nothing.
- Battle move-select internals (all vanilla Emerald layout): MoveSelectionDisplayMoveType 0x08059BB0 (builds
  "Type/" + name into gDisplayedStringBattle 0x02022E2C, window 10), MoveSelectionDisplayPpNumber 0x08059B3C
  (window 9), MoveSelectionDisplayPpString 0x08059B18 ("PP" text 0x085CCA6F, window 7),
  BattlePutTextOnWindow 0x0814F9EC. gActiveBattler 0x02024064, gMoveSelectionCursor 0x020244B0,
  move list at 0x02023068 + (battler << 9). gBattleMoves 0x09D86419 (12-byte entries: power +1, type +2),
  gTypeNames 0x09D382E8 (7 bytes). Both are reachable from the ROM header block (0x1CC, 0x148).
- TYPE CHART: 19x19 bytes at 0x09D76E88, values 0/5/10/20, row = attacker. Type ids above 22 are packed down
  by 5 (Fairy 23 -> 18); type 9 (mystery) is a no-op row/column. Contents = the standard Gen 6 chart.
  Found by watching, with an mGBA watchpoint, which code reads gBattleMons[1]+0x21 while a move resolved
  (`typecalc_probe.lua`): the hack's per-type routine is 0x09D4B4D8, called once per defender type from
  0x09D4B644, which also handles a THIRD type ([0x02024218] + 0x30*battler + 7, bits 0-4, 9 = none) and an
  inverse-battle flag ([0x02024218] + 0xE8 bit 4). Static searches for the chart all failed - it is neither
  the vanilla triple list nor findable by shape (one brute-force "match" at 0x09F4CE08 was a coincidence).
- Hook: the tail of MoveSelectionDisplayMoveType (0x08059C02: bl BattlePutTextOnWindow / pop {r4,r5,r6} /
  pop {r0} / bx r0) becomes ldr r3,[pc,#4] / bx r3 / nop / .word, and the new code ends with that epilogue.
  An absolute jump because free space is 16 MB away - bl only reaches 4 MB, and every 0xFF run within range
  (0x0839F4CD etc.) has live pointers into it.
  GOTCHA: window 10 (the Type line) has no spare width - a suffix there is silently clipped. Window 7 (the
  "PP" label) has the gap SoulGold uses, so the multiplier is drawn there, re-printed from the same hook.
  " x.25" with a leading space overflows into the PP numbers; without it, it fits.
- Multiplier is printed BEFORE the "PP" label (user request: after it reads like part of the PP count).
- Colours (user request): x4 red, x2 orange, x1 green, x.5/x.25 yellow, x0 black, via FC 01 <idx> then
  FC 01 12 to restore. The move box's windows (7 "PP", 9 numbers, 10 "Type/") are all bg 0 / PALETTE 5
  (gWindows @0x02020004, 12-byte entries, paletteNum at +5; printer params per window in the table behind
  0x085CD660: window 7 is fg 12, bg 14, shadow 11). BG palette 5 is: 1 red, 2 dark red, 3 orange, 4 brown,
  5-10 all 0x0000 (spare), 11 light grey, 12/13 dark grey, 14 white, 15 light grey - NOT the battle message
  palette statcolor recoloured (that is BG palette 0), which is why its yellow/green indices render black
  here. Green (0x2726) and yellow (0x037F) are written into spare entries 5 and 6 on every redraw, into
  palette RAM 0x050000AA and both palette buffers (0x020377BE / 0x02037BBE).
- Double battles: the readout follows the target cursor. Second hook at 0x0805783C inside
  HandleInputChooseTarget (0x08057824) replacing "bl 0x08039C28 (draw target cursor) / movs r4,#0 /
  ldr r0,=gBattlersCount", all three replayed by the stub, which then redraws for gMultiUsePlayerCursor
  (0x03005D74). gBattlersCount 0x0202406C. HandleInputChooseMove is 0x08057BFC; the function at 0x08058138
  is the move-swap screen (it also redraws the type line, so the hook covers that too).
  NOT TESTED IN GAME: no double-battle save here; singles never run HandleInputChooseTarget.
- BUG + FIX (2026-09-19, found from a user report): with the target hook installed, the selected target's
  healthbox swung about +-90px instead of ticking by 1. Cause: the 4-byte trampoline "ldr r3,[pc,#0]; bx r3"
  clobbers r3, and at 0x0805783C r3 is the FOURTH ARGUMENT of the call being replaced -
  DoBounceEffect(target, BOUNCE_MON=1, height=15, speed=1) - so the bounce sprite got speed = low byte of the
  stub address (0xCD = -51) as its amplitude/offset (its callback does pos2.y = Sin(data0, data2) + data2).
  Fix: the stub rebuilds all four arguments before replaying the call. LESSON: a trampoline's scratch
  register must not be a live argument at the hook site - check what the replaced instruction consumes.
  Diagnosed with a write watchpoint on the healthbox sprite's pos2.y, which named the hack's bounce callback
  at 0x09D60A00, then by dumping the bounce sprite's data fields against an unpatched build.
- Double battles can be forced for testing without a save: set bit 0 of gBattleTypeFlags (0x02022FEC) every
  frame from the moment CB2 leaves the overworld (0x08085E5D) until setup finishes - the battle comes up with
  4 battlers. Target selection only appears for single-target moves (Rock Slide hits both and skips it).
  `test_target.lua`. Verified: the readout changes x2 -> x1 when the target cursor moves to the other foe.

## BOTH BIKES AT ONCE — 2026-09-19
- `patches/bothbikes/`: once you own either bike, the other is added to the Key Items pocket, so both are
  held and using/registering one switches straight to that bike. Nothing is given before you own a bike
  (so the Bike Voucher errand still plays out), and the check is a no-op once you own both.
- Why it just works: Mach Bike (259) and Acro Bike (272) share field-use routine 0x080FD298 and differ only
  by the item's secondaryId (Mach 0, Acro 1), exactly as in vanilla - holding both was always supported,
  the game simply never gives you both. Item table 0x00FC2C7C, 44-byte entries: name[14], id@14, price@16,
  holdEffect@18, desc@20, importance@24, pocket@26, type@27, fieldUse@28, secondaryId@40.
- Hook: the first four instructions of CB2_Overworld (0x08085E5C: push {r4,lr}; ldr r0,=gPaletteFade;
  ldrb r0,[r0,#7]; lsrs r0,r0,#7) become an absolute jump; the stub replays all four and returns to
  0x08085E64. GOTCHA repeat of the typeeff bug: the 4-byte trampoline's literal lands on the NEXT TWO
  instructions, so count 8 bytes replaced, not 4.
- Addresses: CheckBagHasItem 0x080D6724, AddBagItem 0x080D6928 (found via script command 0x44 in the script
  command table at 0x081DB67C, 228 entries), gBagPockets 0x02039DD8 (5 x {slots*, u8 capacity}; key items is
  index 4), gPlayerAvatar.flags 0x02037590.
- Tested: a save holding only the Mach Bike gains the Acro Bike on reaching the overworld; both appear in
  Key Items (new items append at the END of the pocket list). An unpatched build with the same save does not.
- POKEDEX GATE (2026-09-19): type badges and the effectiveness multiplier are only shown for species whose
  Pokedex entry is CAUGHT, via SpeciesToNationalPokedexNum (0x0806D4A4) + GetSetPokedexFlag (0x080C0664,
  case 1 = FLAG_GET_CAUGHT). "Seen" was asked for first but is useless here: the game marks the opponent
  seen during the battle intro. Proved it by clearing the seen bit at battle start and watching the game
  restore it before the action menu. Dex flag layout (from the hack's GetSetPokedexFlag at 0x09257950):
  seen array at gSaveBlock1 + 0x560, caught array at + 0x5D8, byte = dexNum >> 3, bit mask from the table at
  0x0832A328 indexed by (dexNum & 7) * 4. Tested: an uncaught Tentacool shows no badges and a bare "PP" line;
  setting its caught bit mid-battle brings back two badges and "x2".
- Free-space layout after the gate grew the badge code: typeicons 0x08FDA9BC-0x08FDB9E4, typeeff
  0x08FDB9E4-0x08FDBC2C, bothbikes 0x08FDBC2C-0x08FDBC8C. Each patcher asserts its region is all 0xFF, so a
  collision shows up as "target region not free" - shift the later FREE constants when an earlier patch grows.

## LEFTOVER CHINESE NPC NAMES — 2026-09-19
- `patches/npcnames/`: 104 names rewritten in place, data-driven (`npcnames_data.json` holds address, width,
  expected bytes and the new text; the patcher refuses to touch a site whose bytes differ).
- Why the text passes missed them: those passes follow pointers, and these names sit inside fixed-width
  struct fields nobody points at. Found by scanning struct tables directly for the hack's two-byte lead
  bytes (0x01-0x1E except 0x06/0x1B; second byte can be anything <= 0xF6, NOT only >= 0xA1).
- Tables: gTrainers relocated to 0x090019F8 (902 entries x 40, name +4, 12 bytes; Roxanne = id 265) - only 6
  Chinese names, 3 of them post-game (851 小智 Ash / Charizard, 852 小蓝 Blue / Blastoise, 853 佑树 = Yuki,
  Brendan's Japanese name, on Brendan's pic 126). Battle Frontier trainers at 0x085D5ACC (300 x 0x34) with
  the hack's struct {class u32, name[8], speech u16[18], monSet*} - 298 already English, slots 294/295
  fixed (Alivia, Paige). Battle Tents at 0x085DDA14 / 0x085DE610 / 0x085DF084 (30 each, same struct):
  all 90 were Chinese transliterations of the Japanese originals; their class sequence is exactly vanilla's
  tent order, so each slot got its official English name from pokeemerald's battle_tent.h.
  battle_tower's table selector is at 0x08165D78 (VarGet 0x40CF -> tent tables; gFacilityTrainers 0x0203BC88).
- Honorifics 0x083397A8.. (先生/少年/少女/专家/公子/小姐, pointer table 0x083397D0, used by code at
  0x0807FE80 as a fake link partner's name): Mr./Boy/Girl/Expert/Master/Miss. Expert and Master needed the two
  0x00 padding bytes before them, so their pointers moved back by 2.
- NOT names, left alone but live: 13 PokeNav landmark names (struct {name*, flag u16} table at 0x085B8F10,
  41 entries: Flower Shop, Petalburg Woods, Abandoned Ship, Desert, Cable Car, Glass Workshop, Meteor Falls,
  Safari Zone, Shoal Cave, Seafloor Cavern, Ocean Current, Desert Ruins, Ancient Tomb). Most fit their own
  bytes + the unused filler before them; Shoal Cave, Seafloor Cavern and Ocean Current would need free space.
  Dead copies (no pointer to them): old nature names at 0x0861CAAC, old gTrainers area at 0x08310030.
