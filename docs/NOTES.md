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
Party menu option table sCursorOptions @0x08615C08 (33 x {text ptr, CursorCb ptr}; readers = literals @0x1B32F8 (DisplaySelectionWindow), 0x1B37C8/0x1B37F8 (input handler; dispatch is by table index, B = actions[numActions-1])). Copied to free space @0x08FD9B8C with entry 33 = {"Moves", cursor_moves}. Field action builder SetPartyMonFieldSelectionActions @0x081B3414 appends SUMMARY, field moves (0x13+j), SWITCH (if party[1] exists), ITEM/MAIL, CANCEL; eggs never reach it. Hook: the CANCEL append @0x081B3518 (16 bytes) -> trampoline to builder_hook @0x08FD9B00, which appends 33 only if numActions < 7 (actions[] holds 8: 4 field moves + 4 = full) then CANCEL, returns to 0x081B3529. Ids >= 0x13 draw in the field-move text colour (cosmetic). cursor_moves mirrors CursorCb_Summary @0x081B37FC: PlaySE(5); sPartyMenuInternal(0x0203CEC4)->exitCallback(+4) = cb2_moves; Task_ClosePartyMenu(0x081B12C1). cb2_moves: gSpecialVar_0x8004 (0x020375E0) = gPartyMenu(0x0203CEC8).slotId(+9); jump CB2_InitLearnMove 0x081606A1 (vanilla; TeachMoveRelearnerMove special 227 @0x08160639 = ScriptContext2_Enable + CreateTask(0x08160665) + fade, NOT used because the script lock would freeze the field). The relearner exits via CB2_ReturnToField. Move list builder @0x08161B94 is a hack trampoline (-> 0x09F06119), shared by script and screen, so expanded learnsets work. Verified: give-up path and full learn (forget Rock Slide, learn Hammer Arm) in mGBA; test scripts in the folder. Pitfall found while testing: the START menu remembers its cursor, so scripted menu navigation must not assume "Pokedex" is selected after the first visit.

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
  Route 101's map script (`0x081EBCD5`, var 0x4023 checks) then stages Ash's 2-vs-2 and sets 0x4302; the note
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
