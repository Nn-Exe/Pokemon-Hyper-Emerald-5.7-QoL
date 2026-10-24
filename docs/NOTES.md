# Hyper Emerald v5.7 — Project Checklist

## MOVEMENT SCRIPTS OVERWRITTEN BY OUR TEXT PASSES — FIXED 2026-09-14 (`patches/movefix/`)
- Symptom: new game -> Unown Ruins 34/12 (Arceus "want to watch it?") -> Temple of the End 35/35 -> Mountain Top 34/66
  (Rainbow Rocket lineup, script 0x09828797) crashes with mGBA "Jumped to invalid address 101C0CB4" at
  `applymovement 000f @08B14EB1` (0x09828AEC). The movement pointer had been redirected to relocated English text
  ("???: Wait…!"); the object-event code indexed its movement-action table with text bytes (0xAC...) and jumped to garbage.
- Root cause: `applymovement 0x000F, ptr` = `4F 0F 00 <ptr>` is byte-identical to `loadword 0, ptr` after a 4F. Our
  text passes (translation/) found dialogue by scanning for `0F 00 <ptr>`, so every applymovement on local object 15 became a "text
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
  prompt -> Yes -> "Jude used the Max Repel!" -> count 44->43, steps 250, countdown resumes. (Correction 2026-10-01:
  answering No does NOT show the sign - the No path `end`s inside the subroutine, skipping the parent's sign and
  `release`; see REPEL PROMPTS: NO RELEASES, YES APPLIES AT ONCE.)
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
Party menu option table sCursorOptions @0x08615C08 (33 x {text ptr, CursorCb ptr}; readers = literals @0x1B32F8 (DisplaySelectionWindow), 0x1B37C8/0x1B37F8 (input handler; dispatch is by table index, B = actions[numActions-1])). Copied to free space @0x08FD9B8C with entry 33 = {"Moves", cursor_moves}. Field action builder SetPartyMonFieldSelectionActions @0x081B3414 appends SUMMARY, field moves (0x13+j), SWITCH (if party[1] exists), ITEM/MAIL, CANCEL; eggs never reach it. Hook: the CANCEL append @0x081B3518 (16 bytes) -> trampoline to builder_hook @0x08FD9B00, which appends 33 only if numActions < 7 (actions[] holds 8: 4 field moves + 4 = full) then CANCEL, returns to 0x081B3529. Ids >= 0x13 draw in the field-move text colour (cosmetic). cursor_moves mirrors CursorCb_Summary @0x081B37FC: PlaySE(5); sPartyMenuInternal(0x0203CEC4)->exitCallback(+4) = cb2_moves; Task_ClosePartyMenu(0x081B12C1). cb2_moves: gSpecialVar_0x8004 (0x020375E0) = gPartyMenu(0x0203CEC8).slotId(+9); jump CB2_InitLearnMove 0x081606A1 (vanilla; TeachMoveRelearnerMove special 227 @0x08160639 = ScriptContext2_Enable + CreateTask(0x08160665) + fade, NOT used because the script lock would freeze the field). The relearner exits via CB2_ReturnToField. Move list builder @0x08161B94 is a hack trampoline (-> 0x09F06119), shared by script and screen, so expanded learnsets work (2026-10-21: wrong. The builder is GetMoveRelearnerMoves 0x0806E0B4 -> the hack's 0x09D6A93E: *Egg moves in the Move Relearner*.) Verified: give-up path and full learn (forget Rock Slide, learn Hammer Arm) in mGBA; test scripts in the folder. Pitfall found while testing: the START menu remembers its cursor, so scripted menu navigation must not assume "Pokedex" is selected after the first visit.

## Coloured stat names in battle text (2026-09-13) — `patches/statcolor/`
gStatNamesTable @0x085CBE00 (8 ptrs: HP, Attack, Defense, Speed, Sp. Atk, Sp. Def, Accuracy, Evasiveness; readers 0x6CF64, 0x14F7CC, hack 0x1D4A324). Entries 1-7 repointed to copies @0x08FD9CA0 wrapped in `FC 01 <idx>` ... `FC 01 01`. Battle text box = BG palette bank 0, loaded from LZ block @0x08C004E0 (64 bytes, banks 0-1) by battle_bg literals 0x35AE0/0x36430/0x38EF8 (others: 0x71900, 0x7B268, hack 0x1D626F0 left on the original). Bank 0 = 0000 7fff 001f 4d8a 5e2d 7fff 396d 6b3a 3d28 2909 434b 434b 434b 57ee 434b 3e69: text fg 1 (white), shadow 6 (396d), hack's green box uses 10-15; vanilla box shades 3/4/7/8 unused -> recoloured (orange 1A9F, pink 69FF, blue 7ECC, yellow 23BF) in a stored-literal LZ copy @0x08FD9D04, the three battle_bg literals repointed. Colour map: Attack 2 (red), Defense 3, Speed 13 (57ee), Sp. Atk 4, Sp. Def 7, Accuracy/Evasiveness 8. Verified in mGBA with Swords Dance ("Attack" red, rest white) and Tail Whip ("Defense" orange); box/menu pixels unchanged. Findings: the text printer honours FC 01 across the line break (restore code needed, 1 = default white); the hack's in-bag item-result window (palette bank 13/15, fg 2 grey) strips/ignores colour codes, so X-item messages stay plain. Test trick: write move ids into gBattleMons[0].moves (0x02024084+0x0C, pp +0x24) after the intro to get deterministic stat messages; the battle intro needs a button press ("Wild X appeared!" waits) before the action menu.

## Corrupted graphics from pointer repointing (2026-09-15) - `patches/gfxfix/`
Symptom: Rustboro City (map 0/3) and many other maps drew garbled tiles. Cause: our text passes (translation/) rewrite EVERY 4-byte
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
    zeroed). GetCurrentMapWildMonHeaderId 0x080B4CF8 already points there. Extra 7-entry table @0x08553894
    (see tools/romdata/scan_wild.py) - the Battle Pyramid's, not cities (2026-09-30).
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
  the extra table's Land rows next to the main table's Water/Fish). WRONG, fixed 2026-09-30: 0x08553894 is the
  Battle Pyramid's table - see *DEXNAV LISTS THE GAME'S OWN TABLE*. Species names via the header pointer
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
- 2026-09-20, GATE REMOVED (v1.3.1): the caught-only rule hid badges/multiplier on trainers' Pokemon the player
  had only seen, which read as "sometimes missing". Reproduced with forced trainer battles (set gBattleTypeFlags
  bit 3 and gTrainerBattleOpponent_A 0x02038BCA every frame while CB2 != overworld; Grunt 7 / Floatzel and Aaron
  397 / Gabite): 0 badges until the caught bit was set, then 1 and 2 badges. Per the user, badges now show for
  every opponent. The dex helpers stay documented above in case a gate comes back. Trainer battles otherwise
  behave like wild ones: opponent healthbox body in palette 4 (once seen in 15 after a shinybox repaint, which the
  >= 10 rule accepts). Probe: _testrun/trtest.lua (TRAINER_ID env var).

## NEWS TRACKER FREEZE — 2026-09-20
- Symptom: using the News Tracker key item drew the first line of the roaming Latios/Latias message and then
  the game sat there, music still playing. Reported by the user; reproduced in the harness.
- Cause: one stray byte at the end of the message string (0x09F0AB84). It ends `FC 09 09 FF`, but
  EXT_CTRL_CODE_PAUSE_UNTIL_PRESS (FC 09) takes NO argument, so the 0x09 is read as text - and 0x09 is a lead
  byte of the hack's two-byte Chinese encoding, so the engine ate `09 FF` as one character and swallowed the
  terminator. The string never ended, the message box never reported itself done, and the task polling it
  (0x08121F3C, reading the box state at 0x0203A140) spun forever. Audio is interrupt-driven, hence "frozen but
  still humming". Fix: that byte -> 0xFF, leaving `FC 09 FF`, exactly how the item's own "No news received"
  string (0x09F0ABBC) already ends. The whole block is byte-identical to the original Chinese ROM, so this is
  the hack's bug, not the translation's, and a ROM-wide scan found this is the ONLY string with the shape
  `FC 09 <lead byte> FF`.
- Also translated the two region names the same routine picks between, in place: 0x09F0AB74 Hoenn and
  0x09F0AB7C Sinnoh (was showing "in {Chinese} on Route 132"). Nothing points at them directly or at the
  padding around them - the routine reaches them as base 0x09F0AB48 + 0x2C / + 0x34.
- Item plumbing, for reference: News Tracker is item 695, Key Items, fieldUse 0x08C60538, which is a
  `ldr r1,[pc,#0]; bx r1` trampoline to the real routine at 0x09F063F0. That routine reads the roamer struct
  at gSaveBlock1 + 0x31DC (active flag +0x13, species +8) and the roamer's map from 0x0203BC86/87, builds
  gStringVar1 = species, gStringVar2 = region, gStringVar3 = GetMapName(mapsec) via 0x0812456C, expands into
  gStringVar4 and displays it. Debug probe: patches/newsfix/test_newsfix.lua (drops the item into the first
  Key Items slot, uses it, then logs callbacks, live tasks and the string buffers each step).

## SINNOH MAP SCREEN — 2026-09-20
- `patches/sinnohmap/`: a screen of our own. Sinnoh is drawn on BG1 from LZ77 data in free space, a marker
  blinks on the area you are standing in, its name goes in a box, B returns to the field. Nothing the Hoenn
  region map or Fly touch is modified: gRegionMapEntries, the region map graphics and its code are untouched.
- Artwork: `tools/make_region_map.py` turns a picture into GBA background data (fit to 240x160 by dropping the
  flattest rows rather than cropping or resampling, quantize, pack 16-colour palettes, dedup tiles with flips,
  LZ77). Source `sinnoh-map/`, 24 colours -> 10 palettes, 408 tiles, ~7.6 KB compressed. Also does 8bpp
  (`--bpp 8 --base 112`) which the game's own region map uses.
- The hack's Hoenn map is an AFFINE background (that is how it zooms): 8bpp, one byte per map entry and a hard
  cap of 256 tiles, character base 0x06008000, screen base 0x06003000, palette 48 colours at index 112. Ours
  needs 409 tiles, which is why it could not borrow that screen and has its own (a normal text background has
  no such cap).
- Locations: `locations.json`, 46 mapsecs fitted from the stitched world render (tools/render_world.py,
  tools/compose_sinnoh.py) onto the map grid by least squares on 15 city/town anchors read off the picture -
  mean error 0.53 tiles. Plus 15 indoor areas placed by hand next to where they belong.
- Entry is the Town Map key item (361), which the hack has but never gave out or made do anything. Its
  field-use pointer goes to our routine and the overworld hook hands you the item once. The start menu was the
  first attempt and CANNOT take another entry: sCurrentStartMenuActions is exactly 9 bytes at 0x02037610 and
  AppendToList (0x080A0944) has no bounds check, so a tenth entry overwrites 0x02037619, which 7 places use.
  The menu built but hung.
- GOTCHA, cost an hour: chaining onto the overworld hook soft-reset the game. That hook is at a function's
  FIRST instruction, so lr still holds the live return address and the prologue that saves it has not run. Our
  bl calls destroyed it and CB2_Overworld later returned into nowhere. Keep lr in r4 across the stub and put it
  back before chaining. The DexNav menu hooks never had this problem because they sit at a function's tail,
  where the return address is already on the stack.
- Item-use context: gTasks[taskId].data[3] is 1 when used from the field and 0 from the bag (the Pokeblock
  Case, 0x080FDB6C, is the model). Bag path: gBagMenu (0x0203CE54) -> newScreenCallback, then
  Task_FadeAndCloseBagMenu 0x081AB8F8. Field path: gFieldCallback 0x03005DAC = 0x080AF6D5, FadeScreen
  0x080ABCD0, then a task that waits for the fade, calls CleanupOverworldWindowsAndTilemaps and sets our CB2.
  Messages: on the field 0x081978EC, over the bag 0x081ABB4C. Exit via 0x080860C8.
- Two name boxes, top and bottom; the screen shows whichever is not on top of the marker. The scroll registers
  are zeroed on entry because whatever screen you came from leaves its own.
- 2026-09-20 follow-up: item 361 is renamed "Town Map" -> "Sinnoh Map" inside its own 14-byte name field
  (10 characters + terminator of 14, remainder zeroed), so nothing is repointed and no other item moves.
  The off-map message now goes through StringExpandPlaceholders into gStringVar4 (0x08008EE0) before being
  handed to the message routine, which is what the game's own key items do - the Coin Case (0x080FDC34) is
  the model. Passing a ROM pointer straight to 0x081ABB4C printed the text but it closed itself after a
  moment; via gStringVar4 it waits for A or B like every other message. Verified by holding all input for
  280 frames: the message task stayed put, and only A returned to the bag.
- 2026-09-20, TWO GRAPHICS BUGS the user spotted as "blue speckles all over the roads and cities", both in
  tools/make_region_map.py and both invisible in the converter's own round-trip check:
  (1) Colour 0 is TRANSPARENT on a GBA background. The palette packer was using all 16 entries, so every
      pixel that landed on index 0 showed the backdrop through it. Colours now live at 1..15 (COLORS_PER_PAL),
      index 0 is left alone and the palettes' entry 0 is set to the picture's commonest colour. Cost: one
      extra palette (10 -> 11), still well inside the 16 the hardware has.
  (2) The LZ77 compressor emitted back-references of distance 1 for runs of one repeated byte. The BIOS
      LZ77UnCompVram can only write video memory a halfword at a time, so the byte it just produced is still
      in its buffer and reads back as ZERO - flat areas come out riddled with holes. Minimum distance is now
      2 (MIN_DISP). Costs 12 bytes of compression. Unpacking to normal memory has no such problem, which is
      why nothing caught it before hardware.
  Verified properly this time: dumped 0x06004000 from the running game and compared byte for byte with the
  source file (0 differences; the tilemap differs by exactly 2 bytes, which is the blinking marker), and the
  screen now matches the expected render to 99.8% of pixels.
- 2026-09-20: the marker moves. The D-pad HOPS it to the nearest place in that direction rather than
  sliding a tile at a time, because we hold one point per area, not the per-tile section map the Hoenn map
  uses - free movement would spend most of its time over squares with no name. `snap()` scores every entry
  in the table by distance along the press plus how far off the line it sits, and takes the smallest; the
  name box is redrawn from the entry under the marker, and SE_SELECT plays on each hop. A third literal
  pool was needed (pools A, C and the main one) as the code grew past a Thumb load's 1020-byte reach.
- 2026-09-20: fly from the map, the low-risk way. We never warp on our own. Each Sinnoh town has a courier
  NPC whose destination script is shared (0x0987CD9D: a multichoice grid, then compare/goto_if per town) and
  each town's block begins `checkflag <visited>` (0x4194-0x419B and 0x42E3-0x42EA, the hack's custom-region
  flags, which its GetFlagAddr 0x09F00CEC keeps in SaveBlock1 +0x988 / +0x3B24) then warps into map group 36.
  `COURIER` in sinnohmap_patch.py holds {mapsec, flag, block} for the 16 towns and asserts each block still
  starts with that checkflag and warps into group 36, so a re-run against a changed ROM fails loudly.
  Pressing A: fly_target() looks the marked mapsec up in COURIER and calls FlagGet (0x0809D790) on its flag;
  0 means the press is ignored. Otherwise the screen fades out with state=2, tk_leave sets gFieldCallback to
  fly_cb, and once the field is back a task waits for the fade and hands the courier's block to
  ScriptContext1_SetupScript (0x08098EF8), which locks the player and runs it exactly as if the courier had.
  draw_name prints towns whose flag is clear in grey (lit_colors_dim) so you can see where A will work.
  Verified from the Hearthome save (test_fly.lua): Hearthome -> Route 208 -> 207 -> Oreburgh, A, landed at
  map 36/3 (49,15), the Oreburgh Pokemon Center. Refusal (test_fly_refused.lua): Solaceon is unvisited on
  that save, its name printed grey, A left the map open (CB2 stayed ours), B closed it, player still in
  Hearthome. Mt. Coronet (127) and the Sinnoh League (97) are in the table too, as the couriers offer them.

## DEXNAV SEARCH AND CHAIN — 2026-09-21
- `patches/dexnavchain/`: the DexNav screen gains a cursor; A starts tracking that species; the next wild
  Pokemon of that map is it; catching or beating it raises a chain that improves the next one. Three pointer
  words change in the ROM and nothing else: the word the hack's CreateWildMon trampoline jumps through
  (0x080B4E6C), the overworld hook the earlier patches installed (chained through ours), and the DexNav
  task pointer inside our own dexnav blob. Everything else is new code in free space at 0x08FDE4A0.
- The hack's CreateWildMon (0x09F05F18, behind the trampoline at 0x080B4E68) already has the machinery a
  chain wants: it calls CheckBagHasItem for a Shiny Charm (item 119) and passes a REROLL COUNT - 5 with the
  charm, 1 without - to a generator at 0x09F0071C that keeps making personalities until one is shiny or the
  rolls run out. Our stub does not reimplement any of it: it substitutes species and level, then calls that
  same routine again (up to 1 + chain/4, capped at 12 attempts) until IsShinyOtIdPersonality (0x0806EBD1)
  says yes. Everything else is written into the mon afterwards.
- Mon data in this hack is UNENCRYPTED and UNSHUFFLED, which the probe in `patches/dexnavchain/` confirmed
  (checksum 0, substructs in the plain order): species +0x20, moves +0x2C, PP +0x34, the IV word +0x48
  (5 bits per stat, bit 30 isEgg, bit 31 the second ability), level +0x54. So the stars, the ability slot
  and the egg move are written straight in, then CalculateMonStats (0x08068D0D) makes the stats match.
- Stars: rolled when the next target is chosen, so the bar is honest about what you will meet. Three stars
  means at least four 31s, two means three, one means two, none means whatever the game rolled. The chance
  of three is 1 + chain/2 per cent (capped at 15), of two three times that, of one six times that.
- Egg moves come from the table at 0x09D78128 (vanilla format, species + 20000 markers, terminator at
  0x09D7973C); the move's PP comes from gBattleMoves at 0x09D86419 (12-byte stride, PP at +4). No hidden
  ability is granted. (Written believing the hack had none, from the two ability bytes in the base stats.
  It does: the game reads abilities from three u16 per species at 0x097A0000, two regular and one hidden,
  through the hook at 0x0806B694 -> 0x09D73A80. See tools/build_pokedex.py.)
- gBattleOutcome is 0x0202433A, confirmed by watching it: 1 won, 4 ran, 6 the wild one fled, 7 caught, and
  0 while a battle is being set up.
- THREE BUGS WORTH REMEMBERING, all found by testing rather than reading:
  (1) The chain counted a battle twice. Our stub marks an encounter as ours, but the overworld callback goes
      on running during the battle's transition, so it read the PREVIOUS battle's outcome - still standing in
      gBattleOutcome - and scored it against the new encounter. The stub now zeroes that byte when it seeds
      an encounter, and the tick ignores an outcome of 0.
  (2) A Pokenav call or a rematch trainer battle counted toward the chain. Scoring now also checks that the
      Pokemon still in the enemy party is the species being hunted: anything else neither counts nor breaks.
  (3) THE BAR ATE THE MAP. On the field BG0's tiles start at VRAM 0x06008000 but the map's own tilemaps sit
      at 0x0600E000, which is tile index 0x300 - a window with a baseBlock at or above that writes over the
      map itself, and the whole screen turns to garbage a moment later. The field's own windows sit at
      0x107 (location popup) and 0x194 (message box), with the standard frame at 0x214, so the bar took
      0x240..0x2B0. `test_scratch_ram.lua` and the window dump in the notes below are how this was found.
- The bar is a plain window (28x4 at 1,1, palette 15) filled with palette entry 10, which the text palette
  leaves as one of three identical spare whites; black_slot() writes black into it on every draw, because a
  new map reloads the palettes. Text is white on it, the icon is a real mon icon sprite (LoadMonIconPalette
  0x080D2F29, CreateMonIcon 0x080D2CC5, priority forced to 0 so it draws over the bar, taken down with
  DestroySprite 0x080070E9 and FreeMonIconPalette 0x080D2F69). The star tiles are ours, 8x8, blitted into
  the window's own buffer - the font has no star glyph, only arrows at 0x79-0x7C.
- The bar comes down whenever LockPlayerFieldControls' byte at 0x03000F2C is set - a menu, a message, a
  script, a Pokenav call - and goes back up when the player is free again, so it never fights anything else
  for the screen or holds its window and memory while another screen wants them.
- State lives in 32 bytes at 0x0203A660 with 96 more for text, chosen by filling candidate regions with a
  pattern and playing through battles, menus, the bag, a save and a Pokenav call to see what survived
  (`test_scratch_ram.lua`). 0x0203B700 looked ideal and turned out to be a save staging buffer. Nothing is
  written to the save: the chain is RAM only and starts again after a reload, which is also why the region
  chosen sits well clear of the save blocks and the PC boxes.
- The hunt is per map but leaving only parks it: walk into a Pokemon Centre and back and the chain is still
  there. Encounters are only substituted on the map the hunt was started on.
- Tests, all in the patch folder: `test_chain.lua` (chain arithmetic and what actually appears),
  `test_chain_break.lua` (running away ends it), `test_stars.lua` (forces the rating and counts 31s),
  `test_pokenav_call.lua` (a call with the bar up), `test_park.lua`, `test_screen.lua` (cursor, paging,
  clamping, the bar at chain 200 with the rerolls at full stretch) and `test_scratch_ram.lua`.

## DEXNAV: UNBOUND RULES, SEARCH LEVEL IN FLASH, CATCH FIX (2026-09-21)
Full write-up in docs/DEXNAV-PROGRESS.md; addresses here.
- Catch bug: on a catch the enemy party is zeroed before CB2_Overworld returns (seen: species 0 at +0x20
  with gBattleOutcome 7). Scoring now uses gBattleResults (0x03005D10): +0x20 lastOpponentSpecies
  (0x03005D30), +0x28 caughtMonSpecies, +0x2A caught nickname. Offsets differ by 2 from what pokeemerald's
  struct suggests; they were read off a live catch.
- Save: the hack's save sectors all carry checksum 0x0001 (checks disabled) and data up to 0xFEE, so no
  slack in the main save. Sector 30 (Trainer Hill e-Reader) was blank on a late-game save.
  TryReadSpecialSaveSector 0x081535DC, TryWriteSpecialSaveSector 0x08153634 (sectors 30/31 only),
  ReadFlash 0x082E1AD4, ProgramFlashSectorAndVerify 0x082E1CD0, gSaveDataBuffer 0x0203ABBC (4 KB).
  Trainer Hill read 0x081D3AD8 -> validator 0x081D396C (count byte must be 1..8); its writer 0x081D3AB0 is
  called only from 0x081D53C8 (e-Reader).
- Base stats held items: +12 common, +14 rare (Chansey 222 Lucky Punch / 197 Lucky Egg). Boxed mon held
  item is +0x22. The game's own wild held-item roll still runs after ours.
- State block additions: +24 u8 search level, +26 u16 rolled held item. Bar window top row 15 (was 1),
  icon y 136 (was 24); tiles unchanged at 0x240.
- Test runs on this Mac: mGBA dev build with -C mute=1 -C fpsTarget=2000 -C audioSync=0 -C videoSync=0.
- Bar frame: the menus' standard frame via its window function WindowFunc_DrawStdFrame 0x08197F19 through
  CallWindowFunction 0x08004059. In this hack the Draw*Frame wrappers (DrawDialogueFrame 0x08197B1C,
  DrawStdWindowFrame 0x08197E80) take (windowId, copy, tile, palette) and store tile/palette at 0x0203CD9C
  (u16) / 0x0203CD9E (u8) before calling the window function; calling it without them drew tile 1, palette 0.
  Std frame = tile 0x214, palette 14 (white/grey). The dialogue frame (0x200, palette 15) is the hack's
  translucent blue message box and turns teal under the field palette. Removal: ClearStdWindowAndFrame.
- ORAS rules: chain_break() (chain 0, tracking off, bar down, lastfoe zeroed) on run/lose/flee, map change
  (was: parked), and any battle not seeded by us (lastfoe non-zero on the field with flags bit1 clear).
  Search level is u16 at state +24 and in the flash entries, capped at 999.
- Shaking patch (see DEXNAV-PROGRESS "The shaking patch"): step hook word 0x0809CBEC (was 0x09F06531, the hack's
  CheckStandardWildEncounter, which does its own bookkeeping and jumps back to vanilla 0x0809CBF4).
  sWildEncounterImmunitySteps 0x020375D4, sPrevMetatileBehavior 0x020375D6. gPlayerAvatar 0x02037590
  (+5 objectEventId), gObjectEvents 0x02037350 (0x24 each: +8 localId, +9 mapNum, +10 mapGroup, +11 elevation,
  +0x10/+0x12 currentCoords). FieldEffectStart 0x080B5B18, active list 0x03000F58 (32 ids),
  gFieldEffectArguments 0x02038C08, MapGridGetMetatileBehaviorAt 0x080882BC, IsTallGrass 0x08089448,
  IsLongGrass 0x0808945C, IsSandOrDeepSand 0x08088E80, IsLandWildEncounter 0x0808952C, IsWaterWildEncounter
  0x08089558. pret's pokeemerald.sym (symbols branch) matches this ROM below ~0x0819xxxx; the menu code from
  about 0x08197000 on is shifted (+0xC04 at ClearStdWindowAndFrame), so verify before trusting a symbol there.
  Effects 19-22 (shaking grass, long grass, sand hole, water surfacing) exist but loop forever and 21/22 draw
  a blue box in this hack: not usable.

## R OPENS THE DEXNAV, AUTO RUN IN THE OPTION MENU (2026-09-21)
patches/rbutton/. The field-input chain is ProcessPlayerFieldInput's trampoline (0x0809C014, word 0x0809C018)
-> L quick repel's stub (0x08FD9A41) -> its "next hook" literal (0x08FD9AC8, was auto-run's R toggle 0x08FD9963)
-> r_hook, which re-executes the replaced prologue and resumes at 0x0809C01D like the toggle did. R (newKeys
0x100) with tileTransitionState != 1 and FLAG_SYS_POKEDEX_GET opens the DexNav: bit 7 of the hunt's flags,
FreezeObjectEvents, BeginNormalPaletteFade to black, and a task that calls the DexNav's own start-menu
callback (dexnav blob funcs[0]) until it switches CB2; returning TRUE makes the caller lock the controls.
Auto Run: optionsButtonMode (SaveBlock2+0x13) holds 0 off / 4 on. All 22 readers in the ROM were checked: they
compare with 1 (LR, GetLRKeysPressed and friends) or 2 (L=A, ReadKeys), or copy the byte into a link/record
struct (0x0801EF3A.., 0x080ECFA0); 0x0819C860 is a false hit (Battle Factory swap struct). Auto-run's run
decision now reads it (ldr r1,[r1,#4]; ldrb r1,[r1,#0x13]; lsrs r1,#2 at 0x08FD996C - gSaveBlock2Ptr is
gSaveBlock1Ptr+4). ButtonMode_ProcessInput 0x080BAFCC and ButtonMode_DrawChoices 0x080BB028 (callers: the option
menu only) are trampolines to a two-state version that uses the game's On/Off strings (0x085EE5F4/FD) and
DrawOptionMenuChoice 0x080BAB68 at y 64; sArrowPressed 0x02039B48. Label rewritten in place at 0x085EE5C8.
The old auto-run byte at SaveBlock1+0x31 is no longer read.
Unregister (dexnavchain): A on the tracked species runs chain_break and leaves like a registration.

## GOLD HEALTHBOX ON YOUR SIDE TOO — 2026-09-21
- `patches/shinybox/`: the per-frame pass already handled every healthbox and computed each battler's shininess;
  one test skipped the player's side (`movs r0,#1; tst r0,r6; beq sb_next`, even battler = player). The `beq` is
  now a no-op, so a shiny battler 0 or 2 gets the gold box as well. Same size on purpose: typeicons writes a `bl`
  into this blob at `0x08FDA0BA`, so nothing after it may move. In the current ROM that is two bytes,
  `0x08FDA136`: `14 D0` -> `C0 46`.
- Only palette index 2, the box fill, is gold, and the player's box keeps its HP numbers, HP bar and EXP bar in
  other indices: checked on screen in singles (Swampert, 322/322) and doubles (the second battler's small box).
  `test_shiny_yours.lua` and `test_shiny_yours_double.lua` force shininess through `gBattleMons[n].otId =
  personality`, which is what the pass reads, so no party data is touched.
- GOTCHA, caught by the assembled-bytes check before it shipped: keystone assembles `nop` as `00 BF`, the
  Thumb-2 hint. The GBA's ARM7TDMI is Thumb-1 only, where that encoding is undefined - the first battle frame
  would have hit it. The Thumb-1 no-op is `mov r8, r8` (`C0 46`), which is what the 10-byte trampolines here
  already use. The patchers' Thumb-2 check only rejects 4-byte instructions, so it cannot see this one.

## JOURNAL KEY ITEM — 2026-09-21
- `patches/journal/`: the Fame Checker (item 363, a FireRed leftover: no script gives, checks or removes it, no
  mart sells it, no patch uses it) becomes the **Journal**. Use it from the Bag, or register it and pick it in the
  SELECT popup, and it prints `<part> - Next objective:` and the step. Groups add a page: `<label> k/N` and the
  missing members, all of them (badges, Tapus, clan leaders) or only the first one missing (Plates, in Waji's
  hint order, each with its hiding place).
- ROM: code + data at `0x08FE5400..0x08FE83D4` (inside the unreferenced run from 0x08FE5284); the overworld hook
  word `0x08085E60` -> our stub, which gives the item once and chains to what was there (`0x08FDE4A1`, the
  dexnavchain stub); item 363's name, description pointer and field-use pointer (`0x08FC6AE0..0x08FC6AFF`). No RAM
  of its own: the message is built straight into gStringVar4 and shown with the game's key-item message routines
  (Bag `0x081ABB4C` + `0x081ABBBC`, field `0x081978EC` + `0x080FD1F8`), exactly the Sinnoh Map's no-map path.
- Selection rule (`build`): find the last ANCHOR step that is done, then show the first step after it that is not.
  Anchors are steps that can only happen in order; anything that can be done early or skipped is not one, so an
  early flag never makes the Journal jump ahead, and a skipped optional step behind a later anchor is never asked
  for. A step is ANY(flags), ALL(flags) or a GROUP (done when every member is set, or when one of its "done_any"
  flags is - a later event that proves it).
- The table is `steps.py`: 74 steps (Hoenn 24, post-game 37, Sinnoh 3, Lost Artifacts 10) plus the closing
  message. Each flag was found with `tools/romdata/scripts.py` + `prereq.py` (who sets it, under which branch
  conditions) and checked against every save on hand. Flags that looked right and were not:
  * `0x40C3` (Interpol at Littleroot) is set from the start of the game - it is the Interpol agent's hide flag -
    and the Hall of Fame clears it. On its own it reads as done before you have a Pokémon: the step is
    ALL(0x864, 0x40C3).
  * `0x08E0` (Champion Island, Waji's ticket) is also set by beating Lyra (Route 102 / Bell Tower script
    `0x09800FBC`). Not an anchor.
  * `0x4081` is Giratina's object flag, set when you battle it. The Hoenn post-game Distortion World mission
    (0x42BC) leaves Giratina standing there, so many players have it long before Sinnoh (one of the test saves
    does). Not an anchor; the rift and Celestic steps count as done once it is set, because they only exist to
    lead you to Giratina.
  * `0x42D8` (the Spear Pillar's new passage) is also set by picking Dialga or Palkia at the Unown Ruins in Hoenn.
  * `0x75` (Space Center) is cleared again by C code; the step uses `0xCD` (Steven at the Space Center).
  * `0x42B6` (Team Plasma in Shoal Cave, which unblocks Mossdeep's Gym) can happen before Mt. Pyre. Not an anchor.
- Lost Artifacts, as the scripts have it (the old guide page had several of these wrong, see below):
  Waji at the Spear Pillar (`0x410D`, `0x098723FC`) lists every missing Plate in a fixed order; each Plate is an
  item ball whose hide flag is the Plate flag (Iron and Dread share `0x4109`). With all 16 flags the altar
  (trigger 10,12, `0x098C2488`) warps to the Space-Time Rift: a native at `0x08FE3F48` builds a double wild
  battle against Dialga and Palkia (Lv 50), then Brendan or May from another world (trainers 926/927) -> `0x40F0`.
  Waji then sends you to Celestic Town; its ruins trigger (`0x0988F23D`) sets `0x40B1` and, only if the Pokedex
  has both Dialga and Palkia as caught (GetSetPokedexFlag via native `0x08FF0610`, national 483/484), `0x42D8`,
  which unseals the Distortion World doors at the Spear Pillar (10,9) and Sendoff Spring (21,14) (their map
  scripts setmetatile them shut while it is clear). Giratina (`0x4081`) is inside. Arceus is NOT on Mt. Coronet:
  the trigger is on the Mountain Top above Team Rainbow Rocket's castle (34/94, 11..13,11, `0x0987EEA0`) and needs
  `0x4081`, all 16 Plate flags and all 17 Plate items in the Bag; stairs appear to the Hall (36/96), Arceus Lv 80
  joins whether you catch it or win (`givemon` on a win) -> `0x42FB`, then "Go to Jiayuan City" = Hearthome
  City (家缘市). Cogita there (37/73, west side) needs 0x42FB, 0x4081 and the Plates -> `0x4313` and the rift to
  Hisui: Rei's battle at Prelude Beach (`0x4316`), Cogita on Firespit Island (`0x4318`), Adaman and Irida at the
  Snowview Hot Spring (`0x431A`, `0x431B`), Volo in the Primeval Cave (`0x4315`, trainers 1303 then 1339; the
  Blank Plate and Arceus's blessing).
- Two traps the Journal's Giratina steps route around. (1) The Celestic ruins' trigger is the first tile inside
  the door (8,18; door at 8,19), and it removes the Dialga and Palkia placed there and sets `0x40B1`, which also
  hides the pair in the Unown Ruins - so after any visit to those ruins (Cynthia's tablet during the Sinnoh story
  is one) the Dialga-or-Palkia choice is gone for good, and `0x42D8` then needs both in the Pokedex. (2) The
  Distortion World has an ungated door: Route 129's islet (warp at 64,6 -> 34/13 -> 37/96); a collision-only path
  search from it reaches the tiles next to Giratina (37/96, 24,11). Both Giratina steps mention Route 129.
- The hidden ruins (34/45, doors on Route 210, in the Solaceon Ruins and on Route 111) have a tablet wall
  (`0x098100D7`) that checks all 17 Plate items and opens the Unown Ruins: the God-King Cyrus side story
  (trainer 894), which sets `0x42D8` too when you win the Dialga/Palkia choice, then sends you to Twinleaf Town.
- Tests: `make_tests.py` writes 84 scenarios - one "cut" per step (every earlier step done, every later one
  undone; the answer must be that step) plus the out-of-order cases above - and the exact bytes a Python model
  of `build` predicts. `test_journal.lua` writes each scenario's flags into the save blocks in RAM, uses the
  Journal from the SELECT popup and logs gStringVar4; `check_journal.py` compares: 84 of 84 byte for byte.
  `test_journal_pages.lua` screenshots every page of five messages (the widest 34-character lines fit with room
  to spare); `test_journal_bag.lua` uses it from the Bag (name, description, icon, message over the Bag, closes
  back to the Bag). On a save that never had it, the item was in Key Items as soon as the field came up.
- The message ends `FC 09 FF` (wait for a button, then end), not a bare `FF`: the key-item message routines
  close the box as soon as the printer finishes, so the last page vanished unread (2026-09-22). `make_tests.py`
  appends the same two bytes to every expected message.
- After Volo (2026-09-22): 0x431E base-camp report; 0x4319 Cogita on Firespit Island (needs Tornadus/Thundurus/
  Landorus, species 899-901); 0x4322 the Dried Fish item ball, Prelude Beach 37/104 (13,40), item 744 - Kitty in
  the developer house (35/8) trades it for the nameless stone, item 745; the summit guard 37/106 (0x098B201D)
  needs item 745 + 0x4319 + !0x4323 and warps to the Moonbow Dome 35/10: the God of Forms (trainers 1304, 1340,
  1341) then, after the last battle (the god: "take me with you"), a wild battle with species 1025 Lv 70 - the god itself - -> 0x4323. (Cogita summons the other Enamorus, Lv 50, on Firespit Island: 0x4319.) Species 1025 was named in Chinese (爱娜莫洛斯) until speciesnames; 0x4325 Cogita on
  Champion Island. The Champion Island ticket step uses 0x005C (set only by Scott's Silver Symbol branch,
  0x098737CF): the ferry needs 0x08D5 AND item 371, and Yanshan (0x098C49E5) sets 0x08D5 without the item.
- Solaceon nightmare: 0x4117 husband's story (set on first talk; 37/22, 0x0980DF8C), 0x412F Dawn on Route 210 gives
  the Lunar Wing (item 647; 35/16, 0x0980977C), 0x412D the woman wakes (0x0980E243), 0x4060 Darkrai's hide flag in
  the Lost Tower (35/29): the map script only moves the blocking object while 0x412D is clear; Darkrai's script
  (0x08FE3B51 -> 0x09891F30) needs 0x412D, and the shared legendary handler 0x08FE38F0 (fade, removeobject, fade)
  sets 0x4060; fleeing clears it (0x09823D1C).
- Space: the Journal ends at 0x08FE8AE8 with 84 steps (~1.3 KB left before berrynum at 0x08FE9000; move berrynum
  again, not the Journal, if it grows past that).
- GOTCHA: in this build SELECT always opens the keyreg popup (PC anywhere made it unconditional), even with one
  registered item. Tests must press SELECT, then UP for the first slot.

## BERRY NUMBERS IN THE BAG — 2026-09-22
- Reported with a crash screenshot: the hack's newer berries show as "No?2" in the Berries pocket. The number
  is item id - 132 in two digits (right for Cheri 133 ... Enigma 175 = No01-43); the hack's berries are items
  704-727 and 762-765, i.e. 572-633, and ConvertIntToDecimalStringN prints "?" for a digit above 9. The
  original Chinese ROM has the same bug.
- `patches/berrynum/`: Occa No44 ... Maranga No67, then 762-765 No68-71. Four places compute the number and all
  are hooked (trampolines to one stub at `0x08FE9000`, 116 bytes; `0x08FE8400` until 2026-09-22, when the Journal outgrew the gap):
  * `0x08FD5E32` and `0x08FD7D4E`: the hack's own item-name routine, in TWO identical copies (0x08FD5E20 and
    0x08FD7D3C; the original ROM has both). The Bag's list rows come from the second one. Patching only the
    vanilla sites or only the first copy changed nothing on screen - check every copy.
  * `0x081C5422` (vanilla list routine) and `0x081AB420` (the Bag's vanilla item-name routine, berry case).
  The hack-routine sites sit at 2 mod 4, so they use the 10-byte trampoline, which clobbers the `movs r3,#2` /
  `ldr r6,=...` they cover; the stub replays them and jumps home through r12.
- GOTCHA: keystone pads `.align` with `00 BF` (a Thumb-2 nop) when the code before a literal pool is 2 mod 4.
  The patcher tries again with a hand `mov r8, r8` when that happens.
- The crash in the same report did not reproduce: that exact pocket (Pecha x2, Leppa, Oran x3, Mago, Occa, Jaboca,
  Rowap, Kee), as a girl, cursor from Occa onto Jaboca, on every archived build from 2026-09-13 to now, and every
  berry in the game walked over one by one. "Jumped to invalid address: E3A02004" is the BIOS open-bus value
  after an SWI, i.e. a function pointer read from address ~0: session state, not the berry. Heap in the Bag had
  86 KB free. `test_berrynum_report.lua` rebuilds the reported pocket and dumps registers/stack on a crash.

## QUEST LOG — 2026-09-22
- Asked for a "mission log with ticks" like newer ROM hacks. Using the Journal (item 363) now opens a screen of
  its own instead of the one-line message: one chapter a page (Hoenn 24, Post-game 38, Sinnoh 3, Lost Artifacts
  19 + the closing row), a tick for done, a red arrow for the current objective, a diamond for "any order"
  steps, "???" (dimmed box or diamond) for what is ahead. A on a revealed row shows the objective's full text;
  L/R or Left/Right turn the chapter; B fades back to the field. The header counts done/total per chapter.
- `patches/questlog/`, blob at `0x08FEA000`-`0x08FEB418` (code 2312 bytes, then data), in the unreferenced
  0xFF run `0x08FE9074`-`0x08FF0000` (the pointer-looking words into that run are all inside graphics/audio).
  The only other change is item 363's field-use pointer (`0x08FC6AFC`): the Journal's `item_use` stays, unused.
- One rule, not two: the patch imports `journal_patch.layout()` (split out of `build()` for this), rebuilds the
  Journal blob, reads the one word a rebuild cannot know (its overworld chain target) back from the ROM, and
  asserts the ROM's Journal is byte for byte that blob. Then it calls the Journal's own `step_done`,
  `group_tail`, `append` and `u8dec`, and walks its step table. `compute` is the Journal's `build` rule turned
  into a status per step: 1 done (flags, or an anchor before the last done anchor), 2 current (first not-done
  from there, or the closing row when all are done), 3 an "any order" step left behind, 4/5 ahead.
- Titles: `steps.py` has `TITLES` (one per step, <= 24 chars, the same no-spoiler rule) and `FINAL_TITLE`.
  The patcher asserts the lengths line up.
- Screen: the Sinnoh Map's shape (bag: `gBagMenu->newScreenCallback`; field: `gFieldCallback` + fade + a wait
  task). One BG, three full-width windows in palette 15 (header 30x2, list 30x16 = 8 rows of 16 px, footer 30x2;
  base blocks 1/61/541, 601 tiles under the map at char base 0 / screen 31). One `AllocZeroed(0xC00)`: the BG0
  tilemap buffer, then the state (layout in `questlog.s`'s header), pointer kept in the task's data[0..1].
- Text: `AddTextPrinterParameterized4` with speed `0xFF` (TEXT_SKIP_DRAW) draws into the window buffer only; each
  window is copied once when complete (`CopyWindowToVram(win, 3)`). Icons are 4bpp bitmaps made in the patcher
  from ASCII art and drawn with `BlitBitmapToWindow` `0x080039A5` (colour 0 is the key, so the row's own fill
  shows through); `GetStringWidth` `0x08005ED9` right-aligns the counters.
- Detail pane: the Journal's message for the step (+ `group_tail` for groups) is built into gStringVar4, the
  "<chapter> - Next objective:" line dropped, every FE/FA/FB turned into a plain line break, 8 lines a page
  (up to 8 pages). "A: Next page" when there is more.
- GOTCHA: keystone pads a code-section `.align 2` with `00 BF` and ignores a fill value. The patcher's own
  `thumb()` allows that nop only straight after a return or unconditional branch, where it cannot run.
- Tests (muted mGBA, copies of the ROM and save): `test_questlog.lua` runs the Journal's 94 scenarios
  (`../journal/test_journal_cases.lua`) through the screen from SELECT, and `check_questlog.py` checks against
  `../journal/expected.json` that the arrow is on the Journal's step, the screen opens on its chapter with it
  selected, and the detail text is the Journal's text laid out as above: 94 of 94.
  `test_questlog_screens.lua` opens it from the Bag and screenshots a walk through every chapter.
- Start menu shortcut (same patch): a framed "[R] Journal" box (R-button icon `F8 03`) at tilemap (1,1), 8x2,
  base block 8 - the Safari balls window's place and base block, so it is skipped when `GetSafariZoneFlag` or
  `InBattlePyramid` says that corner is taken, and when the Journal is not in the Bag.
  * Shown from `InitStartMenuStep` step 3 (the Safari/Pyramid step): its jump table entry at `0x0809F8C4`
    points at `case3`, which draws the box and jumps on to the original `0x0809F90C`. The table is reached by
    `mov pc, r0`, so the entry is even and the stub is entered in Thumb. Every path that (re)builds the menu -
    first open, back from the Pokedex/Bag/Save-cancel - goes through this step.
  * `HandleStartMenuInput` `0x0809FAC4` gets an 8-byte trampoline (4-aligned, first instruction: the stub
    replays `push {r4,lr}` before any call, then `r4 = gMain`, `r1 = newKeys`, `r0 = 0x40` and returns to
    `0x0809FACC`). R: SE_SELECT, box down, `gMenuCallback` = `menu_cb`, FadeScreen, return FALSE.
    A/B/START: box down first, then the vanilla code. `menu_cb` is StartMenuPokedexCallback's shape and sets
    `gFieldCallback2 = FieldCB_ReturnToFieldOpenStartMenu`, so B in the Quest Log lands back in the menu.
  * The window id lives at `0x02039E40` (EWRAM measured free) behind the magic "QLOG". EWRAM survives a soft
    reset, so a stale id is only removed if `gWindows[id]` still holds our exact template.
  * Tested (`test_questlog_menu.lua`): box with the menu, R -> Quest Log -> B -> menu with the box, B closes
    it, Pokedex and back re-shows it, R again. Not tested in the Safari Zone or the Battle Pyramid.

## SINNOH MAP: FLY TO THE LEAGUE DOOR — 2026-09-22
- Report: flying to the Sinnoh League lands at the Victory Road entrance, not the League. The outdoor League map
  (36/14, 29x47) has one Pokémon Center door at (10,34), Victory Road at (17,33) and its exit at (20,25), and the
  League building's door at (14,5). The Ride Pokémon courier has 17 stops, not 16: two are section 97 - block
  `0x0987D196` (flag 0x42EA, set by 36/14's on-transition script, warp to (10,35)) and block `0x0987D1AF`
  (flag 0x42EB, set by the trigger at Victory Road (31,2), warp to (14,6)). The Sinnoh Map's table is keyed by
  section, so it had only the first.
- `patches/leaguefly/`, data only: a 14-byte script at `0x08FEFF00` (`checkflag 0x42EB; goto_if_set 0x0987D1AF;
  goto 0x0987D196`) and the section-97 entry's block pointer (`0x08FDC578`) pointed at it. The map's name
  greying and the "visited" gate still use 0x42EA, as before. Flying to the door needs the flag the game
  itself uses for that stop, so it cannot skip Victory Road.
- `test_leaguefly.lua`: with 0x42EB lands at 36/14 (14,6), in front of the League; without it at (10,35).

## QUEST LOG: LEGENDS CHAPTER — 2026-09-22
- A fifth page: the 82 legendary and mythical Pokémon this ROM has (Gen 9's are absent), in National Dex order,
  from `patches/questlog/legends.py` (dex number, name, a no-name hint, and where / level / what it takes, each
  traced in the scripts: `tools/romdata/flag_audit.py`, `scripts.py`). Status comes from the game itself every
  time: `GetSetPokedexFlag` `0x080C0665` (a trampoline into the hack's expanded dex at `0x09257951`), case 1
  caught, case 0 seen. Rows: ✔ caught (1), dark box + name seen (6), grey box + "???" not seen (7). A always
  opens: the hint while unseen, the place once seen.
- National Dex numbers: the hack's `SpeciesToNationalPokedexNum` (`0x0806D4A4`) reads the table at `0x08F50370`
  (the table at `0x08F50CD0` is a different dex - Bulbasaur is 252 there). Species ids are not dex numbers:
  Kyogre is species 404, dex 382; Enamorus is species 1023-1025, dex 905; Dark Lugia (1079) shares Lugia's 249.
- Code: `row_status` / `row_title` (end of questlog.s) now give every row's status and text; the Journal
  chapters read the computed status array as before, the Legends page (PAGES entry byte 3 = 1) asks the dex.
  `STCOLOR` / `STSHOW` tables map a status to its colour set and whether the title shows.
- Data: the Legends table and texts (11,100 bytes) at `0x09F90000`, in the 0xFF run at the ROM's end
  (`0x09F82519`-`0x0A000000`). Code at `0x0802BF40` points at `0x09FE0000`, so the far end is left alone; the
  pointer-looking words into `0x09F90000`-`0x09FA0000` are all odd-aligned noise in graphics and script data.
- Found while tracing: Mew, Deoxys and Latias/Latios are set up through `setvar 0x8004 <species>` + a special,
  not `setwildbattle`, so a script scan for battle commands misses them; the value 249 also shows up in every
  Rock Smash rock's script (not Lugia).
- Silhouettes: at build time each legend's party icon (`GetMonIconTiles` table `0x08F2A020`, species -> 32x32
  4bpp, first frame) is cropped to the Pokémon, shrunk to fit 16x16 (a pixel is set when a third of the pixels
  under it are), and stored twice, in the text colour and the dim colour: 128 bytes each, after the Legends
  table. draw_list blits one at x=24 and moves the name to x=44 on that page only.
- Tested (`test_questlog_legends.lua`) on the late-game save: 37/82 caught, seen-not-caught rows present (which
  also proves case 1 is "caught"), hints and places open with A; the 94 Journal scenarios still 94/94; Start
  menu R still opens the log.

## QUEST LOG: KEY ITEMS CHAPTER — 2026-09-22
- A sixth page (PAGES type 2): the 55 key items the scripts hand out, in story order, from
  `patches/questlog/keyitems.py` {item, flag, name, hint, where}. Ticked when `CheckBagHasItem(item, 1)` or
  `FlagGet(flag)` - the flag covers items that leave the Bag: Devon Goods 0x8F, Letter 0xBC, Meteorite 0x73
  (the Journal's own flags), and pickups' object flags (Storage Key 0x44C, Dried Fish 0x4322, ...).
  `ext_entry` picks the Legends or Key Items table by page type; the Key Items page has no silhouettes.
- Data at `0x09F98000` (7,204 bytes), after the Legends' 32 KB and inside the checked window. The patcher asserts
  each id is in the Key Items pocket.
- `scripts.py` now indexes `copyvarifnotzero VAR_0x8000, <item>` (giveitem / finditem) as items. It also catches
  trainers' Pokénav registration scripts, which put a trainer id in 0x8000 - so "Gold Teeth", "Tea", "TM Case",
  a Route 116 "Meteorite" and similar are false hits; keyitems.py was checked by hand against each script's text.
- Left out (no source in any script): the FireRed leftovers, the Abandoned Ship room keys, Red/Blue Orb 2, the
  Wishing Chip and item 644. The Shiny Charm is a pickup the original hack put on Route 118 (flag 0x4022).
- Scott (Battle Frontier house, script `0x082636A8`): with flag 0x5C unset, ANY one Silver Symbol (Tower 0x8C4,
  Dome 0x8C6, Palace 0x8C8, Arena 0x8CA, Factory 0x8CC, Pyramid 0x8D0) jumps to `0x0987377A`, which gives item 173,
  the Endorsement (699) and the AuroraTicket (371), then sets 0x5C, 0x04 and 0x8D5 (the ferry flag). The all-gold
  branch (0x8C5..0x8D1) only gives item 174. The Key Items text first said "all seven gold Symbols" - wrong.
- Key item names are always shown (asked for: some item icons are custom, the name is what identifies them).
  Not got yet is status 8 - named, dim, empty box - and A gives `where` at once; the `hint` text is unused.
- Tested (`test_questlog_keyitems.lua`): 38/55 on the late-game save, used-up items ticked via their flags;
  94/94 Journal scenarios.

## QUEST LOG: CHAPTER GRID, SIDE CONTENT, ULTRA BEASTS — 2026-09-22
- The log opens on a chapter grid (V+3 mode 3). `draw_grid` draws cards 76 x 39 at x = 3 + col*79,
  y = 3 + row*42 on backdrop colour 13: gold border (14) when selected, the card (1), corners repainted by
  `corners` to round it, a 3 px stripe and a 16 x 16 icon in the chapter's colour (`ACCENT`, `GICONS`), a short
  label (`GNAMES`: "Artifacts", "Side Quests" - the full names do not fit beside nothing on 76 px), done/total
  right-aligned (green set COLORS+28 when complete). (A progress bar was tried and removed on request.)
- Speed: counting every chapter (~90 dex checks, 55 bag checks, the Journal rows) on each cursor move made the
  grid lag. `grid_count` now counts once when the grid is entered (open, B from a list) into V+0xC8..; a move
  only redraws. Measured: the cursor byte changes the frame after the press.
- Flashing border: the selected card's border is palette 15 colour 4 (the lists' selection bar, unused on the
  grid); `grid_pulse` runs every frame in grid mode and every 4th frame LoadPalettes the next of 16 steps of
  `PULSE` (gold <-> deep orange; white vanished against the cream card) - no redraw. Opening a chapter
  LoadPalettes PAL[4] back. The task skips input and pulsing while a palette fade runs.
  `rect(x, y, w, h; [sp] colour)` wraps FillWindowPixelRect. Palette 15 gained 13 backdrop, 14 gold, 15 purple.
  Counting borrows V+0 (row_status reads the chapter from it) and restores the cursor. `grid_input`: D-pad
  moves (Up/Down by 3), A runs `page_sel` and opens the list, B fades out. B in a list now returns to the grid
  instead of closing. `NPAGES` / `NLAST` in questlog.s are substituted by the patcher (7 / 6); up to 9 fit.
- Side Content (PAGES type 3), `patches/questlog/sidecontent.py`: {flag, name, where}, ticked by `FlagGet(flag)`,
  names always shown (status 8 when not done), A shows `where`. Flags are the ones each script sets, from
  the content audit (`tools/romdata/flag_audit.py`): Hisuian trades 0x0099/0x4327/0x4328/0x009B/0x009A/0x4329,
  gifts, the Lv5 starters' encounter flags, side-story scene flags.
- Legends now has the Ultra Beasts (the user counts them as mythical): Nihilego to Stakataka, 92 rows; each
  Ultra Space map is reached from several wormholes, the row names the main Hoenn one (warps read from
  maps.json events). Blacephalon is not in the game.
- Data moved: Legends 0x09F90000 (36 KB), Key Items 0x09F9A000, Side Content 0x09F9C000 - all inside the
  checked 0x09F90000-0x09FA0000 window; the patcher asserts the three do not overlap.
- Tested: `test_questlog_grid.lua` (open, move, open Legends, back, open Side Content and a row, close);
  Start menu R -> grid -> B back to the Start menu; `test_questlog.lua` (now presses A on the grid first) 94/94.

## HIDDEN POWERS: THE BURNING SOUL AND THE HERO GRENINJA — 2026-09-22
- Burning Soul: Route 112 (0/27) tile (7,26) - not in vanilla - warps to Magma Hideout 24/93. Object at (47,7)
  (flag 0x4297) is TM53; the sign at (48,9) needs 0x4297 and the Pokédex (0x864). "Leave?" yes -> var 0x409C=26,
  warp out; stay -> the Crimson Apostle's trial, rounds in var 0x4001, trainers 1155/1156/1157, Heart Scale
  move reminder between rounds; finishing sets 0x409C=27. Route 112's map script (`0x098520CF` ->
  `0x0988240C`) then always sets 0x42E2 (the cave is collapsed for good) and, only for 27, 0x4301. The power
  itself is not in any script (specials 145/312 are screen effects) - it lives in code.
- Hero Greninja: Koga on Champion Island (35/6, trainer 1160) sets 0x42FF and points to Route 102's forest;
  Koga's Village 35/45 (hidden) and trial grounds 35/85: one Greninja only, two stages (1159, 1158), sets 0x4300.
  Ash's 2-vs-2 is started by the rival in Birch's lab, not by Route 101 itself (corrected 2026-10-15: *Side quests
  rechecked*); Route 101's map script (`0x081EBCD5`, var 0x4023 checks) stages it and sets 0x4302; the note
  leads to Steven's Island 35/8 object at (4,5): -Echo-/-Hibiki-, trainer 1016, sets 0x4303. The book at
  35/8 (4,6) (`0x0983D029`) by "Gengyi Xiang" shows entries by 0x4300, 0x4301, 0x41D5, 0x4302.
- Both are Side Content rows (sidecontent.py). The user's save (2026-09-22): TM53 taken, cave not collapsed.

## QUEST LOG: SHINY STARS ON SIDE CONTENT — 2026-09-22
- How the hack forces a shiny: `callasm 0x08302931` rebuilds the Pokémon in party slot var 0x8004 (6 = the
  enemy's first, after `setwildbattle`) with nature var 0x8005 and gender var 0x8006 (255 = random each); var
  0x8007 = 1 makes it call `0x08302B10`, which rolls a personality whose halves XOR to the player's
  (TID ^ SID) & 0xFFF8 plus Random % 8, which is always shiny. Its neighbours in the same scripts:
  `0x08FFF201` sets perfect IVs (var 0x8005 = how many), `0x0981E531` teaches move var 0x8006 in slot var 0x8005.
  givemon (0x79), ScriptGiveMon (0x080F9244), CreateMon and CreateBoxMon are all vanilla, with no shiny switch.
- Always shiny, from each row's scripts: the hidden Snivy (0x045D), Litten (0x0415), Grookey (0x40B8) and
  Scorbunny (0x40EA) battles, the cursed statue's Gengar (0x432D), and the Drifloon gift (0x42DE: getpartysize
  - 1 into 0x8004 after its givemon). Oshawott, Chespin, Chikorita, Cyndaquil and Totodile skip the call; every
  other gift is a plain givemon; the six Hisuian trades (sIngameTrades at 0x08BA0300, 0x3C each, indices 0-5)
  have fixed personalities that are not shiny.
- Checked in mGBA by running each set-up from its own script (`_testrun/rw/ql/shinycheck/`): Snivy, Litten,
  Gengar and Drifloon came out with shiny value 0-2 for the save's OT ID; the Oshawott and Beldum controls were
  3455.
- `sidecontent.SHINY` holds those flags; `sides_blob` writes bit 0 of each row's first halfword (was 0).
  `draw_list`, after printing a row of a type-3 page, blits `STAR` (8 x 16, red = palette 15 colour 7) at
  x = text start + GetStringWidth(1, name, 0) + 3. The star is drawn whether or not the row is ticked. Tested:
  `test_questlog_side.lua` (every screenful of the chapter), `test_questlog.lua` 94/94 (the task moved to
  0x08FEA82D).

## SINNOH LEAGUE ATTENDANT TEXT — 2026-09-22
- Where: the Elite Four hall is map 34/30 (map section "Test of Heart"), reached from the Sinnoh League lobby
  34/37 through the two guards. Its map script `0x09875272` (type 2/4, var 0x4000) runs on every entry: the
  x the player arrives at (var 0x8004: 4, 8, 18, 22) says which door they came back through, adds that door's
  bit to var 0x409C (1, 2, 4, 8), closes the door, then `message 0x09875BFF` (the heal line), the heal jingle,
  and at 15 the Champion's door (x 13, warp to 34/31); otherwise "Please choose the next door." and
  `multichoice 20, 4, 126, ignoreB` at `0x098754BF`. Answers 0-3 open the doors at x 4, 8, 18, 22 (warps 6-9);
  a door whose bit is set gets "didn't you just go through this door?".
- Untranslated: the heal line (the only reference is that `message`; an English version existed in
  translation/translations/trans_22.json as "MoeMoe Staff: ..." but was never inserted) and the four door names
  左一 / 左二 / 右二 / 右一 (left 1, left 2, right 2, right 1, counted from the outer walls). The hack's
  multichoice table is at `0x09700000` (8 bytes an entry: list pointer, count); list 126 is at `0x09876B14`,
  {text, unused u32} rows. The window sizes itself to the longest string and moves left if it would overflow.
- Lucian's line when he beats you (`0x08B41CF9`, used by `0x09875986`) began "Wusong:", his Chinese name 悟松.
- `patches/leaguetext/`: strings at `0x08FF2460..0x08FF24C0`, the message and the four list pointers repointed,
  "Wusong" -> "Lucian" in place. The heal line is "Attendant: ...", matching her translated welcome. Tested
  (`test_leaguetext.lua`): the heal line, the menu with the cursor on each door, the answer (3 for Far right),
  Lucian's line; all drawn from EWRAM scripts on the field. The whole hall was not played through.
- Tool: `_testrun/cn.py ADDR` decodes any text address, Chinese included, with story_extract.py's rules.

## QUEST LOG: "GOTTA CATCH 'EM ALL!" — 2026-09-22
- The Legends chapter has a row 0 above Articuno: "???", an empty box and a dim Master Ball until every legend
  is caught, then a tick, a Master Ball in colour and "Gotta catch 'em all!" in purple. A reads the hint
  before and a congratulation after (`ALL_CAUGHT` in questlog_patch.py). It is selected when Legends opens.
- Data: the Legends table and both silhouette sets gained a first entry (dex 0). PAGES says rows 93,
  objectives 92.
- The ball is the Bag's own Master Ball icon, read from the ROM at build time (`master_ball()`): item icon
  table 0x08FCBFF4 (GetItemIconPicOrPalette, literal at 0x081B0034; {LZ77 4bpp 24x24, LZ77 palette} per item),
  item 1. The ball fills x/y 3..20 of the 24x24; dropping rows and columns 2 and 15 of that 18x18 crop gives
  16x16 with the outline, the M and the pink bumps intact. (A first try drew it by hand in palette 15; the
  palette has no pink, so the bumps came out red.) Its 13 colours go to palette 14 slots 2,3,5-15, with 0/1 the
  paper and 4 the selection bar as in palette 15, so the row's background looks the same. `cb2_init` loads it
  (`MBPAL`, LoadPalette 0xE0). `draw_list` now does PutWindowTilemap, then, on the Legends page scrolled to
  the top with row 0 at status 9, sets the palette bits of the ball's four tilemap entries ((3,2),(4,2),
  (3,3),(4,3); the tilemap is the 0x800 bytes before V) to 14, then CopyWindowToVram(3). Every redraw's
  PutWindowTilemap puts them back to 15. Locked, the ball is drawn in palette 15: its dark colours in 5
  (grey, like the unseen silhouettes), light ones in 12.
- Code: `row_status` for type 1 sends row 0 to `legend_all` (new function, in the `order` tuple after
  ext_entry), which checks FLAG_GET_CAUGHT for table rows 1..NLEG (`#NLEG` is substituted by the patcher) and
  returns status 9 (all caught) or 7. Status 9 is new: tick icon (9th ICONS entry), colour set 32 (COLORS
  (1,15,3)/(4,15,3)), title shown. open_detail shows the hint only for status 7, so 9 gets the "where" text.
- Counting: the header (`dh_cnt`) and the grid (`grid_count`) used to count rows 0..objectives-1, which would
  have skipped the last legend. Both now scan every row and count status 1 only, and show the objectives as
  the total. The rows left out of the total never have status 1: this one is 7 or 9, and the Journal's
  closing row is 2 or 5 (`cp_final`).
- Pokedex flags, for tests: the hack's GetSetPokedexFlag (0x080C0664 -> 0x09257951) uses SaveBlock1 +0x560
  (seen) and +0x5D8, byte dex/8, bit dex%8 (no -1); caught needs both bits.
- Tested: `test_questlog_allcaught.lua`, once on the save as it is (39/92: "???", dim ball, hint) and once
  with ALL=1 (all 92 marked caught: tick, ball, purple title, congratulation, 92/92 in the header and on the
  grid; the bottom still ends at Enamorus). `test_questlog.lua` 94/94 (task now 0x08FEA835).

## QOL VERSION IN THE OPTION TITLE — 2026-09-23
- `patches/qolversion/`: the Option screen's title bar (main menu -> Option, CB2 0x080BA4B1) reads
  "Ultra Emerald v5.7 (Standard)"; it now reads "Ultra Emerald v5.7 +QoL1.5 (Standard)". One string per
  difficulty, through the table at 0x09F07DF4 (4 words: Standard, Hard Mode, Challenge, Lunatic, each
  pointing a byte or two into a string that starts with a space and the colour codes FC 01 04 FC 03 05).
  The patch copies each string from its own pointer, inserts "+QoL<version>" before the "(", writes it to
  free space (0x08FF24C0..) and repoints the word, so the hack's own wording and colour codes are kept.
  Hand-writing the prefix instead put a stray hanzi in front of the text.
- Width: the title window's text area is x 24..225. Measured in mGBA: the old title ends at 174, this one at
  216, and the longest ("Hard Mode", "Challenge") at 219. " +QoL 1.5 " with the inner space overflows - the
  first try was cut off at "(Standar" - so the tag is written "+QoL1.5".
- The hack writes "V5.7" for Standard and "v5.7" for the other three; copying its bytes keeps that quirk.
- Still plain 5.7: the mode-select screen's "Ultra Emerald v5.7" (0x09F07DD5, from 0x09F03434 / 0x09F0368C)
  and the "Ultra Emerald 5.7   Mode: X" banner (0x09F0B5ED.., table around 0x09F0ABEC) - not touched, their
  screens were not measured.
- `patches/version/` (5.5 -> 5.7) is unchanged and still runs early in the chain; this one goes at the end.

## QUEST LOG: THE GRID CURSOR WAS SLOW — 2026-09-23
- Reported as lag when moving between the chapter cards. Measured (`_testrun/rw/ql/lag/test_grid_lag.lua`:
  press a direction, then screenshot every frame and follow the gold frame): the cursor byte V+0 changed on
  the frame after the press, but the frame on screen only moved **13 frames later**. So the input was fine
  and `draw_grid` was taking ~12 frames of CPU.
- Why: every move redrew the whole grid - FillWindowPixelBuffer over the window, then for each of the 7 cards
  a 76x39 filled rect, corners, a stripe, a 16x16 icon and two strings. `rect` is FillWindowPixelRect
  (0x08003B65), which fills **one pixel at a time**, recomputing the tile address per pixel: ~24,000 pixels a
  redraw. The 2026-09-22 fix (caching the counts in `grid_count`) removed the counting, not the drawing.
- Fix: a move changes only two things, the frame the cursor left and the one it arrived at, and the cards
  themselves are already on screen. `card_border(V, card, colour)` draws one card's 2 px frame as four thin
  rects plus `corners`; `gi_move` calls it for the old card in the backdrop colour (13) and the new one in
  colour 4 (which `grid_pulse` cycles), then `show`. About 950 pixels instead of 24,000.
- Measured after: the frame moves **2 frames** after the press (one to process, one to display). The grid is
  pixel-identical to the full redraw apart from the pulse phase. `test_questlog.lua` 94/94.
- Entering the grid (opening the log, or B from a list) still draws all seven cards once, ~12 frames; the
  first one is behind the fade-in. Worth revisiting only if it is noticeable.

## RARE CANDY NPC AND NATURE DISPLAY FIX (PR #1, MERGED IN PART) — 2026-09-23
- From anibalribeiro's PR #1 on the public repo ("Party editor, Rare Candy NPC, and a nature-display fix",
  head b426fa4). Taken: `patches/candynpc/` and `patches/naturefix/` (commit 03cb3a5, authored by them).
  Left out on purpose: the party editor (`patches/partyedit/`), the release patch rebuilt with it, and the
  v1.5 docs (they predate our Journal/Quest Log rows and would have rolled some README rows back).
- Their findings, kept: `giveitem` (0x44) masks its amount to a byte (0x080999C8), so 999 goes over as
  255+255+255+234; the hack's GetFlagAddr (0x09F00CEC) only accepts flags <= 0x3FFF or 0x4000..0x467F; the
  hack persists object events in SaveBlock1, so a save made inside the Mart keeps that save's NPC positions;
  the Mart (8/6) object array is flush against its warps, so it is copied to 0x08F53700 with a 5th entry.
  GetNature (0x0806D070) ignores the Mint's override at mon+0x1F; the stub at 0x08F54200 returns it.
- Changed on merge, both found by testing on our saves:
  * The "given" flag. 0x4013 has no script reference, but it was set in all eight saves checked (147 to 601
    custom flags each), so the hack's code sets it early in every game - the NPC answered "I have already
    given you my stash" on a first talk. Census (every custom flag set on any save vs every flag any script
    touches): 354 flags are set by code alone, mostly 0x4013-0x40F7 and 0x4421-0x4609. Now 0x433F: no script
    references it, clear in all eight, last flag of the SB1+0x3B24 block, past the last story flag 0x432D.
  * The Mint's list (multichoice 0x7C) is None, Lonely .. Careful, Hardy: 0 means no override and 24 is Hardy
    (there is no Quirky). The stub returned 24 as-is, so a Mint "Hardy" showed as Quirky. It now maps 24 to 0.
    Both are neutral natures, so the stats already agreed.
- A wrong turn worth recording: I first split the 999 into 255,255,255,128..1 to "top up to the cap". The
  Bag starts a second stack when one fills (as vanilla does), so every chunk landed and gave 1,020. The PR's
  four chunks give exactly 999 whatever you already hold (checked: 30 -> 1029).
- Tested on our build (their Lua was tied to their machine and to the party editor):
  `patches/candynpc/test_candy_mart.lua` warps into 8/6 by a script from EWRAM, talks, says yes: candies
  30 -> 1029, flag 0x433F 0 -> 1, a second talk gives nothing. `patches/naturefix/test_nature_summary.lua`
  sets the lead's override and opens the summary: 13 Jolly, 24 Hardy, 0 the personality's own (Bold).
- Chain: `... -> qolversion -> candynpc -> naturefix`. candynpc uses 0x08F53700..0x08F5382F and naturefix
  0x08F54200..0x08F5423C, inside the free run 0x08F53700..0x08F54AA0.

## HYPER TRAINING: "THE IV STILL SHOWS THE OLD VALUE" — 2026-09-23
- Report: after hyper training on Champion Island the IV "doesn't show 31, it keeps the old value".
- The trainer (map 35/28, object 18, script 0x09812758): A2 (choose a Pokemon), must be level 100
  (0x098126D9 reads mon[+VAR_8005] = +0x54), then multichoice 0x74 - "All (Gold)", "HP (Silver)" ..
  "Sp. Def (Silver)". Gold needs var 0x40FB > 0 and item 0x2AF; a single stat needs var 0x40FC > 0 and item
  0x2B0. 0x098126FD ORs VAR_8005 into **mon+0x1E** (Gold: 0x7E; one stat: 0x09812721 makes 1 << choice) and
  compares old/new to refuse a second time. Bits, tested one at a time: 1 HP, 2 Atk, 3 Def, 4 Spe, 5 SpA, 6 SpD
  - the IV field order 0x27..0x2C, so bit = field - 0x26. (mon+0x1F is the Mint's nature byte.)
- The training works: the hack's CalculateMonStats (0x08068D0D) counts a trained stat as IV 31 (Gardevoir,
  all six: max HP 272 -> 289 with IV 14, Def 149 -> 177, SpD 246 -> 276). The IV word at +0x48 is never
  rewritten - as in the official games, so breeding and Hidden Power keep the real IVs.
- What was wrong: (1) the EV-IV Display item (item 650, 0x09689001; its loader 0x0968A42C reads IVs with
  GetMonData 0x27..0x2C) and the IV judges (script 0x08FF0040 -> callasm 0x08FF0001, via the stub
  0x08FF0020) print the raw IV; (2) the stats only move on a recalculation. The trainer says "deposit it on
  the PC to rest", but depositing does nothing (tested through the real storage screens: the box copy keeps
  the bits and the old IVs); it is the withdraw that recalculates.
- `patches/hypertrain/`: ht_getmondata (returns 31 for a trained IV field, everything else passes through)
  behind the EV-IV loader's literal 0x0968A65C and the judges' stub word 0x08FF0028 - both used by nothing
  else. The screen then worked out Hidden Power from the displayed 31s (Dragon turned into Dark in the
  first test): its parity code 0x0968A07A..0x0968A0B1 now goes through a 10-byte trampoline to ht_hptype,
  which returns the real IVs' low bits that ht_getmondata recorded at EWRAM 0x0203D600 - masked to six bits,
  because EWRAM is not zeroed (the first try skipped the mask and drew a garbage type icon). The trainer's
  success path 0x09812840 now goes through a script that calls ht_recalc (CalculateMonStats on
  gPlayerParty[VAR_8004]) and rejoins; his last line says the stats are maxed out instead of "deposit it".
  Code and script at 0x08F54300..0x08F543CD.
- Tested (`test_hypertrain.lua`, BITS=126 and BITS=2; `test_hypertrain_bits.lua` maps the bits): stats
  change the moment he finishes; the EV-IV Display shows 31 for trained stats only and keeps the real
  Hidden Power type (Dragon); the judges read 31/31/31 for all six, 31/20/3 for HP only. The item and var
  checks in front of the training are the hack's and were not changed.

## QUEST LOG: UNBOUND-STYLE LIST AND INFO PANEL — 2026-09-24
- Asked for (with a screenshot of Unbound's mission log). The list window is now 30 x 18 tiles (the footer
  window sits on its last two rows and is only put back in the grid and detail views; `draw_footer` returns at
  once in list mode, `draw_grid` re-puts it after every redraw). `draw_list` draws LROWS = 5 rows (y 0-79) on the
  dark backdrop: a hairline, the selected row in colour 8 with the white arrow, the name (white, grey while
  "???": `NAMEFG` by status) and a right-aligned tag (`TAGS` / `TAGFG` by status: Done green, Active gold, Side
  purple, Seen gold, To do / ??? grey). Gold scroll arrows sit in the panel's top right corner (drawn after it). `dl_colours` builds a
  {bg, fg, shadow} triple at V+0xF0 for the selected / unselected background. Scrolling: `tk_down`, `page_sel`
  now use LROWS.
- The panel (`draw_pane`, y 80-143): a white frame, window 3 (8 x 8 tiles at map (1,12), BG palette 13, base
  block 661) with the portrait, "Location:" (gold) plus the place (white), and three lines of text. Rows come
  from `pane_entry`: PANES[chapter type] -> 16-byte rows {kind, Gotta-catch row?, id, location, text, hidden
  text}; the Journal table is indexed by step (first + row). Journal steps still ahead (status 4/5): "???", no
  picture. A legend not seen (7): its silhouette, "???" and its hint. The Gotta catch row: the Master Ball icon,
  as a silhouette until status 9.
- `portrait(kind, id, silhouette?, V)`: LZ77UnCompWram (0x082E7091) the picture into V+0x400 (8 KB: Castform keeps
  all four forms in one 0x2000 block), a 64x64 one copied straight into gWindows[3].tileData (same tile layout),
  an item icon (24x24) blitted in the middle; the palette decompressed to V+0x2400 and LoadPalette'd to 0xD0,
  or `SILPAL` (all dark) for a silhouette. Alloc is now 0x2C40.
- Tables (each asserted against the literal in the routine that uses it): Pokémon pictures 0x08F20A20
  (LoadSpecialPokePic, literal 0x080346CC), palettes 0x08F25520 (0x0806E758), trainer pictures 0x0901BE90
  (DecompressTrainerFrontPic, 0x0805DF78), their palettes 0x0901C660 (0x0805DF80), item icons 0x08FCBFF4 (as the
  Master Ball row already used). 500 trainer-pic slots, 250 real; `tools/romdata/dump_trainers.py` gives each
  trainer's `pic`. Hisuian forms share names with the regular ones (Zorua 623 / 1017, ...): portraits.py can name
  a species by number.
- Texts are wrapped by pixel width at build time with the game's glyph widths (`gFontNormalLatinGlyphWidths`
  0x086542E4, checked at GetGlyphWidth_Normal 0x0800691C) to 158 px, three lines, an ellipsis when cut.
  Locations: portraits.JOURNAL by hand; Legends / Key Items / Side Content from their own texts (`place_in`,
  `tidy`) with `LOC_OVERRIDE`. No-spoiler: Journal steps whose text hides who waits there have no portrait.
- Data: the panel tables and texts at 0x09FA0000 (asserted < 0x09FB0000). Free for other work now:
  0x09FB0000-0x09FDFFFF.
- The grid follows the same theme: backdrop colour 10, cards 13, white names and grey counts (`GCOL`: name, count,
  complete), the Side Quests card's bubble light (12) instead of navy.
- Tested (`test_questlog_panel.lua`) on the late-game save, every chapter type; `test_questlog.lua` 94/94.

## HISUI ON THE SINNOH MAP — 2026-09-25
- `patches/hisuimap/`: the Sinnoh Map shows Hisui while you are in Hisui. The screen is sinnohmap's, rebuilt as
  `regionmap.s` around a REGION RECORD {palettes, tiles LZ, tilemap LZ, places, fly table, names or 0} and
  installed new at `0x08FF3000..0x08FF54C0` (unreferenced run 0x08FF2574..0x08FFD5A0). Item 361's field-use pointer
  moves 0x08FDBCB1 -> 0x08FF3001. The old screen stays in the ROM unused; its overworld stub (hands you the item)
  is still what the hook chain runs. The Sinnoh record points INTO the old blob (palette 0x08FDC5C0, tiles
  0x08FDC760, tilemap 0x08FDDF58, places 0x08FDE3C0, couriers 0x08FDC4FC), found by content and asserted unique,
  so leaguefly's edit of the section-97 courier entry keeps working.
- `where()` picks the record on every lookup: GetMapSec; section 104 = Hisui (only 37/103..108 use it - checked
  by walking every map header), key = SB1+5 mapNum; anything else = Sinnoh, key = mapsec. Tables are {key, x, y}
  and {key, pad, flag, block}; a fly flag of 0 means always allowed (Mingyao checks nothing). Hisui names come from
  its own table {key, pad[3], text}; Sinnoh still uses GetMapName.
- Marker tile moved to a fixed slot, tile 511 of BG1's character block (0x06007FE0, entry 0xD1FF), past both
  pictures (Sinnoh 409 tiles, Hisui 360). The old task clobbered r7 without saving it; the new one pushes it.
- Fly blocks are Mingyao's (menu at 0x0989ADF0, multichoice 137): `75 <Braviary> 01 04` showmonpic, `6D`
  WAITBUTTONPRESS, `76` hidemonpic, `39 25 <map> 01 ...` warp 37.<map> warp 1. 104 AE3C, 103 AE4D, 105 AE5E,
  107 AE6F, 106 AE80 (0x0989xxxx). So after A on the map her Braviary appears and waits for a button, as it
  does when you talk to her. The temple (37/108) has no block: on foot from Coronet Highlands (40,38).
- Mingyao's list 137 at 0x098031A8: entries 1 and 3 (0x098365E1 / 0x098365F3, Chinese) repointed to "Deertrack
  Heights" and "Snowfall Hot Spring" in the blob. The multichoice box sizes itself; "Snowfall Hot Spring" fits.
- Picture: `tools/make_hisui_townmap.py` (Sinnoh palette, drawn from the Legends: Arceus map; the squares now
  fill exactly one 8x8 cell so the marker covers them) -> `tools/make_region_map.py --colors 32` -> 2 palettes,
  360 tiles, 5.6 KB + 1 KB LZ77. Places (tiles): Snowfall (10,4), Temple (15,7), Coronet (15,9), Firespit (26,5),
  Deertrack (6,12), Prelude (10,14).
- Tested (`test_hisuimap.lua`): warp to 37/106, open (direct CB2 and through START > Bag > Use), hop U,U,L,D,R,R
  (Temple, Snowfall, Deertrack, Prelude, Coronet, Firespit - names right), A on Firespit -> Braviary, A -> 37/105;
  from the Bag, D -> Deertrack, A, A -> 37/103 next to Mingyao, script lock 0; her menu shows five English names.
  Sinnoh regression: 36/3 opens on Oreburgh City, hops name Oreburgh Gate / Route 204, B back to the field.

## POKEDEX DESCRIPTIONS AGAINST THE FRAME — 2026-09-25
- Report: Morelull's entry on the "registration completed" page started under the frame ("t scatters...") and
  stopped on a ▼. PrintMonInfo (0x080C020C; the description part 0x080C0314..0x080C0342) prints the text from
  the dex table 0x09250000 (+16) centred: x = GetStringCenterAlignXOffset(1, text, 240) (0x081DB35C), y 95.
- Cause: 5 of 960 descriptions (slots 562, 722, 753, 755, 802) used 0xFA (scroll + wait for a button) as a line
  break. The printer waits on it (the ▼), and the width measured for centring ran the lines around it together
  past 240 px, so x fell to 0. The other 955 use 0xFE only.
- Also: the hack's own English entries are at most 224 px wide per line; ours went to 231 (4 px from the frame).
- `patches/dexdesc/`: 0xFA -> 0xFE, and any description wider than 224 px re-wrapped greedily at 224 px in at most
  4 lines (30 entries; none needed a 5th). Only separator bytes change (93 bytes, 0x00 <-> 0xFE / 0xFA -> 0xFE),
  so lengths and addresses stay; nothing repointed. After: max width 224, max 4 lines, no 0xFA.
- Checked by measuring with the game's glyph widths (gFontNormalLatinGlyphWidths 0x086542E4), not yet on screen.

## OVAL CHARM, AND ITEM 644 — 2026-09-25
- `patches/ovalcharm/`, blob `0x08FF5600..0x08FF590E`: egg_roll, the icon (LZ77 pic + palette), texts, the
  Day-Care Man's new head.
- Item: slot 114, one of the hack's unused "???" slots (name `3D`x7..., id 0x72, pocket 1; the script index
  shows no give/take/check of 114-116). Entry copied from the Shiny Charm (119: pocket 5, type 4, field use
  0x080FE821 "can't use"), name/id/description replaced. Icon table 0x08FCBFF4 entry 114 -> ours;
  `make_icon.py` redraws the Shiny Charm's icon (string, bead, tassel kept) with an oval gem, 9-colour palette.
- Egg roll: TryProduceOrHatchEgg is vanilla. 0x08070B0E..0x08070B33 was `adds r0,r6,#0; bl 0x08070D4C
  (GetDaycareCompatibilityScore: 0/20/50/70); bl Random 0x0806F5CC; *100; bl __udivsi3 0x082E7B68 by 0xFFFF;
  cmp; bl TriggerPendingDaycareEgg 0x080701E0`. Now: `adds r0,r6,#0; ldr r3,=egg_roll; bl <bx r3>; cmp r0,#0;
  beq out; bl 0x080701E0; b out` + pool + `mov r8,r8` filler. egg_roll repeats the roll with 20->40, 50->80,
  70->88 when CheckBagHasItem(114, 1). The other caller of the score (0x08070E76, the man's "get along" line)
  is untouched. GOTCHA from the skill: Keystone's `nop` is 00 BF - never use it, even in dead filler.
- Day-Care Man: Route 117 (0/32) object 2, script 0x08291C18 (`6A 5A 25 B8 00` lock, faceplayer, special
  0xB8; three references, all to the entry, none into its first 5 bytes). Those 5 bytes -> `goto` our head:
  lock, faceplayer; checkflag 0x433E / goto_if set -> usual; checkflag 0x864 / goto_if unset -> usual;
  msgbox intro; additem 114,1 (raw 0x44); setflag 0x433E; playfanfare 0x173; msgbox "received"; waitfanfare;
  msgbox; release; end. "usual" = special 0xB8; goto 0x08291C1D.
- Flags: 0x864 = FLAG_SYS_GAME_CLEAR, the Hoenn League beaten (the Journal's Hoenn finale uses it; first built
  on 0x42D5, the Sinnoh League, set only in Cynthia's room 34/31 - moved to Hoenn at the user's request).
  0x433E (given): no script
  references it, no aligned literal of it anywhere, clear in all 34 saves checked (0x433F is candynpc's).
- Item 644 was 脚本测试器 "Script Tester": a developer's item (field use 0x08FF1C41 runs a test script via
  ScriptContext1_SetupScript), in no script, with the Grassium Z's description. Renamed, own description.
- Tested (`test_ovalcharm.lua`): GIFT on the user's save (0x864 set): warp below him, talk -> intro ("...became the Champion of Hoenn!"),
  "Jude received the Oval Charm!", closing line; item 114 in Key Items; talk again -> his usual line; lock 0. NOHOF=1 (clearflag 0x864 first): only his usual line, nothing given.
  ODDS on a test copy whose egg_roll reads a forced score from an EWRAM stub, 5000 rolls each: no charm
  0 / 19.7 / 50.4 / 69.8 %, with charm 0 / 40.9 / 79.2 / 88.0 % for scores 0 / 20 / 50 / 70. BAG: both items'
  names, icons and descriptions in Key Items. Diff vs the archived ROM: only the six intended regions.
- Not in the Quest Log's Key Items chapter yet (that needs the questlog rebuild).

## HOENN FLY MAP: SQUARES FOR THE ISLANDS — 2026-09-25
- Report: Steven's Island can be flown to from the Fly map but nothing marks it there.
- The hack's GetMapsecType (0x08123D58) is table-driven: u16 per map section at 0x08C4CFA0 (literal at
  0x08123D9C); 0xFFFF -> 1 route, 0 -> 0 none, else FlagGet(flag) ? 2 (can fly) : 3. The Fly map's A press
  (0x08124DAE) flies on type 2 or 4. Non-town sections with a flag: Battle Frontier 0x3A (0x8A8), Champion
  Island 0x45 (0x419C), Southern Island 0x49 (0x8A9), Strange Island 0x71 (0x4178), Steven's Island 0x9E
  (0x4150).
- Towns get their dots from the region map picture; special areas get a red-outlined square SPRITE from
  CreateSpecialAreaFlyTargetIcons (vanilla), which walks sRedOutlineFlyDestinations {flag, mapsec}...{0xFFFF,
  0xD5} at 0x085A1F18 - only the Battle Frontier. Its only reader is the literal at 0x08124CAC.
- `patches/flyicons/`: a new table at 0x08FF5A00 (24 bytes) with all five, read from the hack's flag table and
  using the same flags, so a square shows exactly when Fly works; the literal repointed. Sprite position is
  ((x+1)*8, (y+2)*8) from gRegionMapEntries (0x085A147C), 16x16 for 1x1 sections.
- Other region-map facts found on the way: CB2_OpenFlyMap 0x08124691 (party menu literal 0x081B5620); map
  tiles LZ 0x0859F77C (233 8bpp tiles), 64x64 affine tilemap LZ 0x085A04E0, palette 0x0859F73C.
- Tested (`test_flyicons.lua`, opens the Fly map from the field): on the user's save the control shows only the
  Battle Frontier's square; patched adds Steven's Island, Strange Island and Champion Island (the last partly
  under the fixed name box, where the island is). Southern Island's flag is clear on that save.

## EGG MOVES — 2026-09-25
- Report: "egg moves aren't passed down; the egg move table might be wrong".
- How eggs get moves here (_GiveEggFromDaycare 0x080708C8): parentSlots from DetermineEggSpeciesAndParentSlots
  (0x080707EC, vanilla: [0] mother = female or non-Ditto, [1] father = the other / Ditto); InheritIVs is
  trampolined (0x08070260 -> 0x09F00B08, the hack's): IVs/items, then with the mother from 0x09F007F8 it
  inherits her Ball (0x09F007A0) and her egg moves (0x09F009A4: GetEggMoves(egg), each one the mother knows ->
  GiveMoveToMon 0x08069141 / DeleteFirstMoveAndGiveMoveToMon 0x080694D1). Then vanilla BuildEggMoveset
  (0x08070470, called at 0x08070906 with father = mons[parentSlots[1]]): father's egg moves, his TM moves,
  moves both know. GetEggSpecies 0x08070004 -> 0x09F006F9 (the hack's).
- So the modern rule already holds. Measured (test_eggmoves.lua: two parents written into SB1+0x3030, the egg
  made by 0x080708C9 via callasm, its moves read from the party): mother / father / Ditto+female / Ditto+male
  each pass Curse to a Bulbasaur egg; a father with 4 TMs does not push it out.
- The table (0x09D78128, species+20000 markers, 381 lists) matches modern data; of ~65 common breeders checked
  only Tynamo, Rufflet, Carbink, Impidimp have none, as in the modern games. Internal species ids are not
  National Dex numbers - use tools/romdata/out/species.json and moves.json for names, not the header tables.
- The bug: GetEggMoves copies up to 16 (`cmp r2,#0xF` 0x08070446) into sHatchedEggEggMoves 0x02024A38, which
  BuildEggMoveset sizes at 10 (`cmp r6,#9` 0x080704BA). 11-16 spilled over sHatchedEggMotherMoves 0x02024A4C and
  beyond; a 17th was never read (Turtwig, 17: Tickle). `patches/eggmoves/`: buffer -> 0x02031C00 (32 moves;
  the 64 bytes test_scratch_ram.lua measured), the three words naming it repointed (0x08070580, 0x09F00A60,
  0x09F01CA0 - asserted to be the only ones), both limits -> 31. Turtwig then passes Tickle from either parent;
  the other nine cases give the same eggs as before.

## EXP. SHARE ON/OFF — 2026-09-25
- The hack's Exp. Share is key item 182 (pocket 5, field use 0x080FE821 "can't use"); its own text says "Just
  keep it in your Bag and it takes effect". The experience code (hack, around 0x09D5AB00; getexp in the command
  table 0x0831BD10 entry 0x23 points at 0x08E0BC01, not readable as plain Thumb - not needed) checks
  CheckBagHasItem(0xB6, 1) at 0x09D5AB80, 0x09D5AC22, 0x09D5ACE6 (pool word 0x09D5AE40) and 0x09D5B018 (pool
  0x09D5B094); those two words have no other readers.
- `patches/expshare/`, blob 0x08FF5B00..0x08FF5C36: share_check = CheckBagHasItem, but 0 for item 182 while flag
  0x433D is set (both pool words repointed); item_use flips 0x433D (FlagGet 0x0809D791, FlagSet 0x0809D741,
  FlagClear 0x0809D769) and shows the message the Coin Case way (StringExpandPlaceholders into gStringVar4,
  over the Bag 0x081ABB4D / on the field 0x081978ED). Item 182: field use -> item_use, registrability 1, new
  description. 0x433D: no script refs, no literal, clear in 34 saves.
- Tested (test_expshare.lua, user's save: party Lv 100 x5 + Lv 69 in slot 3): share_check 1; Lv 2 Magikarp
  won with slot 0 -> slot 3 +2 EXP; used from the Bag -> "turned off", share_check 0; same battle -> slot 3 +0;
  used again -> "turned on", share_check 1. Test gotcha again: the Start menu keeps its cursor and the Bag
  its pocket between uses.

## WORKING ROM REBUILT WITH THE QUEST LOG REDESIGN — 2026-09-25
- The Unbound-style Quest Log (6ecc413, made on the other PC) had been pulled but never built into the working
  ROM, which still had the 321ba5a Quest Log. questlog sits early in the chain, so the ROM was rebuilt from the
  v1.4 archive + the shinybox 2-byte edit + the whole post-1.4 chain (HANDOFF order).
- Check first: the same chain with the 321ba5a questlog sources (git archive 321ba5a patches translation tools)
  reproduced the working ROM with 0 differing bytes. With the current sources the only differences are the
  Quest Log's own: its blob 0x08FEA000..0x08FEC5D4 (now 9684 bytes), its panel data 0x09FA0000..0x09FA6196 and
  its two bl sites 0x0809F8C2 / 0x0809FAC6. Every later patch applied unchanged at the same addresses.
- Tested on the rebuilt ROM: test_questlog_panel.lua (every chapter type, detail, grid, back to the field) and
  test_questlog.lua (94 cases, no failures).
- Lesson: after pulling a change to a patch that is not last in the chain, rebuild the chain right away.

## SIDE CONTENT ROWS TICKED ON A NEW GAME; BURNING SOUL PORTRAIT — 2026-09-25
- Report: "A legendary choice" and "Snivy" were ticked right after starting.
- Snivy (0x045D): it is the object's own flag (Petalburg Woods 24/11 object 11, flag 0x045D) - set from the start
  (hidden), cleared by Ever Grande's guard (0x0983CD07: sets 0x40B2, 0x41B0, clears 0x045D, after 0x864/0x40C3),
  set again by the battle script (0x098B9847). No other script touches it. Now done = 0x045D AND 0x41B0:
  sidecontent.ALSO {flag: second flag}; the row's marks u16 carries it in bits 1-15 (bit 0 stays the shiny
  star, tested with lsls #31 only), and row_status's rs_side checks it when non-zero.
- "A legendary choice" (0x4311): Littleroot Town trigger (8,7), var 0x4009 == 0 - a TEMP var, so it runs on
  every entry - script 0x0982BF18: setvar 0x4009 1; if 0x4311 set, end; setflag 0x4311; then 0x0982BF45 (gives
  the Mega Bracelet back when 0x40C6 is set and item 120 is missing) and four calls (0x0989202E/208A/20D1/2118)
  that givemon Kyurem 699 / Giratina 540 / Xerneas 769 / Yveltal 770 only when callasm 0x08C60571 (->
  0x09F037C9: caught in the Pokédex, per GetSetPokedexFlag mode 1, and not owned) says so. So 0x4311 = "been to
  Littleroot", and the script is a lost-legendary safety net, not a choice. No other script gives those four.
  Row removed (43 rows); the legendaries are in Legends.
- Every other Side flag: set by exactly the script the row names and never cleared (script index); only
  0x045D is cleared anywhere. (No pre-League save exists on this PC to check code-set flags directly.)
- Burning Soul portrait: Flareon -> species 157 Typhlosion; trans_17 line 76, the Crimson Apostle: the last one to
  pass the trials and awaken the Burning Soul was a trainer with a Typhlosion (火暴兽). The trial trainers
  1155-1157 use neither.
- Tested (test_questlog_snivy.lua, STATE start/league/done): Snivy To do / To do / Done, count 19/43, 19/43,
  20/43; Burning Soul panel shows Typhlosion; test_questlog_panel.lua passes on the rebuilt ROM.

## QUEST LOG: BADGES CHAPTER — 2026-09-25
- Request: a collection of Sinnoh badges (the Trainer Card shows Hoenn's only). The user chose a new tile on the
  Quest Log grid over touching the Trainer Card or the Start menu (which cannot take a 10th entry).
- Chapter 8 "Badges" (NPAGES 7 -> 8; the grid is 3x3, card 7 is row 3 column 2; V+0xC8.. counts now fill C8-CF,
  still clear of the pulse counter at V+0xD0). It is a second type-3 chapter: its rows (sidecontent.BADGES,
  {flag, name, "City: text"}) are appended to the Side Content table and to type 3's panel table, and its page
  record's `first` byte = len(SIDE). row_status (rs_side), ext_entry and pane_entry now add the chapter's first
  row for every type (Legends / Key Items / Side Content have first 0, so they read exactly as before; the
  Journal's pane lookup already did this). Every other reader of `first` (the opening chapter scan, page_sel,
  the detail page) only uses it for Journal chapters (type 0) - checked.
- Flags: Hoenn FLAG_BADGE01_GET.. 0x867-0x86E (0x866 is clear, 0x86F is FLAG_VISITED_LITTLEROOT); Sinnoh the
  hack's gym flags 0x42CD-0x42D4 (steps.py). Portraits: trainer pics 40-47 (Roxanne..Juan) and 178-185
  (Roark..Volkner) from trainers.json. Grid icon: a gold medal on a red ribbon, accent 14.
- test_questlog.lua finds the screen by its task function: now 0x08FEAA59 (was ..A5D); the default is updated.
- Tested: test_questlog_badges.lua (4 badge flags cleared: grid card 12/16, list, panels, detail), the 94
  Journal cases (check_questlog.py: 94 of 94 match), the panel test, the Snivy test.
- 2026-09-25, later: the user wanted the DS-style badge case (a picture of Platinum's), not a list. The Badges
  card now opens mode 4 (case_open/case_draw/case_show/case_frame/case_text/case_input in questlog.s); the
  list for chapter 8 still exists (grid counts come from it) but L/R in the lists stop at Side Content
  (#NLISTLAST = NPAGES - 2) and the header shows no arrow there, so the case is the only way in.
  - Each badge is its own 4x4-tile window (AddWindow 0x08003381 on opening, RemoveWindow 0x08003575 on B), x
    2 + 7c, y 4 + 6r tiles, BG palette 1 + slot (1-8: unused by the Quest Log), baseBlock 725 + 16 * slot
    (after the portrait's 661..724). Its 512-byte tile buffer (gWindows 0x02020004 + 12 * id + 8) gets the art
    or the silhouette; LoadPalette its 16 colours. Window 1 (panel, frame, text) is shown first, then the
    badge windows, then the footer - they share BG0's tilemap and window 1 reaches under the footer; the first
    build lost the footer after every cursor move until case_show re-put it.
  - A transparent pixel would show the backdrop (cream), not the panel, so every badge palette carries the
    panel colour at 12 and the art fills its 32x32 with it. Palette: 1-11 art, 12 panel, 13/14 silhouette fill
    and outline, 15 the sparkle.
  - Art (badgecase.py): Hoenn = the Trainer Card's badges, LZ77 0x0857BCC0 (a 16x2-tile sheet, badge b =
    columns 2b..2b+1), palette 0x0856F4EC (checked against the card), EPX-doubled to 32x32. Sinnoh =
    badges/sinnoh.png, cut from the user's picture of Platinum's case by badges/extract_sinnoh.py (flood fill of
    the grey panel stops at each badge's rim; scaled to fit 30x30), median-cut to 11 colours.
  - Data: CASE table at 0x09FB0000 (the free window NOTES listed): 16 x 32 bytes {flag, art, silhouette,
    palette, name, "Leader, City", "City Gym"} then the graphics and strings; widths checked at build time.
  - V bytes: 0xD4 region, 0xD5 cursor, 0xD8-0xDF window ids (clear of 0xC8-0xCF counts and 0xD0 pulse).
  - Tested (test_questlog_badges.lua, four badges cleared): grid card 12/16; case Hoenn 7/8 with the Rain Badge
    a silhouette ("Rain Badge  Sootopolis City Gym", dim); frame moves; R -> Sinnoh 5/8 (Mine, Icicle, Beacon
    silhouettes); B -> grid. Regressions: 94/94 Journal cases, panel test.
- 2026-09-25, final: Sinnoh only, at the user's request (the Trainer Card has Hoenn's). BADGES is the eight Sinnoh
  rows (the grid card counts /8), the case table 8 entries, no region byte (case_entry = CASE + 32 * slot), no
  L/R, header "Sinnoh Badges" + earned/8, footer "B: Back"; Hoenn art, pictures and the EPX doubling removed.
  Tested again: grid 5/8 with Mine/Icicle/Beacon cleared, frame and text on earned and unearned badges, B back;
  94/94 Journal cases.

## ITEMS POCKET 100 -> 200 SLOTS — 2026-09-28
- Asked for: raise the Bag's 100 unique-item limit. `patches/bagslots/`, applied last.
- How the hack stores the Bag: 0x08FD7EA4 (through SetBagItemsPointers' trampoline word 0x080D65F4; helper
  0x08FD7E88) gives each pocket its size and packs them back to back from EWRAM 0x0203D030 - Items 100
  (0x0203D030), Key Items 50 (0x0203D1C0), Poke Balls 32 (0x0203D288), TMs 130 (0x0203D308), Berries 50
  (0x0203D510), to 0x0203D5D8. (A pocket no bigger than its vanilla count would stay in SaveBlock1; none is.) An older
  copy of the routine at 0x08FD5F88 (Items 100, Key 60, Balls 32, TMs 108, Berries 80, from 0x0203D094) has no
  caller.
- The save's overflow stream: the hack's HandleWriteSector (trampoline word 0x081527A4 -> 0x092582FC) fills every
  sector to 0xFF0 - the vanilla data, then bytes taken in order from EWRAM 0x0203CF64 (a running counter at
  0x02024064, byte-stored, reset at sector id 0); its CopySaveSlotData (word 0x08152E14 -> 0x09258444) reads them
  back in sector-id order; HandleReplaceSector is patched mid-body at 0x08152B00 -> 0x094A330A (filler 0x094A38B4)
  for link-style saves. Sizes 0xF2C / 0xF80 x3 / 0xF08 / 0xF80 x8 / 0x7D0 leave 3,740 bytes: 0x0203CF64-0x0203DE00,
  which is where vanilla EWRAM ends (sRayScene 0x0203CF60 is its last variable). Checked on the user's save: the
  stream rebuilt from the .sav equals RAM byte for byte.
- Who uses the stream: the pockets; 100-byte stored Pokemon at 0x0203D5E0, 0x0203D644 (0x09F01054, 0x094A2A02) and
  0x0203D800 (0x08FD704E); flags at 0x0203D900 / 0x0203D904 (0x09510ACA); hypertrain's scratch byte 0x0203D600.
  0x0203D908-0x0203DE00: no aligned literal and no script-style unaligned pointer (the five unaligned hits are
  instruction bytes or graphics; the aligned 0x08D26000 -> 0x0203DD78 is compressed data). The hack's extended flags
  (0x09F00CEC) map into SaveBlock1/2, and vars are vanilla (SaveBlock1). So the tail is free.
- Not free: the vanilla bag slots in SaveBlock1 (+0x560..0x848) - the hack keeps other data there (167 non-zero
  bytes in the user's save), even though no pocket points at them any more.
- Why not just 100 -> 200: the pockets are packed, so a bigger Items pocket would move the other four on every
  existing save; and the stored Pokemon start 8 bytes after the pockets.
- The patch (184 bytes at 0x08FF6000; the run 0x08FF5C35..0x08FFD5A0 has three data words pointing at 0x08FF6673+,
  so it stays below 0x08FF6600):
  * set_ptrs (word 0x080D65F4): the hack's layout, then gBagPockets[0] = 0x0203DAE0, capacity 200 - 800 bytes that end
    exactly at the stream's end (sector 13's spare bytes).
  * load_slot (word 0x08152E14): the hack's loader; then, if it returned 1 and MARKER (0x0203DADC) is not "BAG2"
    (0x32474142), copy the 100 old slot words (id + key-encrypted quantity, as saved) from 0x0203D030, zero slots
    100-199, set MARKER. The old copy is left in place: an older build would still show it.
  * clear_bag (8-byte trampoline at ClearBag 0x080D7094; its only caller is NewGameInitData): the game's loop
    (ClearItemSlots over the five pockets), then zero the old area and set MARKER. Without it, a New Game started
    after the title screen had loaded (and migrated) an old save would carry that save's old area into its own first
    save, and the next load would copy it over the new game's items.
  * The Bag's list buffers (the hack's AllocateBagItemListBuffers, 0x08FD7F38): Alloc(0x9C << 3) -> Alloc(0xCA << 3)
    = 202 ListMenuItems, and the names literal 0x08FD7F60 0xE22 -> 0x1300 (202 x 24; LoadBagItemListBuffers' stride
    is 24). They were sized for about 150 rows.
- Limits: gBagPockets' capacity and the Bag's numItemStacks (gBagMenu+0x829, Cancel included) are u8 - 254 is the
  ceiling. Every other reader takes the capacity from gBagPockets: the vanilla bag functions (u8 loop counters, fine
  under 255), AddBagItem (allocates capacity x 4), bagsort (sorts the first N used slots), quickball (the Balls
  entry), the hack's quantity clamp 0x09000150 and its free-slot count 0x09F034EC. No code knows 0x0203D030 but the
  layout routine.
- Frontier/link saves (TrySavingData(SAVE_LINK): SaveGameFrontier, Save*Challenge, SavePyramidChallenge, link
  contests, LinkTest) write sectors 0-4 only, so they do not refresh sector 13 - as for the Poke Balls, TMs and
  Berries pockets already (stream past 0x0203D260). In single player these come only mid-challenge, after the
  lobby's normal save, and the Bag cannot change during a challenge. The hack's own TrySavingData call (0x09F06B48)
  is a Hall of Fame save (full).
- Tested (mGBA, copies of the user's save, both on the full chain and on the working ROM): test_bagslots.lua -
  migration (63 items, 100-199 empty, MARKER), 200 distinct items in the field Bag scrolled to Cancel (row 200; list
  heap blocks 1616 / 4864 bytes; the 200th name right), three sorts keep the same items, additem into slot 200 (1),
  a 201st item refused with the pocket unchanged (0), stacking (1), a wild battle's Bag scrolled to Cancel and the
  battle won, a save from the Start menu, and a pattern in the margin 0x0203D908..MARKER untouched;
  test_bagslots_reload.lua boots that save - the 200 slots exactly as saved, no second migration, the margin pattern
  back through the save; test_bagslots_newgame.lua - New Game over an old save: the pocket and old area empty,
  MARKER set, right after NewGameInitData. The patched ROM differs from its input only at the three hook words, the
  ClearBag trampoline, the two buffer sizes and the code.
- Test harness notes: emu:reset() from a frame callback stalls the script (hence the separate reload script). A
  wild battle started from a script sits on "Wild X appeared!" until a key; B moves text on and picks nothing at
  the action menu (HandleInputChooseAction 0x08057589 is vanilla here). NewGameInitData's effects show a few frames
  after gMain.callback2 reads CB2_NewGame.
- Working ROM: installed on top of the previous working ROM (archived "(before bagslots)", with the .sav). That ROM
  had been rebuilt 2026-09-24 from the v1.4 chain + questlog/leaguefly/leaguetext, so it lacks qolversion..expshare
  (checked: no 0x0203D600 literal, 16 regions differ from the v1.5 ROM). The full chain builds from the repo except
  for patches/questlog/badges/sinnoh.png, which .gitignore's *.png had kept out (exception added); with it, rebuild
  the chain (HANDOFF order) and add bagslots last.
- Follow-up checks (same day), asked "other players' saves?", "sure it is unused?", "does the save screen's count
  follow?":
  * Other saves: make_test_saves.py builds two from any old-layout save - full_junk.sav (a full 100-item pocket and
    random bytes over the whole tail 0x0203D908..0x0203DE00, as a cartridge whose EWRAM was never cleared might
    have) and already.sav (MARKER set, 150 items in the new area, a different stale old area). The hack stores
    checksum 0x0001 in every sector and no longer checks them, so edited sectors load. test_bagslots_saves.lua: all
    100 copied in order and the junk in 100-199 cleared; the upgraded save left alone (no second migration).
  * Pointers built at run time near the tail: 0x0203D900 holds one pointer (a 0x1004-byte heap block allocated at
    0x09510012, freed at 0x09510FE0; every other use reads through it) and 0x0203D904 one byte (a sprite id,
    CreateSprite at 0x09510AC4, then gSprites[id]). The module at 0x09510000 reaches both through a GOT-like
    literal table at 0x0951267C (after its tile data), read by pointer - which is why no direct load showed up.
    The fusion code (0x09F00F62) keeps a whole Pokemon (memcpy of 100 bytes) in 0x0203D5E0 (Solgaleo, for Dusk
    Mane Necrozma) or 0x0203D644 (Lunala); 0x08FD704E the same at 0x0203D800 (Reshiram/Zekrom for Kyurem). No
    base in the stream is indexed past its own block, so nothing reaches 0x0203D908.
  * The save dialog's "There's N space left for items." is the hack's InitSave (0x0809FF28 -> 0x09F0386A ->
    0x09F034EC: capacity - used of gBagPockets[0], into gStringVar1): 37 on the old ROM with the user's 63 items,
    137 on the new one; three digits fit.
- FOUND ON THE WAY - HYPER TRAINING CORRUPTS A STORED FUSION PARTNER: hypertrain's "free" scratch byte 0x0203D600
  is offset 0x20 of the fusion slot 0x0203D5E0 - the low byte of the stored Pokemon's species. ht_getmondata
  rewrites its bits 0-5 on every IV read by the EV-IV Display or the IV judges, so a Solgaleo fused into Necrozma
  (species 844 = 0x34C) can come back as any species 832-895 (Bruxish..Typhlosion) when split. The user's save
  has that Solgaleo (Lv85) - intact, as the Mac's working ROM lacks hypertrain; v1.5 and the full chain have it.
  The scratch-RAM test that cleared 0x0203D600 ran with that slot empty. Fix: move SCRATCH out of the save stream
  to RAM measured free (and re-measure with a fusion stored), then rebuild the chain from hypertrain on.

## JOURNAL: "A FEATHER FOR DREAMS" REMOVED — 2026-09-28
- Asked for ("wrong flags"). The step was ANY(0x412F), "Dawn, on Route 210, carries a feather...". Dawn's script
  (35/16, 0x0980977C) sets 0x4118 and 0x412F around a battle (trainer 864), checks 0x412E - which no script sets -
  and gives item 647 (Lunar Wing); 0x4118 is also the flag of a Steven's Island trainer (0x0988F037, trainer 1161).
  So 0x412F never meant "she gave you the feather". On the user's save 0x4117 = 1, 0x412F = 0: the row had not been
  ticked - rows behind the current objective that are "any order" and not done show the grey Side tag, which reads
  like done (their earlier report).
- Not changed, for the user to decide: "Wake the sleeper" (0x412D) says "Bring the Lunar Wing...", but the woman's
  script (0x0980E243) wakes her when 0x405F is set - the hide flag of Cresselia's objects (Mt. Pyre 24/21 and 24/22,
  Crescent Isle 35/30; set by the removeobject after the battle, cleared again if it flees). The Lunar Wing is not
  checked.
- Changed: steps.py (the step, its title, the comment), portraits.py (row 78 and the numbering after it),
  make_tests.py re-run (104 cases), docs/journal.html rebuilt (94 objectives).
- Tested: on the full chain (placeholder badge art) test_journal on the Journal-only stage and test_questlog on the
  end: 104/104 each. On the working ROM's own lineage (below): 93/93 each, and the Lost Artifacts list shows
  "A sleeping woman" (Done) then "Wake the sleeper" (Active), 18 rows.
- The working ROM's lineage: v1.4 archive + the shinybox 2-byte edit + journal, berrynum, speciesnames, questlog,
  leaguefly, leaguetext from commit 6ecc413's sources reproduces the pre-bagslots working ROM byte for byte
  (b450a795...). The same edit there, then bagslots on top, is the installed ROM (9f45b76c...); it differs from the
  one before only in the Journal blob (0x08FE5400..), the Journal item's description pointer, the Quest Log blob and
  its panel data (0x09FA0000..).

## HYPER TRAINING: SCRATCH BYTE MOVED OUT OF THE SAVE — 2026-09-28
- The bug (found while checking bagslots, above): SCRATCH 0x0203D600 = fusion slot 0x0203D5E0 + 0x20, the stored
  Pokemon's species, inside the saved overflow stream. Shown on the user's save with test_hypertrain.lua: the stored
  Solgaleo (844) became Decidueye (894) after the EV-IV Display and one IV judge.
- Fix: lit_scratch = 0x0203F13C - past the stream (0x0203DE00), inside 0x0203F100..0x0203F13F that
  test_scratch_ram.lua measured free, no ROM literal into 0x0203F100..0x0203F1ED (the hack's block at 0x0203F000
  ends by 0x0203F0BE as far as its literals go; the Lua tests borrow 0x0203F100.. for injected scripts, short of it).
- test_hypertrain.lua now registers the EV-IV Display (item 650) to UP itself (the user's save had the Sinnoh Map on
  DOWN, so the old navigation never opened it) and checks both fusion slots are unchanged. Old build: 844 -> 894,
  CHANGED. Fixed build: 844, UNCHANGED; the EV-IV screen (31s, Hidden Power "DGN" = the real type) and both judge
  screens pixel-identical to the old build's.
- Saves that already went through the bug keep whatever species the byte holds: not repairable in general (the
  original species is gone). A player with a fused Necrozma who used the EV-IV screen or a judge on v1.5 should
  check the Pokemon they get back.

## WORDING RULE: NO BUG IS PINNED ON THE EARLIER COMMUNITY TRANSLATION — 2026-09-29
- The earlier community translation's team (credited in the README) says the bugs people meet are not from them.
  The user does not want trouble: docs, site, changelog, commit messages and release notes must not say a bug came
  from their version. Removed / reworded: the FAQ's row on a Volo / Arceus cutscene freeze (gone); the new-game crash and the garbled Rustboro graphics are described as what they were, our own
  translation passes (translation/patch_conv, patch_story, patch_remaining) overwriting movement scripts and LZ
  graphics; "older versions" lines on the site now name the hack's own earlier releases. The site credits dropped
  Li Yun, as the README already had at his request. README and the site's home page carry a "may still contain
  glitches or bugs - keep a .sav backup" notice. The release notes of v1.1 and v1.2 say "our translation pass".
- Old commit messages (315fead movefix, 8230d7a gfxfix: "the text passes overwrote") mean our passes; history is not
  rewritten (that needs a force push of both repos).

## ITEMS LOOKED GONE AFTER SWITCHING TO v1.6 (SAVE STATES) — 2026-09-29
- Reported: after switching to v1.6 all the items were gone; after restarting the ROM they came back.
- Cause: bagslots migrated only in load_slot, i.e. when the game boots and reads the battery save. An emulator save
  state from an older version (loaded by hand, or restored by the emulator on launch) brings back the old memory -
  gBagPockets[0] at 0x0203D030 x100, no MARKER - and skips that load. The Bag works from the old slots until the
  game re-runs SetSaveBlocksPointers -> SetBagItemsPointers, which MoveSaveBlocks_ResetHeap does after battles and on
  map loads (callers 0x08036762, 0x080867CE); set_ptrs then pointed Items at the new area, still empty. A restart
  loaded the save and migrated. Reproduced on the v1.6 release ROM (test_bagslots_state.lua: the old layout put back
  in memory, then a warp): 63 items -> 0 after the warp.
- Fix: the copy is its own routine, migrate (unless MARKER: old 100 slots -> new, 100 zeroed, MARKER set), called
  by load_slot after the loader and by set_ptrs after every pocket setup. At boot set_ptrs runs before the load and
  may "migrate" whatever is in memory, but the loader then rewrites the stream (MARKER and both areas) from the save,
  so load_slot's check is what counts; with no save, New Game's clear_bag empties everything and sets MARKER.
  Nothing in the save format changes. 198 bytes at 0x08FF6000..0x08FF60C8 (load_slot 0x08FF601D, migrate
  0x08FF6037, clear_bag 0x08FF606D).
- Tested on the fixed full chain: test_bagslots_state 2/2 (63 items after the warp and after a battle, 200-slot
  pocket, MARKER set), test_bagslots 19/19, reload 4/4, newgame 5/5, saves full_junk 4/4 and already 4/4.
- For players on v1.6: restart the game after patching (a real restart, not a save state); a save made while the
  Bag looked empty still holds the items in the old slots, and the next real start moves them - but items picked up
  in that session went into the new pocket and are overwritten by that move.

## TM75: LOW SWEEP WITH BOUNCE'S DESCRIPTION — 2026-09-30
- Reported: TM75's name is Low Sweep but its description is Bounce's. The move is right: the TM table 0x09E0FE80
  (TM n = entry n-1, TM01 = item 378) gives TM75 (item 452) move 490 Low Sweep, and every reader uses that table -
  the Bag's name (0x08FD7BDC via 0x08FD7D3C), the party menu's can-learn / teach (0x081B6D10, 0x081B6D30), 0x08FF1C24.
  The item's description pointer (item + 20 = 0x08FC7A40) was 0x08583197, the same text as TM52 (item 429), which
  does teach Bounce (move 340).
- (2026-10-01: TM75 was the only text naming the wrong move, but the shared ones confused players and five other
  texts were wrong or had typos - see TM DESCRIPTIONS, ALL 128 READ.)
- All 128 TMs checked (move vs description): TM75 is the only mismatch; the other shared descriptions are moves with
  the same effect (Hyper Beam / Giga Impact, Solar Beam / Solar Blade, the draining moves, the high-crit moves, the
  switching moves).
- patches/itemdesc: new text at 0x08FF6400 (50 bytes), the game's own Low Sweep line from the summary's move
  descriptions (table 0x09D2AD00, indexed move - 1; Low Sweep 0x09D2CD1E) rewrapped for the Bag: "The user hits the /
  foe's legs, lowering / its Speed." (90 / 101 / 52 px; item-description lines run up to ~105 px, the summary's two
  lines are 120 / 126). Applied last. Screenshot on the fixed build: the TM pocket shows "No75 Low Sweep" with it.

## SKY PILLAR: ZINNIA AND RAYQUAZA, VERIFIED — 2026-09-30
- Asked: make sure the Sky Pillar / Zinnia scripting works perfectly.
- The pieces (all the hack's own): 24/79 (entrance) trigger (3,9) 0x098C04BE (needs 0x40C6, not 0x1C0: "make sure
  you have a free slot" yes/no; No = step back, Yes = VAR 0x400F 1) and trigger (10,2) 0x0981FA9C (without the 3rd
  Meteorite, item 690, and while 0x50 is clear: "doesn't have the meteorite fragment", step back). 24/85 (summit):
  trigger (12,11) 0x0982040B (VAR 0x4001 == 0; needs 0x40C6, not 0x1C0) -> Zinnia's scene 0x0981FB04 -> the
  Rayquaza object's script 0x08239722 -> battle 0x09824068 (setwildbattle 406 Lv50, callasm 0x08FFF201 - real code,
  special 0x13A, GetBattleOutcome): won (1) or player teleported (5) -> givemon 406 (party / PC / nothing if both are
  full - hence the entrance prompt) and VAR 0x4001 = 406; ran (4) -> "must face Rayquaza!" and the battle again;
  anything else (caught 7) -> on. Then 0x09820501 sets 0x1C0 and 0x098205D1: removeitem 690, giveitem 648 (Final
  Meteor), Mega Rayquaza, removeobject 2-5, setflag 0x50. Summit objects: Rayquaza (local 2), Zinnia (3, main 166),
  local 4, all hidden by 0x50; the map's ON_TRANSITION clears 0x50 while VAR 0x40CA >= 2 and 0x1C0 is clear.
- Static: every script byte in these ranges equals the original Chinese ROM (text was translated in place, pointers
  unchanged); all 21 movement scripts identical and valid; command table entries unchanged; text lines <= 215 px
  with a worst-case 7-letter name (box 216). An oddity from the original: showcoinsbox 1,21 before showmonpic,
  never hidden - off-screen, and the battle right after resets the windows; nothing visible in the tests.
- In mGBA on the user's save (0x1C0 cleared, the 3rd Meteorite in the Items pocket - it is not a Key Item),
  tests/skypillar: test_skypillar.lua MODE catch / ko / run: PASS each (Rayquaza +1 - into the PC with a full party
  -, item 690 -1, item 648 +1, 0x1C0 and 0x50 set, control back); MODE lose: blackout to 36/9 with 0x1C0 and 0x50
  clear, VAR 0x4001 0, 0x8C1 clear, items untouched - the event can be done again. test_entrance.lua: No / Yes / no
  second prompt / the door check. Screens reviewed: every message fits its box.
- Text: "emmited" -> "emitted" (patches/textfix, same length, in place). "Key Stones" / "Keystones" both appear
  (left; a longer word would need the text moved).

## HMS WITHOUT THE POKEMON — 2026-09-29 — `patches/hmfree/` (PR #2, @anibalribeiro)
- Asked for: use HMs without a party Pokemon that has the move. Decided: the HM item in the Bag plus the badge the
  game already asks for; Fly and Flash from every Pokemon's party menu; Rock Climb left as it is.
- How the hack gates field moves. Every obstacle script starts with a vanilla `goto` into hack script: Cut
  (0x082906BB -> 0x09864016), Rock Smash (0x082907A6), Strength (0x082908BA), Surf (0x08271EA0 -> 0x09864066),
  Waterfall (0x08290A49), Dive (0x08290B0F, 0x08290B5A), plus Rock Smash at 0x098A44D0 / 0x098B91CE and four Rock
  Climb scripts at 0x098C346C.. (map events, no badge check anywhere). Each does `setvar VAR_0x8004, move;
  callasm 0x08FF1BA1; compare VAR_0x8004, 6`. That routine looks the move up in the TM/HM list 0x09E0FE80
  (TM01-120 then HM01-08 = Cut, Fly, Surf, Strength, Flash, Rock Smash, Waterfall, Dive; items 498-505) and
  then in 0x08FD80B8, and returns the first non-egg party slot whose species is *compatible* (bit tables
  0x0806E0B0 / 0x081B2390) - so the hack already asks for "can learn", not "knows". The badge checks come first:
  Cut 0x867, Rock Smash 0x869, Strength 0x86A in the scripts; Surf 0x86B in the field code at 0x0809C7F2 (whose
  PartyHasMonWithSurf result, 0x0808BE00, the hack no longer branches on); Waterfall and Dive in the field code.
  Vanilla `checkpartymove` (0x0809B3DC, "knows the move") is still used by Headbutt, Whirlpool (TM36 here) and
  Secret Power; untouched.
- Obstacles: 8-byte trampoline over 0x08FF1BA0 (push {r4-r7,lr}; ldr r5; ldrh r5; ldr r7 - 4-aligned) to fm_entry,
  which saves the move, calls fm_orig (those four instructions replayed, then `bx` to 0x08FF1BA9), and only on 6
  looks the move up in its own 8-entry HM table: HM in the Bag (CheckBagHasItem 0x080D6724) -> VAR_0x8004 = the
  first party slot with a species that is not an egg.
- Party menu: pm_hook is the new head of the builder chain (0x081B351C: pm_hook -> partyedit 0x08F53901 ->
  relearner in the PR; pm_hook -> relearner here). Fly = action 24 (0x13 + FIELD_MOVE_FLY 5), Flash = 20
  (0x13 + 1), appended when numActions < 7, not already listed (a Pokemon that knows the move has it from the
  game), badge set and HM owned; Flash also needs gMapHeader.cave (0x02037318 + 0x15) == 1 and FLAG_SYS_USE_FLASH
  (0x888) clear. They go before Edit and Moves, so in the PR a Pokemon with two field moves and Switch can lose
  Edit (here there is no Edit). Choosing one is the game's own field-move
  path (badge message, "can't use that here", the Fly map).
- 344 bytes of code + the 8 moves at 0x08F54500..0x08F54668. The ROM differs from its input only there, at
  the trampoline and at the builder word.
- Tested (`test_hmfree.lua`, the party's Chimchar turned into a Magikarp, which can learn no HM): unit - each of
  the eight moves answers 6 without its HM and 0 with it; on the tmshop build (control) 6 both ways; Rock Climb 6;
  a Chimchar with Cut compatibility still gets 0 without HM01. surf - Petalburg (19,7): the prompt, "used Surf",
  on the pond (19,6), avatar surfing bit; without HM03 nothing. cut - Route 102 (10,7): "Chimchar used Cut"
  (nickname), Magikarp in the popup, tree flag 0x12 set; without HM01 the plain "can be Cut down!" line. party -
  Petalburg: {Summary, Item, Fly, Edit, Moves, Cancel}, Fly opens "Fly to where?", A lands at (19,16); without
  HM02 no Fly; with Fly known it is listed once, in the game's own place. flash - Granite Cave 34/71 (cave 1):
  Flash listed, chosen, flag 0x888 set and the light circle drawn; without HM05 not listed; not listed outdoors.
  partyedit's entry/e2e/scratch tests unchanged on the final ROM.
- Not tested: an egg in the first slot (first_mon skips eggs by GetMonData isEgg), Waterfall, Dive, Strength and
  Rock Smash end to end (the unit test covers their routine answer; their scripts use it the same way as Cut/Surf).
- Harness gotchas: gBagPockets (0x02039DD8) is in vanilla pocket order (Items, Balls, TMs, Berries, Key), not the
  hack's EWRAM order; a control run with the same screenshot names overwrites the real run's pictures.
- Taken into this repo on its own (2026-09-30): the user wanted only this of PR #2's three features, not the party
  editor or the TM shop. The patcher asserted that the builder chain started at partyedit's hook (0x08F53901) and
  chained to it; it now reads the trampoline's current word and chains to it, accepting the relearner's hook
  (0x08FD9B01, this build) or partyedit's. Code, addresses and FREE 0x08F54500 unchanged (tmshop's list would sit at
  0x08F54400..0x08F544E6, still free here). Applied last, after textfix.
- 2026-09-30, later: Fly taken out of the party menu at the user's request ("every Pokemon has FLY"; the ride pager
  and the map fly you). pm_hook now only offers Flash; the four Fly lines and lit_hm02 / lit_badge6 went, and a
  `mov r8, r8` before the pool keeps it word-aligned (10 bytes fewer left keystone padding with 00 bf, which the
  patcher rejects). The ROM changed only inside the hmfree block and its trampoline word 0x08FF1BA4 (fm_entry
  moved). Re-tested: party with HM02 + badge 6 -> {Summary, Item, Moves, Cancel}; a Pokemon that knows Fly -> Fly
  once (the game's own) and it flies; Flash in Granite Cave offered and lights it; unit, surf, cut unchanged.
- test_hmfree.lua made save-independent: the party becomes one Magikarp (slots 2-6 emptied - on the user's save the
  other five could learn Surf / Cut themselves and the NOHM controls "passed" through them), the Start menu cursor
  is put on POKEMON from the menu's own list, and Fly / Flash are picked by their row in the action list (the user's
  save has Switch and Fly rows the fixed DOWNs did not expect).
- Results on this build with the user's save: unit - every HM move 6 without its HM and 0 with it, Rock Climb 6,
  Chimchar control 0; surf / cut with the HM work, without it nothing; party - {0,3,24,33,2} (Summary, Item, Fly,
  Moves, Cancel: the relearner's Moves still follows), Fly opens the map and lands at (19,16), without HM02 no Fly;
  flash - Granite Cave 34/71: Flash listed and chosen, flag 0x888 set; without HM05 not listed.

## INSTANT TEXT — 2026-09-30 — `patches/instanttext/`
- Asked for: an instant text speed, chosen in the Option menu. Decided (the user's pick of three mock-ups): a 4th
  word on the Text Speed row, all four visible - Slow / Mid / Fast / Instant, the selected one red.
- optionsTextSpeed is the low 3 bits of SaveBlock2+0x14; Instant = 3, so the save format does not change. Readers,
  found by scanning for `ldrb [.., #0x14]; lsls #29; lsrs #29`, the BLs to GetPlayerTextSpeed / Delay and the
  literal pools of their tables (all vanilla in this ROM):
  - GetPlayerTextSpeedDelay 0x08197990: reset anything > Fast to Mid (`cmp r0, #2` at 0x0819799C -> #3) and
    read sTextSpeedFrameDelays {8, 4, 1} (literal 0x081979C0) - now {8, 4, 1, 1}. The byte after the vanilla
    table is 0: a printer started at speed 0 is drawn whole inside AddTextPrinter, waits and all, so Instant
    must not return 0.
  - RenderText's scroll 0x08005CF6 (GetPlayerTextSpeed -> {1, 2, 4} at 0x082E9D10, literal 0x08005D1C) and the
    braille font's 0x081BA5D4 (the option -> {1, 2, 4} at 0x08616124, literal 0x081BA5FC). Both tables are
    followed by a 0: a "\l" scroll at Instant would move 0 px a frame forever. Both literals -> {1, 2, 4, 8}.
  - Berry Crush's SetNamesAndTextSpeed 0x08020FC4 switches 0/1/2 -> 8/4/1 and leaves other values unset: `beq`
    at 0x08021036 -> `bge`. Link-only, not tested.
  - InitOptionMenu 0x080BA792 and Task_OptionMenuSave copy it as is. The recorded-battle copy (0x08185CBA, bits 1-3
    of the record) indexes sRecordedBattleTextSpeeds {8, 4, 1, 0} at 0x085CD668, which has a 4th entry already;
    the other `ldrb [.., #0x14]` readers near gSaveBlock2Ptr are the window frame (`lsrs #3`).
- Printing: RunTextPrinters 0x08004778 -> 8-byte trampoline -> run_printers (0x08FF6901): the game's loop over the
  32 printers (RenderFont 0x08004818: 0 PRINT, 1 FINISH, 3 UPDATE; CopyWindowToVram 0x08003659 on PRINT; callback
  at +0x10 on PRINT and UPDATE; active +0x1B, textSpeed +0x1D), plus: when GetPlayerTextSpeed says 3 (it says Mid
  while gTextFlags.forceMidTextSpeed is set) and the printer's textSpeed is 0, it keeps calling RenderFont while
  it returns PRINT (max 1024 glyphs a frame). Any wait - {PAUSE}, the button arrow, "\l", "\p", the end - returns
  UPDATE or FINISH and ends the burst. The window is copied to VRAM once after the burst, not per glyph (one
  RequestDma3Copy each would flood the DMA queue). Printers started with an explicit slower speed keep it.
- Option menu: TextSpeed_ProcessInput 0x080BABDC wraps at 3 (`cmp r3, #1` at 0x080BABEE -> #2; `movs r3, #2` at
  0x080BAC24 -> #3). TextSpeed_DrawChoices 0x080BAC38 -> trampoline -> draw_speed (0x08FF69B3): DrawOptionMenuChoice
  0x080BAB68 for each word at x 76 / 106 / 130 / 162 (the font's widths 22 / 16 / 24 / 42, 8 px apart, from just
  after the "Text Speed" label, which ends at 65, to 204; the window is 208 wide). Four full words do not fit the
  other rows' column (104..198, 94 px for 104 px of text). "Instant" is new text with Slow's colour prefix
  FC 01 06 FC 03 07; DrawOptionMenuChoice copies at most 15 bytes and it is 13.
- ROM: code + data 0x08FF6900..0x08FF6A32 (in the unreferenced 0xFF run 0x08FF6600..0x08FFD5A0, between the words
  that happen to read 0x08FF67FF and 0x08FF7703); the two trampolines; five single bytes; three literals.
- Tested (`test_instanttext.lua`, on the user's save): menu - from Fast, RIGHT Instant, RIGHT wraps to Slow, LEFT
  Instant, LEFT Fast, Mid, Slow, LEFT wraps to Instant; B saves 3; reopened it shows Instant. text - a scripted
  message of two lines, a "\l" scroll and a "\p" page: frames until the first page waits for A - Slow 502, Mid 250,
  Fast 61 on both the patched and the unpatched ROM, Instant 4 (the box itself takes 2 at every speed); the
  scroll and the second page 6 and 2 frames at Instant. battle - wild Magikarp, B through the intro, Run: the
  action menu, "What will Blaziken do?", "Got away safely!", back on the field (Fast 884 frames, Instant 824 -
  the battle's own fixed pauses dominate).
- Seen while testing: a page of ~70 glyphs takes a little more than one frame to draw, so a probe at VBlank can
  catch the printer mid-burst (37, then 69 characters). The screen still shows the page at once - the window is
  copied after the burst and the DMA lands at the next VBlank, which is also why a screenshot taken on the frame the
  printer starts waiting still shows the old contents.
- Not tested in the game: braille text (the Sealed Chamber) and Berry Crush (link only); both are a table / a
  branch that now covers the 4th value.

## FASTER SURFING — 2026-09-30 — `patches/fastsurf/`
- Asked for: faster surfing, "like holding B". Decided: B while surfing = PlayerWalkFaster 0x0808B768 (4 px a frame,
  4 frames a tile: the Mach Bike's top speed) instead of the game's PlayerWalkFast 0x0808B738 (8 frames a tile, the
  running speed). Same rule as auto-run's run decision: B held XOR Auto Run (optionsButtonMode 0x13 of SaveBlock2,
  0 / 4), so with Auto Run on fast is the default and B gives the old speed. No running-shoes or map check (the
  game's surf speed never had one).
- Site: PlayerNotOnBikeMoving 0x0808AF00. After the collision checks (ledge, getting off onto land, ...), `ldrb
  gPlayerAvatar.flags; tst #8 (SURFING)` and the branch at 0x0808AF5A `adds r0, r5, #0; bl PlayerWalkFast; b
  0x0808AFB6`. 8 bytes at a 2-aligned address, too short for a trampoline: it becomes `ldr r0, [pc, #0x18]; bx r0`
  (4 bytes; the other 4 are dead), and the literal goes into 0x0808AF74 - the first of the 0x38 bytes of nops auto-run
  left dead after its own `ldr r0, =run_hook; bx r0` at 0x0808AF70 (its pool word is at 0x0808AFAC). surf_hook
  (0x08FF6A80..0x08FF6AB4) is entered like run_hook - r4 = &gPlayerAvatar, r5 = direction, r6 = heldKeys - and
  leaves through the function's epilogue 0x0808AFB6 (pop {r4-r6}; pop {r0}; bx r0).
- Animations: both surfing sprites (gfx 2 Brendan, 92 May: sPlayerAvatarGfxIds 0x084974F8 [state 3]) use
  sAnimTable_Surfing 0x08509388, 24 entries; WalkFaster plays GO_FASTER (12-15), which are there. The surf blob
  follows the player's sprite, so it keeps up; checked on screen.
- Tested (`test_fastsurf.lua`, Route 109 (3,48) eastwards, a warp onto water starts the player surfing; 64 frames
  of RIGHT): Auto Run off 8 tiles, off + B 16, on 16, on + B 8; the unpatched ROM 8 with or without B. land: B +
  RIGHT across 24 tiles at 4 frames each to the sandbar at x 27 - the game's own jump off, on foot, control back.
- GOTCHA in the test: a PokeNav Match Call rolls every 10 steps (UpdateMatchCallStepCounter 0x08195F40,
  sMatchCallState 0x0203CD80, counter at +6) and twice stopped a run at x 13, waiting for A while the test held
  B. The test now zeroes the counter every 4 frames.
- ROM: 0x0808AF5A (4 bytes), 0x0808AF74 (the literal), 0x08FF6A80..0x08FF6AB3. Nothing else.

## DEXNAV: UNSEEN SPECIES ARE SHADOWS — 2026-09-30 — `patches/dexnavseen/`
- Asked for: on the DexNav, a Pokemon not seen before is a shadow and cannot be registered until seen once.
  Done: black silhouette icon, name "?????", header hint "Not seen yet" (instead of "A: Register"), A plays
  SE_FAILURE (32) and the screen stays open. Level range, habitat and paging unchanged.
- Seen = GetSetPokedexFlag(SpeciesToNationalPokedexNum(species), 0). GetSetPokedexFlag 0x080C0664 is a trampoline
  to the hack's 0x09257950: flag n is bit n&7 (mask table 0x0832A328) of byte n>>3, seen at SaveBlock1+0x560, caught
  at +0x5D8 (0x78 bytes each, 960 dex numbers); SpeciesToNationalPokedexNum 0x0806D4A4 reads the hack's table at
  0x08F50370. Confirmed in the game: a scripted wild Ralts battle set dex 280's bit, and the DexNav showed it next
  time. A species with dex number 0 is treated as seen.
- The DexNav code is in the v1.4 base ROM, so this is four `bl`s into it (each asserted: bytes around it and its
  current target), code at 0x08FF6B00..0x08FF6C46:
  - 0x08FDA610 draw_page's `bl callr4` (r4 = CreateMonIcon) -> icon_hook: copies the three stack arguments below
    its own frame, calls CreateMonIcon, and for an unseen species LoadSpritePalette (0x08008744) of an all-black
    palette (colour 0 transparent) under tag 0x5E64 and writes the slot into gSprites[id].oam's palette bits (byte
    +5, bits 4-7). draw_page frees all sprite palettes and loads the six mon-icon ones on every page, so the
    shadow palette is reloaded with them (the 7th slot).
  - 0x08FDA628 draw_page's `bl print` for the name -> name_hook: r6 is draw_page's scratch (0x02021DC4, [0] =
    the row's species); "?????" replaces the name pointer, then print (0x08FDA6AA).
  - 0x08FDE7F8 draw_hint's `ldr r2, =state; ldrb r3, [r2, #9]` -> hint_pick (r4 = task data at that point):
    cur_index (0x08FDE738) + find (0x08FDA790) for the cursor row; unseen and not the species being hunted ->
    r5 = "Not seen yet", r3 = 0, so draw_hint jumps straight to drawing; else the two instructions replayed.
  - 0x08FDE708 dt_arm's `bl arm_search` -> arm_hook: seen -> arm_search (0x08FDE89A) and on to the leaving fade;
    unseen -> buzz, drop its own frame and jump to dn_task's exit 0x08FDE734 (add sp, #4; pop {r4-r6, pc}), so no
    fade and no registration. Unregistering (A on the hunted species) is decided before this call, unchanged.
- On a map with no Pokemon (find finds no row) hint_pick sets an empty hint: draw_hint used to put "A: Register"
  over "No wild Pokemon on this map" (seen in Mauville once dexnavscan removed its fake rows).
- Tested (`test_dexnavseen.lua`, Route 102 on the user's save, Ralts and Sentret made unseen, Lotad seen): shadows
  and "?????" on rows 1 and 3, "Not seen yet" on them and "A: Register" on Lotad, A on both unseen rows leaves the
  hunt flags untouched and the DexNav open; B out; a wild Ralts (Run) sets its seen bit; the DexNav then shows
  Ralts in colour and A registers it (flags 09, species 392) and returns to the field.

## DEXNAV LISTS THE GAME'S OWN TABLE — 2026-09-30 — `patches/dexnavscan/`
- Reported: the DexNav in Lilycove. Found: the DexNav's find_header (0x08FDA760) matched the current map by
  group/number in two tables - the hack's encounter table 0x08E17D50 and 0x08553894, which the DexNav notes of
  2026-09-18 took for "a seven-city extra table". It is gBattlePyramidWildMonHeaders: StandardWildEncounter
  (0x080B5352) and SweetScentWildEncounter read it only when gMapHeader.mapLayoutId is 0x169 (the Pyramid floor),
  indexed by frontier.curChallengeBattleNum (SaveBlock2+0xCB2); the Pike's (0x08553A14) likewise for layout 0x166.
  Its seven entries carry leftover map numbers 0/1..0/7, so Slateport, Mauville, Rustboro, Fortree, Lilycove,
  Mossdeep and Sootopolis showed a Land list of the Bulbasaur / Charmander / Squirtle lines at Lv 5. The game never
  gives those there, but a DexNav search could (Mauville: 25 grass tiles, no encounter table at all).
- Also found: GetCurrentMapWildMonHeaderId (0x080B4CF8, vanilla) adds VarGet(0x403E) (0..8) to the index in Altering
  Cave (location word 0x6A18 = 24/106, nine headers in a row); find_header always took the first. A script at
  0x086756F8 does compare / setvar on 0x403E, so the set can change.
- Fix: find's only call to find_header (0x08FDA7A2; no other bl to it in the ROM) -> map_header (0x08FF6C80): table
  index 0 -> GetCurrentMapWildMonHeaderId, 0xFFFF -> none, else 0x08E17D50 + 20 * id (the base read from the
  function's own literal 0x080B4D48); index 1 -> none. So the DexNav shows exactly the header every wild encounter,
  Sweet Scent, fishing and Rock Smash use on this map.
- Audit of all 35 TOWN/CITY maps (mapType 1/2; tools/romdata/out/maps.json) against the main table and the tiles
  (behaviour bits 0x08486EFC: bit 0 encounters, bit 1 surfable; Rock Smash = objects with 0x082907A6 / 0x098A44D0
  / 0x098B91CE): apart from the seven Pyramid ghosts, every listed section has tiles to meet it on, and every town
  with no table (Oldale, Mauville, Littleroot, the Sinnoh towns, ...) has no encounters in the game either - the
  DexNav says "No wild Pokemon on this map". The only duplicate map ids in the main table are Altering Cave's sets.
  The guide site's location data was never built from 0x08553894 (checked); tools/romdata/scan_wild.py and
  SUMMARY.md now describe it as the Pyramid's.
- Tested (`test_dexnavscan.lua`, before / after, the user's save): Lilycove - page 2 was Starmie + Charmeleon,
  Charizard and two shadows, now Starmie only; Mauville - four fake rows, now "No wild Pokemon on this map";
  Mossdeep - the fake Land rows gone; Petalburg unchanged; Altering Cave with VAR 0x403E = 0 the form list both
  times, = 3 the form list before and Houndour Lv 12-22 after. test_dexnavseen passes on the same build.

## DEXNAV SCREEN, UNBOUND STYLE — 2026-09-30 — `patches/dexnavui/`
- Asked for: the DexNav screen reorganised like Pokemon Unbound's (the user's screenshot: habitat boxes of icons,
  X for empty slots, an info panel, a SEARCH button). Decided with the user: two screens - Water (5) over Land (6x2),
  Rock Smash (5) over Fishing (5x2), L/R to switch - and the panel's fourth row is the level range (no hidden
  abilities here). An encounter header has 12 / 5 / 5 / 10 slots, so the boxes can never overflow; checked on all
  254 headers: the most unique species per habitat is exactly 12 / 5 / 5 / 10 (Route 101 / 102 / Safari Zone / Route
  210), the most on one map 28 (Route 208). build_lists still caps each list at its box.
- Entry: the old screen's menu callback (0x08FDA238; the START menu entry and R both go through it) sets its CB2 from
  one literal, 0x08FDA514 (was the old init 0x08FDA267, no other reference). It now points at ui_init (0x09FD8001).
  The old list screen, and dexnavseen's hooks inside it and inside dexnavchain's dn_task, stay in the ROM unused.
- Reused, by address (each asserted): find 0x08FDA790 (the map's own header via dexnavscan - the patcher refuses to
  run without it), arm_search 0x08FDE89A / chain_break 0x08FDE5CC (register / stop, exactly what dn_task did),
  sl_get 0x08FDF10A (Search Level from flash), cb2_return 0x08FDE884, state 0x0203A660 (+2 species, +4 chain,
  +9 flags; bit 7 = leave to the field). Own copies of is_seen and the black shadow palette (tag 0x5E64).
- Layers: BG1 = the art (char base 2, map 30, priority 2), 60 tiles for both screens (art.py draws both 240x160
  images and dedups with flips) + one 32x32 map per screen, one 16-colour palette; entries 5-7 / 8-10 are reloaded per
  screen with the two habitats' colours, 13-15 with the button's (green / red STOP / grey). BG0 = one 30x20 window
  (map 31, priority 0, palette 15, transparent) for every word, number and the 16x16 X (BlitBitmapRectToWindow).
  Sprites: the icons (CreateMonIcon; unseen ones get the shadow palette), a 32x32 red ring (tag 0x5E65), and two
  type labels from the summary screen: LoadCompressedSpriteSheet(0x0861CFBC), LoadCompressedPalette(0x08D97B84,
  OBJ 13-15), CreateSprite(0x0861CFC4), StartSpriteAnim(type), palette = 0x09D381A4[type]; Fairy is type 23.
- ui block from AllocZeroed(0xD0) (layout at the top of dexnavui.s), its address in the task's data[0..1]; freed
  with the BG0 tilemap buffer and the windows on the way out. Leaving: bit 7 -> cb2_return, else
  CB2_ReturnToFieldWithOpenMenu (0x08086195), as dn_task did.
- Code + data 0x09FD8000..0x09FDA7BC, in the 0xFF run 0x09FD29F1..0x0A000000 - the window 0x09FD8000..0x09FDD000 is
  the one 20 KB stretch of it with no word in the ROM pointing inside (the run has chance matches elsewhere).
- GOTCHAS: (1) the art showed 40 px too high: InitBgsFromTemplates does not write the scroll registers, and the field
  leaves BG1's; ChangeBgX / ChangeBgY (0x08001D04 / 0x08001E7C) to 0 for BG0 and BG1 at init. (2) Thumb-1 `adds rd,
  rn, #imm` takes 0-7 only - keystone quietly emitted adds.w for #12; conditional branches past 256 bytes likewise
  became bne.w. The patcher's Thumb check caught both. (3) keystone pads `.align` with `00 bf` (a Thumb-2 hint):
  harmless after a return, never executed.
- Tested (`test_dexnavui.lua` on the user's save, and three more maps by hand-written stops): R and START open it;
  ring moves (RIGHT/DOWN/LEFT/UP, rows skipped when empty, shorter rows clamp the column); L/R switch; A on a seen
  species registers (flags 11, species 79 = Slowpoke, water) and the field bar shows it; reopening shows "Hunting:
  Slowpoke" and a red STOP, A stops it; A on the unseen Ralts changes nothing and stays; START-menu DexNav + B goes
  back to the menu; Lilycove (Water + Fishing only), Petalburg, Oldale (nothing: all X, grey button), Route 208 (the
  busiest: Water 5 + Land 12, Rock Smash 4 + Fishing 7), Route 114. The user tried the test ROM themselves and chose
  to keep it.
- Space audit of the day (every byte changed since "(before hmfree)"): six new blocks, 11,275 bytes, each all 0xFF
  with no pointer into it before; 19 hooks of 1-8 bytes (12 in the game's code, 1 in the hack's field-move routine,
  6 in our own DexNav code). Nothing in the save or in permanent RAM.

## SELECT: THE KEY ITEMS AS A RING — 2026-09-30 — `patches/keyring/`
- Asked for: the SELECT popup (keyreg's list, redrawn by pcanywhere with "A PC") as Brilliant Diamond / Shining
  Pearl's ring - item pictures around the player, the PC in the middle where BDSP has its L icon. Kept by the user
  after screenshots and a test ROM.
- Hooks (2 words, both in our own keyreg code): its `bl draw_popup` at 0x08FD8EF6 (was pcanywhere's new_draw
  0x08FD9DE8) -> ring_open 0x08FF6D00, and its popup task literal 0x08FD9134 (was new_task 0x08FD9E7F) ->
  ring_task 0x08FF6FD0. ring_open returns into the task's data[0] either 0x100 | the centre sprite's id, or the text
  window's id from new_draw (the fallback); ring_task hands a text popup to new_task. The actions are pcanywhere's:
  use_item 0x08FD9F36, the PC script copy 0x08FD9FFC (SetupScript 0x08098EF9), ScriptUnfreezeObjectEvents +
  UnlockPlayerFieldControls to cancel. Code 0x08FF6D00..0x08FF7120 (bl range of keyreg), art and tables
  0x09FDA800..0x09FDB498 (after dexnavui, in the same pointer-free window).
- Sprites: per direction a 32x32 box (grey "empty" sheet when nothing is registered) at (120,34) (162,74) (120,114)
  (78,74) - keyreg's order up/right/down/left - and the item's icon from AddItemIconSprite (0x081AFE70; the hack's
  GetItemIconPicOrPalette 0x081AFFFC reads its own table 0x08FCBFF4 with the item-count check removed), moved +4,+4
  (the 24x24 picture sits top-left in its 32x32) and raised to priority 0 (the template's is 1); a 64x64 centre at
  (120,74) (the player's body; the player is at x 112-126, y 66-86): the PC in a box, four arrows, an A badge.
  All ours at OAM priority 0: above the map, the people and BG0.
- PALETTES, the hard part: on the field gReservedSpritePaletteCount (0x0300301C) is 12 - slots 0-11 belong to the
  map's people (tags 0x1103.. in 4-7 on Route 102; 0-3 untagged but used by the player) - and of 12-15 the weather
  (0x1200/0x1201) and field effects (0x1005) take two or three. Measured: 1-2 slots free for LoadSpritePalette on
  every map tried, the ring needs 1 + one per item. So, the field being frozen while it is up, ring_open marks the
  palette of every sprite in use (gSprites +0x3E bit 0, palette = byte 5 >> 4), takes free slots from 15 down,
  saves each one's tag (sSpritePaletteTags 0x03000CF0) and its 32 bytes in both gPlttBufferUnfaded (+0x200 =
  0x02037914) and gPlttBufferFaded (0x02037D14), tags it 0x5E90+k and loads the ring's / the icon's colours
  (LoadPalette / LoadCompressedPalette). AddItemIconSprite's LoadCompressedSpritePalette then finds the tag and
  loads nothing - IndexOfSpritePaletteTag only searches from the reserved count, so that count is 0 while the
  sprites are made and put back after. ring_close destroys the sprites, frees the sheets by tag (0x5E80..0x5E86)
  and writes back the tags and both buffers. Too few free slots, or no sprite for the centre: the text popup.
- Tested (`test_keyring.lua`, the user's save, Journal / Mach Bike / Pokeblock Case / Itemfinder registered):
  Route 102 with four and with two (grey boxes), Lilycove, Route 119 in the rain, a Pokemon Center - each time 9
  (or 7) sprites more while open, the same count after, and every palette tag and colour of both buffers
  byte-identical to before; A -> "Which PC should be accessed?" -> log off, controls back; UP -> the Journal; RIGHT
  -> the Mach Bike (avatar flags 0x22). Fallback: a test copy asking for 17 palettes opened the old text list,
  identical to the unpatched ROM's, and closed cleanly.
- GOTCHA for tests: marking unused gSprites entries in use from Lua (to fake a crowded map) hangs the game within a
  frame, with or without this patch - fake the shortage in the ROM copy instead (movs r5, #1 at 0x08FF6D02 -> #17).

## BATTLE LUCK IS FIXED PER TURN (SAVE-STATE RETRIES REPLAY IT) — CHECKED 2026-10-02 — `tests/battleluck/`
- Report (a v1.7 player, Hard Mode): against Gym Leaders paralysis / confusion "only take effect when I use a
  particular move, otherwise it is as if they had a 100% hit rate; tested several times, the exact same result".
- Not a bug of ours and not a Gym or Hard rule. Measured with `test_battleluck.lua` (the foe's turn read from RAM:
  its PP went down = it acted, its HP went down without PP = it hurt itself, neither = fully paralysed):
  * Status effects work: 8 battles against Roxanne (trainer 265; DIFF 1 / 2, Gym flags on / off), ~10 turns each:
    fully paralysed 5, 1, 2, 1 times; hurt itself 1, 1, 3, 3 times.
  * MODE=replay: the state saved at the move menu, reloaded, a different number of frames waited (14-210), the same
    move chosen: the foe's turn was the same every time - 24 of 24 (paralysis) and 24 of 24 (confusion) against
    Roxanne on Hard with the Gym flags; 16 of 16 in a wild battle (there "could not move" every time) and in a plain
    trainer battle on Standard. The ORIGINAL Chinese ROM: 16 of 16 as well (wild, and Roxanne on Hard).
  * The main RNG (gRngValue 0x03005D80, sRandCount 0x020249C0) still ticks twice a frame in battle and was different
    in every retry, and never converged afterwards (traced 400 frames) - so the engine's luck for the turn does not
    come from it at the moment of the check. Where it does come from was not traced (the hack's own Random at
    0x09D380B2 / RandomRange 0x09D380E4 use gRngValue; the only other writers of it are vanilla - Battle Palace
    0x0803C658 - and the hack site 0x08AE02AE, not looked into; 0x08FFF208 only reads it - see *Random numbers seeded at power-on*).
  * MODE=seq: the same battle started 5, 6, 120, 333 frames after boot gives different sequences over 9 turns
    (paralysis ..P....P. / ......... / .P.P.... / ....P... ; confusion H....H..H / ...HHH... / HH....... /
    HHH...HH.), so a battle begun afresh is rolled anew; only a retry from a saved moment inside it is replayed.
- So: reload a save state, choose the same thing, get the same thing. A move that draws numbers of its own
  (accuracy, critical hit, damage) before the foe acts would shift what the foe then gets - NOT tested (both
  retried moves, Splash and Growl, draw nothing and gave the same result).
- How a Gym battle is set up (for tests): the leader's script calls 0x0983D1A7 = `special 0; setflag 0x273;
  setflag 0x27F; setflag 0x274`, then `trainerbattle`; 0x098415C2 clears them after. The difficulty is var 0x409B
  (1 Standard, 2 Hard Mode, 3 / 4 Challenge / Lunatic), set by the bedroom clock (0x08292781); the party rules are
  skipped when it is 1 (0x0988F344).
- Test GOTCHA: clear the held buttons and wait a few frames before emu:loadStateBuffer - a button still down is
  seen as a new press by the reloaded game (B there backs out of the move menu and the script stalls). And the
  lead faints around turn 10 from Infestation unless its HP is topped up.

## L: MOVE INFO IN BATTLE — 2026-10-02 — `patches/lmoveinfo/`
- Asked for: hold L while choosing a move to see its exact Power, Accuracy and whether it makes contact, in a box
  that comes in from the left, with a mini "L Move Info" HUD. Built: a "[L] Move Info" tag above the move box
  (64x32 sprite at (2,97), its top 14 rows drawn) and a 128x64 panel (two 64x64 sprites, rows 47-110) that slides
  16 px a frame: the name on a navy strip, Power / Acc., Physical (red) / Special (blue) / Status (grey), Contact /
  No contact, Priority (+N / -N / 0), Eff. N%. "---" for 0 power, 0 accuracy (never misses) and no effect chance.
- HOOK, one word: HandleInputChooseMove (0x08057BFC) is `push {r4-r7,lr}; mov r7,r8; push {r7}; movs r0,#0;
  ldr r0,[pc]; bx r0; .word 0x09D0A8C1` - the hack takes it over after the prologue. The word at 0x08057C08 now
  points at our `entry` (bl body; then bx 0x09D0A8C1). lr is already saved there and r0-r3 are free. The hack's code
  at 0x09D0A8C0 (bl 0x09D6077C ...) manages its own indicator sprite and uses START (newKeys & 8 -> 0x09D6AEE0);
  nothing in it reads L or R, so L was free in the move menu.
- Move data (gBattleMoves 0x09D86419, 12 bytes): effect +0, power +1, type +2, accuracy +3, pp +4, effect chance
  +5, target +6, priority +7 (signed), flags +8 (bit 0 = makes contact), +10 the split: 0 physical, 1 special,
  2 status. Checked on Tackle (40/100, contact, 0), Flamethrower (90, 10%, no contact, 1), Swords Dance (2),
  Quick Attack (+1), Roar (-6), Fake Out (+3, 100%). gMoveNames 0x09D30258, 13 bytes each (the header's 0x14C is
  NOT the move names in this hack).
- No RAM of our own: the tag sprite is found by its callback (hud_cb), and its data[] is the state - data0 a
  heartbeat `body` sets to 3 each frame and hud_cb counts down, data1 L held, data2/3 the panel halves' sprite ids
  + 1, data4 the move drawn, data5 the slide offset (-128..0). When the move menu stops running (A, B, the target
  cursor, the move-swap screen) the heartbeat runs out and hud_cb destroys the panel, frees the tiles (tags
  0x5EB0-0x5EB2) and the palette (tag 0x5EB0, LoadSpritePalette - no HUD if no slot is free) and itself, three
  frames later. No hook on any exit.
- Text into sprites, the way the healthbox does it: AddWindow (bg 0, 16x8 tiles, never put on the tilemap) ->
  the frame's pixels LZ77UnCompWram'd (0x082E7091 = swi 0x11) into its tileData (gWindows 0x02020004 + 12*id + 8)
  -> AddTextPrinterParameterized4 (0x08199EED), font 8 (small narrow), speed 0xFF (drawn at once, no VRAM copy),
  background colour 0 so the frame stays -> the window's rows copied 256 bytes at a time into the two sprites'
  tiles (0x06010000 + sheetTileStart*32; sprite +0x40) -> RemoveWindow. Only when L goes down or the cursor moves.
  ConvertIntToDecimalStringN 0x08008CC1. The palette is the key-item ring's (patches/keyring/art.py).
- Addresses: code 0x09FDBCA8..0x09FDC178 (1232 bytes - 16 too many for the 0x08FF7240 gap after repelfix, and
  every call is absolute, so it sits in the pointer-free window after keyring's data), data 0x09FDC400..0x09FDCB54.
  0x08FF7240..0x08FF7700 stays free.
- Tested (`test_lmoveinfo.lua`, a scripted wild Magikarp): the tag in the move menu; L: +2 sprites, the panel in
  after 8 frames; RIGHT / DOWN / LEFT with L held: the panel shows the new move each time; L let go: sprites back to
  the tag only; B to the action menu with L held: all of ours gone (Quick Ball's widget returns); Fight again: the
  tag again. `DOUBLE=1` (bit 0 of gBattleTypeFlags forced during setup): the same in a 2 v 2. `test_lmoveinfo_moves
  .lua` (Snorlax Lv 100, the move list overwritten once the menu is up): the four panels match the ROM's numbers; A
  with L held uses the move, the panel is gone at once, and the next action menu has 18 sprites - as on the
  unpatched ROM (13 the first time, 18 after a turn, on both).
- The chain build (… -> nocandynpc -> lmoveinfo) equals the tested ROM byte for byte; against the working ROM before it (v1.7 plus the Evolutions data
  change of 2026-10-02, sha1 4e74f11aebb9) it changes
  0x08057C08 and the two regions above. sha1 c40d646c9c41.

## QUEST LOG: THE DEVON SCOUT BEFORE FABA — 2026-10-01 — `patches/journal/steps.py`
- Reported: "Chase Faba" (done by 0x40A0) named the Scorched Slab as soon as Nanu's step (0x41BC) was done, and
  players went there first. The wormhole (Scorched Slab 24/73, object 2 at 7,2, script 0x098BF3C5) only lets you in
  with flag 0x41D6 set ("The passage has stabilized"; else "extremely chaotic… dangerous"), and 0x41D6 is set only by
  the Devon Scout on Steven's Island (35/37 object 1, script 0x0983A24A, path: 0x41BC set, 0x41CD and 0x41D6 clear)
  - `tools/romdata/prereq.py 0x41D6`. 0x40A0 itself is set at Whirl Islands (35/72, trigger 11,19).
- New step ANY(0x41D6) "News of Faba" between "Report to Nanu" and "Chase Faba", portrait trainer pic 31 (a
  Scientist), location Steven's Island; "Chase Faba" reworded. Post-game now 39 steps; make_tests.py -> 94 cases.
  test_questlog.lua: 94/94 (SHOTNAMES = {["cut 41"]=true} shoots a case). test_journal.lua no longer applies: the
  Journal opens the Quest Log now, so it logs nothing.

## SELECT RING: NO PC IN SOME AREAS — 2026-10-01 — `patches/keyring/`
- Asked for: no PC from the key-item ring in Rainbow Castle, Allearth Forest, Giant Chasm, Spear Pillar, the
  Distortion World and Mt. Silver, for balance, with a red cross on the ring; always (the user chose that over
  story flags), and a PC that is part of the map must still work.
- The check is the map section, not a map list: `blocked()` (a leaf, no push) reads gMapHeader.regionMapSectionId
  (0x02037318 + 0x14) and looks it up in NOPC (64 Rainbow Castle, 115 Allearth Forest, 110 Giant Chasm, 133 Spear
  Pillar, 119 Distortion World, 66 Mt. Silver; 0xFF-terminated, in the data). Every map of those sections (14 + 4 +
  2 + 3 + 2 + 9), and only those: their warps were walked and lead only to maps of the same section or to other
  places (Mt. Coronet, Sendoff Spring, Ultra Space, Temple of the End, EV Training Cave...). Allearth Lake (116),
  Mountain Top and Temple of the End are not blocked.
- build: the centre sheet is CENTREXSHEET (the same tag 0x5E82, the PC with a red cross from art.centre(blocked))
  when blocked. ring_task: A on the ring when blocked plays SE_FAILURE (32) and leaves the ring up; on the text
  fallback, A when blocked buzzes before pcanywhere's task sees it. A real PC is a metatile/map script and never
  reaches this code.
- Addresses: code 0x08FF6D00..0x08FF717C (ring_task now 0x08FF7000), data 0x09FDA800..0x09FDBCA7. The code grew
  past 0x08FF7140, where repelfix's use_repel was: repelfix moved to 0x08FF7200 (its only pointer is the
  callnative at 0x083D7761, which its patcher writes).
- Tested (`test_keyring_nopc.lua`, the user's save, warped to warp 0 of 34/82, 34/35, 34/9, 35/11, 34/13, 34/53):
  each shows the crossed-out PC, A leaves the ring up (sprite count unchanged), B closes it with every palette tag
  and colour restored and the lock 0; Route 102 (control) A opens "Which PC should be accessed?". test_keyring.lua
  and test_repelfix.lua (yes, lyes) pass as before. Test GOTCHA: test_repelfix yes sometimes shows a second
  lock at step 10 (no script, closes with B) on the old ROM as well - it depends on the clock (RTC), not the build.

## REGION MAP: A FREE CURSOR — 2026-09-30 — `patches/hisuimap/` (regionmap.s, grid.py)
- Asked for: move around the Sinnoh map freely with a red box, like the Hoenn map when flying, instead of the marker
  hopping from place to place (slow to reach anything). Done for both regions: a 16x16 sprite box (tag 0x5EA0,
  priority 0) centred on the cursor's 8x8 square; D-pad = one square, and while held a step every 4 frames after a
  12-frame pause (own timer in task data[10] over heldKeys - the game's key repeat waits 40 frames); the blinking
  marker stays on where you are. DISPCNT gains OBJ (0x1040; the screen had sprites off).
- Naming any square needs a per-square map, which the screen never had (one point per place). grid.py works it out
  from each region's own picture and place table, 30x20 bytes of keys (0xFF = none), region record +24:
  Sinnoh - each square classed by colour (town red (200,88,112) >= 12 px, road oranges r=248 g 150-210 b <= 115 >= 16
  px, lake cyan >= 16 px, else nothing); every connected block of town squares goes to the nearest City/Town/League
  point (within 2); then all places spread along road and lake squares at once (multi-source BFS), so a road square
  belongs to the nearest place along the roads. 172 squares, all 46 places. Hisui - every land square (not the
  picture's blues) to the nearest place, the Temple of Sinnoh only its own square. `python grid.py` draws both.
- Code: the task's hop (snap) and slot_at are gone; key_at (cell -> grid key), cursor_moved (sprite, name box
  top/bottom swap with ClearWindowTilemap 0x080038A4 when the box reaches rows 0-2 / 17-19, redraw only when the
  key changes - data[9]), place_cursor. draw_name and fly_target read the key under the cursor, so greying and the
  couriers' flags work as before (leaguefly's section-97 entry included). Task data [7] cursor cell, [8] sprite.
- Space: the code grew 28 bytes; the blob (0x08FF3000..0x08FF54E4) still ends before ovalcharm (0x08FF5600, now
  asserted). The grids and the box sprite are at 0x08FF7800..0x08FF7D80 (between chance words reading 0x08FF7785
  and 0x08FF80E8). NOT at 0x09FDB500 as first tried: 0x09FC0000..end is reserved and must stay blank. Outside pointers into the blob: the item's field-use
  (unchanged) and Mingyao's two texts (rewritten by the patch); 19 other matches are chance values in graphics,
  identical before and after.
- Tested (`test_freecursor.lua`, the user's save): Oreburgh opens with the box on the marker (place 92); RIGHT
  steps; 60 frames held = 13 squares and back; LEFT x3 = Jubilife City (91), A -> landed 36/2 (the user has
  visited it); reopened, the marker is on Jubilife; 14 x UP -> Snowpoint rows, the name box moved to the bottom;
  the top-left corner stops the box. Hisui: Coronet Highlands on open, DOWN/LEFT -> Prelude Beach, UP -> Snowfall
  Hot Spring. test_hisuimap.lua (hops) is marked superseded.

## QUEST LOG GRID RESTYLED (DEXNAV LOOK) — 2026-09-30
- Asked for: the chapter grid in the DexNav / key-ring style. Only the grid changes; the lists, the detail page and the
  badge case keep the dark theme.
- Own palette: GPAL (questlog_patch.py) is loaded into palette 15 at the start of draw_grid - every way into the grid
  goes through it (opening, B from a list, B from the badge case). Leaving the grid puts the lists' PAL back: gi_list
  loads all 16 colours (it used to reload only colour 4), and the Badges branch does the same before case_open.
  Colour 0 is never used (transparent on a BG); the stripes are 1 and 3.
- Background: grid_bg() draws the whole window (240 x 144, 0x4380 bytes 4bpp) - stripes, and per card a 2 px navy
  ring exactly where card_border draws, a white body and a TAB_H = 16 row tab in the chapter's colour (ACCENT) with a
  slanted end. One BlitBitmapToWindow; the 0 colour key never applies since no pixel is 0. At GRID_FREE 0x09FB8000
  (after the badge case, before the reserved data at 0x09FBF800 - asserted; a pointer scan of the
  full-chain ROM found only chance matches into 0x09FB4000..0x09FBF800).
- Per card, drawn on top: the name on the tab with colours {tab, white, navy} written to V+0xF0 (text fills its cells
  with the background colour, so each card needs its own), the icon (GCHARS: the Sinnoh mountain navy with grey snow,
  the Side Quests bubble grey) and done/total in dark text, green when complete (GCOL +4 / +8). The selected card's
  ring is card_border in colour 4; moving erases with 13, the ring's own navy, so the stripes never need redrawing.
  PULSE is now red to light red (grid_pulse also drives the badge case's frame).
- Tested (mGBA, the user's save, full chain): test_questlog_grid.lua (grid, cursor moves, Key Items list in its own
  colours, back to the grid, Side Content, field) and test_questlog_badges.lua (the case in its dark colours with a
  red frame, back to the grid).

## QUEST LOG: SCREEN SWITCHES AND SCROLLING SPEED — 2026-09-30
- Reported: a frame or two of wrong colours when switching sections; the Legends list painfully slow to scroll.
- Colours: the grid has its own palette (above). Measured frame by frame (a screenshot every frame after each key): the
  old build showed the previous screen in the new palette ~12 frames (grid -> list) and ~22 (list -> grid). Three layers
  of fix, each needed:
  1. load the new palette only after the new screen's windows are queued (draw_grid, list_tail, case_draw);
  2. the Quest Log's VBlank callback runs ProcessDma3Requests (0x08000BF1) itself before TransferPlttBuffer - twice,
     since one call stops at 40 KB and the badge case queues ~43 KB (ten windows, each re-sending the BG0 tilemap);
     VBlankIntr's own call after the callback then finds the queue empty;
  3. a hold flag (V+0xF7) set around "queue windows ... load palette": a VBlank that falls inside it sends nothing
     (and sets gDma3ManagerLocked 0x03000810 so VBlankIntr's run skips the queue too; V+0xF8 marks the lock as ours
     and the next unheld VBlank undoes it). The callback finds V through gTasks (func == TASK_ADDR, data +8, +0x800).
     Tried first and dropped: IME = 0 around the same code - the VBlank IRQ then fires late, mid-frame, and tears.
- Scrolling (hold Down 300 frames in Legends, rows passed): 16 in every build back to v1.5. Timed with parts stubbed
  out (bx lr patched into a copy): no FillWindowPixelRect 26, no text as well 45, the portrait ~nothing. Now:
  - rect writes window 1's buffer directly (gWindows 0x02020004, 12 bytes each, tileData +8; 30 tiles across,
    32 bytes a tile, 4 bytes a pixel row), a word per tile row with a nibble mask - FillWindowPixelRect is per pixel;
  - draw_list = draw_row x LROWS + list_tail (panel, arrows, show); list_move (Up/Down) redraws only the row left and
    the row reached, first moving rows 0-3 <-> 1-4 inside the pixel buffer when the list scrolled by one (V+0xF4 /
    V+0xF5: top and cursor before the move); anything else falls back to draw_list;
  - on an auto-repeat step (the key in heldKeys but not newKeys) the panel is put off (V+0xF6): draw_pane draws the
    empty panel only, and tk_list draws the real one once Up/Down are released. A fresh press draws it at once.
  Result 35 rows / 300 frames. 57 screenshots of spaced presses (Legends, Hoenn, Side Content: down, scroll, up)
  are pixel-identical to the old full-redraw build.
- Back to the grid took ~25 frames: BlitBitmapToWindow of the 240 x 144 background is per pixel (colour key) - now a
  word copy into the buffer; and grid_count ran on every return - now only when the log opens (nothing changes
  while it is open). ~8 frames now.
- test_questlog.lua's fixed timings (B at +40 then +60) lost the closing B while the grid took 25 frames; with the
  faster return it passes: 93/93 with check_questlog.py (TASK_FN is now 0x08FEABD9).

## QUEST LOG: EVOLUTIONS (SOULGOLD-STYLE FAMILY PAGES) - 2026-09-30
- Asked for: a page of every evolution line in the ninth grid slot, reference only (no ticks), spoiler-light; then
  SoulGold's evolution page (icons on top, "Ivysaur: Lv^16." lines), then a Pokedex-style list on the left, one list
  for all regions, every line on one screen, shadows for families not seen.
- The data (patches/questlog/evolutions.py, all from the ROM):
  - the evolution table 0x08F387C0: 40 bytes a species, five {method u16, param u16, target u16, extra u16}. The
    method's low byte is the method; a high byte 0x3F / 0xFF marks a baby whose Egg needs the incense in `extra`
    (another high byte, 0x18 on Glaceon's, is not that). 250 Ultra Burst, 251 Mega (item; item 702 Wishing Piece =
    Gigantamax), 252 Rayquaza's (a move), 253 Primal (an orb), 255 a form's way back to its base (the Gigantamax
    slots 252-276, National Dex 0) - skipped. Eevee's ten are in a table of their own at 0x09F0B4A0
    (GetEvolutionTargetSpecies, 0x09F0534C via the trampoline at 0x0806D098, reads it for species 133).
  - method 6 (trade holding an item) really needs a trade (the case checks trade mode); the Hisuian Pill (753) is
    described as the Verdanturf seller does: held at the usual evolution level. 17 / 33 are places (mapsections.json),
    29 a type (Sylveon: Fairy is type 23 in this hack), 25 a species in the party.
  - families: the evolution graph plus form changes, merged by the first Pokemon's National Dex number (regional
    forms join their base's family). Forms that share a name are labelled Alolan / Galarian / Hisuian (a list of dex
    numbers; Meowth told by type) or by type ("Wormadam (Bug/Steel)"). 323 families.
  - one record per family: {icons, lines, x0, dx, species x 10, 9 lines {x, y, ball, 0, text}}, laid out in the small
    narrow font (font 8, widths 0x08633AE4 - measured against its rendering); a Pokemon reached two ways is one line
    ("Leafeon: Petalburg Woods/Leaf Stone"). The build asserts every family fits nine lines.
  - at 0x09F82600 (~34 KB) in the 0xFF run before the Legends' - not the ROM's end: 0x09FC0000..end is
    reserved.
- The screen (mode 5, questlog.s evo_*): icons are real sprites (CreateMonIcon 0x080D2CC4 with SpriteCB_MonIcon
  0x080D3015, LoadMonIconPalettes 0x080D2F05, FreeAndDestroyMonIconSprite 0x080D2EF9, FreeMonIconPalettes
  0x080D2F9D); DISPCNT now 0x1040 (OBJ on); each icon's OAM priority is set to 0 (BG0 is priority 0). Shadows: SILPAL
  in OBJ palette 15 and the icon's palette number set to 15. The list and the lines are drawn bottom-up: the small
  font's cell is 12 px on a 10 px pitch and its letters reach the cell's foot, so each line may only cover the empty
  top of the one below. Positions are 16-bit (V+0xFC selected, V+0xFE top; 323 > 255), so this screen has its own
  header with u16dec (the BIOS divide) - the Journal's u8dec prints two digits.
- Also: holding Up/Down in the lists speeds up (step_size: a page after four repeats); the grid cursor fix for
  returning from a region chapter; the hint bar is put back on top inside the hold (a frame of blue showed there).
- Tested (mGBA, the user's save): the pages (first family, unseen families' shadows, Eevee's nine lines, a family past
  255, holding, L/R pages, B), the grid's nine cards, test_questlog.lua 93/93 (TASK_FN 0x08FEAC8D).

## REPEL PROMPTS: NO RELEASES, YES APPLIES AT ONCE — 2026-10-01 — `patches/repelfix/`
- Report: after a repel ran out, "Use another?" kept coming back every few steps after answering No. NOT reproduced:
  UpdateRepelCounter 0x080B5870 (only caller 0x0809C91E, the per-step check) returns when the low byte of 0x4021 is
  0 and prompts only when a decrement takes it to 0; after expiry the var stays item<<8 (checked over 120 steps, a
  wild battle, No by B and by DOWN+A). The only writers of 0x4021 are VarSet in UpdateRepelCounter and Task_UseRepel
  0x080FE164 (the six 0x4021 literals: 0x080B58BC/0x080B5918 counter and encounter check, 0x080FE0E0/0x080FE1C4 the
  bag's repel, 0x08FD9AA4 lrepel's VarGet, 0x08B0D544 a data table); no script setvar/addvar/copyvar on it, no patch
  writes newKeys. The L quick repel ("Use the Max Repel?", a different text) fires on a real L press only.
- Two real flaws found on the way, fixed:
  * No: 0x083D7720 is `loadword; callstd 5; closemessage; compare RESULT,1; goto_if_eq 0x083D7760; end` - the `end`
    stops the whole script, so the parent's `release` never runs and FreezeObjectEvents (from `lock`) stays: the
    people on screen stood still until they left the screen (test: 1 of 1 frozen after No). 0x083D7734..35 = `6C 02`
    (release; end) in the zero padding before the text at 0x083D7740.
  * Yes: `callnative 0x083D7781` (CreateTask(ItemUseOutOfBattle_Repel 0x080FE0BD, 0x50)) then `end` - the script
    ends and unlocks while the task waits 8 frames + SE_REPEL; Task_UseRepel then sets the var, RemoveUsedItem, and
    DisplayCannotUseItemMessage 0x080FD164 with the task's PRIORITY byte (+7, 0x50 != 0) as "on the field" ->
    DisplayItemMessageOnField + Lock. The player walked 4 steps with no repel in between (test). Now 0x083D7760 is a
    17-byte script: `callnative use_repel; playse 0x2F; message 0x085E9080; waitmessage; waitse; release; end`.
    use_repel 0x08FF7200..0x08FF723C (repelfix.s; was 0x08FF7140 until keyring grew): VarSet(0x4021, item<<8 | ItemId_GetHoldEffectParam 0x080D7501),
    RemoveUsedItem 0x080FE059 (RemoveBagItem 1, name -> gStringVar2). gText_PlayerUsedVar2 ends in {PAUSE_UNTIL_PRESS}
    (FC 09), so `message` + `waitmessage`, not callstd 4 (that would want a second press). lrepel's Yes
    (0x08FD9AE8 `callnative 0x083D7781`) -> `goto 0x083D7760`; it leaves its yes/no box up, and `message` works
    without a closemessage because the box is "hidden" once printing ends. 0x083D7781 is now unreferenced.
- Tested (`test_repelfix.lua`, CASE=no/yes/lno/lyes, old ROM as control): No - 0 frozen (old 1), var 0x5400, one
  prompt in 40 steps; Yes - the repel on after 0 steps (old 4), Max Repels 104 -> 103, var counts down from 250,
  the box clears; L+No / L+Yes the same. Chain rebuild (… -> keyring -> repelfix) = installed ROM byte for byte.


## RARE CANDY NPC REMOVED — 2026-10-01 — `patches/nocandynpc/`
- Asked for: the NPC that gives 999 Rare Candies is too exploitable, take him out.
- Done at the end of the chain, not by dropping `candynpc` from the middle: every later patch was built and tested
  with its bytes there, and naturefix (0x08F54200), hypertrain (0x08F54300) and hmfree (0x08F54500) sit after its
  block in the same free run. The only pointer into the block from outside it is the 8/6 events' object pointer
  (0x0852F308; whole-ROM scan).
- 8/6 keeps 5 objects on purpose. The hack saves object events in SaveBlock1, so a game saved inside the Mart
  reloads with him on (5,6). Talking looks his template up by localId among the first objectEventCount entries
  (the SB1 copy on the current map); with the count back at 4 that is NULL and the script pointer is read from
  0x10 (BIOS open bus, 0xE3A02004 - the same value as the open Berries-pocket crash report) and garbage runs.
  So object 5 stays, moved to (-100,-100) (never in view, never spawns), and its script at 0x08F53778 is a single
  `end` (02). The rest of the script and the four texts, 0x08F53779..0x08F5382E, are 0xFF again (182 bytes).
  Flag 0x433F is left as it is.
- Tested (`test_nocandynpc.lua`, the user's save): MODE=gone - in the Mart the objects are 255,1-4 (no 5), the
  player steps onto (5,6), candies 33 -> 33. MODE=save on the pre-patch ROM writes a state with him loaded, MODE=ghost
  loads it on the patched ROM: object 5 is on (5,6), A on him does nothing (lock 0, still on the field, candies 33),
  re-entering the Mart drops him. Control: the same state and A on the pre-patch ROM shows "Want 999 Rare Candies?".
  The patcher refuses a second run. Working ROM = the tested ROM (sha1 95c53fb5…); backup "(before candy NPC removed)".

## TM DESCRIPTIONS, ALL 128 READ — 2026-10-01 — `patches/itemdesc/`
- Reported: TM08 and TM09 have the same description. They did (Hyper Beam / Giga Impact share 0x08582AFE), and so
  did four other groups. Every TM/HM read against its move: TM table 0x09E0FE80 (TM01 = item 378, HM01 = 498), the
  item's description pointer (item + 20; items table 0x08FC2C7C, 44 B), the move's names 0x09D30258 (13 B), the
  summary's move texts 0x09D2AD00 (move - 1) and the battle data 0x09D86419 (12 B: effect +0, power +1, type +2,
  accuracy +3, PP +4, effect chance +5). Every number a description gives matches (Fire/Ice/ThunderPunch 10%,
  Snore / Bounce / Air Slash / Scorching Sands 30%, Razor Shell 50%, Hyper Beam & Giga Impact 150, Magical Leaf /
  Swift / Smart Strike accuracy 0 = never miss). The widest line of the game's own texts is 102 px (Protect,
  Attract, Waterfall), now the patch's MAX_PX.
- Shared texts split (each move now says what it is): 0x08582AFE TM08/09, 0x085829B3 TM11/12, 0x08582CDF
  TM28/63/87 (Draining Kiss heals 75%, not half), 0x095522AA TM56/80/103, 0x0955213B TM65/69.
- Wrong or misleading: TM118 Misty Explosion "Has 150 base power if used in Misty Terrain" (no word of fainting),
  TM31 Attract "Makes it tough to attack a foe of the opposite gender" (backwards), TM38 Will-O-Wisp "It always
  burns" (85% accurate). Typos: TM50 "Hits/hits", TM54 "for 2 to 5 times", TM101 "type varies", TM40 "Star-shaped".
  Left as they are: TM39 Facade "Raises Attack when poisoned, burned, or paralyzed" (Game Freak's own wording; the
  same damage), and the hack's capitalised weather names.
- 19 new texts, the item pointers moved, the old texts untouched: 0x08FF6432..0x08FF65DE (after TM75's, up to the
  0x08FF6600 limit) and 0x08FF8900..0x08FF8B05 (the pointer-free stretch 0x08FF8800..0x08FF94FE of the 0xFF run;
  data words read 0x08FF8100, 0x08FF839E, 0x08FF8776, 0x08FF87FE, 0x08FF8800). The patcher checks no word points
  into either window before writing and asserts afterwards that all 128 TM/HM descriptions differ.
- Tested (`test_tmdesc.lua`): the 20 rewritten TMs in the Bag's TM pocket, each shot with the cursor on it - every
  text in its box, three lines, nothing cut. Chain rebuild (... -> repelfix -> nocandynpc) differs from the
  previous working ROM in exactly the 19 pointers and the two text blocks; installed (sha1 141ec5fe...), backup
  "(before TM descriptions)".

## FORM CHANGES: WHERE THE GAME KEEPS THEM — 2026-10-02 — `tools/romdata/forms.py`
- Asked for: every form on the guide's Pokédex with how you get into it, "even if it is just in battle".
  The evolution table only knows Mega Evolution, Primal Reversion, Ultra Burst and one Gigantamax (Charizard, by the
  Wishing Piece). Everything else is in other tables or in code:
  - **Gigantamax and Crowned forms**: 0x08C9A3B0, {u16 species, u16 form, u16 item}, 0xFEFE ends; 36 rows.
    0x08FF1830 walks it for both parties when a battle is set up (called from 0x08FF1134 and 0x09D48F96) and
    0x08FF1858 does a row: item 0xEFEF means "this Pokémon's Gigantamax bit is set" (mon +0x4E, bit 7), anything
    else must be the held item (Rusty Sword 698, Rusty Shield 692). The bit comes from the Max Soup cook on
    Champion Island (35/28, script 0x098A7425: 3 Max Mushrooms, the party's first Pokémon). Two more tables beside
    it (0x08C9A4B0 / 0x08C9A4F0) swap Iron Head for Behemoth Blade / Bash on the Crowned forms.
  - **Held-item forms**: 0x09E0FC70, {u16 form, u16 base, u16 item, u16 item or 0xFFF}, a 0xFFF row ends; 46
    rows: Arceus (the type's Z-Crystal, then its Plate), Silvally, Genesect, Giratina (Griseous Orb), Armored
    Mewtwo (Mewtwo Armor / Revenger Armor), Dialga and Palkia (Adamant Crystal, Lustrous Globe), Shadow Lugia.
    SetMonData's held-item case (0x0806B050) jumps to 0x0981E826, which changes the species the moment the item is
    given or taken. Lugia's row is special: last word 0x1063 = "only item 0x063 (Shiny Stone) turns it back";
    the Dusk Stone (100) turns it.
  - **By move** (battle, 0x09D5D380, pool 0x09D5D9A4): Marshadow + Spectral Thief (666) or 717, Solgaleo +
    Sunsteel Strike (667) or 726, Lunala + Moongeist Beam (668) or 727, Xerneas + Geomancy (601), Keldeo + Secret
    Sword (548); the same routine turns Arceus by Judgment (449) with the Legend Plate (751) held. Meloetta +
    Relic Song (547) is at 0x09D59922, next to Cramorant's Gulp Missile.
  - **By ability**: the battle code's own cases. 0x09D77138 is the list of battle forms and what they go back to
    ({u16, u16}, 0xFFFF ends): Cherrim, Aegislash, both Darmanitan, Minior, Wishiwashi, Ash-Greninja, Mimikyu,
    Lunala, Xerneas, Solgaleo, Marshadow, Eiscue, both Cramorant, Morpeko.
  - **Bag items**: each item's field-use routine sets a callback that starts a script (ScriptContext_SetupScript
    0x08098EF9): Gracidea 0x08FD6A84, Prison Bottle 0x08FD6500, Reveal Glass 0x08FD6B40 (routine 0x09F0157C:
    Tornadus, Thundurus, Landorus, Enamorus), the Nectars 0x08FD6688 / 6634 / 6730 / 66DC, DNA Splicers
    0x08FD6554, Rotom Catalog 0x08FD6794, Deoxys Meteor 0x08FD6300 (routine 0x08FD7A04), Zygarde Cube 0x0988FFC1
    (10 Cells the 10% form, 50 the 50%, 100 the Power Construct one), N-Solarizer / N-Lunarizer / Unity Reins
    0x094A27C0.
- **The ability table**, found the same day: 0x097A0000, three u16 a species (see the CHANGELOG entry).
- **Names that were on the wrong slot** (`species_display.py`): 963 is Ash-Greninja and 1011 the Battle Bond
  Greninja; 1086 is Eiscue and 1177 its Noice Face; 1077 is Cramorant and 1146 Gulping; 953 is Deoxys's Normal
  Forme and 954 its Defense (410 is the Speed Forme); 1150 is the blue Low Key Toxtricity. Told by base stats,
  front pictures, which slot the wild tables use, and which way the battle code swaps them. 1106 is a Mega Flygon
  of the hack's own (Flygonite), 1091 the Typhlosion with the Burning Soul ability.
- **The National Dex table is wrong for five slots**: Hisuian Sneasel (1062) carries 586, Sawsbuck's; the four
  restored fossil Pokémon (990-993, Chinese names in the ROM) carry Pikachu's 25. `forms.natdex()` puts them right.
- Gotchas: `tools/romdata/` has a `dis.py`, which shadows the standard library's when that folder comes first on
  `sys.path` (keystone -> inspect -> dis): append the folder, do not insert it. mGBA stops on a "Temporary file
  loaded" dialog when the ROM is under a temp folder, so `--script` tests never start there.

## QUEST LOG: EVOLUTIONS SHOW EVERY FORM — 2026-10-02 — `patches/questlog/evolutions.py`
- Asked for: the in-game Evolutions pages "exactly like in the website": Mega, Primal, regional, every form, each
  with how. Charizard's Gigantamax was there (the evolution table has its Wishing Piece row) and nobody else's.
- `families()` now takes its forms from `tools/romdata/forms.py`, names from `species_display.py` /
  `display_names.py` ("Gigantamax" cut to "G-Max"), and what counts as a species and its number from
  `forms.is_species` / `forms.natdex`. A page is headed by its number's own species; a regional form that evolves
  gets a line of its own (no method) with its evolutions one step in; forms nothing leads to go under an "Other
  forms" line; a species with other forms and no evolution gets a page too (Articuno: Galarian Articuno).
- More than nine lines: `pages_of()` splits a family over list rows ("133 Eevee", "133 Eevee 2"), never parting a
  line from what it runs on to. 361 families, 366 rows. `questlog_patch.evo_pages` must count rows, not families:
  with the family count the last five rows could not be reached.
- The records are no longer padded to nine lines (evo_draw reads `lines` of them): the blob is 0x09F82600..
  0x09F8C8B0 with them, and would not have fitted before the Legends' data (0x09F90000) padded.
- No assembly changed. The chain rebuild differs from the previous working ROM in the three EVOCOUNT literals
  (0x08FEBA68, 0x08FEBC94, 0x08FEBE10) and the Evolutions blob. Installed (sha1 4c3db374...), backup "(before
  evolution forms 2026-10-02)".
- Tested (`test_questlog_evolutions.lua`): the grid, 18 families' pages, the last row, B back to the field, on the
  user's save (264 of 366 rows seen, the rest shadows and ?????) and on a copy with evo_seen forced, for the pages
  of families the save has not met.

## WHAT CAN ACTUALLY BE HAD: THE AUDIT — 2026-10-02 — `tools/romdata/obtainable.py`
- Asked: is everything on the evolution and form lists obtainable, "not just the Eternatus case"? It was not checked:
  the lists showed how each form comes about, not whether the way is open to a player.
- **Eternamax Eternatus (1195)** cannot be had. Both Dynamax routines return at once for species 1190-1195 (Zacian,
  Zamazenta, Eternatus, the Crowned forms, Eternamax): 0x09D6ABE4 ("can it Dynamax": also refuses species 385,
  Mega Flygon, 902-951 the Megas, and needs the Dynamax Band and flag 0x278 or the right battle type) and
  0x09D5BB84 (the species -> Gigantamax slot switch, the code twin of the table at 0x08C9A3B0). No table row,
  no code constant (no literal, no shifted immediate, no negative-offset compare besides those two), no givemon,
  no scripted battle. It is on Dragon Tamer Yanshan's team (trainer 899), as a species.
- **Kyurem-WB (1119)**: nothing makes or gives it either; it is on Ghetsis's teams (1044, 1120).
- **The Wishing Piece (item 702)** has the Mega Stone hold effect and a row for Charizard, but no script gives it,
  no mart sells it, no wild Pokémon holds it: not a way a player has. (The bytes "BE 02" in scripts are species 702,
  Genesect.)
- **Ash's Pikachu (1076)** has a way: Ash at the Battle Frontier (26/40, script 0x098BCF8C), once beaten, offers to
  put a hat on your Pikachu. 0x0839C7B0 checks the chosen Pokémon is a Pikachu of some kind, 0x0839C850 sets the
  species by a choice 0-6 and four moves. The script always passes 6. Choices 0-4 are species 989-993, now the
  White-Striped Basculin and the four fossil Pokémon: it looks as if those slots were the Cosplay Pikachu outfits
  once, which would also be why the number table still gives 990-993 Pikachu's 25.
- The rest have a way: 1,168 of 1,170; every one of the 110 items forms need and the 38 evolutions need has a
  source (script gift or item ball, mart, held by a wild Pokémon, Battle Points prize: the Max Mushroom is one).
  Legendaries count as had through the Quest Log's Legends chapter and the guide's list. The audit does not play
  the game: it cannot see a way that is open on paper and blocked in play.
- `forms.TRAINER_ONLY` keeps the two off every list (the site's and the Quest Log's); the audit says so if a way
  to one of them ever turns up.
- In the game too: the chain was rebuilt with these (360 families, 365 rows), tested with
  `test_questlog_evolutions.lua`, installed (sha1 4e74f11a...), backup "(before trainer-only forms left out
  2026-10-02)".

## LEFTOVER CHINESE — 2026-10-02 — `patches/zhtext/`, `translation/official/`

Asked for: every Chinese text still in the game except images; reported with it, Swords Dance at +6 printing the
last word of "…'s Attack can't go higher!" in Chinese. One patch at the end of the chain, 2,341 texts and names,
two small code changes and one graphic. Where each kind was and how it is replaced:

- **Official Emerald texts, in place (official.json, 1,444).** The hack translated Emerald's own strings where
  they stood and zero-filled the rest of each slot, so the English fits back at the same address and nothing is
  re-pointed. `translation/official/vanilla.py` reads every labelled string from the pret/pokeemerald source and its
  address and size from `pokeemerald.sym`; `scan.py` compares. Casing follows the texts an earlier pass had already
  converted (`decap.py`). 260 of them are still referenced by something: the Easy Chat screen, the PokéNav map's
  landmark names (`LandmarkName_*`, shown in the zoomed view), link / wireless / Union Room / trade / Berry Blender /
  Mystery Gift messages, Battle Frontier lines. The other 1,184 are restored anyway (the hack moved most scripts,
  but a slot is cheap to put right and stops the scans listing it).
  - 77 of these end in `\p`. The second pass (NOTES, *Remaining-text pass*) left 42 link / Trainer Card messages
    alone because a translation that ends in a page break can hang the text engine. These are not translations:
    they are Emerald's bytes in Emerald's slots, read by Emerald's code.
  - Two static names exist twice in the source with different text (`sText_PleaseWaitAWhile`,
    `sText_CommunicationStandby`); the symbol's size says which is which.
  - Not restored: `SlateportCity_ContestHall_Text_ImLikeMajorlyCheesed` (unreferenced; the hack put another string
    in its tail).
- **The hack's own strings (hack.json).** In place where the English fits the Chinese string's bytes, else a new
  copy at 0x09FD2A00.. with every reference moved. A reference is one of: `loadword 0` (`0F 00 ptr`), `message`
  (`67 ptr`), `bufferstring` (`85 n ptr`), a `trainerbattle` text argument, or a 4-aligned word in a table.
  - **153 trainer lines the earlier passes never inserted** (`lines.py`): their only references are `trainerbattle`
    arguments at unaligned addresses. Those passes had translations for 44 of them and found no pointer to move.
    Mostly defeat lines of the story bosses. `trainer_arg()` accepts `5C type id16 arg16 ptr [ptr [ptr]]` with the
    earlier pointer fields zero or pointers, and one more shape the hack uses for partner battles: type 0, a
    non-zero arg16, a non-pointer word, then the defeat text (`5C 00 9B 03 6F 00 00 8E 00 00 <ptr>`).
  - Defeat lines are expanded with the field placeholders (FD 01 = player, FD 06 = rival) and printed in the battle
    box; 34 characters a line fits ("their dreams who change the world."), `\l` scrolls there as on the field.
  - `givemon` (`79 species level item u32 u32 u8`) carries stale text pointers in its unused fields in a few
    scripts, and `applymovement` (`4F id16 ptr`) with local id 15 looks like `0F 00 ptr`: neither is a text
    reference. Both were caught by reading the bytes before each site.
- **The battle engine's block 0x09D74000..0x09D77030.** Its strings are reached as a literal plus a constant, so
  they can only be replaced where they stand, in the same bytes. Two cases needed code:
  - **"higher".** 0x09D4AA14 `ldr r4,[pc,#0xd4]; adds r4,#0xe` forms 0x09D749F2, a 5-byte slot between two "rose".
    Those two instructions are now `bl 0x09FDCC00`: `ldr r4,[pc,#0]; bx lr; .word` + "higher". lr is free there (the
    function pushes it at 0x09D4A498). "lower" is Emerald's `gText_Lower`.
  - **Field-effect names** for "{side}'s {effect} effect: N turn(s) remaining." (0x09D74CA2): seven 5-byte slots at
    0x09D76FFE.. copied into B_BUFF1 by seven `ldr r1, =literal; adds r1, #n; bl copy` sites. The names are in
    16-byte slots at 0x09FDCC10 (Swamp, Sea of Fire, Rainbow, Wildfire, Vine Lash, Cannonade, Volcalith), the five
    literals re-aimed (0x09D4DE8C, 0x09D4E22C, 0x09D4E240, 0x09D4E908, 0x09D4EA7C) and two constants changed
    (0x09D4E774 0x0A -> 0x15, 0x09D4E886 0x0F -> 0x25: three sites share one literal). The patcher checks that each
    literal has no other reader. The old slots hold four-letter stand-ins. Not seen in play (it needs a Pledge
    combination or a G-Max move); checked by computing what each site now forms.
- **Names inside tables** (`tables.py`, `gen_tables.py`) - no pointer reaches them, so the text scans never saw them;
  the battle test did ("Champion 阿戴克 would like to battle!").
  - The hack's trainer table is at 0x090019F8, 40 bytes each, name at +4 (12 bytes). Trainers 0x399..0x54A are the
    hack's own and 227 of them had Chinese names. Canon characters get their official names; the hack's people keep
    the names earlier dialogue translations gave them, else pinyin. 小驱 / 小进 are Chase and Trace (Let's Go).
  - The hack's font has its own glyphs in some rare-hanzi slots, so a decode shows 哞 for what reads as 唔 ("Mm…"),
    詈绊 for 羁绊 (bond), 鲷 in 大力鳄 (Feraligatr). Translate by sense, not by the decoded character.
  - Items 697 and 754-767 (name[14] at the start of each 44-byte entry at 0x08FC2C7C): second copies of held items
    with the originals' descriptions; they take the originals' names.
  - Species 990-993: the hack's four restored fossil Pokémon. Move 937: a second Petal Dance.
  - Pokédex entries 906-959 (filler, Bulbasaur's text): category 种子 -> "Seed".
  - Emerald's Trainer Hill (`sFloors_*`: floor 952 bytes, trainer 328, name at +0, six mons of 44 with the nickname
    at +32) and `gApprentices` (name[6 languages][8]; all but the Japanese one were Chinese): from the pret source.
  - Dead tables, left: Emerald's `gMoveNames`, `gAbilityNames`, `gSpeciesNames`, `gTrainers` at their vanilla
    addresses are still Chinese and nothing points at them (the hack has its own at 0x09D30258, 0x09D03068,
    0x08F2B790, 0x090019F8).
- **One graphic** (`cityzoom.lz`). The PokéNav's zoomed city maps label buildings with sprites cut from a 64x64
  sheet (`sCityZoomTextSpriteSheet` 0x086230F8); the hack redrew it in Chinese at 0x08FA5490. Emerald's sheet,
  re-compressed from the pret PNG (702 bytes), is written into Emerald's own slot 0x08DC9208 (0x2C0 bytes, unused
  by the hack) and the sprite sheet points there. Image text stays in capitals like the rest of the PokéNav.
- **Free space**: moved texts 0x09FD2A00..0x09FD5472 (no 4-aligned word in the ROM points into
  0x09FD2A00..0x09FD6F00; the hits at odd addresses are code bytes), the stub and names 0x09FDCC00..0x09FDCC80.
- **Scans** (`remain.py`, `names_scan2.py`), before -> after: official texts still Chinese 1,333 -> 0; engine block
  20 -> 0; strings a pointer reaches 603 -> 60. The 60 are data that decodes as hanzi (graphics, movement lists) and
  old copies whose references were moved long ago. Also still in the ROM and unreferenced: the old copies of every
  string this and earlier passes moved (badge names at 0x09875111, item descriptions at 0x09553C50, Pokédex
  texts at 0x09600777…).
- **Tested** in mGBA: `test_zhtext_battle.lua` MODE=higher (Swords Dance at +6: "Blaziken's Attack can't go
  higher!") and MODE=defeat (a scripted battle with trainer 0x541 using the script's own re-pointed argument:
  "Champion Alder would like to battle!", the three-page defeat speech); `test_zhtext_field.lua` (the Easy Chat
  screen as an interview opens it; the PokéNav's Hoenn map zoomed over Littleroot, Oldale, Petalburg, Rustboro and
  Routes 104 / 116: labels and landmark names). The patch applied twice gives the same ROM. The 40 tests of the v1.7
  batch on the result: same logs but for boot-frame numbers and data another change had touched.
  Test trick that changed: the engine rewrites `gBattleMons[0]` from the party while the menus are up, so a move
  written at the action menu is gone by the time it is used. Write it from the move menu until it is picked.
- Installed (sha1 d73b7c0f...), backup "(before leftover Chinese 2026-10-02)".

## DAY/NIGHT: ON / OFF IN THE OPTION MENU — 2026-10-03 — `patches/daynight/`

Asked for: a way to switch the evening and night colours off in the Option menu ("sometimes the colour of the game
is not good"), and that switching it back on shows the right time of day.

- **How the hack tints.** Not in the palettes: `gPlttBufferUnfaded` and `gPlttBufferFaded` are the same at every
  hour. TransferPlttBuffer (0x080A19C0), which copies the faded buffer to the screen each frame, jumps at 0x080A19E0
  (`ldr r1, =0x08CFE3E1; bx r1`) into the hack's routine. That routine reads gLocalTime's hour (0x03005CFA), stores
  the time of day at 0x0203C000 and picks a mask of colour channels to keep:

  | hour | time of day | mask | what the screen gets |
  |---|---|---|---|
  | 0-3 | 0 | 0x0000 | every channel halved (dark) |
  | 4-5 | 1 | 0x03FF | red and green kept, blue halved |
  | 6-16 | 2 | 0x7FFF | unchanged |
  | 17-18 | 3 | 0x001F | red kept (orange) |
  | 19-21 | 4 | 0x7C1F | red and blue kept (pink) |
  | 22-23 | 5 | 0x7C00 | blue kept |

  Then, unless the map type (gMapHeader+0x17) is 0, 4, 8 or 9 (none, underground, indoor, secret base) or the byte
  0x02021685 is non-zero, it copies the 32 palettes itself, 8 words each, with `((c & ~(0x04210421 | mask)) >> 1) +
  (c & mask)`; a palette bit mask picks which (0xFFFF0FFF: not BG palettes 12-15; none when 0x02021686 is above 2).
  Otherwise it does the plain DMA copy and returns to 0x080A19E6. The Bag and battles are already untinted.
- **Off** = that routine takes its plain copy. `ldr r0, =0x02021685; ldrb r1, [r0]` at 0x08CFE452 became
  `bl tint_gate`, which returns r1 non-zero for the hack's byte or for bit 4 of SaveBlock2+0x15. lr is free there.
  The hour, the time of day at 0x0203C000 and everything that reads the clock are untouched, so On is right for
  the hour from the next frame.
- **The bit.** The 21 accesses to SaveBlock2+0x14 / 0x15 in the ROM use bits 0-3 of 0x15 (sound, battle style,
  battle scene, region map zoom); the hack's own 0x08C60F20 forces battle style. Task_OptionMenuSave writes
  bitfields, so bit 4 survives. 0 = On, so old saves and new games start On.
- **The row.** The menu's window holds seven rows and has no room for an eighth, so it takes the place of "Cancel"
  (B has always left the menu and saved; A on that row no longer does anything):
  - sOptionMenuItemsNames[6] (0x0855C67C) -> "Day/Night";
  - DrawOptionMenuTexts (0x080BB104): its `bl CopyWindowToVram` (0x080BB144) goes to texts_tail, which draws the
    row's On / Off first (dn_draw: the game's On / Off strings through DrawOptionMenuChoice 0x080BAB68 at y 96, "Off"
    right-aligned to 198 like the Battle Scene row);
  - Task_OptionMenuProcessInput (0x080BA86C): `b return` for a row above 5 (0x080BA938) goes to case6, which on
    Left / Right flips the bit in the save, sets sArrowPressed and redraws, then joins the task's tail
    (0x080BAA46). The `beq` that made A leave from row 6 (0x080BA88E) is a `mov r8, r8`.
  - Both are reached through 8-byte veneers at 0x080BAFD4 / 0x080BAFDC: the body of ButtonMode_ProcessInput, dead
    since rbutton put a trampoline at its head. A `b` reaches 2 KB and a `bl` 4 MB; the free space is 16 MB away.
- Code 0x08FF7240..0x08FF7316 (after repelfix). In the chain before `zhtext`.
- GOTCHA: `.align` again - the literal pools are aligned with an explicit `mov r8, r8` and the patcher checks that
  every pc-relative load lands on one of its chunk's own `.word`s.
- Test notes: the game only re-reads the clock on some events (a map load does it), so a test that shifts the
  save's time offset (SaveBlock2+0x9A, hours) must warp afterwards. Tint = the number of colours in palette RAM
  (0x05000000) that differ from gPlttBufferFaded: 398 on Route 102 at 23:00, 0 when off.
- Tested: `test_daynight.lua` (10 checks: tinted at 23:00; the bit set -> not; cleared -> tinted; the menu's row,
  RIGHT sets it, A stays, B leaves; Off kept on the field; LEFT -> the tint back at once; 12:00 no tint) and
  `test_daynight_battle.lua` (BIT=1: field, Bag, battle, field all 0; BIT=0: 398 / 0 / 0 / 400, as before).
- Installed 2026-10-03 (sha1 e85a5245...), backup "(before Day-Night option 2026-10-03)". The 40-test batch gave the
  same logs as the build
  before it (the four repel tests sometimes log a second, unscripted control lock around step 10 - not identified,
  it comes and goes between runs of the same ROM; both builds give the same log when run back to back).

## LORELEI / FLYGONITE FREEZE REPORT — NOT REPRODUCED — 2026-10-04 — `tests/lorelei/`

Report (relayed): "I cannot obtain the Flygonite because on battling with Lorelei, it crashes the game. After she
finishes her dialogue, the game freezes." No version, emulator or save yet.

- **Where.** Ice Maze, map 35/53 (indoor, weather shade), entered from Meteor Temple 35/54. Lorelei is object 2
  (local 3) at (20,9), script 0x098245D6, hidden by flag 0x4163; the Lapras behind her is local 4 (no script).
  The Flygonite (item 700) is not hers: the sealed Flygon, object 0 (local 1) at (25,17), script 0x098249F4, flag
  0x4160 - a scripted wild Flygon Lv 70, then `giveitem 700`. She stands in a one-tile corridor and can only be
  talked to from (20,10).
- **Her script**: lockall; showcoinsbox 1,21 (off screen, never hidden); showmonpic Lapras + cry; "!" on the
  Lapras; msgbox; `special 0x3E`; playbgm 0x1FC; `trainerbattle 0, 0x3D8, 0, NULL, defeat`; msgbox;
  fadescreenswapbuffers; removeobject 3, 4; fade in; setflag 0x4163; releaseall. Trainer 0x3D8: class 0x1F (Elite
  Four), pic 0xD1, Dewgong / Jynx / Cloyster / Slowbro (Slowbronite) / Sandslash Lv 65, Lapras Lv 70.
- **How the hack's boss scripts start a battle** (this pattern is in most of them): special 0x3E is vanilla
  BattleSetup_StartRematchBattle - it creates the battle-start task and stops the script context - and the
  `trainerbattle` behind it runs in the same frame, so it only loads the arguments (the opponent id) and parks the
  script on `lock` in EventScript_TryDoNormalTrainerBattle (0x08271362). No intro text is shown (the pointer is
  NULL and never read). Two consequences:
  - the battle transition and battle music are chosen before the opponent id is loaded, from whatever trainer was
    fought last this session (gTrainerBattleOpponent_A 0x02038BCA, 0 after a boot). An Elite Four / Champion
    class there gives the mugshot transition (the hack's hook 0x094A3420 shows the real opponent's picture).
  - the battle ends in the hack's CB2_EndRematchBattle (0x080B1994 -> 0x09D5E028): won -> back to the field and
    the script goes on; lost or drawn -> white out, unless flag 0x273 is set, which is then treated as won.
    Back in the script, GetTrainerFlag is true (the flag is set at battle end) and `gotopostbattlescript` jumps
    behind the trainerbattle command.
- **Trainer flags.** GetTrainerAFlag / B are hooked (0x094A3404): id <= 0x357 -> flag 0x500 + id; above ->
  id + 0x40C9, in the hack's extended flags. Lorelei = 0x44A1.
- **The hack's extended flags** (GetFlagPointer 0x0809D6EC -> 0x09F00CEC), ids 0x4000..0x467F, byte index
  i = (id - 0x4000) >> 3: i <= 0x33 -> SaveBlock1 + 0x988 + i; 0x34..0x67 -> SaveBlock1 + 0x3B24 + (i - 0x34);
  0x68..0x9B -> SaveBlock2 + 0x5C + (i - 0x68); above -> SaveBlock2 + 0x28 + (i - 0x9C). So 0x4160 / 0x4163 are
  bits 0 / 3 of SaveBlock1 + 0x9B4, and 0x44A1 is bit 1 of SaveBlock2 + 0x88.
- **Tested** (`tests/lorelei/test_lorelei.lua`, a copy of our save with the two flags cleared, mGBA):
  - talk -> action menu: current build and v1.7 with difficulty 2 / 3, party level 40 and 2, one Pokemon, the girl,
    23:00, text speed 0 / 3, battle scene off; last trainer = Lorelei, Sidney, Phoebe, Glacia, Drake, a Champion,
    a Magma and an Aqua member, an ordinary trainer, 0x400, 0x3FE, 0x800, 0xFFFF (every transition the chooser can
    return); each of flags 0x264, 0x268, 0x272-0x274, 0x276-0x278, 0x27F left set. All reach the battle.
  - the whole thing (win, defeat speech, after-battle lines, fade, both objects gone, controls free, screen back):
    current build; v1.7 at difficulty 2 and 3, as a first-time fight (0x44A1 cleared), as a rematch, at 23:00, as
    the girl at Lv 60, with Instant text.
  - a real fight (each of her Pokemon acting for several turns: Waterfall, Lovely Kiss, Poison Jab, Thunder,
    Earthquake, Mega Slowbro's Psychic, four Full Restores): v1.0, v1.3, v1.4, v1.5, v1.6, v1.7.
  - the sealed Flygon to "put away the Flygonite": v1.7.
  - In every release the script, texts, trainer, party, map events, standard trainer scripts, battle-setup and
    transition code are byte-identical to the original Chinese ROM.
- Not tested: losing (the harness got stuck in the party menu), other emulators or hardware, the player's own
  party. Open until we have the save.

## RANDOM NUMBERS SEEDED AT POWER-ON — 2026-10-06 — `patches/rngseed/`

Report (relayed): for a static encounter like Rayquaza "the RNG in the Emerald ROM is broken: it always reverts the
odds to zero on the counter and doesn't keep registering when you reset the game".

- True, and vanilla Emerald (pret/pokeemerald fixes it behind BUGFIX). AgbMain (0x080003A4) never seeds the RNG:
  gRngValue (0x03005D80) is 0 at power-on. Random (0x0806F5CC, x = x * 0x41C64E6D + 0x6073, returns the top half)
  also counts its steps in sRandCount (0x020249C0, "the counter"); VBlankIntr steps it once a frame. So the RNG at
  any moment is step N of one fixed sequence, N = frames since power-on plus the numbers used.
- Measured (`test_rngseed.lua`): two boots 7 s apart had the values of steps 28 and 23 from seed 0 at the script's
  first frame (only the emulator's start-up differed). A scripted Rayquaza battle at a fixed frame after loading the
  save: runs 1 and 2 at step 738 -> the same Rayquaza (personality 5F48539D, Quiet, 31/15/31/31/31/2); run 3 at step
  737 -> its neighbour (539D6757, Timid). Resetting with similar timing therefore keeps landing in the same short
  stretch of the sequence; what is not in it never comes up.
- Rayquaza's battle (Sky Pillar, script 0x09824068) is `setwildbattle 406 50`, then 0x8004 = 6, 0x8005 = 3 and
  `callasm 0x08FFF201`: the hack's routine that makes 0x8005 random IVs of party slot 0x8004 (6 = the wild one, as
  gPlayerParty + 6 x 100 = gEnemyParty) 31, choosing them with its own LCG on gRngValue's top half (it reads gRngValue,
  it does not write it - the earlier note that 0x08FFF208 writes it is wrong). 257 scripts use it.
- The patch: AgbMain's `bl RtcInit` (0x080003DA) -> veneer 0x080BB030 (the dead body of ButtonMode_DrawChoices,
  behind rbutton's trampoline) -> rng_seed (0x08FF7320..0x08FF7368): RtcInit, RtcGetInfo(&sRtc) (sRtc 0x03000DC0:
  year, month, day, weekday, hour, minute, second in BCD, then status; the game's default date when there is no
  clock), then gRngValue = hash of those seven bytes (two multiplies and a shift-xor). Nothing else: the RNG still
  steps per frame and per use, sRandCount is untouched, Random2 is not seeded (it was not before either).
- Tested: after the patch the three runs' RNG values were on no step of the seed-0 sequence (checked to 2,000 steps)
  and gave three different Rayquazas (Mild 24/19/31/31/31/31, Mild 1/14/14/31/31/31, Quirky 31/31/31/15/5/31) - each
  still with three 31s. The 40-test batch (Sky Pillar catch and entrance included) on the build.
- Not changed: an emulator save state restores gRngValue with everything else, so reloading one before an encounter
  replays the luck it was made with (see *Battle luck is fixed per turn*); waiting a different number of frames
  before acting still changes the result.
- Installed 2026-10-06 (sha1 5a84f01b...), backup "(before RNG seed 2026-10-06)". The 40-test batch: 36 logs the same as the
  build before, the four repel tests differ only in random wild battles, Sky Pillar catch PASS.

## "SOUND" IS THE HACK'S EXP SWITCH — 2026-10-07 — `patches/expgain/`
- Reported: Sound set to Stereo = no experience until it is set back to Mono. Reproduced with the real menu
  (`test_expgain.lua`, a Lv 2 Magikarp, the Lv 69 party member): Mono 2 EXP, Stereo 0, Mono 2.
- Why: SetPokemonCryStereo 0x082E1810 is a trampoline to the hack's 0x09D45278 = `if (val) FlagSet(0x267) else
  FlagClear(0x267)` (FlagSet 0x0809D741, FlagClear 0x0809D769; literals at +0x1C/+0x20/+0x24). It writes nothing
  to REG_SOUNDCNT_H or the sound info any more. The row's handler (Sound_ProcessInput 0x080BADD8, vanilla) calls
  it on Left / Right, and the game calls it with the saved bit when a save is loaded. The hack's experience code
  tests FlagGet(0x267) at 0x09D5ACC0 and 0x09D5B00A (literals 0x09D5AE6C / 0x09D5B090) right after FlagGet(0x276)
  and skips the award; 0x276 is the script-side "this battle gives no EXP" flag (44 setflag / 46 clearflag in
  scripts), 0x267 has no script reference at all. Writing only the option bit (SaveBlock2+0x15 bit 0) changes
  nothing - the flag is what counts.
- Fix = the label: sOptionMenuItemsNames[3] (0x0855C670) -> "Exp. Gain", written over the "Mono" / "Stereo"
  strings (0x085EE61D, 24 bytes; only Sound_DrawChoices' literals 0x080BAE54 / 58 pointed at them), and those two
  literals -> the game's "On" / "Off" (0x085EE5F4 / FD). Choice 0 (flag clear) = On. No code changed.
- Not done on purpose: making it a real Mono / Stereo row again would remove a feature players use (level caps),
  and a save sitting on "Stereo" would need its flag cleared.

## NAMING SCREEN: AN ENGLISH KEYBOARD — 2026-10-07 — `patches/namingkb/`
- Asked: the nickname keyboard still shows Chinese letters. It did (see the patcher's docstring for the three
  pages and the buttons).
- The hack's keyboard code is 0x094A3378..0x094A3810, hooked from naming_screen.c through literals at 0x080E3338,
  0x080E3D7C, 0x080E46D4, 0x080E4A30, 0x080E4D14, 0x080E4DE8: setup of the Chinese page (0x094A3378), the key
  handler (0x094A3388: START = to OK, R / L = next / previous Chinese page, else Emerald's 0x080E46E1), page_ptr
  (0x094A35B8), build of the RAM page (0x094A35D8), PrintKeyboardKeys (0x094A3626), the cursor's position
  (0x094A36A8: x = 0x1D + 12 * col, y = 0x58 + 16 * row), GetCharAtKeyboardPos (0x094A36EC: 0xFF00 | c, or the
  two-byte code). sPageColumnCounts (0x0858BEA0) is 12, 12, 12. Emerald's own key tables (sKeyboardChars
  0x0858BE40, the row strings 0x0862B88D..) are unused; the hack's two ROM pages (0x0862B810, 2 x 0xC4) lie over
  Emerald's Easy Chat keyboard strings and the first naming rows.
- A ROM page: 4 rows x 0x31 bytes, 12 cells `FC 11 n c` + 0xFF. The hack's own spacing drifts a pixel after narrow
  letters; the new rows are computed (key i starts at 3 + 12 i, glyphs narrower than 6 px centred) from the font's
  width table 0x086542E4.
- The patch: new 3-page table at 0x08FF7380..0x08FF75CC (after rngseed), page_ptr's literal 0x094A35D4 -> it,
  six `cmp #2; bne` -> `b` (0x094A35BA, 36FE, 3638, 365A, 37B4, 37D0), the setup's `strh; bl build` -> nops
  (0x094A3380). The RAM page is simply never used; names keep their two-byte support (a saved Chinese nickname
  still prints).
- Art: compared with pret/pokeemerald's graphics/naming_screen/*.png as 4bpp, only four sheets differ from
  Emerald - back_button (0x08DD3C84), page_swap_upper / lower / others (0x08DD4044 / 40E4 / 4184). They are
  Emerald's again (the .4bpp files in the folder). The button shows the page SELECT goes to next (UPPER page ->
  "lower"), as in Emerald.
- GOTCHA: "\x53".."\x56" for the PK MN PO Ke glyphs are the ASCII letters S T U V - the first table mapped those
  four keys to the glyphs. The glyphs now have their own placeholder characters.
- GOTCHA (test): keys are ignored while the page turns (about a second) - wait after SELECT.
- ChangePokemonNickname is special 0xA1 here (0x9E is the wall clock), DoWaldaNamingScreen 0x201.
- Tested (`test_namingkb.lua`): the three pages and buttons, "ABbz♀1" typed across them (bytes BB BC D6 EE B6 A2),
  L / R ignored, START to OK, A saves; a blank key = space, B deletes ("A C" = BB 00 BD); the same on Walda's
  15-letter screen. Chain (... -> rngseed -> expgain -> namingkb -> zhtext) = the previous build + exactly these
  two patches' bytes (932 bytes in 23 runs); sha1 6ef5c8d9....
- Test harness, 2026-10-07: the "latest" macOS mGBA build on the download server is now 0.10.5 (no `--script`).
  mGBA's headless tool, built from source with `-DBUILD_HEADLESS=ON` and Lua, runs the same test scripts
  (`mgba-headless --script run.lua game.gba`) once it is given a video buffer and `mCoreAutoloadSave` (two lines
  in src/platform/headless-main.c) - without them the save is not loaded and `emu:screenshot` has nothing to save.
- Installed on the Mac 2026-10-07 (sha1 6ef5c8d9...), backup "(before Exp Gain + naming keyboard 2026-10-07)" - that
  ROM was still the 2026-10-01 build (141ec5fe), so this install also brought it up to the repo.

## TM AND HM LOCATIONS FOR THE GUIDE — 2026-10-06 — `tools/build_tm_locations.py`
- Asked: can the site show where the TMs are? Yes: all 128 have a source the scripts show. The page is `/wiki/tms/`
  (`site/src/pages/wiki/tms.astro`, data `site/src/data/tms.json`).
- TM01-TM120 are items 378-497, HM01-HM08 are 498-505 (the tool finds them by name in the item table).
- What hands one over, per map entry point (objects, triggers, signs, map scripts; `scripts.walk`):
  `setorcopyvar 0x8000, item` + `callstd 1` is an item ball (72), + `callstd 0` a gift (49: 31 gifts, 16 Gym
  prizes, 2 trades); `additem` after a `removecoins` is the Game Corner's prize counter (10/3: TM40 1,500 coins,
  TM10 3,500, TM03/04/05 4,000 each); `pokemart` lists: Lilycove Department Store 4F's right-hand clerk (list
  0x0830AD06: TM08, 09, 17, 18, 19, 60, 61, 62) and Champion Island's shop (35/25, list 0x08F55CB0: TM01-TM90).
  No hidden item (bg event kind 7, 112 of them) is a TM.
- Champion Island's clerk checks flag 0x42D5 first ("We are still busy preparing goods"); the flag is set by the
  map script of 34/31 (Test of Heart) after trainer 1135, Champion Cynthia. The island is a warp on Route 105.
- Not sources, though they look like it: `setorcopyvar 0x8000, n` + `callstd 8` (registering a rematch: n is a
  trainer id that happens to fall in 378-505); scripts no map runs - the vanilla Lilycove list at 0x0821FE20 (TM38,
  25, 14, 15: that clerk's script is now 0x08F55BF0, evolution items), a run of ball scripts near 0x098327B4 and
  0x08FE3E00 for TMs the author moved, and a block at 0x09807964 that gives TM118-HM08 in a row.
- One ball on two maps: TM117 (Hearthome City 36/7 and Iron Island 36/67, flag 0x4310) and TM120 (Meteor Temple
  34/17 and Icirrus Town 35/17, flag 0x4298). Whichever is picked up sets the flag both objects hide on; the page
  says so on both rows.
- The gifts' conditions come from reading each script, kept as `NOTES` in the tool. Ones that needed the code, not
  just the text: the Pacifidlog brother gives TM100 Mega Punch at friendship score 4+ (150 or more) and TM01 Mega
  Kick at score 0-1 (under 50), nothing between, once a day (flag 0x12B); Fortree's Hidden Power game is multichoice
  0x36 (Right, Left) and wants 0, 0, 1; the Trick House TM70 is the fifth branch of the reward switch; TM79 is given
  for the Meteorite by Prof. Cozmo and also by Tatara at Fuego Ironworks (37/52).
- `tools/romdata/out/script_index.json` was from 2026-09-21 and knew 5 of the 128. The tool does not use it (it
  walks the scripts itself) but `obtainable.py` does: rebuilt with `scripts.py` (7,603 entry points on 867 maps),
  and the audit on it gives the same answer as before, 1,168 of 1,170 with nothing new missing.
- Place names: `tools/romdata/map_names.json` (pret's `map_groups.json`) for groups 0-33 within vanilla's counts,
  checked against the ROM's map section; the hack's own maps have only their section name, so the eight Sinnoh Gyms
  (37/82-84, 37/89-93) and the Champion Island shop are named in `PLACES`.
- Site: 21 browser checks (filters, search, the links from Moves and a learnset, phone, dark) on both the GitHub
  build and the domain-root copy; link check clean; `wiki/tms/index.html` is 134 kB. The learnset links add about
  1 MB over the 1,168 species pages.
- Published 2026-10-07: public repo commit 8850ff1, together with the lighter Encounters page, the Pokédex index's
  sprite sheets and the InfinityFree package script from 2026-10-04.

## FUSION SLOTS: "MULTIPLE FUSIONS ARE NOT ALLOWED!" WITH NOTHING FUSED — 2026-10-07 — `patches/fusionfix/`

Report (a player's, no save): "how to fuse Necrozma and Solgaleo - when I select Necrozma it says multiple fusions are
not allowed".

- **How the game fuses.** Each item's field-use routine starts a script that opens the party screen (special 0xA2,
  the choice in var 0x8004) and calls one routine, which answers in var 0x800D:
  * N-Solarizer (641), N-Lunarizer (642), Unity Reins (742): field use 0x094A28D8, script 0x094A27C0, callasm
    0x08C60D31 = a trampoline (`ldr r0,[pc,#0]; bx r0; .word 0x09F00F59`). The routine tells the three apart by the
    item's byte +0x28 (0, 1, 2; 0x080D7644). Answers: 0 "can't be combined", 1 done, 2 "You are missing a
    <partner>", 3 "Multiple fusions are not allowed!", 4 choose a move to forget, 5 party full. The script calls it
    twice: var 0x8006 = 0 asks, then 1 (fuse) or 2 (split) does it. The player chooses the Necrozma or Calyrex; the
    partner is found in the party.
  * DNA Splicers (671): script 0x08FD6554, callasm 0x08FD7021 (called straight, no trampoline). The player chooses
    Reshiram or Zekrom to fuse (Kyurem is found in the party) or the fused Kyurem to split. Answers: 1 fused, 2 "no
    Kyurem in your party", 3 the same refusal, 4 split, 5 no room.
  * The Pokemon that goes inside is kept whole (100 bytes) in the saved overflow stream: **0x0203D5E0 Necrozma's
    (Solgaleo 844 or Lunala 845 - both items use this one slot), 0x0203D644 Calyrex's (Glastrier 1088 or Spectrier
    1089), 0x0203D800 Kyurem's (Reshiram 696 or Zekrom 697)**. So one fused Necrozma, one Calyrex and one Kyurem at
    a time, by design. (The earlier notes here called 0x0203D644 Lunala's: wrong.)
  * "Taken" is: species (+0x20) not 0 for the first two (GetMonData at 0x09F0124A), first word not 0 for Kyurem's
    (0x08FD704E). A split by the first routine also wants the slot's species to be exactly the partner's
    (0x09F01262), or it answers 3 as well. Kyurem's split checks nothing.
  * A dead older copy of the Necrozma routine sits at 0x094A2974 (it reads the slot through the literal
    0x094A2B50); nothing calls it.
  * The first routine never updates gPlayerPartyCount: a split puts the partner in slot [count] and leaves the
    count; the game recounts later (the party screen does). Kyurem's updates it.
- **Three ways a slot stayed "taken" with nothing to split** (each reproduced on our save):
  1. **v1.5's Hyper Training** (ours). Its scratch byte was 0x0203D600 = Necrozma's slot + 0x20, the stored
     species' low byte, in the saved stream. Every look at the EV-IV Display or an IV judge rewrote the low six bits
     with the parities of the IVs read. v1.6 moved the scratch (0x0203F13C) but did not clean saves. On a
     v1.5-era build (archive "before bagslots 2026-09-28"): split Necrozma, open the EV-IV Display once -> the byte
     is 62; save; on any later build the N-Solarizer answers 3, the N-Lunarizer too (or 2 with no Lunala). With a
     Solgaleo stored the species became 832-895 and the split answered 3: the 2026-09-28 note ("would hand back
     Decidueye") was wrong, it handed back nothing.
  2. **NEW GAME does not empty the slots** - the original Chinese ROM's behaviour, checked on it. The title screen
     has loaded the save; NewGameInitData leaves the stream's three slots as they were, so a new game started over a
     save with a fusion carries the stored Pokemon and can never make that fusion.
  3. **The fused Pokemon is gone** (released), or case 2 on a save made before this patch.
- **The patch** (312 bytes at 0x09FDCD00..0x09FDCE38; three pointer words):
  * 0x08C60D34 -> fx_entry, 0x08FD655E (the DNA script's callasm operand) -> fx_dna. Before the game's routine:
    Necrozma's slot with no Pokemon in it (level byte +0x54 = 0, which is how ZeroMonData and a new game leave it)
    gets species 0; when the chosen Pokemon is Dusk Mane (1068) / Dawn Wings (1069) and the stored species is in
    832-895, it becomes 844 / 845 (the slot only ever takes that form's partner; 844 can have become 845, so the
    form decides); when a fusion is asked for (plain Necrozma 853, Calyrex 1098, or Reshiram / Zekrom chosen) and
    the slot holds a Pokemon, the slot is zeroed if the player has none of the forms that could hold it - 1068,
    1069 and the two Ultra Necrozma (1070, 1090; evolution table method 250) / 1099, 1100 / 995, 996.
  * "Has" is the game's own routine 0x09F03738 (r0 = species): party (after CalculatePlayerPartyCount), the 14
    boxes x 30 (GetBoxMonData: has species, not an egg), the two Day Care places (SB1+0x3030, +0x30BC). It is what
    lets Littleroot hand a lost legend out again (0x09F037C8), so it is the author's own idea of "gone".
  * 0x080D7098 (ClearBag's trampoline word, bagslots'; NewGameInitData's `bl` at 0x0808454E is its only caller) ->
    fx_newgame: zero 200 bytes at 0x0203D5E0 and 100 at 0x0203D800, then on to what the word held (clear_bag
    0x08FF606D).
  * Left as it was: a slot whose fused Pokemon the player has (a second fusion is refused, the slot byte for byte);
    Kyurem-WB (1119) has no part in any of it.
- **Tested** (`test_fusionfix.lua`, `test_fusionfix_newgame.lua`; every scenario also with OLD=1 on the unpatched
  build, where each healed case answers 3):
  * v15: the stray byte on an empty slot -> fuse answers 1; stored Solgaleo reading 894, and reading 845 -> split
    answers 1 and Solgaleo comes back; the same with the N-Lunarizer (883); the Unity Reins fuse and split as
    before; a second Necrozma while Dusk Mane is in the party -> 3, slot unchanged; N-Lunarizer on Dusk Mane -> 0.
  * gone_necrozma / gone_calyrex / gone_kyurem: fused form gone -> the fusion goes through. With the Black Kyurem
    still in the PC (box 1 on our save) the DNA Splicers answer 3 and leave the slot alone: the box scan sees it.
  * a v1.5 save carried over (made on the v1.5-era build: split, EV-IV Display, save from the Start menu), the
    item used through the SELECT popup and the party screen: unpatched "Multiple fusions are not allowed!",
    patched "Successful operation!", then split again the same way. DNA Splicers the same way: 3, then fuse 1 and
    split 4.
  * NEW GAME over our save: the three slots are empty 600 frames into the new game (unpatched: still Solgaleo and
    Zekrom); `test_bagslots_newgame.lua` still passes behind the chained hook.
  * The build differs from its input in the three words and the blob only. zhtext run again on top changes
    nothing (2,350 "already English"), so `fusionfix` then `zhtext` gives the same ROM; the patcher refuses a
    second run.
- GOTCHA: free space at 0x08FF75CC..0x08FF7800 (after namingkb) looks free, but graphics data elsewhere holds the
  aligned words 0x08FF7703 (at 0x09273FB4) and 0x08FF7785 (0x094530A8, 35A8, 36A8) - the same bytes in the original
  ROM, where the target was 0xFF, so chance matches - and a patcher's pointer check stops any blob that reaches them
  (at most 0x137 bytes fit before the first). The blob went to the hack's tail instead: 0x09FDCC80..0x09FDD400 has
  no aligned word pointing in.
- GOTCHA: the Thumb check's twin only replaces `.word` lines that carry a label, so every word of a table needs
  its own label; and a literal pool that does not start on a 4-byte boundary makes Keystone emit `ldr.w` (the
  patcher tries the source with and without one `mov r8, r8` pad).
- GOTCHA (test): after a split the party count is stale, so the test looks at all six slots; the script's
  messages need A, and a `use` step waits for the field (lock byte 0) before the next.
- **By design**: the Pokemon let go in case 3 is not given back. After a new game it belongs to the old save, and
  after a release the original game never returned it either. It is let go only at the moment a new fusion is
  asked for, never otherwise.
- **Not known**: which of the three the reporter had (no save). v1.5 plus one look at IVs is the likeliest; if the
  refusal survives this build, ask for the save - 0x0203D5E0 is in the overflow stream, not in SaveBlock1 / 2.
- Installed 2026-10-07 (sha1 86ad2d6f... = the working ROM cdc6346d + this patch), backup "(before fusion fix
  2026-10-07)"; every test above run again on a copy of the installed file. `roms/test-fusion/Necrozma fusion test
  (a v1.5 save)` is the same build with the carried-over v1.5 save (Necrozma and Solgaleo in the party, the stray
  byte in the slot; one party member was dropped to make room), for trying the report by hand.

## RELEASE v1.8 — 2026-10-07
- Everything since v1.7: `lmoveinfo`, `daynight`, `rngseed`, `expgain`, `namingkb`, `zhtext`, the Quest Log's
  Evolutions data and `fusionfix`. `qolversion`'s QOL is "1.8"; the Option title reads "+QoL1.8" (looked at;
  `docs/showcase/option-expgain.png` retaken on it).
- The release ROM is the chain's own output: the v1.4 archive + the shinybox two-byte edit + the 35 patches in
  HANDOFF's order (`fusionfix` before `zhtext`), 33 s. It is the ROM tested that day (sha1 86ad2d6f...) with one
  byte changed in each of the four title strings (0x08FF24E0.., the version digit). sha1
  ade383bab8682dd25676b3a1ea8a85b10ca97677.
- `release/hyper-emerald-en-qol.hpatch`: 4,455 runs, 922,577 bytes, made against the original ROM; applied to it,
  it gives that sha1 back.
- The data that was reserved at 0x09FBF800 / 0x09FC0000 is not in the build any more: `0x09FBC380..0x09FD2A00` is
  one free 0xFF run of 89.6 KB (zhtext's moved texts start at 0x09FD2A00), and the map slots it held (37/122-126,
  34/96-101, layouts 846-856) are free. With it gone, the same chain run from a checkout of the public repository
  builds the release ROM byte for byte - the first release that does (checked on the checkout the release was
  committed from).
- GOTCHA: a fresh checkout cannot run `questlog_patch.py` as it is: `evolutions.py` reads `moves.json` and
  `mapsections.json` from `tools/romdata/out/`, which is git-ignored. `python tools/romdata/dump_tables.py` with
  `HE_ROM` set writes them (from the 2026-10-01 build or from the release ROM: the chain's result is the same). Now in
  the README's list and in HANDOFF.
- Tested on the release ROM: the Option title, `test_fusionfix.lua` (four scenarios) and
  `test_fusionfix_newgame.lua`. Everything else in it is byte-identical to the build the day's batch ran on.
- Guide site: its tables regenerated from the release ROM. `build_site_data.py` gives 212 trainers the names
  `zhtext` gave them (they showed "(untranslated name)") and 30 more boss teams, which are matched by name (Steven,
  Volo, Lusamine, Faba, 26 under Champions); `species.json` / `forms.json` pick up the form names of 2026-10-02
  (the four Genesect Drives, both Gigantamax Urshifu, Toxtricity (Amped)). The Pokédex, moves, abilities, sprites,
  TM and Journal data came out identical. `PATCH_VERSION` 1.8, a v1.8 card, feature cards (move info, Day/Night,
  Exp. Gain, the naming keyboard, the last 2,341, fusions, resets) and FAQ entries (the Sound option, Day/Night,
  "Multiple fusions", soft resets; "set Sound to Mono" is gone - that row never was the sound). 1,196 pages, link
  check clean. The InfinityFree copy is rebuilt (largest page 887 KB) and still has to be uploaded by hand.
- GOTCHA: `tools/romdata/out/` and `site/src/data/{trainers,species,forms}.json` were from 2026-10-01/02, before
  `zhtext`: after a patch that changes names, run the `dump_*` / `scan_*` tools and `build_site_data.py` again.
- GitHub: `gh` is not on this PC. The release was made through the REST API with the token Git Credential Manager
  holds for github.com, after checking with GET /user that it is the project's account.
- Installed 2026-10-07 (sha1 ade383ba...), backup "(before v1.8 title 2026-10-07)".
- Published: public repo commit 41391be on main ("Release v1.8: ..."), tag v1.8, GitHub release with the patch
  and checksums. Checked from outside: the downloaded patch applied to the original is the installed ROM. The
  local branch `release-1.8` is that commit. The helpers stayed outside the repo, in `gba-trans/hyper-emerald/_testrun/rel18/`:
  `rebuild_chain.py` (the chain from the v1.4 archive; `CHAIN_REPO` builds from another checkout) and
  `mirror_public.py` (dev working copy -> public checkout; prints every passage it rewrites, dry run first).

## SPECIES TABLES: 1,200 -> 1,280 SLOTS — 2026-10-08 — `patches/speciesx/`
- Asked for: Gen 9 legendaries taken from another ROM hack (Crest). The hack has no free species slot (1199 is the
  only blank one) and every species table is exactly 1,200 entries with the next one starting on the next byte.
- **Status: a test build, not in the working ROM or the chain yet** (`roms/test-gen9/`). `speciesx` then `gen9` go
  LAST, after `zhtext`: zhtext still writes species names into the old name table, and speciesx copies the tables.
  A patch that runs after speciesx must take a species table's address from the ROM header (0x128-0x144, 0x1BC) or
  from `speciesx_patch.layout()`, never from the old addresses below.
- **The tables** (old address, bytes an entry, words that pointed at it):
  base stats 0x08F186E0 28 (74, + four field words: 0x0806EB7C +12, 0x0806EBA0 +14, 0x08070A08 / 0x08070AA4 +17) ·
  front pictures 0x08F20A20 8 (43) · back pictures 0x08F22FA0 8 (15) · palettes 0x08F25520 8 (6) · shiny palettes
  0x08F27AA0 8 (3) · icons 0x08F2A020 4 (3) · icon palette ids 0x08F2B2E0 1 (13) · names 0x08F2B790 11 (131) ·
  evolutions 0x08F387C0 40 (7) · front coordinates 0x08F44340 4 (15) · back coordinates 0x08F45600 4 (11) · front
  anim ids 0x08F468C0 1 (4) · anim delays 0x08F46D70 1 (2) · footprints 0x08F47220 4 (1) · elevation 0x08F4F560 1 (4)
  · National Dex no. 0x08F50370 2 (2) · Hoenn -> National 0x08F50CD0 2 (2) · Hoenn Dex no. 0x08F51630 2 (2) · back
  anim sets 0x08F51F90 1 (1) · front anim tables 0x08F52440 4 (5) · level-up pointers 0x09D89578 4 (14) · TM/HM bits
  0x08FCD8F4 16 (4) · tutor bits 0x09750000 16 (1; rows 0..1198, other data starts at row 1199).
  Four are indexed by species - 1 (anim ids, anim delays, both Dex number tables). Between the names and the
  evolutions (0x08F2EB20..0x08F387C0) is compressed graphics, not a table.
- New home: 0x0968D000..0x096C4A00, 1,280 entries each, 367 words repointed. The old tables are left as they were.
- **Left alone because long enough**: the cry tables 0x08F484E0 / 0x08F4BD20 (indexed by cry id; 386 ids are in use,
  388 and up are free - 666 species share cry id 274, the hack never gave Gen 4+ their cries); species -> cry id
  0x08F4FA10 (indexed by species - 277: 1,200 entries reach species 1476); abilities 0x097A0000 (three u16 a
  species; zeros follow).
- **The species count** in code, nine sites: 0x08FD5D60 and 0x08FD7C7C (`movs r4,#0x96; lsls r4,#3`: the TM/HM and
  tutor bit test returns 0 above it) · 0x092582BA (the egg-species walk back through the evolution table) ·
  literals 0x4AF at 0x09D00210 (which species a Mega goes back to), 0x09D45370, 0x09F006DC, 0x09F01C80
  (pre-evolution searches) · literals 0x4B0 at 0x080DE860 (SanitizeSpecies) and 0x09257F18 (Dex number -> species).
  Not raised, on purpose: 0x08FF12B2 (`movs r0,#0x4B; lsls r0,#4`), in a routine that fills gEnemyParty, which
  looks like a random species below 1,200. The clamps vanilla has on `species > NUM_SPECIES` are not there: the
  hack's author made those branches unconditional (GetIconSpecies 0x080D2E3A,
  GetMonSpritePalFromSpeciesAndPersonality 0x0806E750).
- **Which words are pointers.** A word equal to a table address is rewritten only when it is the ROM header's or a
  literal some `ldr rX,[pc,#n]` in front of it loads, inside the regions that hold code. That test alone finds the
  one false match: 0x092A14DC holds 0x09750000 inside graphics data. (The first prototype rewrote it.) The same
  test guards the free space: no code literal points into it. Words that merely look like addresses are common in
  the vanilla script area 0x081DB680..0x082E7000 and in sound data - not evidence of use.
- **Free space, a new kind.** The hack's upper 16 MB was padded with 0x00, not 0xFF: megabytes of it between the
  author's blocks, which sit at round addresses (0x09250000 Dex entries, 0x09750000 tutor bits, 0x097A0000
  abilities, 0x09D00000 the engine). Used: 0x0968D000..0x096C4A00 (speciesx) and 0x09A10000..0x09AB810C (gen9, third build), out
  of the zero runs 0x0968D000..0x096FFF00 and 0x099E5508..0x09D00000. Evidence they were unused: no code literal
  points in; they hold real data in every test below (boot, battles, menus, Dex, bag, PC, saving) and nothing reads
  differently for the old species. The FF runs the skill lists are too small for this (414 KB in all).
- **The Pokedex has room.** The hack's flag arrays are 120 bytes each (SaveBlock1 + 0x560 seen, + 0x5D8 caught):
  960 numbers. 906-959 were unused, their entries (0x09250000, 32 bytes a number) copies of Bulbasaur's. So new
  species get real entries with no change to the save - numbered 906 up, not their official numbers.
- `check_gen9.py before.gba after.gba` audits a build: every differing byte must be one of the intended changes,
  the first 1,200 entries of each moved table must equal the old table, the old tables must be untouched.
- Tested (`patches/gen9/test_gen9.lua`, helpers in `gba-trans/hyper-emerald/_testrun/gen9/`): 17 old species (Bulbasaur to the
  Galarian Zen Darmanitan, 1198) in a seeded wild battle read the same on the ROM before and after.

## GEN 9: LEGENDARIES, MYTHICALS, PARADOX POKEMON, THE BAXCALIBUR LINE — 2026-10-08 — `patches/gen9/`
- Asked for: "all gen 9 mythical and legendaries, including paradox", "faithful as possible but not high risk".
  38 species in slots 1200-1237, Dex 906-940, in National Dex order: Great Tusk to Iron Thorns (12), Frigibax /
  Arctibax / Baxcalibur, the four Treasures of Ruin, Roaring Moon, Iron Valiant, Koraidon, Miraidon, Walking Wake,
  Iron Leaves, the Loyal Three, Ogerpon in its four masks (four species, one Dex number), Gouging Fire, Raging
  Bolt, Iron Boulder, Iron Crown, Terapagos, Pecharunt. That is all 20 Paradox Pokemon; the Baxcalibur line is
  there because the user's "sudos" was read as pseudo-legendaries (not confirmed).
  **Nothing in the game hands them out yet** - that is the open decision.
- **Sources.** Numbers are the official Scarlet/Violet ones (`official.json`, from PokeAPI; `make_official.py`
  rebuilds it byte for byte): stats, types, abilities, level-up moves, everything each can learn, Dex text.
  Pictures, palettes, icons and cries come from the Crest ROM (third argument of the patcher, sha1 checked; not in
  the repository). Crest's own numbers are not used: its Miraidon never learns Electro Drift, Terapagos and
  Pecharunt have no ability.
- **Crest v1.0.F** is a pokeemerald-expansion build (about 1.7): BPEE, 31.1 MB, the vanilla ROM header at
  0x128-0x1BC still valid, 1,381 species, 36-byte species info, cries at 0x0901D3D8 (12 bytes, species - 1),
  elevation at 0x083A890C. Its Gen 9 front pictures are one 64x64 frame, like the hack's own late species
  (Terapagos's has two: the first is kept). It has six icon palettes, the hack three: ten icons are redrawn with
  the closest of the three (`fit_icon`).
- **Moves.** The engine's own, plus seven signature moves (ten ids, 938-947): the seven Crest has - Collision
  Course, Electro Drift, Ruination, Ivy Cudgel, Hydro Steam, Psyblade, Glaive Rush. Asked for on the second pass:
  "if Crest has 7, then try 7 ... try to match Crest for now". The other six of the thirteen (Burning Bulwark,
  Thunderclap, Mighty Cleave, Tachyon Cutter, Tera Starstorm, Malignant Chain) are in neither game and stay out
  of the lists; Snowscape is given as Hail. TM/HM and tutor bits: a bit is set when the Pokemon learns that move
  in Scarlet/Violet by any method (TM list 0x09E0FE80, 128; tutor list 0x08FD80B8, 127).
  - **How Crest has them** (read from its tables: 20-byte move rows 0x083D3940, names 0x083C703F, scripts by
    effect 0x08367AA8, animations 0x08332AF0). Collision Course / Electro Drift (effect 404), Hydro Steam (393),
    Psyblade (392) and Ivy Cudgel (414) run the plain-hit script and get their rule from the expansion's C
    damage code; Ruination is Super Fang's effect (40). Glaive Rush is effect 204, which 14 unfinished moves
    share: its script prints a message and ends (the expansion's placeholder), so in Crest the move does
    nothing. All seven share one animation with Crest's other Gen 9 moves. Crest gives Collision Course and
    Electro Drift 10 PP; the numbers here are Scarlet/Violet's (5).
  - **The engine's move tables** hold 938 moves (0-937; 676-729 are the Z-Moves, 937 a spare Petal Dance), but
    two of them were made for more and are written in place: the data at 0x09D86419 (12 bytes: effect, power,
    type, accuracy, PP, chance, target, priority, flags, an argument, 0 physical / 1 special / 2 status, a second
    argument; a plain hit has 0 and 9 in the two) is zero up to id 1023, and the animation pointers at 0x09D0AB00
    run to id 1029, the unused ones holding 0x09D0BB18. Four end at the last move with other data behind them and
    move to free space with 1,024 entries (63 words): names 0x09D30258 (13 bytes; 58 words; the Z-Moves' long
    names start 5 bytes after entry 937), description pointers 0x09D2AD00 (indexed move - 1; 2 words; 938
    entries, the last no move's), and two byte tables read with the move a Z-Move or Max Move was made from: Z
    power 0x09D8A838 (2 words; 932 entries, then the first record of another table) and Max power 0x09D86050
    (1 word; 929, then a table of stat changes). The first 938 bytes of each are copied as they read today.
  - Flags (byte 8): 0x01 contact, 0x02 Protect, 0x10 Mirror Move, 0x20 King's Rock, **0x40 high critical-hit
    ratio**. Effect 0 is a plain hit. **Effect 1 is "a set amount", and the engine picks the amount by the
    move's number** (0x09D63DFC: Sonic Boom, Seismic Toss, Dragon Rage, Night Shade, Psywave, Super Fang,
    Endeavor, Final Gambit, Nature's Madness; any other move gets 1). A move's type can be keyed by its number
    the same way (Revelation Dance is effect 0), which is why Ivy Cudgel is four ids, one type each, one for
    each of Ogerpon's four species.
  - Animations are borrowed: Close Combat, Volt Tackle, Night Daze, Wood Hammer / Crabhammer / Fire Punch /
    Stone Edge, Scald, Psycho Cut, Dragon Rush. Z power and Max power are filled in by the usual scale.
- **Booster Energy** is item 769, the first of the game's unused "New Item" rows (769-799: id set, pocket 1,
  type 4, field routine 0x080FE821 "cannot be used", text "?????"; items 0x08FC2C7C, 44 bytes; pictures
  0x08FCBFF4, {compressed 24x24 picture, compressed palette}, 800 entries). It gets a name, a text and Crest's
  picture of it (Crest's item 771; its items are 40 bytes at 0x08EB686C, pictures 0x08F70A30). No hold effect:
  gen9.s knows the item by its id. Nothing hands it out yet.
- **How the engine holds abilities** (found for this): the species table gives a 16-bit id. The battle engine keeps
  each battler's at 0x0203F000 + 2 * battler (0x0203F008 is the last one looked up); `gBattleMons[].ability` is
  only its low byte. The engine switches on the 16-bit value, so an id it does not list does nothing - Groudon
  given 326 (256 + Drought) summons no sun. The hack's own ids above 255 (Chilling Neigh 334...) work because its
  code names each. Two places read a species' ability for battle: 0x09D00110 (stores the one of the Pokemon coming
  in for gActiveBattler; called from the stubs at 0x09D000F8 / 0x09D00104 that Cmd_switchindataupdate and the
  battle intro jump to) and 0x09D73A9C (species, slot -> ability; 14 callers). The summary screen reads the table
  through the game's own GetAbilityBySpecies (0x0806B694 -> 0x09D73A80) and prints `names[id]` with a 16-bit id.
- **What gen9 does with that.** The ability name and text tables (0x09D03068, 13 bytes, and 0x09D00218; 342
  entries, code right behind) move to free space with 1,793 entries (ten words). Then six hooks, `gen9.s`:
  - `g9_enter` / `g9_lookup` replace 0x09D00110 and 0x09D73A9C (8-byte trampolines; both sites are 4-aligned
    leaf routines): an alias ability is handed to the engine as the ability it stands on. Aliases are 256 + base,
    so the one-byte paths agree: Orichalcum Pulse 326 (Drought), Hadron Engine 420 (Electric Surge), Toxic Chain
    399 (Poison Touch), Guard Dog 295 (Inner Focus), Tera Shell 487 (Shadow Shield), Poison Puppeteer 452
    (Merciless), Thermal Exchange 297 (Water Veil). The last five do exactly what their base does and show the
    base's own text; in battle messages the base's name appears.
    (Since 2026-10-21 none of this is used: each ability has an id of its own and the alias list is empty -
    *The Gen 9 abilities work in battle*.)
  - `g9_damage` is entry 5 of the engine's command table (0x09D77190; the live table is 0x09D7717C, 251 entries
    - the vanilla one at 0x0831BD10 is dead, its entries point into graphics). It runs the engine's damage
    command (0x09D6046C, which calls 0x09D5FF3C) and scales gBattleMoveDamage. The abilities: Orichalcum Pulse
    (Koraidon with Drought, physical, sun) and Hadron Engine (Miraidon with Electric Surge, special, Electric
    Terrain) x4/3; Sword / Beads of Ruin x4/3 and Tablets / Vessel of Ruin x3/4 (another battler has it, the one
    whose stat drops does not); Protosynthesis and Quark Drive x13/10 or x10/13 when the best stat is the one
    in play. The six are ids of their own with a low byte of 0 (512, 768, 1024, 1280, 1536, 1792): nothing else
    in the engine knows them. The moves: Hydro Steam x3 in sun (the engine has just halved it), Psyblade x3/2 on
    Electric Terrain, Collision Course / Electro Drift x4/3 when gMoveResultFlags (0x0202427C) has 0x02, super
    effective. Whole multiples are applied first, so that less is lost to rounding.
  - **The engine works type effectiveness out inside command 5.** Its scripts go critcalc, damagecalc,
    adjustnormaldamage (`04 05 07`, no `06`); command 6 is still the game's own Cmd_typecalc and is not on
    their path - a hook put there never ran.
  - Glaive Rush: `g9_damage` marks the user when the move is about to land (the command only runs after the
    accuracy check; the mark needs result flags 0x29 clear) and doubles what a marked target takes; `g9_cancel`,
    entry 0 of the command table (0x09D5783C, a battler starts on a move), takes the mark off that battler.
  - `g9_fixed` is entry 24 of the engine's second table of routines (0x09D79EAC, 220 entries; the command at
    0x09D686CC reads a 16-bit number from the script and calls that entry). It runs the set-amount routine and,
    for Ruination, stores half the target's HP (a quarter where the engine would quarter Super Fang's).
  - `g9_speed` stands in front of the engine's speed routine (0x09D5E3F0: battler in r0 -> its speed with
    stages, items and paralysis; 16 `bl` callers, no stack arguments). Its first instruction loads r3, so r3 is
    free at the entry: an 8-byte trampoline goes there, the four instructions it replaces are in
    `g9_speed_engine`, which carries on at +8 through r2 (dead once `str r2,[sp]` has run). x3/2 when
    Protosynthesis or Quark Drive is working and Speed is the holder's best stat.
  - Booster Energy: asking and using are apart. `g9_boosted` (asked by the damage and speed routines) only
    reads: the boost is on in the sun / on the terrain, or when the battler has used a Booster Energy since it
    came in (a flag), or holds one now. `g9_booster` does the using and runs only from `g9_cancel`, for every
    battler, when a real move starts: a holder whose ability the sun / terrain is not carrying loses the item in
    gBattleMons (+0x2E) and in the party (+0x22; the side from gBattlerPositions 0x02024076, the slot from
    gBattlerPartyIndexes 0x0202406E), and the flag keeps the boost on until the battler is replaced.
  - Abilities are read through the engine's own "is it in effect" test, 0x09D45AEC (battler, 0): 0 under Gastro
    Acid (bit 0x40 of the battler's byte +2 in the engine's struct) or with Neutralizing Gas (235) out.
  - The stats a move uses: its category, with the engine's exceptions (Body Press 759 attacks with Defense, Foul
    Play 492 with the target's Attack, Psyshock 473 / Psystrike 540 / Secret Sword 548 are taken on Defense).
    The Ruin abilities are (stat + 2) * 256 in the order Attack, Defense, Sp. Atk, Sp. Def, so the code works
    out which one matters from the stat.
  - Hydro Steam: x3 when the engine halved it (sun, a Water move by its current type, 0x09D4B164, and the target
    without a Utility Umbrella, hold effect 0xA4 through 0x09D68700 (battler, 1): the engine skips its whole
    weather modifier for that target at 0x09D5FFF0), else x3/2; nothing when the user holds the umbrella.
  - State: 8 bytes of EWRAM at 0x0203F130 (+0..3 a Booster Energy was used, +4..7 Glaive Rush's mark), cleared
    for a battler by `g9_enter`, which runs before anything reads them.
  - Helpers it uses: 0x09D45B84 (1 unless Cloud Nine or Air Lock is on the field); sun is gBattleWeather & 0x860;
    Electric Terrain is `*(*(0x02024218) + 0xD4) & 0x1E000` (its turn counter).
- **Where it is not the official rule** (all in gen9.s's header): stat stages are not counted when picking the
  best stat; a Booster Energy is used at the first move after its holder comes in, not on entry (its boost is
  there from the start), shows no message, and is not stopped by Embargo or Magic Room; attacks on a Glaive Rush
  user are not made sure to hit (that would mean the accuracy command, which also carries Protect); an
  attacker's Mold Breaker does not get past Tablets or Vessel of Ruin; Orichalcum Pulse and Hadron Engine travel
  as Drought and Electric Surge through Skill Swap, Trace and Role Play, and Protosynthesis and Quark Drive can
  be copied; moves that pick their category when used (Photon Geyser) go by their data; damage worked out
  elsewhere (confusion, Future Sight, the AI's estimates) is untouched; and the five stand-in aliases above.
  Terapagos is one species in its Terastal Form (the form it always has in battle; Normal and Stellar need
  Terastallizing) with the Normal Form's icon. Ogerpon's masks are four separate species: nothing switches them
  (the user: "left Ogerpon as is").
- **Tested** in mGBA on the build (`test_gen9.lua`; `MODE=`), each number the same battle with the same random
  numbers on a `--no-effects` build as the control:
  - `battle`: all 38 in a wild battle with our lead made the same species - pictures, names, types, stats, and
    the species' own cry sample found in the sound engine's RAM (run again after the second pass);
  - entry effects: Koraidon brings sun (ability 70 in the engine's array), Miraidon Electric Terrain (164);
    Groudon, Tapu Koko and Glastrier (334) as before;
  - `damage`, the abilities: 19 cases on two seeds - every ratio as intended (78 vs 59, 68 vs 51, 69 vs 92...),
    every case that should not change equal to the point, and the same numbers before and after the second pass;
  - `damage`, the moves (two seeds): Collision Course 218 vs 164 super effective, equal when neutral or
    resisted; Electro Drift 336 vs 252; Hydro Steam 81 vs 27 in sun (55 without), and equal when Rayquaza's Air
    Lock cancels the sun; Psyblade 88 vs 59 on terrain; Ruination 230 of 460 HP (1 on the control); the four
    Ivy Cudgels super effective on Blastoise, Charizard, Venusaur, Charizard; Koraidon's Collision Course 394 vs
    222 (16/9); Walking Wake's Hydro Steam in sun 128 vs 33; Iron Leaves' Psyblade on terrain 148 vs 76;
  - Booster Energy on Great Tusk: 54 vs 42 and the item gone from party and battle; kept when the sun was up
    before the battle's first events; kept by Rayquaza; the boost in both turns of a two-turn fight;
  - `duel` (the foe answers): Glaive Rush's user takes 132 vs 66 until it next moves and 66 after, both when it
    moves first and when the foe does; Iron Bundle on terrain, or with a Booster Energy, outruns a foe 20 Speed
    faster, not one 150 faster, and not without either; old set-damage moves (Super Fang, Seismic Toss, Dragon
    Rage) and turn order with nothing new involved are equal on both builds;
  - every new move's animation frame by frame, its name in the battle message and the move menu; summary pages
    (names, type icons, PP, power, accuracy, the two-line texts); Booster Energy in the bag (picture, text);
    wild Koraidon, Miraidon, Walking Wake and Iron Leaves choosing their signature move by themselves;
  - `give`: summary pages (ability names and texts, Dex numbers, level-up moves); `dex`: all 35 entries and the
    list's end; `catch`: Iron Moth with a ball, into the PC, Dex flags set; `evolve`: Frigibax -> Arctibax at 35,
    Arctibax -> Baxcalibur at 54, learning Glaive Rush as it evolves (level 0 in the list, the hack's own way);
    `tm`: Rest offered to Koraidon; `fight`: battles played to the end both ways; `save` / `check`: party, PC
    and Dex flags after a fresh start; `pc`: the storage screen on a box full of them; shiny colours (`SHINY=1`).
- **Not tested**: trainers using them, the Battle Frontier, contests, the Hall of Fame record, breeding in the
  Day Care (Frigibax's egg moves are appended to the list at 0x09D7973C and its bound at 0x08070464 raised;
  checked by `check_gen9.py`, not by an egg), abilities being copied, a new move as a Z-Move or Max Move (the
  two power tables are checked byte for byte, not played).
- **Independent review, and the third build (2026-10-08).** Three reviewers (Thumb code; patcher and data; game
  rules), each from the code and the disassembly alone. The patcher and the data were found sound (all 38 rows
  recomputed from official.json and equal; no table reference left behind). Four real problems, all fixed:
  - **Booster Energy was used inside the engine's look-ahead.** Each turn, during action selection, the engine
    copies gBattleMons aside, puts the Pokemon a battler would switch to into its slot (gBattlerPartyIndexes
    unchanged), asks for speeds (0x09D6BDCC, 0x09D6B678; the AI's damage estimate 0x09D6EEC4 reaches the speed
    routine through Gyro Ball / Electro Ball power) and copies gBattleMons back. A routine that uses the item
    while asked therefore left the flag set and the item held, or cleared the party item of the Pokemon whose
    index the slot still named. Seen in play: switching to a benched holder against trainer 1020 (a Bronzong
    with Gyro Ball) set the flag while the item stayed in battle and in the party. Fixed by splitting asking
    from using (above). Rule: in this engine, nothing that the speed or damage routines call may write.
  - Hydro Steam tripled against a Utility Umbrella; Gastro Acid and Neutralizing Gas did not switch the new
    abilities off; Body Press / Foul Play / Psyshock-type moves were counted by category. Fixed as above.
  - `check_gen9.py` only checked where bytes changed. It now also compares the number of repointed words with
    what the patchers expect (440), refuses a code literal still holding a moved table's old address, reads the
    nine count sites, and checks the six hook sites (all the engine's own, or all leading into gen9's code).
    Three planted faults (a move-name literal put back, a count site at 1,208, command 5 aimed at the header)
    each make it fail.
  Tested on the third build (`_testrun/gen9/moves.ps1` and `damage.ps1`, control vs fixed): every earlier
  number unchanged; Hydro Steam with the target's umbrella 82 vs 55; Koraidon's bonus gone under Gastro Acid
  and for its Body Press; Chien-Pao's Psyshock 60 vs 45 (Sword of Ruin), Chi-Yu's unchanged; a Booster Energy
  handed over mid-battle in a trainer battle and the benched-holder switch both end with the item gone from
  battle and party and nothing else touched; two double battles (a second Pokemon's Booster Energy used, the
  lead's Leftovers kept; Glaive Rush's mark on battler 2); all 38 species again; Arctibax -> Baxcalibur with
  Glaive Rush. One ability case differed by 1 HP: the hit landed two frames later, so the roll differed; with
  the random numbers held fixed until the hit (`PINRNG=1`) the control, the second and the third build all
  deal 32.
- **GOTCHAS**
  - Comparing two builds: different code can make a turn a frame or two longer, and the damage roll moves with
    the frame. Hold the random numbers (`PINRNG=1`) before reading a 1-HP difference as a bug.
  - A wild Pokemon's AI does not think ahead; a trainer's does. Anything about the engine's look-ahead has to be
    tested in a trainer battle (`duel` with `TRAINER=`).
  - A test that compares two builds needs the same Pokemon in both: `givemon` and a wild battle draw IVs and
    nature from the random numbers, and `rngseed` starts them from the clock. Write 0x03005D80 before each.
  - The damage roll is drawn when the hit lands, and the random numbers step every frame: if the foe strikes
    first and its damage differs between the builds, its HP bar drains for a different number of frames and our
    roll changes. `MODE=damage` puts the foe to sleep.
  - A hit cannot take more than the HP that is left: against a foe it knocks out, both builds read the same
    number. Use a level 100 Snorlax. A wild Snorlax holds Leftovers: read a hit as it lands, not at the turn's end.
  - Rayquaza's Air Lock cancels the weather for everyone, the test's sun included: it is the wrong user for a sun
    test (and the right one to see that Hydro Steam is then not tripled either).
  - A wild Pokemon picks its move as the action menu comes up, from its party data: to give it one move, write
    gEnemyParty on the battle's first frame (`FOEMOVE`). Writing gBattleMons at the menu is too late.
  - The engine asks for speeds before the battle's first events. A sun written at the menu comes after a Booster
    Energy has gone; `EARLY=1` writes it from the intro.
  - With the literal pool off a 4-byte boundary keystone does not fail: it reaches the pool with `ldr.w`. The
    Thumb check catches it; the patcher tries each padding (gen9.s has two pools: a load reaches 1020 bytes).
  - PowerShell `Start-Process -ArgumentList` does not quote: a ROM name with a space reaches mGBA as two
    arguments and the script never runs. Run Python that reads the Crest ROM or the PokeAPI files with `-I`
    (which also ignores PYTHONIOENCODING and leaves the script's folder off the path: gen9_patch.py adds it).
- **Still to do before it ships**: a way to obtain them and Booster Energy (one cheap way for the item: the two
  held-item fields of the Paradox Pokemon's base stats, so that wild ones can carry it; PokeAPI has no held-item
  data for them to copy); Ogerpon's masks - the held-item form table at 0x09E0FC70 could switch them if the
  masks become items; `tools/build_pokedex.py`,
  `build_sprites.py`, `romdata/forms.py` and `patches/questlog/evolutions.py` hold 1,200 and the old table
  addresses, so the guide and the Quest Log do not see the new species yet; README and CHANGELOG once it is in
  the chain.

## HISUI MAP: NO FLYING — 2026-10-08 — `patches/hisuimap/`
- Asked for: "prohibit the use of flying Hisui, since it can skip several flags cuz the game bug, still open the
  map". In Hisui the Sinnoh Map's A ran Mingyao's Braviary block for the square (showmonpic, waitbuttonpress,
  hidemonpic, warp 37.<map> 1), and those blocks check nothing, so it took you to any Hisui area ahead of the story.
- `HISUI_FLY = False`: the Hisui region record's fly table (H_FLY) now starts with its end mark, 0xFF, in place of the
  first entry's key (107, Snowfall Hot Spring). courier_for finds no entry, so fly_target answers 0 (A does
  nothing) and draw_name prints every name plain (no entry means "not a fly stop", the same as a Sinnoh route).
  The table keeps its size: nothing after it moves. Sinnoh's record is untouched. Mingyao's own menu (multichoice
  137) is the game's and still flies; only the map's shortcut is gone.
- Chain rebuild (`_testrun/rel18/rebuild_chain.py`): before the change it gave the installed v1.8 ROM byte for byte
  (sha1 ade383ba...); after it, one byte differs: 0x08FF544C, 0x6B -> 0xFF. The same single byte separates the Gen 9
  and Area Zero builds made on top (speciesx, gen9, check_gen9 clean, paldea) from the ones before.
- Tested (`test_nofly_hisui.lua`, run by `_testrun/hisuifly/run.ps1`, the working save), old build as the control:
  in Hisui (37/106) A on Coronet Highlands and on Firespit Island closed the map and flew you (old) / did nothing,
  the map stayed up with the names right (new); B back on the same tile; Sinnoh, Oreburgh -> A on Jubilife flies to
  36/2 on both.
- Installed 2026-10-08 (sha1 742ae12b...), backup "(before Hisui no-fly 2026-10-08)" with the .sav. The Gen 9 test
  ROM (roms/test-gen9, now sha1 cd311786...) and Area Zero test 5 (roms/test-paldea, b5e0b95a...) carry it.
- Since 2026-10-22 a later step, `hisuifly`, gives the places back, each needing flag 0x431E (after Volo): *The
  Hisui map flies again, after Volo*. hisuimap itself is unchanged.

## AREA ZERO: THE PALDEA AREA FOR THE GEN 9 BUILD — 2026-10-08 — `patches/paldea/`

- Asked for: where the Gen 9 Pokemon are found. The user wanted "a mini location for Paldea region like theme
  future and past", optional after Team Rainbow Rocket, with existing or new minor characters only ("I don't wanna
  use Colress and Dulse ... it should be unimportantn npcs or new npc"), Jacq at "custom darkhole maybe like some
  students got sucked from it after ultrawormhole", "medium but faintful like should be event about stupid sandwich
  as well". The story (revision 2, approved; `story.py` says it in full) and the research behind it are in
  `gba-trans/hyper-emerald/_testrun/gen9/paldea/`. On test 6 the user asked for "the npcs and story" and then "let go full mode
  now": test 7 has all of it.
- Goes after gen9 (it needs species 1200-1237). Data at `0x09FBC400..0x09FCBF38` on test 16 (62.8 KB of the 0xFF
  run `0x09FBC380..0x09FD2A00`, blank in the hack's own ROM; 26.7 KB left): seventeen map layouts (the thirteen maps
  and the four strips past the crater's edges: *Test 14*, *Test 15*), tinted tileset copies, the copied
  layout and group-35 tables, events, scripts, texts, four trainer parties. Its sprites are a block of their own,
  `0x09FF1000..0x09FFB608` (41.5 KB; to `0x09FFBF5C`, 43.8 KB, with the time rift of 2026-10-12; `0x09FF1000..0x09FFC000` kept for it) in the ROM's free tail (0xFF from
  fusionfix's end `0x09FDCE38` to the end of the ROM; the aligned words that seem to point into the tail are a
  number compared in vanilla code at `0x0802BF0A`, 0x09FE0000, and bytes of pictures and text).
- **The story in the game** (flags in story.py):
  - Mossdeep City (0/6; the Timeless Woods, 34/67, up to test 15: *Test 16*): Jacq and the hole (shown after
    0x41D5). ON_FRAME (stage 3) plays the ending with
    Arven, Nemona and Penny there (F_HIDE_HOME cleared for it): Jacq gives a Master Ball, they say they are going
    back in, a fade, all four are taken off the map, stage 4. From then on they live in the research stations
    (test 11; up to test 10 they stayed by the hole, and the user: "those 4 standing blocking the way").
  - Research Station No. 1 (the wall): Penny. Every station's recorder (left counter) plays its log and sets
    F_LOGS[k]. Penny gives the next missing station's whereabouts; with all four she opens the Zero Lab
    (F_LAB_OPEN: unlocked. The door is a shutter until Arven and Nemona stand at it: *The lab's door*, below).
  - Arven at the picnic (both eras, one script each, shared flags): first meeting, then "the Titan is in the den";
    with the Titan beaten the sandwich (fade, heal jingle, the legend's cry: F_KORAIDON_UP / F_MIRAIDON_UP).
  - **Arven and Nemona go to the lab's door by themselves** when both legends are up, Nemona is beaten and the lab
    is open: F_GUARDS_UP set (their picnic / field objects' hide flag), F_HIDE_GUARDS cleared (the door pair's).
    Whichever of the four comes last does it: Arven's script after the second sandwich, Nemona's after her battle
    (both: a fade, removeobject / addobject for the people on this map), or, for Penny's (she is on another
    map), the next map script: `state` works F_GUARDS_UP out on the way into every map (test 10: `guards_check`
    in the craters' ON_TRANSITION). **Test 9 did it only in Arven's script, and the
    lab's machine asked for F_GUARDS_UP**: the user talked to Arven before the logs were done ("the order of
    mine"), opened the lab, and got "VISITOR NOT AUTHORIZED" from the machine with nothing saying that Arven had
    to be talked to once more (and a terminal beside it saying "Visitor authorized"). Now nobody has to be talked
    to twice, and what is still missing is said in words: Penny (on opening the lab, and after) and the machine
    give a line for each of Koraidon, Miraidon and Nemona that is not done, with where to go.
  - The Titans (den, between two crystals): two wild battles (lv 68, then lv 72 with Leftovers after "it ate the
    herb"), each with the Totems' flags set around it (0x272: the battle refuses Poke Balls as a trainer battle
    does, read at 0x09D6115E; 0x273: a loss is not a white-out, the script heals you), GetBattleOutcome (special
    183) checked; a flag per Titan remembers the first win (0x43D2 / 0x43D3). The Titan's object hides by its done
    flag (removeobject sets it).
  - Nemona (the future, in the tall grass south of the waterfall's pond): `trainerbattle 3` (no intro), then
    F_BEAT_NEMONA.
  - The Zero Lab's machine (the glass cylinder, read from below): with both legends up and Nemona beaten (the
    open door is how you got in; it sets F_GUARDS_UP itself, for a save made in the lab) the finale: the AIs appear
    (clearflag F_HIDE_LAB_CAST, addobject), heal, AI Sada, heal, AI Turo, the Protocol (a camera shake; you step
    back two tiles and the lab's Koraidon and Miraidon come up behind you at 4,9 and 8,9, facing you: at 4,10 and
    9,10, test 9's places, they were below the screen), heal, the Protocol's double battle, both AIs gone in a white flash; then
    F_STORY_DONE, the door pair hidden again, the students shown at home, the post-story legends shown, stage 3,
    `warpteleport` to the woods. A white-out on the way sends you to a Pokemon Center; the machine starts the
    finale again. (The white-out leaves F_HIDE_LAB_CAST cleared, so the lab's ON_TRANSITION sets it each time you
    come in: otherwise the AIs and both guardians would be standing there before the machine is touched.)
  - After the story: the picnic legends (the same objects: their script asks to battle; caught -> removeobject),
    six Paradox legends in the craters, Roaring Moon and Iron Valiant in the Crystal Cavern, Terapagos in the
    Underdepths (the cavern's ladder, whose crystal hides by F_STORY_DONE), the Ruinous four as themselves (test 11:
    Chien-Pao in the icy cave; Wo-Chien, Ting-Lu and Chi-Yu in the Crystal Cavern; up to test 10 they were stone
    stakes in a Sealed Shrine). Caught = gone; knocked out = still there. Penny in Station No. 1 says where the
    legends are; Arven in No. 2 (his sandwiches heal), Nemona in No. 3 (a rematch, as often as you like) and Jacq
    in No. 4 hide by F_HIDE_RESIDENTS until the ending is over.
  - **Who is to be seen is worked out, not kept** (test 11). `state`, a subroutine every Area Zero map's
    ON_TRANSITION and ON_RESUME call (the woods' too, then `woods_state`), sets or clears every hide flag that only
    says "shown later" or "gone again" from the story's own flags and the stage: the door pair (F_HIDE_GUARDS, and
    F_GUARDS_UP itself once everything it stands for is done), the post-story legends until F_STORY_DONE, the
    students in the woods (stage 3 only), Jacq in the woods (0x41D5 until stage 4), the residents (stage 4). So a
    save from any older build shows the right people, and no order of doing things can leave a flag behind. Tests
    7-10 kept these as flags set once (F_INIT) and by whichever conversation came last. ON_RESUME matters:
    Continue does not run ON_TRANSITION (test 7 showed the ending's students beside Jacq on the user's save). It
    runs in ResumeMap, before the saved objects are put back, so `removeobject` there takes a saved one off the
    map (the four people a test 10 save made after the ending has standing in the woods).
- **The hole's sprite**: the hack's sprite table entry 125 (blank, no map uses it) is overwritten in place with a
  copy of main sprite 168's info (the dark vortex of Hisui 37/104 and Hearthome 37/73, 32x32) and palette tag
  0x1119 (deep indigo; the vortex's own 0x1106 is pink). Entry 126 is the hack's crystal shard (its sprite 20,
  16x32) in 0x1111 (pale and glassy: the time crystal up to 2026-10-11; the craters have the time rift since, and the entry is still written for a save's copy of a crater from before). Decorative crystals: the red shard (22) in the past, the
  black one (21) in the future, the purple one (20) in the caves.
- **Sprites of its own** (`mons.py`, `sprites/`). Tests 1-9 stood Koraidon, Miraidon and the Titans on the map as
  their 64x64 battle pictures and borrowed Suicune, Entei and so on for the post-story legends; the user: "cannot
  we use sprite from the other game? cuz right now it is too big, should not it be sprite?". Now all seventeen
  (thirteen on test 10; the Ruinous four on test 11: "cannot we just use the sprite instead of the statue?") are
  the overworld sprites pokeemerald-expansion gives them (rh-hideout/pokeemerald-expansion,
  `graphics/pokemon/<name>/overworld.png` and `overworld_normal.pal`, fetched 2026-10-08, kept in `sprites/src/`;
  that project's artists drew them, credit them if this is released): six square frames a sheet (down, down
  stepping, up, up stepping, left, left stepping), 16 colours. Most are 32x32; Koraidon, Miraidon and Raging Bolt
  64x64 with the drawing about 44x48. `sprites/convert.py` (needs PIL; run once) writes the three standing frames
  as `<name>.4bpp` and the colours as `<name>.gbapal`; the patch reads only those.
  - **Slots**: the hack's sprite table (0x0839CF00, 0x24 an entry, graphics 0x4E + the template's fourth byte) has
    room for 256 entries. 0-239 are the hack's; 240-255 are 576 bytes of 0x0F that nothing points at (the next
    table starts right after, at 0x0839F300), and the lookup (0x094A2BCE) has no bound. Ours: 127, 212, 225, 227
    (the blank 16x32 entries tests 1-9 already used: Koraidon, Miraidon, Great Tusk, Iron Treads; 217 looks blank
    but Ever Grande 16/8 places it) and 240-253 (Walking Wake, Gouging Fire, Raging Bolt, Iron Leaves, Iron
    Boulder, Iron Crown, Roaring Moon, Iron Valiant, Terapagos, the recorder, Wo-Chien, Chien-Pao, Ting-Lu,
    Chi-Yu); 254 and 255 were free up to 2026-10-12 and are the time rift now (*The time rift*): none is left. An entry is a copy of one of the
    hack's of the same size (32x32 Suicune 73, 64x64 Giratina 83, 16x32 a shard 20: its OAM and subsprites) with
    our palette tag and frames, the standard animation table (0x08509100: frames 0 down, 1 up, 2 left, mirrored
    for right, 3-8 the steps) so that `faceplayer` turns it, nine frame entries (the steps are the standing
    frames again: nothing walks), not inanimate, no footprints. The recorder keeps still (the animation table of
    the clipboard, sprite 28).
  - **Palettes**: the hack gives every object palette by its tag, not by the entry's slot: 0x0808DA02 jumps to
    0x094A3354 for every slot but 0 and 10, and 0x094A356A finds the tag among sprite palettes 4-9 or loads it
    into a free one of those (so six object palettes at a time; a seventh goes to 10). The tag is looked up in
    vanilla's table (0x0850BBC8, {pointer, tag} x 35 and a zero row; six of its rows point at 0x08FFFFFF) by
    vanilla's code, which holds the table's address in three words: 0x0808E8BC (LoadObjectEventPalette), 0x0808E950
    (PatchObjectPalette), 0x0808E9A8 (FindObjectEventPaletteIndexByTag). The table is full, so it is copied into
    our block with eighteen rows added (tags 0x1124-0x1135) and those three words point at the copy. The copy
    ends in tag 0x11FF, the one the search stops at; vanilla forgot it (its last row is zeros), so a search for a
    tag that is not there ran on into the data after the table. Tests 1-9 used four of the 0x08FFFFFF rows
    instead; the vanilla table is left alone now.
  - **A reflection on dry land**: the game mirrors a sprite below itself when a reflective tile (pond water,
    behaviour 0x10) lies under it: (width + 8) / 16 - 1 columns either side and (height + 8) / 16 rows down
    (0x08096A8C; a 64x64 sprite: three columns each way, four rows), whatever is in between. The mirror image is
    hidden by ordinary ground but not by tiles whose picture is on the bottom layer (the picnic's dirt): Koraidon
    at 34,42 and then at 35,42 (the lake's shore is 33) had its feelers lying upside down on the picnic. The
    legend stands at 39,42 now. Keep a 64x64 sprite four columns from pond water that is level with it or below.
  - **Standing behind one**: a 64x64 sprite covers the two tiles above its own; the tile behind Koraidon /
    Miraidon and Raging Bolt holds a rock (`world.rock`, put wherever places.py stands them), or you could talk
    to it while hidden.
  - The Sealed Shrine's stakes (the hack's stone statue, 23) went with the shrine in test 11.
- **People** (main sprites, stand-ins): Jacq 9, Arven 37, Nemona 20, Penny 58, AI Sada 202, AI Turo 46.
- **Trainers**: entries 952 (Nemona: class 38 Champion, pic 194), 943 (AI Sada: new class 71 "Professor", pic 218),
  947 (AI Turo: class 71, pic 31), 958 ("Protocol": new class 72 "Paradise", pic 146, a double battle: Koraidon
  and Miraidon lv 78). The four slots are ones no script names. Class names go in
  the 0xFF space after the game's 71 (0x0830FCD4 + 13 * class). Parties: custom moves and items (flags 3), IV
  field 114 as the hack's bosses, moves by the ROM's own names (cut: "Coll. Course", "ElectroDrift", "U-Turn",
  "Dazzle Gleam", "MysticalFire", "1st Impress."). Nemona lv 72-74 (Lycanroc, Goodra, Iron Hands, Iron Bundle,
  Baxcalibur); the AIs lv 75-77 with Scarlet's and Violet's Area Zero teams, Booster Energy on Roaring Moon and
  Iron Valiant. Booster Energy gets a price (5000; gen9 left it 0) for the lab's shop (`pokemart`).
- **New maps** (maps.py), group 35, layout ids 846-857: 35/89 the wall, 35/90 and 35/91 the crater
  in the past and in the future, 35/92, 93, 97, 98 Research Stations No. 1-4, 35/94 the Crystal Cavern, 35/95 the
  icy cave, 35/96 the Zero Lab, 35/99 the old Sealed Shrine (empty since test 11 and with no way in: kept so that 35/100
  keeps its number and a save made inside it still loads; its way out leads to the wall), 35/100 the Underdepths (the first eight keep test 6's
  numbers). Group 35, not 34/37: a save parked in a map of groups 34/37 that an older build had cannot load into one of these. The
  first builds copied the unused cliff 34/27 and the Giant Chasm 34/79 whole; the user: "the cliff is kinda too
  big to walk", "this is just a copy paste with is boring". Both are drawn new by `world.py`:
  - **The wall** (27x30, General + NavelRock, tint "zero" grey-green, music 479, place-name popup on): 34/27's sky
    and summit on top, rock seen from above (529) and the rock face (537); three ledges (540 | 529 ... | 539, the
    lip under each 536 | 537 | 538), ladders 516 (height 0), five cave mouths 523 524 525 / 531 532 533 (only 532
    walkable, height 0): the hole, Station No. 1 and the icy cave, the Sealed Shrine and the way down.
  - **The crater** (52x44, General + Petalburg, tints "past" / "future", music 381 / 501), painted from a sketch
    (`Sketch`, `paint()`): land above 113, the north wall's face 121, grass 1 (sometimes 399 / 437 / 4), tall grass
    13, flowers 4, boulders 224, trees as the Chasm has them (2 wide, 3 tall, even columns: 462 463 / 454 455 /
    494 495, then 470 471 and 484 485, 468 469 where two meet), ponds as Route 102 (176 177 178 / 184 161 186, the
    shore 203 204 205 below, widening only), dirt with every corner (464-466 / 472-474 / 480-482, 456-459).
    **Heights**: a level per tile, LEVEL_STEP 2 (floor 3, then 5, 7: at an even height the game draws people in
    front of the map's top layer). Terraces are cut-corner blocks (`Sketch.blob`): top corners cut two tiles per
    row, bottom corners three. Every raised tile with a lower neighbour is an edge, drawn as the hack's Hisui maps
    (37/103) draw theirs: rim 153 (walked on), corners 108 / 129, sides 116 / 137, face 100 with round ends 124 /
    145, where the edge turns inwards 140 / 139 above and 132 / 131 below, steps 207 (height 0) on a face (tests
    1-12 had 136 / 138, 122 / 125 and 124 / 145 there: the rock family's pieces, see *Test 13*). **A face one tile long
    is drawn as a round end beside an inner corner and reads as a loose boulder** (the user's screenshot of test
    6: "the tiles are miss align"): `paint()` refuses any face shorter than 3 or rim shorter than 2 on one level
    and row (`edge_problems`). Woods and the wall count as level 9: no edge against them.
    Copied pieces: the Chasm's north stairs and mouth (its x 42-52, y 0-8) and two of Petalburg's houses (its x
    8-13, y 14-18; door 647 at height 0) for Stations No. 2 and 3, their floor (height 3 there) set to the height
    around them; mouths 159 over 167 (height 0) for the Crystal Cavern, the Zero Lab and Station No. 4.
    **The waterfall** is Route 119's (0/34): a river on the land above (400 368 402), the lip (187 179 188), the
    falling water (185) down the wall's other three rows, the splash (193 across; Route 119's ends 376 / 377 carry
    a bank each and stood in the middle of the pond until test 13) on the pond's top row. All of
    it open water at height 1: Waterfall climbs it (the field effect walks up while the tile is a waterfall and
    stops on the river), coming down it pushes you south (vanilla's forced movement on waterfall tiles). Test 6
    had it solid: the climb ended on the river at the top with water and rock all round - stuck (the user). Test
    8 put Station No. 4 in a mouth in a little cliff on the sand above the wall; the user: "what the hex is up
    there? this is half cheap work". So the map is 8 rows taller (TOP): the floor is sketched as before
    (`crater_floor`, its own coordinates) and moved down; above it the rim's woods and a **hanging valley**
    (x 24-41, rows 3-9): a meadow closed in by trees, the river from a spring (the pool's top edge 392 393 394)
    to the lip, Research Station No. 4 as a Petalburg house, tall grass, crystals, and the rim (row 10, plateau
    113 walked on, sketch "=") as a lookout over the crater.
  - **The rooms** are rooms the game has, copied whole (layout and tilesets, recoloured where marked) with new
    events: the stations the lab room 35/13 (no warp leads to it; door mat 571 572 at 9-10,8; the space behind its
    counters is shut off, so the cot is a sign on the right counter; its PC, behaviour 0x83 at 5,1, opens the
    game's own PC). The log is an object you can see on the left counter and the note one on the table (a
    clipboard ext 28, a bag main 97, a paper ext 28, an open book ext 27): test 8 had both as signs on bare
    tiles, and the user tried the PC for the log ("it is just a normal PC storage?") and found the table
    answering with no book on it. The log's object was main sprite 88 on tests 8 and 9, taken for a small machine
    at catalogue size: it is Mr. Briney's boat seen from the front (the user: "why use the ship sprite for
    recorder?"). The game has no machine among its sprites, so the recorder is drawn for the patch
    (`sprites/convert.py`: a tape machine, two reels and a display, 16x32 with its foot on the counter's front
    edge; sprite 249). The Crystal Cavern is a Mt. Coronet room 36/82 ("crystal"; mouth 774 at 3,1, ladder 575 at
    6,11), the icy cave an Iron Island room 36/65 ("ice"; way out 758 at 6,8), the Zero Lab the Rocket Hideout's
    lab 34/75 ("future"; its pad 627 is behaviour 0x70 and warps as you step on it), the Sealed Shrine a Regigigas
    Temple room 36/74 ("past"; way out 572 at 8,12), the Underdepths a Mt. Coronet chamber 36/94 ("tera": its lava
    pool turns to crystal light; way out 734 at 12,21). The patch checks each room's size and those tiles.
- **Map section 186** ("Route 224", no map uses it, and its name string is its own) points at "Area Zero".
- **Warps**: the hole and the way back are object scripts (`warpteleport`). The wall: 0 the lowest mouth -> the
  past crater, 1 Station No. 1, 2 the icy cave (3 was the Sealed Shrine up to test 10). Each crater: 0 its north mouth -> the wall,
  1 Station No. 2, 2 the Crystal Cavern, 3 the Zero Lab, 4 Station No. 3, 5 Station No. 4. The cavern's ladder ->
  the Underdepths. Every room's way out is MAP_DYNAMIC (127/127): entering by a warp whose target warp is dynamic
  stores the map and warp you came by, so one room serves both eras.
- **Time crystals** (drawn as a time rift since 2026-10-12: *The time rift*; on the dais at 26,30 and on the north-east platform at 45,20, map coordinates): `getplayerxy 0x8004, 0x8005`
  and `warpteleport` to the other era with those vars: you arrive where you stood.
- **Wild tables**: gWildMonHeaders (0x08E17D50, 254 headers) ends at 0x08E19128 in a terminator followed by 68
  bytes of 0xFF, nothing pointing in before 0x08E19180. Three headers (35/90, 35/91, 35/95) where the terminator
  was, then the terminator: that space is full. Land rate 20, levels 63-67: the six Paradox Pokemon of each era;
  the icy cave the Frigibax line (Baxcalibur 4%), Glalie, Froslass, Weavile, Mamoswine, Abomasnow, Beartic,
  Avalugg, Iron Bundle 1%.
- **State**: flags 0x43AB-0x43BE and 0x43C0-0x43D6 (all taken; 0x43B0, the old F_INIT, is set in
  older saves and left alone; 0x43D6 says which crater you were last in) and vars 0x40A8 (0 nothing, 1 met Jacq, 2 in Area Zero, 3 on the way home, 4 the
  ending over) and 0x40F9 (the build's stamp: *Positions are data*), checked unused on the Gen 9 build (scripts,
  object hide flags, aligned literals, the saves). 0x43BF is not free. story.py lists each.
- **GOTCHAS**
  - An object takes the height of the tile it stands on (1 on water): A from the shore then offers Surf. Objects
    here are placed at height 0 (they answer at any height) or the room's 3.
  - A copied piece keeps its heights: the Chasm's stairs and the houses came in at 3 and would have walled the
    shelf off. `crater()` sets their floor to the height around them. A house's door must face a plain floor tile:
    Station No. 3 first stood where its doorstep was an inner corner (solid).
  - A 64x64 sprite is drawn up from its tile and 4 tiles wide (tests 1-9: Great Tusk's battle picture hid one of
    its two crystals until they moved a tile further out). It mirrors itself below when pond water is within
    three columns, and it covers whoever stands behind it: see *Sprites of its own*.
  - A sprite picked from a numbered sheet at catalogue size can be something else entirely (main 88, "a small
    machine", was a boat). Look at it at 4x, and in the game, before it stands for something.
  - A message that reads like a lock ("VISITOR NOT AUTHORIZED") must say how it opens. Whatever a step needs is
    checked where the step is taken, not through a flag another conversation sets.
  - A post-story Pokemon must not close a corridor with the crystals beside it: Roaring Moon at 11,3 of the cavern
    did (found by the post-story test).
  - Waterfall tiles must be open water, or the climb strands you at the top.
  - Anything that answers A must be something you can see: a sign on a bare counter or table tile reads as a bug.
  - The crater's map coordinates are the floor's plus TOP (8): (26,22) in crater_floor is (26,30) on the map.
  - Tests: walking tests refresh a running-low Repel (its "use another?" prompt stops a walk); scripted battles go
    through a "fight" step (A mashed, our battlers pinned at 9999 with full HP and Dark Pulse); a multi-tile
    "step" on land can overshoot (running), so walks are used there; mashing A in front of a PC reopens it.
- **Tested** (mGBA dev, hidden; `_testrun/paldea/run.ps1` with `test_paldea.lua`; `run_all.ps1` runs a list, each
  from the same save, and keeps each run's log and pictures), on test 10: test_story1-5 walk the whole story and
  the post-story (Penny and logs, Arven, both Titans twice, both sandwiches, Nemona's battle, the waterfall up
  and down with Station No. 4, Penny opening the lab, Arven and Nemona at its door, the finale's three battles,
  the ending and Jacq's gift, the picnic legend, Walking Wake, Wo-Chien, the ladder to the Underdepths and
  Terapagos); **the orders**: test_story6 is the user's (Arven talked to when only a log is missing, the door
  still shut, the log, up to Penny, back down: the pair at the door, the finale), test_story7 Nemona last (Penny
  and the machine say she is missing, nobody at the door, her battle sends them), test_story8 a sandwich last
  (Arven goes straight on to "let's finish this"); test_steps_whiteout (the cast's flag left cleared: hidden
  again on the way in); test_steps (the way in, Station No. 1, the icy cave and a wild battle, home),
  test_steps_crater (both time crystals, a wild battle each era, the lab, Station No. 2's cot / note / log / PC,
  the cavern), test_steps_save (save in the crater, Continue), test_steps_before (the woods before the arc) all
  pass, with flag and who-is-on-the-map checks ("expect" steps stop the run when wrong); test_steps_continue loads
  the user's own save (no setup) and checks nobody from the ending is in the woods. test_steps_tour and
  test_steps_sprites (every sprite of ours, Koraidon and Miraidon talked to from three sides) take pictures.
  Test builds in `gba-trans/hyper-emerald/roms/test-paldea/` with a map guide (`map_guide.py`: gold during the story, green
  ways in and out, cyan after it; objects drawn, hidden ones too).
- **A second save beside test 10**: the user played test 9 up to the lab without saving (the .sav in the folder
  was never written after it was put there), so that play is gone. `make_save_lab_door.lua`, run on a copy of
  their own save, sets the story's flags up to the finale, warps to the lab's door and saves from the Start menu
  (the Repel counter left alone); `test_save_lab_door.lua` continues from that save and plays the finale. It is
  offered as a second copy of the ROM with that save, next to the usual one with their own.
- **Test 11 (2026-10-08): the user's five notes on test 10.** "walkingwake should be on top of the waterfall":
  it stands on the river above the falls (33,7), water on all four sides, and is talked to from a surfing
  Pokemon. "the door should be prohibited to enter until those two are at the door": *The lab's door*. "can I
  edit the placement myself???": *Positions are data*. "Chien Pao should be in the icy cave, and the other 3
  should be in Crystal cave", as sprites: done, the shrine emptied. "those 4 standing blocking the way ... let
  them be in the area zero houses?": they leave after the ending's last line and live in the stations.
- **The lab's door**: Penny unlocks it (F_LAB_OPEN) but it stays a shutter until F_GUARDS_UP, which `state` sets
  once both legends are up, Nemona is beaten and the lab is unlocked; whoever of the four comes last also fades
  the screen and puts the pair there and then (`to_the_door`). The crater's ON_LOAD writes the shut tile
  (`setmetatile`) while F_GUARDS_UP is clear; a sign on it says what is missing. **The shut tile must have
  behaviour 0.** Test 11's first try used 584, which looks right but is an "animated door" (behaviour 0x69):
  walking north into a 0x69 tile warps you whether it is solid or not (TryDoorWarp looks at the tile in front),
  so the shut door let you in. 653 (behaviour 0) is used and the patch asserts it. A "non-animated door" (0x60,
  the open mouth 167) only warps when stood on.
- **Positions are data** (`places.py`, `check.py`, `rebuild.py`, `editor.py`): no position of a person, a Pokemon,
  a crystal or an item is in paldea_patch.py. `places.THINGS` has the built-in ones; a `placements.txt` (the
  user's is in `gba-trans/hyper-emerald/roms/test-paldea/`) overrides them; lists of crystals may be any length, or "none".
  - `check.py` refuses a build and says why in plain words: off the map, in something solid (the recorder, the
    note and Terapagos may be), in a doorway, two things on a tile that are there at the same time, on water
    with a bank beside it (A from the bank offers Surf, and Surf then puts you on top of it), a reflection on dry
    land (the rule under *Sprites of its own*), more than 15 things within one screen (the game keeps 16 objects
    with you; it spawns 9 tiles left to 10 right and 7 up to 9 down of you), more than 64 on a map
    (LoadObjEventTemplatesFromHeader copies them all into the save block's 64 without counting), ground that can
    no longer be walked to from the way in (story and after-story checked apart, on foot and with Surf; patches
    under 4 tiles ignored unless a door is in them), and a thing nobody can walk up to. Walking is the game's
    rule: collision bits; height 1 water; 15 keeps your height; 0 fits any; else heights must match.
  - `rebuild.py <folder>` (rebuild.bat): builds "Hyper Emerald - Area Zero (my placements N).gba" from the Gen 9
    test build, N past every ROM, save and save state of that name it can find (the user's emulator loads a ROM's
    last save state by itself, and one from an older build crashes), copies the newest save that has a game in
    it beside the ROM and into every mGBA `savegamePath`, warns if a save state is newer than that save, redraws
    the map guide, keeps its last two ROMs (the others' saves go to "old saves").
  - `editor.py <folder>` (edit placements.bat): a page served on 127.0.0.1 only. Every map as the game draws it
    (`map_guide.Rom.ground`), every thing as its own sprite; drag, arrow keys, add / remove a crystal, "Check"
    (a build in a temporary folder, check.py's findings), "Save and rebuild" (writes placements.txt, runs
    rebuild.py). `?selftest` on the page's address exercises it without a mouse.
  - `map_guide.py` draws tile numbers round each picture and a faint grid; a rebuild draws them again.
  - **A save keeps its own copy of the map it was made on**: the 64 object templates (positions, hide flags,
    sprites) and the objects in sight. On Continue only the templates' script pointers are refreshed, by index
    (LoadSaveblockObjEventScripts). So after a rebuild a save made in Area Zero showed everything where it used
    to stand until you left the map, and with a crystal added or taken away the wrong script behind an object.
    Var 0x40F9 holds the stamp of the build the copy was taken from (a CRC over every map's objects and blocks
    and over the positions; `STAMP_SALT` for what the woods get): ON_TRANSITION sets it; ON_RESUME turns any
    other value into 0; each map's ON_FRAME table starts with (0x40F9, 0) -> `refresh_<map>`: `getplayerxy`,
    `warpsilent` to the same map and tile, `waitstate`. The map is read again from the ROM, once, with one more
    fade. A save from before test 11 has 0 there and is read again too (the old shrine got map scripts for this).
  - Object order in a map's list is kept as test 10 had it (time crystals, crystals, then the people), local ids
    are counted, never written.
- **The user plays from save states** (their emulator: EmuDeck's mGBA, `savegamePath` the Desktop,
  `savestatePath` N:\Emulation\saves\mgba\states, autoload and autosave on). They finished test 10 without one
  in-game save: the .sav their emulator made on the Desktop is all 0xFF, and the .sav put beside the ROM is never
  read by it. `state_to_save.lua` (run on the ROM the state belongs to, with a copy of the state) loads the
  state, saves from the Start menu and continues from the save; test 11's save is their last test 10 state made
  that way, put beside the ROM and on the Desktop under the ROM's name. A state from one build must not be
  loaded on another: every script and map-script pointer in RAM is stale.
- **Tested on test 11** (sha1 d8e70efd...): `final11.ps1` runs test_story1-9 (9: the four in the stations,
  Nemona's rematch twice), test_steps, _crater, _before, _tour, _sprites, _whiteout, _save, _door; `old_saves.ps1`
  (saves made on test 10 in the woods after the ending, in the shrine and in the Underdepths, continued on test
  11); `refresh11.ps1` (a save made in the crater continued on a build with Arven and Koraidon moved, a crystal
  gone and two added: everything where the new placements put it, both answer; and on the same build: nothing
  read again). test_steps_continue is the user's own save: nobody by the hole, in through it, Penny at home.
  `second_save11.ps1` makes "(before the door opens)" from their save (make_save_before_door.lua: all but Nemona,
  the lab unlocked, below the shut door in the future) and plays it to the ending and on to Arven in Station
  No. 2 (test_save_before_door.lua). The tests' boot presses no keys once the field is up (BOOT_QUIET_FIELD in
  dexnavchain/test_boot.lua): a key landing on the frame a refresh ends would open a menu.
- **Test 12 (2026-10-08): three things the user found on test 11, and painting.**
  - "the crystal cavern right now it is loop cannot go out". A room's way out is MAP_DYNAMIC, and **the game
    keeps one dynamic place**: SetupWarp notes "the warp you came by" whenever the warp you take leads to a warp
    that is itself dynamic. The Underdepths' way out was dynamic too, so going down the cavern's ladder made the
    place the ladder, and the cavern's mouth then led to the cavern's own ladder. Never chain two dynamic rooms.
    Now the Underdepths' way out is a plain warp to the cavern's ladder (warp 1), and the cavern's ON_TRANSITION
    and ON_RESUME say where its mouth leads (`setdynamicwarp` to the crater's warp 2), by F_IN_FUTURE (0x43D6,
    set by the future crater's map scripts and cleared by the past's): a save or state made in the loop gets out.
    `setdynamicwarp`'s x and y go through VarGet: plain numbers there, 0xFFFF would be read as a var far outside
    the table. test_steps_cavern (in from each time, down, up, out) and old_saves' "loop" (a save made on test 11
    in the loop).
  - "the head of the player character got cut off when stand in front of locked gate": the shutter's picture is
    on its metatile's second layer, and with layer type 0 that layer is drawn over people. "the record UI, the
    top part got cut off": the same, the counter's top behind the recorder (a tile made to cover a clerk
    standing behind it). `tint.tileset(..., covered=)` copies a tileset's attribute table (512 words: nothing
    says how many metatiles a tileset has) with the named metatiles' layer type set to 1 (both layers under
    people): the shutter 653 in the craters' copies; in the stations' copy (same colours, their first copy at
    all) the tile the recorder stands on and the one above it, wherever placements.txt has it. No map of the
    game's sees a copy. test_steps_look12 takes the pictures.
- **The ground can be painted** ("apart from placement, can I change tiles layout everything myself? like Hex
  app. I cannot use Hex app": Hex Maniac Advance does not open this ROM). `ground.py`: ground.txt beside
  placements.txt, `[map]` then `x,y:block` words (hex, the game's own map word), only the tiles that differ
  from the map as the patch draws it; sections are grounds: the wall, the crater (both times: a time crystal
  puts you on the same tile), the research stations (one room), the cavern, the icy cave, the lab, the
  Underdepths; not the Timeless Woods. `paldea_patch.build(..., ground=)` gives every map rows of its own, keeps
  a copy as drawn, lays the file over them (`GR.lay`), then puts the rocks behind the big Pokemon; an unpainted
  build is byte for byte the build before.
  - **Tiles that stay**: every warp, sign (bg event) and trigger tile is "locked"; check.py refuses a build in
    which one differs from the map as drawn, or a way in or out that could be reached as drawn (with Surf) no
    longer can, or a tile a script puts you on (the wall's landing tile, the lab's standing tiles) is not
    ground. A warp only works on a tile whose behaviour is a door's or a ladder's, so painting over one would
    silently kill it.
  - **The editor** (`editor.py`, "edit placements.bat"): two modes. "Paint the ground" draws the map on a canvas
    from a 512 x 512 atlas of the map's metatiles (`map_guide.Rom.atlas`: 32 a row, as the built ROM's tinted
    tilesets draw them) and paints as Hex Maniac Advance does: left paints, right-click picks the tile under the
    mouse with its collision and height, right-drag picks an area as a brush (stamped, or laid side by side when
    dragged), Shift-drag fills a box, Ctrl+Z / Ctrl+Y. The list of tiles is every metatile that some layout of
    the game uses from the map's two tilesets (`usage()`: one pass over the 845 layouts), so nothing in it is
    past a tileset's end; a tile from the list gets the collision the game most often gives it (the map's own
    use first) and the height of what it is painted on, unless it has a height of its own (0, 1, 15) or the
    Walk / Height boxes say otherwise. Overlays: walls and water, heights, locked tiles.
  - check.py's findings are tidied for it: with a locked tile changed nothing else is said about that map; more
    than three things out of reach are one finding; the two craters, or the four stations, saying the same
    thing say it once ("the crater, both times").
  - A save holds the tiles round you as you last saw them; the build's stamp (0x40F9) takes the blocks in, so a
    save made beside a painted tile reads its map again (test_ground_make / _load).
  - Not yet: a map's size; where its doors, mouths and ladders are; the Timeless Woods' ground.
- **Tested on test 12** (sha1 300ba50c...): `final11.ps1 -Rom p12.gba` (22 runs), `fixes12.ps1` (the cavern, the
  pictures, the loop save), `ground12.ps1` (make_painted.py's build: a boulder painted on grass, a boulder
  painted away, a station floor tile made solid; both times, two stations, and a save from before the paint).
  The editor's page: `?selftest` in headless Edge (dragging, arrows, crystals, picking, painting, undo, an area,
  a box, a door refusing paint, and with `&apply` the save and rebuild). The user's own build is rebuild.py's
  "(my placements 2)" from their placements.txt.
- **Test 13 (2026-10-08): the terraces' pieces, and "Tidy the edges".** The user painted over a hundred tiles of
  the crater with the new editor, most of them terrace corners, and wrote: "I have adjusted some tiles, maybe you
  need to bake everything balance like corner of each tiles, don't make graphical glitch".
  - **The terraces were built from the wrong family.** The General tileset has a cliff set per surrounding: rock
    (104-109, 120-125), sand (128, 130), water (152, 154), and grass. `TERRACE` had the top corners 136 / 138 and
    the round ends 122 / 125 (taken from layout 826 where they stand against the rock plateau 113): each shows a
    sand-coloured corner on grass. And it had the grass set's round ends 124 / 145 where an edge turns inwards.
    The grass set, read off every layout that uses the tileset (`patches/paldea/neighbours.py`: for a tile, the commonest
    tiles above, below and beside it over all 845 layouts): 108 153 129 / 116 . 137 / 124 100 145, and 140 (a rim
    from the left meets a side from above), 139 (mirror), 132 (a face from the left meets a side going down), 131
    (mirror). The user had found 108, 129, 124 and 132 by eye; they had 122 for the right-hand end (still a sand
    corner), 106 (rock) on three corners and no 131.
  - **How to find a piece's family**: never by eye on a sheet. Count neighbours over the game's own layouts; a
    piece that fits has the expected partner on each side hundreds of times.
  - `world.py`: TERRACE is the grass set; `terrace_kind()` and `edge_piece()` are module functions;
    `crater_levels()` and `crater_dirt()` give the sketch's levels and path; the waterfall's splash is 193 across.
  - `tidy.py` (`crater(blocks, drawn, levels, dirt)`): works every edge piece out again from the shape, for
    terraces (level from height: 3 / 5 / 7; a raised tile with lower ground beside it gets its piece, walking and
    height; a terrace piece where no edge is becomes grass; steps and anything that is not plain ground or a
    terrace piece stay), dirt paths (`edge_piece` over the dirt family; a path counts as going on under a terrace
    edge the sketch drew over it) and puddles (200 431 201 / 216 319 210 / 208 217 209, behaviour 0x16: walked
    through). On the map as built it changes nothing (asserted by hand: `try_tidy.py`), and it leaves the mound's
    rock pieces (the Chasm's chunk) alone unless somebody painted them. Lakes are not tidied.
  - The editor: "Tidy the edges" on the crater's tabs (POST /tidy, applied as one stroke, Ctrl+Z takes it back);
    a check, a save and the opening message say how many edge tiles do not fit. The user's ground.txt was tidied
    with the same code (48 tiles; their path, puddle and lamp kept; their file as painted is kept beside it).
  - **Two editors on one port.** Python's HTTP servers set SO_REUSEADDR, and on Windows that lets a second
    process bind a port another is listening on; each gets some of the connections. A test editor started while
    the user's was open answered on "their" port. `editor.Server` binds exclusively (SO_EXCLUSIVEADDRUSE) and
    takes the next port. Test editors are stopped by PID or by their own port, never by the default port.
  - An editor left open keeps the code it was started with: after a change to the patch the user has to close
    the black window and open it again, or a save from the old page rebuilds with the old pieces.
- **Test 14 (2026-10-08): past the crater's edges.** The user: "increase the border of the map, cuz rightnow it got
  cut off when ran on the border, notsure u understand or not".
  - **What was cut off.** The screen shows 7 tiles either side of you and 5 above and below (the top and bottom
    rows by half). The crater's ground comes within 4 tiles of its sides, 3 of its top and 4 of its bottom, so
    3, 2 and 1 tiles past the edge come on screen. There the game draws the layout's border block, 2 x 2 tiles
    picked by `(x & 1) + 2 * (y & 1)` in the map's own coordinates. Ours was a wood (470 471 / 468 469). It
    could not go on with the land above (113, rows 7-10) and the wall's face (121, rows 11-12), which run out
    through both sides: the cliff stopped dead against trees. The rim's wood (rows 0-6) has its tree middles on
    odd rows and the border has them on even ones: the trees jumped a row at the edge. Row 0 was tree tops
    drawn against the land above (494 495): a strip of sand with trees over it. Row 51 was trunks, with the
    border's middles under them.
  - **Strips joined as connections, not a bigger map.** A bigger map moves every x and y: placements.txt,
    ground.txt, the saves made in the crater, the tests. Instead the game is given what lies past each edge the
    way it is given the next route: `maps.Map.connect(side, offset, key)` writes the vanilla table (header
    +0x0C -> count, pointer; 12 bytes each: side 1 south, 2 north, 3 west, 4 east; offset at +4, group +8,
    number +9). On loading a map the game copies, from each joined map's layout, the 7 rows or columns nearest
    the edge (8 columns on the east) into the 7 tiles it keeps round the map (its copy is w+15 by h+14); only
    the blocks, drawn with the current map's tilesets, so one set serves both times. A north or south strip at
    offset -7 and w+15 wide fills the corners too. Maps 35/101-104: north and south 67x7, west 7x52, east 8x52.
    They have no events and no scripts; nobody enters them (every tile of theirs is shut, and the crater's
    outer ring is trees and cliff).
  - `world.beyond(blocks)`: every row goes on west and east, and every column north and south, with its last
    two tiles again and again (a tree is two wide; two rows of a wood are a row of middles and a shared row).
    `world.woods_on()` turns row 0's tops and row 51's trunks into the shared row (468 469), so the top and
    bottom are a wood that goes on. The strips are made from the map as painted (ground.txt). They and the
    connections are in the build's stamp: a save made in the crater on an earlier build reads the map again
    (its saved view holds 0x03FF, "nothing here", past the edge, and that would be put back over the strips).
  - `patches/paldea/margins.py <rom> <outdir>`: any map with the 7 tiles past each edge as the game fills them
    (joined maps, then the border block). The other maps were looked at with it: the wall's border is its own
    face, the rooms are indoors, the Timeless Woods' own border fits.
  - The editor shows 4 tiles of it as a dim band round the two crater tabs. The page works it out by the same
    rule, and `?selftest` holds that against the build's strips (1718 tiles, none differ).
  - Tests: `test_steps_edges.lua` (the tiles the game holds past each edge, read from its own copy of the map,
    after a warp and after walking to each edge, in both times; pictures), `test_edges_make.lua` and
    `test_edges_load.lua` (a save at the west edge made on test 13 and on test 14, continued on test 14);
    `_testrun/paldea/edges14.ps1`, and everything together `final14.ps1`.
  - **The runner let go of the emulator while it still held the save.** `run.ps1` stopped it and returned; on a
    busy machine the next `Copy-Item` of the base save failed ("a file with a user-mapped section open") and
    that test ran on the previous test's save, and said ok. It waits for the process to exit now.
  - **How to make scenery go on past a map's edge**: a border block only if two tiles by two can carry it on
    every side; otherwise strips joined as connections. Before handing a map over, find how near the ground
    comes to each edge (7 across, 5 up and down) and look at `margins.py`'s picture.
- **Test 15 (2026-10-09): the Sealed Vault, and two item balls in the crater.** The user: "for the tinglu, chiyu,
  wochien, can we new room for them and have a puzzle to solve to obtain them at around 15,1 ? cave entrace? and
  have more item ball booster energy in the crater as well like 1-2 location", then "make sure u polish
  everything as perfect as possible, but also beaware of the glitches bugs that can occur as well".
  - **15,1** is the Crystal Cavern's second cave mouth (tile 774). The Mt. Coronet room it is copied from (36/82)
    has a warp there to 36/94; ours had none, so it led nowhere. It is the cavern's warp 2 now, into the vault;
    a crystal stands on it until the story is done (flag F_STORY_DONE, as on the ladder). The vault's way out is
    a plain warp back to it (two MAP_DYNAMIC rooms in a row break the first: *Test 12*). The cavern's
    decorative crystal at 15,2 stood in front of the mouth: out of the defaults, and out of older files
    (`places.GIVEN_UP`).
  - **The room**, 35/101 (the edge strips are 35/102-105 now), 17 x 18, drawn by `world.vault()` from the
    Snowpoint Temple's pieces (36/75-79: General + 0x083DF8CC): double walls 898 / 896 / 891 905 892, the snow
    ledge 889, floor 901 (903 ice below, 911 ice above), ICE 909 (behaviour 0x20), an ice boulder 899, a snow
    patch 655 (General's), the way out 902 (floor, arrow warp south). Five niches one tile wide along the back
    wall, a dais of floor, the mirror floor 13 x 9, a strip of floor, the way out in the bottom wall at 9,16. Tint
    "crystal", like the cavern. Wo-Chien, Ting-Lu, Chi-Yu in niches 2, 11, 14 behind dark crystals; the great
    tablet (hack sprite 13) in the middle niche; the Sword's niche (5) empty with a slat (sprite 12): Chien-Pao
    is in the icy cave. Three stakes (sprite 23, the stone marker that stood for the Ruinous four up to test 10)
    on the ice. Flags 0x43D8-0x43DA (story.F_SEALS): each hides a stake and its crystal; the stake's script
    removes both (SE 42 ice crack, a shake, SE 41 ice break, the Pokemon's cry). Item balls: 0x43DC / 0x43DD
    (story.F_BOOSTER). New flags checked like the old ones (script index, object hide flags, script bytes,
    aligned literals, three saves); 0x43D7 and 0x43DB have chance matches and are skipped.
  - **The puzzle** (built-in: boulders world.VAULT_ROCKS, patches VAULT_PATCHES, stakes in places.py) was found
    by `patches/paldea/vault_search.py`: layouts thrown together and kept if the middle column is clear, no
    straight slide from the dais or the strip runs into a stake, no place traps you, every stake can still be
    pulled whatever was pulled before; then ranked by how they play (every order of the stakes). Eleven slides
    at the least; the stake of the Vessel is reachable only after the stake of the Beads is pulled (the slide
    on after pulling it reaches 12,7, the one place that leads to the Vessel's row).
  - **Engine facts, seen in the game:**
    - On ice the game retries the forced move every frame you stand there (DoForcedMovement on a collision calls
      ForcedMovement_None and returns FALSE, and the next frame tries again). So **when what stopped you is
      removed you slide on** the way you face: a stake pulled from 3,12 left the first build's player at 3,9.
      check.py and the search play it so (`on()` in puzzle_states).
    - A press on ice is a slide; a quick tap does not turn you in place. A is read while you stand still on ice.
    - Step events (coord events) do not fire on ice tiles (FieldGetPlayerInput sets tookStep only off forced-
      movement tiles), so nothing of the puzzle is a floor switch: the stakes are objects answered with A.
    - An arrow warp takes you out the moment you stand on it holding its direction. The first build had the way
      out at the foot of the clear middle column: a slide down holding Down left the room. It is one tile aside,
      in the bottom wall, now (test: `{"hold", "DOWN", 150}` stays in the room).
    - A save made standing on ice continues there; a save from another build's vault is read again (FRESH) and
      put back on the same tile, facing as before.
    - Reflections: ice is reflective; the mirrored sprite is drawn at priority 3, over the map's bottom layer and
      under its middle one, so it shows on tiles of layer type covered or split (grass is covered: Koraidon's
      feelers on the picnic, test 9) and is hidden by normal ones (the vault's floor). `check.layers()`; the
      reflection rule now only concerns water, and only ground that shows it.
    - **Object palettes**: the hack hands them out by tag from slots 4-9 (sSpritePaletteTags at 0x03000CF0;
      0x094A356A) and frees none until the field is reloaded (a warp, a battle). A seventh tag goes to slot 10, an
      eighth takes slot 10 from it. The first vault had 8 (three crystal colours): Ting-Lu stood there in Chi-Yu's
      colours. The crystals are all the dark shard now, which shares the stake's palette (tag 0x1116): 6 tags.
      check.py refuses a map whose things need more than `PALETTES` = 7 tags in one phase; both craters are at 7
      after the story with their item ball. The harness step `{"pals", label}` logs the sixteen tags.
  - check.py: `Ground.step` / `go` / `stand` (reach slides on ice); `check_puzzle` plays every state (stakes
    standing x treasures there, from the door; a save from an older build may have any treasure caught):
    nowhere to get stuck, every stake can be pulled in some order, a crystal closes its niche, the treasure can
    be walked up to once it is gone; `puzzle_way` gives the shortest way (the editor's Check says how many slides,
    the READ ME has it written out). `crowded()` is the old "15 on one screen" rule as a function.
  - places.py: `MOVED` (Wo-Chien, Ting-Lu, Chi-Yu were in [Crystal Cavern]), `GIVEN_UP`, and `.notes` on what
    parse() did to an older file; rebuild.py then writes placements.txt afresh and keeps the old one as
    "placements - as it was before build N.txt". The editor has a "Sealed Vault" tab, says what an older file
    had when it starts, and names ice in the tile list.
  - Tests: walk.lua slides (a route is presses; a press has landed after 18 still frames); harness steps
    `slide` (a press, released as soon as you set off), `hold`, `pull` (the stakes, in whatever order can be
    reached), `pals`; `test_steps_vault.lua` (shut, open, caught, ice), `test_vault_old_make/load.lua` (a
    cavern save from test 14), `test_vault_ice_make/load.lua` (an ice save from another build),
    `test_steps_balls.lua`; `_testrun/paldea/vault15.ps1`, everything `final15.ps1`.
  - Part 2 (Kitakami) is to look Japanese (the user: "can we have japanese house style for them to match
    theme?"). The game has the buildings: Koga's Village 35/45 (thatched wooden houses; General + 0x083DF734)
    and Celestic Town 36/10 (dark-roofed houses, a big wooden shrine; 0x089CBC6C + 0x08A6550C); the Bell Tower
    35/9 and Bellchime Trail 35/74-75 have a pagoda's insides.
  - Gotchas: `python -I` does not put the script's own folder on sys.path; a Git Bash heredoc turned "\n" into
    a real line break in a search script (write such scripts with the Write tool).
  - **rebuild.py gave the user's ROM a save that was not theirs.** It took the newest save with a game in it of
    any Area Zero build, and the newest was the copy of the second save ("test 14 (before the door opens)")
    that test 14 had put on the Desktop. Caught on test 15's handover (the save's checksum was the second
    save's), the right save put in place; `newest()` now prefers the user's own builds and never takes a
    second save.
- **Test 16 (2026-10-09): the way in moved to Mossdeep City.** The user, with a screenshot: "change the entry of
  blackhole and Jacq to Mosdeep city instead at where I stand in the picture here", then "make sure everything in
  Mosdeep will work exactly the same since it has various event".
  - The spot: the screenshot (1960x1256: 8.17 picture pixels a game pixel, 154 of the 160 rows) slid over the
    ROM's render of 0/6 (`find_spot.py`, in the session's scratch): tile 68,33, the strip of grass at height 3
    below the Space Center between the cliff and the sea, (66-70,33) and (68-70,32), stairs up at 66,32.
    Defaults (places.py): the hole 68,32 (you come back out on 68,33, the user's tile), Jacq 70,32 facing it, the
    ending's three on 67,33 / 69,33 / 70,33. 69,32 is the game's item ball (hack sprite 60, item 468, flag 0x4016,
    script 0x08FE3DE6 in the hack's list of finditem scripts): fixed, nothing of ours on it.
  - Mossdeep (header 0x08482560, events 0x08B0C3C0): its 29 objects copied as they are, ours 30-34. Its map
    scripts were ON_TRANSITION alone, 0x0980BFE2, the hack's: clears 0x64-0x67, checks 0x88A and 0x1AD, shows or
    hides the Space Center's group (21-25, flag 0x411F) and object 19 (0x4067), and ends with `end` on every path.
    So ours (state, the stamp, who of ours is shown) ends with `goto 0x0980BFE2`: a `call` would never come back
    from its `end`. ON_RESUME and ON_FRAME (the refresh, the ending) are ours alone. The build asserts the header,
    the events, the scripts list and the first bytes of that script. Palette tags: Mossdeep's own five (0x1103-
    0x1106, 0x110B) and ours give six. Our people's height is the ground's under them (`height_at`); Jacq and the
    students face the hole / the tile you come home on (`toward`).
  - The Timeless Woods keep map scripts only (transition, resume, refresh). A save made in them on an older build
    holds Jacq, the hole and the students in its copy of the woods; its stamp is not this build's, so the woods
    are read again from the ROM, where they are the game's own eight objects. The user's save is such a one.
  - check.py: what is not ours to move (fixed, not open) now stands in the baseline the "can no longer be reached"
    and "way in or out" findings are measured from. Mossdeep's own people shut off much of the city in the
    checker's eyes (objects 10-14 stand in a row across 44,23-26 until flag 0x337, people in narrow ways), and all
    of it was reported as ours to put right. Only what our things shut off besides is said; Jacq put on 67,33,
    the strip's only way off, is still refused (tried).
  - places.py: RETIRED sections ({"timeless woods": "mossdeep"}): an older file's [Timeless Woods] lines are
    passed over with one note, and the five are not listed again as new.
  - Story texts: Jacq says the Space Center saw the hole open; the hole "hangs in the air above the grass"; the
    wall's way back hears the sea at Mossdeep; Jacq in Station 4 speaks of the hole in Mossdeep.
  - Tests: `test_mossdeep.lua` with `_testrun/paldea/mossdeep16.ps1` and `mossdeep_compare.py`: the build against
    the Gen 9 build without Area Zero (`c16.gba`), from p9.sav, kinds space (0x1AD set) / nospace / before (no
    0x41D5) / save (a save standing in Mossdeep, and one surfing off the north shore at 20,3, each continued):
    who is on the map (local id and sprite; 1, 3, 4 and 9 wander, so not where) and 14 flags at five stops, and
    gPlayerAvatar's flags (harness step `avatar`): identical. `test_mossdeep_old_make/load.lua`: a save in
    Mossdeep on test 15 continued, Jacq and the hole there after the refresh. The way in (test_steps.lua), before
    Team Rainbow Rocket (test_steps_before.lua), the ending (test_story4/6/7, whiteout, save_before_door: the
    finale ends on map 0/6), after the story (test_story9), the user's save (test_steps_continue.lua) and old
    saves (old_save_load.lua, woods) rewritten for Mossdeep. Everything: `_testrun/paldea/final16.ps1`.
    Woods expectations no longer ask for 0x43D4 (Jacq's hide flag): nothing in the woods sets it now; Mossdeep's
    transition does, and test_steps_continue checks it there.
  - The user, looking at the map guide's Mossdeep page with the ending's three drawn round the hole: "make sure
    that after the ending of the mission, those new npcs would not block the way out". They do not (the ending
    removes all four; only the hole stays): test_story4 and test_save_before_door now walk onto every tile of the
    strip after the ending and up the stairs. map_guide.py: the Mossdeep page is a close-up (window round our
    things, 3 picture pixels a game pixel; `ruled` numbers the tiles from the window's corner), people of a scene
    only (when "ending" / "finale") are drawn at 45% and labelled "(only in the ending)", and a label pushed away
    from its ring gets a line back to it.
- **Test 17 (2026-10-09): Area Zero in the Journal, its legendaries in the Legends.** The user: "update the
  journey game log as optional quest, so player knows what to do next", then "update the legendary checkbox as
  well". `patches/paldea/journal_az.py`, called by paldea_patch.py after everything else; its data goes to
  `0x09FE1000..0x09FE4438` (13 KB, a blob of its own in the ROM's free tail before the sprites' block; the
  Area Zero block did not grow). The release's Journal and Quest Log are not touched: only this test build has the
  rows.
  - The journey log is the Journal (item 363, "A notebook of your journey. Use it to see what to do next."), which
    opens the Quest Log; its four Journal chapters are the Journal's step table (`patches/journal/steps.py`).
  - Seven rows after "Steven is waiting" (rows 61-67; Post-game 39 -> 46 rows): Area Zero: Jacq (opened by 0x41D5,
    done 0x43AC), Penny (0x43AC / 0x43B1), sandwiches (0x43B1 / group: Arven, Great Tusk, Koraidon up, Iron Treads,
    Miraidon up), Nemona (0x43B1 / 0x43B7), the four logs (0x43B1 / group: logs 1-4, Penny unlocks the lab), the
    Zero Lab (0x43BD / 0x43C1), legends (0x43C1 / group: the fifteen caught, 0x43C3-0x43D1, which mean caught only
    after 0x43C1). A group row's detail is the Journal's own group_tail: "Sandwiches: 2/5" and the next one
    missing. Portraits: trainer pictures 31 / 194 / 218, Koraidon and Miraidon by species id (kind 1).
  - The copy: a new step table (the ROM's 84 rows as they are, their texts and groups where they were, ours put in),
    titles and Journal panel tables likewise; repointed: the step table's three literals (0x08FE563C, 0x08FEA3F4,
    0x08FEAC7C), the titles' (0x08FEB248), PANES[0] (0x08FED35C); PAGES: Post-game rows and count +7, Sinnoh's and
    Lost Artifacts' first row +7. Nothing depends on step numbers at run time and nothing goes to the save.
  - **Optional rows.** The Quest Log's compute (0x08FEA31C) makes the first step not done after the last done
    anchor the current objective, so a row of ours there would have taken "Return to Steven's Island" away, and a
    row left behind gets the grey Side tag the user once read as done. A step row's spare byte 3 now marks an
    optional row (1-based into a table of the flags that open them), and compute is replaced (8-byte trampoline at
    its start, 0x08FEA31C, so the caller's lr is untouched; `compute2` in the blob): the same three passes, but
    optional rows are never the current objective, and read "???" (4) until their flag is set, Active (2) while
    not done, Done (1). Every other row gets the status it got before.
  - **Legends**: Koraidon, Miraidon, the four Treasures of Ruin, Terapagos after the 92 (Dex order, 921-939 are
    this build's numbers): a new table (the old rows as they are, row 0's "all N of them" texts with 99), a new
    Legends panel table (PANES[1], 0x08FED360), rs_legends (0x08FEB23C) repointed, legend_all's `cmp r4, #92`
    (0x08FEB220) -> 99, PAGES[4] rows/count +7. The species -> Dex table is the one speciesx moved (0x096B5F00,
    through SpeciesToNationalPokedexNum's literal 0x0806D448), not questlog's NATDEX (0x08F50370, pre-speciesx:
    species 1200+ read past its end). **Done/total print two digits (u8dec)**: the first build added all fifteen
    (107) and the header read "44/!7"; the eight Paradox Pokemon are not legendary and stay in the Journal's
    group only. Adding Ogerpon, the Loyal Three or Pecharunt (Part 2) needs a 3-digit count first.
  - Tests: `test_journal_az.lua` (harness steps `journal`, `dex`, `qlog`), `_testrun/paldea/journal17.ps1` and
    `journal_compare.py`: the stages of Area Zero's story on the build and on the Gen 9 build without it, with
    p9.sav as it is (its story in Lost Artifacts) and with every Journal step after Rainbow Rocket undone (current:
    Steven): every main row reads the same, the current objective is the same row, Area Zero's rows read as
    planned, Post-game and Legends counts grow by exactly ours. Gotchas: the Pokedex bit of number n is bit n
    (not n - 1) in the hack's arrays; p9.sav (from the Gen 9 test save) has the Gen 9 numbers caught already; the
    Evolutions' grid count (V+0xC8+8) is not shown and varies run to run (row_status over 255 placeholder rows);
    the harness's key is "SEL", not "SELECT"; its "hold" step waits for the field.
- **Test 18 (2026-10-10): a legend caught or knocked out is gone.** The user: "when defeat the legendaries or
  capture, such as walkignwake, koraidon... there should disappear not infinite reencounter". Up to test 17 one
  knocked out stayed, to be tried again. Now the partners' scripts (Koraidon / Miraidon at the picnic) and the
  thirteen legends' go to "gone" on B_CAUGHT (7) or B_WON (1): fade to black, removeobject (which sets the
  object's own hide flag: the partner's caught flag; the legends also setflag their flag first), fade back - the
  game's Common_EventScript_RemoveStaticPokemon. Ran (4), fled (6) and the rest leave it. The flags 0x43C3-0x43D1
  now mean "caught or knocked out"; the Journal's group counts "Done:" and its text says each is met once.
  Tests: test_story5 (Gouging Fire run from: stays; knocked out: gone; Koraidon, Walking Wake, Chien-Pao,
  Terapagos gone, and still gone on coming back), test_steps_vault (Wo-Chien gone). Harness step `flee`: B
  through the battle's opening lines (B goes on in text and does nothing in the action menu), then Right, Down, A
  (Run), each once its frame has passed: the battle's callback is not BATTLE on every frame of its intro, and
  a key tied to one exact frame was missed.
- **Test 19 (2026-10-10): tiles for the craters taken from other maps.** The user: "if I want to decorate the
  map, can u make the edit placement.bat for me? like I need more tiles as well"; of the ways offered they chose
  "Pick from any map" for "The two craters". `patches/paldea/tiles.py`, a third file of the user's (`tiles.txt`:
  `656 = 35/45 713`, our number = the map it came from and its metatile there) and the editor's "Take from another
  map...". Without tiles.txt the build is test 18 byte for byte: nothing was rebuilt for the user.
  - **A tileset** is 24 bytes: compressed u8, secondary u8, pad, then pointers to the picture cells (LZ77 when
    compressed), the palettes (16 rows of 16), the metatiles (16 bytes: eight entries of cell 10 bits | hflip
    0x400 | vflip 0x800 | palette row << 12), the attributes (u16: behaviour in the low byte, layer type in bits
    12-15) and a callback (animations; 0 = none). A map draws with rows 0-5 of its primary set and 6-12 of its
    secondary; each half has 512 cells and 512 metatiles; the last 8 secondary cells (1016-1023) are where an
    opening door is drawn. General is `0x083DF704`, the craters' secondary (Petalburg's) `0x083DF71C`: 144
    metatiles (512-655), 254 of its 504 cells referenced, callback 0. 413 maps have General as primary, over 36
    secondary sets (`tiles.sources`); Celestic and the other Sinnoh / Hisui towns have a primary of their own
    and are not offered. A few of the hack's tilesets have the compressed flag set and raw cells: `tiles.lz`
    takes a first byte other than 0x10 as raw.
  - **The craters' own secondary set** (`tiles.build` -> `tint.custom_secondary`): Petalburg's metatiles as they
    were, the taken ones at 656-1023 with the numbers tiles.txt gives them for good (ground.txt keeps painted
    tiles by number). Cells (LZ, never a distance of 1), metatiles and attributes go to the second blob
    (JOURNAL_FREE, ahead of the Journal's data, whose addresses move with it: journal17 passes), the tinted
    palettes and the 24 bytes to the main blob, once per time. A cell of the primary set drawn with a secondary
    row needs no cell of ours unless its colours had to be renumbered.
  - **The room: 433 cells and 75 colours.** The stations' houses keep 70 cells and rows 9 and 12 (the game draws
    an opening door with the door metatile's rows: test_tiles_door, frame by frame the same as test 18 with every
    other row repacked). The colours are what runs out: a row is 15 and a piece seldom uses a whole one, so they
    are packed. First a source row at a time (the colours keep their indexes, most cells stay as they are), then
    a cell at a time (tighter, costs cells); each first exact, then with shades one step (of 32) apart sharing a
    colour, then two (`JOIN`). The first way with room for everything is used; the last one's reason is given
    when none has. Koga's thatched house: 13 colours, 20 cells. A corner of Fortree (Pokemon Centre, a tree
    house): 34, 66. Koga's house + all of Fortree + the top half of Lavaridge: 121 tiles, 213 cells, 74 colours
    with shades a step apart, a cell at a time (this is tiles19's build). All three towns whole do not fit.
  - Gotchas. (1) Shades may be joined only across pieces: the first try let any two colours within the
    tolerance share one, and the straw of Koga's roof (shades a step apart, drawn together) came out flat. What
    is placed together gets a colour of the row each (`pack.fit`). (2) Petalburg metatiles that use a row now
    taken, or a cell now needed, are given up and leave the editor's list; never one that is on the ground
    (`needed`: the craters' ids and DOOR_SHUT_TILE). (3) The places for a secret base (behaviours 0x90-0x9D) are
    made plain: Secret Power on one looks for the base the map has there. Doors, cave mouths and ladders are
    pictures: no warp event. Animations do not come along (callback 0). A taken cave floor (0x08, 0x0B) has wild
    Pokemon on every step, as in a cave; the editor's brush says what a tile does (`DOES`). (4) The past's warm
    tint turns a blue hot spring sage, as it does the crater's own pond: not a wrong colour. (5) The page: the
    hint above the other map's picture changed its height when a drag began, and the picture jumped a row under
    the mouse (fixed height). The selftest's save step moved Arven onto a pond the user has since painted (it
    now tries a step west and stays if Check refuses). (6) The build's stamp does not need the taken tiles: a
    save holds block numbers, tilesets are read from the ROM; painted blocks change it as before
    (test_tiles_make / _load: a save from before, right below the painted house, continued).
  - **Tested** on `p19x.gba` (tiles19.ps1 builds it from `_testrun/paldea/tiles19/`): `final16.ps1 -Rom p19x.gba
    -Old p18.gba` (43 lines, all ok), `journal17.ps1 -Rom p19x.gba`, `tiles19.ps1` (pictures of three spots in
    both times, the door against test 18, the save from before). The editor: `?selftest` and `?selftest&apply`
    in headless Edge on a copy of the user's folder (the list of 413 places, a place by name, a box dragged on
    its picture, the button, the brush put down, Check, the same box again taking nothing new, a second place,
    the tidy-up, save and rebuild, the reload with the taken tiles in both craters' lists); `&shot=lib` and
    `&shot=paint` with `--screenshot` for a look at the page. rebuild.py with tiles.txt, with a painted tile
    missing from it, and with a map that does not exist.
- **Test 19, part 2 (2026-10-10): objects' palettes given back (`patches/paldea/objpal.py`).** The user, with a
  screenshot of Walking Wake on the channel above the waterfall in washed-out orange and white: "sometimes the
  static legen such as walking wake, koraidon, etc.. will have inveted visual graphical glitch".
  - **Why.** The hack's allocator (0x094A356A, reached from its two hooks at 0x094A3356 and 0x094A3362: spawning
    an object and changing its graphics) looks for the tag in slots 4-9, else an empty one there, else writes it
    into slot 10, and nothing is given back until the field is reloaded. After the story the past crater has
    more kinds than six (red crystal 0x110D, time crystal 0x1111, Raging Bolt 0x112A, item ball 0x1105, Gouging
    Fire 0x1129, Koraidon 0x1124, Walking Wake 0x1128, Arven...). The user's save, walked round the crater and
    up the waterfall: Walking Wake was the seventh and got slot 10, and slot 10 did not hold its colours but a
    copy of slot 4's (the red crystal, which stands by the ponds: something of the hack's writes slot 10 again,
    the reflections most likely). So even the seventh kind was wrong, not only the eighth as noted for the
    vault. Picture: `_testrun/paldea/out/ww_compare.png`.
  - **The fix.** The hack's function starts with a jump (10 bytes: `014b1847c046` + word, it is 2 past a word)
    to ours in the second blob: the tag's slot (4-9) if it has one, else an empty one (4-9), else one that no
    sprite in use draws with (gSprites 0x02020630, 64 x 0x44: in use = bit 0 of +0x3E, palette = OAM attr 2 at
    +4, top 4 bits), else slot 10 as before; then the tag into sSpritePaletteTags (0x03000CF0) and the palette
    loaded by the hack's own 0x0808E91D (tag, slot: FindObjectEventPaletteIndexByTag + LoadPalette). A thing
    that goes out of sight loses its sprite, so its slot comes back. The allocator is the hack's for every map:
    any map with more than six kinds of people had the same fault.
  - **check.py** counted kinds per map and phase (at most 7). Now `colours()`: at most 6 kinds within one
    screen and its margin (TrySpawnObjectEvents' window, as `crowded()`), per phase; more than that and one
    still falls to slot 10.
  - Tested with the user's own save (their "(my placements 11)" and the same files built with the fix): round
    the crater, Surf, Waterfall to Walking Wake (old: slot 10, wrong; new: slot 5, the time crystal's, which was
    out of sight), down again past the dais, the picnic and the den (every object's slot holds its own tag;
    pictures right). Test harness step `objpal` (each object's sprite and slot, the other sprites, the slots'
    tags and first colours). final16, journal17 and tiles19 on builds with the fix.
- **More gotchas (test 12)**
  - Git Bash heredocs halve backslashes: an edit script fed through one wrote NUL bytes into check.py where
    a backslash and a 0 were meant. Scripts with backslashes go through the Write tool.
  - A metatile whose picture is on its second layer hides whoever stands in front of the tile below it. Look
    at the layer type before using a tile next to where people stand.
- **More gotchas (test 11)**
  - A tile that looks like a shut door may be a door to the game (behaviour 0x69): look the behaviour up.
  - A flag that means "somebody has been sent somewhere" is a second copy of the story's state, and a second
    order of events will leave it wrong. Work such flags out from the first copy on the way into the map.
  - `removeobject` on a save's first resume is how saved people are taken off a map; a hide flag alone leaves
    the ones already in sight standing there.
  - A hide flag that is worked out is only right after the next map script has run: straight after the ending
    F_HIDE_RESIDENTS is still set, and cleared on the way into the station.
  - Removing a map renumbers the ones after it and strands saves made in them. Empty it instead.
  - The hack's message box turns white for one frame between two messages and when it closes; that is the
    hack's own, in every conversation of the game.

## DEXNAV BAR: THE ABILITY IT NAMES — 2026-10-08 — `patches/dexnavabil/`
- Reported with a screenshot: the bar under a hunted Corvisquire read "-------" where the ability goes. The search
  (`patches/dexnavchain`, in the v1.4 base) read a species' abilities from the base stats, +22 and +23, in two
  places: reroll() to see whether there is a second slot to roll for, hud_text() to print `names[byte]`. Those
  bytes are leftovers (*DexNav search and chain*, above): the game reads three u16 a species at 0x097A0000 through
  GetAbilityBySpecies (0x0806B694 -> 0x09D73A80), and a Pokemon's slot bit (IV word bit 31) indexes that table. So
  the Pokemon always had a real ability; the bar and the roll looked elsewhere.
- What that did, over the 772 species in the wild table (0x08E17D50): 55 have 0 in the bytes (the Gen 8 ones) and
  showed ability 0's name, "-------"; 129 more showed another ability's name in at least one slot (Bulbasaur's
  bytes are 66 / 65, Blaze or Overgrow, and it is Overgrow / Overgrow; Riolu read Protean for Steadfast; byte 75,
  vanilla's Shell Armor, is "Grassy Surge" in this hack's names, and its Shell Armor is 260); 46 species with two
  different abilities were never given the second (35 of them the blank ones: 0 / 0 reads as "no second slot"); 5
  were rolled between two slots that hold the same ability (harmless). No wild species has an empty second slot
  where the old roll could pick it, so nothing was ever handed "no ability".
- The fix is two `bl`s inside the dexnavchain blob, retargeted; no other byte of it changes (the blob is in the
  v1.4 base, so it is hooked, as dexnavseen and dexnavscan do, not rebuilt):
  * reroll's `bl basestats` (0x08FDE996) -> `slots_hook`. reroll only compares the two bytes it reads at +22 / +23
    of what comes back (second != 0 and != first -> rndmod(2)), so the hook returns a pointer 22 bytes before one
    of two constant pairs: 1, 2 for a species whose table row has two different abilities, 1, 0 otherwise.
  * hud_text's `bl scopy` for the ability line (0x08FDED6A) -> `name_hook`, which drops the source it is given and
    copies `names[table[3 * species + slot]]`, slot = state +7 (what apply_extras writes into the Pokemon). The id
    is 16 bits: the hack's run past 255 (Shell Armor 260, Solid Rock 333).
  Code and the four pair bytes: 0x08FF75D0..0x08FF7634 (after namingkb's table; that run is usable up to
  0x08FF7700 - the gotcha at the end of *Fusion slots*).
- Two choices worth keeping:
  * The table is read directly (its address taken at patch time from the routine's own literal, 0x09D73A94), not
    through GetAbilityBySpecies: that routine also stores what it found at 0x0203F008, the engine's "last ability
    looked up", and the bar redraws on its own clock. 0x09D73A9C is the same lookup without the store, but gen9
    turns it into "the ability the engine acts on" (an alias gives its base), which is the wrong name to print.
  * The names come through the ROM header (0x080001C0) at run time. A literal holding 0x09D03068 would have been a
    ninth word with that value: gen9 moves the name table, expects exactly eight, and stops.
- Tested (`test_dexnavabil.lua`; `_testrun/abil/run.ps1` runs it hidden; the working save, Route 102) on six
  species: Corvisquire, Bulbasaur, Riolu, Tirtouga, Krabby, Charmander. For each: 40 calls of reroll() (a
  `callnative` script) give slot 0 only to a one-ability species and both slots to a two-ability one; for every
  slot the bar's text (scratch +64) is the table's ability name; and the hunted battle (the patch put next to the
  player, one step) brings that species with that slot bit and the engine's own 16-bit ability for the foe
  (0x0203F002) equal to it. PASS three runs in a row. The unpatched working ROM, the control, fails 8 checks: its
  bar reads "-------", "Blaze", "Protean", "Intrep.Sword", "Grassy Surge" and its roll never gives Corvisquire slot
  1; its Pokemon are right. The same test passes on a Gen 9 build made on top (speciesx, gen9 with `check_gen9.py`
  clean, and paldea all apply), where the names have moved. `test_dexnavui.lua` logs the same on both builds.
- GOTCHA for tests that step onto the patch: the game's step scripts run before the encounter check, so one of
  them can take the step and the hunted battle does not start (flags stay 0x09, the field is locked). Met here:
  "The Repel ended... Use another?" on the first step after loading the working save, a Pokenav call, a script at
  Route 102 (10, 6), the door at (7, 3). The test warps to (9, 6) before every case and does a case again when its
  step goes to a script. In play it would leave you standing on the patch, which on_patch only notices on a step
  onto it (read from the source, not played).
- Chain: `dexnavabil` goes before `zhtext` (HANDOFF). `_testrun/rel18/rebuild_chain.py`, with it added, gives the
  installed ROM byte for byte; against the ROM before, 108 bytes differ: the two `bl`s and the blob.
- Installed 2026-10-08 (sha1 22806e2f...), backup "(before dexnavabil 2026-10-08)" (742ae12b...). In no release.
  The Gen 9 test ROM and the Area Zero test builds were made before it and still have the old bar; they get it when
  they are next rebuilt (the Gen 9 one differs from a rebuild in these 108 bytes only).

## A PLAYER'S REPORT: FOUR THINGS — 2026-10-09 — `patches/shinyfade/`, `patches/evivpal/`, `patches/mistmsg/`
- The report (RetroArch, mGBA core, dx11, fast-forward 5-6x): "EV/IV displayer has graphical bug when showing certain
  pokemon sprites; golden health bar for shinies has some graphical bug; mist in the rusturf tunnel can cause
  graphical bug; one time I was selecting something in my journal, the emulator got frozen". Each was looked for
  in the dev mGBA with scripted tests, on the working ROM and, as controls, on the untouched original
  (`roms/original`) and the translation-only ROM. Scratch work: `_testrun/report/`.
- **Gold healthbox (ours).** shinybox's paint wrote the 16 gold colours into palette RAM and both palette buffers on
  every battle frame. A fade works in the buffers, so the gold was put back at full brightness each frame and the
  box stayed lit on a black screen through every fade (the Bag, the party, the end of a battle) - the palette RAM
  write alone was enough, since it lands mid-frame after the VBlank copy. `shinyfade`: shiny_boxes' only
  `bl paint` (0x08FDA15E) goes to paint2 (0x08FF7640..0x08FF76C4): the gold goes into the unfaded buffer when it is
  not there, and into the faded one only while the stock box palette (tag 0xD6FF, found through
  sSpritePaletteTags) is shown unfaded too - so whatever fades the plain box fades the gold one, normal and fast
  fades alike, and a box made again after the Bag (faded buffer black, unfaded still gold) is put right as soon
  as the screen is. Palette RAM is left to the VBlank. `test_shinyfade.lua` (wild battle, both battlers shiny the
  way shinybox reads it; watches palette RAM colour 2 of the gold slot against the stock box's every frame into
  the Bag, back, and while running away): PASS; the old build fails both fades (the gold 1.00 brighter, lit on
  every black frame).
  * gPaletteFade (0x02037FD4) in this ROM, as vanilla: +0 selected palettes, +4 bits 6-10 y, +6 bits 0-14 blend
    colour and bit 15 active, +9 bits 0-1 mode. Not needed in the end; written down because it cost a look.
- **EV-IV Display (the hack's own).** The screen (item 650, 0x09689000..; main task 0x0968A960, "show this
  Pokemon" 0x0968A7C8, the picture 0x0968A6C0, each picture's slide task 0x09689590 with its sprite in data[2])
  builds the next Pokemon's picture first and lets the old picture's task remove the old one on its next run. The
  picture asked for its palette by tag, and the hack's palette tables (0x08F25520, shiny 0x08F27AA0; 8 bytes a
  species, tag at +4) give species 1-439 their own number and the other 760 tag 1 (588) or 0 (172), shiny 501 /
  500. LoadSpritePalette returns a tag that is loaded without loading it, so between two Pokemon with one tag
  (any two from No. 440 on, mostly, or Bulbasaur and one of them) the new picture kept the old colours; the old
  task then freed the slot under it. Found by fuzzing the screen (random D-pad at random moments; every settled
  frame compared with a plain sweep of all 1,197 species - all of which draw correctly one at a time) and a
  per-frame trace of the tags. `evivpal` rewrites the picture routine in place (0x0968A6C0..0x0968A743, one caller,
  no pointer to it; 120 bytes + padding): a palette slot instead of a tag, 15, or 14 when the picture on screen has
  15, through the game's own CreateMonPicSprite_HandleDeoxys (the Pokedex's way). The tables are left alone.
  `test_evivpal.lua`: A -> B -> A for five pairs, the picture's 15 colours against a fresh open of each species:
  PASS; the old build fails the three shared-tag pairs. Fuzz: 24 of 400 rounds wrong before, 0 of 700 after;
  shiny and egg pictures pixel-identical to before.
- **Mist (the hack's own).** Its field message box is see-through. ShowFieldMessage's task is chosen at 0x08DEDF2E
  (reached from the trampoline at 0x080981BC): the hack's (0x08DEDE7A) unless the flash level is not 0 or its option
  byte SaveBlock2+0xE68 is set, then the game's Task_DrawFieldMessage. The hack's task calls 0x08DEDE42: WIN0 over
  the box, BLDCNT 0x1E41 / BLDALPHA 0x0710 written straight to the registers; at the end 0x08DEDED4 writes
  0x1E40 / 0x080C. BLDALPHA is what the weather's see-through sprites use: in fog (weather 6, 9 - Rusturf Tunnel is
  6) and the underwater haze (10, and 14 on the underwater maps) the fog turned nearly opaque while a message was
  up; and 0x080C is the fog's own
  value, so after any message ash and sandstorm (0x0010) and the haze (0x1004) were drawn wrong until a map load.
  The see-through box also explains the black Yes/No box seen there. `mistmsg`: the two flash-level tests (the task
  chooser 0x08DEDF34 and the text-colour prefix at 0x08DEDF04) load gSaveBlock1Ptr from one literal
  (0x08DEE028, nothing else reads it), which now holds plain_box; `ldr r5,[r5]; adds r5,#0x30; ldrb r5,[r5]` became
  `bl <the blob's bx r5>; mov r8,r8`. plain_box (0x08FF770C) answers like the flash level, and "plain" when
  GetCurrentWeather is 6, 9, 10 or 14: the game's own white box with dark text, as in dark caves. The end routine's
  register write (0x08DEDEE4) is `bl restore`: BLDCNT / BLDALPHA from SetGpuReg's copy (sGpuRegBuffer 0x03000818
  +0x50, read as one word). Code 0x08FF7704..0x08FF7744, between the chance words 0x08FF7703 and 0x08FF7785.
  `test_mistmsg.lua` (weathers 0, 1, 6, 7, 8, 9, 10, 14 by setweather, then Rusturf Tunnel): PASS; the old build
  fails 9.
  * Which weathers: a survey (`_testrun/report/weather_survey.lua`: every weather on Route 102, the OAM entries in
    semi-transparent mode and the game's copy of BLDALPHA) - see-through sprites in 1 (3 clouds, 12 / 8), 6, 9, 10,
    14 (20 fog sprites, 12 / 8 or 4 / 16), 7 and 8 (ash, sand: 16 / 0, drawn at full strength); none in the rest. A
    message whites out 6, 9, 10 and 14; ash and sand only get a little lighter, the clouds of the one cloudy map
    nothing to see, so those keep the see-through box.
  * Every mist location (asked for after the first install, which had missed 14): `mistmaps.py <rom>` lists the maps
    whose header weather is 6, 9, 10 or 14 from gMapGroups (0x08A54698 here, 38 groups, 789 maps) - 37: 15 fog
    (Rusturf Tunnel, Mt. Pyre Summit, Phoebe's room, Seafloor Cavern 9, Cave of Origin B1F and two unused rooms,
    Marine and Terra Cave ends, six of the hack's maps in groups 34-36), 2 diagonal fog (34/6, 35/36), 20 underwater
    (14). No map uses 10. Only Mt. Pyre Exterior (24/21) turns fog on by script: three trigger tiles at (24-26, 21)
    and its on-transition script above row 12 (both `setweather 6` at 0x08231FD2 / 0x08231FED); no other trigger
    or map script sets a mist weather. `test_mistmaps.lua` warps into each of the 37, then into Mt. Pyre Exterior
    from the summit and onto its trigger, and checks the registers with a message up and after: 39 of 39; the
    first install fails the 20 underwater maps.
  * GOTCHA: the hack carries the message-box blob four times - 0x08DEDE1E (live), 0x094A2C34, 0x09811A.. and
    0x09F004.. - older copies with no caller from the game. The first fix went into 0x094A2C34 and changed nothing.
    Find the live one from the vanilla function's trampoline, not from a search for the constants.
- **Journal freeze: not reproduced.** `fuzz_questlog.lua` (in `_testrun/report/`) opens the Quest Log from the ring
  or the Start menu and presses random keys with random holds, long ones too (fast-forward); it watches for an
  emulator crash, the main loop standing still (SaveBlock2's play-time frame counter stops while frames go on),
  and a screen B no longer leaves. 1.25 million frames, about 1,700 visits and 74,000 keys on the old and the new
  build: nothing. Not tried: opening it from the Bag, and a save whose Quest Log shows other rows than the test
  save's. Its first "freeze" was the fuzzer pressing A+B+START+SELECT, the soft reset; START is out of its keys.
- Test-side lessons: on the working save the first step after loading is "The Repel ended... Use another?", and a
  Pokenav call can take any step - tests that step onto something answer such scripts and try again. A frame
  callback keeps running through the game's lag frames: the EV-IV display needs ~9 video frames for one switch,
  and memory read inside them shows the half-done state.
- Chain: the three go after `dexnavabil`, before `zhtext`. `_testrun/rel18/rebuild_chain.py` gives the scratch
  build byte for byte (sha1 f0acd977...); 346 bytes differ from the ROM before them: 08DEDEE4 (6), 08DEDF06 (6),
  08DEDF36 (6), 08DEE028 (4), 08FDA15E (4), 08FF7640..76C3, 08FF7704..7743, 0968A6C2..0968A743. speciesx, gen9
  (`check_gen9.py` clean) and paldea still apply on top; `test_dexnavabil.lua` and `test_dexnavui.lua` unchanged.
- Installed 2026-10-09 (sha1 3e352b3a...), backup "(before shinyfade evivpal mistmsg 2026-10-09)" (22806e2f...); the
  underwater fix the same day (sha1 f0acd977...), backup "(before mistmsg underwater 2026-10-09)" (3e352b3a...).
  In no release. The Gen 9 and Area Zero test builds are made from the working ROM and get these when rebuilt.

## A SECOND REPORT: TEXT PAST THE BOX, EGG MOVES, CHASE — 2026-10-10 — `patches/textfix/`, `patches/eggmoves/`, `tools/text_overflow.py`
- The reports: (1) "Chase's post-battle dialogue is still in Chinese"; (2) "a Sailor NPC in Slateport, near Captain
  Stern, whose dialogue is too long and extends beyond the text box border"; (3) "Cosmic Power is a Gen 8 egg move
  for Buneary but breeding with a male Smeargle fails - please check all Pokémon". Scratch work: `_testrun/report/`.
- **Text past the box: the cause.** `translation/inserter.py` wraps a page at 34 characters (`wrap_page`), not at
  a width. The field message box is 27 tiles, 216 px, and the font is proportional (widths at 0x086542E4, one byte
  a glyph, 0x200 of them: the `F9 xx` extra symbols are entries 0x100 + xx; a space is 3 px, most letters 5-6). A
  line of wide letters reaches 216 px before 34 characters. Past the edge the printer does not clip: the line
  wraps round inside the window's row and draws over its own start (the sailor's "You should visit the Weather
  Institute and ask around!" showed as "'yound!ould visit the Weather Institute ar"). The ▼ is drawn after the
  last letter, so it is cut too when a line ends within 8 px of the edge - cut only, nothing is drawn over.
- **The sailor**: Slateport Harbor (9/9), object 2 at (4,12), script 0x0820CC52, text 0x0820D08E - shown once the
  game-clear flag 0x864 is set and flags 0x1BE / 0x1BF (Emerald's Kyogre and Groudon ones) are not both. Its
  last page was one line of 288 px (the translation gave that page no break at all).
- **The scan**: `tools/text_overflow.py <rom>`. Every text a script shows in that box - `0F 00 <ptr> 09 nn`
  (msgbox: loadword 0 + callstd 0-6), `67 <ptr> 66` (message + waitmessage), trainerbattle (`5C`) intro and
  not-enough-Pokémon texts - 9,965 of them, each line measured; trainer defeat texts (1,474, shown in battle)
  apart: none is over, at 216 or at 208 px. `{PLAYER}` and `{RIVAL}` count as 42 px, the widest 7-letter name;
  texts with a Chinese lead byte are skipped, a glyph the tool has no name for counts with its own width. A
  wider net (any `0F 00 <ptr>`, any `67 <ptr>` in the hack's script block) adds 38 texts and nothing real (a
  Pokédex description, a blank line). Result on the ROM before: 55 texts.
- **The fix** (`textfix_patch.py`, two new lists; every page was chosen by hand from the tool's suggestion):
  * `BREAKS`, 56 pages in 52 texts: only spaces and line breaks swap places (0x00, 0xFE, 0xFA), so each text
    keeps its length and its address; the patcher refuses an entry that changes anything else, or whose old page
    is not in the text exactly once. A page's first break is `\n`, the later ones `\l` (scroll), as the game's
    own texts do - a page may gain a line that way. Where a page was re-broken, lines followed by the ▼ were kept
    to 208 px. (Elsewhere 83 texts still have a line of 209-216 px before a scroll or a new page, 99 lines: the
    arrow is hidden or cut there and nothing else happens; left alone.)
  * `REWRITE`, two pages that get shorter (the bytes left over become 0xFF): "-------------GAME OVER-------------"
    (0x09837591, Lilycove rooftop; it had 13 + 16 dashes, 225 px), and the tablet of the statue about the three
    Regis (0x08BBF100, sign script 0x08A7FFBC). That text had **no 0xFF**: its last page ran straight on into
    the text at 0x08BBF1B9 ("A battle? Of course, but I need to get ready first.", which the pointer table at
    0x082EE83C names). "When gathers the three Pokémon," became "When the three Pokémon gather," - one byte
    shorter - and the 0xFF went into the byte that freed, 0x08BBF1B8; the next text is untouched.
- Checked before patching: all 54 texts are byte for byte what the v1.4 base has (no later patch writes them)
  and none is in `zhtext`'s files, so `textfix`, which runs before `zhtext`, sees them as they are. Pointers into
  the middle of the texts (every 4-byte value in the ROM that lands inside one): one real one, the msgbox at
  0x0985D254 / 0x0985D262 -> 0x0985DE3B, further on than the bytes that change. 0x0985DB6F (Ever Grande) and
  0x0985DC7A (map 35/54) end in the same bytes - one entry.
- Tests (`_testrun/report/`): `showtext.lua` shows any text address in the real message box (a script with
  loadword + callstd 4) with the player's name set to "MMMMMMW", a screenshot per press - all 58 pages were looked
  at; `sailor.lua` warps to the Harbor and talks to the sailor. The tool on the new ROM: 0 texts.
- **Egg moves: what the hack's table is.** 0x09D78128..0x09D7973C: `species + 20000`, that species' moves, ...,
  0xFFFF. `eggcheck.py` / `eggmissing.py` compare every list with the official games' egg moves by version group
  (PokeAPI's CSVs: `pokemon_moves.csv`, method 2). Of 381 lists: 296 are one game's list exactly (220 Sword/Shield's;
  Pokémon that are not in Sword/Shield have BDSP's, USUM's or Scarlet/Violet's); 53 are such a list plus moves no
  game gives by breeding - old event moves the author added (Pichu Volt Tackle / Petal Dance / Sing, Skitty Pay
  Day, Charmander Block / Howl / Quick Attack, Magikarp Dragon Rage...); 30 mix two games' lists or leave some
  moves out; two were broken. Regional forms have their own lists under their own species ids (Alolan Rattata
  856, female Indeedee 1178).
- **The two broken lists (the original hack's).** Mr. Mime (122) and Mime Jr. (492) had no marker. Where
  `20122` belongs, after Goldeen's five moves, the table has 53 (Flamethrower), and where `20492` belongs, after
  Bonsly's six, 107 (Minimize) - each followed by the Mimes' five moves (Hypnosis, Fake Out, Confuse Ray, Power
  Split, Tickle; Sword/Shield's list). So those moves, and Flamethrower / Minimize, were read as Goldeen's and
  Bonsly's, and the two Mimes had none. `eggmoves_patch.py` writes the two markers (0x09D78478, 0x09D78E40) after
  asserting the move id there, the five moves after it, the species whose list it ran on from, and that the
  species has no list yet. Goldeen and Bonsly are left with Sword/Shield's lists exactly.
  `test_eggmoves.lua` (the game's own `_GiveEggFromDaycare`), before -> after: a Mr. Mime pair's Egg (a Mime Jr.)
  with a father knowing Fake Out, Tickle, Hypnosis: none of them -> all three; mother knowing Confuse Ray, Power
  Split: none -> both; Goldeen with a father knowing Flamethrower, Hypnosis, Haze: all three -> Haze only;
  Sudowoodo pair (a Bonsly) with Minimize, Tickle, Curse: all three -> Curse only. The eleven older cases
  read the same.
- **Buneary and Cosmic Power: not a bug.** Buneary's list is Sword/Shield's nine (Circle Throw, Copycat, Double
  Hit, Fake Out, Flail, Focus Punch, Sweet Kiss, Switcheroo, Teeter Dance); a Smeargle father passes Fake Out in
  the test and not Cosmic Power. Cosmic Power is Buneary's egg move in X/Y to USUM and in BDSP; in Sword/Shield
  it is TR44. The hack's tutor list (0x08FD80B8, 127 moves) is the TRs - Cosmic Power is entry 44 - and
  Buneary's bit for it is set (0x09750000, 16 bytes a species). Which NPC teaches it was not looked for.
  Giving every Pokémon the union of Sword/Shield's and BDSP's lists would add 511 moves to 133 species: a change
  to what the game is, not a fix; not done.
- **Not fixed: Duraludon (species 274) has no list.** Sword/Shield gives it Mirror Coat, Night Slash and Slash.
  A list for it has to be appended, which moves the 0xFFFF (0x09D7973C; 418 bytes of 0xFF follow) and needs the
  search bound raised wherever it is held (the literal 0x0B09 at 0x08070464, the readers at 0x080703F0 and
  0x08070468, dexnavchain's 0x08FDEAE0). `gen9_patch.py` appends its own lists there and asserts the end and the
  bound it found: add Duraludon's there, or teach that patcher to take both from the ROM first.
- **Chase: already fixed.** Fortree City (0/4), (19,4); flag 0x4170 set and 0x4171 clear make him battle
  (`chase.lua` plays it: hack flags above 0x4000 are not in SaveBlock1's flag array - set them with the script
  commands `29` / `2A`). The line he says when beaten (0x0982CAE0 in the v1.6 ROM, Chinese there) is one of the
  trainer lines `zhtext` translated for v1.8; on the current build everything he says is English. "Player
  defeated PkMn Trainer Chase!" is Emerald's own wording, not a missing name.
- Chain: unchanged (both are patches already in it). `rebuild_chain.py` gives sha1 71ed64dc...; 171 bytes differ
  from the ROM before: 167 in the 54 texts (all of them space / break swaps but the two rewritten pages) and the
  two markers. speciesx, gen9 (`check_gen9.py` clean) and paldea still apply on top.
- Installed 2026-10-10 (sha1 71ed64dc...), backup "(before text overflow egg markers 2026-10-10)" (f0acd977...).
  In no release. The Gen 9 and Area Zero test builds are made from the working ROM and get these when rebuilt.


## OBJECTS' PALETTES GIVEN BACK — 2026-10-10 — `patches/objpal/`

Reported on the Area Zero test build (screenshot: Walking Wake on the channel above the waterfall in a red crystal's
colours): "sometimes the static legen such as walking wake, koraidon, etc.. will have inveted visual graphical
glitch". A bug of the original hack, in every map.

- **The hack's allocator.** Objects (people, Pokemon, item balls) get their sprite palette by tag from 0x094A356A,
  called from the hack's two hooks at 0x094A3356 (spawning: `ldrh r0, [r7, #2]` = graphicsInfo->paletteTag) and
  0x094A3362 (changing an object's graphics). It looks for the tag in slots 4-9 (sSpritePaletteTags 0x03000CF0),
  else an empty one there, else writes it into slot 10, and loads the palette with 0x0808E91D (tag, slot:
  FindObjectEventPaletteIndexByTag + LoadPalette). Nothing is given back until the field is loaded again. The
  graphics info's paletteSlot means "by tag" for every slot but 0 (the player) and 10 ("special": loaded straight
  into slot 10, no tag). In the field the general sprite palette allocator starts at slot 12 (weather 0x1200/0x1201
  at 12/13, field effects at 14), so only objects use 4-10.
- **Slot 10 is no good.** Measured with the user's own save on the Area Zero build: round the crater, Surf, then
  Waterfall up to Walking Wake, the seventh kind. Its tag went into slot 10, and slot 10 held the red crystal's
  colours (slot 4's) in gPlttBufferUnfaded, gPlttBufferFaded and palette RAM alike: something of the hack's writes
  slot 10 again, most likely the reflections (the crystals stand by the ponds). So the seventh kind is already in
  borrowed colours, and the eighth takes the tag from the seventh. Which one it hits depends on the way you walked.
- **The fix** (`objpal.s`, 132 bytes at 0x08FEF600, in the unreferenced 0xFF run 0x08FED3C8..0x08FEFE00): the
  hack's function starts with a jump to it (10 bytes, `014b1847c046` + word: it is 2 past a word; r3 is free at a
  call; the rest of the old body stays and no longer runs). It looks for the tag in 4-9, then an empty slot in
  4-9, then a slot in 4-9 that no sprite in use draws with (gSprites 0x02020630, 64 x 0x44 bytes: in use = bit 0
  of the halfword at +0x3E, palette = top 4 bits of OAM attribute 2 at +4), and only then slot 10. A thing that
  goes out of sight loses its sprite (RemoveObjectEventsOutsideView), so its slot comes back for the next kind.
  With six kinds or fewer on a visit it chooses exactly as the hack did.
- **What it cannot do.** TrySpawnObjectEvents runs before RemoveObjectEventsOutsideView in the same frame, so as
  you walk the screens of two neighbouring tiles are briefly alive together; more than six kinds in that union
  still fall to slot 10. In the game: `_testrun/objpal/busy_maps.py` (graphics info by template: the main table
  0x08505620, the hack's own 0x0839CF00 + 0x24 * n for graphics 0x4E) finds eight maps with more than six kinds
  (35/49 8, 37/104 8, 35/87 7, 35/40 7, 35/8 7, 34/94 7, 26/40 7, 34/42 7) and at most eight within one screen.
  check.py of Area Zero now refuses more than six kinds within one screen of any tile (`colours()`).
- **The test harness** (`patches/paldea/test_paldea.lua`, used for the game itself too): `PALWATCH=1` watches every
  sprite in use in slots 4-10 each frame (its slot's tag must not change while it lives) and every 8 frames whether
  the slot shows that tag's colours (the field palette table through the literal at 0x0808E8BC; the copy keeps
  vanilla's zero row 35 inside it, so a search must stop at 0x11FF only; only while the player's slot is not being
  faded, and only if wrong at two looks running). It flags Walking Wake on the old Area Zero build and nothing on
  the fixed one. Steps `objpal` (each object's sprite and slot, the slots' tags and colours), `roam` (walk about
  with a fixed round of keys, B through talk, battles won) and `seed` (gRngValue set: the hack seeds it from the
  clock, so two runs only match picture for picture from a common seed; a map load can still draw on it
  differently, through the clock's events, and then people step and turn otherwise).
- **Tested.** `_testrun/objpal/rebuild_chain.py` (the chain with `objpal` before `zhtext`) gives the same bytes as
  objpal_patch.py on the working ROM (sha1 f5ee5822...); without objpal it gives the working ROM before (71ed64dc...).
  `_testrun/objpal/objpal_tests.ps1`: from the working ROM's save, the same keys on the ROM before and after, at
  the first door of the eight busy maps (4,000 frames each) and of eleven towns (2,400), the watchdog on: all 38
  runs finished; the eleven towns and six busy maps the same picture for picture (36 or 23 pictures each); 35/8
  and 26/40 differ by people's steps and turns only (the same slots and tags in both at every dump; the roam went
  through a door on 35/8), and the watchdog's one finding, a sprite of the hack's own in slot 10 on 37/104 (tag
  0x27F9, callback 0x081731FD: not an object), is the same in both. Three busy maps had none of their people out
  in that save (35/49, 34/94, 34/42: story flags). The seventh-kind case itself is the Area Zero one (the user's
  save, Surf and Waterfall up to Walking Wake): the old build flagged, the new one and the Area Zero build made
  from the new working ROM clean. speciesx, gen9
  (`check_gen9.py` clean) and paldea still apply on top; paldea sees the allocator in its base and leaves it
  (`patches/paldea/objpal.py`, which brought the same code to the Area Zero build first, in its second blob).
- Installed 2026-10-10 (sha1 f5ee5822...), backup "(before objpal 2026-10-10)" (71ed64dc...). In no release. The Gen 9
  and Area Zero test builds are made from the working ROM: rebuilt, they take the allocator from it.

## TORNADUS AND THUNDURUS ROAMED HOENN AFTER CONTINUE — 2026-10-10 — `patches/roamfix/`

Asked by the user: "can u make sure that tornadus can be encountered correctly with news tracker".

- **How the storms work** (the hack's own, traced here for the first time). The Valley Windworks researcher
  (36/54, object 2 at 10,12, script 0x0987A93F): with 0x42E1 set he is done; `callnative 0x08FF0611` is
  GetSetPokedexFlag(0x8005, 0x8004) -> 0x800D (caught 645: the Drifloon gift and 0x42E1; then 641 and 642).
  First talk (0x42DE clear): `callnative 0x08FF1731` returns the active roamer's species (SaveBlock1 + 0x31DC:
  species +8, hp +0xA, level +0xC, active +0x13), and if there is one he only says "What lovely weather" -
  the game has one roamer slot, so while Latias or Latios still roams Hoenn the storms cannot start.
  Otherwise `setvar 0x8004, 2; special 299` and 0x42DE. Tornadus caught and Thundurus not: mode 3. Both: the
  Celestic shrine hint and 0x42E0. Played (`_testrun/tornadus/steps_block.lua`): with Latios active he says his
  one line, 0x42DE stays clear and Latios stays the roamer. Read from the script, not played: a storm that is
  knocked out is set inactive as any roamer (vanilla), and with 0x42DE set and it not caught he only says "I'm
  counting on you!" - nothing starts it again.
- Special 299 is the game's InitRoamer (0x08161CBC). Its CreateInitialRoamerMon is a trampoline (0x08161B94) to
  the hack's 0x09F06118: mode 0 Latias (407), 1 Latios (408), 2 Tornadus (0x2B6 = 694), 3 Thundurus (0x2B7 = 695),
  Lv 40. For 2 and 3 it writes map group 0x24 into sRoamerLocation (0x0203BC86: group, map) and takes the map
  from the hack's Sinnoh table, 0x09F0AACC: 27 rows of 6 bytes like the game's Hoenn table (0x085CEC30, 20
  rows): Routes 201-223 (36/15 ... 36/42), each with the routes it moves on to (0xFF = none). All 27 have wild
  Pokemon; Routes 219, 220 and 223 on water only. The game's RoamerMoveToOtherLocationSet (0x08161D00) and
  RoamerMove (0x08161D54) are trampolines to the hack's 0x09F062D0 and 0x09F06340, which pick the Sinnoh table
  when the group byte is not 0 (a warp: any other row; a walk onto another map: 1 in 16 any row, else one of the
  row's neighbours, never the map two back in the history). IsRoamerAt (0x08161DE8) and TryStartRoamerEncounter
  (0x08161EDC: on the roamer's map, one wild battle in four) are vanilla. The News Tracker (item 695,
  0x09F063F0) prints the species, "Sinnoh" or "Hoenn" by the group byte, and the map's section name.
- **The bug.** sRoamerLocation is EWRAM and not in the save. After Continue the group byte is 0, the first move
  (Continue moves the roamer once) picks a Hoenn row, and from then on Tornadus or Thundurus is a Hoenn roamer:
  "The roaming Tornadus is located in Hoenn on Route 130", met there (mostly sea routes). In one sitting
  everything was right. The working ROM's own test save had Tornadus active at 0/43 on loading.
- **The fix** (`roamfix.s`, 88 bytes at 0x08FEF700): the two trampoline words (0x08161D04, 0x08161D58) point at
  stubs that write the group 0x24 if the roamer is active and its species is 694 or 695, then go on to the
  hack's routines (both take no arguments; lr is put back before the jump). Latias and Latios, and no roamer at
  all, pass through untouched. Nothing is saved.
- **Tested** (`patches/roamfix/test_roamfix.lua`, steps for `patches/paldea/test_paldea.lua`, whose new steps
  are `roamer`, `clearroamer`, `setroamer`, `script`, `tracker` - the News Tracker used from the SELECT ring, its
  message read from gStringVar4 - and `hunt`): the researcher starts Tornadus on a Sinnoh route; the tracker
  names that route each time (after a warp, on your own route, after the battle); it is met in the grass of
  Route 201 at the 3rd battle, Lv 40, and moves on; after a save, a reset and Continue it is still in group 36,
  the tracker says Sinnoh, and it is met again (2nd battle); Thundurus the same through a reset; Latios stays in
  Hoenn before and after. With `OLD=1` on the ROM before: Tornadus "in Hoenn on Route 122", Thundurus "on Route
  118" after the reset. `_testrun/tornadus/steps_none.lua`: no roamer, warps, walking in three places, a save
  and a reset: nothing changes, "No news received". The chain with `roamfix` after `objpal` gives the same bytes
  as the patcher on the working ROM (72ca49d2...); speciesx, gen9 (`check_gen9.py` clean) and paldea apply on top.
- Installed 2026-10-10 (sha1 72ca49d2...), backup "(before roamfix 2026-10-10)" (f5ee5822...). In no release.
- Not changed, worth knowing for the guide: the storms cannot start while a Hoenn roamer is still active; a
  storm that is knocked out does not come back; on Routes 219, 220 and 223 it is met only while surfing.

## A SPRITE'S MISSING PICTURE COPIED OVER VIDEO MEMORY — 2026-10-11 — `patches/sprframe/`

A player's report on v1.8 (Pizza Boy A, a phone, fast-forward on), with a picture: "Hisui Region visual glitch -
it gets fixed only after I battle a pokemon, then again it is cooked again". Prelude Beach (37/104) from (18,24):
the ground in blue and green stripes on black, the palms and the water right, the player and most people gone, one
person as coloured noise.

- **The cause** (the hack's own; the same bytes in the original ROM). A sprite that is not drawn from a sheet has
  the picture of animation frame n copied from `images[n]` = {address, u16 size} of its picture table: the game's
  RequestSpriteFrameImageCopy (0x08007488) queues {address, where in sprite memory, size} in sSpriteCopyRequests
  (0x02021838, 12 bytes each, the count at 0x02021835) and ProcessSpriteCopyRequests (0x0800742C) does the copies
  in the vertical blank with the BIOS's CpuSet. Nothing checks n against the table's length. Some of the hack's
  wandering wild Pokemon (graphics id 78 with the template's fourth byte N: the record at 0x0839CF00 + 0x24 * N)
  have a picture table shorter than the animation table they are given. The one at sea off Prelude Beach (local
  id 8, N = 0x23, record 0x0839D3EC) has 3 pictures at 0x092979F4 and the 7-frame table 0x085090B0 (0-2 facing
  south / north / west, 3 and 4 walking south and north, 5 and 6 walking west and east). After its three pictures
  come 14 bytes of 0xFF and the sprite's own graphics, so frames 3 to 6 read {0xFFFFFFFF, 0xFFFF},
  {0xFFFFFFFF, 0xFFFF}, {0, 0} and {0x22BB0000, 0xB000}. The one on the sand by (25,21) (local id 13, N = 0x36) has
  7 pictures and a 9-frame table: frames 7 and 8 read {0x05300200, 0x0B90} and {0xE0FF28E0, 0xE039}.
- **What a copy does.** It starts at the Pokemon's own picture (sprite cell T) and runs on: over the pictures of
  every sprite after it; from 0x06018000, which is sprite memory again, over every sprite before it; and from
  0x06020000, which is 0x06000000 again, over the first cells of the map's first tileset. A sprite heals when it
  next changes its frame (people who stand still do not); the tileset is loaded once per field and stays as it is
  until a battle, a menu or a door rebuilds the field - "fixed only after I battle".
- **Which copies are made depends on the BIOS.** A real BIOS (and mGBA's) refuses a CpuSet whose source starts
  or ends below 0x02000000. Measured in mGBA on the working ROM (the harness's BADCOPY, video memory before the
  call against the next frame):

      {0xFFFFFFFF, 0xFFFF}   65,534 bytes   refused (the end wraps round to 0x0000FFFD)
      {0xE0FF28E0, 0xE039}   57,400 bytes   refused
      {0x22BB0000, 0xB000}   45,056 bytes   made: 992 to 1008 of the 1024 sprite cells changed - every sprite on
                                            screen a block of stripes (mGBA answers BA FF FF FB for memory that is
                                            not there)
      {0x05300200, 0x0B90}    2,960 bytes   made: palette memory over the Pokemon's own cells and the next 92 -
                                            it and its neighbours as coloured noise

  So on a console and in mGBA the bug is sprites that turn to stripes or noise for a moment (and stay so if they
  stand still); the tileset is reached only if T is 640 or more. An emulator whose BIOS does not refuse (Pizza
  Boy's own) makes all four, and the 65,534-byte one from cell T ends at 0x06020000 + 32 * T - 2.
- **The report's picture, to the byte.** From a dump of video memory at the same spot (the harness's `vram` step)
  and the picture (`_testrun/tornadus/locate.py`, `forensic.py`, `inverse.py`, `ticks.py`, `simulate.py`): the
  stripes' colours do not follow each tile's palette, so they are not the ground's tiles alone - they are the map's
  empty top layer (BG1, cell 0, palette 0: index 11 is that blue, 15 that green) over ground cells that hold the
  same bytes and so show black between. Every row of cells 0 to 91 holds BB 00 FF 00, up to and with byte 0xB7D;
  byte 0xB7F is the tileset's own (one tan pixel pair per sand tile, the last byte of cell 91); cells from 96 on
  are right. 0xB7E bytes = 32 * 92 - 2: a 65,534-byte copy from sprite cell 92. Drawn with those bytes the dump
  gives the report's picture (85% of the screen within tolerance; `_testrun/sprframe/report_explained.png`).
- **How it was found** (it does not show in an ordinary walk in mGBA: 0 findings from the tile and sprite
  watchdogs in 60,000 frames). mGBA's own log, written to a file (`run.ps1 -MoreArgs "-l 79 -C logToFile=1 -C
  logFile=<path without spaces>"`), had 22,528 lines "Bad memory Load16: 0x22BB0000.." in a row, a few times per
  run on the water. A read watchpoint there (the harness's `WATCHADDR=r:22BB0000`) stopped inside the BIOS with
  r1 = 0x06010480, r2 = 0x5800 and 0x0800745D on the stack - ProcessSpriteCopyRequests - and the sprite whose
  animation was at frame 6 with a 3-picture table was local id 8.
- **Where else** (`_testrun/sprframe/survey.py`: every walking map object, its record's pictures counted against
  the frames of animations 0-7). Eleven objects on seven maps; nine can have a copy made on some emulator, and
  seven of those are Hisui's wandering Pokemon: 37/103 local 15; 37/104 locals 8 and 13; 37/105 locals 4, 6 and 15;
  37/106 local 6 - hence "Hisui Region". Also 36/27 local 22 (a 1-picture record that walks a route; its missing
  frames are refused by a real BIOS). 34/79 local 6 is listed with pictures of another size than its record
  says: not looked into.
- **The fix** (`sprframe.s`, 60 bytes at 0x08FEFA20). The 8 bytes of ProcessSpriteCopyRequests at 0x08007454
  (`ldrh r2, [r2, #8]; lsrs r2, r2, #1; bl CpuSet`) are `ldr r3, [pc, #0]; bx r3; .word guard`. The guard makes the
  copy (its own `svc 0x0B`, at 0x08FEFA4E) only if the address is in 0x02, 0x03, 0x08 or 0x09, the size is 1 to
  0x1000 and where + size is not past 0x06018000; then it goes back to 0x0800745C. A dropped frame leaves the
  sprite's picture as it was: those Pokemon glide in a standing picture (for a third of a second in the one of
  the way they faced before). The copies the game really makes are 0x40 to 0x800 bytes from the ROM or, for a
  Pokemon's battle picture, from EWRAM.
- **Tested** (`patches/sprframe/test_sprframe.lua`, steps for `patches/paldea/test_paldea.lua`: ten seconds
  beside local 13 on the sand, Surf out to local 8, fifteen seconds there). Without the fix 13 of 5,742 copies
  were bad ones; with it 19 bad ones were asked for, none was made, and the 5,720 good ones asked for were all
  made; the tileset's cells as they were. `_testrun/sprframe/sprframe_tests.ps1`: the objpal tests' 19 maps, the
  five Hisui maps, a walk with the menus (R, SELECT, START, L) and Surf with wild battles - 26 runs, 40,950 copies
  asked for, 55 bad ones dropped (Prelude Beach and Coronet Highlands), 40,895 made, every run finished. The chain
  with `sprframe` after `roamfix` gives the same bytes as the patcher on the working ROM; speciesx, gen9
  (`check_gen9.py` clean) and paldea apply on top.
- Installed 2026-10-11 (sha1 7d2700d8...), backup "(before sprframe 2026-10-11)" (72ca49d2...): 68 bytes in two
  places. In no release, and not in the Area Zero test builds (their Gen 9 base is older).
- **For the harness** (`patches/paldea/test_paldea.lua`). This mGBA build's breakpoints and watchpoints do call
  back (`_testrun/tornadus/wp`: the skill said they did not). New: `WATCHADDR=r:<hex>` (registers, stack, every
  sprite's animation frame and what its table holds for it, a picture and a dump on the next frame);
  `BADCOPY=1` (a breakpoint on the copy: the bad ones by kind, what each changed, the good ones by size; on a ROM
  with the fix `BADCOPY_AT` and `BADCOPY_IN` are the two addresses the patcher prints, `BADCOPY_MUST=none|some`
  the verdict); `BIGWRITE=1` (4 KB blocks of video memory and EWRAM changed in one frame: noisy, every step moves
  ten of EWRAM's); steps `vram`, `cells` (keep / check the tileset's first 400 cells), `lockstate`.
  Gotchas: PowerShell variables ignore case - a parameter `$Mgba` in run.ps1 was overwritten by its own `$mgba`
  (the emulator's path), which then went into the argument list and the script never ran; values passed with
  `-Extra` stay in the PowerShell session for the next run of the same command (an `OLD=1` leaked into the
  run after it); a script that walks a wanderer (`lockall`, `applymovement`) stalls one run in three, fix or no
  fix; Surf is fast in this game, so the harness's `step` goes two tiles on water - `slide` goes one.

## ONE ROM: GEN 9 AND AREA ZERO IN THE WORKING ROM — 2026-10-11

The user, after being handed the main game and looking for Area Zero in it ("where the hex is area zero???????"):
"everything should be into one rom now? area zero plus everything fix, change?" Until then the working ROM was
the main chain's result and Gen 9 and Area Zero lived in test builds on a base from v1.8.

- **What the working ROM is now.** The main chain (v1.4 archive, shinybox, the 42 patches to `zhtext`: sha1
  7d2700d8..., the game as every release up to v1.8 was) + `speciesx` (b27a7f0e...) + `gen9` with the Crest ROM
  (1e46d50d...) + `paldea` with the user's own `placements.txt` and `ground.txt` from `roms/test-paldea` (no
  `tiles.txt` yet) = sha1 725e63e2.... 793,403 bytes differ from the main game alone. `rebuild_chain.py`
  (`_testrun/rel18`, `_testrun/objpal` and `_testrun/full`: one file now) runs those three steps after the main
  chain, keeps the main chain's stage, and `--main` stops there; from v1.4 it gives the working ROM byte for byte.
  `_testrun/full/build.py <main rom> <out dir>` does the three steps alone and also makes the test companions
  (Area Zero with the built-in placements; Gen 9 without its battle effects).
- **The Gen 9 base** (`roms/test-gen9/Hyper Emerald - Gen 9 test.gba`, what `patches/paldea/rebuild.py` builds
  on) is that 1e46d50d... now, so every "(my placements N)" the user's editor makes has every fix of the main game.
  "(my placements 13)", made by rebuild.py right after, is the working ROM byte for byte.
- **Two names for one ROM, because of the user's emulator.** It loads the last save state of a ROM by itself when
  a ROM of that file name is opened, and keeps saves on the Desktop by ROM name. Under the working ROM's name it
  has the main game's save (75:26 of play, 30 Sept) and a state of 9 Oct (77:07, Route 116, Area Zero not begun);
  under "(my placements 12)" the newest save of the same game (77:56, Area Zero's story finished). All are one
  trainer (Jude, id 3416EBE4): the game forked on 8 Oct when Area Zero's test builds began. Their files are not
  touched: "(my placements 13)" has a copy of the 77:56 save (rebuild.py: beside the ROM and on the Desktop), the
  working ROM's name keeps what it had. The 9 Oct state was tried on the new ROM (a copy of it:
  `_testrun/full/steps_state.lua`): it loads, walks, opens the Start menu as on the old ROM, and in Mossdeep
  Jacq and the hole stand - so that branch of their game can begin Area Zero too.
- **Tested before it was installed** (`_testrun/full/tests.ps1` -> `tests.txt`):
  1. Area Zero with the built-in placements on the new base (`p21.gba`): the whole of `final16.ps1` (story 1-9,
     the craters, the vault, old saves, Mossdeep against the game without Area Zero, the user's save) and
     `journal17.ps1` - every line ok.
  2. The one ROM itself: the user's save continued; their crater walked, Surf and Waterfall up to Walking Wake
     (11,817 sprite picture copies, none bad; the palette watchdog silent); `sprframe`'s test (14 bad copies asked
     for, none made), `roamfix`'s, a walk on four maps, the menus on Prelude Beach.
  3. Gen 9's battle effects (`moves.ps1`, the build without `gen9.s` against the one with): the 116 lines of
     8 Oct's record, to the letter.
  `check_gen9.py` clean (440 literal words repointed).
- Installed 2026-10-11. Backups in `archive/`: "(before Gen 9 and Area Zero 2026-10-11)" (7d2700d8..., the main
  game alone - what a release without Area Zero is still made of) and "Hyper Emerald - Gen 9 test (the base until
  2026-10-11, on v1.8)" (cd311786...). In no release: ask before Gen 9 or Area Zero goes into one.
- **From here on.** A fix for the main game: write the patcher as before (it runs on the working ROM as it is;
  its place in the chain stays before `zhtext`), then `rebuild_chain.py` for the proof, the new Gen 9 base into
  `roms/test-gen9`, and `python -I patches/paldea/rebuild.py` so the user gets a "(my placements N)" with it -
  that file, not the working ROM's name, is the one to open for them. When the user saves placements in the
  editor, their newest "(my placements N)" is ahead of the working ROM until the chain is run again.
  The main ROM's own test save (`roms/current/....sav`, 75:00) is still what the main game's tests start from.

## JACQ BEFORE THE HOLE — 2026-10-11 — `patches/paldea/`

The user: "next before the blackhole paldea appears, we should at least have Jacq standing there talkign about
taking students on trip or something to at least make ppl know before hand there is something like a
foreshadowing? got me??"

- **What changed.** Jacq (Mossdeep's local 30, on his tile from placements.txt) is shown from the start of the
  game; up to now he came with the hole. `mossdeep_state` (run on the way into Mossdeep and on resume): Jacq's
  hide flag 0x43D4 is cleared unless the stage is 4 (the ending is over: he lives in Station No. 4); the hole's
  0x43AB is cleared only with 0x41D5, as before.
- **What he says** (`story.py`; script `jacq`). Before 0x41D5: `JACQ_EARLY`, four pages (who he is, the three
  students "off around the island somewhere", "We came for the sky ... the air over this shore has been restless
  lately. As if something were pressing on it from the other side", "It's probably nothing!"), which sets the new
  flag 0x43E2 (`F_MET_EARLY`); after that `JACQ_EARLY_AGAIN`, one line. With the hole open: if 0x43E2 is set,
  `JACQ_INTRO_KNOWN` ("You! The Trainer from before! ... The restless sky, remember?") stands for the first three
  pages of `JACQ_INTRO` and its last four follow; if not, `JACQ_INTRO` as it always was. Either way 0x43AC and
  stage 1, then `JACQ_AGAIN`. Nothing else of the story reads 0x43E2.
- **The flag.** 0x43E2 (SaveBlock2 + 0x70, bit 2) passed the checks the others did, now a script:
  `_testrun/full/flagcheck.py <rom without Area Zero> <flags>` (no script command 29/2A/2B with it anywhere in
  the ROM, no aligned word, no object hidden by it, not in the script index, clear in four saves). 0x43DE-0x43E1
  each have one chance match and are skipped, as 0x43D7 and 0x43DB were.
- **Older saves.** `STAMP_SALT` 12 -> 13. A save made in Mossdeep before 0x41D5 on the build before has Jacq's
  hide flag set; on Continue the map's people are put back before ON_RESUME works the flag out, so he came only
  with your first step. With another stamp the map is read again on Continue (the mechanism of test 11), and he
  stands there at once.
- **Not changed:** placements.txt, ground.txt, `check.py` (before the hole is the story's phase without the hole:
  fewer things on the same tiles), the Journal (its Area Zero rows still begin with 0x41D5), Mossdeep's own 29
  objects and scripts.
- **Tested** (`patches/paldea/test_jacq_early.lua`, `_testrun/paldea/jacq22.ps1` on `p22.gba`): early (Jacq and
  no hole; his talk, the second line, nothing to press where the hole will be; then 0x41D5: the hole on the way
  in, "You! The Trainer from before!", asked in, through the hole to the wall), late (never met: the old first
  talk, 0x43E2 clear), done (after the ending: the hole alone), a save of the build before made in Mossdeep before
  0x41D5 and continued. Then all of `final16.ps1` and `journal17.ps1` (`test_steps_before.lua` now expects Jacq
  alone there; "mossdeep, before" still reads as the game without Area Zero once our objects are left out), the
  user's save continued on their build, and `sprframe`'s test on it. Every line ok. The message boxes were looked
  at (`_testrun/full/jacq_pages.png`): every page fits.
- Installed 2026-10-11: the working ROM is 4bfe13d2... (the chain gives it byte for byte), backup "(before Jacq's
  early scene 2026-10-11)" (725e63e2...); "(my placements 14)" is the same ROM. The user's own games are past
  Team Rainbow Rocket, so they cannot meet the scene there: pictures in `roms/test-paldea/Jacq before the hole
  (pictures).png`.

## WAS THE SPACE GEN 9 AND AREA ZERO TOOK REALLY FREE? — 2026-10-11 — `_testrun/space/`

The user: "wanna make sure for the gen9 and paldea area zero, have u used the actual free available space? like I
heard some FF 00 might not be acatually availabe for some reasons". Checked again from nothing, three ways, on
the working ROM of before they went in (archive, "before Gen 9 and Area Zero 2026-10-11", 7d2700d8...).

- **What they wrote** (`regions.py <main> <one ROM> <the hack's own ROM>`): 794,430 bytes in 295 stretches.
  790 KB of it on blank space, in seven areas, each blank in the main game AND in the hack's own ROM (so nothing of
  ours had been there before either):

      0968D000..096C4A00  228 KB  00   the species tables' new home (speciesx); the zero run is 0968D000..096FFF00
      097A1C21..097A1D04  227 B   00   ability rows 1200-1237, straight after the ability table (zeros to 09800000)
      09A10000..09AB810C  688 KB  00   Gen 9 pictures, cries, data, code; the zero run is 099E5508..09D00000 (3.2 MB)
      09D89012..09D89089  119 B   00   move rows 938-947, straight after the move table
      09FBC400..09FCC424   66 KB  FF   Area Zero's maps, scripts, text   } all three in the FF run from 09F82519
      09FE1000..09FE446C   13 KB  FF   Area Zero's Journal rows          } to the end of the ROM (515 KB in the
      09FF1000..09FFB608   42 KB  FF   Area Zero's sprites               } hack's own ROM)

  The move table is the telling one: 938 rows of 12 bytes end at 09D89011, the zeros go on to 09D89419, and
  938 + 86 = 1,024 rows end exactly there - the author left the table room for 1,024 moves, and rows 938-947 are
  that room.
- **The rest, 3,400 bytes, are edits inside existing tables**, each an unused or placeholder row filled or a
  pointer moved: 440 literal words and the ROM header's table pointers (speciesx / gen9: `check_gen9.py` accounts
  for every one); 38 cry rows that pointed at the placeholder cry 08747790 (two tables, 08F49714 and 08F4CF54);
  trainer rows that were the dummy "Seed" entry (09257140...); the hack's sprite table's slots 240-253, which
  held 0x0F filler (0839F0C0...), and 125-127, 212, 225, 227; map section 186's name (0900AD50); and three wild
  headers written over the wild table's own FF padding after its end row, the end row moved down (08E19128).
- **Does anything point there?** (`refs.py`, `script_refs.py`.) No word of the ROM header and no literal that code
  loads holds an address inside any of the seven (speciesx_patch.is_pointer). Of the 5,439 scripts reachable from
  the maps' events (86,933 commands, 25,677 address fields) none holds one. A few hundred words elsewhere read as
  such addresses by chance - inside pictures and tunes, at any byte offset; expected in 32 MB.
- **Does the game ever read it?** The decisive test (`watch.ps1`, the harness's new `WATCHRANGES`): the game
  without Gen 9 and Area Zero played with a read watchpoint on each area: the Pokedex (list, a page, the area
  map), the party, a summary's pages, the Trainer Card; Prelude Beach with R, SELECT, START and L; Surf with wild
  battles; the Windworks researcher, the News Tracker, battles on Route 201, three saves, resets and Continues;
  walks on eight maps in four regions. Twelve runs: **0 reads in every area.** Two control stretches watched the
  same way were read 89,788 times (the species' base stats, by code) and 3,245,898 times (the first tileset's
  animation frames, by DMA), so the watchpoints see both kinds of read.
- **What this does not prove:** a path of the game nobody walked in those runs (a late event, a rare screen) could
  still read there; nothing found suggests one. And one use of blank space is outside the game altogether: a
  bootleg cartridge without a battery keeps its save in the last part of the ROM chip, so a 32 MB hack whose end
  is in use (ours is, up to 09FFB608) cannot be patched for those. Emulators and ordinary flash carts are not
  affected.
- **What lies next to each area** (the user: "the neighbour of those FF00, are all free space right? like not
  exactly next to something important?" and "this is a huge project so I want to take more cautious").
  `neighbours.py <main> <one ROM> <the hack's own ROM>`: from the first and the last byte we changed in each area,
  the blank bytes to the nearest byte that is not 00 or FF, in the game as it was before:

      area                      blank left before ours            blank left after ours
      species tables' new home  7,028 (data ends 0968B49C)        243,621 (code at 096FFF00)
      ability rows 1200-1237    none: the table's next rows       385,788 (code at 09800000)
      Gen 9 data                174,840 (data ends 099E5507)      2,391,798 (data at 09D00000)
      move rows 938-947         none: the table's next rows       913 (data at 09D8941A)
      Area Zero maps            128 (our Quest Log's picture)     26,076 (our English texts, 09FD2A00)
      Area Zero Journal rows    16,846 (fusionfix ends 09FDCE38)  43,924 (Area Zero's sprites)
      Area Zero sprites         43,924 (the Journal rows)         18,936 (the end of the ROM)

  The two with none are meant to touch: 097A0000 + 1200 x 6 = 097A1C20 and 09D86419 + 938 x 12 = 09D89011 are
  where those tables end, and a row for species 1200 or move 938 has to be the next row or the game would not
  find it. The data before Area Zero's maps is ours: the Quest Log's chapter grid, a raw picture of a fixed
  0x4380 bytes at 09FB8000 (read by size, no end mark); its patcher's limit said 09FBF800 and now says 09FBC380,
  where Area Zero's guard begins.
  Before matters more than after: the first blank bytes after a text or a list can be its end mark. Every build
  already refuses to go on otherwise: speciesx and gen9 assert their whole range is zero (and gen9 that move rows
  938 on, their animations and the species slots are blank), paldea that each of its three blocks is 0xFF from
  0x80 bytes before it.
  A first try at the same list for every patch of the project (`neighbours_all.py`) is not usable as it is: the
  hack's own ROM has blank stretches inside text slots, and the translation's in-place text counts as "next to
  data" there by nature. It needs telling a text slot from free space before it says anything.

## MEGA STONES READ FROM THE ROM — 2026-10-11 — `tools/build_mega_stones.py`
- **Corrected 2026-10-12:** the bullet below that says nothing shows on the map is wrong, and so is every
  "unseen" in this section. See the next section.
- Reported: the guide's row "Venusaurite, Blastoisinite, Charizardite Y - Route 115" is wrong, "recheck all mega". The
  guide's Mega Stones table was typed in from community lists (the Chinese v5.0-era ones and the v5.6 Scribd guide).
  It is now `site/src/data/megastones.json`, read from the v1.8 release ROM (sha1 ade383ba...), and the guide prints
  it with `<MegaStoneList />`.
- The stones are the items the evolution table asks for (0x08F387C0; method 251 a Mega Evolution by held item, 253 a
  Primal Reversion): 48 Mega Stones, the Blue and Red Orb and Rayquaza's Final Meteor (item 648; Rayquaza also has
  a 252 row, "knows Dragon Ascent"). The Wishing Piece (702) is left out, as in forms.py.
- What was wrong: Venusaurite is on Route 119 (0/34 at 13,82), Blastoisinite on the S.S. Tidal's lower deck (25/42),
  Charizardite Y in the Scorched Slab (24/73), Charizardite X at Mt. Silver (34/56); Gengarite is in Scott's house
  (26/46), Mt. Pyre has the Medichamite (6F) and the Banettite (summit); Pinsirite is on Route 124. Right all along:
  Pidgeotite, Scizorite, Salamencite, Aerodactylite, Metagrossite, the Route 114 three, Galladite, Gardevoirite
  (Wanda's house), Houndoominite, Manectite, Tyranitarite, Cameruptite, Gyaradosite, Abomasite, Garchompite,
  Beedrillite, Slowbronite. The seven "not documented" and nineteen never listed are all found.
- **[Wrong: see the next section.] Nothing shows on the map.** 46 stones and the two orbs are finditem scripts on objects with graphics 78, whose
  first frame is blank (the table at 0x08505620; +0x1C the frame list; the same in the original hack). Ordinary item
  balls use graphics 59: 256 objects against 130 on 78. So "item ball" was the wrong word, on the TMs page too: 71
  of its 72 are on graphics 78, only TM120 at the Meteor Temple is a ball. `item_sources.py` calls these `unseen`
  and gives the tile ("group-num-x-y"); `tools/build_spot_maps.py` draws 21 x 15 metatiles around it with
  `tools/render_world.py` and frames the tile: 120 pictures (49 for stones, 71 for TMs), 0.56 MB of lossless WebP in
  `site/public/spots/`. The Itemfinder works on hidden-item bg events (kind 7); none of those is a stone or a TM.
- Five are given: Flygonite (Ice Maze 35/53: the "sealed Flygon" is itself an unseen object; a Lv 70 Flygon
  holding a Smooth Rock, then giveitem), Metagrossite (Steven, Meteor Falls 24/107, after trainer 804), Blue Orb
  (Archie, trainer 876, Marine Cave 24/103), Red Orb (Maxie, trainer 882, Terra Cave 24/105), Final Meteor (Zinnia,
  Sky Pillar top). Each orb also has an unseen pick-up in the same room (the Blue Orb's has no hide flag).
- Not true, and taken off the site: "Groudon / Kyogre holds the Red / Blue Orb" (both setwildbattle rows pass item
  0, neither has a held item in its base stats); "Professor Elm rewards you for showing him Venusaurite,
  Blastoisinite and both Charizardites" - the script exists at 0x09836AA2 (checkitem 305, 307, 304, 306) but no
  pointer to it is anywhere in the ROM, original hack included: Elm's object on Steven's Island (35/41) runs
  0x09836CA6, "I'm a little busy". Its rewards were items 695-697, of which 695 and 696 are now the News Tracker and
  the Travel Suit; 697 is still a "Feraligatrite" with the Mega Stone hold effect and no evolution row.
- Other scripts no map runs: a second Gengarite ball (0x0980D9E8), a Lopunnite one (0x08222926), a Charizardite Y
  and a Metagrossite one beside the live balls near 0x08FE3B9D, older copies of the Flygonite and orb scenes.
- The scan moved out of `build_tm_locations.py` into `tools/romdata/item_sources.py`, shared by both tools; tms.json
  came out the same but for the kind (71 x ball -> unseen, with the tile) and one place name.
- Place names: the hack has a second Route 106 map (34/68), west of Dewford Town, with a cave named Granite Cave
  (34/69) whose left and right doors lead to the Sablenite (34/73) and the Mawilite (34/71); TM75 is on 34/68.
- Site: `<Spot>` shows a picture as a thumbnail or behind "Show the spot", opening in the image viewer (which takes
  the size from `data-w`/`data-h` when there is no thumbnail); a Mega form's Pokédex page says where its stone is;
  search has an entry a stone. 21 browser checks; the TM, Pokédex and general suites still pass.
- Not rechecked: the Z-Crystal and Plate rows of the same guide are still from community lists.
- Published 2026-10-11: public repo commit 2cd6ecc, built in the public checkout (the dev site has unreleased edits
  of other work in it, so only this change's files were copied across); `infinityfree/` rebuilt from the same.

## THE BUILT ROM IN THE DEV REPO — 2026-10-12

The user: "push to dev repo, include the rom itself so that I can work easily no need to patch left and right".

- `rom/Pokemon Hyper Emerald v5.7 - Full English Modern.gba` (4bfe13d2..., the working ROM), `rom/placements.txt`
  and `rom/ground.txt` (what its Area Zero was built with), `rom/README.md`. `.gitignore` lets that one `.gba` in.
- The dev repo (`dev`, Nn-Exe/hyper-emerald-qol-dev) is private; the public one (`origin`) must never get the
  game. Three locks: `mirror_public.py` (which copies every file git knows across for a release) leaves out `rom/`
  and anything ending in .gba / .sav / .ss0-9 / .bak; `.git/hooks/pre-push` refuses a push to any remote but the
  dev repo if a commit being sent adds or changes such a file (tried by hand: `main` to the public repo refused,
  as an update and as a new branch; a release branch to the public repo and `main` to `dev` let through);
  and `main` tracks `dev/main` instead of `origin/main`, so an editor's "sync" goes to the private repo. The hook
  is not in the repo: a fresh clone has none.
- Pushed 2026-10-12 as seven commits on `main` (dbc0a30..d2e0aaa): the patches since v1.8, speciesx + gen9, paldea,
  the documents, the v1.8 release files, the ROM, the guide site and tools. Everything the working copy held went
  up, the other sessions' site work with it. Checked first: no save, no token, no account email among the 1,702
  files; on GitHub afterwards: `rom/` is in the dev repo and the public repo has none.
- Gen 9 and Area Zero are now files git knows, so the next public mirror would carry their source across: that is
  the release question still to be asked.

## THE SUMMIT: A LOST ATTEMPT ENDED THE QUEST — 2026-10-12 — `patches/summitfix/`
- Reported (a player, Pizza Boy, Quest Log "The summit: Active" with Kitty's fish Done): "I battled the girl on top
  of the highland, I didn't understand what to do so I just defeated her every time until I was brought back;
  now my nameless stone is gone."
- The scripts (all the hack's own; listed with a small command lister over tools/romdata/scripts.py's tables):
  * guard, Hisui 37/106 objects 1-2, 0x098B201D: `checkitem 745`, flag 0x4319, not 0x4323 -> two yes/no boxes
    ("Best not to approach the summit?" No, "Do you really want to head for the summit?" Yes) -> warp 35/10.
  * Moonbow Dome 35/10 object 0, 0x098C5E66: setflag 0x273, 0x276; trainer 1304 twice (outcome > 1 -> 0x098C5F06,
    the way down); the stone glows; 0x098C60FA: setflag 0x278, trainer 1340 - outcome > 1 (she won) -> 0x098C5F66
    (the Rainbow Ring, trainer 1341, which must be won, then `setwildbattle 1025, 70`, setflag 0x4323,
    removeitem 745, warp out); a win -> VAR 0x4002 += 1, at 3 -> 0x098C6143 "I'm getting a bit bored" -> the
    way down; else her "Hourai Elixir" line and 0x098C60FA again.
  * the way down, 0x098C5F06: the Galaxy Team message, clearflag 0x273/0x276/0x278, **removeitem 745**
    (0x098C5F19), heal, warp 37/106.
  * Kitty, Steven's Island 35/8, 0x098B1F85: `checkitem 744` -> eats it, removeitem 744, additem 745. No flag.
    Items 744 and 745 are Key Items; 744's only source is the Prelude Beach ball (hide flag 0x4322).
  Nine older copies of the dome script lie at 0x098B2xxx-0x098B8xxx (their removeitem / setflag 0x4323 show up
  in a byte search); no map entry point reaches them.
- Checked in the emulator on the current game: a loss to trainer 1340 (the party at 1 HP with no PP) gives
  outcome 2, no black-out, and the script goes on at 0x098C5F77 into the battle with 1341. So the way through is:
  win twice, lose once, win once.
- The patch: 0x098C5F19 -> five nops; Kitty's `checkitem 744` (0x098B1F87) -> `goto` a script in free space
  (0x08FF8B40: her own fish check first; then 0x4323 set, 0x4322 clear or the stone present -> her greeting
  0x098B1F97; else a line and `additem 745`); the "bored" loadword (0x098C6145) -> a new text. Free space
  0x08FF8B40..0x08FF8CEF, in itemdesc's pointer-free window (it ends at 0x08FF8B06; the window runs to 0x08FF9400).
- GOTCHA (test): flags from 0x4000 up are not in the vanilla flag array - writing SaveBlock1+0x1270+(n>>3) for
  0x4322 set nothing (and scribbled on the save copy). The test sets them with setflag / clearflag in a script
  and reads them back with a checkflag script into VAR 0x8004 / 0x8005.
- Tested (`test_summitfix.lua`, seven cases, the unpatched game as control): the way down and the "bored" exit
  keep the stone (old: gone) and land on 37/106; Kitty gives a stone when the fish is taken and there is neither
  fish nor stone and the summit is not done (old: nothing), and not when the stone is there, the summit is done or
  the fish was never taken; her trade for a Dried Fish is as before. `tools/text_overflow.py`: the same report
  before and after.
- In the chain it is after `sprframe`, before `zhtext` (43 patches; the main game 7d2700d8... -> 29d20002...). It
  changes 440 bytes, and the same 440 whether it runs there or on top of the finished game (compared byte for
  byte), which is how `rom/` was updated on the Mac, where `gen9` cannot run (no Crest ROM): 4bfe13d2... ->
  36c0f986.... The other PC's `rebuild_chain.py` needs `summitfix` added after `sprframe` and must then give
  36c0f986... for the full game.
- **Done on the Windows PC, 2026-10-12** (after `git pull`). The patcher run there on its working ROM (4bfe13d2...)
  gave 36c0f986...; with `summitfix` after `sprframe` in the three copies of `rebuild_chain.py` the whole chain
  from the v1.4 archive gave 36c0f986... too (the main game alone 29d20002..., the Gen 9 base 0ce62833...).
  Its free space checked as the user asks: 08FF8B40..08FF8CEF was 0xFF there and in the hack's own ROM; 58 blank
  bytes before it (itemdesc ends 08FF8B05), 18,609 after; no word of the ROM at any byte offset reads as an
  address inside it; the game before the fix played with a read watchpoint on it (the menus, Prelude Beach with
  R / SELECT / START / L, walks in Mossdeep and on Coronet Highlands): 0 reads. Four of the test's cases run there
  (down: the stone stays; kitty_lost: she gives one; kitty_has and kitty_done: she does not). Installed: the
  working ROM, the Gen 9 base, and "(my placements 15)" from `rebuild.py`, all 36c0f986...; backups "(before the
  summit fix 2026-10-12)" and "Gen 9 test (the base of 2026-10-11, before the summit fix)". The user's save
  continued on it (`test_steps_continue.lua`).
- Not done: the Journal's step text still does not say that she has to win once. It is in the Journal / Quest
  Log data, early in the chain, so changing it means a full rebuild with `gen9`.
- Installed on the Mac 2026-10-12: the working ROM there (the 2026-10-07 build, 6ef5c8d9...) became the full
  game with this fix (36c0f986...); backup "(before the full game + summit fix 2026-10-12)".


## THE TIME RIFT — 2026-10-12 — `patches/paldea/`
- The user wanted something more unique than the pale time crystals in the two craters. From three mock-ups made
  on the Mac they chose B, the wide rift ("wide rift is perfect"), and it was tried there on top of the finished
  game (`rom/unreleased/time-rift/`: the Mac cannot build Area Zero). Then, of the game on this PC: "what doesn't
  it have new timerift replaced crystal in paldea?" - it had never been built in. Now it is.
- What it is: a tear in the air, 32x32, the other time seen through it - cold blue in the past crater (35/90),
  warm amber in the future one (35/91) - shimmering through four pictures. `sprites/rift.py` draws it (the trial
  kit's `rift_art.py`: the files it writes are the kit's, byte for byte). `rift_cold.4bpp` and `rift_warm.4bpp`
  are the same 0x800 bytes; the two `.gbapal` differ.
- `mons.py`: a fourth kind, `KINDS[0x800]` = 32x32, four frames, an entry copied from Suicune's like the 32x32
  Pokemon. Identical pictures are stored once (both rifts: 0x09FFB450, 2,048 bytes). The frame table has the nine
  entries the standard animations count (pictures 0 1 2 3 0 1 2 3 0), so no animation can ask for a picture that
  is not there (*A sprite's missing picture copied over video memory*). The animation table (0x09FFBD34) is 24
  pointers to one loop (0x09FFBD20): ANIMCMD_FRAME(n, 9) for n = 0..3, then ANIMCMD_JUMP(0) (0xFFFE). The entry
  keeps the hack's "inanimate" bit (byte 12, 0x40; the byte is 0x52): the thing never turns.
- `paldea_patch.py`: `SPRITES["rift_past"]` = slot 254 (0x0839F2B8), palette tag 0x1136; `["rift_future"]` = slot
  255 (0x0839F2DC), tag 0x1137; each crater's two time objects take their era's slot. The hack's sprite table has
  no spare entry left (240-255 are all Area Zero's). Entry 126 (the pale shard, tag 0x1111) is still written: a
  save holds its own copy of a map's objects until the stamp makes the game read them again. `STAMP_SALT` 13 ->
  14 for that: a save made beside a crystal shows the rift on Continue.
- GOTCHA: at first the rift did not shimmer - thirty pictures, one frame. The rifts were among `mon_slots`, the
  slots whose objects get "face down" as their movement type, and `FaceDirection` (the sprite callback 0x0808FD8D)
  sets `sprite->animPaused`. A thing with an animation of its own needs movement type 0 (MovementType_None,
  callback 0x0808F3E1): the `rift_*` keys are left out of `mon_slots`, like the recorder.
- Words: story.py's six lines that said crystal (TIME_CRYSTAL_FIRST "A tear hangs in the air, shimmering. ...";
  TO_FUTURE / TO_PAST "Through the rift, ... Step through?"; Arven's two "The rifts in the air will take you.";
  Turo's log "If the rifts down here open onto time ...") and the Journal's step ("Step through a time rift to
  the future, ..."). The names in the code (TIME_CRYSTAL_*, time1, time2, F_RIPPLE_SEEN) are as they were.
- placements.txt: the two are "time rift 1" and "time rift 2" (`places.THINGS`, kind "rift", 32x32 for the editor
  and check.py). `places.ALIASES` reads "time crystal 1 / 2" as the same things, without a note, so the user's
  file is not written afresh (compared after `rebuild.py`: untouched); the editor writes the new names the next
  time it saves. The editor's ?selftest (`_testrun/rift/editor_selftest.py`: the editor on a copy of the folder,
  Edge without a window) drags "time rift 1" and ends "SELFTEST DONE"; the map guide draws both rifts.
- A rift moved to water with the editor (tried on copies of the user's folder): beside the pond check.py refuses
  it like a Pokemon ("too close to water": its reflection would lie on the grass); on the pond (33,17) it is let
  through, and in the game it stands on the water with a pale blue mirror image under it in both times (the
  reflection is drawn from the rift's own tiles in palette slot 1), 819 picture copies, none bad
  (`_testrun/rift/steps_pond.lua`, `rift_on_pond.png`). The positions built in and the user's have no water near.
- Space, checked as the user asks (`_testrun/rift/space.py`, `_testrun/paldea/rift23b.ps1`):
  * The sprites' block grows from 0x09FFB608 to 0x09FFBF5C: 44,892 of the 45,056 bytes kept for it, 164 left
    (another sprite means a longer block; the 16,548 bytes after it, to the end of the ROM, are blank). The 2,388
    new bytes were 0xFF in the game before and in the hack's own ROM, as is everything from there to the end of
    the ROM. Of the ROM's words at any byte offset eight read as an address in 0x09FFB608..0x09FFC000 (one on a
    4-byte boundary, inside graphics at 0x089AE364); none is a pointer (speciesx's `is_pointer`).
  * Sprite entries 254 and 255 (0x0839F2B8..0x0839F2FF) were the table's 0x0F filler in both ROMs, and none of the
    game's 5,818 map objects is drawn with slot 254 or 255.
  * Read watchpoints. The game before the rift (36c0f986...), on 0x09FFB608 to the end of the ROM - the crater
    with Surf and Waterfall, both time crystals through and back, the menus: 0 reads (the sprites' block before
    it, as the control: 12,938, 3,302 and 1,048). The game with the rift, on 0x09FFBF5C to the end: 0 reads; on
    the rift's own 2,388 bytes: 35,678 and 100,320.
  * All else that differs between the two ROMs (50,463 bytes in 51 stretches) lies in Area Zero's own areas (its
    data at 0x09FBF84A..0x09FCC42F and its Journal rows, moved along by the new words; the sprites' block) or is
    a pointer of ours into them.
- Tested (`test_rift.lua`; `_testrun/paldea/rift23.ps1` and `rift23b.ps1`; hidden, with the picture-copy guard's
  count and the palette watchdog): look - both rifts in both times are 32x32 and show four different pictures
  within a few frames, through and back lands on the same tile, 2,039 picture copies, none bad; busy - the rift
  met after a walk past the crater's other kinds of thing, after the story (7,757 copies; no sprite in another's
  colours); a save made below the dais's crystal on the build before, continued: the rift stands there and takes
  you through; Jacq's three scenes and a save from before them; the whole Area Zero list (final16, journal17: all
  ok). On the user's own placements: their save continued, their crater with Surf and Waterfall (12,003 copies,
  none bad), both rifts, and sprframe's own test (22 bad copies asked for on Prelude Beach, none made). Two lines
  of the first batch read BAD and were the tests' own mistakes, run again right in the second: an expectation
  that the far rift is on the map from the dais (it is too far to be made), and the Jacq save test given the
  build that already has his early scene as its "before".
- Installed 2026-10-12: the chain from the v1.4 archive gives 52db9719... (the main game alone 29d20002... and the
  Gen 9 base 0ce62833..., both as before); the working ROM, `rom/` and "(my placements 16)" from `rebuild.py` are
  that file; backup "(before the time rift 2026-10-12)". In no release.

## THE MEGA STONES AND TMS CAN BE SEEN; OBJECTS NOBODY CAN REACH; Z-CRYSTALS AND PLATES — 2026-10-12
- **The mistake.** The section above concluded that Mega Stones and TMs sit on invisible objects, because graphics
  id 78 (0x4E) has an empty first frame in the object graphics table at 0x08505620. It went live on 2026-10-11. The
  doubt came a day later, while reading the Z-Crystal scripts: Nanu, Prof. Kukui and the Sinnoh Gym Leaders use id
  78 too, and they are plainly not invisible.
- **How the hack draws its own objects.** GetObjectEventGraphicsInfo (0x0808E69C) is vanilla, but its callers are
  hooked (literals at 0x0808D9F0, 0x0808DB6C, 0x0808DD04, 0x0808E204, 0x08096A98 -> 0x094A2BA0..0x094A2BF8). The
  shared tail at 0x094A2BCE: `cmp r0, #0x4E; bne vanilla; r0 = 0x0839CF00 + 36 * r1`, with r1 the object's byte
  0x1A, which is the template's fourth byte (vanilla leaves it unused). So graphics 0x4E means "extended sprite n":
  a table of 36-byte graphics infos. 0x18 is the Mega Stone (16x32, a round stone of many colours, palette tag
  0x1103), 0x3C the TM (a ball, tag 0x1106), 0x30 the sealed Flygon, 0x3F Nanu, 0xA2 Roark. Object palettes:
  {pointer, tag} at 0x0850BBC8, 35 of them. Of the objects whose script is a finditem, 255 use graphics 59 (the
  Poké Ball), 77 use 0x4E/0x3C, 48 use 0x4E/0x18; **none has an empty sprite**.
- `item_sources.sprite()` and `frame()` follow that rule; `blank()` now tests the frame the game would draw.
  `tools/build_spot_maps.py` draws the object's own sprite on its tile.
- **Objects nobody can reach.** With the sprites right, the pictures showed pick-ups inside trees, water and lava.
  The hack parks objects where no tile around them can be stood on (map grid bits 10-11, collision), scripts
  intact. `walled_in()` drops a finditem whose four neighbours are all solid (a neighbour with metatile behaviour
  0x80, a counter, counts as open if the tile behind it is; past the edge of a map without connections there is
  nothing) and a giveitem whose giver is sealed that way and stands on a solid tile itself. Dropped: fifteen spare
  Plates in the filler of Solaceon Ruins (35/14), a Grassium Z on Route 116 (63,16), a Grassium Z in the Lurantis
  room, the Blue Orb in Marine Cave (6,23) and the Red Orb in Terra Cave (15,24) (so each orb comes from Archie or
  Maxie only), a Max Revive at Spear Pillar, a second TM117 in Hearthome City (42,8), and three gifts that were on
  the TMs page: Lucas (TM103) and X (TM119) on the west cliff of Ever Grande City (5,67 and 5,64), Serena (TM113)
  in the top wall of Rustboro's Flat 2 3F (13,0). No script of those maps moves any of them.
- **Z-Crystals.** The 18 type crystals: a trigger in each of 18 secret-base rooms (map group 25) runs
  `setwildbattle <Totem>, 80, <crystal>`. A room is reached from the routes' secret-base spots (bg events of kind
  8); the spot's id picks the room through the table at 0x0858CFE8 (refs 0x080E8FCC, 0x080E91E8): four bytes a
  group of ten ids, the first the room's map number, in the order 0, 6, 12, 18, 1, 7, ... (not id // 10, which
  put Wishiwashi behind the wrong trees until Gladion's own tree on Route 111 disagreed). 75 spots, 57 of them into
  Totem rooms. The script: nothing unless flag 0x419D (set by Anabel on Steven's Island, 0x09833C35, on your
  report from the first Ultra Wormhole journey; it also brings Gladion back to Route 111); Wishiwashi's room also
  wants 0x41A2 clear and sets it on a win, the other seventeen want it set. callnative 0x094A224C: for each of
  the four moves at 0x094A2318 (Destiny Bond, Perish Song, Pain Split, Leech Seed), 0x094A2204 walks the party's
  move slots; a hit answers 77 and the script says "Can't use some moves!". Otherwise it adds 623 to var 0x8000
  (the Totem's index: so the crystal's item id) and sets the Totem up. A win (special 0xB7 == 1) does finditem
  with that var and sets the Totem's flag. Selene (34/42, 0x098B72D6) clears the flag of each beaten Totem whose
  crystal is not in the Bag; for Wishiwashi she adds the Waterium Z herself.
- The community's route hints named one spot of each room and all eighteen agree with the table; "all 18 are
  needed for Team Rainbow Rocket's castle" was not checked and is off the page.
- **The other Z-Crystals and the Plates**: `tools/build_guide_items.py`, sources from `item_sources.scan`, a note
  a gift. The four Tapu trials give a crystal after the Lv 50 battle however it ends; Prof. Oak (Steven's Island,
  Eterna City) or a Sandgem researcher splits the Special Gem into Pikanium Z and Eevium Z. The fifteen Plate balls
  and the Icicle Plate agree with the Lost Artifacts guide's table, which was written from the scripts.
- Site: `<TotemList />`, `<ItemPlaceList list="plates|crystals" />`; 196 pictures, 0.98 MB; 29 browser checks.
- Still from community lists on that guide page: the key items table (the Quest Log's list disagrees with it on
  the Mega Bracelet and the Z-Power Ring), shops and tutors, the HM paragraph.

## THE VERSION NUMBER: 1.9 — 2026-10-12 — `patches/qolversion/`
- Asked: "change number to 1.9 ver". `QOL = "1.9"` in `qolversion_patch.py`: the Option screen's title reads
  "Ultra Emerald v5.7 +QoL1.9 (Standard)" (one string a difficulty, in the block at 0x08FF24C0).
- The patch sits mid-chain, so the whole chain was rebuilt (`_testrun/rel18/rebuild_chain.py`). First unchanged, as
  a control: 52db9719..., the installed game byte for byte, so the repository as it stood (the time rift's
  uncommitted files included) was the game. Then with 1.9: d7e673b3... (the main chain alone 64db7201..., the Gen 9
  base 935553a0...). It differs from the game before in four bytes, 0x08FF24E0, 0x08FF250D, 0x08FF253B and
  0x08FF2569: 0xA9 "8" -> 0xAA "9". Both digits are 6 px wide; no new space is taken.
- Looked at in mGBA (hidden, `_testrun/v19/run_option.ps1`, the expgain test's save): the title fits its bar, and
  the test's three battles give EXP, none, EXP as before.
- Installed: the Gen 9 base in `roms/test-gen9`, "(my placements 17)" from `rebuild.py` (the same file as the
  chain's result), the working ROM and `rom/`. Backups in `gba-trans/hyper-emerald/archive`: "(before v1.9 2026-10-12)" and the
  Gen 9 base "(the base of 2026-10-12, on QoL 1.8)".
- The number only. No release was made: `release/` still holds v1.8's patch, the site's `PATCH_VERSION` is 1.8,
  HANDOFF's "last published release" is v1.8. A v1.9 release needs the user's word on Gen 9 and Area Zero first.

## THE GOLD HEALTHBOX KEPT ITS PALETTE — 2026-10-13 — `patches/goldbox/`
- The report: "the shiny box sometimes still disappear" (after shinyfade, 2026-10-09). Looked for by playing wild
  battles on Route 102 with every battler made shiny the way shinybox reads it (gBattleMons[n].otId =
  personality), each battler given the same move every turn (ids 1, 2, 3 ...), and on every frame each visible
  healthbox looked at: the slot its sprite is on and colour 2 of that slot in palette RAM
  (`_testrun/shinybox2/sweep.lua`, in the patch folder as `test_goldbox.lua`).
- **Wild battles are double ones at random**: the hack's code at 0x09D60CA0 (called from 0x09D60C94, with the
  second wild Pokemon at 0x020247A8) sets bit 0 of gBattleTypeFlags (0x02022FEC) before the battle starts. (The
  test's way of running - DOWN, RIGHT, A at the action menu - did not end a double one; not looked into. It
  leaves one by letting the wild Pokemon faint.)
- **Sprite palette slots in a battle** (sSpritePaletteTags 0x03000CF0; gReservedSpritePaletteCount 0x0300301C = 4):
  0-3 the four battlers' own (untagged; 2 and 3 unused in a single battle), 4 healthboxes (0xD6FF), 5 HP bars
  (0xD704), 6 and 7 the hack's (tags 0x1234, 0x2345: sprites with callbacks 0x09D608C5 / 0x09D605E1), 8 our type
  badges (0x5E62), then one ball palette per battler that stays loaded (0xF12D, 0xF10D, 0xF109, 0xF129 in the
  runs here: two in a single battle, four in a double one). Free for everything else: 11-15 in a single battle,
  13-15 in a double one. Our quick-ball widget takes two more at the action menu of a wild single battle (0x5E5E,
  0x5E5F: freed when the menu closes), lmoveinfo one at the move menu (0x5EB0).
- **Bug 1: the gold slot was never claimed.** shinybox took "the highest slot from 15 down whose tag is 0xFFFF"
  on every frame and painted there, tag left free. LoadSpritePalette gives out the lowest free slot, so the two
  meet when an animation needs all that is left: in a double battle the third palette of a move animation went
  into slot 15, over the gold, and shiny_boxes then found no free slot and "left every box as it is" - on slot
  15, in the animation's colours - until the animation freed it. Moves 1-118 in a double battle: 51 moves, 57,052
  of 666,854 healthbox-frames drawn in colours that were not the box's (7, 8, 9 the punches, 40 Poison Sting, 47
  Sing, 71 Absorb, 72 Mega Drain, 75 Razor Leaf, 85 Thunderbolt, 86 Thunder Wave ...; and once Leech Seed is on
  the field its drain, three palettes, every turn). In a single battle: none.
- **Bug 2: status icon colours.** The game's UpdateStatusIconInHealthbox writes the icon's colour to index 12 +
  battler of the palette slot the box's sprite is on (both buffers; four boxes, one palette, four colours). The
  stock palette is stored with placeholders there (0x7C00, 0x03E0, 0x001F, 0x7E4D), and paint / paint2 put the
  whole ROM palette back every frame: PAR (0x0EF7) showed green on battler 1, SLP (0x4694) pure blue on battler
  0. (PSN / TOX 0x6198, BRN 0x29DC.)
- **goldbox.s**, 1,164 bytes at 0x08FEE400 (entries: +0 gold_pass, +2 LoadSpritePalette, +4 AllocSpritePalette,
  +6 ti_load):
  * `gold_pass` replaces shiny_boxes (typeicons' pool word 0x08FDAB5C; shinybox's shiny_boxes / paint and
    shinyfade's paint2 are no longer called). While a shiny battler's box exists it claims the highest free slot
    from 15 down to 10 with tag 0x5E63, copies the stock palette there as it is (both buffers) and gives the slot
    back when no shiny battler has a box. Every frame: unfaded colours 0-11 from the stock palette with colour 2
    = 0x1F5F; faded = unfaded while the stock palette's faded and unfaded agree, else left to the fade
    (shinyfade's rule). For each box body the status colour (12 + battler) is copied from the slot the box is on
    to both palettes, so it is right whichever the box is on next. A battler counts as shiny only if its species
    is not 0 (before, the blank gBattleMons of the first frames read as shiny and the boxes were painted and
    unpainted).
  * A box the game has moved to another slot (the level-up flash, AnimTask_LoadHealthboxPalsForLevelUp 0x08170920,
    copies the box palette to a new slot and puts the box on it): a shiny battler's goes straight back to the
    gold when that slot is 10 or more (the flash then does not show on it, as before); below 10 (it gets slot 8
    when the badges have given it up) it stays, flashes, and the game puts it back itself. A plain box on a slot
    somebody owns is left alone - before, shinybox pulled every box back to slot 4 each frame, so no level-up
    flash showed at all.
  * `load_pal` / `alloc_pal`: the game's LoadSpritePalette (0x08008744) and AllocSpritePalette (0x080087D4), whole,
    behind 8-byte trampolines at their starts. Same code, but when IndexOfSpritePaletteTag(0xFFFF) finds nothing
    they call `make_room`: the type badges' slot first (the badge sprites, callback 0x08FDA9CB, are made
    invisible), then the gold's (its boxes go to the stock palette, status colours carried), each also set right
    in this frame's OAM buffer; 0xFF only if neither is loaded. The original hack had four free slots in a double
    battle; typeicons had taken one for good and the gold squatted on another. Now both are given back on demand.
  * `ti_load` is what typeicons calls for its palette (its pool word 0x08FDAB74): it loads only if a slot is
    free - two while a move animation has palettes loaded (tags 0x2710-0x2B0F), so that it does not take back,
    mid-animation, the slot the animation asks for next - puts every badge sprite on the slot it got, and
    otherwise hides the badges and returns 0xFF.
- GOTCHAs:
  * gMain.oamBuffer is gMain + 0x38 = 0x030022F8 (LoadOam 0x08007188 says so). The first build had + 0x3C; the
    test compared the buffer with OAM itself and found them never equal. With the right address: equal on about
    three frames in four.
  * A move animation's script runs from the battler controllers, in callback1 - BEFORE BattleMainCB2 builds the
    OAM buffer - so a palette taken there is seen by the same frame's gold_pass and typeicons. A task run by
    RunTasks comes after the buffer is built: that is what the OAM fix in make_room is for.
  * keystone pads `.align 2` in Thumb code with 00 BF, the Thumb-2 nop. The patcher puts a `mov r8, r8` before
    each pool when it is needed (PADA / PADB / PADC), so the assembler has nothing to pad.
  * The first place chosen for the code, 0x08FEE000, has an aligned word reading 0x08FEE20B in the chain's ROM
    before zhtext - two Chinese characters of a text zhtext replaces (0x08224C28). On top of the finished game
    the check passed; in the chain it did not. 0x08FEE400..0x08FEEA00 is clear in both.
  * "wrong for 1 frame" in the first runs was the test: on the frame gold_pass moves a box, palette RAM still has
    the slot's old colours until the vertical blank. The test now also checks what was DRAWN: OAM against
    palette RAM, by the tile numbers of the boxes and the badges.
- Space, checked as the user asks (`_testrun/shinybox2/space.py`, `watch.ps1`): 0x08FEE400..0x08FEE88B was 0xFF in
  the game before and in the hack's own ROM; 4,152 blank bytes before it (the Quest Log ends at 0x08FED3C8),
  3,444 after (objpal's allocator at 0x08FEF600). Words of the ROM that read as an address in
  0x08FEE400..0x08FEEA00: 16 at odd byte offsets, none on a 4-byte boundary, none a pointer; of 87,801 script
  commands walked none holds an address there. Read watchpoints on it while the game of before was played -
  moves 1-40 in a double and in a single battle, the Bag, ball throws, the level-up flash, the menus, the user's
  crater with Surf and Waterfall, the menus on Prelude Beach: 0 reads in all eight (the controls beside it:
  shinybox's pool 32,626 to 1,725,801 reads, the tileset animation frames 6,963 to 1,988,863). The other bytes
  that change: 8 at each of the two functions' starts (the hack's own ROM has the vanilla code there) and the
  two words of typeicons' pool.
- Tested on the build (`_testrun/shinybox2/final.ps1`, `everything.ps1`; hidden):
  * moves 1-118, double, every battler shiny: 654,131 gold box-frames, 976 plain (Sing, four palettes), none in
    wrong colours (0 of 655,107 drawn boxes; 0 of 299,870 drawn badges); the badges hidden during 51 moves; 0 of
    1,142 palette requests went without a slot. Single: 175,162 gold, nothing hidden, nothing plain.
  * moves 150-250, double: plain during Tri Attack, Belly Drum, Heal Bell and DynamicPunch (four palettes), the
    badges hidden during 11 moves, none drawn wrong. Belly Drum and Heal Bell ask for a FIFTH palette and get
    none (8 requests): that is the hack's own limit - four free slots in a double battle - not ours. (The test's
    driver stalls from Torment, move 259, on: a move it may not repeat. Not looked at further.)
  * status icons, single and double: PAR 0x0EF7, TOX 0x6198, BRN 0x29DC, SLP 0x4694 on gold boxes, the same as on
    plain ones (`test_goldbox_status.lua`; the game of before: 0x03E0 / 0x001F / 0x7C00).
  * a quick ball throw and catch (single), into the Bag and back (single, double), the level-up flash (double,
    shiny and not), shinyfade's own fade test: PASS / nothing wrong drawn.
  * the one ROM's regression list (`_testrun/full/tests_goldbox.ps1`: Area Zero's story start to end, the old
    saves, the user's save and crater, sprframe, roamfix, the walks, the menus, Gen 9's battle effects): the same
    results as on 2026-10-11, but for one damage roll - Ivy Cudgel (Fire) 224 where it was 252, the random factor
    0.89 for 1.00; with five other seeds the two builds deal the same.
- Seen while testing, in the game of before too, not looked into: with every battler using Fire Punch after six
  other moves in a double battle, the flames around the target are drawn as cream blocks for some frames
  (`_testrun/shinybox2/s7_cream.png`); and during a level-up flash the foe's type badges are partly behind its
  box.
- In the chain after `summitfix`, before `zhtext` (44 patches; the three copies of `rebuild_chain.py` have it).
  The same bytes in the chain and on top of the finished game (compared: 8c155ddc... both ways; the main game
  alone ffce047a..., the Gen 9 base f43e0a2b...). Installed 2026-10-13: the working ROM, `rom/`, the Gen 9 base in
  `roms/test-gen9` and "(my placements 18)" from `rebuild.py`; backups "(before goldbox 2026-10-13)" and "Gen 9
  test (the base of 2026-10-12, before goldbox)". In no release.

## THE HACK'S OWN BALLS WERE NEVER LET GO OF — 2026-10-13 — `patches/ballfree/`
- The user, after goldbox: "more than that especially when heal in battle". They were right and goldbox's test was
  wrong: it wrote every battler's hit points to the maximum on every frame, so a move that heals failed ("HP is
  full") and its animation never played. (And the game copies hit points and the held item back from the party's
  data at the action menu: a test cannot hold them in gBattleMons.) With the party as the save has it (the lead at
  160/346) heal and drain animations play, and most load FOUR palettes in a double battle.
- **The bug** (the original hack's). It has 27 kinds of ball: sheets 0x09F097E4, palettes 0x09F096E4 (tags
  0xD6D8-0xD6E3 for the game's twelve, 0xF100-0xF10E for ids 12-26), the opening sparkle's sheets 0x09F092E4 and
  palettes 0x09F091E4 (0xD6EC-0xD6F7, 0xF120-0xF12E); 32 entries each, the last five a copy of the first.
  LoadBallGfx (0x08076A78) and LoadBallParticleGfx (0x08171D60) load sheet and palette when the sheet's tag is not
  loaded. The two clean-ups still count to twelve: HandleBallAnimEnd (0x08075FD4) calls FreeBallGfx(0..11) when no
  battler has a ball in the air (`cmp r4, #11` at 0x080760DA), DestroyBallOpenAnimationParticle (0x08172944) frees
  sparkle sheets and palettes 0..11 when the last sparkle is gone (`cmp r6, #11` at 0x081729C6). So a Pokemon sent
  out of a ball from id 12 on left 12 + 8 tiles and TWO palette slots loaded until the battle ended (the save's
  Swampert: ball 25, tags 0xF10D / 0xF12D; Necrozma and a thrown Quick Ball: ball 21, 0xF109 / 0xF129). Those were
  the four tags goldbox's notes call "one ball palette per battler".
- **The fix**: both counts to 26 (0x0B -> 0x1A, two bytes). FreeBallGfx does nothing for a ball that is not
  loaded. The test before the second loop ("is a sparkle task still running?", 12 entries of the task table
  0x09F08E44) needs no change: every ball from 12 on uses entry 0's task (0x08171E51).
- After it a battle's tag table reads D6FF D704 1234 2345 5E62 and the gold's 5E63 at 15: slots 9-14 free in a
  double battle (13-15 before).
- How wild battles become double ones (needed for the tests): 0x09D60C48 - if the grass you stand in has behaviour
  0x0D (0x09D60C10) and 0x09D4B2B0(30) says so (RandomRange(100) < 30, 0x09D380E4) it makes a second wild Pokemon
  and sets bit 0 of gBattleTypeFlags. In one run of the game that number hardly changes (sixty double battles
  running, or none): the test sets what the function draws (a breakpoint at 0x09D4B2BA writes r0: 0 double, 99
  single).
- Tested (`_testrun/shinybox2/final2.ps1`, `final3.ps1`; `patches/goldbox/test_goldbox.lua` is the watcher; hidden):
  * 39 heal, drain and heavy moves, double, every battler shiny. The game of 12 October: 61,888 of 233,608
    healthbox-frames drawn in colours that were not the box's, during 21 of the moves. goldbox alone (build 18):
    none drawn wrong, but the gold plain on 21,688 frames during 11 moves and the badges hidden during 20. With
    ballfree: gold on all 149,195, the badges never hidden, no palette request without a slot. Single: the same
    (the game of before: Belly Drum and Heal Bell, 680 frames).
  * every move, double: 1-259 gold on all 1,163,140 frames (the game of before, the same moves: 76,036 of
    1,503,380 drawn wrong, 34 moves); 261-944 plain on 566 frames, all Sparkle Aria (627: eight palettes). Single,
    all moves: plain during nine - Sparkle Aria, the Max Moves 868-873 and the three moves after them in that
    battle (874-876); Max Drum Solo and Max Hydrosnipe ask for more palettes than there are at all.
  * a Hyper Potion from the Bag (single, double), a Pokemon taken back and another sent out after the balls were
    freed (the thrown ball the same picture as on the game of before, frame by frame), ball throws, the level-up
    flash (it shows on a shiny's box now: the copy lands on slot 9), the Bag, shinyfade's test: nothing wrong.
  * the one ROM's regression list (`_testrun/full/tests_ballfree.ps1`): the same as goldbox's, line for line.
  * Not tested: Leftovers and the berries (the test could not make a battler hold one).
- **OPEN, not fixed - the hack leaks sprite tiles.** Sheets of 32 tiles tagged 0x2345 and 0x2347 (the hack's:
  {0x09D77F74, 0x400, 0x2345} at 0x09D77CFC, {0x09D77DFC, 0x400, 0x2347} at 0x09D77D04; its sprite's callback
  0x09D605E1) are loaded again and again during a battle and never freed: eleven to thirteen of them after ten
  turns of a double battle with the save's party, 6 to 18 of the 1,024 sprite tiles left. Then a move's sheet
  does not fit and its sprites show whatever is at tile 0 - Celebrate's confetti (Flatter's, 12 tiles) drew
  pieces of the healthbox in the test's ten-move battle on 2 of 4 runs with ballfree and 0 of 8 without (the old
  game had 18 tiles left at that point, enough by a few), and the "cream blocks" for Fire Punch's flames seen on
  both builds are the same thing. What loads those sheets was not looked for (once a turn or so: the move menu?).
- OPEN: Flatter (260) stops the game at "used Flatter!" in a double battle, on the game of before too (not in a
  single one). Beat Up (251) stalled the single-battle run of the test; not looked at.
- In the chain after `goldbox`, before `zhtext` (45 patches; the three copies of `rebuild_chain.py`). The same
  two bytes in the chain and on top (compared: adcc2707... both ways; the main game alone and the Gen 9 base
  27b6fa53...). Installed 2026-10-13: the working ROM, `rom/`, `roms/test-gen9` and "(my placements 19)"; backups
  "(before ballfree 2026-10-13)" and "Gen 9 test (the base of 2026-10-13, before ballfree)". In no release.

## THE MOVE MENU ATE THE SPRITE TILES — 2026-10-13 — `patches/sheetonce/`
- Found while testing goldbox and ballfree: in a long battle a move's sprites came out as blocks (Fire Punch's
  flames, Celebrate's confetti). The user: "yeah" (fix it).
- **The bug** (the original hack's; its own untouched ROM does the same with the same save). The move menu shows a
  small sprite beside the player's healthbox - the Mega Evolution icon (at 130,90; callback 0x09D605E1; palette
  tag 0x2345). Each time the menu opens, the hack's routine at 0x09D6077C destroys that sprite and makes it again:
  DestroySprite (0x080070E9), LoadSpritePalette of {0x09D77CCC.., 0x2345} (0x09D77D1C), LoadCompressedSpriteSheet
  (0x08034531) of one of four 32-tile sheets at 0x09D77CF4 (tags 0x2346, 0x2345, 0x2347, 0x2348: which one goes by
  the battler and its kind of change), CreateSprite of the template that goes with it (0x09D89470 + 0x18 * n).
  Nothing frees the sheet, and LoadSpriteSheet (0x080084F8) does not look whether its tag is loaded: every
  opening took 32 more of the 1,024 sprite tiles. Measured (`_testrun/shinybox2/leak.lua`: a breakpoint on
  LoadSpriteSheet and on FreeSpriteTilesByTag, the free bits of sSpriteTileAllocBitmap 0x02021B3C): a single
  battle 543 free at the first menu, 287 after the menu was opened and shut eight times; a double battle 430,
  then 64 fewer every turn (two menus), 110 after five turns. No call of FreeSpriteTilesByTag for those tags at
  all. When a move's sheet no longer fits, LoadSpriteSheet returns 0, the animation's sprites get tile start
  0xFFFF and are drawn from tile 0 on: the first healthbox's tiles, in the animation's palette.
- **The fix**: the routine calls through a pool word (0x09D60848, loaded by the one instruction at 0x09D607F8);
  it points at load_once (sheetonce.s, 48 bytes at 0x08FEE100), which asks GetSpriteTileStartByTag (0x08008621)
  first and calls LoadCompressedSpriteSheet only if the tag is not loaded. Each tag has one picture (the patcher
  checks: four tags, four pictures), so the sheet that is there is the right one. The sheets go with everything
  else when the battle screen is torn down.
- Tested (hidden): the menu opened and shut eight times in a single battle - 539 tiles free every time, the
  menu's picture the same at the first and the eighth opening, pixel for pixel; ten turns of a double battle -
  398 free after turn 1 (the second battler's icon), 398 after turn 10; the ten-move battle in which Celebrate's
  confetti broke - three runs, its sheet loaded each time (350 tiles free), nothing drawn from another sprite's
  tiles; the 39 heal and drain moves in a double battle with every battler shiny - gold on all 238,740 frames;
  Gen 9's battle list (`moves.ps1`, the move menu in every case) - the same 116 lines as before.
  Not run on this build: the every-move runs and the whole regression list (`_testrun/full/tests_sheetonce.ps1`
  is ready).
- Space, as the user asks: 0x08FEE100..0x08FEE140 is 0xFF in the game before and in the hack's own ROM, inside the
  blank run 0x08FED3C8..0x08FEF600 (3.4 KB of blank before it, goldbox 0x2D0 after it); no word of the ROM at any
  byte offset reads as an address in it; read watchpoints on it while the game before was played (twelve moves in
  a double battle, the menus): 0 reads. The only other change is the hack's pool word.
- In the chain after `ballfree`, before `zhtext` (46 patches; the three copies of `rebuild_chain.py`). The same
  bytes in the chain and on top (2db23aa2... both ways; the Gen 9 base a8bd70c0...). Installed 2026-10-13: the
  working ROM, `rom/`, `roms/test-gen9` and "(my placements 20)"; backups "(before sheetonce 2026-10-13)" and
  "Gen 9 test (the base of 2026-10-13, before sheetonce)". In no release.
- Still open: Flatter (260) stops the game at "used Flatter!" in a double battle (the game of before too).

## THE REST OF GEN 9 (A TEST BUILD) — 2026-10-14 — `patches/gen9rest/`
- Asked for: "can we fit whole Gen 9?", then "spread of Hoenn", "u decide what best for me with safe route",
  "don't patch to the current yet, this will be like a test". Built on top of the working ROM (2db23aa2, after
  gen9 and paldea), NOT in the chain: `roms/test-gen9full/Hyper Emerald - Whole Gen 9 test 1.gba` (7f4a9f2b...).
  `python -I gen9rest_patch.py <working ROM> <out> <Crest_v1.0.F.gba>`; `check_gen9rest.py before after` audits
  every changed byte (0 unexpected on test 1).
- The safe route as chosen: no new battle-engine code. Moves are copies of moves the game has (template rows);
  abilities are aliases (gen9's list, made longer); evolution methods the game lacks are levels or items.
- **Species tables 1,280 -> 1,408** (`GROW_AT` 0x09AC0000): speciesx's 23 tables moved again by the same rules
  (367 words + 4 field words + the 9 count sites, now 0xB0<<3 / 0x57F / 0x580). Slots 1238-1326: 85 species and
  4 forms (Paldean Wooper 1323, Paldean Tauros 1324-1326, sharing numbers 194 / 128). Data 0x09B00000..0x09C286E8.
  The ability table 0x097A0000 grows in place (zeros to 0x09800000).
- **Moves 948-985** (`NEW_MOVES`): row = template's 12 bytes with the official type/power/acc/PP/category, then
  overrides. Row bytes: effect, power, type, acc, PP, chance, target (0 one, 8 both foes, 32 all others),
  priority, flags (0x01 contact, 0x02 Protect, 0x10, 0x20, 0x40 high crit), stat (byte 9: 16+n +1, 32+n +2,
  144+n -1, 160+n -2; n 1 Atk 2 Def 3 Spe 4 SpA 5 SpD; effect 4 = the user, 5 = the target), category, an
  effect argument (recoil 1/n for effect 19, the charge text for 71...). Some effects are keyed by MOVE NUMBER
  in the engine and do not copy: Retaliate, Payback, Storm Throw, Frost Breath (effect 0). gen9's description,
  Z-power and Max-power tables are found by content. All 38 used in battle (`test_moves.lua`; Mew does not obey
  a givemon'd copy - not from the event; use Snorlax).
- **Abilities**: aliases 256k + base (k from 1, the first blank name), the base's text; gen9's alias list
  (0 terminated, one literal in gen9.s) copied longer. Run Away has 5 free ids, Illuminate 5. (Since 2026-10-21 ids of their own
  instead: *The Gen 9 abilities work in battle*.)
- **Items 770-775** from Thunder Stone's row (use) / Razor Claw's (held), hold effect cleared; Crest's pictures by
  Crest's spelling (`AuspciousArmr`, `UnrmkblTeacup`, `Leader'sCrest`; Crest has no Metal Alloy: Metal Coat's
  picture). Some Crest item palettes hold fewer than 16 colours: padded. Sold: the Lilycove clerk's list
  (pokemart at 0x08F55BF8 -> 0x09865D20, 19 items, also on map 12/29) copied longer. The stone shops are
  post-game (Steven's Island 35/37, Veilstone 37/30).
- **Evolution methods of this game** (its table, 8-byte rows): 4 level, 7 item used, 16 level up knowing a
  move, 18/19 level by day/night, 20/21 level up holding an item day/night, 22/23 by gender. The hack's own
  GetEvolutionTargetSpecies is 0x09F0534C (0x0806D098 jumps there; it reads the method as a byte).
  Test lesson: `test_gen9.lua`'s evolve mode sets the experience by the Slow group's formula: for any other
  growth group the Pokemon is already past the level and the game never calls the evolution check
  (`test_evolve.lua` uses the species' own group).
- **The Pokedex past 960** (dexext.s):
  * Flags: the hack's GetSetPokedexFlag 0x09257950 (vanilla callers reach it through 0x080C0664) gets an 8-byte
    jump to dex_flag: below 960 exactly the old routine (mask table 0x0832A328, 4 bytes apart); 960+ in the save
    stream's free margin, EXT 0x0203DA00: marker "DEX9" (0x39584544), 32 bytes seen, 32 caught (960-1215). No
    marker = nothing seen; the first set clears the 64 bytes and writes the marker (old saves, save states).
    ClearPokedexFlags' jump word 0x08084394 -> dex_clear (the hack's 0x092579D9, then the marker off).
    The only direct readers of +0x560/+0x5D8 besides the routine are vanilla BAG copies (0x08076ECC link/record,
    0x081ADC70 the Battle Pyramid's bag: it zeroes and restores the seen array there - the hack's own quirk).
  * Limits: GetNationalPokedexCount 0x080C07F4 (literal 0x3BF at 0x080C080C -> 1024); the hack's list buffer
    (Alloc 0x8FC at pool 0x09257914 -> 0xA20; blank fill 0x182..0x3C1 at 0x0925791C -> 0x409); eleven
    `movs rX,#0xF0; lsls rX,rX,#2` (960) in 0x09257B96..0x09258168 -> `#0x81, #3` (1032).
  * Entries 0x09250000 (960 x 32, code right behind) copied to 1,040 entries; 8 code literals repointed.
  * Order tables (pool 0x09257FA0 height 0x09258580, FA4 name 0x09259480, FA8 weight 0x09258D00; 960 u16 each,
    with zeros and junk, and none of 906-959): rebuilt with 1..1025, old order kept, new ones inserted by key.
  * Four digits: CreateMonDexNum's digits 0x080BD194..0x080BD1CC -> dex_digits (from 1000: "1000" in place of
    "No"+3); ConvertIntToDecimalStringN(…, 3) for the dex number at 0x080C025E (Pokedex page) and 0x081C2662
    (summary) -> two 16-byte jumps in the dead body of the game's old flag routine (0x080C066C, 0x080C067C) ->
    conv_dexnum (4 digits from 1000) / conv_dexnum_sum (also empties the summary's "No" 0x02021CC4 - the box
    has no room for "No1000"). Words in sound data point at 0x080C0700-04 by chance (not used).
- Tested (`_testrun/gen9rest`, the user's save): battle, catch (number 1000 set in EXT), summary, the Pokedex
  list and all 85 pages, level and move evolutions, all 38 moves, save + fresh boot (EXT and a new species kept,
  906-940 unchanged), the bag pictures. Not yet: walking to the wild spots, the shop on screen, item evolutions
  in game, New Game, DexNav, double battles.
- **Test 2 (2026-10-15), after the user: "bruh u have not tested shit? ... buy new item evolution at the clerk lily
  and then game keeps restart when buying".** Three faults, none caught by test 1 (it never bought or used one):
  * **The hack's shop guard.** BuyMenuTryMakePurchase's AddBagItem call goes through 0x080E0F00 -> 0x096FFF00
    (the hack's own; speciesx's region stops just before it): it checks the item bought AND every id in the list
    menu (8-byte rows from [task2 data], until an id >= 800) against a bitmap - byte 0x09E0FE5F - (item >> 3),
    bit item & 7 (check 0x096FFF64, one literal at 0x096FFF88; 441 of 800 allowed: no Master Ball, Rare Candy,
    Mega Stones, key items...) - that the name shown is the item's, and that sShopData->totalCost (at the list
    buffer - 0xC0: it assumes ShopData's heap block lies just before the list) >= 50 * quantity; any failure
    jumps to 0 (the only `movs r0,#0; bx r0` in the ROM) = a reset. Fix: the bits of 770-775 (byte
    0x09E0FDFF -> 0xFC). Test harness lesson: opening the mart with a bare `pokemart` script puts the heap
    elsewhere and trips the totalCost check even on the untouched ROM - test through the real clerk
    (`test_martbuy.lua NPC=13,19,7,4 FACE=down`: Lilycove Dept. Store 13/19 or 12/29, object 4 at (7,6)).
  * **Items past 178 cannot be used on a Pokemon.** PokemonUseItemEffects (0x0806BD28, vanilla) does
    `if (item - 13 > 0xA5) return TRUE` before gItemEffectTable (0x0831E58C; words at 0x08063FDC, 0x0806BE90,
    0x0806CE04, 0x0806D010, 0x081B6304/6B44/7D48). The hack's own use-evolution items are all <= 178. evoitems.s:
    8-byte jump at 0x0806BE70 (r4 = item - 13, item at [sp,#0xC], r1 free; no branch lands in 0x0806BE72..7F),
    the game's lookup for 13-178, the Thunder Stone's effect (0x0831E4FC: 00 00 00 00 80 00) for 770-774,
    else back to "no effect" (0x0806BEF1). Held-item (20/21) and known-move (16) evolutions need nothing.
  * **Dipplin's growth group**: PokeAPI gives Slow; Applin and Hydrapple Erratic. On evolving the game works the
    level out again from the experience (Applin 30 -> Dipplin 31). GROWTH_FIX in gen9rest_data; the patcher
    now asserts that every evolution pair shares a group.
  * Tested: buying at the real clerk (King's Rock and 770-775, five each); every use-item from the Bag
    (`test_useitem.lua`, the menus as a player goes); Bisharp + Leader's Crest, Dipplin + Dragon Cheer,
    Girafarig, Dunsparce (`test_evolve.lua` HELD= KNOWS=; it computes the experience by the species' group).
  * Test 2: `roms/test-gen9full/Hyper Emerald - Whole Gen 9 test 2.gba` (0f5a510e...) and "(DexNav open)"
    (37cca4c2..., `dexnav_open_test.py`, made by another session for the test 1 build).

## THE DEXNAV BAR'S ICON IN ITS OWN COLOURS — 2026-10-15 — `patches/iconpalfix/`
- Reported on the whole Gen 9 test: "dexnav scan, sometimes mostly the pokemon img color is kinda inverted
  especially on gen9". The fault is the main game's (not Gen 9's). The user: "OFC" (put it in the game). In the
  chain after `sheetonce`, before `zhtext` (47 patches; the three copies of `rebuild_chain.py`); the chain differs
  from 2db23aa2... in the one byte 0x080D2F35 (d9 -> e0). Installed 2026-10-15: the working ROM, `rom/` and
  "(my placements 21)" are 40685de4..., `roms/test-gen9` 356a8bb6...; backups "(before iconpalfix 2026-10-15)" and
  "Gen 9 test (the base of 2026-10-15, before iconpalfix)". Checked on the user's own save (placements 20's):
  Route 102, Rookidee (icon palette 2) in the bar's slot tagged 0xDAC1 before, 0xDAC2 after; Grookey and Ralts
  (palette 1) the same both ways.
- The search bar (dexnavchain: litE_loadiconpal, the word at 0x08FDF034 - LoadMonIconPalette's only user in the
  ROM) loads its icon's palette with LoadMonIconPalette (0x080D2F28), which still clamps `species > 412` to 260
  (INVALID_ICON_SPECIES, icon palette 1); CreateMonIcon and FreeMonIconPalette (0x080D2F68) read the real species
  (the hack removed their clamps). So for any species above 412 with icon palette 0 or 2, the bar loaded palette 1
  (tag 0xDAC1) and the icon - asking for its own tag, not loaded - drew with that slot; and the palette was never
  freed. Measured (`test_iconpalfix.lua`, palette slots and tags dumped with the bar up, Route 102): Nymble
  (palette 0) in slot 15 tagged DAC1; after the fix DAC0, Grookey DAC1, Rookidee DAC2.
- Fix: 0x080D2F34 `bls` -> `b` (01d9 -> 01e0). The patcher asserts the routine and that its palette-id literal
  (0x080D2F60) is the header's 0x13C table.
- Icon palette tags in this hack: 0xDAC0 + id (6 loaded by LoadMonIconPalettes, species use 0-2); the three
  palettes equal Crest's 0-2 (checked), so the Gen 9 icons' own colours were right everywhere else.
- Test GOTCHA: the field's orange cast on Route 102 late in a session is the hack's evening tint (the same on the
  untouched ROM at the same moment): game time = RTC + the save's offset, not the PC clock.

- **gen9rest test 3 (2026-10-15)** = test 2 + iconpalfix (`roms/test-gen9full/... test 3.gba` 28ffd40f...,
  "(DexNav open)" c143ab36...). Tested at the user's word ("test for me"):
  * The wild, 45/45 (`wild_cases.py` reads each placement's map, slot, rod, levels and tiles of the right
    behaviour; `test_wild.lua` warps onto one, callnatives SweetScentWildEncounter 0x080B5579 or
    FishingWildEncounter 0x080B5735 (hooked by the hack at its start; rod in r0, set by a breakpoint), and sets the
    slot the game's own picker returns: a breakpoint on ChooseWildMonIndex_Land / _WaterRock / _Fishing (0x080B4AC8 /
    0x080B4B84 / 0x080B4BD8) learns its caller's return address (the hack's TryGenerateWildMon 0x09D454FA; its
    fishing 0x09F060CA) and overwrites r0 there. Results in `wild_results.txt`.
  * Night evolutions: the hack's GetEvolutionTargetSpecies method 19 = hour 18..5 by 0x09F0527C (RtcCalcLocalTime,
    then gLocalTime +2 = 0x03005CFA); `test_evolve.lua HOUR=` writes the hour after it is computed.
  * Selling (`test_martsell.lua`): money SaveBlock1 +0x490 xor SaveBlock2 +0xAC; no guard on selling.
  * New Game (`test_newgame.lua`, no .sav): dex_clear ran once, flags empty, marker 0; a wild Fidough sets 961 +
    the marker.
  * The normal DexNav (`test_dexnav.lua`): shadows for unseen, registration refused, then seen -> registered ->
    the patch (state +28/+29) walked into under a Repel (var 0x4021; the patch's encounter passes Repel) -> the
    species. Random walking meets ordinary encounters first (ORAS rules), which is not a fault.
  * Doubles (`test_gen9rest_doubles.lua`, the double mode plus a party-screen step): 12 pairs, no freeze; the
    harness cannot pick a second replacement when both of ours faint.

## SIDE QUESTS RECHECKED — 2026-10-15 — `patches/sidefix/`, `patches/questlog/`

The user: "recheck the side quests in journey, such as Ash's challenge and the note's sender, how does it work? and
is it actually correct?", then "what about Galar gift?" and "the Lilycove Hall contest pass? the receptionist takes
you to the contest right away". Every Side Content row's flag was checked against the scripts that set it (all are
set where the row says), then the rows' conditions read script by script; the doubtful ones were played in mGBA.

- **Ash's challenge (0x4302)**. Not Route 101 by itself: the rival in Birch's lab (1/4 object 2, `0x081FA3EC`; var
  0x40D3 >= 2, then `0x098C0000`) needs 0x40C3, offers a battle, and on yes sets var 0x4060 = 0 and then var 0x409C =
  10 (the usual rematch) unless 0x4302 is clear and 0x41D5 (Team Rainbow Rocket at the Mountain Top), 0x4300 (Hero
  Greninja) and 0x4301 (Burning Soul) are all set: then Ash walks in, 0x409C = 11, `warp 0/16`. Route 101: ON_WARP_INTO
  `0x0988C9D4` adds the rival (10) or rival, Ash and the passerby (11); ON_FRAME `0x081EBCD5` (0x4060 == 0) sets 0x4060 = 3
  and runs the scene `0x0988CB19`: special 239 with 0x8015 = 1294 (Ash), 0x8005 = 1295 (the passerby), 0x8006 = the
  rival (1296-1301 by starter and gender) - you and the rival against Ash and her. Won: the cartridge, the note,
  0x4302. Lost: special 183 != 1, whiteout (`callasm 0x08FF2211`); talk to the rival again. Played: all three flags ->
  Ash in the lab, Route 101, the scene up to the party choice; 0x4301 clear -> the rival's battle alone. 0x409C is left
  at 11 after the scene (the rival's branch zeroes it, Ash's does not); harmless: the Hoenn League's hall zeroes it
  (`0x09843446`), the Sinnoh League's hall too (`0x098753AE`), and so does a whiteout (`0x082718CC`), and nothing else
  warps into Route 101.
- **The note's sender (0x4303)**. 35/8 object 18 (local 19, 4,5, flag 0) in the top room of Steven's residence (reached
  by 35/87, whose east end leads up). The map's ON_WARP_INTO `0x0983CCD4` removes local 19 while 0x4302 is clear.
  Tested: absent before, present after, and not respawned by walking around the room. 0x4303 is set on the first word
  (`0x0983D0BF`), the battle (trainer 1016) is a yes/no after it.
- **The Burning Soul (0x4301)**. The sign (`0x0987B90B`, Magma Hideout 24/93 at 48,9) does nothing past its braille
  unless 0x4297 (TM53 taken) and 0x864 are set, the party is exactly one Pokemon and special 329 (slot 0's species) is
  157, Typhlosion. The flame creature's "will you leave?": Yes -> var 0x409C = 26, warp to Route 112, whose ON_FRAME
  (`0x098520CF`) collapses the cave (0x42E2) on 26 or 27; No -> rounds 1-3 by the Crimson Apostle (`0x0987B9D4`,
  temp var 0x4001, trainers 1155-1157), 27 at the end, then 0x4301. A lost round is an ordinary whiteout: 0x409C stays
  0, the cave stays open, you start again (tested with a lone Typhlosion at 1 HP: map 36/9 after, 0x42E2 clear, Route
  112 run). The row's "ONE try" was wrong.
- **Magikarp (was 0x4118, now 0x4552)**. The gift is the "1230-year-old demon soul" in the same top room (object 10, 7,7,
  `0x0988F037`: pay 1,996, trainer 1161, `givemon 129, 1`), not Route 210. Dawn on Route 210 (`0x0980977C`) sets 0x4118
  after her first battle, and he checked 0x4118: Dawn first, no Magikarp ever. `sidefix` makes him check and set
  0x4552, his trainer flag (id + 0x40C9 for ids above 0x357, NOTES *Lorelei*), so Dawn keeps 0x4118 to herself.
  Older saves: one that got the Magikarp has 0x4552 (he was beaten); one that beat Dawn first can now get it.
- **Blue's Galar team (0x40B9)**. 13/2 (Lilycove Museum 1F) object 10 (local 11, graphics 231, `0x0980B0DE`) stood at
  3,0 inside the top wall with movement type 76 (invisible); 3,1 is wall too (collision 1, behaviour 0, no counter),
  no script moves her and only the template points at her script: nobody could reach her (tested). `sidefix`: 3,2,
  height 3, movement type 8. After a battle (trainer 858) her script runs nine `givemon` in a row - 1081-1089, Galarian
  Mr. Mime, Stunfisk, Weezing and Corsola, Indeedee, Eiscue, Morpeko, Glastrier, Spectrier, all Lv15 - with no check of
  room: past the party they go to the PC, past a full PC they are lost (as in the original). Not a choice of one.
  Her lines: "Kalos" -> "Galar" (0x08B1443B; the Chinese said Kalos too), "Kotone" -> "Lyra" (0x0836E48E, the string
  moves up two bytes; only its start is pointed at). Her defeat line's "Green:" stays: it is `zhtext`'s moved text
  (0x09FD3184), and a shorter English there moves every later moved text; the hack's Blue / Green names are mixed
  throughout anyway.
- **Meltan (0x40CA)**: the Cove Lily Motel's Game Designer (13/1, `0x0981B76B`) after special 337 (`0x080C08E5`: Hoenn
  Pokedex 1-200 all caught). **Kubfu or Rockruff**: 0x40F2 is set when Palmer (26/14, `0x09812E05`) is beaten, gift-less;
  later talks give Rockruff for a 35+ singles streak (0x42DB, `0x09874AE1`), Kubfu with the Dark and Water Scrolls
  for 35+ doubles (0x42DC, `0x09874B3A`), another Kubfu for all seven Gold Symbols (0x42DD, `0x09874BAB`). Three rows.
- **Contest Pass (Key Items)**: the reception (13/4 object 0, `0x0821A554`) does `additem 266` only in a branch behind
  special 93 (`0x0821A5CF`) that plain play does not take; talked to with no pass, it entered the contest (25/37) and no
  pass appeared. The row is gone (`keyitems.py` says why).
- **Putting the Quest Log text into the finished game on the Mac** (`patches/sidefix/questlog_on_top.py`). The
  Quest Log's data is `questlog`'s, fourth in the chain, and the Mac cannot run `gen9`. The main chain built with the
  old and the new texts differs in 32,925 bytes, all in the Quest Log's blocks (the PAGES counts at 0x08FEC615, PANES[3]
  at 0x08FED368, Key Items 0x09F9A000, Side Content 0x09F9C000, the panel block 0x09FA0000), and the finished game holds
  the old build's bytes in every one of them. GOTCHA: `paldea` (journal_az.py) copied the Journal's and the Legends'
  panel rows into its own block (PANES[0] = 0x09FE2580, PANES[1] = 0x09FE3E28) with pointers to strings in the panel
  block, and those strings move when Key Items or Side Content grow or shrink. The tool re-points those 539 words by
  the string they pointed at - what `paldea` writes when it copies the new table on a full rebuild - and refuses if
  anything else of the game points into the block. Checked: 576 pointers of the two copies read the same strings
  before and after; 34 screens of the Post-game chapter (Area Zero's rows included) and the Legends are pixel for
  pixel the same as on the game before; the main chain with `sidefix` changes 33,188 bytes and the finished game the
  same bytes with the same values, plus the 570 of the re-pointed words.
- **Tests** (`patches/sidefix/test_sidefix.lua`, on copies of the user's save; the battles are skipped by setting
  0x273, which makes the hack count a lost trainer battle as won, with the party cut to one Pokemon at 1 HP): `blue`
  - she stands at 3,2, A from below, a battle, 0x40B9, 1081-1085 in the party; `soul_dawn` (0x4118 set) - the fee, a
  battle, a Magikarp, 0x4552 set, 0x4118 untouched; `soul_done` - his last line only. Controls on the game before:
  Blue unreachable, no Magikarp. Quest Log screens of the changed rows and their A pages; Side Content 17/45 and Key
  Items 38/54 on the user's save. `tools/text_overflow.py`: the same report before and after.
- **Installed (Mac)**: the working ROM and `rom/` are 370503cf84100dc0aa44a8414dfc35bcf445911a (from `rom/`'s
  40685de4...; the main game alone 048790b490633194a8314fd9f479a5ed63fb1ba0). Backup "(before side quest fixes
  2026-10-15)" = 36c0f986..., what the Mac's working ROM was. The Windows PC: `sidefix` after `iconpalfix` in
  `rebuild_chain.py`.
- **The full rebuild, on the Mac** (the user brought the Crest ROM the same day: `rom/Crest_v1.0.F.gba`, sha1
  e892062a..., git-ignored). From the v1.4 archive: the main chain (48 patches with `sidefix`), `speciesx`, `gen9`
  (`python -I`, the Crest ROM), `paldea` (`python -I`, `rom/placements.txt`, `rom/ground.txt`). Without the fixes:
  fee5c5cf... / 356a8bb6... (the Gen 9 base, as on the Windows PC) / 40685de4..., the Windows PC's game. With them:
  c877c78b... / c919d3ba... / **370503cf...**, the game made with `questlog_on_top.py`, byte for byte. `gen9rest` on
  the game without the fixes gives 28ffd40f... (Whole Gen 9 test 3) and `dexnav_open_test.py` c143ab36..., as on
  the Windows PC; on the fixed game f71d606c... and e6d75ed6..., "Whole Gen 9 test 4" in
  `rom/unreleased/whole-gen9-test/` (its `.sav` a copy of test 3's). The fixes change the same 33,758 bytes with the
  same values in the game and in the Gen 9 test.
- **Whole Gen 9 test 4, tested on the Mac** (the user: "can u full test especially gen9 related"). The tests of
  `patches/gen9rest` and `patches/sidefix`, run on test 4 and on test 3 as the control, 600 runs, with
  `tests/gen9mac/` (`gen_jobs.py` makes the list, `runner.py` runs twelve at a time in the headless mGBA):
  * wild 45/45 (`wild_results.txt`'s placements) and Area Zero's three tables (Paradox Pokemon, Lv 63-67); a battle
    with each of the 89 new slots (seeded: the two builds log the same); catch x6, summary x4, the Pokedex 906-1025,
    a TM screen; 39 evolutions by level, move and held item; Greavard at every hour (evolves 18:00-5:59, not
    6:00-17:59); 8 item evolutions; the 38 new moves (none hangs); buying 5 of each new item at the Lilycove clerk
    (the right money, no reset); selling two; New Game (empty Pokedex, a Fidough sets 961 and the marker); the
    DexNav (unseen refused, Fidough registered once seen, the search brings it); 12 double battles at Lv 100; save +
    a fresh boot (the 960+ flags and the new species in the PC kept); sidefix's three cases.
  * Everything passes on test 4, and test 3 gives the same except sidefix's cases (the old behaviour) and what the
    power-on random seed decides (IVs, levels, abilities).
  * Harness lessons (Mac): the headless mGBA does not call Lua breakpoints, so `test_wild.lua`'s slot is forced by
    writing `movs r0, #slot; bx lr` over the game's slot picker in that run's copy of the ROM (the test's VECTOR /
    GUARD / dex_clear lines never appear there); `test_martbuy_count.lua` logs the money and the Bag instead. New
    Game must run with no `.sav` (else A is Continue). `test_dexnav.lua SEE=` is a species (Route 102 row 2 column 1
    is Fidough). Species 274 is Gigantamax Duraludon, 1186 the one that evolves. Greavard's night: SaveBlock2
    +0x9A (the clock offset's hours). Doubles at Lv 60 stop at the party screen when both of ours faint (the
    script's limit, as on the Windows PC); at Lv 100 all 12 run through.
- **The owned-Pokemon pass** (the user: "test all of this, especially owned, and also beaware of visual glitches"):
  `tests/gen9mac/gen_jobs_owned.py` + four new tests, on test 4 and test 3, 647 runs, ~1,700 screenshots looked at.
  * Breeding (`test_breed.lua`): each of the 89 new slots with Ditto in the Day Care (SB1 + 0x3030; the second
    parent's steps set to 0xFE before each step, so every step is the game's own roll), the Day-Care Man's script
    (0x08291C18; flag 0x433E set first, else his first talk is the Oval Charm), the Egg hatched by walking. 89/89:
    each Egg the line's first stage (Annihilape -> Mankey, Kingambit -> Pawniard, Hydrapple -> Applin, Archaludon
    -> Duraludon 1186, Clodsire -> Paldean Wooper, each Paldean Tauros its own breed); Gimmighoul and Gholdengo
    never get one (no-Eggs group, 40 rolls). The hatch scene draws every one right.
  * Rare Candy from the Bag (`test_candy.lua`: the Items pocket rewritten so one Rare Candy is last): 40
    evolutions by level, known move, held item, Greavard at 22:00 (evolves) and 12:00 (does not).
  * Party, summary (3 pages) and PC screens of all 89 (`test_screens.lua`), and every one shiny: no glitch; every
    shiny palette differs from the normal one (Gimmighoul, Gholdengo, the Tauros breeds only slightly - Crest's
    palettes). GOTCHAs: the summary closes onto "Do what with this PKMN?" (B again); the PC opens on slot 1.
  * Each one fighting (`test_fight2.lua`): MODE=own, its four Lv 100 moves chosen on the menu with the D-pad (writing
    gBattleMons' moves does not stick: the menu keeps the old), both sides' HP held every frame; MODE=foe, it as
    the wild one against our Blissey. 178 runs, no hang. Not faults: Roar / Circle Throw end a wild battle
    (Fuecoco, Tarountula, Spidops: rerun from the next move), Beat Up hits once with one party Pokemon, Population
    Bomb hits 2-5 (gen9rest's Bullet Seed copy; 2-4 counted), "Blissey's Volt Absorb" after Pawmo's Entrainment.
    Jolteon and Pawmo's electric moves hit on test 4, test 3, the main game and v1.4.
  * Everything the same on test 3. Not covered: the foe mode's shots mostly catch our Blissey's turn (its Splash
    does not stick either), so the foes' own animations were seen less; the moves they used show in the PP logs.

## WHOLE GEN 9 TEST 5: THE POKEDEX IN OFFICIAL ORDER, EGG MOVES — 2026-10-15 — `patches/gen9dex/`, `patches/gen9egg/`
- Asked for: "for order of pokedex, reorder only gen9, don't touch the original rom since I don't wanna risk bugs also
  beaware of area zero implementation as well", then an 8-point test list ("test this but don't mind about other
  emulators"). Test build only: `gen9rest` -> `gen9dex` -> `gen9egg` (-> `gen9rest/dexnav_open_test.py` for the
  twin). `rom/` and the main chain are not touched. Test 5: f71d606c (test 4) -> 33ee387f..., DexNav open 29fbf86d....
- **gen9dex** (`gen9dex_patch.py`, `gen9dex.s`): the 120 Gen 9 Pokemon get their official numbers (gen9's 38 slots sat
  at 906-940, gen9rest's 85 from 941). What holds a number: SpeciesToNationalPokedexNum's table (literal 0x0806D448;
  Ogerpon's masks share 1017, Paldean Wooper / Tauros keep 194 / 128), gen9rest's 1,040-row entries table
  (0x09C1EB64, rows 906-1025 permuted), the three order tables (height / name / weight, words 0x09257FA0/4/8:
  numbers renamed; the name table's Gen 9 numbers re-sorted by the game's charset, case folded - gen9rest had used
  Python's order, so "-" sorted before letters and Chi-Yu, Wo-Chien, Houndstone stood one off), and Area Zero's
  Legends rows (literal 0x08FEB23C -> 0x09FE37E8, 100 rows; 7 renamed: 921->1001 ... 939->1024, still in order).
  Nothing else stores a number (DexNav, summary, list, counts, Quest Log ask at run time).
  The saves' marks: the hack's GetSetPokedexFlag (0x09257950, gen9rest's 8-byte jump) now jumps to dexmig_entry
  (0x09C28900): when dexext's marker word (EXT 0x0203DA00) is not "DEXA" (0x41584544; gen9rest's marker word in its
  code, 0x09C28710, was "DEX9" and is now DEXA), the old marks of 906-1032 (the area only with the old marker) are
  read into a 32-byte stack bitmap, the new numbers' bits cleared (SB1 906-959 both arrays, the whole area), the
  marker set, each mark written at map[old - 906] (u16 table 0x09C28800). One way: a migrated save shown in the main
  game would put Gen 9 marks on the wrong Pokemon.
  The page's number: PrintMonInfo (0x080C025E) prints "{NO}{CLEAR 1}" (0x085E8D4F, 5 bytes) then the number through
  a 16-byte veneer at 0x080C066C whose word pointed at gen9rest's conv_dexnum (four digits from 1000); with the name
  at x 132 the fourth digit touched it ("No1014Okidogi"). The word now points at page_num (0x09C28BC0): from 1000,
  r0 -= 5 (the digits over the No mark), then conv_dexnum. The new-entry page after a catch is the same routine.
- **gen9egg** (`gen9egg_patch.py`): only Frigibax had egg moves (gen9's); gen9rest added none. The table
  (0x09D78128: species + 20000, moves, 0xFFFF; full, 408 bytes after it) is copied to 0x09C29000 with 41 lists
  added (Scarlet/Violet's "egg", mapped with gen9rest's own move() rules: none left out); its three words
  (GetEggMoves 0x080703F0, BuildEggMoveset 0x08070468, the DexNav's egg-move picker 0x08FDEAE0 - it scans to the
  0xFFFF) repointed and GetEggMoves' bound (0x08070464) 2830 -> 3045. Longest list 12 (the buffer holds 32).
- **Tests** (`tests/gen9mac/`, Mac headless mGBA, test 4 as the control):
  * `test_pokedex.lua` (KEYS script; MARKER for test 4): list, five orders, 120 pages + area maps; per species the
    page equals test 4's but for the number, the area maps all equal (two differ only in the blink phase). Waits
    of 90 frames lose UP presses on the page (slide animation): 320+ is safe. `test_ql_legends.lua`: the 99
    Legends rows on test 4 and test 5 with the same save, pixel-identical (the Quest Log must be registered to
    SELECT: SB1+0x496 = 363, then test_ql_panes' ring keys). `test_catchdex.lua`: catches set the new number only
    (B pressed at the action menu can run from the battle - outcome 4). `test_newgame_dex.lua`: New Game.
    `test_dexmig.lua`: the three save kinds.
  * `test_tm.lua`: the TM pocket is 0x0203D308 (130 slots); the Bag SHOWS it sorted by TM number (item 378 + n =
    TMn, index n - 1; HMs 498-505 = 120-127), not in slot order - the first run picked the wrong TMs from row 62 on.
    The routine is the hack's 0x08FD7C70 (bit n of the 16-byte row). 254/254, "Learned" read as not able.
  * `test_relearn.lua`: CB2_InitLearnMove (0x081606A1) set as callback2 with 0x8004 = slot; sMoveRelearnerStruct
    pointer 0x0203BC34, moves +0x12, count +0x110 (with Cancel; not vanilla's +0x114). This game's relearner lists
    level-up moves only (Bulbasaur, Pichu, Mudkip: no egg moves).
  * `test_breed.lua EGGMOVE=`: 42/42 on test 5, 1/42 (Frigibax) on test 4.
  * `test_movetext.lua`: summary page and L panel for 938-985; 986/987 are empty ids (gen9rest adds 38, not 40: its
    docstring said 40 - corrected). Comeuppance copies Metal Burst's priority -5 (the hack gives Counter, Mirror Coat
    and Metal Burst -5).
  * `test_switch.lua`: switch out and back in (the battle's party screen lists the one out first: DOWN both times).
  * `test_ability.lua` / `test_healer.lua`: the 22 stand-ins against controls (ABIL=0 or the other ability slot;
    SEED set before the Pokemon are made, PINRNG for damage). In battle a stand-in is its template's id (gen9's
    alias pairs 0x09B00764 map 16-bit ids to the template), so battle messages name the template ("Oinkologne's
    Mummy!"). GOTCHAS: HP written at the action menu is put back from the party a few frames later - write it 8
    frames after; givemon may roll the hidden ability (Farigiraf with seed 999 got Sap Sipper); the hack's Sand
    Force boosts Rock moves x1.3 with no sandstorm (Rocky Payload, and so the old holders too).
  * `test_dexnavall.lua` + `gen_jobs_dexnav.py`: register with the D-pad on the DexNav's own cursor (the ui block
    from the task's data[0..1]), then a breadth-first path over gBackupMapLayout (0x03005DC0) to the patch. 68/68
    (45 placements, 23 Area Zero species) brought the registered species; no battle begun on a patch ever brought
    another. Harness lessons: A on the Pokemon being hunted STOPS the search; Repel (var 0x4021) asks the first
    non-Egg party Pokemon's level - set every slot to 100; a patch can come up out of reach (Mirage Tower: behind
    a 0x60 tile) - search again; warping onto water makes the player surf.
  * v1.8 saves (`test_oldsave.lua`): v1.8 rebuilt exactly - a0125f7's patches up to `namingkb`, then `zhtext`, the
    release hpatch's runs laid over it (they bring `fusionfix`, which v1.8 has) and the 169 bytes that later
    textfix / zhtext edits had changed put back from the v1.4 archive: sha1 ade383ba = CHECKSUMS.txt. v1.8 does not
    have `dexnavabil`, `shinyfade`, `evivpal`, `mistmsg`, `objpal`, `roamfix` or `sprframe`, though that commit's
    README lists the last three before `zhtext`. Three older saves of the user's saved in it; each dumped on v1.8
    and on test 5: equal but for the DEXA marker; saved in test 5 and loaded again: equal.
  * `test_soak.lua`: random input weighted by where the game is (field: mostly walking; battle: mostly A; menus:
    A / B / D-pad), a warp every 9,000 frames through the 43 DexNav spots, a hash of OAM + palettes + BG scroll
    every 60 frames (unchanged 2,400 frames under input = suspected, 9,000 = frozen) and the pc checked every frame.
    16 runs x 120 game minutes (test3.sav x6, PARTY9 x4, the three v1.8 saves x2): 4,568 battles, 634 warps, 67
    different callbacks, no suspected freeze, no crash. 120 minutes take ~140 s headless.

## PLAYING THE STORY BY HAND, FROM NEW GAME — 2026-10-15 — `tests/gen9mac/test_play.lua`, `tests/gen9mac/play/`
- Asked for: "can u start new game and play each flag script in order to test everything for me? imitate by hand???
  the release will be whole gen9+ area zero". Stopped by the user the same day ("stop the testing for now I think
  it is ready") after the first two Journal steps and most of the third, on Whole Gen 9 test 5.
- Played from New Game through the game's own scripts: the truck, the clock (the hack's difficulty choice runs in
  it), the TV, the rival's house, Birch and the starter (the bag's first ball is Charmander; Pikachu-LG comes as a
  second Pokemon), the lab (0x0860), the rival on Route 103 and the Pokedex (0x0861), Norman and Wally's catch
  (var 4057 0 -> 2 -> 3, 4085), Route 102 round the Cut tree through the Timeless Woods (34.67), Scott, Route 104,
  Petalburg Woods' Aqua grunt, Rustboro (a battle by the gym door the hack added: flag 0x273 set for it) and
  Roxanne's gym - Roxanne (Shuckle Lv 18 and species 1139) not beaten yet. ~90 wild and trainer battles, Gen 9 in
  the early grass (Lechonk, Squawkabilly, Tarountula). Every scene set its flags and vars; in-game saves load.
  No fault of the game found; everything that went wrong was the driver's, fixed as it was found.
- Worth knowing (not faults): before Cut, the only way west from Route 102's east half is the Timeless Woods (a Cut
  tree, gfx 82, at 11,7); Petalburg Woods has Cut trees too (the way north is the corridor of the grunt scene);
  Roxanne's team is far stronger than vanilla's for a Fire starter.
- The driver (its header lists the actions): GOTCHAS it hit - door tiles have collision bits (the goal tile skips
  collision and elevation); ledges are one-way jumps; elevation: 0 and 15 go with anything, else equal; people load
  only near the camera (walk toward the map's template position); the truck's exit is an arrow warp (hold the
  direction ~24 frames); the save menu's text prints letter by letter and a second save asks "overwrite?" (A while
  the field is held, stop when free); the Start menu's cursor is 0x0203760E (count +1, entries from 0x02037610, Save
  = 5); the battle action menu keeps its cursor (UP, LEFT before FIGHT; check HandleInputChooseMove 0x08057BFD);
  B in the evolution scene stops it; a screen inside a battle is not the end of the battle; HP written at the
  action menu is put back; the relearner, party menu and other screens: the SCREENS table. Speed: the map is read
  once per map (emu:readRange) and behaviours cached per layout.

## THE QUEST LOG'S GEN 9 ROWS, AND THE WHOLE OF GEN 9 IN THE GAME — 2026-10-15 — `patches/gen9journal/`
- Asked for (one message): "pull from dev repo and two adjustments, 1. at the battle scene, at L to see move info,
  change the name to like magnifier icon instead so it will be L magnifier cuz the text too long and cover some
  pokemon sprite 2. update the journey logs to include gen9 in terms of legendary and side quests / then patch to my
  current rom, including every fix and whole gen9". Their choices: Legends "The 20 Paradox" and "Kitakami ones as
  locked"; Side Content "Area Zero extras".
- **The game** is now the main chain (48 patches, `sidefix` included) + `speciesx` + `gen9` + `paldea` (the user's
  placements) + `gen9rest` + `gen9dex` + `gen9egg` + `gen9journal`: sha1 ca71db7b... in the working ROM, `rom/` and
  "(my placements 22)". Without `gen9journal` and today's two small changes it is exactly the Mac's Whole Gen 9
  test 5: the difference of `54_gen9egg` to test 5 is the same 15,408 bytes in 12 runs as `51_paldea` to `rom/`'s
  370503cf (the tag's picture, 429 bytes at 0x09FDC449; `paldea`'s script block one `setflag` longer from
  0x09FC47B1; the 13 words that point into that block, among them the three wild headers at 0x08E19128).
  `rebuild_chain.py` (all three copies) and `patches/paldea/rebuild.py` run the four steps after `paldea`;
  `rebuild.py` gives the same bytes. The main game alone is bf8a9d28... (the tag).
- **The tag** (`lmoveinfo/art.py`, `hud()`): the pill is 30 pixels wide (was 61) - the white L key and a 10x10
  magnifying glass (white ring and handle, light-blue lens, a glint). Same sprite size (64x32), same tiles count,
  nothing else in `lmoveinfo` changes. Holding L still shows the panel (a tap does not: it is shown while L is held).
- **Nemona's rematch** (`paldea_patch.py`, `nemona_home`): `setflag 0x43E4` right after her `trainerbattle`. A
  single battle's script goes on after the command only when it is won (a loss whites out), so the flag means
  "rematch won". 0x43E4 was checked free as the others were (no set/clear/check bytes for it in the ROM, no map
  object's flag, no aligned word, not a trainer flag; 0x43E3 has two chance `setflag` byte runs and is skipped).
- **Legends.** `paldea` (journal_az) gives the chapter 100 rows (row 0 + 92 + Area Zero's 7) and `gen9dex` renames
  the 7 to official numbers; `gen9journal` runs last, so every number it meets is the official one and nothing
  after it renames rows. New table: row 0 (its texts with 119), the 92 as they are, the 27 Gen 9 rows sorted by
  number (the 7 rows kept byte for byte, 20 new), then the 5 locked rows; PAGES[4] = {0, 125, 119, 1};
  `legend_all`'s `cmp r4, #NLEG` (0x08FEB220) 119. Where texts: the twelve wild Paradox Pokemon from the ROM's own
  wild tables (`paldea`'s three headers at 0x08E19128: past, future, icy cave - checked by their Titans' and the
  Frigibax line's presence), levels 63-67 read there; Iron Bundle is in two (the future's grass and the icy cave);
  the eight that stand on the map from `story.LEGENDS` (what `paldea` placed them by). Hints name no Pokemon.
- **Locked: status 10.** A Legends row whose second halfword is 1 is Locked. `row_status`'s legend branch
  (rs_legend) is reached by an 8-byte trampoline at 0x08FEB0F0 (its `lsls r1,#4; ldr r2,rs_legends; ldrh r4,[r2,r1];
  adds r0,r4,#0`; 4-aligned; r3 is free there): `lk_hook` does the same through the literal, then for a marked row
  `movs r0,#10; pop {r4, pc}` (row_status pushed {r4, lr}), else back to 0x08FEB0F8. The four tables indexed by
  status get an eleventh entry in copies: NAMEFG (literal 0x08FEA898) 5 = dim, TAGFG (0x08FEA89C) 5, TAGS
  (0x08FEA8A0) "Locked", STSHOW (0x08FEB244) 1 = the title shows. Every other reader of a status was checked: the
  panel draws a silhouette when the pane row's byte 1 is set (the locked rows set it, as "Gotta catch" does; status 9
  never comes) and its "where" text for anything but 7; the detail (A) shows the where text; the header, the grid
  and Gotta catch count status 1 only; ICONS and STCOLOR are no longer read by anything.
- **Three digits.** u8dec (the Journal's, 0x08FE55DE, not 4-aligned) printed 0-99: 119 came out with 0xAC as its
  tens digit. A 10-byte trampoline at its start with r2 (`ldr r2,[pc,#4]; bx r2; mov r8,r8; .word`: u8dec used r2
  anyway, and r3 is left as it was for its callers) to `u8dec3`: hundreds, then the tens always once there were hundreds, then the
  ones; below 100 the same bytes as before. Callers: the Journal (two), the Quest Log's header (four), grid (two)
  and badge case. The number buffer (V+0xE0, scratch to V+0xF0) holds "119/119" + end.
- **Side Content.** Ten rows after the 45, before the Badges (which share the table and start at its PAGES first
  byte: 45 -> 55): the four logs (F_LOGS), Arven's sandwiches (0x43B5, and 0x43B6 as the second flag in marks bits
  1-15), Nemona's rematch (0x43E4), a row per Sealed Vault stake (a row checks two flags at most: 0x43D8, 0x43D9,
  0x43DA), Booster Energy (0x43DC + 0x43DD; its picture the item's icon). New SIDES (rs_sides 0x08FEB230, the one
  word) and Side info-panel table (PANES+12), PAGES[6] {0,55,55,3}, PAGES[7] {55,8,8,3}.
- **Space**: 0x09FE8000..0x09FEC0F4 (16,628 bytes) of 0x09FE8000..0x09FF0000. The hack's own ROM is 0xFF from
  0x09F82519 to its end; `paldea`'s Journal block before it ends at 0x09FE4468 (15,256 blank bytes between) and
  its JOURNAL_END is now 0x01FE8000, so it cannot grow into ours; after ours, 0xFF to `paldea`'s sprites at
  0x09FF1000 (20,236 bytes). About 130 words in the ROM read as an address inside the 32 KB - all in pictures and
  sound data (0x086C..., 0x0980...); none is a word of the ROM header or a literal that code loads
  (`speciesx_patch.is_pointer`, which the patcher asserts). Not checked: a read watch of the area while playing
  without the patch (2026-10-11's runs watched other areas).
- **Tested** (`test_gen9journal.lua`, a steps file of `paldea/test_paldea.lua`, on a copy of "(my placements
  21).sav"; three harness commands added: `dex9` - Pokedex marks for numbers 960+ in gen9rest's block once the
  marker is "DEXA", `clear` too; `qcard` - the grid's cursor; `lmove` - FIGHT, L held, pictures): the first opening
  moves the save's marks (gen9dex) and the grid reads Legends 68/119, Side Quests 25/55, Badges 8/8; the Gen 9 rows
  Done / Seen / "???" with silhouette and hint as their marks say; the five Locked rows dim with a silhouette and
  "Location: Kitakami"; every Legends row caught -> "Gotta catch 'em all!" Done, 119/119, the Locked rows not
  needed; the ten Side rows and their details; Nemona's rematch in Station No. 3 (35/97): 0x43E4 clear before, set
  after winning; a wild Iron Hands: the new tag, L held -> the panel, let go -> the tag. GOTCHA of the test: list
  presses 8 frames apart got lost while a long list redrew (14 is safe).
- On the user's save the three vault stakes read "To do" though Wo-Chien, Ting-Lu and Chi-Yu are caught: they were
  caught at the Sealed Shrine of the tests up to 10, before the vault (test 15), so their stake flags were never set
  and the stakes still stand in that game's vault. The rows are right about that game; pulling the stakes ticks them.
- **Evolutions (2026-10-16).** The user, after the above: "evolution line?". `questlog` builds the Evolutions chapter
  early in the chain (`evolutions.py` + `tools/romdata/forms.py`, 1,200 species, regions to Galar), so no Gen 9
  family was in it - not even the Frigibax line of 11 October - and Primeape, Paldean Wooper, Bisharp, Applin and
  Duraludon did not show their Gen 9 evolutions. `gen9journal` builds it again from the finished game with the same
  code, its module constants pointed at this build's tables: EVOS / NATDEX / NSPECIES (forms.py and evolutions.py)
  = gen9rest's copies (its layout from 0x09AC0000 in speciesx's table order, 1,408 rows; checked against the header
  words 0x128 / 0x138 / 0x144 / 0x1BC, the National Dex literal and two evolution rows). Names: the Gen 9 slots
  in full through `species_display.FORMS` (from gen9_data / gen9rest_data's keys; the ROM cuts to ten letters),
  the six new items through `display_names.ITEMS_BY_ID`, moves moves.json lacks from the ROM's move-name table
  (`evolutions.EXTRA_MOVES`, a new hook, empty in the main chain); a Paldea region (906-1025) in `REGIONS` (no
  effect on the main chain: nothing there); Bisharp's two Leader's Crest rows (by day, by night) shown as one.
  Written in place at 0x09F82600 (the old data 41,416 bytes, the new 44,920, of 0xDA00 up to the Legends' blob at
  0x09F90000; the region's first word is the table every literal reaches it by); the row count (365 -> 400) in its
  three literals 0x08FEBA68 / 0x08FEBC94 / 0x08FEBE10. Nothing outside the region points inside it (checked as
  real pointers). The main chain's result is unchanged (bf8a9d28), and every page of the old 365 is the same line
  for line except Mankey's, Wooper's, Pawniard's, Applin's and Duraludon's (each with its Gen 9 Pokemon); Girafarig,
  Dunsparce and Tauros (its three Paldean forms) have pages now. Game: 65b5a7f6..., "(my placements 23)".
  Tested (`test_gen9evolutions.lua`; harness command `evosel`: the list's cursor V+0xFC / top V+0xFE): the
  changed and new pages from the user's save (unseen families are shadows) and with every Gen 9 number seen,
  the header (268/400, then 301/400), the last row; `test_gen9journal.lua` again on the final ROM.

## RELEASE v1.9 — 2026-10-16
- Asked for: "push to release repo", then "Full v1.9 release" (Gen 9 and Area Zero had been cleared to go public
  the same morning: "Yes, both public"). The game is the working ROM, sha1 65b5a7f6... (the chain from the v1.4
  archive gives it byte for byte, before and after the release's source edits below).
- `release/hyper-emerald-en-qol.hpatch` (3,215,517 bytes, 9,046 runs) and `release/CHECKSUMS.txt`: applied to
  `Hyper EMR LA v5.7 bugfix 2.gba` (f785bed9...) it gives 65b5a7f6.
- Public commit: the dev working copy mirrored as for v1.8, but without `site/` and the built `docs/` (only the
  hand-kept NOTES, DEXNAV-PROGRESS and showcase cross); the site's release switch made in the public checkout itself
  (`RELEASED_VERSION` = '1.9', the v1.9 card's note, Install's callout and "+QoL1.8", two FAQ answers) and built
  there: six pages change. The public `.gitignore` kept, with the one rule Area Zero's sprite sources need.
- README: the Gen 9 and Area Zero rows, the v1.9 showcase GIF, the one-way save note, the Gen 9 credits (Pokémon
  Crest, PokeAPI, pokeemerald-expansion).

## BASE STATS IN THE POKÉDEX (HOLD R) — 2026-10-16 — `patches/dexstats/`
- Asked for: "would it be possible to redesign the pokedex to display stats of each pokemon like a number + graph?";
  of the three ways offered (a panel on a button, a STATS page in place of CRY or SIZE, a fifth page): "let do the
  easiest one first". In the main chain after `sidefix`, before `zhtext`.
- **The page.** The hack's Pokédex is Emerald's: the INFO page's input task is Task_HandleInfoScreenInput
  (0x080BEDF4), the entry it shows is `sPokedexListItem` (0x02039B54 -> {dex number u16, seen bit 0 / caught bit 1}).
  On that page R, L, SELECT and START did nothing (L and R only turn the page in the L/R button mode). The
  description box is screen y 94..157.
- **Hook.** An 8-byte jump at the task's head (4-aligned; its first four instructions - push {r4, r5, lr}; sub sp, #4;
  lsls / lsrs r0 - have nothing pc-relative and are done again by the stub, which then goes on at 0x080BEDFC). Two
  words name the function (Task_LoadInfoScreen's, IsInfoScreenScrolling's comparison): both untouched.
- **Second build, the same day** (the user: "it works but it is hard to keep holding, can we make as another page, or
  something indicate to press R??"): R toggles, and a 41x14 "[R] Stats" tab (a 64x32 sprite, the L tag's look) sits
  at (194, 84), where the page's two boxes meet on the right, clear of the description's text. On / off is the INFO
  task's data[15]: the page uses data[0..5], StartInfoScreenScroll keeps the same task through Up / Down (so it stays
  on), and CreateTask clears it when a Pokémon is opened from the list. PlaySE(SE_DEX_PAGE) on each press.
- **Panel.** Four 64x64 sprites (screen x -8..247, rows 94..157) over the description box, made, drawn and shown in
  the same frame, behind the tab. The tab's callback finds it again and holds the state in data[] (lmoveinfo's
  design): a heartbeat the hook sets to 3 each frame, so anything that stops the INFO page (Up / Down to another
  Pokémon, AREA, CRY, SIZE, B, the caught-Pokémon page) takes tab and panel with it three frames later; data1-4 the
  pieces' ids + 1, data5 the species drawn. R off: the pieces go at once, the tab stays.
  Text: AddWindow (32x8 tiles, on window 0's bg, never on a tilemap), the LZ'd frame unpacked into it, the lines
  printed with the small narrow font, the bars with FillWindowPixelRect (a light track, then the colour), the tiles
  copied into the four pieces, RemoveWindow. Species = NationalPokedexNumToSpecies(dex number) (the hack's own,
  reached by its jump at 0x0806D40C); the stats from the table the header word 0x1BC names, read as the page runs.
  Bars: min(stat, 200) * 60 / 200 as (min * 615) >> 11 (the same for 0..200); colours below 50 / 80 / 110 / 140.
- **Space.** 0x09FDD000..0x09FDDF70 (code ..0x09FDD508, data from 0x09FDD600), in the FF run the hack's own ROM has
  from 0x09F82519: after fusionfix (0x09FDCE38: 456 blank bytes between), before paldea's Journal block (0x09FE1000:
  12,432 blank bytes after). No word of the header or literal that code loads points into 0x09FDD000..0x09FDF000.
  Tiles: 4 x 64 for the panel (sheet tags 0x5EC0-0x5EC3), 32 for the tab (0x5EC4), one OBJ palette (tag 0x5EC0).
- GOTCHA: goldbox put an 8-byte jump at LoadSpritePalette's head, and NationalPokedexNumToSpecies is a jump into the
  hack's code: the patcher accepts exactly those.
- **Tested** (`test_dexstats.lua`, steps of paldea's harness: `dexnum`, `dsinfo`): on the user's save, Bulbasaur
  (seen): the tab; R -> 45/49/49/65/65/45, total 318; R -> the page as before; R on, Down -> Venusaur's, on to
  Charizard (caught) 534; by setting the entry's number: 1007 Koraidon 670, 1025 Pecharunt 600, 151 Mew, 906
  Sprigatito; A to AREA -> tab and panel gone, B back -> both again (still on); R off; B to the list and A again ->
  off; 20 presses of R, then out of the Pokédex: 11 sprites in use before and after. Game 8462fa6f... (the chain's
  build and the patch on top of the v1.9 release give the same bytes), the main game alone d8467ef5....

## THE SHINY CHARM IS NOT IN THE PC — 2026-10-17 — guide text only

- The guide said the PC starts with a Shiny Charm (install, mechanics, Hoenn walkthrough, legendaries; since the
  Astro rebuild of 2026-10-03). Wrong. The new-game PC table is at `0x0837F790` (its one pointer is in the literal
  pool at `0x0816AE54`): EV-IV Display (650) and the six Power items (740, 735, 736, 739, 737, 738), x1 each, then
  0,0. Same bytes in the original v5.7 bugfix 2 and in our builds; no patch touches it.
- The Shiny Charm (119) is an item ball the original hack put on Route 118 (map 0/33), object local id 22 at 4,16,
  script `0x08FE4222` (finditem), flag 0x4022, extended sprite 0x3C (the TMs' ball). item_sources.scan finds no
  other source.
- It needs Surf. The ball and the tile below it (4,17) are a two-tile strip: the building to the west, a cliff
  row (y 15) to the north, sea (behaviour 0x15) east and south. A walk that only checks collision passes over the
  water (collision 0, elevation 1): check elevation and water behaviours too. From the beach (11..13,15) you surf
  west and land on 4,17 (elevation 3, no object: CanStopSurfing), then face the ball.

## KITAKAMI: THE TEAL MASK AND MOCHI MAYHEM — 2026-10-14..17 — `patches/kitakami/`

- What it is: Mossui Town (Kitakami) as an on-top patch for the finished game: Ogerpon's story in eight chapters
  (Briar's bus from Mossdeep once Area Zero's ending is over; Carmine, Kieran, the Festival of Masks at night, the
  Loyal Three, Ogerpon's four masks, the catch, Grandpa's mask change after), then Part 2, Mochi Mayhem (Briar's
  letter, the town under the mochi's spell at night, Nemona's battle, Pecharunt Lv 82 given once beaten). The Loyal
  Three can be caught where they hide after the story; with Pecharunt, the five Kitakami legends make the Quest Log's
  Legends 124. The story, the user's decisions and the build's history are in `rom/unreleased/kitakami/STORY.md` and
  `patches/kitakami/README.md`; this section is the reference for what it changes in the ROM.
- **In the game since 2026-10-17** (the user: "try to merge with main rom, make sure to not touch something
  unrelated, I don't want to have new bugs"): the last step of the chain, after `gen9journal`, with the user's
  `placements.txt` (`roms/test-kitakami/`, written by the editor `patches/kitakami/editor.py`; `rom/kitakami-
  placements.txt` is the copy the game was built with). The working ROM, `rom/` and "(my placements 26)" are
  382cf97c...; the game before it, 8462fa6f..., is in `archive/` ("before Kitakami 2026-10-17"). Three ways give the
  same bytes: the chain from the v1.4 archive (the three `rebuild_chain.py` copies), `patches/paldea/rebuild.py`
  (Area Zero's editor: `kitakami` is the last step of its TAIL) and `patches/kitakami/krebuild.py` (Kitakami's
  editor, "Hyper Emerald - Kitakami (my placements N)").
- GOTCHA, two editors, one game: Kitakami cannot be built on a game that has it (its space must be empty). Kitakami's
  editor builds on `krebuild.base_rom()`: `rom/` while it has no Kitakami, else `roms/before-kitakami/Hyper Emerald -
  the game before Kitakami.gba`. `rebuild.py` refreshes that file with each of the user's Area Zero builds (the
  stage before `kitakami`; only in the user's own folder, not in a test folder), so a Kitakami build always has the
  newest Area Zero places. Kitakami's Briar takes Jacq's tile in Mossdeep (70,32) after Area Zero's ending: if Jacq
  is moved in Area Zero's placements, the kitakami step stops and says so.
- **Space.** The blob at `0x09E40000..0x09E80000` (95,596 bytes used): zero-filled in the game and in the hack's own
  ROM, no real pointer in, read by nothing in 14 watched runs (`_testrun/space/kitakami_watch.ps1`, 2026-10-16). Code
  `0x08FEF540..0x08FEF600` (kit_bgmask, kit_hour), in the free run after goldbox: all 0xFF in both ROMs, no real
  pointer (one word in graphics data, at `0x086D65B0`, reads `0x08FEF5F9` by chance), 0 reads in 14 watched runs on
  the game without it (`kitakami_watch_night.ps1`, 2026-10-17).
- **Everything outside the blob** (`_testrun/kitakami/regions.py <game> <build>` accounts for each changed byte and
  stops on any it cannot explain; 71,750 bytes on 2026-10-17):
  - two `bl` into the hack's day/night tint routine (0x08CFE3E0): `0x08CFE3EA` (its hour read -> kit_hour: 22:00 in
    Mossui during the festival's night and Part 2's, the real hour otherwise) and `0x08CFE472` (`mov r8, r7; ldr r7,
    =0xFFFF0FFF` -> kit_bgmask: 0xFFFF1FFF in Mossui, so BG palette 12 is tinted too; the literal itself is shared and
    stays);
  - pointer words to tables copied longer into the blob: the trainer picture, palette, animation and coordinate
    tables (0x0901BE90, 0x0901C660, 0x0901CE30, 0x0901D218: 6, 18, 3 and 8 words; pictures 250-251 are Carmine's
    and Kieran's), the wild table (0x08E17D50, 15 words), the layout table (3 words, as Area Zero moved it), the
    field palette table (3 words; tags 0x1138-0x1140);
  - group 35's map table pointer (`0x08A54724`; maps 35/106-111: Mossui, the Hall, the family house, the Pokémon
    Center, two homes), Mossdeep's header +4/+8 (`0x08482564`: Briar added to Area Zero's copies of its people and
    scripts), map section 187's name (`0x085A1A58`: "Mossui Town", was "Route 225");
  - trainer rows 1358-1360 and 1378 (Carmine, Kieran twice, Nemona), the hack's sprite table entries 204-206,
    228-230, 235-239 (none used by any map: `patches/kitakami/sprite_slots.py`), the shop guard's bitmap byte
    `0x09E0FE54` (bits for Sweet Apple 88 and Tart Apple 89), gen9journal's five Locked Legends rows, row 0 and their
    panes, the two counts (`0x08FEB220`, `0x08FEC60E`: 119 -> 124), Area Zero's stamp in its scripts (30 places).
- **Flags** between 0x4337 and 0x441B (Part 2's in 0x437D-0x439F), picked one by one with
  `_testrun/kitakami/freecheck.py` (`kstory.py` names each); var 0x40F9 is Area Zero's stamp, shared.
- GOTCHA, shops: the hack's shop guard (`0x096FFF00`) resets the game when a shop's list holds an item outside its
  bitmap (byte `0x09E0FE5F - (item >> 3)`, bit `item & 7`). A new shop must give its items their bits
  (`kitakami_patch.allow_shop_items`).
- GOTCHA, a new Pokémon Center: its ON_RESUME must do `special 0x01A4` (InitUnionRoom, as CableClub_OnResume
  0x08277C30 does). Without it the Union Room name buffer (0x02022C20) is not cleared and the nurse's "It appears as
  if ... is playing" prints garbage (a crash in mGBA dev).
- GOTCHA, the night: the hack's tint leaves BG palettes 12-15 alone; a tileset that keeps ground colours in row 12
  stays bright at night unless the mask changes for that map.
- GOTCHA, trainer pictures: copy and repoint all four picture tables. With two of the four the battle hung on black.
- GOTCHA, keystone: `.align` and `.balign` padding assembles as `00 BF`; pad with `mov r8, r8` yourself.
- GOTCHA, palettes: at most six object palettes on a screen. Part 2's market went to seven with Area Zero's Arven
  and Penny (palettes of their own); the main table's 67 and 70 share. `kpeople.layout_report` counts every stage.
- Saves made before: Kitakami's maps and Mossdeep re-read their people when the stamp differs (Area Zero's way). A
  save made in Mossdeep on the game without Kitakami has Briar after Continue (`steps_oldsave.lua`).
- **Tested** on 382cf97c... (hidden, muted; `_testrun/paldea/run.ps1` with `_testrun/kitakami/steps_*.lua`): the
  whole of Part 1 (every chapter, the battles, a stall's shop, the catch, the mask change, save and Continue), Part 2
  from the user's Part 2 start save with their placements, the nurse, the Hall, the night (both nights, the market
  dark), a real Quick Ball thrown at Ogerpon (`steps_ball.lua`), the Quest Log (`steps_journal.lua`: 124 counted,
  Ogerpon's and Pecharunt's details, the count after they are caught), `test_walk`, `test_doors`, `test_wild` (r101:
  the game (the same, four times); `tools/text_overflow.py` (only the one text it flags on `rom/` too).

## FREE SPACE LEFT AFTER KITAKAMI — 2026-10-17 — `_testrun/space/free_survey.py`

- `free_survey.py <build> <the hack's own ROM>` lists every blank run of 4 KB or more with what the hack's own ROM has
  there, our patches' claims over it (FREE..FREE_END and the like) and the words that point in (real by
  `speciesx_patch.is_pointer`). Zeros below 0x09000000 are counted as the game's own data (blank tiles, empty tables
  read from their start), whatever points in. On 382cf97c... (all blank in the hack's own ROM too):
  - **Free and watched**: 0x09E10044..0x09E40000 (192 KB) and 0x09E80000..0x09F00000 (512 KB), the zero run around
    Kitakami's space (`kitakami_watch.ps1`, 14 runs, 0 reads), plus Kitakami's own unused room to 0x09E80000 (162 KB).
  - **Free by the static check, never watched** (~3.3 MB): the upper 16 MB's zero padding at 0x090D0DB9 (189 KB),
    0x096319C8 (124), 0x09652D48 (217), 0x0970119C (316), 0x097A1F1A (376), 0x098C6AF9 (229), 0x09900160 (774),
    0x099C21EA (140), 0x099E5508 (171), 0x09D8AC7E (478), 0x09E03764 (49), 0x09F0B8E3 (42); 0xFF runs, ~190 KB
    together, the largest 0x08FB9920 (37 KB), 0x09FA6464 (39), 0x09FB23B3 (23), 0x08FF8CEE.. (16 past summitfix).
  - **Kept by our patches** (1.37 MB blank today): gen9rest's 0x09C2A7CE..0x09D00000 (854 KB), speciesx's
    0x096C475B..0x096FFF00 (238), Kitakami's (162), Area Zero's (~56), the Journal's and Quest Log's growth.
  - **Not free**: 0x0901D5FE..0x090D0000 (714 KB: 15 code literals point in, likely chance, unproven) and
    0x09754F00..0x097A0000 (300 KB: a literal points into its middle).
- Other limits (2026-10-17): species slots full (1,279 of speciesx's 1,280 named); moves 938 of 1,024 rows; 99 blank
  trainer rows (1355-1458); 51 entries of the hack's sprite table on no map (`sprite_slots.py`: candidates, each to
  check); group 35 has 112 maps (a warp reaches 126); **flags are the tightest**: the extended range ends at 0x467F
  and `freecheck.py` passes 41 in it, four of them Kitakami's trainer flags (0x4617-0x4619, 0x462B: set, never read),
  seven below 0x4614 (0x407A, 0x414F, 0x415B, 0x416B, 0x43A4, 0x43A8, 0x43A9), the rest the trainer flags of blank
  rows 1355-1462 (taking one costs that row); every var 0x4000-0x40FF shows script use in the byte scan.

## A WILD POKEMON KEEPS THE ITEM IT WAS GIVEN — 2026-10-18 — `patches/wilditem/`

- Reported: "Light ball is not attached to pikachu when fighting him in the abandoned ship. An Oran berry is in its
  place." The Pikachu is object 2 of the Abandoned Ship's 24/56 (sprite 209, flag 0x447), script 0x098B96CB:
  `showmonpic 25`, `waitbuttonpress`, `setwildbattle 25, 34, 0xCA` (item 202, the Light Ball), callnative 0x08FFF201
  (0x8004 = 6, 0x8005 = 0), callnative 0x0981E531 (0x8004-7 = 6, 3, 25, 252), `dowildbattle`, then the object goes and
  0x447 is set. The trainer table has no Pikachu on the ship: it is this scripted wild battle.
- Why: SetWildMonHeldItem (0x0806EA68; the hack's code is vanilla's, with its Compound Eyes test hooked to
  0x09D00022, which also takes abilities 0x1C and 0x69, and the species table read at 0x09AC0000) skips only battles
  with gBattleTypeFlags & 0x302008 (trainer, legendary, Pyramid, Pike); otherwise Random16 % 100: under 45 nothing,
  under 95 the common item (base stats +12), else the rare one (+14) - 20 / 80 with Compound Eyes; when both are the
  same non-zero item it always gives it. It never reads the held item first. Pikachu's are Oran Berry (139) and
  Light Ball (202). It is called **twice** a battle: from the hack's battle setup 0x08FF10C0 (first thing it does,
  through the word at 0x08FF1178) and from vanilla's 0x080369E4. Measured (breakpoints at the entry and 0x0806EB90,
  `test_wilditem.lua`): the first call already turned 202 into 139, the second left it. Light Ball after both: about
  0.5 x 0.5 + 0.5 x 0.05 = 27.5 %; 13 of 40 seeds.
- The original hack's bug, not ours (checked 2026-10-18, the user: "so it is not bug by our work??? r u sure??"): on
  the hack's own ROM (`roms/original/Hyper EMR LA v5.7 bugfix 2.gba`) the roll function, the Compound Eyes hook, the
  battle setup at 0x08FF10C0 that calls it first, the call at 0x080369E4 and the Pikachu's script are byte for byte
  the same; the only bytes that differ are the function's three species-table words (0x08F186E0 / +0xC / +0xE there,
  0x09AC0000 / +0xC / +0xE here: Gen 9 moved the table), and Pikachu's items are 139 / 202 in both. The same test on
  that ROM (the save of 2026-09-23): both calls hit, Oran Berry 29 of 40, Light Ball 11.
- Scripted battles with an item (`tools/romdata/scan_static.py`, 48 rows): Route 110's Poochyena (Nugget), Route
  115's Altaria (Rare Candy), Fiery Path's Ninetales, Mt. Pyre's Absol, Aqua Hideout's Sharpedo, the ship's Pikachu,
  the Underwater Empoleon, the eighteen Totems of the Secret Bases (Z-Crystals), Giratina (Griseous Orb), Terminus
  Cave's Aerodactyl, the Remote Island and Whirl Islands ones, Glastrier and Spectrier, Area Zero's Great Tusk and
  Iron Treads (Leftovers), Kitakami's Loyal Three (Black Sludge, two scripts each), Milotic, Glaceon. Each lost its
  item the same way unless its battle sets one of the four flags; a species with no wild items lost it to nothing
  (both rolls write item 0 when the number says "common" or "rare"). DexNav (`dexnavchain`'s apply_extras writes mon
  +0x22) was overwritten too: the DEXNAV notes above already said "the game's own wild held-item roll still runs
  after ours".
- The Totems (the user: "does it affect z crystal? I believe the OG rom does not have z crystal issue"): Gumshoos'
  script 0x098C15B1 = `setwildbattle 788, 80, 623` (Normalium Z), `setvar 0x8000, 0`, a Yes/No ("Want to battle the
  Totem?"), callnative 0x094A224D, setflag 0x272 / 0x273, `dowildbattle`; on a win `setorcopyvar 0x8001, 1`,
  `callstd 1` (obtain item: var 0x8000). 0x094A224D adds 0x26F to var 0x8000 (623 + the type number: the Z-Crystal)
  and writes the Totem's data from a table at 0x094A2328. So the Z-Crystal the player is GIVEN never depended on the
  roll: var 0x8000 read 623 in every run on the hack's own ROM, whatever the Totem held. What the roll changed is the
  Totem's own item in battle: battle type 0 (0x272 / 0x273 do not set gBattleTypeFlags), both calls hit; the hack's
  own ROM, 40 seeds: Normalium Z 9, Pecha Berry (135, Gumshoos' common item; its rare one is 0) 27, nothing 4; our
  game before the fix 10 / 29 / 1; after it 40 of 40 Normalium Z. Not checked: whether the Totem's AI uses its
  Z-Move when it holds the crystal.
- The fix: an 8-byte trampoline at 0x0806EA7C (4-aligned; `bl Random16; lsls; lsrs` = `00f0a6fd0004000c`), right
  after the battle-type test, to keep_item at 0x08FF9800: GetMonData(gEnemyParty, 12) and, if non-zero, straight to
  the function's epilogue 0x0806EB90; else Random16 as before and back to 0x0806EA84. The prologue has run there, so
  lr is on the stack. Nothing branches into 0x0806EA7E..0x0806EA83 (all halfwords of the ROM scanned for b / bcc / bl,
  and every word, at any alignment). The bytes there are the same in the hack's own ROM, v1.4 and 382cf97c.
- Ordinary wild Pokemon: CreateMon zeroes the Pokemon, so they hold nothing at the first call and are rolled; the
  second call now keeps what the first gave. The odds do not change: with two rolls of the same kind, "the second
  one's item if it gives one, else the first's" and "the first's if it gives one, else the second's" are the same
  distribution (20.25 / 72.5 / 7.25 % none / common / rare for Pikachu). Measured: a `setwildbattle 25, 34, 0` 40
  times, same seeds: 11 / 26 / 3 before, 11 / 27 / 2 after (one seed differs: the second Random16 is no longer
  drawn when the first call gave an item, so the numbers after it shift by one).
- Tests (`patches/wilditem/test_wilditem.lua`, through `_testrun/wilditem/run.ps1`, the save of "(my placements 26)"):
  the real script 0x098B96CB 40 times from one moment, each with its own gRngValue: before 13 Light Ball / 27 Oran
  Berry, after 40 / 0 (both calls see 202 and keep it); the screenshot shows the Lv 34 Pikachu.
- Space: 0x08FF9800..0x08FF9838 (0x08FF9900 kept), in the 0xFF run 0x08FF8CEE..0x08FFD5A0. summitfix's window is
  0x08FF8B40..0x08FF9400 (its data ends at 0x08FF8CED: 2,834 blank bytes before keep_item); code at 0x08FFD5A1 is
  15,721 blank bytes after it. The hack's own ROM is blank there too (29,612 blank bytes before). No word of
  382cf97c reads as an address in 0x08FF9800..0x08FF9900 at any byte offset (`_testrun/space/kitakami_space.py`; the
  patcher checks again). Read watchpoints on the game without the patch (`_testrun/space/wilditem_watch.ps1` ->
  `wilditem_watch.txt`, 8 runs: the menus, Prelude Beach with every button, surfing and wild battles, the
  researcher / News Tracker / three saves and resets, four walks): 0 reads; the DMA control (0x08510000) was read in
  every run. The base-stats control that script inherits (0x08F186E0) reads 0 since Gen 9 moved the table, so the
  surf-and-wild-battle run was repeated with 0x09AC0000..0x09ACA000 as the code-read control: 25,023 reads there,
  0 in ours. Not covered: a watch on the patched game (keep_item itself is code that runs there).
- Chain: after `gen9journal`, before `kitakami`, so that `roms/before-kitakami` (Kitakami's editor builds on it)
  has the fix; the three `rebuild_chain.py` copies and `paldea/rebuild.py`'s TAIL. Whole chain from the v1.4
  archive = 382cf97c... + the patch = 8dac47f0... (main chain's result unchanged, d8467ef5...); before-kitakami
  1ea26019...; "(my placements 27)" = 8dac47f0....

## THE MEGA BRACELET COMES FROM STEVEN, NOT FROM MOM — 2026-10-19 — guide text only

- A player talked to Mom after Norman and got the Amulet Coin, where the guide promised the Mega Bracelet
  (mechanics, Hoenn walkthrough, the key items table). The guide was wrong, and the line it quoted from her ("…such
  a precious band, so he left it with me!") is in neither the v1.9 release (65b5a7f6) nor the working ROM.
- Mom (Littleroot 1/0 and 1/2, local 1, script `0x082929C5`): with flag 0x86B (fifth badge, set in Norman's
  script) and 0x85 clear she gives item 189, the Amulet Coin, and sets 0x85. No branch gives item 120.
- The Mega Bracelet (120) is Steven's, on Route 118 (0/33): three triggers at 42,3, 44,11 and 45,11 (var 0x4071 ==
  0) under the Route 119 connection (north edge, offset 40), scripts `0x098266FF`, `0x098267A8`, `0x09826780`.
  Each checks flag 0xD1. Clear: "There's an explosion at the power plant… I should go see Wattson…" and the
  player is walked back. Set: Steven's speech (`0x09826321`, "As my thanks for helping with Wattson's power plant
  problem…"), giveitem 120, var 0x4071 = 1.
- Flag 0xD1 is Wattson's (Mauville City 0/2, local 8 at 28,9, script `0x081DF73A`; hidden by flag 0x390 until
  Norman's script clears it): the Basement Key (271) and flag 0xD0 first; New Mauville's switch (24/53, 33,6) sets
  var 0x40BA = 2; back at Wattson, TM80 Volt Switch (457) and flag 0xD1.
- Later the bracelet goes away once: Zinnia's Granite Cave script (24/7, `0x09817AE6`) removes item 120 after her
  battle, and Zinnia gives it back at Meteor Falls (24/107, local 15). The in-game Quest Log's row
  (`patches/questlog/keyitems.py`) already said "a route east of Mauville".

## THE KEY TRAINERS' GEN 9 TEAMS — 2026-10-19..20 — `patches/keytrainers/`

- Luciano Fire (a coworker of the user; credit them in releases) rebuilt 42 trainers' teams with Gen 9 Pokemon on a copy of "(my placements 26)"
  (382cf97c...). Their second file (e19e1e44..., 2026-10-20, `roms/trainer-adjustment-coop/`) is that ROM plus 549
  bytes: 88 party entries of the 42 trainers (gTrainers 0x090019F8, 40 bytes each; the battle code's literals at
  0x0803587C / 0x08036320 / 0x08036480 name it) and Danielle's (#650) class 43 -> 20 (Battle Girl -> Lady) and picture
  64 -> 59 (59 is the Triathletes' picture; Lady's is 21 - left as the coworker made it, the user: "ok with this").
  No party moved or changed size, so no free space is used. Their first file (1429bf40) was a wrong one: an unedited
  build of 2026-09-29.
- `make_data.py base edited` writes `keytrainers.json` (every changed entry, raw old/new bytes and the fields read
  out) and stops on any difference outside a trainer's struct or party; `keytrainers_patch.py` checks every old byte
  before it writes (it refuses a game that already has it).
- Checked against the ROM's own tables before merging: every new species has stats and abilities (0x097A0000), every
  move a data row, every item a real id (the coworker used the main ids, not the duplicate names at 754-767), the
  Mega Stones fit. Their first edit had four slips, fixed in the second: Sidney's normal Greninja (#711) held
  Greninjium Z - measured, that Z-Crystal works only for Ash-Greninja #963 (Golden Shuriken), not #711 nor the Battle
  Bond Greninja #1011 (`_testrun/coop/test_z.lua`: START at the move menu is the Z trigger; Waterium Z on #711 gives
  Hydro Vortex); Phoebe's Ceruledge held Light Clay with no screen; Maxie #602's Skeledirge held an Assault Vest with
  Slack Off; Keegan's Cinderace was Lv 28. Still as made: Maxie #601's Heliolisk holds Throat Spray with no sound move.
- Chain: after `wilditem`, before `kitakami` (kitakami's nearest change is more than 64 bytes from any of these, and
  the bytes replaced are the same in the game before Kitakami), so that `roms/before-kitakami` - Kitakami's editor
  builds on it - has the teams. The three `rebuild_chain.py` copies and `paldea/rebuild.py`'s TAIL run it. Whole
  chain from the v1.4 archive = 1ecd960b... = "(my placements 28)" = 8dac47f0... with the coworker's 549 bytes
  copied in (main chain unchanged, d8467ef5...); before-kitakami bb39febc...; previous working ROM archived as
  "(before keytrainers 2026-10-20)".
- Tests: `_testrun/coop/run.ps1` + `test_coop.lua` play a trainer's battle (trainerbattle 3) from a late save, four
  turns for each foe, then knock it out, logging the party the game built against the data, every battle message
  (gDisplayedStringBattle 0x02022E2C - not gCurrentMove, which this hack's AI writes while it weighs moves) and
  pictures. The wilditem test on the merged game: Light Ball 40 of 40.

## KITAKAMI: CARMINE STOPS YOU; NO SUN LEFT ON THE TOWN — 2026-10-20 — `patches/kitakami/`

- The user, playing Kitakami: "Carmine should automatically see u and start battle when the player step up 1 step.
  Carmine should have alert emote to make sure player would not skip the script", and "she has ninetail with dought
  ability and after battle, it cuase the overworld sunlight, so it affect first impression of the town map".
- **Carmine.** Her battle was only in her talk script (`k_carmine`), so the player could walk past her into the town
  (measured: a step up from the bus stop did nothing). Now a coord event on the tile one step up from where Briar's
  bus leaves you (`ARRIVE` x, y - 1: 23,45 with the user's placements) runs `k_carmine_spots`: lockall, SE_PIN, "!"
  over Carmine, she turns to you and you to her, then `k_carmine_fight` (the battle, Kieran running in, the flag),
  which her talk script now jumps to as well. A coord event needs a var: VAR_TEMP_9 (0x4009, cleared on every map
  load), 0 while `F_CARMINE` is clear; `k_state_mossui` (ON_TRANSITION, ON_RESUME, and every refresh) sets it from the
  flag, and the script checks the flag itself, so the story's state stays flags only. `layout_report` checks that
  Carmine stands next to that tile and that the tile is the only way on from the bus stop (with it blocked, the user's
  placements leave a pocket of 10 tiles of the town's 1,256).
- **The sun.** A write watchpoint on SaveBlock1 + 0x2E (the map's saved weather) during her battle: the hack's own
  battle engine, `0x09D494AC` (called at `0x09D49690` as a battle ends), sets the field's weather from the battle's:
  sun -> 0x0C (Drought), rain -> 3 / 5, sandstorm -> 8, ... - except indoors (map type 8), in recorded battles and
  over a few weathers (0x0A, 0x0E, 0x0F). The same code is in the hack's own ROM; it holds until you leave the map.
  Mossui has no weather of its own (its evening and night are the tint routine's hour: kasm), so its ON_RESUME
  (`k_res_mossui`) runs `resetweather` (0xA3: the saved weather from the map's header) and then calls
  ResumePausedWeather (0x080AEE84: GetSavedWeather, SetCurrentAndNextWeather 0x080AB104) - the routine ResumeMap has
  just run with the battle's weather, before the on-resume script and before the weather task first draws: so the
  weather is set outright and the sun is never drawn. Other maps keep the hack's behaviour.
- **Lesson: not doweather.** The first build (29, ee18c144) ran 0xA5 doweather there: SetNextWeather starts a change
  (weatherChangeComplete = 0) while the field is fading in from the battle, and the fade never finished - the town
  stayed black behind Kieran's lines until the script's own fade (the user's screenshot). The test had the pictures
  (every frame of his lines black) and I only looked at the one after the scene. Look at every picture of a scene.
  Build 30 (6b167bfa): his lines over the town in its own colours; the frames after every story battle (Kieran's,
  the hunt, the finale, Part 2's at night) checked by eye.
- **The badges** (the user: "when battle in kitakami, the type badge is not shown, but when open bag or pokemon menu
  and back to battle, the badge will display"): not reproduced. Shown in every test - Carmine's battle (Mossui with
  and without the no-white-out flag, Mossdeep), wild Okidogi (with and without the Totem flags, Mossui and
  Mossdeep), the after-story Okidogi talked to, the Quick Ball widget up, after the Bag, eight turns with a thrown
  Quick Ball - and a sweep of moves as our lead's, one a turn (`_testrun/kitakami/test_badges.lua` MODE=sweep: shown
  badges against the foe's current types), stopped at the user's word after about half (1-200, 341-355, 676-850):
  none left a badge wrong. The user's screenshot is mid-battle (both HP bars down).
- Tests: `_testrun/kitakami/steps_k3fix.lua` (the step up, the battle by itself, the weather byte, no second
  trigger after the win); the whole story (`steps_story_mine.lua`, regenerated: Carmine is met by the step now) and
  Part 2 (`steps_part2_mine.lua`, from "(my placements 12) (Part 2 start).sav") pass. Working ROM = rom/ = "(my
  placements 30)" = 6b167bfa...; every byte that differs from 1ecd960b... is in Kitakami's space or a word pointing
  into it (its blob grew by the new scripts).

## PAUL'S SECOND EV-IV DISPLAY — 2026-10-20 — `patches/paulgift/`, `patches/questlog/`

- The report: "Paul gives duplicate EV-IV display. This is very minor but since you start with the EV-IV display,
  after beating Paul in Fortree he gives you another one, which does nothing." The user: "paul doesn't need to give
  again".
- **What was there.** The new-game PC holds one (item 650; the table at `0x0837F790`, *The Shiny Charm is not in the
  PC*). Paul's rematch is the coord event at 22,11 in Fortree City (0/4, var 0x400A == 0), script `0x0987D721`:
  lockall, setvar 0x400A 1, checkflag 0x42B1 (done) -> end; the door at 22,10 opens, `addobject 10` (object local 10,
  gfx 163, at the door, flag 0x42AF), his line, `trainerbattle 3` (trainer 1033), his speech, closemessage, then at
  `0x0987D775` "I'll give you this. I don't need it anymore……" (loadword 0 `0x0987D7AF`, callstd 4) and giveitem 650
  x1 (copyvarifnotzero 0x8000 / 0x8001, callstd 0) up to `0x0987D789`, where he flies off (applymovement 10, Fly's
  field effect, removeobject 10, setflag 0x42AF, 0x42B1). The original v5.7 bugfix 2 has the same bytes. The only
  other giveitem of 650 in the ROM (`0x09810457`) is in a script nothing runs: `0x0981041C`, a "Paul at the Day Care"
  (battle with trainer 959, the EV-IV Display, flag 0x4341, then an IV judge at `0x09810471`). No word anywhere in
  the ROM, aligned or not, points into `0x0981041C..0x098104A0` but its own goto_if; the same in the original.
- **The fix.** `goto 0x0987D789` (5 bytes) at `0x0987D775`. Nothing points into `0x0987D775..0x0987D789` (no word,
  aligned or not, in the whole ROM), so the 15 bytes left after the goto are never read; the string stays, unused.
  The script walkers (`tools/romdata/scripts.py`, `item_sources.py`) follow the goto, so they no longer list Paul as a
  source. Chain step `paulgift` after `keytrainers`, before `kitakami` (the three `rebuild_chain.py` copies and
  `paldea/rebuild.py`'s TAIL).
- **The Quest Log.** Key Items row 41 (of 54): "where" is now "In your PC from the start: Item Storage, then Withdraw
  Item." (the PC menu's own words, `0x085EAB41` / `0x085EAB63`), location "Your PC" (`portraits.LOC_OVERRIDE`; the
  text names no place, `place_in` would have said Hoenn). The row is ticked when the item is in the Bag, as before:
  a player who never takes it out of the PC sees it "To do". This text is in the main chain (`questlog`), so the Gen
  9 base (`roms/test-gen9`) changes with it: a9f9397b... (was 77072fae..., archived as "the base of 2026-10-20,
  before paulgift"). The bytes that differ from 6b167bfa...: Paul's 5, the Quest Log's Key Items block (0x09F9A29C..)
  and panel strings (0x09FA0DB4.., 0x09FA57D3..), and `gen9journal`'s rows that point at panel strings after it
  (0x09FEBD0C.., 0x09FEC078..): 5,115 bytes in 7 runs.
- **Tested** (`patches/paulgift/test_paulgift.lua` via `run.ps1`; `test_questlog_row.lua` via
  `_testrun/paldea/run.ps1 -Steps ..\paulgift\test_questlog_row.lua`), on a copy of the user's "(my placements 30)"
  save, the new build against 6b167bfa... (the control): flag 0x42B1 cleared, var 0x400A 0, flag 0x273 set and the
  party cut to one Pokemon at 1 HP (the hack counts the lost battle as won), warp to 22,12, a step up. Both: the
  door, Paul, the battle, his speech, the flight, 0x42AF and 0x42B1 set. The EV-IV Displays in the Bag (checkitem
  1/2/3): control 2 -> 3, fixed 2 -> 2. The script context's return addresses: the control calls the standard scripts
  from 0x0987D762, 0x0987D774, 0x0987D77D (his gift line) and 0x0987D789 (the item box); the fixed game only from the
  first two. Every screenshot read (contact sheets): no message box left over while he flies off. The Quest Log's
  grid and counts the same on both; the row's detail reads as above.
- GOTCHA: the `.sav` beside `roms/current` (6ab08a3c...) has no game this build reads (the new-game intro comes up);
  the user's saves are the "(my placements N)" ones in `roms/test-paldea`.
- GOTCHA: `rebuild.py` failed once with WinError 32 removing a step's fresh output (a scanner holding it); it now
  waits and tries again, as `rebuild_chain.py` does.
- Working ROM = rom/ = "(my placements 31)" = **8aeca761...**; the whole chain from the v1.4 archive gives it byte
  for byte (67 s), and so does `rebuild.py`. `roms/before-kitakami` = the `paulgift` stage, 0813e72e.... Backup
  "(before paulgift 2026-10-20)" = 6b167bfa.... The main game alone (49_zhtext) 265a0e93... (was d8467ef5...).

## CONTINUE WALKED YOU INTO A TREE; THE DEXNAV ICON AT NIGHT — 2026-10-21 — `patches/contexit/`, `patches/iconnight/`

- The report (version not given): "sprites are still buggy in dexnav (sunkern spearow). I entered the petalburg woods
  and saved my game (didnt take a single step). I reloaded the save now im stuck inside of a tree".
- **The tree.** Petalburg Woods (24/11, 48x44). Route 104's doors 10,38 / 11,38 lead to the woods' warps 2 / 3 at
  26,43 / 27,43 (the map's last row), and 32,42 / 33,42 to warps 4 / 5 at 36,43 / 37,43. Both rows of each way in
  have behaviour 0x6E (deep south warp: metatiles 0x37F/0x38F on row 43, 0x377/0x387 on row 42); only row 43 has
  warps. Coming in, FieldCB_DefaultWarpExit -> SetUpWarpExitTask (0x080AF334) walks you one step up
  (Task_ExitNonAnimDoor) onto row 42. Saved there, Continue runs CB2_ContinueSavedGame's callback
  FieldCB_FadeTryShowMapPopup (0x08086204) -> FieldCB_WarpExitFadeFromBlack (0x080AF3C8) -> SetUpWarpExitTask again:
  on 0x6E (IsNonAnimDoor: 0x60, 0x6C, 0x6E) it makes Task_ExitNonAnimDoor, one forced step (a held movement, no
  collision) the way you face. Measured (`contexit/steps_woods.lua`, the player object logged every frame, a write
  watchpoint on its tile): saved at 26,42 facing up -> Continue at 26,41 (path); a tap on Left at 26,42 (you only
  turn: the tree blocks the step) -> 25,42, a tree of height 1 among tiles of height 3, and no direction moves you;
  Right -> 27,42 (the other row-42 tile). The second way in the same (35,42 stuck). That is the report.
- Vanilla's code is the same (pret: FieldCB_FadeTryShowMapPopup ends in FieldCB_WarpExitFadeFromBlack), but vanilla's
  Petalburg Woods is drawn differently (ways in at 16/17,38 and 36/37,38) and has no door tile without a warp. The
  hack's own ROM has these woods (the original hack's map). `contexit/scan_doors.py` lists every tile of every map
  with a door behaviour (the values read from MetatileBehavior_IsDoor 0x08088EFC / _IsNonAnimDoor 0x08088F58), no
  warp and collision 0: 164 on 8aeca761 (the hack's own ROM 163), e.g. 0/3 (31,17) 0x6E, 24/24 (29,10-11) 0x6E,
  34/26, 34/67 (32-33,18: the woods' metatiles again), 36/5, 36/53, many houses' animated doors on their top row
  (Continue there played the door and stepped you down). The map group table is the hack's (0x08A54698, the
  literal of Overworld_GetMapHeaderByGroupAndId); its group lists have no end mark, so a group ends where the next
  one's list starts.
- **The fix (`contexit`).** CB2_ContinueSavedGame's literal at 0x08086314 (= 0x08086205, the only word of the ROM
  that holds it) -> cont_cb at 0x08FFA100: FieldCB_FadeTryShowMapPopup + FieldCB_WarpExitFadeFromBlack with every call
  kept (the map name popup, OnTrainerHillEReaderChallengeFloor, Overworld_PlaySpecialMapMusic, FadeInFromBlack,
  LockPlayerFieldControls) except SetUpWarpExitTask, which runs only when one of the map's warp events is on your
  tile (on_warp: PlayerGetDestCoords - 7 against gMapHeader.events->warps, any height); otherwise
  CreateTask(Task_ExitNonDoor 0x080AF611, 10), the task the game makes on a plain tile. Warps never come here (they
  use FieldCB_DefaultWarpExit), nor does a save made where the game keeps a "continue warp". The patcher asserts the
  two callbacks, SetUpWarpExitTask with its three task literals, PlayerGetDestCoords and Task_ExitNonDoor byte for
  byte (all the same in the hack's own ROM).
- **The icon.** Route 104 has Sunkern (slot 5) and Spearow (slot 7) in its grass (and Squirtle, slot 9: the report
  of 2026-10-19). At noon the DexNav screen and bar were right on the user's save. From 17:00 the bar's icon was not:
  `test_dnlook.lua` with HOUR set, 01:00 / 19:00 / 21:00 / 23:00: Sunkern dark blue at 23:00, red-orange at 19:00,
  Spearow darkened or pink, on the bar's black. The hack's tint (NOTES, *Day/Night*) halves channels for the palettes
  of the mask 0xFFFF0FFF (since `kitakami`, kit_bgmask at 0x08FEF540 picks it: 0xFFFF1FFF on Mossui), BG 0-11 and
  all 16 sprite palettes; the bar's window is BG 12-15, its icon a sprite (LoadMonIconPalette: tag 0xDAC0 + icon
  palette; gMonIconPaletteTable 0x0857C540 has tags 0xDAC0..0xDAC5). The DexNav screen, the party screen and the
  Pokedex are not tinted (pictures at 01:00, `iconnight/steps_night_menus.lua`).
- **The fix (`iconnight`).** Both ways out of the tint routine (tinted, or the hack's plain DMA) go through
  `ldr r0, [pc, #0xC8]; bx r0` at 0x08CFE40A, the word 0x08CFE4D4 (= 0x080A19E7, back into TransferPlttBuffer; the
  only word of the ROM that holds it). It -> icon_untint at 0x08FFA200: for each of the 16 sprite palette slots whose
  tag (sSpritePaletteTags 0x03000CF0, GetSpritePaletteTagByPaletteNum's table) is 0xDAC0..0xDAC5, the 32 bytes of
  gPlttBufferFaded + 0x200 + 32 * slot to 0x05000200 + 32 * slot again; then to 0x080A19E7 with r2-r7 kept (r0 / r1
  are loaded again there). Same VBlank, so no flicker. Kitakami's two hooks (0x08CFE3EA, 0x08CFE472) are untouched,
  so the step can go before `kitakami` and Kitakami's checks still pass.
- **Space.** 0x08FFA100..0x08FFA300 (contexit to 0x08FFA200, 208 bytes used; iconnight from 0x08FFA200, 68): in the
  0xFF run 0x08FF9838..0x08FFD5A0 after wilditem, blank in the hack's own ROM too. Of the 82 byte sequences in the ROM
  that read as addresses in that run (any byte offset), none lands in 0x08FFA0F8..0x08FFA400: the nearest is
  0x08FFA0F7 (at 0x080F2C5D, an odd address in code, a chance match). Read watchpoints on 8aeca761 (the game without
  them, `_testrun/space/contexit_watch.ps1` -> `contexit_watch.txt`, 9 runs: the menus, Prelude Beach with R / SELECT
  / START / L, surfing and wild battles, the researcher / News Tracker / three saves and resets, the woods' Continue,
  four walks): 0 reads; the code control (the base stats at 0x09AC0000) read in 5 runs (2 to 20,261), the DMA control
  (0x08510000) in all 9.
- **Tested** on the user's save of "(my placements 27)" (Timeless Woods), the fixed build against 8aeca761:
  * Continue (`contexit/steps_woods.lua`): no turn / Left / Right -> 26,41 / **25,42 stuck** / 27,42 before; 26,42
    all three after, then up, left, right and down all move. The second way in, Left: 35,42 stuck before, 36,42 after.
    Put on the warp tile itself (setobjectxy, ONWARP=26,43) and saved: Continue still walks you out to 26,42, both
    builds. Every eighth frame from the reset to the field read (45 pictures): the Continue menu, the fade, the woods
    with the map name sliding in.
  * The icon (`iconnight/test_dnlook.lua`, Sunkern and Spearow registered on Route 104): at 01:00 and 21:00 the bar's
    icon slot (14, tag 0xDAC1 / 0xDAC0) holds its noon colours after (426C 39CE 5EF7 7FFF ... for Sunkern), the
    tinted ones before (2126 1CE7 ... / 412C 38EE ...); the pictures show the route tinted as before and the icon in
    its own colours. 12:00 the same on both.
  * Each patcher refuses a second run, and runs on the other's output.
- **The report's sprites were not the tint.** The user, afterwards: the player is on v1.9 and it was not night. On
  v1.9 (65b5a7f6, `archive/`) at 14:00 on Route 104 (`test_dnlook.lua`): seen, Sunkern and Spearow are right on the
  screen and the bar; not seen, they are black silhouettes named "?????" with a grey Search (`dexnavseen`, asked for
  2026-09-30), as are Lillipup and Dedenne on the user's own save. They stay right through R / L page flips and cursor
  moves. `_testrun/woods/steps_barwatch.lua` (a search armed, then a walk; every 4 frames the icon's slot tag, its
  colours in gPlttBufferUnfaded and its 16 tiles against the ROM's two icon frames): nothing wrong but the bar's
  first frame (the icon's picture is copied the next frame). The land slot odds (ChooseWildMonIndex_Land 0x080B4AC8,
  vanilla's 20/20/10/10/10/10/5/5/4/4/1/1): Sunkern slot 5 10%, Spearow slot 7 5%, Squirtle (the report of
  2026-10-19) slot 9 4% - the three a player at Petalburg Woods is least likely to have met. Most likely they are the
  silhouettes; not confirmed without the player's screenshot. `iconnight` stays: it is a real fault of its own.
- GOTCHA: the save beside `roms/current` stops at boot in the read-watch harness (cb2 0x0802F6B1), as paulgift's
  notes say; use a "(my placements N)" save.
- GOTCHA: GNU sed turns `\U...` / `\n...` of a Windows path in the replacement into case changes and new lines; edit
  such lines with the editor. A heredoc with quotes in it failed in this shell too: write the text to a file first.
- Working ROM = rom/ = "(my placements 32)" = **66d87291...** (= 8aeca761... with both patches on top, byte for byte;
  `paldea/rebuild.py` with the chain gives the same). `roms/before-kitakami` = the `iconnight` stage, daa23880....
  Backup "(before contexit 2026-10-21)" = 8aeca761.... Chain: ... `paulgift` -> `contexit` -> `iconnight` -> `kitakami`
  (the three `rebuild_chain.py` copies and `paldea/rebuild.py`'s TAIL). The whole chain from the v1.4 archive gives
  66d87291... byte for byte (76 s); the main game alone (49_zhtext) is still 265a0e93....

## AREA ZERO'S PEOPLE IN PICTURES OF THEIR OWN — 2026-10-21 — `patches/paldea/` (`cast.py`, `sprites/people*.py`), `patches/kitakami/`

- The user: "can u custom draw npcs in paldea area zero? rightnow reusing npcs make the game look cheap", then "both
  overworld sprites and in battle scene"; of the mock-up sheet (`gba-trans/hyper-emerald/_testrun/paldea/people/Area
  Zero people - mock-up.png`: the official look for comparison, the stand-in, the new map sprite, the battle
  pictures): "everything is great". Up to then: Jacq main sprite 9, Arven 37, Nemona 20, Penny 58, AI Sada 202, AI
  Turo 46; in battle Nemona picture 194, AI Sada 218, AI Turo 31.
- **The drawings** (`sprites/people_map.py`, `sprites/people_battle.py`; `python sprites/people.py <rom>` writes
  `<person>.4bpp/.gbapal`, `<person>_battle.*` and `people_preview.png`, reading only the game's own pictures out of
  the ROM: `sprites/romgfx.py`). Each person is drawn over one of the game's own sprites so the style matches: map
  sprites over main sprites 14 (Nemona), 25 (Arven), 85 (Penny), 96 (Jacq), 202 (AI Sada), 172 (AI Turo); battle
  pictures over trainer pictures 114, 100, 187. A map character is a recolouring rule (facing, x, row, base colour)
  and drawn rows per facing (the head; some of the body); the walking frames are the base's own, recoloured by the
  same rule, with the drawn rows moved by the step's bob (a head only bobs). Lesson: the body's rows keep the base's
  outline exactly (colours only), or the walking frames' legs come out wrong; a head can change shape.
- **Palettes.** Six object palettes a screen. Mossdeep's ending has Jacq, Penny, Arven and Nemona by the hole with
  the town's 0x1103, 0x1105, 0x1106 and the hole's 0x1119: four palettes of their own would make eight. So two share
  one 16-colour palette: Arven + Penny 0x1141 (light skin), Nemona + Jacq 0x1142 (tan and dark skin); AI Sada 0x1143
  and AI Turo 0x1144 one each (only the Zero Lab has them). check.py counts the real tags (`own_tags`).
- **Map sprites.** The hack's sprite table entries 174 Nemona, 175 Arven, 176 Penny, 177 Jacq, 178 AI Sada, 180 AI
  Turo: the hack's own unused people (no map object uses them: `patches/kitakami/sprite_slots.py`; `cast.WAS` asserts
  their bytes). Each is a copy of its base's main-table entry (walking animations, OAM, shadow) with our nine frames,
  our tag and slot 2 (by tag), as Kitakami's people. Their palettes are rows of Area Zero's copy of the field palette
  table (`mons.put`'s `more`). Pictures, frames and palettes go after the rest of the sprite block, which runs to the
  ROM's end now: `SPRITE_END` 0x02000000 (was 0x01FFC000, 164 bytes left). Proof for 0x09FFC000..0x0A000000: blank
  (0xFF) in the hack's own ROM (`roms/original`, whose last used byte is 0x09F82518) and in 66d87291; no word that
  code loads or the header holds points into it (`speciesx_patch.is_pointer`); the 49 aligned words elsewhere whose
  value falls in it are chance (46 in the hack's own ROM at the same place, 2 in 4bpp tiles at 0x09B395A0 /
  0x09B90924, 1 in Quest Log text at 0x09FE805C); no patch uses it. The block is now 0x09FF1000..0x09FFF7AC (59,308
  bytes): 2,132 bytes left before the ROM ends.
- **Battle pictures 250-252** (Nemona, AI Sada, AI Turo). The four trainer picture tables (0x0901BE90 pictures,
  0x0901C660 palettes, 0x0901CE30 animations, 0x0901D218 coordinates, 250 entries, back to back) are copied longer,
  still back to back, at the end of Area Zero's main blob with the LZ77 pictures; the 6, 18, 3 and 8 code words that
  hold their addresses (the Quest Log's portraits at 0x08FEA820 / 0x08FEA82C among them; all are in `roms/test-gen9`
  already, so no later step writes the old address) point at the copies. Ours take the animations and coordinates of
  the pictures they were drawn over, and their own numbers as tags (unused). `story.TRAINERS`: Nemona 250, AI Sada
  251, AI Turo 252; `gen9journal` reads Nemona's for her Side Content row. The main blob is 0x09FBC400..0x09FCE6BC
  (74,428 bytes, +8,840): 17,220 bytes left.
- **Kitakami.** `ktrainers` finds the four tables through the code words (`REF_AT`: the first word of each kind; all
  of a kind must agree), their length from the layout ((palettes - pictures) / 8), and puts Carmine and Kieran after
  the last: pictures 253 and 254 (were 250, 251). Part 2's Nemona (row 1378) takes row 952's picture (`("as row",
  952)`); `check()` asserts row 952 is Area Zero's Nemona in a picture of her own. `regions.py` reads the tables'
  addresses through the same words. `ksprites.AZ_PEOPLE`: Part 2's Nemona wears Area Zero's entry 174
  (`kchapters.STORY_OBJECTS`, the editor). Arven and Penny stay the game's 67 and 70: in Area Zero's sprites (one
  palette between them) the night market (stage 12, Kieran's letter) and the dance (stage 15) showed seven palettes
  (the organiser and the stalls 0x1105, the mother and child 0x1106, Carmine, Kieran, Briar, Arven + Penny, Nemona or
  Pecharunt); their stand-ins share the mother's and child's. `kpeople`'s palette check now names what it counts on
  that screen.
- **Saves.** `STAMP_SALT` 15 (Mossdeep's people changed): a save made in Mossdeep or on an Area Zero map reads its map
  again and shows the new sprites.
- **Tested.** `test_story7.lua` on "(my placements 33)" with the user's save (Penny, the shut door, Nemona's battle,
  the guards, the finale's three battles, the ending in Mossdeep): passed, and all 1,305 pictures read (the VS splash
  and the battle show the new pictures; in the ending the five stand in their own colours). Kitakami Part 2
  (`_testrun/kitakami/steps_part2.lua`, on a build with the built-in places, from "(my placements 12) (Part 2
  start).sav"): passed, Nemona's battle in her picture, Pecharunt caught. `_testrun/kitakami/editor_test.py` passes;
  Area Zero's editor draws the six from the ROM.
- Working ROM = `rom/` = "(my placements 33)" = **8dafe8d1...**; `roms/before-kitakami` = 3e75e37b...; archive
  "(before Area Zero's own people 2026-10-21)" = 66d87291.... The whole chain from the v1.4 archive gives 8dafe8d1...
  byte for byte (80 s); the main game alone is still 265a0e93....

## EGG MOVES IN THE MOVE RELEARNER — 2026-10-21 — `patches/eggrelearn/`

- Asked: "hyper emerald, does this rom has npc to teach egg move?" No: the English text of "(my placements 33)"
  (every run of the game's characters) and the Chinese strings taken from the original have no line about egg moves;
  the tutors (the Dragon Elder, Cogita, the glass-flute man, the Shard tutors, Keldeo's Secret Sword ...) teach fixed
  lists, and the relearner listed level-up moves only (*Whole Gen 9 test 5*). Offered egg moves in the relearner; the
  user: "yeah in party relearner".
- **The relearner, read from the ROM.** The party menu's Moves (`relearner`) and the Fallarbor tutor open one screen.
  CB2_InitLearnMove 0x081606A1 and CB2_InitLearnMoveReturnFromSelectMove 0x08160741 (the way back from the summary
  screen when a move must be forgotten) each AllocZeroed(0x118) sMoveRelearnerStruct (pointer 0x0203BC34), the vanilla
  layout: movesToLearn +0x12 (25), partyMon +0x44, moveSlot +0x45, menuItems +0x48 (25 x {name, id}), numMenuChoices
  +0x110 (with Cancel), numToShowAtOnce +0x111, the list task +0x112. sMoveRelearnerMenuSate 0x0203BC38: listOffset,
  listRow, showContestInfo +4. CreateLearnableMovesList 0x08161280: GetMoveRelearnerMoves(mon, +0x12), each item
  {gMoveNames + 13 * move (0x09AB2EC4 = the header's 0x148), id = the move}, the nickname into gStringVar1, Cancel
  {gText_Cancel 0x085E8CF0, -2}, then LoadMoveRelearnerMovesList 0x081D28C8 (the template's items and count, no
  limit). GetCurrentSelectedMove 0x08161054: menuItems[listRow + listOffset].id. Nothing else reads the items, and no
  word outside the module holds 0x0203BC34.
- GetMoveRelearnerMoves 0x0806E0B4 = `ldr r2, [pc]; bx r2` -> 0x09D6A9D9 -> 0x09D6A93E (the hack's): the learnset from
  the pointer table 0x09AF0D00 (3 bytes: move u16, level; ends at move 0 or level 0xFF), level <= the Pokemon's
  (GetMonData 0x38 through 0x09D380D4), not one of its four moves, not twice, at most 24 (`cmp r4, #0x17` at
  0x09D6A998: 24 moves and Cancel are the 25 items exactly). GetNumberOfRelearnableMoves 0x0806E25C -> 0x09D6A9E1 ->
  the same routine without a list (it counts duplicates); called by the party menu at 0x081B0B6E (each slot's ABLE /
  NOT ABLE on the tutor's screen) and 0x081B95B0 (CB2_ChooseMonForMoveRelearner: gSpecialVar_0x8005, 0 = "no move to
  teach").
- **Correction.** *In-party move relearner* (2026-09-13) calls 0x08161B94 -> 0x09F06119 the move list builder. It is
  not: 0x09F06118 makes a Pokemon in gEnemyParty from SaveBlock1 + 0x31E4. The list builder is the one above.
- **The egg species routine.** 0x08070004 (the Day Care's GetEggSpecies) is a trampoline to 0x09F006F9, a wrapper
  (daycare, slot) -> 0x09F00600(species, mode). That one hard-wires Jolteon 0x87, Leafeon 0x20B, Glaceon 0x20C,
  Sylveon 0x2F1 -> Eevee 0x85, Manaphy 0x21F -> Phione 0x21E, Hisuian Typhlosion 0x443 -> Cyndaquil 0x9B (none of the
  six is a target in the evolution table); otherwise it walks back: the table through the literal 0x0806D140
  (0x09ADA200 today), species 1..0x57F, five entries of 8 bytes, the target at +4, the first species with an entry
  for it whose method's low byte is <= 0xF9 (Mega Evolutions and form changes are above), again from that one until
  none. Mode 1 (breeding) then picks Nidoran, Volbeat / Illumise and two more at random. Nine egg lists sit on a
  middle stage, not on the species that hatches: Chansey, Mr. Mime (122 and the Galarian 1081), Snorlax, Marill,
  Sudowoodo, Mantine, Roselia, Chimecho (their babies came later and have lists of their own).
- **Room.** 896 species gain egg moves. Modelled from the tables: at Lv 100 knowing four of its level-up moves, 56
  species would lose 1-8 egg moves in 25 items (Pikachu, the Eeveelutions, Donphan, Victreebel, Lucario ...); the
  longest list in the game is 36 (Donphan).
- **The patch** (`eggrelearn.s`, 0x08FFC900..0x08FFCB0C):
  * create_list (trampoline on CreateLearnableMovesList's first instruction): collect into 64 halfwords on the stack,
    the items at struct + 0x118 (65: 64 moves and Cancel), the rest as the game's (nickname, Cancel, +0x110, +0x111).
  * selected_move (trampoline on GetCurrentSelectedMove): the id from +0x11C.
  * count_moves (the word 0x0806E260): collect into a list on the stack, its length.
  * collect: GetMoveRelearnerMoves (0x0806E0B5: the level-up part is whatever that gives), then add_egg for the
    species and each step back (preevo: the routine's rule, the five entries unrolled; at most 8 steps); when the
    species has no step back, also add_egg(0x09F00600(species, 0)), for the hard-wired six (for any other species
    the routine only walks the table again: no species' list changes, checked in Python). add_egg: the table through
    GetEggMoves' literal 0x080703F0 (gen9egg moved it to 0x09C29000), its marker species + 20000, the moves up to the
    next marker or 0xFFFF; not the four known moves, not one listed; stops at 64.
  * Both allocations (0x081606B4, 0x08160754): `movs r0, #0xC8; lsls r0, r0, #2` = 0x320.
  * Read at run time, so a later repoint is followed: the move names (header 0x148), the egg table (0x080703F0), the
    evolution table (0x0806D140). The patcher asserts every other byte it counts on (both init sites, the two replaced
    functions with their pools, both trampolines, the hack's level-up routine with its cap, the egg species routine,
    LoadMoveRelearnerMovesList).
- **Time.** The first version ("(my placements 34)", a5f45f28...) always called the egg species routine and looped
  over the five entries: a count took 3-6 frames (Tinkaton 6.25: three near-full scans of mine, then the routine's
  three). Now (breakpoints on a stub's call, the frame number and VCOUNT): Pikachu 0.13 frames, Donphan 0.14,
  Azumarill 0.29, Eevee 0.51, Hisuian Typhlosion 0.09; Mewtwo 1.34 and Smeargle 2.04 (the routine's own slow scan),
  Baxcalibur 1.37, Tinkaton 1.64 (lines at the table's end). The tutor's party screen counts each slot once; the
  relearner builds its list behind its fade.
- **Space.** 0x08FFC900..0x08FFCC00 kept (0x20C bytes used), in the blank run 0x08FFA244..0x08FFD5A0 (0x08FF2454.. in
  the hack's own ROM). Every word at any byte offset that reads as an address in the run was listed (92): none in
  0x08FFC8F8..0x08FFCC02; the nearest are 0x08FFC8F7 (at 0x080C1811, odd, in code) and 0x08FFCC02 (at 0x095FEA4B,
  odd). 0x08FFA300.. (right after iconnight) was passed over: the aligned word at 0x09276580 is 0x08FFA400 (in data,
  not a pointer by `speciesx_patch.is_pointer`, but a stretch with none is better). Read watchpoints on the game
  without the patch (`_testrun/space/eggrelearn_watch.ps1`: the menus, Prelude Beach with R / SELECT / START / L,
  Surf and wild battles, the researcher / News Tracker / three saves and resets, Petalburg Woods and Continue, four
  walks): 0 reads in all nine, the two controls read in each.
- **Tested** (`test_eggrelearn.lua` and `check_lists.py`, which works the list out from the tables on its own;
  `_testrun/eggrelearn/run.ps1`, hidden and muted):
  * MODE=list: 27 species at Lv 100 and 10 at Lv 5 (Bulbasaur, Pikachu, Victreebel, Azumarill, Blissey, the
    Eeveelutions, Donphan, Smeargle, Mewtwo, Ditto, Hisuian Typhlosion, Sprigatito, Baxcalibur, Tinkaton, both Mr.
    Mimes, Mr. Rime, Mega Charizard, Magikarp, Lucario, Snorlax, Azurill, Happiny, Manaphy, Phione): every list equals
    the model, item for item. On the game without the patch (ITEMS=0x48) every list equals the level-up part.
  * MODE=count: a stub (test copy only, 0x08FFCB80) run by `callnative`, which needs the address with its Thumb bit
    (without it the CPU ran the stub as ARM and the script engine stopped): 36 counts equal their lists' lengths (0
    for Smeargle and Ditto).
  * MODE=learn: Pikachu Lv 100, item 27 of 28 (Teeter Dance, past the old 25) taught over Discharge through the
    summary screen and back (the list built again by CB2_InitLearnMoveReturnFromSelectMove, the cursor kept);
    Donphan, item 32 of 33 (Snore). Every frame looked at (contact sheets in `_testrun/eggrelearn`).
- Working ROM = `rom/` = "(my placements 35)" = **767e052c...**; `roms/before-kitakami` = c2c97e5e... (= 3e75e37b...
  and this patch: undoing its 546 bytes gives 3e75e37b...); archive "(before eggrelearn 2026-10-21)" = 8dafe8d1....

## THE GEN 9 ABILITIES WORK IN BATTLE — 2026-10-21 — `patches/gen9abil/`

Until now the Gen 9 abilities were stand-ins: gen9 and gen9rest gave each an id of 256 + an ability the engine has
(*Gen 9*, *The rest of Gen 9*), handed to the engine as that ability (gen9.s's alias list), plus a few rules in
gen9.s's damage and speed hooks. In battle they did what their stand-in did ("Oinkologne's Mummy!"), and most had
none. Now each has an id of its own and does what it does in Scarlet/Violet.

- **Ids.** The engine's free ids 0x101..0x12C (`gen9abil_data.ABILITIES`; the hack's own five there stay: 0x104
  Shell Armor, 0x10D Air Lock, 0x112 Burning Soul, 0x11D White Smoke, 0x125 Pure Power). Sharpness is the engine's
  own 0x4F. The patcher finds each stand-in by its name in the name table and renumbers the 67 rows of the species'
  ability table (0x097A0000) that held one; the stand-in ids stay, unused. gen9.s's alias list is emptied (its first
  pair zeroed), so the engine is handed every ability as it is; gen9.s's ability rules key on the old ids and do
  nothing now (its move rules and Booster Energy's item stay). Booster Energy (item 769) gets a hold effect of its
  own, 0xAB, which the engine has no case for: Klutz, Embargo and Magic Room stop it as they stop any item.
- **The code is C.** `build.py` compiles `g9.c calc.c hit.c moves.c entry.c state.c commander.c` and `scripts.s` with
  xPack arm-none-eabi-gcc 12.2.1 (`%LOCALAPPDATA%\xpack-arm-gcc\xpack-arm-none-eabi-gcc-12.2.1-1.2\bin`; -mthumb
  -mcpu=arm7tdmi -Os -ffunction-sections, Thumb-1 checked on the result) and links it at 0x09E33000 against the
  game's addresses: `he.ld` (RAM, scripts, tables), `he_syms.s` (routines, as `.thumb_set` so the linker calls them
  with bl and makes no ARM veneers), `he.h` (the engine's structures as this build of it lays them out). The result,
  `gen9abil.bin` and `gen9abil.sym` (its symbols, size and sha1), is what the patcher writes; a machine without the
  compiler (the Mac) patches from those two files. Gotchas: `--gc-sections` drops what nothing calls, so the
  wrappers (`.text.w_*`), callasm routines (`.text.g9_asm_*`) and strings are KEPT in `he.ld`; `-fno-strict-aliasing`
  (the weather is read as a halfword and written as a word: `gBattleWeatherWord`).
- **How it reaches the engine.** The engine already asks one routine about every ability at every point of a
  battle, `ability_battle_effects(switch_id, bank, ability, special, move)` (0x09D45F8C; 0 a Pokemon comes in, 1 the
  turn ends, 3 a move is about to hit, 4 it has hit (target), 10 (attacker), 6 after an action, 24 its own entry
  ability...). gen9abil stands in front of it and of the routines that decide a number or a rule (`WRAP` in the
  patcher, 25): the attack, defense, base power, final damage, speed, type matchup, status checks (cant_poison and
  four more), check_field_for_ability, check_ability_with_mold, has_ability_effect_inalternate, get_first_to_strike,
  change_stats, can_switch, findability_in_table, and the commands 0x07, 0x6A, 0x84, 0x8F, 0xB2 (their words in
  the command table 0x09D7717C; 0x8F and 0xB2 are the game's own). Every bl to such a routine in the code regions and
  every pointer word to it is pointed at the wrapper (found on the input, before our code is written); the wrapper
  calls the routine. Two script words: Intimidate's per-target stat change (0x09D06CA8) and Tailwind's last goto
  (0x09D05563).
- **Its state** is 0x40 bytes after the engine's own 0x118 at gNewBattleStruct (0x02024218): the allocation at
  0x09D49230 becomes 0x158 (`movs r0, #0xac`), so it is cleared at a battle's start and freed at its end
  (`g9.h: struct G9State`, 60 bytes used). A Pokemon coming in (switch_id 0) clears its battler's part.
- **Messages** are strings 0x2B7.. of the engine's table (its 315 words copied longer, the word at 0x09D4A204);
  routines scripts call by number are 220.. of its callasm table (copied longer; the word 0x09D686F0 - the same value
  also sits at 0x09D68524 as get_move_from_pledge's base, which reads the three Pledge moves just before the table:
  that one stays). Every new line measured with the font's widths: 202 px at most with two ten-letter nicknames.
- **The lists of untouchable abilities** (Skill Swap 0x09D79E36, Gastro Acid / Neutralizing Gas 0x09D79E1A, Trace /
  Role Play 0x09D79E74, Entrainment / Mummy 0x09D79E58) get the Gen 9 ones (`FORBIDDEN`): longer copies, every word
  holding a list's address pointed at its copy - and findability_in_table checks the Gen 9 ones too when it is asked
  about one of the four by its own address, because some routines (Skill Swap's ability_change at 0x09D67328) reach
  a list from a nearby address plus an offset (0x09D79E20 + 0x16), which no word holds: the first test swapped
  Protosynthesis. Sharpness's slicing moves (0x09D743F2, one literal 0x09D5F368) get the five Gen 9 ones the game
  has, found by name: Psyblade 946, Population Bomb 955, Kowtow Cleave 962, Bitter Blade 975, Aqua Cutter 979
  (Mighty Cleave and Tachyon Cutter are not in the game).
- **What each does here** (as in Scarlet/Violet unless said):
  * Entering: the Ruin four (x0.75 on everyone else's stat, the holder excepted), Orichalcum Pulse (sun as Drought,
    Heat Rock 8 turns) and Hadron Engine (Electric Terrain as Electric Surge, Terrain Extender), Supreme Overlord
    (x1.1 for each of ours that has fainted in this battle, up to x1.5, on its Attack and Sp. Atk), Costar, Hospitality (a quarter of the
    partner's HP), Supersweet Syrup (once a battle for each of the party's slots), Protosynthesis / Quark Drive
    (sun / Electric Terrain, else a Booster Energy, which is used up; on and off as the weather changes, each
    action), Commander. Orichalcum Pulse and Hadron Engine power up by x1.3 (not x4/3 Attack / Sp. Atk); the Paradox
    best stat is worked out with its stages each time.
  * Hit: Earth Eater, Well-Baked Body, Wind Rider (also Tailwind on its side, on entering under one), Wind Power and
    Electromorphosis (charged), Thermal Exchange, Seed Sower, Anger Shell, Toxic Debris, Lingering Aroma (as Mummy;
    on every contact hit, the engine has no first-hit counter), Purifying Salt (no status, Ghost damage x0.5),
    Rocky Payload, Sharpness, Good as Gold (others' status moves: Magic Coat's list without the hazards, plus 42),
    Armor Tail (priority moves at its side), Guard Dog (Intimidate ups its Attack; it cannot be forced out),
    Mycelium Might (status moves last, past abilities), Tera Shell (at full HP every hit x0.5 and "not very
    effective"; all the hits of a multi-hit move; its message before the hit), Toxic Chain (30% bad poison),
    Poison Puppeteer (its poison confuses too).
  * Later: Cud Chew (a Berry used up is eaten again at the end of the next turn: removeitem's wrapper notes it, the
    turn's end eats it with the routines Bug Bite uses, callasm 158 and 117), Opportunist (every stat a foe raises
    is counted in change_stats' wrapper and copied after the action, one stat at a time; its own copies are not
    counted).
  * Commander: Tatsugiri beside a Dondozo goes into it on entering (or when the Dondozo comes in): Dondozo's five
    stats +2 (callasm 153/154, as a multi-stat move); Tatsugiri gets the game's absent bit (gAbsentBattlerFlags),
    the one an empty spot in a double battle has, so no action is chosen for it, moves pass it over (spread) or turn
    to its partner, and the turn's end leaves it alone; its picture is hidden the way the engine hides a caught
    Pokemon (the sprite info's bit 0 at *0x020244D0, gSprites +0x3E bit 2). Dondozo cannot switch (can_switch: the
    player's menu and the AI both ask it) or be forced out (forcerandomswitch fails). Tatsugiri comes out after the
    action in which its Dondozo fainted (switch_id 6; not at once, or the rest of a spread move that knocked Dondozo
    out would hit it) or when another Pokemon takes Dondozo's place (U-turn, Eject Button).
  * No effect: Zero to Hero (the game has no Hero Form: Palafin stays as it is), Mind's Eye, Embody Aspect, Tera
    Shift, Teraform Zero (no Pokemon here has them; names and texts only).
- **Gotchas.** gSpecialStatuses is 0x14 bytes a battler in this engine (not vanilla's 0x1C): Toxic Chain never fired
  until that was right. A move's "confusion self-hit" is gProtectStructs[b][1] bit 0, its "not first to strike"
  [2] bit 3. A callasm routine runs with gBattlescriptCurrInstr already past its 3 bytes (a word after it is read
  there). switch_id 6 is asked again after each one that did something (HandleFaintedMonActions' state does not
  move on), so a poll there does one battler a call.
- **Space.** 0x09E33000..0x09E3C000 (36 KB; 0x09E33000..0x09E36652 used, 13.9 KB), in the zero run
  0x09E10044..0x09E40000 of the game before Kitakami, 16 KB below Kitakami's 0x09E40000 (to 0x09F00000 before it).
  All zero, and no word at a 4-byte boundary anywhere in the ROM holds an address in it (checked by the patcher);
  19 words at other offsets do (0x0851034B, 0x09204202 ...: inside pictures and code, none a literal or a table
  entry). The run's lower part has chance values in pictures pointing in, which is why 0x09E20000 was given up.
  Read watchpoints on the game without it (`_testrun/space/gen9abil_watch.ps1`, rom/ 767e052c...: the menus, Prelude
  Beach with R / SELECT / START / L, Surf and wild battles (again alone, `gen9abil_watch_surf.ps1`: the first try
  timed out while other tests ran), the researcher / News Tracker / battles / three saves and resets, Petalburg
  Woods and Continue, four walks): 0 reads in all nine, the two controls read in each.
- **Tested** (`test_gen9abil.lua`, `_testrun/gen9abil/batch1..7.ps1`: a battle each, hidden and muted, the battle's
  messages logged, damage against a control with another ability; doubles against trainer 56, Gabby & Ty):
  * 1: Sword of Ruin (Tackle 62 vs 47), Koraidon's sun, Miraidon's terrain, Booster Energy, Protosynthesis on with
    Sunny Day and off when it fades (turn 5), Quark Drive from Electric Terrain.
  * 2: Earth Eater, Well-Baked Body, Wind Rider, Thermal Exchange, Seed Sower, Anger Shell (five stats),
    Electromorphosis, Wind Power, Toxic Debris (twice), Lingering Aroma, Toxic Chain, Poison Puppeteer, Purifying
    Salt against Toxic, Yawn, Thunder Wave and Will-O-Wisp.
  * 3: Good as Gold against Thunder Wave (stopped), Spikes and Perish Song (not), its own Nasty Plot; Armor Tail
    against Quick Attack (and without it); Mycelium Might past Insomnia, last; Guard Dog against Intimidate and Roar.
  * 4: Supersweet Syrup (one foe and two), Tailwind with Wind Rider and Wind Power (its own, then the partner's,
    then on entering under one), Hospitality (+29 = 119/4), Costar.
  * 5: Cud Chew (Sitrus +56 twice, Oran +10 twice), Opportunist (Swords Dance copied each turn; Sturdy does not),
    Tera Shell (Brick Break 13 vs 54 at full HP, 54 below it; Double Kick 6 + 6; Mold Breaker 54), Rocky Payload
    (Rock Slide 110 vs 73), Purifying Salt against Shadow Ball (13 vs 26).
  * 6 and 8: Commander, Tatsugiri first and Dondozo first (+2 five times); Hyper Voice passes over Tatsugiri;
    Dondozo knocked out (five seeds, a spread move in three): Tatsugiri out after that action, hit and acting from
    then on.
  * 7 and 8: Skill Swap fails at Protosynthesis and Commander, swaps Sturdy; Trace passes Quark Drive by, takes
    Sturdy; Sharpness (Aqua Cutter 60 vs 40); Supreme Overlord with two fainted (`FAINTED=2`; Tackle 56 vs 49).
  * Batches 1-6 again after batch 7 (the same messages); batch 8 and Lingering Aroma after the last two changes
    (the list wrapper, Tatsugiri out after the action).
  * Not tested: Roar at a Dondozo with its commander (the test cannot pick a target in a double battle), the switch
    menu's refusal for that Dondozo (can_switch is what the menu asks), Cud Chew after Bug Bite or Fling (not
    noted: only removeitem is), two Opportunists.
- **Differences from Scarlet/Violet**, known: Orichalcum Pulse and Hadron Engine as x1.3 power; Opportunist copies
  after the action, not at once; Lingering Aroma on every contact hit; a Dondozo that leaves by U-turn, Eject Button
  or Red Card lets Tatsugiri out (only switching and Roar-type moves are refused); Zero to Hero does nothing.
- Working ROM = `rom/` = "(my placements 36)" = **3c9f52c1...**; `roms/before-kitakami` = **3d32f3cf...**
  (c2c97e5e... + this patch); archive "(before gen9abil 2026-10-21)" = 767e052c.... The whole chain from the v1.4
  archive gives 3c9f52c1... byte for byte (135 s; the main game alone still 265a0e93...).

## THE GEN 9 MOVES' OWN ANIMATIONS — 2026-10-22 — `patches/gen9anim/`

Until now each Gen 9 move played the animation of the older move gen9 or gen9rest made it from (Kowtow Cleave Night
Slash's, Make It Rain Pay Day's...). Each of the 48 (938-985) now plays its own: 43 scripts (the four Ivy Cudgels
share one, the three Raging Bulls one).

- **The scripts** (`anims.s`) are in the game's battle animation language, its own commands 0x00..0x2F (`defs.inc`:
  the macros, and the address of everything the scripts name). They use the game's own sprite templates, tasks,
  particles, backgrounds and scripts: every sprite template of the game's they launch has its tags and pointers
  where the game keeps them (the patcher checks); the vanilla scripts they call or go to (Jump Kick 0x082D216E, Spit Up 0x082D49EB, the
  scrolling background's end 0x082D7CDD) are the ones the game's own animation table points at; the particles they
  load (0x2797, 0x2861, 0x2862...) are all in the engine's particle table (0x09D33568, 367 entries to 0x287E) and
  the backgrounds in its background table. 91 labels: the scripts, their subroutines, the sprite templates of
  their own (built from the game's oam, frames and callbacks).
- **Built** by `build.py` (xPack arm-none-eabi-as; `ARMGCC=<its bin>` elsewhere) into `gen9anim.bin` and
  `gen9anim.sym` at 0x09E38000; the patcher only reads those two. It points the animation table's words for the
  48 moves (0x09D0AB00 + 4 x id, the table read through the literal 0x080A3A44) at the scripts, each move found by
  its name among ids 938-985 (Petal Blizzard is also the engine's own 572). It checks before writing: every task
  is a Thumb address in the game's or the engine's code, every template has its tags and pointers in the ROM, every
  script called is one the table points at or starts with a command, and every routine of the engine's a template
  of ours calls is also named by one of the game's own (below).
- **The one that froze.** Make It Rain's coins are the engine's Happy Hour coins, whose callback is an engine
  routine: the first build named it from an address list that was wrong (0x09D450A4 is the routine after it) and
  the battle stopped with a coin in the air. The game's own Happy Hour coin template (0x09D2A460) names 0x09D4520D:
  that routine reads the animation's argument 5 as the coins expect. Hence the patcher's last check.
- **Space.** 0x09E38000..0x09E3C000 (11,472 bytes used), the upper part of the stretch *The Gen 9 abilities work
  in battle* proved (all zero, no aligned word points in, never read in nine watched runs); gen9abil keeps
  0x09E33000..0x09E38000 (its claim made smaller, its output the same), Kitakami starts at 0x09E40000.
- **Tested** (`_testrun/gen9abil/batch9.ps1`: 17 battles, our Pokemon against a Lv 100 Snorlax that only
  Splashes, four moves a battle; doubles against trainer 56): every one of the 48 ids used, a picture every 8
  frames while one of ours plays (`SHOTANIM`: the word at 0x020383F0 holds the start of the animation playing),
  and every frame in which the scene changed looked at (`sheet2.py`): all 43 play to their end and give the screen
  back as it was, in singles and in doubles (Make It Rain, Mortal Spin, Petal Blizzard on both foes; Dragon Cheer
  on the partner). Last Respects and Rage Fist against a Raichu (they do not touch a Normal type), Comeuppance
  after a Tackle, Electro Shot's charge and hit, Silk Trap's web.
- **Seen on the way, not changed** (the moves' effects, gen9rest's templates): Make It Rain lowers Sp. Atk once for
  each foe it hits; Salt Cure's message is Bind's ("was squeezed by ... Bind"); Double Shock hurts its user
  instead of losing its Electric type; Gigaton Hammer makes its user recharge.
- Working ROM = `rom/` = "(my placements 37)" = **84a2d8d7...**; `roms/before-kitakami` = **5da2d7f6...**; archive
  "(before gen9anim 2026-10-22)" = 3c9f52c1.... The whole chain from the v1.4 archive gives 84a2d8d7... byte for byte (100 s).

## VERSION 2.0 AND ITS SHOWCASE — 2026-10-22 — `patches/qolversion/`, `_testrun/showcase20/`

- Asked: "update version in rom to 2.0". `qolversion_patch.py`: `QOL = "2.0"` (a number only: no release, the site
  and `release/` still say 1.9). All digits of the font are 6 px wide, so "+QoL2.0" takes the room "+QoL1.9" took;
  the Option screen, seen in mGBA on build 38 from the user's save: "Ultra Emerald V5.7 +QoL2.0 (Standard)", inside
  its bar. The step is mid-chain: the whole chain rebuilt (8 bytes differ from 84a2d8d7..., the two digits of each of
  the four titles at 0x08FF24DE..0x08FF2569), the Gen 9 base (`roms/test-gen9`, archived first as "(the base before
  2.0, 2026-10-22)") replaced with the chain's `gen9` stage, then `paldea/rebuild.py`: "(my placements 38)" =
  **10203d90...**, equal to the chain's result.
- Asked: "make a gif for showcase 3*3", then "remove" the three battle cells (Drake's Roaring Moon, Koraidon's
  Orichalcum Pulse, Gholdengo's Make It Rain), "add more kitakami whole town" and "also focus on new sprites".
  `docs/showcase/showcase-v2.0.gif` (and `gba-trans/hyper-emerald/showcase/gifs/v2.0.gif`): 1464 x 1084, 62 frames of
  160 ms (the last 1.5 s), 13.3 MB - the 1.9 one's size, layout and timing (`_testrun/showcase19/montage.py`;
  `_testrun/showcase20/montage.py`). Nine clips filmed on build 38 from a copy of the user's save through Area Zero's
  harness (`_testrun/paldea/run.ps1 -Steps ../../../_testrun/showcase20/steps*.lua`), a picture every 6 game frames,
  the story's flags set as the Kitakami and Area Zero tests set them:
  * Kitakami: Mossui Town walked from the bus stop through the market, past the Pokemon Center and up the maples to
    Loyalty Plaza (Part 1's flags, so Carmine lets you by); Carmine stopping you at the bus stop, her talk and her
    battle picture; Kieran at the market on Part 2's night (the game's own day/night on: `daynight_off` would take
    the festival's night tint away); Kitakami Hall's Mask Hall, a plaque read; Ogerpon at the plaza and her battle's
    start; Briar by the hole in Mossdeep, her intro;
  * Area Zero's people in their own sprites: Nemona in the future crater (stage 2), her talk and battle picture;
    Arven and Penny dancing in Mossui's market (Part 2), Arven's talk; AI Sada and AI Turo appearing at the Zero Lab's
    machine (every flag before the finale set), their talk.
  Every frame of the GIF looked at (two contact sheets): each clip runs through; the only dark frames are three
  battle starts' transitions. Not used: Nemona and Pecharunt at the plaza (Part 2; talked to from the tile the Part 2
  test uses, nothing started), the Pokédex stats and Relearner clips (`frames/`, kept). The README still shows 1.9's
  GIF: swap it at the release.

## THE HISUI MAP FLIES AGAIN, AFTER VOLO — 2026-10-22 — `patches/hisuifly/`

- Asked: "we have implemented flying in hisui, but we have removed it before since it skip the events in Hisui,
  however, can we add it back but make sure it check if we already completed Hisui quest at finding Volo but before
  skitty Cat". The no-fly change of 2026-10-08 is *Hisui map: no flying* above.
- No code: hisuimap's fly table already gives each place a flag that must be set ({key u8, pad, flag u16, block
  u32}; `fly_target` answers 0 while it is clear, `draw_name` greys the name), the way Sinnoh's couriers work.
  `hisuifly_patch.py` puts the five places back (the first key, 0xFF -> 107) with flag **0x431E** on each: 11 bytes
  at 0x08FF544C..0x08FF546F. It asserts the no-fly table as hisuimap leaves it, that REGION_HISUI's fly word
  (0x08FF54D8) is the only word pointing at it, and the first 12 bytes of each of Mingyao's five blocks.
- Why 0x431E, read from the ROM (`tools/romdata/scripts.py flag`, `dis.py`): Volo's script (37/108, 0x098A15DE)
  sets 0x4315 when he is beaten and warps you to Coronet Highlands. 0x431E is the trigger at base camp (37/104, 12,19,
  0x098C5DCC): Rei and Cogita's news, the Journal's "Volo is beaten. Return to base camp" step. Mingyao's own menu
  (multichoice 137): at Coronet Highlands (0x0989B177) only once 0x431E is set - between 0x4315 and 0x431E she says
  "to think you defeated Volo" and flies you straight to base camp; at base camp (0x0989A9FC) only once 0x431E is
  set ("Oh! Looks like everyone's here!" before); at Deertrack Heights (0x0989ADB7), Firespit Island (0x0989AAEC)
  and the Alabaster Icelands (0x0989B390) once 0x4315 is. So from 0x431E on every Mingyao offers all five places
  and the map offers nothing she does not. The steps after it (Cogita and the three legends 0x4319, Kitty's Dried
  Fish 0x4322, the summit 0x4323, Cogita on Champion Island 0x4325) are free roaming; the summit guard (37/106,
  0x098B201D) checks its own flags and item whatever way you arrive.
- Chain step after `gen9anim`, before `kitakami` (`paldea/rebuild.py`'s TAIL and the three `rebuild_chain.py`).
  "(my placements 39)" = **f5ce12ce...**, 11 bytes from build 38 (10203d90...); the whole chain from the v1.4
  archive gives it byte for byte (96 s).
- Tested (`test_hisuifly.lua`, run by `_testrun/hisuifly2/run.ps1` with the build 38 save; build 38 as the control),
  every screenshot looked at: 0x431E clear (cleared by a script), Coronet Highlands, the map: the names greyed, A on
  Firespit Island does nothing, the map stays up, B back on 37/106. 0x431E set: names white; A on Firespit Island:
  Mingyao's Braviary, A, on 37/105 (21,42); from there A on Prelude Beach: on 37/104 (12,18), her warp 1, at base
  camp. Sinnoh: Oreburgh -> A on Jubilife flies to 36/2. The control never flies from the Hisui map.
- The guide site still says the Hisui map does not fly (`site/src/data/features.ts`, `guides/mechanics.mdx`): change
  it at the release with the rest.

## EVS FROM BATTLES STOPPED AT 509 — 2026-10-22 — `patches/evgain/`

- Reported: "Total EV sometimes stuck at 509 when I ev train my pokemon".
- Where: the battle engine's EV gain, **0x09D5A880** (mon, species), called by getexp (0x09D5AAE8, at 0x09D5AC4E) for
  every Pokemon that gets experience, the Exp. Share's included. Found by a write watch on the party Pokemon's six EV
  bytes (+0x38..+0x3D) in a battle: the store is SetMonData's (0x0806B0B0/B6; the lr there, 0x08068CAF, is stale -
  the checksum routine's), the return addresses on the stack give 0x09D5A9B5 (in the routine) and 0x09D5AC53
  (getexp). The writes at 0x0806A23C..0x0806A266 are the (en|de)crypt loops rewriting the words, not EV changes.
- The routine: total = the six EVs; a Pokerus flag; held item and hold effect - 24 is Macho Brace's and every Power
  item's, and 0x09D6AB0C(item) tells them apart (0 = Macho Brace: yields x2; else the Power item's stat + 1: +8 to
  that stat, once); if total > 510 at a stat's turn every EV is set to 0 (only a save with an impossible total can
  get there). Then per stat, HP, Atk, Def, Spe, SpA, SpD: the yield (base stats +10, 2 bits each) with the item and
  Pokerus (x2), and a loop one point at a time - `if (total == 510) return; ev = GetMonData(0x1A + i); if (ev <= 251)
  SetMonData(ev + 1); total++` until total = start + gain. **The bug:** `total++` ran when the stat was full (252) and
  nothing was added, so every point due to a full stat ate room the Pokemon never used, and at 510 "reached" the
  routine returned before the stats after it. With 509 real and Attack full, a Power Bracer (+8 Attack) or any foe
  giving Attack ended it before the foe's Defense point: 509 after every battle while that item or that foe stayed.
  Below 509 points were lost the same way (Atk 248 of 500 + 8: 4 added, 4 counted).
- Fix, one byte: 0x09D5A9A2 `bhi 0x09D5A9B4` (to `total++`) -> `bhi 0x09D5A9C0` (the loop's next stat), 0x07 -> 0x0D:
  a full stat now ends that stat's share and the count stays the real total. The patcher asserts the loop's bytes,
  the next-stat step and the `adds r4, #1`. The original hack's ROM has the same bytes: its bug.
- Chain step after `hisuifly`, before `kitakami`. "(my placements 40)" = **ebeae0f5...**, 1 byte from build 39; the whole chain
  from the v1.4 archive gives it byte for byte (98 s).
- Tested (`test_evgain.lua` - test_gen9abil.lua's battle with EVS / EVS2 / POKERUS and the watch - by
  `_testrun/evgain/evrun.ps1`; Mewtwo Lv 50, Tackle, a Lv 5 foe at 1% HP), build 39 as the control, 12 cases:
  Power Bracer, Attack full, 509 + Geodude (1 Def): 509 -> 509 before, 510 after; no item, 509 + Parasect (2 Atk,
  1 Def): 509 before, 510 after; the Exp. Share's share (a second Pokemon at 509 with a Power Bracer): 509 before, 510
  after. The same on both: Power Bracer Atk 248 of 500 -> 505 (Atk 252, Def 1); Parasect on 0/251/252/5 -> 509 (both
  stats full: right); Power Belt 504 -> 510; Graveler 509 -> 510; Golem 508 -> 510; Pokerus 508 -> 510; Macho Brace +
  Graveler 505 -> 509 (2 x 2 = 4: right); 0 + Parasect -> 2/1; 510 stays 510.
- The EV items, checked after (`test_evitems.lua` by `_testrun/evitems/run.ps1`; build 43, the user's save; used from
  the Bag, every message looked at; the game's PokemonItemEffects 0x0806BD28, not this routine). The hack has no
  Wings. Vitamins: 509 + Carbos -> 510 (one point); 510 + Carbos -> "It won't have any effect.", the item kept; Attack
  full at 509 + Protein -> no effect; 505 + Zinc -> 510; SpA 95 + Calcium -> 100 (vitamins stop at 100, as in
  Emerald). Berries (the pocket sorts itself when opened, and Check Tag is the menu's first line): Pomeg on HP 252 ->
  242, then a Carbos +10 -> 510; Hondew on SpA 0 -> no effect. Nothing sticks at 509.
- Found there, the original hack's: its own CalculateMonStats (0x09F038D8, behind the trampoline at 0x08068D0C; the
  original ROM's bytes but for mintquirky's bl at 0x09F03930) sets HP to HP + (new max - old max) and anything above
  the new max - a negative result wraps - to the new max. Emerald leaves a fainted Pokemon at 0. So HP Up on a fainted
  Pokemon revives it (0/293 -> 2/295), and a Pomeg Berry gives full HP to a fainted one (0/338 -> 335/335) or one at
  1 HP (1/340 -> 338/338). Fixed the same day: *A fainted Pokemon stays fainted* (`patches/hpcalc/`).

## CHEREN'S MINT LIST: QUIRKY, INSIDE THE SCREEN — 2026-10-22 — `patches/mintquirky/`

- Reported: "The Mint table that Cheren uses to change natures is missing the 'Quirky' nature ... there's a space
  with the word 'None' that reverses the action of the Mint ... the table box extends beyond the game screen limit
  ... so maybe use replace 'None' with 'Quirky'". The user chose that (the 5x5 grid, Quirky in None's place, no
  undo, names cut to fit) over a two-step menu and a 3 x 9 list.
- The offer (0x0984A658; both Mint people, 11/4 and 37/77, run 0x0984AB8D): `multichoicegrid 0, 0, 0x7C, 5 columns,
  B ignored` (op 0x71) -> VAR_0x8005 -> ChoosePartyMon -> callasm 0x08FF0E01, which writes the slot to mon + 0x1F
  (bits 0-6) and recalculates the stats. The list (0x0984A9B8, entries {text, unused word}; the multichoice table
  is the hack's at 0x09700000, 143 entries, 296 zero bytes after it) was None, Lonely .. Careful, Hardy: slot =
  nature for 1-23, 0 = no Mint, 24 = "Hardy" (naturefix shows 24 as Hardy). Quirky had no value.
- Who reads the byte (every `ldrb rX, [rY, #0x1f]` with a 7-bit mask after it, in the whole ROM: three in code, the
  rest chance bytes in pictures): naturefix's GetNature stub (0x08F54200, reached by GetNature's word 0x0806D074) for
  what is shown (summary, Synchronize ...), and two places in the hack's stats code - its nature getter (0x09F038BC)
  and CalculateMonStats (0x09F03928) - that take the byte as the nature's number (24 = Quirky there: stats and
  display have disagreed since the start, harmlessly, both neutral). 0x09D4A636 is another structure.
- The grid's width (vanilla ScriptMenu_MultichoiceGrid): each column (widest name + 9) / 8 + 1 tiles. "Adamnt" is
  36 px (field font, 0x086542E4) -> 6 tiles, 5 x 6 + the frame = 32 on a 30-tile screen: its right edge was off it.
  Full names need 7 (Adamant, Naughty 42 px); 5-tile columns (27 tiles with the frame) need every name <= 30 px. The
  grid is shared by seven menus (lists 0x76, 0x77, 0x7C, 0x7F, 0x83, 0x8A, vanilla's 0x0D), so its drawing was left
  alone.
- mintquirky (code and texts 0x09E3C000..0x09E3C10C):
  * the 25 entries' texts: Hardy, Lonly, Brave, Adamt, Nauty / Bold, Docil, Relax, Impsh, Lax / Timid, Hasty,
    Serio, Jolly, Naive / Modst, Mild, Quiet, Bashf, Rash / Calm, Gentl, Sassy, Caref, Quirk (slot = nature; the
    patcher measures each <= 30 px);
  * the callasm -> mint_apply: slot 0 (Hardy) -> 24, slot 24 (Quirky) -> 25, then 0x08FF0E00;
  * 25 reaches the stats as 24: `bl mint_r0` at 0x09F038C4 and `bl mint_r3` at 0x09F03930 (each in place of the
    two shifts that masked the byte); GetNature's word -> get_nature: 24 Hardy, 25 Quirky, 0 the personality's
    (naturefix's stub stays, unused). Saves with 24 keep showing Hardy. No undo: the Pokemon's own nature gives the
    same stats (the summary then names it, as the Mint's).
- Space: 0x09E3C000..0x09E3C200 kept, within 4 MB of the stats code (its bl's). Blank since the original hack (its
  zero run 0x09E10044..0x09F00000), blank today from gen9anim's end (0x09E3ACD0) to kitakami (0x09E40000); no word
  in the ROM reads as an address in 0x09E3C000..0x09E3C400 (15 chance words point elsewhere in the gap, none a code
  literal: speciesx_patch.is_pointer); a read watch on build 40 (`_testrun/space/mintquirky_watch.ps1`: menus, Hisui
  with R/SELECT/START/L, Surf and wild battles, the researcher and three saves and resets, Petalburg Woods' Continue,
  four walks): 0 reads, while the two control stretches were read (base stats up to 25,362 times, DMA 2 million).
- Tested (`test_mintquirky.lua`, `_testrun/mint/run.ps1`, build 40's save; build 40 as the control): the grid
  inside the screen with its right edge, the cursor on Adamt and Quirk; Blaziken (own nature Calm) given each Mint:
  Hardy byte 24, stats 296/279 (Atk/SpA, neutral); Quirky byte 25, the same stats; Lonely Atk 325 Def 172; Adamant
  Atk 325 SpA 251; Modest SpA 306 Atk 266; Careful SpD 202 SpA 251. The summary (one boot per slot: the Start menu
  keeps its cursor): Hardy, Quirky, Lonely ↑Atk ↓Def, Modest ↑Sp.A ↓Atk, Careful ↑Sp.D ↓Sp.A. Control: slot 0
  "None" byte 0 (Calm again), slot 24 "Hardy" byte 24, the grid past the edge. "(my placements 41)" = **8cccc1f9...**;
  the whole chain from the v1.4 archive gives it byte for byte (109 s).

## TWO REPORTS THAT NEEDED NO CHANGE — 2026-10-22

- "Between Jubilife and Route 204, there's an extra graphic text box appearing on the screen." Filmed on build 40
  (`_testrun/jubilife/steps*.lua` through Area Zero's harness, a picture every 3 frames, every frame looked at):
  Jubilife's north exit (36/2) to Route 204 (36/19, connection N +34) by both lanes, both ways, day and the game's
  own clock: the only boxes are the two location signs, and twice in eight crossings a PokeNav call (the Match Call
  window: the PokeNav icon, "......" and the arrow). The call is the game's own, random: it can start on the 10th
  step after a map loads, and from Jubilife's warp that step falls on Route 204. Nothing else came up; the player's
  screenshot was asked for.
- "Can shiny charm apply to breeding? ... the Charm adds 2 extra rolls". It already does. The hack makes an egg's
  personality when you take it, not when the Day Care decides there is one: InheritIVs (0x08070260) jumps to the
  hack's 0x09F00B08, which ends in 0x09F008F0: the Everstone nature (0x09F00830), then CheckBagHasItem(119) -> 5
  rerolls, else 1, into the same generator wild Pokemon use (0x09F0071C: random personalities that keep the nature
  (and a gender when asked); while rerolls are left it returns the first shiny one; the try after the last reroll is
  kept as it is). So an egg gets 6 tries with the charm and 2 without: about 1 in 1,365 against 1 in 4,096 - the x3
  the user chose. The Day Care's own roll (daycare + 0x118, vanilla _TriggerPendingDaycareEgg) is overwritten.
  Measured on build 40 (`_testrun/eggcharm/test_eggcharm.lua`, GIVE=1: _GiveEggFromDaycare 4,000 times each way, on a
  test copy whose shiny check is 1 in 256): no charm 30 shiny (0.75%; 2 tries: 0.78%), charm 100 (2.50%; 6 tries:
  2.32%). An eggcharm patch (three rolls of the Day Care's personality) was written first and dropped: that roll
  is thrown away.

## RAINBOW CASTLE: THE FENCE — 2026-10-22 — `patches/castlefence/`

- Reported: "during the rainbow rocket castle mission, there are two kirlia to warp u back town, on the second inner
  kirlia, if u have not completed the castle mission and warp back, the fence is locked as softlock ... you'll get
  stuck and won't be able to go back in to fight Rainbow Rocket!!", with a screenshot: the player between a railing
  and the exit mat.
- The castle, read from the ROM (`tools/romdata/scripts.py`, `dis.py`, the maps' warps): EV Training Cave (35/49):
  Colress (object 25, hidden by 0x41E1) wants the 18 Z-Crystals, says "Once you enter, you won't be able to leave the
  castle until the end", opens the hidden door ((18..20, 21)) and sets 0x41E9, 0x41E1; the cave's on-load script walls
  the door while 0x41E9 is clear. -> the entrance hall 35/3 (its exit covered while 0x41D5, the castle beaten, is
  clear; the outer Kirlia at (5,15) teleports to Pacifidlog 0/15 once 0x41EA is set) -> the first floor 34/82 -> the
  hub 34/83 (six locks 0x41EB..0x41F0 open its door, 0x41F1, kept on reload) and its rooms 34/84..34/89 (34/89's doors
  by 0x41F5..0x41FA, kept) -> 35/4 -> 35/5 (the inner Kirlia at (6,6): "Maybe you just want to be an ordinary Trainer
  ..." and Yes teleports to Pacifidlog, no check) -> Temple of the End 34/93.
- 34/82: the triggers at (12..14, 18) (var 0x400A, once: 0x41EA) are Pawn's trap: you are moved north, a fence is
  raised on row 15 (setmetatile x 5, 6, 12, 13, 14, 20, 21: 0x297 / 0x269, impassable), Steven and Gladion stay south,
  Pawn's battle (trainer 1070), 0x41EA. Its on-load script (0x09866A65, the only map script; table entry 0x08A399D5)
  raises the fence again whenever 0x41D5 is clear and 0x41EA set. Back from Pacifidlog you come in by 35/3, whose
  warp puts you at (13,19), south of it: the railing above, the exit below. The only ways on were the outer Kirlia
  (out again) and the Blue-Haired Passerby (35/49 object 16, while 0x41E9 is set and 0x41D5 clear): 500,000 "to send
  you back to the recent past", which clears 0x41E1, 0x41E9..0x41FA, 0x41FD and the castle's trainers (1071..1115) -
  the whole castle again. The other gates only open with progress and stay open, so they do not shut anyone out.
- castlefence: a new on-load script (0x09E3C200..0x09E3C227; the table entry repointed): as before, but after the
  two flag checks `getplayerxy 0x400E, 0x400F; compare 0x400F, 15; goto_if > end` - the fence only when you are north
  of row 15 (as everyone is after the trap, and on reload from the hub). Temp vars: 34/82's triggers use 0x400A only.
  40 bytes differ from build 41.
- Tested (Area Zero's harness, build 41 as the control; `_testrun/castle/steps_*.lua`; the floor's four trainers
  1071-1074 marked beaten so they do not stop the walk): back in mid-castle (0x41E9, 0x41E1, 0x41EA set, 0x41D5 clear)
  at (13,19): build 41 the railing closed and the walk STUCK; the fix a gap in it and the walk up to the hub's door
  (13,2). The trap from the start (0x41EA clear): the same on both - Pawn's speech, his battle (Houndoom Lv 85 ...),
  you at (13,14), Steven and Gladion at (12,19) / (14,19); 34/82 loaded again from the north (13,2): the fence up and
  the way back south (13,18) shut on both. The reporter's case: a save made stuck at (13,19) on build 41, Continued on
  the fix: free, up to (13,2); on build 41: still stuck. "(my placements 42)" = **c5a095b0...**; the whole chain from the v1.4 archive gives it byte for byte.
- The script space: mintquirky's proof covers it (blank since the original hack, no word reads as an address in
  0x09E3C000..0x09E3C400, 0 reads in the read watch).
- The round trip, tested after (`_testrun/castle/steps_loop.lua`, build 43, mid-castle with the hub's locks done): the
  inner Kirlia to Pacifidlog, then on foot through the warps: the cave's wormhole (0x41D4 + the Ultra Suit) and door,
  the entrance hall (its wild Pokemon, object 1 with no flag, removed by the test), 34/82 through the fence's gap at
  (13,16), the hub, 35/4, 35/5 and the inner Kirlia again. Pawn's triggers and the hub door's only release once their
  flags are set (they stop a walk, nothing more).

## BERRIES, READ FROM THE GAME - 2026-10-22 - `tools/build_berries.py`, `/wiki/berries/`
- Asked: "what about every berry location? or seller berry? objective is for every berry existing, we should at
  least know one place where to get it". The page reads v1.9 (`_testrun/site19/hyper19.gba`, 65b5a7f6).
- The berries are the items in pocket 4: 133-175 (Emerald's 43), 704-727 (the hack's 24, numbered No44-67 by
  patches/berrynum) and 762-765, which repeat the names Mago, Wiki, Aguav and Tanga Berry: no script, shop, trainer
  or wild Pokemon has those four, so the page leaves them out.
- Trees: 120 objects run the berry tree script 0x082742F9 (graphics 60); the tree id is the template's +14. A New
  Game runs one script of 80 `setberrytree` commands (opcode 0x8A: id, berry, stage; at 0x0827149D, called from
  0x082717BC; ScrCmd at 0x0809B71C calls PlantBerryTree 0x080E191C), all stage 5 (ripe). Checked in mGBA: a New
  Game from no save (`_testrun/berries/run_newgame.ps1`), then all 128 slots of SaveBlock1 +0x169C hold exactly that.
  No map script plants a tree. Ids are shared between a Sinnoh tree and a Hoenn one (Route 205 = Route 102 ...):
  one slot, one plot. The Route 130 Liechi tree is on Mirage Island (temp flag 0x11, which Route 130's map script
  sets on the days the island is away); Route 212 has a Liechi tree with the same id and flag, which nothing on
  Route 212 sets, so it is always there.
- ItemIdToBerryType (0x080E19E8): item - 133 > 42 gives berry 1. Planting Occa ... Maranga grows Cheri Berries.
- Daily gifts: `random N` + addvar(s) + giveitem VAR_RESULT, guarded by a flag in 0x920-0x95F, which
  ClearDailyFlags (0x0809D3A0: memset SaveBlock1 + 0x1394, 8 bytes) clears. The Berry Master: Pomeg-Nomel and Occa-Roseli
  (two addvars: 20 + 133, then 571 + 133); Kiri in Sootopolis: Pomeg-Nomel and Sitrus-Iapapa; Lilycove's man:
  Liechi-Apicot; Route 114: Razz-Pinap; Route 111 and the wife: Cheri-Sitrus; the Pretty Petal girl: Figy-Iapapa.
- The wife's sayings: the routine 0x0811BF40 compares your two Easy Chat words with the table 0x0859776C (five
  pairs) and returns 1-5 (0 otherwise) in VAR_0x8004; her script turns 1-5 into Spelon, Pamtre, Watmel, Durin, Belue
  (once each, flags 0xF8-0xFC) and anything else into one of Cheri-Sitrus. Easy Chat words: group << 9 | index into
  the group's records at 0x0859D004 ({records, u16, u16}; a record {text, order, enabled}); groups 0 and 21 are
  species (0x197 = Latias, 0x198 = Latios). The pairs: GREAT BATTLE, CHALLENGE CONTEST, OVERWHELMING Latias, COOL
  Latios, SUPER HUSTLE.
- The Contest Lobby / Contest Hall girl (one script, Lilycove and Hearthome): a Pecha Berry if your Berries pocket is
  empty (special 0x34 = pocket 4 not empty), you have the Pokeblock Case (item 0x111) and a free slot in it (special
  0xA3), once a day (0x921). Lilycove's lobby shows her only on some visits (its map script sets/clears 0x369).
- Dad's Enigma Berry (Petalburg Gym) checks special 0x35 (0x080E162C: the save's e-Reader Berry data and its
  checksum): with no e-Reader data it is never given. The Floaroma shop sells Enigma.
- Shops: the Pretty Petal Flower Shop in Floaroma Town (37/10, named by the sign by its door, 36/4 at 17,34) sells
  all 67, with no condition; Route 104's sells Leppa and Pomeg-Tamato. item_sources.PLACES names 37/10, 37/22
  (a Solaceon house) and 37/100 (Hearthome's Contest Hall).

## AREA ZERO'S PEOPLE, AFTER THE REFERENCES — 2026-10-22 — `patches/azpeople/`

- The user sent phone screenshots of Pokemon Essentials art of Paldea's people ("I found these accurate reference
  for sprites of Paldea npcs"): battle pictures (160 x 160, art at 2x) of Nemona, Arven, Penny, Jacq, Sada, Turo and
  AI Sada + AI Turo together, and walking sheets (256 x 256, 4 x 4 cells of 32 x 32 at 2x: rows down, left, right,
  up) of Nemona, Turo and Sada; no file of them anywhere on this PC. Asked whether to use them or
  redraw: "redraw I guess cuz I don't have files"; for the walkers' size (32 x 32 like the references, or the game's
  16 x 32): "u decide" - 32 x 32. Who drew the references is not known: a public release should credit them if found.
- Recovering the art (`_testrun/paldea/people/refs/extract.py`): the viewer enlarged it by a fraction (13.49 screen
  pixels an art pixel for the battle pictures, 8.44 for the sheets) and the JPEG blurred the edges, so the pixel size
  and grid offset are found from where the colour changes (a comb over the gradient profile; the sheets need the
  range 6-11, else it locks on twice the size) and each cell's middle is read. The viewer's grey background
  (136,136,136) is made see-through only where the picture's edge reaches it without crossing an outline: Turo's grey
  hair is that grey (first pass: holes in his hair).
- Making the new pictures (`_testrun/paldea/people/redraw`):
  * redraw.py: the walkers of Nemona, Sada (AI Sada) and Turo (AI Turo) taken from the sheets as they are, the 16
    cells mapped to the game's nine frames (down, up, left standing; then down, up, left walking, two each; right is
    left turned over); walking frames lift the head one row. The battle pictures brought to 64 x 64 (references 69-79
    rows): each new pixel takes the colour covering most of it, an outline at a third of it wins; set on the bottom
    row, centred. Colours: JPEG noise merged, then k-means in Lab to 15 (in RGB it put Turo's grey hair with the coat's
    purple; seeded with the darkest colour).
  * draw3.py / draw3b.py: Jacq and Arven drawn over Turo's walker (Jacq wears Turo's lab coat), Penny over Nemona's:
    a colour rule per base pixel (head and body apart) and drawn rows per facing - Jacq's lavender sweep and glasses,
    Arven's bangs and yellow backpack (front, back, side), Penny's red bob rimmed in blue, glasses, hoodie emblem and
    the Eevee bag; Penny's head is drawn whole over Nemona's (her ponytail cleared).
  * finalize.py: the people who share a palette in the game cut together (Mossdeep's ending shows Arven, Penny, Nemona
    and Jacq with the town's people and the hole: six palettes at most) - B = Nemona + Jacq by k-means; A = Arven +
    Penny by 15 colours chosen by hand (k-means gave Arven's skin a brown); AI Sada, AI Turo, and each battle picture
    on its own. GBA-rounded colours.
- The patch (after castlefence, before kitakami): it checks the six entries, frames, palettes and pictures are the
  cast's (patches/paldea/cast.py), then
  * entries 174-178, 180 of the hack's sprite table: size 0x200, 32 x 32, OAM 0x0850951C and subsprite tables
    0x085095F4 (the hack's 32 x 32 people, e.g. 98, 182, use them), the new frame lists; tags, palette slot (2, by tag),
    shadow, walking animations kept;
  * the four palettes (0x1141 A, 0x1142 B, 0x1143, 0x1144) rewritten where the field palette table (the word at
    0x0808E8BC; Area Zero's copy, Kitakami's after it) has them;
  * battle pictures 250-252: new LZ77 pictures and palettes; the tables found through their entries (n of 250-252 is
    {picture, 0x800, n}, the palettes follow), the entries repointed. Kitakami copies the tables after it and takes
    them along (its Part 2 Nemona battle shows 250).
  * 30,836 bytes at 0x09E24000..0x09E2B874 (0x09E24000..0x09E2E000 kept): the hack's zero run 0x09E10044..0x09F00000,
    blank in its own ROM and in build 42; no code word points in (5 aligned look-alike words, none a literal; 27
    unaligned ones); read watch on build 42 (`_testrun/space/azpeople_watch.ps1`, nine runs: menus, Hisui, Surf and
    wild battles, saves and resets, Petalburg Woods' Continue, four walks): 0 reads. The cast's old pictures stay
    where paldea put them, unused.
  * kitakami/ksprites.py accepts Nemona's entry 32 x 32 too (it asserted 16 x 32). The map guide and both editors
    read a sprite's size from its entry, so they draw the new ones as they are.
- Tested (Area Zero's harness, `_testrun/azpeople/steps_azpeople*.lua`, the user's save; every scene looked at):
  Nemona in the future crater and her battle (her picture in the intro and on her platform; in the crater plants
  cover her legs, as on build 41); Arven in the past crater (his pack); the research stations after the ending
  (stage 4: Penny, Arven, Nemona with her rematch, Jacq); the Zero Lab: AI Sada and AI Turo at the machine, their
  battles (AI Sada's picture, "Professor AI Turo sent out Iron Moth" with his); Mossdeep's ending (stage 3, the four
  by the hole beside the town's people, colours right). The ROM's own frames decoded back match the pictures.
  "(my placements 43)" = **38fac465...**, 12,303 bytes from build 42; the whole chain from the v1.4 archive gives
  it byte for byte.

## A FAINTED POKEMON STAYS FAINTED — 2026-10-22 — `patches/hpcalc/`

- Found while checking the EV items for the 509 report (*EVs from battles stopped at 509*); the user: "if u r sure
  then, patch to current rom", "everything".
- The hack's own CalculateMonStats (0x09F038D8, behind the trampoline at 0x08068D0C) set HP to HP + (new max - old
  max) as a u16 and anything above the new max to the new max. A fainted Pokemon whose max HP rose came back with the
  difference (HP Up: 0/293 -> 2/295), and one whose max HP fell wrapped round to full HP, fainted or at 1 HP (Pomeg
  Berry: 0/338 -> 335/335, 1/340 -> 338/338) - a free Max Revive.
- The game's own routine is still in the ROM behind the trampoline (0x08068FAC..0x08068FF0): a new Pokemon (old max 0)
  gets the new max, a fainted one keeps 0, any other HP + (new max - old max), no floor (Emerald's Pomeg glitch).
  hpcalc does that in the hack's routine with a floor of 1: the 40 bytes 0x09F03A5C..0x09F03A84, the path taken when
  the max changes (an unchanged max keeps the HP as before, Shedinja's max is 1 there too). In place, no free space;
  asserted: the trampoline, the 40 bytes, the cap after them, the GetMonData literal. The original ROM has the bytes.
- Tested (`patches/evgain/test_evitems.lua`, from the Bag, build 43 as the control): HP Up on the fainted lead 0/295
  (control 2/295); Pomeg on 1 HP 1/338 (338/338), fainted 0/335 (335/335); a living Pokemon still moves with its max
  (100 -> 148/343, 148 -> 85/280, the same on both); a Rare Candy at 100 HP 100/228 -> 103/231 on both (the hack
  refuses a Rare Candy on a fainted Pokemon, on both); a wild Zigzagoon starts at full HP (109/109).
- "(my placements 44)" = **34921763...**, 39 bytes from build 43 (one of the 40 is the same).

## ELECTRO SHOT IN THE RAIN — 2026-10-22 — `patches/eshot/`

- Reported: "from 1.9, i also found out that electro shot was not attacking in first turn during rain", "fixed in
  2.0?" - no: gen9rest made Electro Shot (982) from Meteor Beam and noted "charges in rain too"; nothing changed it.
- The two-turn moves are one effect (71). Its script (0x09D0509C: attackcanceler; `83 5400`) runs the engine's
  routine 84 (0x09D63A64), which picks the charge message by the move's number (a list of 15 moves; Electro Shot is not
  in it, so it showed the string the last two-turn move left: Geomancy's "is absorbing power!") and jumps by the move's
  last data byte to one of six scripts (pointers 0x09D050A0..0x09D050B7). Kind 2 (Skull Bash, Meteor Beam, Electro
  Shot): the charge message, `83 1900` (the stat change from byte 9), its message script 0x09D06DD0, `83 5500` (Power
  Herb: jump to the hit), else the charging turn. Kind 3 (Solar Beam, Solar Blade) checks Cloud Nine and the sun.
- The engine's script command 0x83 (0x09D686CC) steps over its three bytes, then calls routine n of the table at
  [0x09D686F0] + 12 with r0 = &gBattlescriptCurrInstr; a routine with a pointer reads it (0x09D3809A) or steps over it.
  Battle strings from 0x17C are [0x09D4A204] + 4 (id - 0x17C), no upper bound (0x09D4A1E8). Both words point at
  gen9abil's longer copies (342 strings, 222 routines, back to back at 0x09E35C98).
- eshot: kind 2's pointer (0x09D050A8) -> a new script: Electro Shot (`jumpifhalfword ==, gCurrentMove`) its own way,
  the others on to the old script. Electro Shot: the second turn if charging; its own charging turn ("{attacker}
  absorbed / electricity!", string 0x2D2, 180 px at most with "The opposing" and a ten-letter name); Sp. Atk +1;
  routine 222 (eshot.s): rain on the attacker -> the hit now; Power Herb -> the hit now; else the charging turn. Rain
  = gBattleWeather & 0x1007 (the engine's own mask, e.g. Swift Swim's), the weather in effect (0x09D45B84: Cloud Nine
  0x0D, Air Lock 0x10D) and no Utility Umbrella (hold effect 164, item 733). So a Power Herb is kept in the rain.
- Space: 0x09E3B000..0x09E3BA18 (the two longer tables, the routine, the script, the text; 0x09E3BC00 kept), in the
  stretch gen9abil proved (0x09E33000..0x09E3C000; gen9anim's part ends at 0x09E3ACD0): blank, no word at a 4-byte
  boundary points in (the same two unaligned look-alikes, 0x0851034B and 0x08703D25, inside pictures and code); a
  read watch on build 44 (`_testrun/space/eshot_watch.ps1`, nine runs as mintquirky's) found 0 reads while both
  control stretches were read.
- Tested (`_testrun/gen9abil/batch_eshot.ps1`, Pikachu against Snorlax; build 44 as the control). Gotcha: WEATHER=n
  written at the menu is gone by the time the move runs (0000 at the routine) - real rain needs Rain Dance first.
  Control: Rain Dance, then Electro Shot charges ("is absorbing power!") and fires the turn after. Fixed: in the rain
  "absorbed electricity!", Sp. Atk rose, the hit before Snorlax moves, each turn; dry: charges, hits the next turn;
  Utility Umbrella, Cloud Nine, Air Lock: charges in the rain; Power Herb: kept in the rain (534 after three turns),
  used up when dry; Meteor Beam and Skull Bash still charge in the rain, Solar Beam still fires in the sun.
- "(my placements 45)" = **2cb96ba2...**, 2,428 bytes from build 44; the whole chain from the v1.4 archive gives it
  byte for byte (111 s).
- Supreme Overlord, asked the same day ("still works or just a run away ability? in 2.0?"): gen9abil's (x1.1 for
  each fainted party Pokemon, up to x1.5), checked again on build 45: Kingambit in with two fainted, "Kingambit
  gained strength / from the fallen!", Tackle 58 against 49 with none fainted. In v1.9 it did nothing.

## GRANITE CAVE: FALLS INTO THE ROCK — 2026-10-22 — `patches/granitefall/`

- Reported with two screenshots (B1F's north-west cracked patch with its right-hand column ringed; the player inside
  the rock spur of B2F's north wall): "in granite cave, there is spot bug / Falling here will result in being stuck
  inside the wall."
- How a fall works here: B1F (24/8) resume script 0x0822DC6E = `setstepcallback 7` (cracked floor) + `setholewarp 24/9`;
  its frame script drops you when var 0x4022 is 0, which the step callback sets when you step onto a cracked tile
  (behaviour 0xD2) below the Mach Bike's top speed; you land on B2F at the same x, y (`SetWarpDestinationToFixedHoleWarp`).
  A warp onto a cracked tile drops you at once (the callback sees a new tile on its first frame).
- B1F's 67 cracked tiles (block 0x322F) against B2F's blocks: four over rock - (8, 1) 0x1610 and (8, 2) 0x1618 (the
  spur, the report), (25, 6) 0x1608 (the east wall's edge), all elevation 1 among elevation-3 floor, so you land and
  cannot move (an elevation mismatch on every side); (20, 3) 0x3650, a lone rock at elevation 3 (you can step off).
  Every other map with a `setholewarp` (24/16 -> 24/15, 24/80 -> 24/79, 24/82 -> 24/81, 24/95 and 24/96 -> 24/94
  and 24/95, 37/50 -> 37/51) has no cracked tile over a blocked one.
- granitefall: the four B1F blocks become 0x3201 (the floor beside them; low byte 0x2F -> 0x01 at 0x08431710,
  0x08431750, 0x084317A8, 0x08431872). The B2F spots under them are reached from the cracked tiles beside them. The
  patcher asserts the hole script, both floors' size, that one word holds B1F's blocks, the four cracked blocks and the
  four B2F blocks under them.
- Tested (`_testrun/granite/steps_fall.lua` in Area Zero's harness, build 45 as the control): build 45 onto (8, 1):
  B2F (8, 1), in the spur, Down / Left / Left do nothing; onto (25, 6): B2F (25, 6); onto (20, 3): B2F (20, 3), on the
  rock. Fixed: (8, 1), (8, 2), (25, 6), (20, 3) stay on B1F; the cracked tiles beside them, (7, 2), (24, 6), (19, 3),
  drop you onto B2F floor at the same spot, and you walk on from (7, 2). Every picture looked at.
- "(my placements 46)" = **f1fc3a60...**, 4 bytes from build 45; the whole chain from the v1.4 archive gives it
  byte for byte.

## A CLOCK ON THE START MENU — 2026-10-23 — `patches/startclock/`

- Asked, with a picture of a Start menu clock ("Thu. 10:29 AM (DAY)" in a box at the top left): "can we have
  time table next to R journey when press start menu?"
- What the game has: gLocalTime (0x03005CF8: s16 days, s8 hours, minutes, seconds) = the cartridge clock (sRtc
  0x03000DC0, BCD: year, month, day, weekday, hour, minute, second) less the offset the player set (SaveBlock2 +0x98,
  same layout), by RtcCalcLocalTime (0x0802F588). The game's day count, measured: the cartridge's 22 Oct 2026 (its
  weekday byte 4, a Thursday) is day 9792 = local days + offset days, so day 1 is Saturday 1 January 2000 and the
  weekday is (local days + offset days + 5) mod 7 (pokeemerald's ConvertDateToDayCount would leave out 2000; this one
  counts it). No time-of-day names in the hack: only its tint by the hour (*Day/night: on / off*) and night
  evolutions (18-5). The clock's names follow the tint: Morning 4-5, Day 6-16, Evening 17-18, Night 19-3.
- The window: BG0, palette 15, 15 x 2 tiles (the widest line, "Wed 12:59 PM (Evening)", 114 px in the normal font,
  printed at x 2), base block 64. Measured with the menu up (a `windows` step in the harness: gWindows 0x02020004):
  the menu 313-452, the Journal box 8-23, the message box (hidden) 404-511, the map-name popup's tiles 263-292; the
  Safari window takes 8-43 and the Pyramid's 8-55; the save window 8-147 (the clock is down by then). BG0's map with
  the menu up uses 0, 8-23, 313-452, 532-540. At (1, 5) under the Journal box, (1, 7) under the Safari / Pyramid
  window, (1, 1) without the Journal. The menu's own frame starts at x 21; the box ends at x 16.
- The hooks are the Quest Log's two, chained (ours first): InitStartMenuStep's step-3 jump table entry (0x0809F8C4,
  `mov pc` into it: an even address in Thumb) and HandleStartMenuInput's trampoline word (0x0809FAC8; lr is live:
  ours saves it, runs, puts it back and jumps on to the Quest Log's stub). Every frame of the menu's input it calls
  RtcCalcLocalTime and redraws when the hour or minute differs from the drawn one; A, B, START (and R with the
  Journal) take it down, as the Journal's box goes. Its state is 0x02039E48..0x02039E7F (magic "CLOK", window id,
  minute, template, hour, then the text), in the 64 bytes at 0x02039E40 the scratch test measured, after the Quest
  Log's 8; no ROM word points into it. Code and data 0x09E3BC00..0x09E3BF1C (eshot's proven stretch and read watch).
- Gotcha: keystone made `adds r5, r6, #8` a Thumb-2 `adds.w` (Thumb-1 takes 0-7 there); the patcher's twin check
  caught it.
- Tested (`_testrun/clock/steps_clock.lua`, `steps_clock2.lua`, `steps_nojournal.lua`; the offset's hours moved to
  show each hour): "Thu 4:21 PM (Day)", 10:22 AM Day, 4:22 AM Morning, 1:22 PM Day, 5:22 PM Evening, 12:22 AM Night,
  10:22 PM Night, a minute later 10:23 PM; B and START take it down; R -> Quest Log -> B, A -> Pokedex -> B and Save ->
  Cancel bring it back; in the Safari Zone (flag 0x88C) under "Safari Balls Stock"; without the Journal (a test copy
  asking for item 0x3FF) at the top, R leaves it. Taking the Journal out of the Bag in RAM did not hide the Journal's
  box (not looked into: the test copy did it).
- "(my placements 47)" = **9d6d95bb...**, 721 bytes from build 46; the whole chain from the v1.4 archive gives it
  byte for byte.

## THE CONSOLE'S CARTRIDGES IN THE QUEST LOG — 2026-10-23 — `patches/consolequest/`

- Asked: "after beating the game, I know that the gameconsole inside our character room, can battle like a lot but is
  the purpose??", then "include in the side quest, 4 quests".
- The console, read from the ROM (`tools/romdata/scripts.py`, `dis.py`): 1/1's sign at (3,1) (0x0987B8A8) and 1/3's at
  (5,1) (0x098806C3) say "It's a Nintendo GameCube..." and go to 0x0988F782 when the player is in their own room;
  it needs 0x41D5 (Team Rainbow Rocket beaten, Mountain Top) and 0x42F3 (Elio, Steven's Island 34/42 object 10,
  trainer 929: "I have a few cassettes here ... Use the console in your room", 3 cartridges). Menu: the hack's own
  multichoice lists carry each item's result in the word after its text (0x0987B890: 0x84, three items; 0x09882470:
  0x85, four), 0x85 once 0x4302 is set (Ash's challenge on Route 101, 0x081EBCD5: the red-haired passerby drops "a
  game cartridge with no label ... the console upstairs" and a note). Result in 0x4004: 0 Rainbow R. 0x09882666,
  1 Ultra A. 0x09882B87, 2 Friends 0x09882C45, 3 HP League 0x09882D19 (dispatcher 0x0988F7DF).
  - Rainbow R.: exactly 6 Pokemon (special 0x87); 10 battles (0x4002 counts): six doubles where you pick 2 leads
    (Tabitha 1092, Shelly 1086, Jupiter 1101, Zinzolin 1108, Xerosic 1115, Gideon 1079), three tag battles (special
    0xEF, pick 3) with a random partner from Red 857, Ash 878, Lucas 866, Black 867, Blake 870, X 874 against two
    random bosses from 1117-1122 (Archie, Maxie, Cyrus, Ghetsis, Lysandre, Faba; trainer flags keep them apart), then
    Giovanni 1116.
  - Ultra A. (rules mask 0x8000 = 55): Lance 883, Alder 887, Cynthia 886, Iris 888, Steven 884, Diantha 889, Blue 855,
    Wallace 885, Leon 881. Friends (47): Ash 878, Elio 929, X 874, Blake 870, Black 867, Lucas 866, Ruby 926 (Sapphire
    927 for a girl), Gold 859, Red 857. HP League (47): Gengyi 1016, Xiao Bing 923, Yolgz 954, Wudan 925, Aimon 1154,
    Waji 998, Yanshan 899. These three: at least 2 Pokemon, then the Gym's party rules (0x0983B147, "Rules for the
    Pokemon Gym") unless the difficulty var 0x409B is 1 (Standard); team order fixed.
  - Each battle: the party saved (special 0x28), healed, the battle, the party loaded back (0x29), a loss -> "GAME
    OVER" (0x09882B67, nothing else). All won: `call 0x09882738` (clears the run's hide flags 0x264, 0x268, 0x273,
    0x274, 0x276, 0x278, 0x27F), "GAME CLEAR ... The winning team will be recorded in the Hall of Fame", then
    0x082298E9 / 0x082298F5 by gender: the Hall of Fame's own ending (0x082298D9 jumps there too: setrespawn, special
    0x113): the Hall of Fame (it saves the game), the credits, THE END, the title. No item, no money, and until now
    no flag: nothing in the save said a cartridge was won.
- consolequest: each cartridge's `call 0x09882738` before GAME CLEAR (0x09882B3F, 0x09882C1C, 0x09882CF0, 0x09882D9A;
  the GAME OVER path's own call at 0x09882B6C stays) -> an 8-byte stub, `setflag F; goto 0x09882738` (the routine's
  `return` comes back behind the call). Flags 0x43A4 Rainbow R., 0x43A8 Ultra A., 0x43A9 Friends, 0x416B HP League:
  `kitakami/freecheck.py` on build 46 and the user's saves (Area Zero 45, 46, Kitakami's eight; the old
  roms/current save does not parse): no setflag / clearflag / checkflag bytes for them anywhere, no aligned word, no
  object hides by them, clear in every save, not trainer flags; the same seven free ones as on 2026-10-17 (0x407A,
  0x414F, 0x415B, 0x416B, 0x43A4, 0x43A8, 0x43A9), the 0x43xx three taken first. The patcher checks the ROM tests
  again on its input.
- The Quest Log: four rows after "The note's sender" (row 44, 0x4303), Area Zero's ten after them; the tables are
  copied longer (63 -> 67 rows with the Badges', which follow Side Content in the same table), SIDES_LIT (0x08FEB230)
  and PANES[3] (0x08FED368) repointed, PAGES' Side Content entry 55/55 -> 59/59 and the Badges' first row 55 -> 59, as
  gen9journal grew it. Location "Littleroot Town"; pictures Giovanni (128), Leon (226), Red (94) from the trainer
  records; HP League none (who waits in it is the surprise, as the note's sender's row). A page fits 8 lines (the
  texts were cut to 7-8; `journal_az.pane` asserts it), the panel 3 (cut with an ellipsis).
- Space: 0x09E22000..0x09E22DC4 used, 0x09E22000..0x09E24000 kept: the zero run 0x09E10044..0x09F00000 (the read
  watch of 2026-10-17), just below azpeople's 0x09E24000. 0x09E2E000..0x09E30000 was tried first and refused by the
  patcher: seven aligned words in pictures read as addresses in it (0x086E933C -> 0x09E2ECEC ...); no aligned word of
  the ROM reads as one anywhere in 0x09E21200..0x09E24000.
- Tested (Area Zero's harness, `patches/consolequest/steps_ending.lua`, the user's save of build 47 with 0x42F3 and
  0x4302 set; build 47 as the control): the console's lines and the four-item menu, B out of it; Rainbow R.'s ending
  entered at 0x09882B3F (`goto` from the harness's script): "GAME CLEAR", the Hall of Fame's "Saving..." and team,
  the credits, THE END, the title, Continue into Brendan's room (4,2): 0x43A4 = 1 after the reload (so in the Hall of
  Fame's save), the other three 0; the Quest Log grid "Side Quests 27/59", Side Content's rows 43-50 (the four with
  their pictures, Rainbow R. Done), Rainbow R.'s and HP League's 8-line pages, Friends' 7. Control: 0x43A4 stays 0,
  26/55, Area Zero's rows straight after the note's sender. Every frame looked at.
- Gotchas: SELECT with the Quest Log registered opens the key ring when other items are registered too: UP picks the
  Quest Log (as `test_questlog_side.lua`). Presses timed by frames slip a box: B meant for the menu advanced "Jude
  happens to have some games at hand", and the next A started Rainbow R.; press one box at a time and look. The
  harness's "fight" gives up after 60,000 frames; a cartridge's battles take about 10,000 each, so the playthrough ran
  on a copy of `test_paldea.lua` with 200,000 (`_testrun/console/h/`, `-Here` to it).
- Tested after, played through (`patches/consolequest/steps_play.lua`, build 48, the same save): the console's menu,
  DOWN x 3 to HP League, A, then the harness's "fight" (our side pinned): 7 battles (Gengyi's Lopunny and Typhlosion
  ... Yanshan's Darkrai and Blaziken), every foe Lv50 and the party screen shows ours at Lv50, "Jude got 0 for
  winning" each time; GAME CLEAR, the Hall of Fame, the credits, Continue (99,141 frames): 0x416B = 1, the other
  three 0. Every frame looked at.
- "(my placements 48)" = **b5572a73...**, 3,113 bytes from build 47 (only the regions above); the whole chain from the
  v1.4 archive gives it byte for byte (116 s).

## THE GIGANTAMAX MARK ON THE SUMMARY — 2026-10-23 — `patches/gmaxicon/`

- Asked, with a mock-up (the summary's first page, a small red mushroom at the bottom right of the picture): "for
  pokemon that already gained Gmax, can we dispaly icon like a mushroom in the pokemon detail ... I know that this
  game might use ribbon as as marked". Of the first mark (a red mushroom drawn here, build 49): "that mushroom design
  is stupid, cannot we use this attached img? I think it is the item max mushroom" (a crop of the Bag's Max Mushroom
  icon); of that icon at its own 24 x 24 (build 50, not handed over): "smaller", "too big"; of 51, with a mock-up of
  it right of the nickname: "the gmax icon cannot be on top overlay of the name right like this reference position
  but make sure it would not affect any name".
- The mark the game keeps (*Form changes: where the game keeps them*): bit 7 of the Pokemon's byte +0x4E, set by the
  Max Soup cook on Champion Island (35/28, script 0x098A7425: checkitem 87 x3, the party's first Pokemon, removeitem,
  0x8004 = 0, callasm 0x08C60581) and read by the Gigantamax table walk (0x08FF1858, item 0xEFEF). It is Emerald's
  ribbon word (+0x4C) bit 23, the Country Ribbon's, which nothing else gives: the summary's ribbon count counts it
  (Blaziken with the bit: "Ribbons: 3"). The cook gives it to any Pokemon (its text: "if you give soup to a Pokemon
  that can only Dynamax, the form won't change"), so the mark shows on any Pokemon that has had the soup.
- The summary screen (this hack's layout): sMonSummaryScreen 0x0203CF1C; its copy of the Pokemon it shows at +0xC;
  the picture's sprite id at +0x40D3 and the ball's at +0x40D4 (measured: 5 / 7 on the first page). Its
  CreateCaughtBallSprite (0x081C4A08: GetMonData ball, the hack's ball templates at 0x09F093E4, CreateSprite at
  (16, 136)) runs for every Pokemon the screen shows, from 0x081BFD56 (opening) and 0x081C07F6 (switching), both with
  r0 = +0xC.
- gmaxicon: an 8-byte trampoline at 0x081C4A08 (its push {r4, lr}, movs r1, #0x26 and bl GetMonData) to stub, which
  replays them inside a frame that returns to it, lets the routine make the ball, then: any sprite whose template is
  ours goes (found by scanning gSprites for its callback, so nothing is kept in RAM), its tiles and palette freed by
  tag (0x47A1; LoadSpriteSheet takes tiles again for a tag already loaded), and when the bit is set a 16 x 16 sprite
  (OAM 16 x 16, priority 0) centred at (70, 103) - the right end of the nickname's row, the icon at x 64..77, y
  97..110 (measured: the nickname is printed from x 8 in rows 96..111, the panel's inside ends at x 78, the frame at
  y 95, the species row starts at 112) - when the nickname (mon +8, up to 10 letters; its width from the normal
  font's own table 0x086542E4, "Blaziken" 44 px as on the screen) is at most 54 px, 2 px clear of the icon; a longer
  one (a 10-letter name reaches 60 px, x 68) gets it at (64, 88), its bottom right on the picture frame's. So it
  never covers a name. The picture is the Max
  Mushroom's own icon (item 87: the table at 0x08FCBFF4 the Bag's icons come from, LZ77, 24 x 24 4bpp and a
  16-colour palette, both read by the patcher), brought to 14 x 14 by taking the source pixel under each new pixel's
  middle (every pixel one of the icon's own colours), in the sprite's bottom right. Its callback hides it while the
  summary's copy has no bit (another Pokemon or an egg after a switch) or while the picture is hidden. (Build 50
  showed the icon at 24 x 24 through the game's AddItemIconSprite 0x081AFE70, which frees the template it builds -
  why the mark is found by its callback.) Gotcha: a last LZ77 copy can run past the stated size; trim to it. Routines: CreateSprite 0x08006DF4, DestroySprite 0x080070E8, LoadSpriteSheet
  0x080084F8, FreeSpriteTilesByTag 0x08008568, LoadSpritePalette 0x08008744 (goldbox's), FreeSpritePaletteByTag
  0x0800884C.
- Space: 0x09E3AD00..0x09E3AF0C (0x09E3AFF0 kept: the word for eshot's routine table holds 0x09E3AFF4, its table -
  12, which the 0x83 command never reads; the patcher's pointer check found it), in gen9abil's proven stretch after
  gen9anim's 0x09E3ACD0: blank, no other word points in; read watch on build 47 (`_testrun/space/gmax_watch.ps1`, nine runs as eshot's): 0 reads, while the control
  stretches were read.
- Tested (`_testrun/gmax/steps_gmax.lua`; the lead Blaziken given the bit, the second Pokemon not; the mark found
  by its callback): the mark on the lead; gone on the second (DOWN), back on the lead (UP); on the four pages and the move details;
  out to the party and back in; none on the field.
- Built on the console step as "(my placements 49)" = **b0c4a118...**, 427 bytes from build 48 (the trampoline and
  0x09E3AD00..0x09E3AF0B); the same test on it: the same results. The whole chain from the v1.4 archive gives it
  byte for byte. With the Max Mushroom icon at 14 x 14: "(my placements 51)" = **dee892f0...**, 341 bytes from build
  50 (in 0x09E3AD04..0x09E3AF0F); the same test: the same results; the whole chain from the v1.4 archive gives it
  byte for byte.
- On the name row (`_testrun/gmax/steps_gmax_names.lua`, the lead given the bit and four nicknames): "Spooky!" (40
  px) and "AAAAAAAAA" (54 px) on the row, 2 px clear; "Fletchindr" (55) and "Mmmmmmmmmm" (60) in the picture's
  corner; the Moves page and its move details (the mark above the Effect box), a switch to the second Pokemon (gone)
  and back, the field (none). Gotcha again: keystone makes `adds rD, rN, #8` Thumb-2. "(my placements 53)" =
  **e8810b63...**, built on the other session's 52 (the clock beside the Journal), 408 bytes from it (in
  0x09E3AD04..0x09E3AF37); the test copy was the whole chain from the v1.4 archive and is the same file.

## THE CLOCK BESIDE THE JOURNAL — 2026-10-23 — `patches/startclock/`

- Asked, with a screenshot of build 47's menu ("[R] Journal" over "Thu 5:02 PM (Evening)"): "remove the evening,
  whatever, and move into the same row as R Journey".
- startclock now: the text is the day and the time only ("Thu 5:08 PM"; clock_draw no longer copies a period, and
  HOURTAB / PERIODS are gone from the data); the three window templates differ in their left as well as their top
  (PLACES): (1,1) without the Journal, (11,1) beside it, (1,7) under the Safari / Pyramid window, all 9 x 2 (widest
  line "Wed 12:59 PM", 63 px, + 2 px each side). The geometry: the Journal's box is the Quest Log's WIDGET_TEMPLATE
  (1,1) 8 x 2, frame tiles 0-9 (the patcher finds those 8 bytes once in the Quest Log's code); ours at (11,1), frame
  10-20; the Start menu's window is at x 22, its frame from 21 (the patcher asserts both edges). The Safari window
  (1,1) 9 x 4 and the Pyramid's (10-12 wide) leave no room beside them, so the clock stays under them there. The two
  frames side by side look as the stacked boxes did (the frame tile's own margin keeps them apart).
- Tested (`_testrun/clock/steps_clock.lua`, `steps_clock2.lua`, `steps_nojournal.lua` on the whole chain's result,
  the user's save of build 51): the windows log reads the Journal (1,1) 8x2, the clock (11,1) 9x2 tiles 64-81, the menu
  (22,1); the hours 10, 4, 13, 17, 0, 22 and a minute later ("Thu 10:09 PM", "Thu 12:08 AM" fit); B and START close it,
  it comes back after the Quest Log (R) and the Pokedex; the save window takes the corner and Cancel brings it back
  beside the Journal; in the Safari Zone (1,7) under "Safari Balls Stock"; without the Journal (a test copy whose two
  checks, 0x08FEB07C and 0x09E3BE04, ask for item 0x3FF) at (1,1), R leaves it. (steps_clock2's own no-Journal case,
  flag 0x4004, did not take the Journal away on this save: the Journal's box and R's Quest Log came up; the test copy is
  the real test.) Every frame looked at.
- "(my placements 52)" = **e3e56cec...**, 456 bytes from build 51, all in 0x09E3BC08..0x09E3BF1B; the whole chain from
  the v1.4 archive gives it byte for byte.

## THE ZYGARDE CUBE IS IN TERMINUS CAVE, NOT ON ROUTE 110 — 2026-10-23 — `patches/questlog/keyitems.py`

- Reported: "for the zygrade cube key items, change the location to terminus cave since it is not obtainable in route
  110". The Quest Log's Key Items row said "Lying on Route 110 (also in Terminus Cave)."
- In the ROM: two item balls run the Cube's finditem script (0x08290D81: item 621) and share one flag, 0x03EF:
  Route 110 (0/25) object 19 at (39,83) and Terminus Cave (34/34, map section 0x69) object 1 at (13,26). Route 110's
  stands on a blocked tile (block 0x170, elevation 1) in the map's last column, with blocked tiles on its other three
  sides ((38,83), (39,82), (39,84)) and no connection to the right: nobody can face it. Terminus Cave's is on open
  floor at elevation 3 with open floor all round. (The other two scripts holding 0x026D near a call are trainer
  battles on 0/249 and 0/250, not the Cube.)
- The row now reads "Lying in Terminus Cave." (the list's Location line follows: "Terminus Cave"). The Quest Log is
  a main-chain step, so: the whole chain from the v1.4 archive (`_testrun/full/chain_zc`), its gen9 stage as the new
  Gen 9 base in `roms/test-gen9` (9f2e5b2b...; the old one f9e053b0 in archive/ "(before the Zygarde Cube row
  2026-10-23)"), then rebuild.py. The Quest Log's texts after the row move, so the base differs in 5,589 bytes, all in
  the Quest Log's data (0x09F9A23C..0x09FA647B), and the steps that copy its tables follow (consolequest's
  0x09E2299C.., gen9journal's 0x09FEBD0C..).
- Tested (`_testrun/zcube/steps_zcube.lua`): Start, R, the Key Items card, row 36: "Location: Terminus Cave / Lying
  in Terminus Cave.", and A shows the same; the next row (Rotom Catalog) as before.
- "(my placements 54)" = **9932ea5b...**, the same file as the whole chain from the v1.4 archive.

## KIERAN'S GIGANTAMAX APPLES — 2026-10-24 — `patches/kitakami/`

- Found while the guide site's data was made for v2.0: the trainers page named Kieran's team "Gigantamax Appletun,
  Gigantamax Flapple". The ROM had it so: trainer rows 1359 and 1360 held species 270 and 269, and in battle his
  Appletun and Flapple showed the Gigantamax pictures (`_testrun/coop/run.ps1 -Trainers 1359,1360` on build 54 and
  55: the same levels, HP, items and abilities, the pictures and species ids differ).
- Why: in this hack a Gigantamax form is a species slot of its own that carries its Pokemon's name, and for 21 of
  them (Orbeetle, Corviknight, Coalossal, Hatterene, Grimmsnarl, Flapple, Appletun, Melmetal, Sandaconda, Copperajah,
  Duraludon, Toxtricity, Basculegion, Rillaboom, Cinderace, Inteleon, Drednaw, Urshifu, Alcremie, Centiskorch,
  Indeedee) that slot comes first in the name table: "Appletun" is 270 (Gigantamax) and 1143, "Flapple" 269 and 1142.
  `kitakami_patch.name_id` took the first slot of a name.
- The fix: the species lookup skips the Gigantamax slots, read from the ROM - the hack's battle-form table
  (0x08C9A3B0, {u16 species, u16 form, u16 item}, 0xFEFE ends; item 0xEFEF = a Gigantamax form, as
  `tools/romdata/forms.py` reads it; the patch asserts the table's fifth row and that 269 and 270 are in it). Where a
  name has only Gigantamax slots the first is still taken (none in Kitakami).
- Checked for the rest: every species Area Zero and Kitakami place (their trainers, wild tables and static
  encounters, 48 places in the v2.0 game) against the form slots, and every patch source that names a species by
  name against the 21 names: only Kieran's two. (`paldea_patch.species_id` has the same first-match rule; Area Zero
  names none of the 21.)
- Build 55 = build 54 with 8 bytes changed (0x09E474F4, 0x09E47504, 0x09E47514, 0x09E47534: 270 -> 1143, 269 -> 1142).
  "(my placements 55)" = `rom/` = **fb949e02...**; the whole chain from the v1.4 archive gives it byte for byte
  (`_testrun/rel20/chain.log`).

## RELEASE v2.0 — 2026-10-24

- Asked for: "push to release repo, follow instruction". The game is
  build 55 (fb949e02...). `release/hyper-emerald-en-qol.hpatch` (3,389,718 bytes, 9,815 runs) and
  `release/CHECKSUMS.txt`: applied to `Hyper EMR LA v5.7 bugfix 2.gba` (f785bed9...) it gives fb949e02.
- Public commit: the dev working copy mirrored by `_testrun/rel20/mirror_public.py` (rel18's with v1.9's rules: no
  `site/` and no built `docs/` but the hand-kept NOTES, DEXNAV-PROGRESS and showcase; the public `.gitignore` kept,
  with the rules the new sprite sources need; the first 2.0 GIF left out, as it was filmed before Area Zero's people
  were redrawn; a stray `infinityfree/` folder left out) into a worktree of `origin/main` in
  `gba-trans/hyper-emerald/_public/release-2.0`. The site was changed and built there and its sources copied back.
- Before it, every file that goes public was searched for what the public repo leaves out (the mirror's STRICT) and for any other
  project of this PC; two passages that pointed elsewhere were reworded.
- `.gitignore` (dev and public): `!patches/azpeople/sprites/*.png` and `!patches/kitakami/sprites/src/*.png`, the
  pictures `azpeople` and Kitakami's sprites are made from (the patchers read the `.4bpp` / `.gbapal` beside them).
- The site's data tools, for v2.0: `scan_wild.py` reads the wild table where the code points (Kitakami's longer copy:
  258 headers, Mossui Town's surfing and fishing), `build_sprites.py` the trainer pictures through their code words
  (0x0005DF78, 0x0005B784: 255 pictures, Area Zero's 250-252 and Kitakami's 253-254), `build_site_data.py` a Kitakami
  boss group (rows 1358-1360 and Mochi Mayhem's Nemona, 1378, who has Area Zero's name and class: `GROUP_IDS`).
- README: the v2.0 showcase GIF (`docs/showcase/showcase-v2.0-kitakami.gif`, `_testrun/showcase20b`), the Kitakami
  row marked v2.0, the save note, a credit for the art Area Zero's people were redrawn after (artist not found).
  Luciano Fire is credited for the key trainers' teams in the README, on the site's About page and in the release.
