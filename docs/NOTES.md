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
