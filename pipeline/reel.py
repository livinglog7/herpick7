"""herpick 상품 릴스 렌더러 (1080x1920, 30fps) — 리빙로그 render.py 구조를 herpick 톤으로 옮김.

장면
  harin   : 하린 사진 전체 화면 + 천천히 확대(켄번스) + 자막
  product : 분야 + 대표 문구 + 상품 카드 + 자막
  feature : 상품 카드 크게 + 포인트 문구 + 자막
  cta     : "프로필 링크" + 큰 번호 + herpick7.com + 상품 카드
음성: 기본은 ElevenLabs v4 "루나"(voice_id 375a3398-e3b4-4f91-845d-42181e352899)로 v0~v3.mp3 를 미리 만들고
spec "voice":"file" 로 렌더(10/23 사용자 선택). edge-tts(ko-KR-SunHiNeural)는 예비용.
대사 말투: 친구한테 말하듯 "~거든?", "~더라", "와," 등 구어체. 설명문/스펙 나열 금지. 장면 길이 = 음성 길이 + 0.35초.
커버: 가운데 1080x1440 영역에 피드용 상품 이미지(그리드와 동일하게 보이도록).

사용: python reel.py spec.json out.mp4
spec = {"no":3,"category":"...","headline":"...","harin":"a.jpg","product":"p.jpg","cell":"cell.jpg",
        "points":["...","..."], "lines":["대사1","대사2","대사3","대사4"]}
"""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

W, H, FPS = 1080, 1920, 30
BG = (20, 16, 13)
INK = (242, 234, 224)
SUB = (162, 150, 138)
ACC = (196, 150, 95)
SLIDE, POP = 0.28, 0.38
DOMAIN = "herpick7.com"
FONT = os.environ.get("KR_FONT", os.path.expanduser("~/grid/kr.ttf"))
VOICE = os.environ.get("VOICE", "ko-KR-SunHiNeural")


@lru_cache(maxsize=None)
def font(size: int, weight: int = 700) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(FONT, size)
    try:  # 가변 폰트면 굵기 지정
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f


def ease_out_cubic(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def ease_out_back(t):
    t = max(0.0, min(1.0, t))
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def text_layer(text, size, color, weight=800, max_width=W - 120, box=None, pad=(36, 18), radius=22):
    f = font(size, weight)
    while True:
        b = f.getbbox(text)
        tw = b[2] - b[0]
        if tw <= max_width - (2 * pad[0] if box else 0) or size <= 28:
            break
        size = int(size * 0.94)
        f = font(size, weight)
    asc, desc = f.getmetrics()
    th = asc + desc
    if box:
        img = Image.new("RGBA", (tw + 2 * pad[0], th + 2 * pad[1]), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((0, 0, img.width - 1, img.height - 1), radius=radius, fill=box)
        d.text((pad[0] - b[0], pad[1]), text, font=f, fill=color)
    else:
        img = Image.new("RGBA", (tw + 8, th + 8), (0, 0, 0, 0))
        ImageDraw.Draw(img).text((4 - b[0], 4), text, font=f, fill=color)
    return img


def wrap(text, size, max_width, weight=700):
    f = font(size, weight)
    words, lines, cur = text.split(" "), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if f.getlength(t) <= max_width or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def subtitle(text):
    """화면 아래 자막(반투명 검은 박스, 최대 2줄)"""
    lines = wrap(text, 54, W - 200)[:2]
    lays = [text_layer(l, 54, (255, 255, 255), weight=700, max_width=W - 160) for l in lines]
    w_ = max(l.width for l in lays) + 64
    h_ = sum(l.height for l in lays) + 40
    img = Image.new("RGBA", (w_, h_), (0, 0, 0, 0))
    ImageDraw.Draw(img).rounded_rectangle((0, 0, w_ - 1, h_ - 1), radius=26, fill=(0, 0, 0, 165))
    y = 20
    for l in lays:
        img.alpha_composite(l, ((w_ - l.width) // 2, y))
        y += l.height
    return img


def card(path, width, max_height, radius=34):
    src = Image.open(path).convert("RGB")
    s = min(width / src.width, max_height / src.height)
    w_, h_ = int(src.width * s), int(src.height * s)
    src = src.resize((w_, h_), Image.LANCZOS)
    mask = Image.new("L", (w_, h_), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w_ - 1, h_ - 1), radius=radius, fill=255)
    sh = 30
    out = Image.new("RGBA", (w_ + 2 * sh, h_ + 2 * sh), (0, 0, 0, 0))
    shadow = Image.new("RGBA", out.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle((sh, sh + 12, sh + w_, sh + h_ + 12), radius=radius,
                                             fill=(0, 0, 0, 150))
    out = Image.alpha_composite(out, shadow.filter(ImageFilter.GaussianBlur(18)))
    out.paste(src, (sh, sh), mask)
    return out


def paste_center(base, layer, cx, y, scale=1.0, alpha=1.0):
    if alpha <= 0.01:
        return
    lay = layer
    if abs(scale - 1) > 0.005:
        lay = layer.resize((max(1, int(layer.width * scale)), max(1, int(layer.height * scale))),
                           Image.BILINEAR)
    if alpha < 0.999:
        lay = lay.copy()
        lay.putalpha(lay.getchannel("A").point(lambda v: int(v * alpha)))
    x, yy = int(cx - lay.width / 2), int(y + (layer.height - lay.height) / 2)
    l, t = max(0, x), max(0, yy)
    r, b = min(base.width, x + lay.width), min(base.height, yy + lay.height)
    if r > l and b > t:
        base.alpha_composite(lay.crop((l - x, t - yy, r - x, b - yy)), (l, t))


class Pop:
    def __init__(self, layer, y, delay=0.0, cx=W // 2, back=True):
        self.layer, self.y, self.delay, self.cx, self.back = layer, y, delay, cx, back

    def draw(self, base, t):
        p = (t - self.delay) / POP
        if p <= 0:
            return
        e = ease_out_back(p) if self.back else ease_out_cubic(p)
        paste_center(base, self.layer, self.cx, self.y, scale=min(0.8 + 0.2 * e, 1.05),
                     alpha=min(1.0, p * 1.6))

    def done(self, t):
        return t >= self.delay + POP


def bg_from(path):
    """상품 사진을 흐리게 깔아 어두운 배경 만들기"""
    im = ImageOps.fit(Image.open(path).convert("RGB"), (W, H)).filter(ImageFilter.GaussianBlur(40))
    dark = Image.new("RGB", (W, H), BG)
    return Image.blend(im, dark, 0.78).convert("RGBA")


def num(n):
    return f"{int(n):02d}"


# ---------------------------------------------------------------- scenes
def scene(kind, spec, line):
    """(정적 배경, 애니메이션 요소, 동적 그리기 함수 or None)"""
    no = spec["no"]
    sub = subtitle(line) if line else None
    items, dyn = [], None
    if kind == "harin":
        src = ImageOps.fit(Image.open(spec["harin"]).convert("RGB"), (W, H), centering=(0.5, 0.35))
        grad = Image.new("L", (1, H))
        for y in range(H):
            grad.putpixel((0, y), int(max(0, (y - H * 0.6) / (H * 0.4)) * 200))
        shade = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        shade.putalpha(grad.resize((W, H)))

        def dyn(t, dur, src=src, shade=shade):  # 천천히 확대
            z = 1.0 + 0.06 * (t / max(dur, 0.1))
            w_, h_ = int(W * z), int(H * z)
            im = src.resize((w_, h_), Image.BILINEAR).crop(((w_ - W) // 2, (h_ - H) // 3,
                                                           (w_ - W) // 2 + W, (h_ - H) // 3 + H))
            fr = im.convert("RGBA")
            fr.alpha_composite(shade)
            return fr
        base = None
    elif kind == "product":
        base = bg_from(spec["product"])
        items.append(Pop(text_layer(spec["category"], 46, ACC, weight=700), 200, delay=0.0, back=False))
        items.append(Pop(text_layer(spec["headline"], 96, INK, weight=900), 280, delay=0.1))
        c = card(spec["product"], 900, 980)
        base.alpha_composite(c, ((W - c.width) // 2, 470))
    elif kind == "feature":
        base = bg_from(spec["product"])
        c = card(spec.get("product2") or spec["product"], 960, 1000)
        base.alpha_composite(c, ((W - c.width) // 2, 180))
        y = 180 + c.height + 10
        for i, ptxt in enumerate(spec.get("points", [])[:2]):
            items.append(Pop(text_layer(ptxt, 64, (20, 16, 13), weight=800, box=ACC + (255,),
                                        pad=(34, 14)), y + i * 130, delay=0.1 + i * 0.2))
    elif kind == "cta":
        base = bg_from(spec["product"])
        items.append(Pop(text_layer("프로필 링크에서", 88, INK, weight=900), 200, delay=0.0))
        items.append(Pop(text_layer(f"{num(no)}번", 230, (20, 16, 13), weight=900, box=ACC + (255,),
                                    pad=(70, 16), radius=40), 360, delay=0.18))
        items.append(Pop(text_layer(DOMAIN, 60, INK, weight=700), 740, delay=0.45, back=False))
        c = card(spec["product"], 780, 700)
        base.alpha_composite(c, ((W - c.width) // 2, 880))
    else:
        raise ValueError(kind)
    if base is not None:
        tag = text_layer(f"HERPICK {num(no)}", 34, ACC, weight=800)
        base.alpha_composite(tag, (60, 70))
    return base, items, dyn, sub


# ---------------------------------------------------------------- audio
def probe(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                 "-of", "csv=p=0", path], capture_output=True, text=True,
                                check=True).stdout.strip())


def tts(text, path, rate="+8%"):
    import edge_tts

    async def go():
        await edge_tts.Communicate(text, VOICE, rate=rate, pitch="+6Hz").save(path)
    asyncio.run(go())


def build_audio(paths, durs, out, bgm=None):
    inputs, filt, labels = [], [], []
    for i, p in enumerate(paths):
        inputs += ["-i", p]
        filt.append(f"[{i}:a]aresample=44100,aformat=channel_layouts=stereo,"
                    f"apad=whole_dur={durs[i]:.3f},atrim=0:{durs[i]:.3f}[a{i}]")
        labels.append(f"[a{i}]")
    total = sum(durs)
    filt.append("".join(labels) + f"concat=n={len(paths)}:v=0:a=1[v]")
    final = "[v]"
    if bgm and os.path.exists(bgm):
        inputs += ["-stream_loop", "-1", "-i", bgm]
        filt.append(f"[{len(paths)}:a]aresample=44100,aformat=channel_layouts=stereo,volume=0.12,"
                    f"atrim=0:{total:.3f},afade=t=out:st={max(0, total - 1.2):.3f}:d=1.2[bg]")
        filt.append("[v][bg]amix=inputs=2:duration=first:dropout_transition=0[m]")
        final = "[m]"
    subprocess.run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(filt),
                    "-map", final, "-c:a", "aac", "-b:a", "192k", out], check=True)


def make_cover(spec, out):
    """그리드에 보이는 가운데 3:4 영역 = 피드용 상품 이미지"""
    cv = Image.new("RGB", (W, H), BG)
    cell = ImageOps.fit(Image.open(spec["cell"]).convert("RGB"), (1080, 1440))
    cv.paste(cell, (0, (H - 1440) // 2))
    cv.save(out, quality=92)


def render(spec, out, wd):
    kinds = ["harin", "product", "feature", "cta"]
    lines = spec["lines"]
    auds, durs = [], []
    for i, line in enumerate(lines):
        p = os.path.join(wd, f"v{i}.mp3")
        if spec.get("voice") != "file":  # "file" = v0~v3.mp3 를 미리 만들어 둔 경우(ElevenLabs 루나)
            tts(line, p)
        auds.append(p)
        durs.append(max(probe(p) + 0.35, 2.0))
    audio = os.path.join(wd, "audio.m4a")
    build_audio(auds, durs, audio, spec.get("bgm"))
    built = [scene(k, spec, lines[i]) for i, k in enumerate(kinds)]
    starts = [0.0]
    for d in durs[:-1]:
        starts.append(starts[-1] + d)
    total = int(round(sum(durs) * FPS))
    tmp = os.path.join(wd, "video.mp4")
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", audio, "-c:v", "libx264",
                            "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "copy",
                            "-shortest", "-movflags", "+faststart", tmp], stdin=subprocess.PIPE)

    def frame(i, t):
        base, items, dyn, sub = built[i]
        fr = dyn(t, durs[i]) if dyn else base.copy()
        for it in items:
            it.draw(fr, t)
        if sub is not None:
            a = min(1.0, max(0.0, (t - 0.05) / 0.25))
            paste_center(fr, sub, W // 2, H - 330, alpha=a)
        return fr

    for f in range(total):
        t = f / FPS
        i = max(k for k, s in enumerate(starts) if s <= t + 1e-6)
        lt = t - starts[i]
        if i > 0 and lt < SLIDE:
            p = ease_out_cubic(lt / SLIDE)
            prev, cur = frame(i - 1, durs[i - 1]), frame(i, lt)
            fr = Image.new("RGBA", (W, H), BG + (255,))
            off = int(W * p)
            if off < W:
                fr.alpha_composite(prev.crop((off, 0, W, H)), (0, 0))
            if off > 0:
                fr.alpha_composite(cur.crop((0, 0, off, H)), (W - off, 0))
        else:
            fr = frame(i, lt)
        enc.stdin.write(fr.convert("RGB").tobytes())
    enc.stdin.close()
    if enc.wait() != 0:
        raise RuntimeError("인코딩 실패")
    os.replace(tmp, out)
    make_cover(spec, os.path.splitext(out)[0] + "_cover.jpg")
    return {"duration": round(sum(durs), 2)}


if __name__ == "__main__":
    sp = json.load(open(sys.argv[1], encoding="utf-8"))
    o = sys.argv[2]
    print(json.dumps(render(sp, o, os.path.dirname(os.path.abspath(o))), ensure_ascii=False))
