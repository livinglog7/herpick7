"""하린 릴스 자막 이미지 생성: python mk.py "훅" "대사" → hook.png(상단 띠) sub.png(하단 자막)
글씨체(10/26 변경): 훅 = 고운바탕 Bold(우아한 명조 계열), 대사 = 고운돋움(둥글고 부드러운 고딕). 둘 다 구글폰트(OFL).
폰트는 샌드박스 ~/fonts 에 있음 (github.com/google/fonts ofl/gowunbatang, ofl/gowundodum)."""
import os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
FD = os.path.expanduser('~/fonts')
HOOK_FONT = f'{FD}/GowunBatang-Bold.ttf'
SUB_FONT = f'{FD}/GowunDodum-Regular.ttf'

def band(text, size, path, font, w=1080, h=240, box=True, stroke=0):
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0)); f = ImageFont.truetype(font, size)
    d = ImageDraw.Draw(img)
    def meas():
        b = d.textbbox((0, 0), text, font=f); return b, b[2] - b[0], b[3] - b[1]
    b, tw, th = meas()
    while tw > w - 120:
        size -= 4; f = ImageFont.truetype(font, size); b, tw, th = meas()
    x = (w - tw) // 2 - b[0]; y = (h - th) // 2 - b[1]
    if box:
        d.rounded_rectangle(((w - tw) // 2 - 34, (h - th) // 2 - 24, (w + tw) // 2 + 34, (h + th) // 2 + 24), radius=28, fill=(0, 0, 0, 120))
    sh = Image.new('RGBA', (w, h), (0, 0, 0, 0)); ImageDraw.Draw(sh).text((x + 3, y + 4), text, font=f, fill=(0, 0, 0, 200))
    img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(3)))
    ImageDraw.Draw(img).text((x, y), text, font=f, fill=(255, 255, 255, 255), stroke_width=stroke, stroke_fill=(30, 20, 18, 230))
    img.save(path)

band(sys.argv[1], 80, 'hook.png', HOOK_FONT, box=False, stroke=4)
band(sys.argv[2], 54, 'sub.png', SUB_FONT)
