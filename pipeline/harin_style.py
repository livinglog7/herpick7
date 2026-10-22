"""하린 사진 스타일 라이브러리 + 프롬프트 생성기.

레퍼런스 계정(옷·배경·포즈) 분석으로 만든 목록에서 날짜(줄 번호)마다 겹치지 않게 골라
한 줄(오른쪽·왼쪽 하린 2장)에 쓸 프롬프트 2개를 만든다.
- 같은 줄 2장은 옷·헤어·장소가 같고 포즈·구도만 다르다 (하루의 이야기).
- 몸매 문구는 고정, 옷은 항상 몸에 붙는 핏(가슴 크기 유지).
사용: python pipeline/harin_style.py 7   → 7번째 줄 프롬프트 출력
"""
from __future__ import annotations

import json
import sys

BODY = "mature hourglass figure with a full bust, defined waist, curvy hips"

# (이름, 프롬프트) — 전부 몸에 붙는 핏. 계절감(가을·겨울) 위주 + 사계절 아이템 섞음
OUTFITS = [
    ("화이트 집업 크롭 니트+연청", "a thin fitted white long-sleeve zip-up cropped knit top, half unzipped, with low-rise light washed distressed jeans"),
    ("홀터넥 탑+블랙 슬랙스", "a thin fitted ivory halter-neck sleeveless top with black high-waisted slacks"),
    ("그레이 나시+오픈 가디건", "a fitted heather gray tank top with a loose cropped white cardigan slipping off one shoulder and light jeans"),
    ("그레이 하이넥 반팔+트레이닝팬츠", "a thin fitted gray mock-neck short-sleeve tee with matching gray jogger sweatpants"),
    ("카라 니트+미니스커트", "a fitted beige collared polo knit top with a short cream mini skirt"),
    ("도트 미니 원피스", "a fitted black polka-dot square-neck mini dress with burgundy pointed flats"),
    ("버터옐로 플레어 원피스", "a butter yellow sleeveless fitted-bodice flared mini dress"),
    ("민트 니트+크림 미니스커트", "a thin fitted mint short-sleeve scoop-neck knit top with a cream mini skirt"),
    ("코르셋 벌룬 미니 원피스", "an ivory corset-bodice bubble-hem mini dress with black sneakers"),
    ("브라운 슬립 미니 원피스", "a fitted brown ruched cami mini dress"),
    ("하늘색 셔츠 원피스", "a fitted light blue short-sleeve button-up shirt mini dress, top buttons open"),
    ("베이지 골지 니트 원피스", "a fitted beige ribbed knit sleeveless bodycon midi dress"),
    ("블랙 나시+플리츠 미니", "a fitted black camisole top with a cream pleated tennis mini skirt"),
    ("새틴 하이넥 미니", "a silver satin sleeveless mock-neck fitted mini dress"),
    ("라일락 플라워 캐미 원피스+가디건", "a lilac floral print cami mini dress with a white knit cardigan off the shoulders"),
    ("레드 트위드 재킷+블랙 미니+롱부츠", "a cropped red tweed jacket over a fitted black top, black mini skirt and knee-high black boots"),
    ("트위드 재킷+브라운 롱부츠", "a cropped beige tweed jacket with a fitted brown mini skirt and knee-high brown riding boots"),
    ("니트 셋업+부츠컷", "a fitted taupe knit sleeveless top and matching flared knit pants set"),
    ("블랙 터틀넥+가죽 스커트", "a thin fitted black turtleneck with a black leather pencil mini skirt and sheer tights"),
    ("스트라이프 가디건+핑크 미니", "a fitted brown-and-cream striped cropped cardigan buttoned up with a pink mini skirt"),
    ("크림 니트 셋업 숏츠", "a fitted cream knit cardigan with matching knit shorts set"),
    ("블랙 바디슈트+요가", "a black sleeveless scoop-neck bodysuit, home workout look"),
]

# (이름, 프롬프트, 야간 여부)
SCENES = [
    ("카페 창가", "sitting at a window table in a bright Seoul cafe with an iced americano", False),
    ("편의점", "inside a bright Korean convenience store aisle holding a shopping basket", False),
    ("베이커리 카운터", "at the counter of a cozy bakery cafe with pastries in the display", False),
    ("호텔 방 소파", "in a sunlit hotel room sitting on a cream sofa near the window", False),
    ("아파트 거실", "in a bright minimal apartment living room with a beige sofa", False),
    ("노출 콘크리트 계단", "on exposed concrete outdoor stairs with a metal handrail", False),
    ("벽 앞 벤치", "on a wooden bench in front of a gray concrete wall", False),
    ("리조트 수영장", "at the edge of a blue resort infinity pool with white villas behind", False),
    ("갤러리 벽", "in a white art gallery with paintings on the wall", False),
    ("호텔 라운지", "in a dim warm hotel lounge with leather sofas and wall lamps", True),
    ("성수동 거리", "on a trendy Seongsu-dong street in front of a cafe with a brand sign", False),
    ("부티크 입구", "in front of a stylish boutique entrance with a lattice wall", False),
    ("공원 벤치", "on a park bench under autumn trees", False),
    ("노을 해변", "on a sandy beach at sunset with gentle waves", False),
    ("침실", "in a cozy bedroom with white bedding and soft window light", False),
    ("야경 루프탑", "on a rooftop terrace at night with Seoul city lights", True),
    ("백화점 에스컬레이터", "near the escalators inside a luxury department store", False),
    ("한강 산책로", "on the Han River walking path with the river behind", False),
]

# 같은 줄 2장에 하나씩 (포즈, 구도)
POSES = [
    ("뒤돌아보기", "looking back over her shoulder at the camera"),
    ("두 팔 머리 뒤", "both arms raised behind her head, glancing to the side"),
    ("브이 셀카(위에서)", "high-angle selfie taken from above, making a peace sign, looking up at the lens"),
    ("내려다보는 셀카", "high-angle POV shot from above while she looks down at her phone, hair falling forward"),
    ("다리 꼬고 앉기", "sitting with legs crossed, one hand resting on her knee, smiling at the camera"),
    ("걷는 순간", "caught mid-stride walking toward the camera, holding a shoulder bag"),
    ("한쪽 다리 뒤로", "standing with one leg kicked back playfully, holding a top-handle handbag"),
    ("계단 내려오기", "walking down the stairs holding the handrail, looking down"),
    ("테이블에 기대기", "leaning forward over the table, chin near her hand"),
    ("거울 셀카", "taking a mirror selfie with her phone, one hip popped"),
    ("수영장 가장자리", "sitting on the pool edge with hands on the deck behind her"),
    ("뒷모습 걷기", "walking away from the camera, looking slightly back"),
    ("머리 넘기기", "running one hand through her hair, soft smile"),
    ("윙크 클로즈업", "close-up from chest up, winking with a playful smile"),
    ("허리에 손", "standing with one hand on her waist, confident smile"),
    ("턱 괴고 앉기", "sitting and resting her chin on her hand, gazing at the camera"),
]

HAIRS = [
    ("풀어 내린 웨이브", "long dark wavy hair worn down"),
    ("포니테일", "long dark hair in a sleek high ponytail with face-framing strands"),
    ("승무원 쪽머리", "dark hair pulled back into a sleek low chignon bun like a flight attendant, small pearl earrings"),
    ("반묶음", "long dark hair in a half-up half-down style with a small claw clip"),
    ("집게핀 업스타일", "dark hair loosely clipped up with a claw clip, messy strands around the face"),
    ("시스루뱅 생머리", "long straight dark hair with see-through bangs"),
]

CAMERAS = [
    "candid smartphone photo, natural light",
    "shot on 35mm film, soft grain",
    "iPhone photo, slightly warm tone",
]

ALL_POSES = {p[0] for p in POSES}
_SIT = {"다리 꼬고 앉기", "턱 괴고 앉기", "테이블에 기대기", "내려다보는 셀카", "브이 셀카(위에서)", "윙크 클로즈업", "머리 넘기기"}
_WALK = {"걷는 순간", "뒷모습 걷기", "뒤돌아보기", "한쪽 다리 뒤로", "허리에 손", "머리 넘기기", "브이 셀카(위에서)", "두 팔 머리 뒤"}
# 장소마다 자연스러운 포즈만
SCENE_POSES = {
    "카페 창가": _SIT, "베이커리 카운터": _SIT | {"뒤돌아보기", "허리에 손"},
    "편의점": {"내려다보는 셀카", "뒤돌아보기", "브이 셀카(위에서)", "윙크 클로즈업", "머리 넘기기"},
    "호텔 방 소파": _SIT | {"두 팔 머리 뒤", "거울 셀카"}, "아파트 거실": _SIT | {"두 팔 머리 뒤", "거울 셀카", "허리에 손"},
    "노출 콘크리트 계단": {"계단 내려오기", "다리 꼬고 앉기", "뒤돌아보기", "머리 넘기기", "허리에 손"},
    "벽 앞 벤치": {"다리 꼬고 앉기", "턱 괴고 앉기", "머리 넘기기", "허리에 손", "두 팔 머리 뒤"},
    "리조트 수영장": {"수영장 가장자리", "뒷모습 걷기", "뒤돌아보기", "머리 넘기기", "두 팔 머리 뒤"},
    "갤러리 벽": _WALK, "호텔 라운지": _SIT | {"허리에 손", "거울 셀카"},
    "성수동 거리": _WALK, "부티크 입구": _WALK, "공원 벤치": _SIT | {"두 팔 머리 뒤"},
    "노을 해변": {"뒷모습 걷기", "뒤돌아보기", "머리 넘기기", "걷는 순간", "두 팔 머리 뒤"},
    "침실": {"두 팔 머리 뒤", "윙크 클로즈업", "브이 셀카(위에서)", "거울 셀카", "머리 넘기기", "턱 괴고 앉기"},
    "야경 루프탑": _WALK | {"다리 꼬고 앉기"}, "백화점 에스컬레이터": _WALK, "한강 산책로": _WALK,
}

# 계절에 안 맞는 조합 제외 (수영장/해변은 바디슈트·원피스류만 등은 프롬프트에서 자연스럽게 처리)
NIGHT_OK = {"새틴 하이넥 미니", "블랙 터틀넥+가죽 스커트", "브라운 슬립 미니 원피스", "도트 미니 원피스", "레드 트위드 재킷+블랙 미니+롱부츠"}


def pick(row: int) -> dict:
    """줄 번호로 결정적으로 고름(서로소 보폭으로 순환 → 연속된 줄끼리 겹치지 않음)."""
    o = OUTFITS[(row * 7) % len(OUTFITS)]
    s = SCENES[(row * 5) % len(SCENES)]
    if s[2] and o[0] not in NIGHT_OK:  # 야간 장면엔 야간용 옷만
        s = SCENES[(row * 5 + 1) % len(SCENES)]
    h = HAIRS[row % len(HAIRS)]
    ok = [p for p in POSES if p[0] in SCENE_POSES.get(s[0], ALL_POSES)]
    p1 = ok[(row * 3) % len(ok)]
    p2 = ok[(row * 3 + max(1, len(ok) // 2)) % len(ok)]
    if p2 == p1:
        p2 = ok[(row * 3 + 1) % len(ok)]
    cam = CAMERAS[row % len(CAMERAS)]
    return {"outfit": o, "scene": s, "hair": h, "poses": (p1, p2), "camera": cam}


def prompts(row: int) -> dict:
    c = pick(row)
    base = (f"One single full-frame photograph, not a collage. A Korean woman with {c['hair'][1]}, {BODY}, "
            f"wearing {c['outfit'][1]}, {c['scene'][1]}")
    out = []
    for pose in c["poses"]:
        out.append(f"{base}, {pose[1]}, {c['camera']}, realistic Instagram lifestyle photo")
    return {
        "row": row,
        "summary": f"{c['outfit'][0]} / {c['hair'][0]} / {c['scene'][0]} / 포즈: {c['poses'][0][0]}, {c['poses'][1][0]}",
        "right": out[0],
        "left": out[1],
    }


if __name__ == "__main__":
    rows = [int(a) for a in sys.argv[1:]] or [7]
    for r in rows:
        print(json.dumps(prompts(r), ensure_ascii=False, indent=2))
