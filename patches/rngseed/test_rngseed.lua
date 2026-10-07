-- rngseed: the RNG at power-on, and a static Rayquaza rolled the same way every run.
-- Logs gRngValue and the step counter sRandCount at frame 1 after the script attaches (the game's own seed check:
-- unpatched, the value is step N of the sequence from seed 0), then boots the save, starts a scripted battle with
-- Rayquaza Lv 50 exactly like the Sky Pillar's (setwildbattle 406 50; 0x8004 = 6, 0x8005 = 3; callasm 0x08FFF201
-- for its three perfect IVs; dowildbattle) at a fixed frame, and logs the wild Rayquaza's personality, nature and
-- IVs. Run it twice a few seconds apart: unpatched, the same inputs give the same Rayquaza (up to the emulator's
-- start-up jitter of a few frames); patched, a different one each time.
NAME = "rngseed"
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
w(string.format("first frame: gRngValue %08X  steps %d  clock %02X:%02X:%02X", emu:read32(0x03005D80), emu:read32(0x020249C0),
  emu:read8(0x03000DC4), emu:read8(0x03000DC5), emu:read8(0x03000DC6)))
local NATURES = {"Hardy", "Lonely", "Brave", "Adamant", "Naughty", "Bold", "Docile", "Relaxed", "Impish", "Lax", "Timid", "Hasty",
  "Serious", "Jolly", "Naive", "Modest", "Mild", "Quiet", "Bashful", "Rash", "Calm", "Gentle", "Sassy", "Careful", "Quirky"}
local t0, stage = nil, "start"
function TEST(f)
  t0 = t0 or f
  local d = f - t0
  if d == 30 then
    w(string.format("before the battle: gRngValue %08X  steps %d", emu:read32(0x03005D80), emu:read32(0x020249C0)))
    run({0xB6, 0x96, 0x01, 50, 0, 0, 0x16, 0x04, 0x80, 6, 0, 0x16, 0x05, 0x80, 3, 0, 0x23, 0x01, 0xF2, 0xFF, 0x08, 0xB7, 0x02})
  end
  if stage == "start" and d > 30 and cb2() == BATTLE then stage = "battle"; t0 = f - 31 end
  if stage == "battle" and d == 91 then
    local m = 0x02024744
    local pid, iv = emu:read32(m), emu:read32(m + 0x48)
    local ivs = {}
    for i = 0, 5 do ivs[#ivs + 1] = (iv >> (5 * i)) & 31 end
    w(string.format("Rayquaza: personality %08X  nature %s  IVs %d/%d/%d/%d/%d/%d (HP/Atk/Def/Spe/SpA/SpD)  species %d level %d",
      pid, NATURES[pid % 25 + 1], ivs[1], ivs[2], ivs[3], ivs[4], ivs[5], ivs[6], emu:read16(m + 0x20), emu:read8(m + 0x54)))
    shot("rngseed_rayquaza"); stage = "end"; done()
  end
  if d > 3000 and stage ~= "end" then w("TIMEOUT"); stage = "end"; done() end
end
