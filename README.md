# HERPICK (herpick7)

인스타그램 herpick7 피드의 번호별 상품 페이지입니다. 인스타 프로필 링크는 이 사이트 주소 하나로 고정하고,
새 줄을 올릴 때마다 `docs/products.json`에 상품을 추가하면 사이트가 갱신됩니다.

- `docs/products.json` : 상품 목록 (번호, 이름, 분야, 대표 문구, 가격, 이미지, 쇼핑커넥트 링크)
- `pipeline/site_build.py` : `docs/` 정적 사이트 생성 (GitHub Pages: main 브랜치 / docs 폴더)
- 도메인 연결 시 `SITE_DOMAIN=herpick7.com python pipeline/site_build.py` 로 CNAME 생성

## 게시 규칙 (고정)
- 한 줄 = 3게시물: 오른쪽 하린 사진 → **가운데 상품 = 항상 릴스 영상** → 왼쪽 하린 사진
- 상품 영상: `pipeline/reel.py` (하린 장면 → 상품 소개 → 포인트 → "프로필 링크 N번", 여자 음성 + 자막, 16~19초)
  - 커버(`*_cover.jpg`) 가운데 3:4 = `tools/product_cell.py` 상품 이미지 → 그리드에서는 기존 상품 칸과 똑같이 보임
  - Metricool: `instagramData.type = REEL`, `showReelOnFeed = true`, `videoThumbnailUrl = 커버`
- Threads 글: 반말, 끝에 "🛒 <naver.me 상품링크>" + 수수료 문구("이 포스팅은 네이버 쇼핑 커넥트 활동의 일환으로, 판매 발생 시 수수료를 제공받습니다.")를 본문에 직접 넣음(프로필 안 가도 되게). 인스타 캡션은 링크가 안 눌리므로 "📌 프로필 링크 N번" 유지
- 캡션: 자연스러운 말투, 끝은 "📌 프로필 링크 N번" + 상품 해시태그. #광고 #AI모델·수수료 문구 넣지 않음(수수료 안내는 herpick7.com에만)
- 하린 사진: `pipeline/harin_style.py` 옷·장소·포즈·헤어 순환, 후보 3장 → `tools/facecheck.py` 0.70 이상 최고점 사용
- 하린 배경: 큰 간판·한글 글씨가 크게 보이는 장소는 피함(AI가 한글을 깨뜨림). 간판 없는 장소 + 배경 흐림
