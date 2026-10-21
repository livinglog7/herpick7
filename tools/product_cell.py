"""상품 칸 이미지(1080x1440) 생성: python tools/product_cell.py 원본사진 출력파일 번호 분야 대표문구 상품명 한줄설명"""
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
src,out,no,cat,head,name,desc=sys.argv[1:8]
W,H=1080,1440
bg=(20,16,13); ink=(240,232,220); muted=(160,146,128); accent=(196,150,96)
F=lambda w,s: ImageFont.truetype(f"/usr/share/fonts/opentype/noto/NotoSansCJK-{w}.ttc",s,index=1)
im=Image.new("RGB",(W,H),bg)
p=Image.open(src).convert("RGB")
pw=720; ph=int(p.height*pw/p.width)
if ph>760: ph=760; pw=int(p.width*ph/p.height)
p=p.resize((pw,ph),Image.LANCZOS).filter(ImageFilter.UnsharpMask(2,60,2))
m=Image.new("L",(pw,ph),0); ImageDraw.Draw(m).rounded_rectangle((0,0,pw,ph),36,fill=255)
y=170; im.paste(p,((W-pw)//2,y),m)
d=ImageDraw.Draw(im)
d.text((72,70),f"HERPICK  {int(no):02d}",font=F("Bold",30),fill=accent)
d.text((W-72,70),cat,font=F("Medium",30),fill=muted,anchor="ra")
ty=y+ph+40
size=76
while d.textlength(head,font=F("Black",size))>W-144: size-=2
d.text((72,ty),head,font=F("Black",size),fill=ink)
d.line((72,ty+118,150,ty+118),fill=accent,width=4)
d.text((72,ty+142),name,font=F("Medium",36),fill=ink)
d.text((72,ty+196),desc,font=F("Regular",30),fill=muted)
d.text((72,H-80),f"프로필 링크 → {int(no):02d}번",font=F("Medium",28),fill=accent)
im.save(out,quality=92)
