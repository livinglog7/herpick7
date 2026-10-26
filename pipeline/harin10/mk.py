import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
FONT=__import__('os').path.expanduser('~/grid/kr.ttf')
def band(text, size, path, w=1080, h=240, box=True):
    img=Image.new('RGBA',(w,h),(0,0,0,0)); f=ImageFont.truetype(FONT,size)
    d=ImageDraw.Draw(img); b=d.textbbox((0,0),text,font=f); tw,th=b[2]-b[0],b[3]-b[1]
    while tw>w-120: size-=4; f=ImageFont.truetype(FONT,size); b=d.textbbox((0,0),text,font=f); tw,th=b[2]-b[0],b[3]-b[1]
    x=(w-tw)//2-b[0]; y=(h-th)//2-b[1]
    if box:
        d.rounded_rectangle(((w-tw)//2-34,(h-th)//2-24,(w+tw)//2+34,(h+th)//2+24),radius=28,fill=(0,0,0,120))
    sh=Image.new('RGBA',(w,h),(0,0,0,0)); ImageDraw.Draw(sh).text((x+3,y+4),text,font=f,fill=(0,0,0,200))
    img=Image.alpha_composite(img,sh.filter(ImageFilter.GaussianBlur(3)))
    ImageDraw.Draw(img).text((x,y),text,font=f,fill=(255,255,255,255))
    img.save(path)
band(sys.argv[1],76,'hook.png',box=False)
band(sys.argv[2],52,'sub.png')
