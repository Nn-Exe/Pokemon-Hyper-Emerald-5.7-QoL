# ROM data-mining scripts

These dump the tables the guide site is built from (map names, wild encounters, trainers, items, species, moves,
scripted encounters). They only need Python 3.

```
set HE_ROM=path	o\Hyper Emerald v5.7 EN+QoL.gba      # the patched build
python tools/romdata/dump_tables.py
python tools/romdata/dump_maps.py
python tools/romdata/dump_trainers.py
python tools/romdata/scan_wild.py
python tools/romdata/scan_static.py
python tools/romdata/make_key_trainers.py
python tools/build_site_data.py tools/romdata/out      # -> site/src/data/{wild,trainers,static,species,items,forms}.json
python tools/build_sprites.py                          # -> site/public/sprites/{mon,trainer,item}.png (needs Pillow)
python tools/build_site_content.py                     # -> site/src/data/{journal,side-content}.json
cd site && npm run build                               # -> docs/ (the published site)
```

`species_display.py` and `display_names.py` hold the names the site prints: the ROM's tables cut names to 10-13
characters and name every alternate form after its base species.

Outputs land in `tools/romdata/out/` (git-ignored). `SUMMARY.md` records every ROM address the scripts rely on and the
caveats of the heuristic script scans.
