# Hyper Emerald v5.7 — English translation: RESUME (updated 2026-07-12)

Goal: finish translating leftover Chinese text in `Hyper EMR LA v5.7 bugfix 2.gba`
(Hyper Emerald: Lost Artifacts v5.7, a 32MB=max Pokemon Emerald hack, code BPEE).
Output: `Hyper Emerald v5.7 - Full English.gba` (sits next to original; original untouched).

## CURRENT STATUS: WORKING, FREEZE FIXED, AUDITED
- All 27 translation batches complete (~6,500 strings translated; ~4,000 safely inserted).
- The ~5-min freeze (Volo/Arceus legendary cutscene) is FIXED and re-verified.
- Independent audit: all 3,931 relocated strings sit in genuinely-free, unreferenced space (0 violations).
- Game code byte-identical to original (0 changes < 0x1DC000, font excluded). Header intact.
- Not exhaustively played (only ~15 min autoplay + static audit). Deep post-game screens unverified.

## FILES IN THIS FOLDER
- `patch_final3.py`  — THE current/correct patcher. Rebuilds the output ROM. Edit `sp` path if paths change.
- `audit_freespace.py` — independent post-build check: every relocated string in truly-free space.
- `safespace.py`     — computes how much genuinely-safe free space exists.
- `inserter.py`      — English->Gen3 text encoder + word-wrap.
- `worklist2.json`   — {chinese: [rom_offsets]} aligned-pointer corpus.
- `worklist3f.json`  — delta (unaligned/script-pointer) corpus.
- `translations/trans_00..26.json` — {chinese: english}; "@@SKIP@@" = junk/skip.

## TO REBUILD
1. Ensure `sp` in patch_final3.py points at the scratchpad (or copy the .json inputs next to it and adjust).
2. `python patch_final3.py`  -> writes the output ROM. Watch the asserts:
   - "low-ROM changed bytes (must be 0): 0"
   - "placed strings overlapping a pointer target (must be 0): 0"
3. `python audit_freespace.py` -> must end "ALL relocated strings are in genuinely-free, unreferenced space".
4. Freeze-test (see below) before declaring done.

## KEY TECHNICAL FACTS (verified, don't rediscover)
- Chinese encoding: two-byte GB2312. lead 0x01-0x1E except {0x06,0x1B}; second 0x00-0xF6.
  char = GB2312_hanzi[ adj(lead)*247 + second ]; adj=lead-1, -1 more if lead>6, -1 more if lead>0x1B.
  (GB2312 hanzi table = 0xB0A1..0xF7FE, 94 per row.)
- Chinese font: 12x12 in 16x16 cell, 2bpp, 64 bytes/glyph, tiles TL,TR,BL,BR, MSB-first, ink=pixel value 1.
  Located at ROM 0xE3CF64 and 0xEAAF64.
- Single-byte punctuation: 0x37 . 0x38 — 0x39 ~ 0x3A 、 0x3B , 0x3C ! 0x3D ? 0x3E : 0x35 = 0x36 ;
  0x2D & 0x2E + 0x34 Lv 0x5B % 0x5C ( 0x5D ) 0x51 ¿ 0x52 ¡ 0x06 É 0x1B é 0xF0 :
- English text = vanilla Gen3 charmap (A=0xBB, a=0xD5, 0=0xA1, space=0, \n=0xFE \l=0xFA \p=0xFB,
  terminator=0xFF, buffers=0xFD xx, extended ctrl=0xFC + sub + args).

## PATCHER SAFETY RULES (all essential — each fixed a real bug)
1. FREE SPACE: only write into 0xFF bytes with NO pointer target within 768 bytes (MARGIN);
   EXCLUDE the mega expansion region at 0x1F82521+ and any 0xFF run with >6 inbound pointer refs.
   (A run of 0xFF is NOT free if the game holds pointers into it — that caused the cutscene freeze.)
2. POINTER OCCURRENCES: never rewrite a pointer occurrence at offset < 0x1DC000 (code/menu literals).
3. Drop worklist addresses strictly INSIDE another accepted string's extent (shifted-dup false pointers).
4. Deterministic allocation: sort unique encoded strings by (len desc, bytes).
5. Skip translations that end in \p/\n/\l or have unbalanced []  (can hang the message engine).

## VERIFICATION HARNESS (mGBA)
- Emulator: mGBA dev build in %TEMP%\mgba-dev\*\mGBA.exe (supports --script lua). If gone, re-download
  from https://s3.amazonaws.com/mgba/mGBA-build-latest-win64.7z and extract.
- Freeze test: run `fz.lua` (autoplay: START/A then walk+A) on the ROM for ~285s, screenshot frames
  8800-17000, then measure DISTINCT screen hashes among frames>=9600. FROZEN = distinct<=2 (screen
  stuck on the cutscene); CLEAN = distinct>=30 (interactive). Original ROM = ~179; fixed build = ~181.
- `freeze_bisect.py` = full automated classify+bisect harness (finds exact culprit rewrite if a freeze
  recurs). Its self-test runs a placed-only build which MUST come back clean.
- Emulator runs ~55-60fps real-time; delete the ROM's .sav before each fresh-boot test.

## SAVE COMPATIBILITY (tell the user)
.sav battery saves transfer across ALL builds (code is byte-identical). User can play now and swap in a
future fixed ROM keeping progress — mGBA matches .sav by filename. Save-STATES (.ss0) do NOT transfer.

## KNOWN REMAINING WORK / IDEAS
- ~365 strings couldn't be placed in safe space (left Chinese) — could reclaim space by translating
  more tersely or reusing in-place slots.
- Not all screens verified; if a specific screen freezes or shows Chinese, use freeze_bisect.py / the
  encoding facts above to target it.
- Possible image-baked Chinese (title logo etc.) is pixel art, not text — out of scope of this text pass.
