-- dexstats: the "[R] Stats" tab and R on the Pokedex's INFO page. A steps file of patches/paldea/test_paldea.lua
-- (its run.ps1: -Steps ../dexstats/test_dexstats.lua -Extra "TABCB=0x09FDD1F7"), from a copy of the user's save.
-- dsinfo logs the tab: data0 heartbeat, data1-4 the panel's pieces (id + 1; 0 = no panel), data5 the species drawn.
--   * a seen Pokemon's page (Bulbasaur): the tab; R -> the panel (a picture, its species); R -> gone;
--   * R on, then Down: the next Pokemon's page comes up with its panel; on through to a caught one (Charizard);
--   * the panel for Gen 9 and other numbers, by setting the entry's number (the page keeps its picture; the panel
--     follows the number): 1007 Koraidon, 1025 Pecharunt, 151 Mew, 906 Sprigatito;
--   * A opens AREA: tab and panel gone; B back: both again (the task kept the panel on);
--   * R off; B to the list, A on the same Pokemon: the page opens with the panel off (a new task);
--   * 20 presses of R, then out of the Pokedex: as many sprites in use as before (nothing left behind).
local CB = tonumber(os.getenv("TABCB") or "0x09FDD1F7")
local function cat(...)
  local out = {}
  for _, l in ipairs({...}) do for _, s in ipairs(l) do out[#out + 1] = s end end
  return out
end
local function info(tag) return {"dsinfo", tag, CB} end
local churn = {}
for k = 1, 20 do churn[#churn + 1] = {"press", "R", 8} end
STEPS = cat(
  {{"boot"}, {"daynight_off"}, {"menutop"}, {"press", "START", 60}, info("field"), {"press", "A", 200},
   {"press", "A", 200}, info("info_page"), {"shot", "bulbasaur"},
   {"press", "R", 30}, {"shot", "bulbasaur_on"}, info("bulbasaur_on"),
   {"press", "R", 30}, {"shot", "bulbasaur_off"}, info("off"),
   {"press", "R", 30}, {"press", "DOWN", 180}, {"shot", "venusaur_on"}, info("venusaur_on"),
   {"press", "DOWN", 150}, {"press", "DOWN", 150}, {"press", "DOWN", 180}, {"shot", "charizard_on"},
   info("charizard_on"),
   {"dexnum", 1007}, {"wait", 20}, {"shot", "n1007_on"}, info("n1007"),
   {"dexnum", 1025}, {"wait", 20}, {"shot", "n1025_on"}, info("n1025"),
   {"dexnum", 151}, {"wait", 20}, {"shot", "n151_on"}, info("n151"),
   {"dexnum", 906}, {"wait", 20}, {"shot", "n906_on"}, info("n906"),
   {"dexnum", 6}, {"wait", 20}, info("back_to_6"),
   {"press", "A", 150}, {"shot", "area"}, info("area"),
   {"press", "B", 150}, {"wait", 30}, {"shot", "back_from_area"}, info("back_from_area"),
   {"press", "R", 30}, {"shot", "charizard_off"}, info("charizard_off"),
   {"press", "B", 150}, info("list"), {"press", "A", 200}, {"shot", "reopened"}, info("reopened")},
  churn,
  {{"wait", 20}, {"shot", "after_churn"}, info("after_churn"), {"press", "B", 150}, info("list2"),
   {"press", "B", 150}, info("menu_again"), {"press", "B", 60}, info("field_again"), {"finish"}})
