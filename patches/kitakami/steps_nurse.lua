-- Mossui's Pokemon Center: talk to the nurse, one press at a time, a picture of every page (the user, 2026-10-17:
-- "the npc to heal in pokemon center has a weird dialog mixed chinese and spacebar").
local at = os.getenv("PLACE") == "petalburg" and {8, 4} or {35, 109}
STEPS = {
  {"setup"},
  {"warp", at[1], at[2], 7, 5},
  {"walk", 7, 4, "on", "to_counter"}, {"face", "UP"}, {"shot", "at_counter"},
  {"a"}, {"wait", 60}, {"shot", "p1"},
  {"press", "A", 60}, {"shot", "p2"},
  {"press", "A", 60}, {"shot", "p3"},
  {"press", "A", 120}, {"shot", "p4"},
  {"press", "A", 120}, {"shot", "p5"},
  {"press", "A", 120}, {"shot", "p6"},
  {"press", "A", 120}, {"shot", "p7"},
  {"press", "A", 120}, {"shot", "p8"},
  {"press", "A", 120}, {"shot", "p9"},
  {"press", "A", 120}, {"shot", "p10"},
  {"press", "A", 120}, {"shot", "p11"},
  {"flags", 0x880, 0x159, 0x111},
  {"finish"},
}

-- who resets the game: the registers when the CPU reaches address 0, and the last few callbacks before it
local caught = false
emu:setBreakpoint(function()
  if caught or emu:currentFrame() < 900 then return end
  caught = true
  local t = {}
  for _, r in ipairs({"r0", "r1", "r2", "r3", "r4", "r5", "r6", "r7", "r8", "r12", "lr", "sp", "pc", "cpsr"}) do
    t[#t + 1] = string.format("%s=%08X", r, emu:readRegister(r))
  end
  w("RESET at 0: " .. table.concat(t, " "))
  local sp, s = emu:readRegister("sp"), {}
  for k = 0, 23 do s[#s + 1] = string.format("%08X", emu:read32(sp + 4 * k)) end
  w("   stack: " .. table.concat(s, " "))
  w(string.format("   script ctx: ptr %08X, cb1 %08X cb2 %08X", emu:read32(0x03000E40 + 8), emu:read32(0x030022C0), emu:read32(0x030022C4)))
end, 0x00000000)
for _, v in ipairs({0x08000000, 0x08000004, 0x080000C0}) do
  emu:setBreakpoint(function()
    if caught or emu:currentFrame() < 900 then return end
    caught = true
    w(string.format("RESET at %08X: lr %08X sp %08X r0 %08X cpsr %08X | script ptr %08X cb2 %08X", v, emu:readRegister("lr"), emu:readRegister("sp"), emu:readRegister("r0"), emu:readRegister("cpsr"), emu:read32(0x03000E40 + 8), emu:read32(0x030022C4)))
    local sp, st = emu:readRegister("sp"), {}
    for k = 0, 23 do st[#st + 1] = string.format("%08X", emu:read32(sp + 4 * k)) end
    w("   stack: " .. table.concat(st, " "))
  end, v)
end

-- every change of the script's position and the callbacks from the nurse's heal on, until it goes wrong
local tr = {on = false, n = 0, last = ""}
callbacks:add("frame", function()
  local ptr = emu:read32(0x03000E40 + 8)
  if not tr.on and ptr >= 0x08271990 and ptr < 0x08271A00 then tr.on = true end
  if not tr.on or tr.n > 400 then return end
  local s = string.format("ptr %08X mode %d cb1 %08X cb2 %08X lock %d | task0 %08X", ptr, emu:read8(0x03000E40 + 1),
    emu:read32(0x030022C0), emu:read32(0x030022C4), emu:read8(0x03000F2C), emu:read32(0x03005E00))
  if s ~= tr.last then
    tr.n = tr.n + 1; tr.last = s
    w(string.format("f%d %s", emu:currentFrame(), s))
  end
end)
