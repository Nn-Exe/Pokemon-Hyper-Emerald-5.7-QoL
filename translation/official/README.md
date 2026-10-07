# The leftover-Chinese pass: generators and scans

These scripts make the data files of `patches/zhtext/` and check a ROM for Chinese the game can still reach.
They read the working ROM and a checkout of [pret/pokeemerald](https://github.com/pret/pokeemerald) with its
built `pokeemerald.sym` beside it (default `gba-trans/_testrun/pret_src/`, or set `HE_PRET`). Nothing here is
needed to build the ROM: `zhtext_patch.py` only reads the JSON it ships with.

Run them from this folder, on the ROM as it is **before** `zhtext` (the chain's stage after `lmoveinfo`):

```
python scan.py         <rom> scan_now.json          # every labelled Emerald text: same / Chinese / other
python gen_official.py <rom> ../../patches/zhtext   # official.json + charmap.json   (needs scan_now.json, decap.json)
python gen_hack.py     <rom> ../../patches/zhtext   # hack.json   (-v lists every entry with its Chinese)
python gen_cityzoom.py ../../patches/zhtext         # cityzoom.lz
python remain.py       <rom> [out.txt]              # what is left: run it on the ROM after zhtext too
python names_scan2.py  <rom>                        # Chinese names that repeat at a fixed stride (tables)
```

| File | What it is |
|---|---|
| `vanilla.py` | Emerald's texts by address: labels and strings from the pret source, addresses and sizes from the symbol file. A static name used in two files (`sText_PleaseWaitAWhile`) is told apart by size. |
| `scan.py` | Compares the ROM with each official text at its own address, decodes the hack's two-byte Chinese (`dec`). |
| `decap.py`, `decap.json` | The casing rule ("POKéMON" → "Pokémon"…), learned from the official texts an earlier pass had already turned to modern casing in place. |
| `gen_official.py` | The official texts that are Chinese in the ROM, with their English in modern casing. A handful are overridden where the hack's text means something else (`OVERRIDE`). |
| `gen_hack.py` | The hack's own strings. `INPLACE`: English that fits the Chinese string's bytes. `MOVE`: a new copy, with every reference found and classified (`sites`). Then `lines.py` and `gen_tables.py`. |
| `lines.py` | 153 trainer intro / defeat lines (and three field lines) that were only reachable through `trainerbattle` arguments at unaligned script addresses. Unwrapped English; `gen_hack.py` wraps at 34. |
| `tables.py`, `gen_tables.py` | Names inside tables: the hack's trainers, items, its four restored fossil Pokémon, the Pokédex filler entries, and Emerald's Trainer Hill and apprentice names (from the pret source). |
| `gen_cityzoom.py` | The PokéNav's zoomed-city labels sheet from the pret PNG, as LZ77. |
| `remain.py` | Three scans: official texts still Chinese; strings a pointer reaches that read as real Chinese; the battle engine's offset-addressed block. |
| `names_scan2.py` | Short Chinese strings ended by 0xFF, with any byte before them, clustered by stride: a table of names shows up as a run (the hack's trainer table does, 40 bytes apart). |

What the scans still list on the finished ROM, and why each is left, is in `docs/NOTES.md`, *Leftover Chinese*.
