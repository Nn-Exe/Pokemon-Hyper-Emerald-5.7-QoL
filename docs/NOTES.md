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
  0x09D7973C); the move's PP comes from gBattleMoves at 0x09D86419 (12-byte stride, PP at +4). There is no
  hidden ability to grant: base stats are the vanilla 28-byte struct with two ability slots.
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
