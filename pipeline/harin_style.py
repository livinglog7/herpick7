"""하린 사진 스타일 라이브러리 + 프롬프트 생성기.

레퍼런스 계정(옷·배경·포즈) 분석으로 (2차: h0_barbie·happyyy_star·koreangirlsontop 의상·포즈·헤어 추가,
비키니·속옷·침대 눕기·시스루 등은 현재 수위 유지를 위해 제외) 만든 목록에서 날짜(줄 번호)마다 겹치지 않게 골라
한 줄(오른쪽·왼쪽 하린 2장)에 쓸 프롬프트 2개를 만든다.
- 같은 줄 2장은 옷·헤어·장소가 같고 포즈·구도만 다르다 (하루의 이야기).
- 몸매 문구는 고정, 옷은 항상 몸에 붙는 핏(가슴 크기 유지).
- 배경: 큰 간판·글씨가 보이는 장소 금지(AI가 한글을 깨뜨림) → 간판 없는 장소 + 배경 흐림
- 얼굴 고정: soul_2 + 하린 v2(c4722e5c) 로 자리마다 후보 3장 생성 →
  tools/facecheck.py 로 첫 학습 얼굴(하린 v1 12장)과 비교해 0.70 이상 중 최고점만 사용.
  (하린 v3 4027e7c5 는 얼굴은 조금 낫지만 가슴이 작아져서 보류)
  3장 중 통과가 없으면 3장 더(최대 6장). 그래도 없으면 그 자리 헤어/포즈를 정면 얼굴이 잘 보이는 것으로 교체.
  (10/22 테스트: 하이 번·옆으로 앉아 고개 돌리기는 6장 모두 0.66 이하 → FACE_RISKY 참고)
  얼굴만 따로 바꾸는 편집(image_auto 얼굴 교체)은 오히려 점수가 떨어져서 쓰지 않음.
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
    # --- 2차 학습 (h0_barbie · happyyy_star · koreangirlsontop) ---
    ("오프숄더 러플 블라우스+스키니진", "a fitted white off-shoulder ruffled blouse with a front tie string and light blue skinny jeans"),
    ("그린 튜브탑+도트 미디스커트", "a fitted olive green tube top with a burgundy polka-dot midi skirt"),
    ("트렌치코트+화이트 탑", "an open beige trench coat over a fitted white ruched top and light jeans"),
    ("블랙 반팔 티+스키니진", "a thin fitted black crew-neck tee with black skinny jeans"),
    ("그레이 카라티+플리츠 미니+로퍼", "a fitted gray short-sleeve polo knit top with a cream pleated mini skirt, white socks and black loafers"),
    ("화이트 나시+연청", "a fitted white ribbed tank top with high-waisted light blue jeans and a brown belt"),
    ("화이트 크롭티+데님 숏츠", "a thin fitted white crop tee with high-waisted denim shorts"),
    ("오프숄더 니트+베이지 플리츠", "a fitted beige off-shoulder long-sleeve knit top with a beige pleated mini skirt"),
    ("브라운 홀터 미디 원피스", "a fitted mocha brown halter-neck midi dress"),
    ("그레이 스쿱넥 반팔+청바지", "a fitted heather gray scoop-neck short-sleeve top tucked into dark jeans with a brown belt"),
    ("아이보리 나시+와이드팬츠", "a fitted ivory ribbed cami top with cream wide-leg pants and a brown belt"),
    ("블랙 브이넥 롱슬리브+진", "a fitted black long-sleeve V-neck top with dark denim jeans"),
    ("트리밍 버튼 카디건", "a fitted white button-up cardigan with black trim, worn as a top, with a black mini skirt"),
    ("브라운 골지 터틀넥", "a thin fitted chocolate brown ribbed turtleneck knit with a black mini skirt"),
    ("레이스 트림 카디건+블랙 스커트", "a fitted black V-neck cardigan with lace trim, buttoned up, with a black midi skirt"),
    ("화이트 셔츠+화이트 숏츠", "a fitted white button-up shirt with rolled sleeves tucked into white tailored shorts"),
    ("화이트 나시+트랙팬츠", "a fitted white tank top with sky-blue striped track pants, sporty look"),
    ("니트 가디건+체크 미니", "a fitted cream V-neck knit cardigan with a brown plaid pleated mini skirt"),
    ("네이비 점퍼 원피스+셔츠", "a fitted navy pinafore mini dress over a light blue short-sleeve shirt"),
    ("블랙 집업 롬퍼", "a fitted black long-sleeve zip-front short romper with white sneakers"),
    ("플로럴 슬립 미디 원피스", "a fitted pale floral print satin slip midi dress"),
    ("러플 캐미+데님 숏츠", "a fitted white ruffle-trim cami top with denim shorts and a straw bag"),
]

# (이름, 프롬프트, 야간 여부)
SCENES = [
    ("카페 창가", "sitting at a window table in a bright Seoul cafe with an iced americano", False),
    ("꽃집 앞", "in front of a small flower shop with buckets of fresh flowers", False),
    ("베이커리 카운터", "at the counter of a cozy bakery cafe with pastries in the display", False),
    ("호텔 방 소파", "in a sunlit hotel room sitting on a cream sofa near the window", False),
    ("아파트 거실", "in a bright minimal apartment living room with a beige sofa", False),
    ("노출 콘크리트 계단", "on exposed concrete outdoor stairs with a metal handrail", False),
    ("벽 앞 벤치", "on a wooden bench in front of a gray concrete wall", False),
    ("리조트 수영장", "at the edge of a blue resort infinity pool with white villas behind", False),
    ("갤러리 벽", "in a white art gallery with paintings on the wall", False),
    ("호텔 라운지", "in a dim warm hotel lounge with leather sofas and wall lamps", True),
    ("성수동 골목", "on a quiet tree-lined side street with red brick walls in Seongsu-dong", False),
    ("부티크 입구", "in front of a stylish boutique entrance with a lattice wall", False),
    ("공원 벤치", "on a park bench under autumn trees", False),
    ("노을 해변", "on a sandy beach at sunset with gentle waves", False),
    ("침실", "in a cozy bedroom with white bedding and soft window light", False),
    ("야경 루프탑", "on a rooftop terrace at night with Seoul city lights", True),
    ("백화점 에스컬레이터", "near the escalators inside a luxury department store", False),
    ("한강 산책로", "on the Han River walking path with the river behind", False),
    # --- 2차 학습 (간판 없는 장소만) ---
    ("책장 앞", "in a quiet study room in front of tall wooden bookshelves", False),
    ("잔디 피크닉", "sitting on a picnic mat on the grass in a city park in the late afternoon", False),
    ("고궁 담장", "in front of a traditional Korean palace wall with red pillars and green lattice windows", False),
    ("영화관 좌석", "in a dark movie theater sitting in a black leather recliner seat with popcorn", True),
    ("벽돌 벽 벤치", "on a wooden bench in front of a red brick wall", False),
    ("인더스트리얼 카페", "in a spacious industrial cafe with concrete floor and wooden tables", False),
    ("호숫가 데크", "on a wooden deck by a calm green lake", False),
    ("검은 차 옆", "standing next to a glossy black car on a quiet street", False),
    ("나무 쪽문 앞", "in front of a white wall with a blue wooden door", False),
    ("녹차밭", "on a green tea plantation hillside", False),
    ("야자수 테라스", "at an outdoor terrace with white umbrellas and palm trees", False),
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
    ("거울 셀카", "taking a mirror selfie with her phone, one hip popped"),
    ("수영장 가장자리", "sitting on the pool edge with hands on the deck behind her"),
    ("뒷모습 걷기", "walking away from the camera, looking slightly back"),
    ("머리 넘기기", "running one hand through her hair, soft smile"),
    ("윙크 클로즈업", "close-up from chest up, winking with a playful smile"),
    ("허리에 손", "standing with one hand on her waist, confident smile"),
    ("턱 괴고 앉기", "sitting and resting her chin on her hand, gazing at the camera"),
    # --- 2차 학습 ---
    ("팔 뻗은 셀카", "arm-extended front-camera selfie, head slightly tilted, soft pout"),
    ("머리 묶는 중", "both hands behind her head tying her hair up, hair tie between her lips"),
    ("벽에 기대기", "leaning her shoulder against the wall, hands behind her back, gentle smile"),
    ("음료 들고 서기", "standing and holding an iced latte in one hand, other hand touching her hair"),
    ("가방 메고 정면", "standing facing the camera with a black shoulder bag, relaxed arms"),
    ("귀 뒤로 머리 넘기기", "tucking her hair behind her ear, looking off to the side"),
    ("바닥에 앉아 무릎", "sitting on the ground with knees bent to the side, leaning on one hand, looking up"),
    ("옆모습 턱선", "side profile looking away, one hand under her chin"),
    ("한 팔 위로 스트레칭", "one arm raised above her head in a relaxed stretch, eyes to the camera"),
    ("의자에 옆으로 앉기", "sitting sideways on a chair, legs together, turning her face to the camera"),
]

HAIRS = [
    ("풀어 내린 웨이브", "long dark wavy hair worn down"),
    ("포니테일", "long dark hair in a sleek high ponytail with face-framing strands"),
    ("승무원 쪽머리", "dark hair pulled back into a sleek low chignon bun like a flight attendant, small pearl earrings"),
    ("반묶음", "long dark hair in a half-up half-down style with a small claw clip"),
    ("집게핀 업스타일", "dark hair loosely clipped up with a claw clip, messy strands around the face"),
    ("시스루뱅 생머리", "long straight dark hair with see-through bangs"),
    # --- 2차 학습 ---
    ("옆으로 땋은 머리", "long dark hair in a loose side fishtail braid over one shoulder, a small flower tucked behind her ear"),
    ("로우 포니+스크런치", "long dark hair in a low ponytail with a white scrunchie, loose strands framing the face"),
    ("하이 번", "dark hair in a high messy top bun with wispy strands"),
    ("귀 뒤로 넘긴 생머리", "long straight dark hair tucked behind both ears, sleek middle part"),
]

# 얼굴 점수가 잘 안 나오는 조합 — 쓸 때는 후보를 6장까지 뽑을 것
FACE_RISKY = {"하이 번", "의자에 옆으로 앉기", "옆모습 턱선", "뒷모습 걷기"}

CAMERAS = [
    "candid smartphone photo, natural light",
    "evening flash photo, warm ambient light",
    "warm natural daylight",
    "soft golden hour light",
]

ALL_POSES = {p[0] for p in POSES}
_SIT = {"다리 꼬고 앉기", "턱 괴고 앉기", "내려다보는 셀카", "브이 셀카(위에서)", "윙크 클로즈업", "머리 넘기기",
        "팔 뻗은 셀카", "옆모습 턱선", "의자에 옆으로 앉기", "귀 뒤로 머리 넘기기"}
_WALK = {"걷는 순간", "뒷모습 걷기", "뒤돌아보기", "한쪽 다리 뒤로", "허리에 손", "머리 넘기기", "브이 셀카(위에서)", "두 팔 머리 뒤",
         "음료 들고 서기", "가방 메고 정면", "귀 뒤로 머리 넘기기", "팔 뻗은 셀카"}
_WALL = {"벽에 기대기", "머리 묶는 중", "한 팔 위로 스트레칭", "허리에 손", "가방 메고 정면", "옆모습 턱선"}
# 장소마다 자연스러운 포즈만
SCENE_POSES = {
    "카페 창가": _SIT, "베이커리 카운터": _SIT | {"뒤돌아보기", "허리에 손"},
    "꽃집 앞": {"내려다보는 셀카", "뒤돌아보기", "브이 셀카(위에서)", "윙크 클로즈업", "머리 넘기기"},
    "호텔 방 소파": _SIT | {"두 팔 머리 뒤", "거울 셀카"}, "아파트 거실": _SIT | {"두 팔 머리 뒤", "거울 셀카", "허리에 손"},
    "노출 콘크리트 계단": {"계단 내려오기", "다리 꼬고 앉기", "뒤돌아보기", "머리 넘기기", "허리에 손"},
    "벽 앞 벤치": {"다리 꼬고 앉기", "턱 괴고 앉기", "머리 넘기기", "허리에 손", "두 팔 머리 뒤"},
    "리조트 수영장": {"수영장 가장자리", "뒷모습 걷기", "뒤돌아보기", "머리 넘기기", "두 팔 머리 뒤"},
    "갤러리 벽": _WALK, "호텔 라운지": _SIT | {"허리에 손", "거울 셀카"},
    "성수동 골목": _WALK, "부티크 입구": _WALK, "공원 벤치": _SIT | {"두 팔 머리 뒤"},
    "노을 해변": {"뒷모습 걷기", "뒤돌아보기", "머리 넘기기", "걷는 순간", "두 팔 머리 뒤"},
    "침실": {"두 팔 머리 뒤", "윙크 클로즈업", "브이 셀카(위에서)", "거울 셀카", "머리 넘기기", "턱 괴고 앉기"},
    "야경 루프탑": _WALK | {"다리 꼬고 앉기"}, "백화점 에스컬레이터": _WALK, "한강 산책로": _WALK,
    "책장 앞": _WALL | {"팔 뻗은 셀카", "귀 뒤로 머리 넘기기"},
    "잔디 피크닉": {"바닥에 앉아 무릎", "팔 뻗은 셀카", "옆모습 턱선", "머리 넘기기", "턱 괴고 앉기"},
    "고궁 담장": _WALK | {"벽에 기대기"},
    "영화관 좌석": {"옆모습 턱선", "팔 뻗은 셀카", "턱 괴고 앉기", "윙크 클로즈업"},
    "벽돌 벽 벤치": _SIT | {"벽에 기대기", "머리 묶는 중"},
    "인더스트리얼 카페": _WALL | {"음료 들고 서기", "의자에 옆으로 앉기", "다리 꼬고 앉기"},
    "호숫가 데크": {"팔 뻗은 셀카", "바닥에 앉아 무릎", "뒤돌아보기", "머리 넘기기", "옆모습 턱선"},
    "검은 차 옆": {"벽에 기대기", "옆모습 턱선", "가방 메고 정면", "귀 뒤로 머리 넘기기", "뒤돌아보기"},
    "나무 쪽문 앞": _WALL,
    "녹차밭": {"팔 뻗은 셀카", "옆모습 턱선", "뒤돌아보기", "머리 넘기기", "걷는 순간"},
    "야자수 테라스": _SIT | {"음료 들고 서기", "뒤돌아보기"},
}

# 계절에 안 맞는 조합 제외 (수영장/해변은 바디슈트·원피스류만 등은 프롬프트에서 자연스럽게 처리)
NIGHT_OK = {"새틴 하이넥 미니", "블랙 터틀넥+가죽 스커트", "브라운 슬립 미니 원피스", "도트 미니 원피스", "레드 트위드 재킷+블랙 미니+롱부츠",
            "블랙 반팔 티+스키니진", "블랙 브이넥 롱슬리브+진", "레이스 트림 카디건+블랙 스커트", "브라운 골지 터틀넥", "트리밍 버튼 카디건"}


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
        out.append(f"{base}, {pose[1]}, {c['camera']}, background softly blurred with shallow depth of field, natural candid lifestyle photo")
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
