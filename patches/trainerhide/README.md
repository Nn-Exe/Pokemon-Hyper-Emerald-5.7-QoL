# Hide trainers you choose

A tool for taking specific trainers off the map, where **you** decide which ones. Nothing is hidden until you
list it in `hidden.json`.

## 1. See the trainers on a map

```
python patches/trainerhide/trainers.py "your rom.gba" --map "Rainbow Castle"
python patches/trainerhide/trainers.py "your rom.gba" --map 34/87            # one floor
python patches/trainerhide/trainers.py "your rom.gba" --sav "your save.sav"  # the map you saved on
```

Use the name the in-game map screen shows; partial names work ("Allearth" finds Allearth Forest and Lake).
Each trainer gets a verdict:

| Verdict | Meaning |
|---|---|
| SAFE | Plain trainer: a battle and nothing else. Hiding it only skips the fight. |
| CHECK | Harmless to hide, but look first: double battle, rematch trainer, a phone-registration call after the battle, or it already vanishes later together with a group. |
| RISKY | Leave it unless you know the story there: a boss class (Admin, Leader, Champion...), a script after the battle that sets a flag / moves objects / warps / gives an item, an object the story shows or hides on its own, or one a cutscene moves or removes. |

## 2. Pick

Add one entry per trainer to `hidden.json` (`--json` prints entries you can copy):

```json
[
  {"map": "34/87", "object": 0, "trainer_id": 1096, "name": "Grunt"}
]
```

## 3. Build

```
python patches/trainerhide/trainerhide_patch.py in.gba out.gba
```

Each entry is checked first (the object must still be that trainer), so a typo can't hide the wrong thing.

## How hiding works, and why it is safe

The trainer's object stays in the map's list, so every other object keeps its number and cutscenes that refer to
objects by number still work. Its position is moved far outside the map and its line of sight is turned off.
The game only creates objects near the camera, so it never appears, never spots you, and can't be talked to. No
save data changes: its trainer flag stays unset, as if you never met it. Delete the entry and rebuild to bring it
back. Verified in mGBA on Rainbow Castle 34/87: without the patch the Galactic Grunt at (23,7) spots you and starts
a battle; with it hidden the room is empty there and the other trainers are unchanged.
