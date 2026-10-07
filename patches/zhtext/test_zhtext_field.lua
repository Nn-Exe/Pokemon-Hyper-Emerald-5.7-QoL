-- zhtext on the field. Screens whose words were Chinese, opened and walked with a fixed list of key presses and a
-- screenshot after each, to be looked at.
-- MODE=easychat (default): the Easy Chat screen as an interview opens it (special 0x62 with VAR 0x8004 = TYPE, default 5,
--   the TV interview): the phrase, then the word groups and a group's words.
-- MODE=menu: START and the keys in KEYS (letters: U D L R A B S(tart) E(select) l r, "." = wait) - used for the
--   PokeNav's Hoenn map and its zoomed view with the landmark names.
-- Shots zh_<mode>_NN.png in the run directory.
local MODE = os.getenv("MODE") or "easychat"
local TYPE = tonumber(os.getenv("TYPE") or "5")
local KEYS = os.getenv("KEYS") or (MODE == "easychat" and "..A.A.D.D.R.A.D.D.A.B.B" or "S")
NAME = "zhtext_" .. MODE
dofile((DIR or "./") .. "../dexnavchain/test_boot.lua")
local SCRIPT = 0x0203F100
local function run(bytes)
  for i, b in ipairs(bytes) do emu:write8(SCRIPT + i - 1, b) end
  local ctx = 0x03000E40
  emu:write8(ctx + 0, 0); emu:write8(ctx + 1, 1); emu:write8(ctx + 2, 0)
  emu:write32(ctx + 4, 0); emu:write32(ctx + 8, SCRIPT)
  emu:write32(ctx + 0x5C, 0x081DB67C); emu:write32(ctx + 0x60, 0x081DBA08)
  emu:write8(0x03000F2C, 1); emu:write8(0x03000E38, 0)
end
local KEY = {U = K.UP, D = K.DOWN, L = K.LEFT, R = K.RIGHT, A = K.A, B = K.B, S = K.START, E = K.SEL, l = K.L, r = K.R}
local STEP = 70
local t0, n = nil, 0
function TEST(f)
  t0 = t0 or f
  local d = f - t0
  if d == 10 and MODE == "easychat" then
    run({0x16, 0x04, 0x80, TYPE, 0x00, 0x25, 0x62, 0x00, 0x27, 0x02})   -- setvar 0x8004, TYPE; special 0x62; waitstate; end
  end
  local start = MODE == "easychat" and 200 or 60
  if d >= start and (d - start) % STEP == 0 then
    local i = (d - start) // STEP + 1
    if i > #KEYS then
      if i == #KEYS + 1 then shot(string.format("zh_%s_%02d", MODE, i)); w("done at +" .. d); done() end
      return
    end
    shot(string.format("zh_%s_%02d", MODE, i))
    local k = KEYS:sub(i, i)
    w(string.format("+%d shot %02d, then key %s  (cb2 %08X)", d, i, k, cb2()))
    if KEY[k] then tap(KEY[k]) end
  end
end
