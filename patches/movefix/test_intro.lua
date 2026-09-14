-- test_intro.lua: mGBA (0.11 dev, --script) autoplay from the title screen through the new-game intro:
-- Unown Ruins 34/12 -> Temple of the End 35/35 -> Mountain Top 34/66 cutscene -> truck 25/40 -> Littleroot.
-- Edit base to a writable folder; logs map/pos/script per frame to nav2_log.txt and screenshots to shots/.
local base="/path/to/testrun"
local log=io.open(base.."/nav2_log.txt","w")
local A,B,SEL,START,RIGHT,LEFT,UP,DOWN=0,1,2,3,4,5,6,7
local frame=0; local lastscr=-1; local lx,ly,still=-1,-1,0
local wp66={{12,31},{11,31},{11,30},{11,29},{11,28},{12,28},{13,28},{14,28},{14,27},{14,26},{14,25},{14,24},{14,23},{15,23},{16,23},{16,22},{16,21},{16,20},{16,19},{16,18},{16,17}}
local function follow(wps,x,y)
  local idx=nil
  for i,p in ipairs(wps) do if p[1]==x and p[2]==y then idx=i end end
  local t
  if idx==nil then t=wps[1] elseif idx>=#wps then return nil else t=wps[idx+1] end
  if t[1]>x then return RIGHT elseif t[1]<x then return LEFT elseif t[2]>y then return DOWN elseif t[2]<y then return UP end
  return nil
end
callbacks:add("frame", function()
  frame=frame+1
  emu:clearKeys(0x3FF)
  local sb1=emu:read32(0x03005D8C)
  local grp,num,x,y=-1,-1,-1,-1
  if sb1>=0x02000000 and sb1<0x02040000 then x=emu:read16(sb1); y=emu:read16(sb1+2); grp=emu:read8(sb1+4); num=emu:read8(sb1+5) end
  local mode=emu:read8(0x03000E41)
  local scr=emu:read32(0x03000E48)
  local key=nil
  if x==lx and y==ly then still=still+1 else still=0 end
  lx,ly=x,y
  if frame<5000 and not (grp==34 and num==12) then
    local c=frame%40
    if c<4 then key=START elseif c>=20 and c<24 then key=A end
  elseif mode~=0 then
    if frame%12<3 then key=A end
  else
    if grp==34 and num==12 then key=nil
    elseif grp==35 and num==35 then
      if x~=25 then key=(x<25) and RIGHT or LEFT else key=UP end
    elseif grp==34 and num==66 then key=follow(wp66,x,y)
    elseif grp==25 and num==40 then key=RIGHT
    else if frame%30<3 then key=A end end
    if still>90 and still%40<3 then key=A end
  end
  if key then emu:addKey(key) end
  if frame%20==0 or scr~=lastscr then
    log:write(string.format("f%d map %d/%d pos %d,%d mode %d scr %08x cb2 %08x\n",frame,grp,num,x,y,mode,scr,emu:read32(0x030022C4))); log:flush()
    lastscr=scr
  end
  if frame>=8000 and frame%20==0 then emu:screenshot(string.format("%s/shots/f%06d.png",base,frame)) end
end)
