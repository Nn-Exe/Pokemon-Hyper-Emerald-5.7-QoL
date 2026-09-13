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
python tools/build_site_data.py tools/romdata/out      # -> docs/data/{wild,trainers,static}.json
python tools/build_search_index.py                     # -> docs/data/search.json
```

Outputs land in `tools/romdata/out/` (git-ignored). `SUMMARY.md` records every ROM address the scripts rely on and the
caveats of the heuristic script scans.
