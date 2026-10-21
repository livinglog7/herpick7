# HERPICK (herpick7)

인스타그램 herpick7 피드의 번호별 상품 페이지입니다. 인스타 프로필 링크는 이 사이트 주소 하나로 고정하고,
새 줄을 올릴 때마다 `docs/products.json`에 상품을 추가하면 사이트가 갱신됩니다.

- `docs/products.json` : 상품 목록 (번호, 이름, 분야, 대표 문구, 가격, 이미지, 쇼핑커넥트 링크)
- `pipeline/site_build.py` : `docs/` 정적 사이트 생성 (GitHub Pages: main 브랜치 / docs 폴더)
- 도메인 연결 시 `SITE_DOMAIN=herpick7.com python pipeline/site_build.py` 로 CNAME 생성
