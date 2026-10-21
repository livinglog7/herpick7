"""herpick7 정적 사이트 생성 (GitHub Pages, docs 폴더).

- index.html  : 전체 상품 목록 + 번호/이름 검색
- N/          : 인스타 피드 N번 상품 페이지 (네이버 쇼핑 커넥트 링크 버튼)

링크는 모두 상대 경로라서 username.github.io/herpick7/ 같은 하위 경로에서도,
나중에 연결할 herpick7.com 같은 도메인에서도 그대로 동작합니다.
SITE_DOMAIN 환경변수가 있으면 CNAME 파일을 만듭니다.
"""
from __future__ import annotations

import html
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")
SITE_DOMAIN = os.environ.get("SITE_DOMAIN", "").strip()

BRAND = "HERPICK"
TAGLINE = "여사친이 골라주는 남자템"
DISCLOSURE = "쇼핑 커넥트 활동으로 판매 시 수수료를 받을 수 있어요. 하린은 AI 버추얼 모델이에요."

HEAD = """<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><meta name="description" content="{desc}">
<meta property="og:title" content="{title}"><meta property="og:description" content="{desc}">
{og_image}<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='16' fill='%23141010'/%3E%3Ctext x='32' y='44' font-size='34' text-anchor='middle' fill='%23C4965F' font-family='serif'%3EH%3C/text%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;900&family=Cormorant+Garamond:wght@600&display=swap" rel="stylesheet">
<style>
:root{{--bg:#141110;--card:#1E1A18;--ink:#F2EAE0;--sub:#A2968A;--line:#332C28;--acc:#C4965F;color-scheme:dark}}
*{{box-sizing:border-box}}html{{-webkit-text-size-adjust:100%}}
body{{margin:0;background:var(--bg);color:var(--ink);font-family:"Noto Sans KR",system-ui,sans-serif;line-height:1.5;word-break:keep-all;overflow-wrap:anywhere}}
a{{color:inherit}}.wrap{{max-width:980px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}}
.top{{padding-block:34px 10px;text-align:center}}
.brand{{font-family:"Cormorant Garamond",serif;font-size:34px;font-weight:600;letter-spacing:.24em;text-decoration:none;color:var(--acc)}}
.tag{{margin:4px 0 0;color:var(--sub);font-size:14px}}
.note{{margin:14px auto 0;max-width:640px;font-size:12px;color:var(--sub);text-align:center}}
.search{{position:sticky;top:0;z-index:5;background:var(--bg);padding-block:14px}}
.search input{{width:100%;font:inherit;font-size:17px;padding:14px 20px;border:1px solid var(--line);border-radius:999px;background:var(--card);color:var(--ink);outline:none}}
.search input:focus{{border-color:var(--acc)}}
.grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;padding-bottom:40px}}
@media(min-width:720px){{.grid{{grid-template-columns:repeat(4,minmax(0,1fr));gap:16px}}}}
.item{{display:block;background:var(--card);border:1px solid var(--line);border-radius:16px;overflow:hidden;text-decoration:none}}
.item:focus-visible,.btn:focus-visible{{outline:2px solid var(--acc);outline-offset:2px}}
.ph{{position:relative;aspect-ratio:1;background:#0c0a09}}.ph img{{width:100%;height:100%;object-fit:cover}}
.no{{position:absolute;top:8px;left:8px;background:var(--acc);color:#141110;font-weight:900;font-size:14px;min-width:38px;height:30px;padding:0 9px;border-radius:999px;display:flex;align-items:center;justify-content:center;font-variant-numeric:tabular-nums}}
.tx{{padding:10px 12px 14px}}.cat{{margin:0;font-size:11px;color:var(--acc);letter-spacing:.04em}}
.nm{{margin:2px 0 0;font-size:14px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;min-height:2.9em}}
.pr{{margin:6px 0 0;font-weight:900}}.empty{{text-align:center;color:var(--sub);padding:40px 0}}
.detail{{max-width:560px;margin:0 auto;padding-block:8px 48px}}
.hero{{background:#0c0a09;border-radius:20px;overflow:hidden;border:1px solid var(--line);position:relative}}.hero img{{width:100%;display:block;aspect-ratio:1;object-fit:cover}}
.hero .no{{top:14px;left:14px;font-size:18px;min-width:56px;height:40px}}
.hl{{margin:18px 0 0;color:var(--acc);font-size:14px;font-weight:700}}
h1{{font-size:21px;line-height:1.4;margin:4px 0 6px;text-wrap:balance}}
.price{{font-size:30px;font-weight:900;margin:10px 0 2px;font-variant-numeric:tabular-nums}}.small{{font-size:12px;color:var(--sub)}}
.btn{{display:block;margin:20px 0 10px;text-align:center;background:var(--acc);color:#141110;text-decoration:none;font-weight:900;font-size:18px;padding:17px;border-radius:14px}}
.back{{display:block;text-align:center;color:var(--sub);font-size:14px;margin-top:8px}}
</style></head><body>"""


def esc(s) -> str:
    return html.escape(str(s or ""), quote=True)


def won(n) -> str:
    return f"{int(n):,}원" if n else ""


def num(n) -> str:
    return f"{int(n):02d}"


def detail_page(p: dict) -> str:
    title = f"{num(p['no'])}번 · {p['name']} | {BRAND}"
    head = HEAD.format(title=esc(title), desc=esc(f"하린픽 {num(p['no'])}번 · {p.get('headline', '')}"),
                       og_image=f'<meta property="og:image" content="{esc(p.get("image"))}">')
    return head + f"""
<div class="wrap"><header class="top"><a class="brand" href="../">{BRAND}</a>
<p class="note">{esc(DISCLOSURE)}</p></header>
<main class="detail">
<div class="hero"><span class="no">{num(p['no'])}</span><img src="{esc(p.get('image'))}" alt="{esc(p['name'])}"></div>
<p class="hl">{esc(p.get('headline'))}</p>
<h1>{esc(p['name'])}</h1>
<p class="price">{won(p.get('price'))}</p>
<p class="small">{esc(p.get('date'))} 기준 가격이에요. 실제 가격은 네이버에서 확인해 주세요.</p>
<a class="btn" href="{esc(p['link'])}" rel="sponsored nofollow noopener" target="_blank">네이버에서 보기</a>
<a class="back" href="../">다른 하린픽 둘러보기</a>
</main></div></body></html>"""


def index_page(items: list) -> str:
    head = HEAD.format(title=f"{BRAND} · 하린픽", desc=f"{TAGLINE} · 인스타 번호로 찾아보세요", og_image="")
    cards = []
    for p in sorted(items, key=lambda x: -x["no"]):
        key = esc(f"{p['no']} {num(p['no'])} {p['name']} {p.get('category', '')}".lower())
        cards.append(f"""<a class="item" href="./{p['no']}/" data-no="{p['no']}" data-s="{key}">
<div class="ph"><span class="no">{num(p['no'])}</span><img loading="lazy" src="{esc(p.get('image'))}" alt=""></div>
<div class="tx"><p class="cat">{esc(p.get('category'))}</p><p class="nm">{esc(p['name'])}</p><p class="pr">{won(p.get('price'))}</p></div></a>""")
    empty = "검색 결과가 없어요" if items else "곧 첫 하린픽이 올라와요"
    return head + f"""
<div class="wrap"><header class="top"><a class="brand" href="./">{BRAND}</a>
<p class="tag">{TAGLINE}</p>
<p class="note">{esc(DISCLOSURE)}</p></header>
<div class="search"><input id="q" type="search" inputmode="search" autocomplete="off" placeholder="인스타 번호 또는 이름 (예: 01)"></div>
<div class="grid" id="g">{''.join(cards)}</div>
<p class="empty" id="e"{' hidden' if items else ''}>{empty}</p></div>
<script>
var q=document.getElementById('q'),cs=[].slice.call(document.querySelectorAll('.item')),e=document.getElementById('e');
function n(v){{return String(parseInt(v,10))}}
q.addEventListener('input',function(){{var v=q.value.trim().toLowerCase(),k=0;
cs.forEach(function(c){{var ok=!v||(/^\\d+$/.test(v)?c.getAttribute('data-no')===n(v):c.getAttribute('data-s').indexOf(v)>-1);c.style.display=ok?'':'none';if(ok)k++}});
e.hidden=k>0;}});
q.addEventListener('keydown',function(ev){{var v=q.value.trim();if(ev.key==='Enter'&&/^\\d+$/.test(v)){{var c=document.querySelector('.item[data-no="'+n(v)+'"]');if(c)location.href=c.getAttribute('href')}}}});
</script></body></html>"""


def build(items: list) -> None:
    os.makedirs(DOCS, exist_ok=True)
    with open(os.path.join(DOCS, "index.html"), "w", encoding="utf-8") as fp:
        fp.write(index_page(items))
    for p in items:
        d = os.path.join(DOCS, str(p["no"]))
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as fp:
            fp.write(detail_page(p))
    with open(os.path.join(DOCS, "404.html"), "w", encoding="utf-8") as fp:
        fp.write(f'<!doctype html><meta charset="utf-8"><title>{BRAND}</title>'
                 '<body style="background:#141110;color:#F2EAE0;font-family:sans-serif;text-align:center;padding:60px 16px">'
                 '<p>페이지를 찾을 수 없어요.</p><p><a style="color:#C4965F" href="javascript:history.back()">돌아가기</a></p>')
    cname = os.path.join(DOCS, "CNAME")
    if SITE_DOMAIN:
        with open(cname, "w") as fp:
            fp.write(SITE_DOMAIN + "\n")
    elif os.path.exists(cname):
        os.remove(cname)
    open(os.path.join(DOCS, ".nojekyll"), "w").close()


if __name__ == "__main__":
    db_path = os.path.join(DOCS, "products.json")
    data = json.load(open(db_path, encoding="utf-8")) if os.path.exists(db_path) else []
    build(data)
    print(f"사이트 생성: 상품 {len(data)}개")
