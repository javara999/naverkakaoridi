# naverkakaoridi

BookOasis 메타데이터 플러그인 - 네이버웹툰/네이버시리즈/카카오웹툰/카카오페이지/리디북스 통합 검색.

- id: `naverkakaoridi`
- 이름: 네이버/카카오/리디 메타 검색

## 설정 항목

| 키 | 기본값 | 설명 |
|---|---|---|
| SOURCES | all | 검색 사이트. `all` 또는 `naver_webtoon,naver_series,kakao_webtoon,kakaopage,ridibooks` 조합(콤마 구분) |
| MAX_RESULTS | 20 | 전체 사이트 결과를 합쳐 반환할 최대 개수 |
| TIMEOUT | 10 | 외부 사이트 요청 제한 시간(초) |
| USER_AGENT | Chrome UA | 차단 회피가 필요할 때만 변경 |
| SEARCH_EXACT | false | true면 검색어와 제목이 거의 같은 결과만 사용 |
| INCLUDE_ADULT | false | true면 19세/성인 플래그 결과도 포함 |
| NAVER_COOKIE / KAKAO_COOKIE / RIDI_COOKIE | (공백) | 연령 제한/로그인 필요 작품 검색 시에만 입력 |
| KAKAOPAGE_CATEGORY | - | 카카오페이지 카테고리 필터 |

## 설치

`plugins/metadata/naverkakaoridi/` 경로에 배치하면 BookOasis가 자동으로 인식합니다.
