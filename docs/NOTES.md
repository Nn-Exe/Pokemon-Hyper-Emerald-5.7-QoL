# Hyper Emerald v5.7 — Project Checklist

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
